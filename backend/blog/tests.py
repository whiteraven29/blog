import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Category, Comment, Post, Tag


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
        self.assertEqual(response.data['results'][0]['post_count'], 1)

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
                'body': 'Pending review',
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

    def test_health_endpoint_checks_database(self):
        response = self.client.get(reverse('health'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'status': 'ok'})
