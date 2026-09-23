from django.conf import settings
from django.core.management.base import BaseCommand

from blog.newsletter import send_new_posts


class Command(BaseCommand):
    help = 'Email confirmed subscribers about newly published posts. Run on a timer.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report what would be sent without sending or recording anything.',
        )

    def handle(self, *args, dry_run=False, **options):
        if not settings.DEBUG and not settings.EMAIL_HOST and not dry_run:
            # Without SMTP the console backend would "send" into the journal and
            # mark every post as done. Leaving them pending means they go out
            # once email is configured.
            self.stderr.write('Email is not configured (DJANGO_EMAIL_HOST is empty); nothing sent.')
            return
        sent = send_new_posts(dry_run=dry_run, log=self.stdout.write)
        if not dry_run:
            self.stdout.write(f'Sent {sent} newsletter email(s).')
