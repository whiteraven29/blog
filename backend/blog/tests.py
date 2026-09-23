import json
import re
from datetime import timedelta
from io import StringIO
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase

from . import newsletter
from .models import Category, Comment, ContactMessage, Newsletter, NewsletterDelivery, Post, Tag


class BlogApiTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='author', password='safe-password')
        self.other_user = User.objects.create_user(username='other', password='safe-password')
        self.category = Category.objects.create(name='Security')
        self.tag = Tag.objects.create(name='django')
        self.published = Post.objects.create(
            title='Published post',
            author=self.author,
            category=self.category,
            content='Public content',
            status='published',
        )
        self.published.tags.add(self.tag)
        self.draft = Post.objects.create(
            title='Draft post',
            author=self.author,
            category=self.category,
            content='Private content',
            status='draft',
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.author)

    def test_category_count_only_includes_published_posts(self):
        response = self.client.get(reverse('category-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['post_count'], 1)

    def test_category_list_is_not_paginated(self):
        for index in range(20):
            Category.objects.create(name=f'Topic {index}')

        response = self.client.get(reverse('category-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 21)

    def test_anonymous_user_cannot_create_category(self):
        response = self.client.post(reverse('category-list'), {'name': 'Forensics'})

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Category.objects.filter(name='Forensics').exists())

    def test_author_can_create_category(self):
        self.authenticate()

        response = self.client.post(
            reverse('category-list'),
            {'name': 'Reverse Engineering', 'color': '#22c55e', 'description': 'REV'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['slug'], 'reverse-engineering')
        self.assertEqual(response.data['color'], '#22c55e')
        self.assertEqual(response.data['post_count'], 0)

    def test_duplicate_category_name_is_rejected_case_insensitively(self):
        self.authenticate()

        response = self.client.post(
            reverse('category-list'), {'name': 'security'}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.data)

    def test_category_slug_collision_gets_a_suffix(self):
        self.authenticate()
        Category.objects.create(name='Web Dev')

        response = self.client.post(
            reverse('category-list'), {'name': 'Web  dev!'}, format='json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['slug'], 'web-dev-1')

    def test_invalid_category_color_is_rejected(self):
        self.authenticate()

        response = self.client.post(
            reverse('category-list'), {'name': 'Crypto', 'color': 'purple'}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('color', response.data)

    def test_public_comment_response_does_not_expose_email(self):
        Comment.objects.create(
            post=self.published,
            author_name='Reader',
            author_email='reader@example.com',
            body='Useful post',
            is_approved=True,
        )

        response = self.client.get(reverse('post-detail', kwargs={'slug': self.published.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('author_email', response.data['comments'][0])

    def test_comment_submission_accepts_email_without_returning_it(self):
        response = self.client.post(
            reverse('comment-create', kwargs={'slug': self.published.slug}),
            {
                'author_name': 'Reader',
                'author_email': 'reader@example.com',
                'body': 'Thanks for the writeup',
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertNotIn('author_email', response.data)
        self.assertEqual(Comment.objects.get().author_email, 'reader@example.com')

    def test_comment_submission_allows_anonymous_author(self):
        response = self.client.post(
            reverse('comment-create', kwargs={'slug': self.published.slug}),
            {'body': 'Anonymous feedback'},
        )

        self.assertEqual(response.status_code, 201)
        comment = Comment.objects.get()
        self.assertEqual(comment.author_name, '')
        self.assertEqual(comment.author_email, '')

    def test_submitted_comment_is_visible_without_review(self):
        self.client.post(
            reverse('comment-create', kwargs={'slug': self.published.slug}),
            {'author_name': 'Reader', 'body': 'Straight onto the page'},
        )

        response = self.client.get(reverse('post-detail', kwargs={'slug': self.published.slug}))

        self.assertEqual(response.data['comment_count'], 1)
        self.assertEqual(response.data['comments'][0]['body'], 'Straight onto the page')

    def test_editor_get_returns_nested_category_and_tags(self):
        self.authenticate()

        response = self.client.get(reverse('post-update', kwargs={'slug': self.published.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['category']['id'], self.category.id)
        self.assertEqual(response.data['tags'][0]['name'], self.tag.name)

    def test_author_can_update_post_with_tag_names(self):
        self.authenticate()

        response = self.client.patch(
            reverse('post-update', kwargs={'slug': self.published.slug}),
            {'category': self.category.id, 'tags_by_name': ['python', 'Django']},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(self.published.tags.values_list('name', flat=True)),
            {'python', 'django'},
        )

    def test_other_user_cannot_edit_post(self):
        self.authenticate(self.other_user)

        response = self.client.patch(
            reverse('post-update', kwargs={'slug': self.published.slug}),
            {'title': 'Not allowed'},
            format='json',
        )

        self.assertEqual(response.status_code, 404)

    def test_page_size_query_parameter_is_capped(self):
        for index in range(15):
            Post.objects.create(
                title=f'Extra post {index}',
                author=self.author,
                content='Content',
                status='published',
            )

        response = self.client.get(reverse('post-list'), {'page_size': 50})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 16)

    def test_post_detail_reports_approved_comment_count(self):
        Comment.objects.create(post=self.published, body='Shown', is_approved=True)
        Comment.objects.create(post=self.published, body='Hidden', is_approved=False)

        response = self.client.get(reverse('post-detail', kwargs={'slug': self.published.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comment_count'], 1)
        self.assertEqual(len(response.data['comments']), 1)

    def test_view_counter_matches_the_stored_value(self):
        first = self.client.get(reverse('post-detail', kwargs={'slug': self.published.slug}))
        second = self.client.get(reverse('post-detail', kwargs={'slug': self.published.slug}))

        self.published.refresh_from_db()
        self.assertEqual(first.data['views'], 1)
        self.assertEqual(second.data['views'], 2)
        self.assertEqual(self.published.views, 2)

    def test_draft_preview_does_not_count_as_a_view(self):
        self.authenticate()

        response = self.client.get(reverse('post-detail', kwargs={'slug': self.draft.slug}))

        self.assertEqual(response.status_code, 200)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.views, 0)

    def test_author_can_preview_own_draft(self):
        self.authenticate()

        response = self.client.get(reverse('post-detail', kwargs={'slug': self.draft.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'draft')

    def test_anonymous_user_cannot_read_a_draft(self):
        response = self.client.get(reverse('post-detail', kwargs={'slug': self.draft.slug}))

        self.assertEqual(response.status_code, 404)

    def test_staff_user_does_not_see_drafts_in_the_public_list(self):
        staff = User.objects.create_user(
            username='staff', password='safe-password', is_staff=True
        )
        self.authenticate(staff)

        response = self.client.get(reverse('post-list'))

        slugs = [post['slug'] for post in response.data['results']]
        self.assertIn(self.published.slug, slugs)
        self.assertNotIn(self.draft.slug, slugs)

    def test_repeat_subscription_is_indistinguishable_from_the_first(self):
        first = self.client.post(reverse('newsletter'), {'email': 'reader@example.com'})
        second = self.client.post(reverse('newsletter'), {'email': 'READER@example.com'})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data, second.data)
        self.assertEqual(Newsletter.objects.filter(email='reader@example.com').count(), 1)

    def test_malformed_subscription_email_is_rejected(self):
        response = self.client.post(reverse('newsletter'), {'email': 'not-an-email'})

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_health_endpoint_checks_database(self):
        response = self.client.get(reverse('health'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'status': 'ok'})


class ImportPostCommandTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='importer', password='safe-password')

    def write_markdown(self, tmp_path, body='Imported body'):
        path = tmp_path / 'my-post.md'
        path.write_text(f'---\ntitle: My Post\nstatus: published\n---\n\n{body}\n')
        return path

    def test_update_handles_a_duplicated_title(self):
        import tempfile
        from pathlib import Path

        # Two posts can legitimately share a title; only the slug is unique.
        Post.objects.create(title='My Post', author=self.author, content='First')
        Post.objects.create(title='My Post', author=self.author, content='Second')

        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_markdown(Path(tmp), body='Rewritten')
            call_command(
                'import_post', str(path), '--author', 'importer', '--update',
                stdout=StringIO(),
            )

        oldest = Post.objects.filter(title='My Post').order_by('created_at').first()
        self.assertEqual(oldest.content, 'Rewritten')
        self.assertEqual(Post.objects.filter(title='My Post').count(), 2)

    def test_reimport_keeps_the_original_publication_date(self):
        import tempfile
        from pathlib import Path

        original = timezone.now() - timezone.timedelta(days=30)
        Post.objects.create(
            title='My Post', author=self.author, content='First',
            status='published', published_at=original,
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_markdown(Path(tmp))
            call_command(
                'import_post', str(path), '--author', 'importer', '--update',
                stdout=StringIO(),
            )

        self.assertEqual(Post.objects.get(title='My Post').published_at, original)


class ContactFormTests(APITestCase):
    url = None

    def setUp(self):
        self.url = reverse('contact')
        # Throttle counters live in the cache and would otherwise leak between tests.
        cache.clear()

    def payload(self, **overrides):
        data = {
            'name': 'Reader',
            'email': 'reader@example.com',
            'subject': 'Collaboration',
            'message': 'I would like to talk about a security assessment.',
        }
        data.update(overrides)
        return data

    def test_message_is_stored(self):
        response = self.client.post(self.url, self.payload(), format='json')

        self.assertEqual(response.status_code, 201)
        message = ContactMessage.objects.get()
        self.assertEqual(message.email, 'reader@example.com')
        self.assertFalse(message.is_read)

    def test_markup_is_stripped_from_submitted_text(self):
        self.client.post(
            self.url,
            self.payload(
                name='<script>alert(1)</script>Reader',
                subject='<img src=x onerror=alert(1)>Hello',
                message='<b>Bold</b> request about an assessment please.',
            ),
            format='json',
        )

        message = ContactMessage.objects.get()
        self.assertNotIn('<', message.name)
        self.assertNotIn('<', message.subject)
        self.assertNotIn('<', message.message)
        self.assertIn('Reader', message.name)

    def test_newlines_are_stripped_from_single_line_fields(self):
        self.client.post(
            self.url,
            self.payload(subject='Hello\r\nBcc: victim@example.com'),
            format='json',
        )

        subject = ContactMessage.objects.get().subject
        self.assertNotIn('\n', subject)
        self.assertNotIn('\r', subject)

    def test_null_bytes_are_rejected(self):
        response = self.client.post(
            self.url,
            self.payload(message='A genuine enquiry\x00 about your work.'),
            format='json',
        )

        # DRF's CharField refuses these before the field validator runs, which is
        # what keeps the value away from a text column that cannot store it.
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ContactMessage.objects.exists())

    def test_other_control_characters_are_stripped(self):
        self.client.post(
            self.url,
            self.payload(message='A genuine enquiry\x07\x1b about your work.'),
            format='json',
        )

        stored = ContactMessage.objects.get().message
        self.assertNotIn('\x07', stored)
        self.assertNotIn('\x1b', stored)

    def test_link_heavy_message_is_rejected(self):
        response = self.client.post(
            self.url,
            self.payload(
                message='Deals http://a.example http://b.example http://c.example www.d.example'
            ),
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(ContactMessage.objects.exists())

    def test_very_short_message_is_rejected(self):
        response = self.client.post(self.url, self.payload(message='hi'), format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(ContactMessage.objects.exists())

    def test_invalid_email_is_rejected(self):
        response = self.client.post(self.url, self.payload(email='nope'), format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_honeypot_submission_is_accepted_but_discarded(self):
        response = self.client.post(
            self.url, self.payload(website='http://spam.example'), format='json'
        )

        # Indistinguishable from success, so the bot has nothing to adapt to.
        self.assertEqual(response.status_code, 201)
        self.assertFalse(ContactMessage.objects.exists())

    def test_honeypot_is_never_echoed_back(self):
        response = self.client.post(self.url, self.payload(), format='json')

        self.assertNotIn('website', response.data)

    def test_rate_limit_applies_per_client(self):
        for _ in range(5):
            self.assertEqual(
                self.client.post(self.url, self.payload(), format='json').status_code, 201
            )

        blocked = self.client.post(self.url, self.payload(), format='json')

        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(ContactMessage.objects.count(), 5)


def token_from(message, path):
    url = re.search(rf'{re.escape(path)}\?token=\S+', message.body).group(0)
    return parse_qs(urlparse(url).query)['token'][0]


class NewsletterSubscriptionTests(APITestCase):
    def setUp(self):
        cache.clear()

    def subscribe(self, email='reader@example.com', **extra):
        return self.client.post(reverse('newsletter'), {'email': email, **extra}, format='json')

    def confirm(self, token):
        return self.client.post(reverse('newsletter-confirm'), {'token': token}, format='json')

    def subscribe_and_confirm(self, email='reader@example.com'):
        self.subscribe(email)
        self.confirm(token_from(mail.outbox[-1], '/newsletter/confirm'))
        return Newsletter.objects.get(email=email)

    def test_signing_up_sends_a_confirmation_and_nothing_more(self):
        response = self.subscribe()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['reader@example.com'])
        self.assertIn('/newsletter/confirm?token=', mail.outbox[0].body)
        self.assertFalse(Newsletter.objects.get().is_receiving)

    def test_confirmation_link_starts_the_subscription(self):
        subscriber = self.subscribe_and_confirm()

        self.assertTrue(subscriber.is_receiving)

    def test_response_is_the_same_for_new_pending_and_confirmed_addresses(self):
        new = self.subscribe('new@example.com')
        self.subscribe_and_confirm('confirmed@example.com')
        confirmed = self.subscribe('confirmed@example.com')
        pending = self.subscribe('new@example.com')

        self.assertEqual(new.data, confirmed.data)
        self.assertEqual(new.data, pending.data)

    def test_confirmed_address_is_not_emailed_again(self):
        self.subscribe_and_confirm()
        mail.outbox.clear()

        self.subscribe()

        self.assertEqual(mail.outbox, [])

    def test_repeat_signups_for_one_address_are_cooled_down(self):
        self.subscribe()
        self.subscribe()
        self.assertEqual(len(mail.outbox), 1)

        Newsletter.objects.update(confirmation_sent_at=timezone.now() - timedelta(minutes=16))
        self.subscribe()
        self.assertEqual(len(mail.outbox), 2)

    def test_only_the_latest_confirmation_link_works(self):
        self.subscribe()
        first = token_from(mail.outbox[0], '/newsletter/confirm')
        Newsletter.objects.update(confirmation_sent_at=timezone.now() - timedelta(minutes=16))
        self.subscribe()

        self.assertEqual(self.confirm(first).status_code, 400)
        self.assertEqual(self.confirm(token_from(mail.outbox[1], '/newsletter/confirm')).status_code, 200)

    @override_settings(NEWSLETTER_CONFIRMATION_MAX_AGE=timedelta(seconds=-1))
    def test_expired_confirmation_link_is_refused(self):
        self.subscribe()

        response = self.confirm(token_from(mail.outbox[0], '/newsletter/confirm'))

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Newsletter.objects.get().is_receiving)

    def test_forged_confirmation_token_is_refused(self):
        self.subscribe()
        token = token_from(mail.outbox[0], '/newsletter/confirm')

        self.assertEqual(self.confirm(token[:-2] + 'xx').status_code, 400)
        self.assertEqual(self.confirm('not-a-token').status_code, 400)

    @override_settings(NEWSLETTER_CONFIRMATIONS_PER_HOUR=2)
    def test_confirmation_emails_are_capped_across_all_addresses(self):
        for index in range(3):
            self.client.credentials(REMOTE_ADDR=f'10.0.0.{index}')
            self.assertEqual(self.subscribe(f'reader{index}@example.com').status_code, 200)

        self.assertEqual(len(mail.outbox), 2)

    def test_honeypot_signup_is_answered_but_ignored(self):
        response = self.subscribe(website='http://spam.example')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Newsletter.objects.exists())
        self.assertEqual(mail.outbox, [])

    def test_signups_are_rate_limited_per_client(self):
        for index in range(5):
            self.assertEqual(self.subscribe(f'reader{index}@example.com').status_code, 200)

        self.assertEqual(self.subscribe('late@example.com').status_code, 429)

    def test_confirmation_failure_does_not_start_the_cooldown(self):
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=OSError):
            self.assertEqual(self.subscribe().status_code, 200)

        self.assertIsNone(Newsletter.objects.get().confirmation_sent_at)
        self.subscribe()
        self.assertEqual(len(mail.outbox), 1)

    def test_unsubscribe_link_stops_mail(self):
        subscriber = self.subscribe_and_confirm()

        response = self.client.post(
            reverse('newsletter-unsubscribe'), {'token': subscriber.unsubscribe_token}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_receiving)
        self.assertIsNotNone(subscriber.unsubscribed_at)

    def test_one_click_unsubscribe_from_mail_client(self):
        subscriber = self.subscribe_and_confirm()

        # RFC 8058: form-encoded body, token in the List-Unsubscribe URL.
        response = self.client.post(
            f"{reverse('newsletter-unsubscribe')}?token={subscriber.unsubscribe_token}",
            'List-Unsubscribe=One-Click',
            content_type='application/x-www-form-urlencoded',
        )

        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_active)

    def test_unsubscribe_ignores_a_stale_login_token(self):
        subscriber = self.subscribe_and_confirm()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer expired.or.garbage')

        response = self.client.post(
            reverse('newsletter-unsubscribe'), {'token': subscriber.unsubscribe_token}, format='json'
        )

        self.assertEqual(response.status_code, 200)

    def test_opening_the_unsubscribe_url_does_not_unsubscribe(self):
        subscriber = self.subscribe_and_confirm()

        response = self.client.get(
            f"{reverse('newsletter-unsubscribe')}?token={subscriber.unsubscribe_token}"
        )

        self.assertEqual(response.status_code, 405)
        subscriber.refresh_from_db()
        self.assertTrue(subscriber.is_receiving)

    def test_unknown_unsubscribe_token_is_refused(self):
        response = self.client.post(
            reverse('newsletter-unsubscribe'), {'token': 'nope'}, format='json'
        )

        self.assertEqual(response.status_code, 400)

    def test_resubscribing_after_unsubscribing_needs_a_new_confirmation(self):
        subscriber = self.subscribe_and_confirm()
        newsletter.unsubscribe(subscriber.unsubscribe_token)
        mail.outbox.clear()

        self.subscribe()

        subscriber.refresh_from_db()
        self.assertTrue(subscriber.is_active)
        self.assertFalse(subscriber.is_receiving)
        self.assertEqual(len(mail.outbox), 1)

    def test_unsubscribing_voids_an_outstanding_confirmation_link(self):
        self.subscribe()
        token = token_from(mail.outbox[0], '/newsletter/confirm')
        newsletter.unsubscribe(Newsletter.objects.get().unsubscribe_token)

        self.assertEqual(self.confirm(token).status_code, 400)
        self.assertFalse(Newsletter.objects.get().is_active)


class NewsletterSendingTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='author', password='safe-password')
        self.reader = Newsletter.objects.create(email='reader@example.com', confirmed_at=timezone.now())
        Newsletter.objects.create(email='pending@example.com')
        Newsletter.objects.create(
            email='gone@example.com', confirmed_at=timezone.now(), is_active=False
        )

    def publish(self, title='Fresh post', **fields):
        fields.setdefault('status', 'published')
        fields.setdefault('published_at', timezone.now())
        return Post.objects.create(title=title, author=self.author, content='Body', **fields)

    def test_new_post_goes_only_to_confirmed_active_subscribers(self):
        post = self.publish()

        sent = newsletter.send_new_posts()

        self.assertEqual(sent, 1)
        self.assertEqual([message.to for message in mail.outbox], [['reader@example.com']])
        self.assertIn(f'/posts/{post.slug}', mail.outbox[0].body)
        post.refresh_from_db()
        self.assertIsNotNone(post.newsletter_sent_at)

    def test_post_email_carries_unsubscribe_link_and_one_click_headers(self):
        self.publish()

        newsletter.send_new_posts()

        message = mail.outbox[0]
        token = self.reader.unsubscribe_token
        self.assertIn(f'/newsletter/unsubscribe?token={token}', message.body)
        self.assertIn(f'/api/blog/newsletter/unsubscribe/?token={token}', message.extra_headers['List-Unsubscribe'])
        self.assertEqual(message.extra_headers['List-Unsubscribe-Post'], 'List-Unsubscribe=One-Click')

    def test_a_post_is_only_ever_sent_once(self):
        self.publish()

        newsletter.send_new_posts()
        newsletter.send_new_posts()

        self.assertEqual(len(mail.outbox), 1)

    def test_drafts_scheduled_and_old_posts_are_not_sent(self):
        self.publish('Draft', status='draft')
        self.publish('Scheduled', published_at=timezone.now() + timedelta(days=1))
        old = self.publish('Old', published_at=timezone.now() - timedelta(days=30))

        self.assertEqual(newsletter.send_new_posts(), 0)

        old.refresh_from_db()
        self.assertIsNotNone(old.newsletter_sent_at)
        self.assertEqual(mail.outbox, [])

    @override_settings(NEWSLETTER_DAILY_SEND_LIMIT=2)
    def test_daily_limit_pauses_and_a_later_run_resumes(self):
        for index in range(3):
            Newsletter.objects.create(email=f'extra{index}@example.com', confirmed_at=timezone.now())
        post = self.publish()

        self.assertEqual(newsletter.send_new_posts(), 2)
        post.refresh_from_db()
        self.assertIsNone(post.newsletter_sent_at)

        NewsletterDelivery.objects.update(sent_at=timezone.now() - timedelta(days=2))
        self.assertEqual(newsletter.send_new_posts(), 2)

        self.assertEqual(len({tuple(message.to) for message in mail.outbox}), 4)
        post.refresh_from_db()
        self.assertIsNotNone(post.newsletter_sent_at)

    def test_failed_send_is_retried_on_the_next_run(self):
        self.publish()

        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=OSError):
            with self.assertRaises(OSError):
                newsletter.send_new_posts()
        self.assertFalse(NewsletterDelivery.objects.exists())

        self.assertEqual(newsletter.send_new_posts(), 1)

    def test_dry_run_sends_and_records_nothing(self):
        post = self.publish()

        newsletter.send_new_posts(dry_run=True, log=lambda line: None)

        self.assertEqual(mail.outbox, [])
        self.assertFalse(NewsletterDelivery.objects.exists())
        post.refresh_from_db()
        self.assertIsNone(post.newsletter_sent_at)

    def test_post_title_is_escaped_in_the_html_email(self):
        self.publish('<script>alert(1)</script>')

        newsletter.send_new_posts()

        html = mail.outbox[0].alternatives[0][0]
        self.assertNotIn('<script>alert(1)', html)
        self.assertIn('&lt;script&gt;', html)

    @override_settings(DEBUG=False, EMAIL_HOST='')
    def test_command_refuses_to_run_without_smtp_in_production(self):
        post = self.publish()
        stderr = StringIO()

        call_command('send_newsletter', stdout=StringIO(), stderr=stderr)

        self.assertIn('not configured', stderr.getvalue())
        post.refresh_from_db()
        self.assertIsNone(post.newsletter_sent_at)


class ContactNotificationTests(APITestCase):
    def setUp(self):
        cache.clear()

    def send(self, **overrides):
        data = {
            'name': 'Reader',
            'email': 'reader@example.com',
            'subject': 'Collaboration',
            'message': 'I would like to talk about a security assessment.',
            **overrides,
        }
        return self.client.post(reverse('contact'), data, format='json')

    @override_settings(CONTACT_NOTIFY_EMAIL='owner@example.com')
    def test_message_is_forwarded_with_reply_to_the_sender(self):
        self.send()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['owner@example.com'])
        self.assertEqual(mail.outbox[0].reply_to, ['reader@example.com'])
        self.assertIn('security assessment', mail.outbox[0].body)

    @override_settings(CONTACT_NOTIFY_EMAIL='owner@example.com')
    def test_honeypot_message_is_not_forwarded(self):
        self.send(website='http://spam.example')

        self.assertEqual(mail.outbox, [])

    @override_settings(CONTACT_NOTIFY_EMAIL='owner@example.com')
    def test_mail_failure_still_stores_the_message(self):
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=OSError):
            response = self.send()

        self.assertEqual(response.status_code, 201)
        self.assertTrue(ContactMessage.objects.exists())

    @override_settings(CONTACT_NOTIFY_EMAIL='')
    def test_nothing_is_sent_without_a_notify_address(self):
        self.send()

        self.assertEqual(mail.outbox, [])
