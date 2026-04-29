from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Tag, Post, Comment, Newsletter


class CategorySerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(source='posts.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'color', 'post_count', 'created_at']


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
    comment_count = serializers.IntegerField(source='comments.filter(is_approved=True).count', read_only=True)

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['content', 'comments', 'comment_count', 'updated_at']

    def get_comments(self, obj):
        approved = obj.comments.filter(is_approved=True)
        return CommentSerializer(approved, many=True).data


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
    class Meta:
        model = Newsletter
        fields = ['email']
