import yaml
import re
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from blog.models import Post, Category, Tag


FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def parse_md(path: Path):
    raw = path.read_text(encoding='utf-8')
    m = FRONTMATTER_RE.match(raw)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        content = raw[m.end():]
    else:
        meta = {}
        content = raw
    return meta, content.strip()


class Command(BaseCommand):
    help = 'Import a Markdown file (with optional YAML frontmatter) as a blog post'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='Path to the .md file')
        parser.add_argument('--author', default='admin', help='Username of the post author (default: admin)')
        parser.add_argument('--publish', action='store_true', help='Set status to published immediately')
        parser.add_argument('--update', action='store_true', help='Update existing post if slug matches')

    def handle(self, *args, **options):
        path = Path(options['file'])
        if not path.exists():
            raise CommandError(f'File not found: {path}')

        try:
            author = User.objects.get(username=options['author'])
        except User.DoesNotExist:
            raise CommandError(f"User '{options['author']}' does not exist.")

        meta, content = parse_md(path)

        # ---- Title ----
        title = meta.get('title') or path.stem.replace('-', ' ').replace('_', ' ').title()

        # ---- Category ----
        category = None
        if cat_name := meta.get('category'):
            category, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={'color': '#a855f7'}
            )
            if created:
                self.stdout.write(self.style.WARNING(f"  Created new category: {cat_name}"))

        # ---- Tags ----
        tag_names = meta.get('tags') or []
        if isinstance(tag_names, str):
            tag_names = [t.strip() for t in tag_names.split(',')]
        tags = []
        for t in tag_names:
            tag, _ = Tag.objects.get_or_create(name=t.lower().strip())
            tags.append(tag)

        # ---- Status ----
        status = 'published' if options['publish'] else meta.get('status', 'draft')
        if status not in ('draft', 'published'):
            status = 'draft'

        # ---- Build fields ----
        fields = {
            'author': author,
            'category': category,
            'content': content,
            'excerpt': meta.get('excerpt', ''),
            'difficulty': meta.get('difficulty', 'beginner'),
            'status': status,
            'is_featured': bool(meta.get('featured', False)),
            'read_time': int(meta.get('read_time', max(1, len(content.split()) // 200))),
        }

        # ---- Create or update ----
        # `title` is not unique, so match the oldest post carrying it rather than
        # letting update_or_create() raise MultipleObjectsReturned.
        existing = Post.objects.filter(title=title).order_by('created_at').first()

        if existing and not options['update']:
            raise CommandError(
                f'A post titled "{title}" already exists. Use --update to overwrite it.'
            )

        if existing:
            for field, value in fields.items():
                setattr(existing, field, value)
            # Keep the original publication date; only stamp one on first publish.
            if status == 'published' and not existing.published_at:
                existing.published_at = timezone.now()
            elif status != 'published':
                existing.published_at = None
            existing.save()
            post, verb = existing, 'Updated'
        else:
            post = Post.objects.create(
                title=title,
                published_at=timezone.now() if status == 'published' else None,
                **fields,
            )
            verb = 'Created'

        post.tags.set(tags)

        self.stdout.write(self.style.SUCCESS(
            f"{verb} post: \"{post.title}\" [{post.status}] → slug: {post.slug}"
        ))
