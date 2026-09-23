"""Newsletter and notification email.

Sign-up is double opt-in: the form only ever triggers a confirmation email, and
posts go out only to addresses that followed the link in it. New-post mail is
sent by the `send_newsletter` management command on a timer, never inside a web
request, so a slow SMTP server cannot stall the site.
"""

import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Newsletter, NewsletterDelivery, Post

logger = logging.getLogger(__name__)

CONFIRM_SALT = 'blog.newsletter.confirm'


class NewsletterError(Exception):
    """Raised when a link token is missing, forged, expired or superseded."""


def _one_line(value):
    # Django refuses header values containing newlines outright. Collapsing them
    # keeps a post title with a stray line break from failing the whole send.
    return ' '.join(str(value).split())


def _site_link(path, **params):
    url = f'{settings.SITE_URL}{path}'
    return f'{url}?{urlencode(params)}' if params else url


def _build_email(subject, template, context, to, *, headers=None, reply_to=None, connection=None):
    context = {'site_name': settings.SITE_NAME, 'site_url': settings.SITE_URL, **context}
    message = EmailMultiAlternatives(
        subject=_one_line(subject),
        body=render_to_string(f'blog/email/{template}.txt', context),
        to=[to],
        headers=headers,
        reply_to=reply_to,
        connection=connection,
    )
    message.attach_alternative(render_to_string(f'blog/email/{template}.html', context), 'text/html')
    return message


# --- Subscribing -------------------------------------------------------------

def confirmation_token(subscriber):
    # Bound to the exact send time, so each new link voids the ones before it.
    return signing.dumps(
        [subscriber.pk, subscriber.confirmation_sent_at.isoformat()], salt=CONFIRM_SALT
    )


def subscribe(email):
    """Start, or restart, a subscription for `email`.

    The caller gives the same answer whatever happens here, so the form cannot
    be used to find out who is subscribed.
    """
    subscriber, _ = Newsletter.objects.get_or_create(email=email)
    if subscriber.is_receiving:
        return
    if not subscriber.is_active:
        # Coming back after unsubscribing needs a fresh confirmation, otherwise
        # anyone could re-subscribe an address that opted out.
        subscriber.is_active = True
        subscriber.confirmed_at = None
        subscriber.unsubscribed_at = None
        subscriber.save(update_fields=['is_active', 'confirmed_at', 'unsubscribed_at'])
    send_confirmation(subscriber)


def send_confirmation(subscriber, *, ignore_cooldown=False):
    """Email a confirmation link. Returns whether one was sent."""
    now = timezone.now()
    if (
        not ignore_cooldown
        and subscriber.confirmation_sent_at
        and now - subscriber.confirmation_sent_at < settings.NEWSLETTER_CONFIRMATION_COOLDOWN
    ):
        # Stops the form being used to flood one inbox from many IPs.
        return False

    recent = Newsletter.objects.filter(confirmation_sent_at__gte=now - timedelta(hours=1)).count()
    if recent >= settings.NEWSLETTER_CONFIRMATIONS_PER_HOUR:
        logger.warning('Newsletter confirmation cap reached; not emailing %s', subscriber.email)
        return False

    previous = subscriber.confirmation_sent_at
    subscriber.confirmation_sent_at = now
    subscriber.save(update_fields=['confirmation_sent_at'])
    link = _site_link('/newsletter/confirm', token=confirmation_token(subscriber))
    try:
        _build_email(
            f'Confirm your subscription to {settings.SITE_NAME}',
            'confirm',
            {'confirm_url': link, 'valid_days': settings.NEWSLETTER_CONFIRMATION_MAX_AGE.days},
            subscriber.email,
        ).send()
    except Exception:
        logger.exception('Could not send a newsletter confirmation to %s', subscriber.email)
        # Put the cooldown back so the reader can try again straight away.
        subscriber.confirmation_sent_at = previous
        subscriber.save(update_fields=['confirmation_sent_at'])
        return False
    return True


def confirm(token):
    """Confirm the subscription a link was issued for."""
    try:
        pk, issued = signing.loads(
            token,
            salt=CONFIRM_SALT,
            max_age=settings.NEWSLETTER_CONFIRMATION_MAX_AGE,
        )
        issued = datetime.fromisoformat(issued)
    except (signing.BadSignature, TypeError, ValueError):
        raise NewsletterError('This confirmation link is invalid or has expired.')

    subscriber = Newsletter.objects.filter(pk=pk, is_active=True).first()
    if (
        subscriber is None
        or subscriber.confirmation_sent_at is None
        or subscriber.confirmation_sent_at != issued
    ):
        # Only the most recent link counts, and unsubscribing voids it.
        raise NewsletterError('This confirmation link is invalid or has expired.')

    if subscriber.confirmed_at is None:
        subscriber.confirmed_at = timezone.now()
        subscriber.save(update_fields=['confirmed_at'])
    return subscriber


