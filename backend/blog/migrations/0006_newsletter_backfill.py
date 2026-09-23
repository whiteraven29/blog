import secrets

from django.db import migrations
from django.utils import timezone


def backfill(apps, schema_editor):
    Post = apps.get_model('blog', 'Post')
    Newsletter = apps.get_model('blog', 'Newsletter')

    # Everything already published predates the newsletter. Without this, the
    # first send_newsletter run would email subscribers about every old post.
    Post.objects.filter(status='published').update(newsletter_sent_at=timezone.now())

    for subscriber in Newsletter.objects.filter(unsubscribe_token__isnull=True):
        subscriber.unsubscribe_token = secrets.token_urlsafe(32)
        subscriber.save(update_fields=['unsubscribe_token'])
    # Existing subscribers stay unconfirmed: they signed up before confirmation
    # existed. "Resend confirmation email" in the admin invites them to opt in.


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_newsletter_double_opt_in'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
