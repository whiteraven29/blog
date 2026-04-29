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

        published_at = None
        if status == 'published':
            published_at = timezone.now()

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
            'published_at': published_at,
        }

        # ---- Create or update ----
        if options['update']:
            post, created = Post.objects.update_or_create(
                title=title,
                defaults=fields,
            )
            verb = 'Created' if created else 'Updated'
        else:
            if Post.objects.filter(title=title).exists():
                raise CommandError(
                    f'A post titled "{title}" already exists. Use --update to overwrite it.'
                )
            post = Post.objects.create(title=title, **fields)
            verb = 'Created'

        post.tags.set(tags)

        self.stdout.write(self.style.SUCCESS(
            f"{verb} post: \"{post.title}\" [{post.status}] → slug: {post.slug}"
        ))
