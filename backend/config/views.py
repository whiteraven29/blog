from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils.html import escape
from blog.models import Post


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        return JsonResponse({'status': 'unhealthy'}, status=503)
    return JsonResponse({'status': 'ok'})


def sitemap(request):
    base_url = request.build_absolute_uri('/').rstrip('/')
    static_paths = ['', '/posts', '/categories', '/about', '/contact']
    urls = [f'<url><loc>{escape(base_url + path)}</loc></url>' for path in static_paths]
    urls.extend(
        f'<url><loc>{escape(base_url + "/posts/" + post.slug)}</loc>'
        f'<lastmod>{post.updated_at.date().isoformat()}</lastmod></url>'
        for post in Post.objects.filter(status='published').only('slug', 'updated_at')
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + ''.join(urls)
        + '</urlset>'
    )
    return HttpResponse(xml, content_type='application/xml')


def rss(request):
    base_url = request.build_absolute_uri('/').rstrip('/')
    feed = Rss201rev2Feed(
        title='wh1t3r4v3n Blog',
        link=base_url,
        description='Offensive security, CTF, web development, and programming writeups.',
        language='en',
    )
    posts = Post.objects.filter(status='published').select_related('author').order_by('-published_at')[:20]
    for post in posts:
        feed.add_item(
            title=post.title,
            link=f'{base_url}/posts/{post.slug}',
            description=post.excerpt,
            author_name=post.author.username,
            pubdate=post.published_at,
            unique_id=f'{base_url}/posts/{post.slug}',
        )
    return HttpResponse(feed.writeString('utf-8'), content_type='application/rss+xml; charset=utf-8')