def unsubscribe(token):
    subscriber = Newsletter.objects.filter(unsubscribe_token=token).first()
    if subscriber is None:
        raise NewsletterError('This unsubscribe link is not valid.')
    if subscriber.is_active:
        subscriber.is_active = False
        subscriber.unsubscribed_at = timezone.now()
        subscriber.confirmation_sent_at = None
        subscriber.save(update_fields=['is_active', 'unsubscribed_at', 'confirmation_sent_at'])
    return subscriber


# --- New-post mail -----------------------------------------------------------

def unsubscribe_links(subscriber):
    page = _site_link('/newsletter/unsubscribe', token=subscriber.unsubscribe_token)
    # RFC 8058 one-click: mail clients POST straight to the API, no page involved.
    one_click = _site_link('/api/blog/newsletter/unsubscribe/', token=subscriber.unsubscribe_token)
    return page, one_click


def build_post_email(post, subscriber, connection=None):
    page, one_click = unsubscribe_links(subscriber)
    return _build_email(
        f'New post: {post.title}',
        'new_post',
        {'post': post, 'post_url': _site_link(f'/posts/{post.slug}'), 'unsubscribe_url': page},
        subscriber.email,
        headers={
            'List-Unsubscribe': f'<{one_click}>',
            'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
        },
        connection=connection,
    )


def posts_awaiting_newsletter(now=None):
    now = now or timezone.now()
    return (
        Post.objects.filter(status='published', newsletter_sent_at__isnull=True)
        .filter(Q(published_at__isnull=True) | Q(published_at__lte=now))
        .order_by('published_at', 'created_at')
    )


def send_new_posts(*, dry_run=False, log=logger.info):
    """Email receiving subscribers about published posts not yet sent out.

    Stops at the daily limit and resumes on a later run. An SMTP failure aborts
    the run with the failed delivery rolled back, so the next run retries it.
    Returns the number of emails sent.
    """
    now = timezone.now()
    budget = settings.NEWSLETTER_DAILY_SEND_LIMIT - NewsletterDelivery.objects.filter(
        sent_at__gte=now - timedelta(days=1)
    ).count()
    sent = 0

    with get_connection() as connection:
        for post in posts_awaiting_newsletter(now):
            if post.published_at and now - post.published_at > settings.NEWSLETTER_MAX_POST_AGE:
                log(f'Skipping "{post.title}": published too long ago to announce.')
                if not dry_run:
                    Post.objects.filter(pk=post.pk).update(newsletter_sent_at=now)
                continue

            recipients = Newsletter.objects.receiving().exclude(deliveries__post=post).order_by('pk')
            if dry_run:
                log(f'Would email {recipients.count()} subscriber(s) about "{post.title}".')
                continue

            for subscriber in recipients.iterator():
                if budget <= 0:
                    log('Daily send limit reached; the rest will go out on a later run.')
                    return sent
                try:
                    with transaction.atomic():
                        delivery = NewsletterDelivery.objects.create(post=post, subscriber=subscriber)
                except IntegrityError:
                    continue  # Another run already claimed this one.
                try:
                    build_post_email(post, subscriber, connection).send()
                except Exception:
                    delivery.delete()
                    raise
                sent += 1
                budget -= 1

            Post.objects.filter(pk=post.pk).update(newsletter_sent_at=now)
            log(f'Finished emailing subscribers about "{post.title}".')
    return sent


# --- Contact form ------------------------------------------------------------

def notify_contact_message(message):
    """Forward a contact-form message to the site owner, if an inbox is set."""
    if not settings.CONTACT_NOTIFY_EMAIL:
        return
    try:
        _build_email(
            f'[{settings.SITE_NAME} contact] {message.subject}',
            'contact',
            {'message': message},
            settings.CONTACT_NOTIFY_EMAIL,
            # Replying goes straight to the sender. The From address stays ours,
            # since sending as the visitor would fail SPF and DMARC.
            reply_to=[message.email],
        ).send()
    except Exception:
        # The message is already stored and visible in the admin.
        logger.exception('Could not forward contact message %s', message.pk)
