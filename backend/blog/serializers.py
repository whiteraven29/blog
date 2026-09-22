import re

from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from .models import Category, Tag, Post, Comment, ContactMessage, Newsletter


# Control characters serve no purpose in form input. DRF's CharField already
# refuses NUL on its own — which matters, since PostgreSQL cannot store it in a
# text column at all — so this covers the rest, and NUL for any future caller
# that does not arrive through a CharField.
CONTROL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
LINK_RE = re.compile(r'https?://|www\.', re.IGNORECASE)
MAX_LINKS = 2


def clean_text(value, *, single_line):
    """Normalise submitted text to inert plain text.

    This is hygiene, not the XSS control. Injected markup cannot execute anyway:
    React escapes text nodes and the Django admin escapes its output. Stripping
    tags on the way in means the stored copy stays plain no matter where it is
    rendered later — an email notification, say, or a future template.
    """
    value = strip_tags(value)
    value = CONTROL_CHARS_RE.sub('', value)
    if single_line:
        # Collapsing whitespace also removes the CR/LF that would let a crafted
        # subject line inject extra headers into a notification email.
        return ' '.join(value.split())
    return value.strip()


COLOR_RE = r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$'


class CategorySerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()
    color = serializers.RegexField(
        COLOR_RE,
        required=False,
        error_messages={'invalid': 'Use a hex colour such as #a855f7.'},
    )

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'color', 'post_count', 'created_at']
        read_only_fields = ['slug', 'created_at']

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError('Name cannot be blank.')
        existing = Category.objects.filter(name__iexact=name)
        if self.instance is not None:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError('A category with this name already exists.')
        return name

    def get_post_count(self, obj):
        annotated_count = getattr(obj, 'published_post_count', None)
        if annotated_count is not None:
            return annotated_count
        return obj.posts.filter(status='published').count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class AuthorSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar', 'bio']

    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.profile.avatar.url) if request else obj.profile.avatar.url
        return None

    def get_bio(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.bio
        return ''


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'author_name', 'author_email', 'body', 'created_at']
        read_only_fields = ['created_at']
        extra_kwargs = {
            'author_name': {'required': False, 'allow_blank': True},
            'author_email': {'required': False, 'allow_blank': True, 'write_only': True},
        }


class PostListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = AuthorSerializer(read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'author', 'category', 'tags',
            'excerpt', 'cover_image', 'status', 'difficulty',
            'is_featured', 'views', 'read_time', 'published_at', 'created_at',
        ]

    def get_cover_image(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.cover_image.url) if request else obj.cover_image.url
        return None


class PostDetailSerializer(PostListSerializer):
    comments = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['content', 'comments', 'comment_count', 'updated_at']

    def _approved_comments(self, obj):
        # Filter in Python so the view's prefetch_related('comments') is reused
        # instead of issuing a fresh query per field.
        return [comment for comment in obj.comments.all() if comment.is_approved]

    def get_comments(self, obj):
        return CommentSerializer(self._approved_comments(obj), many=True).data

    def get_comment_count(self, obj):
        return len(self._approved_comments(obj))


class PostWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=False
    )
    # Accept tag names from the frontend editor (get-or-create)
    tags_by_name = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, write_only=True
    )
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'slug', 'title', 'category', 'tags', 'tags_by_name',
            'excerpt', 'content', 'cover_image', 'status',
            'difficulty', 'is_featured', 'read_time', 'published_at',
        ]

    def to_representation(self, instance):
        return PostDetailSerializer(instance, context=self.context).data

    def _resolve_tags(self, validated_data):
        tag_names = validated_data.pop('tags_by_name', None)
        tags = validated_data.pop('tags', None)
        if tag_names is not None:
            tags = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name.lower().strip())
                tags.append(tag)
        return tags

    def create(self, validated_data):
        from django.utils import timezone
        tags = self._resolve_tags(validated_data)
        if validated_data.get('status') == 'published' and not validated_data.get('published_at'):
            validated_data['published_at'] = timezone.now()
        post = Post.objects.create(**validated_data)
        if tags is not None:
            post.tags.set(tags)
        return post

    def update(self, instance, validated_data):
        from django.utils import timezone
        tags = self._resolve_tags(validated_data)
        if validated_data.get('status') == 'published' and not instance.published_at:
            validated_data['published_at'] = timezone.now()
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance


class NewsletterSerializer(serializers.ModelSerializer):
    # Uniqueness is resolved in the view so that resubscribing looks identical to
    # a first subscription; the default validator would report which addresses
    # are already on the list.
    email = serializers.EmailField(validators=[])

    class Meta:
        model = Newsletter
        fields = ['email']


class ContactMessageSerializer(serializers.ModelSerializer):
    # Bots fill in every field they find. A real browser leaves this one empty
    # because it is hidden, so anything here marks the submission as automated.
    website = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message', 'website']

    def validate_name(self, value):
        name = clean_text(value, single_line=True)
        if not name:
            raise serializers.ValidationError('Please tell me your name.')
        return name

    def validate_subject(self, value):
        subject = clean_text(value, single_line=True)
        if not subject:
            raise serializers.ValidationError('Please add a subject.')
        return subject

    def validate_message(self, value):
        message = clean_text(value, single_line=False)
        if len(message) < 10:
            raise serializers.ValidationError('Please write a little more.')
        if len(LINK_RE.findall(message)) > MAX_LINKS:
            raise serializers.ValidationError(
                'That is more links than this form accepts. Please describe them instead.'
            )
        return message

    def create(self, validated_data):
        validated_data.pop('website', None)
        return super().create(validated_data)
