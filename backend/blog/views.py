from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum
from .models import Category, Tag, Post, Comment, Newsletter
from .serializers import (
    CategorySerializer, TagSerializer, PostListSerializer,
    PostDetailSerializer, PostWriteSerializer, CommentSerializer,
    NewsletterSerializer,
)


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.annotate(
        published_post_count=Count('posts', filter=Q(posts__status='published')),
    ).order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.annotate(
        published_post_count=Count('posts', filter=Q(posts__status='published')),
    ).order_by('name')
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class PostListView(generics.ListAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug', 'tags__slug', 'difficulty', 'status', 'is_featured']
    search_fields = ['title', 'excerpt', 'content', 'tags__name', 'category__name']
    ordering_fields = ['published_at', 'views', 'created_at', 'read_time']
    ordering = ['-published_at']

    def get_queryset(self):
        qs = Post.objects.select_related('author', 'category').prefetch_related('tags')
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(status='published')
        return qs


class PostDetailView(generics.RetrieveAPIView):
    serializer_class = PostDetailSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Post.objects.select_related('author', 'category').prefetch_related('tags', 'comments')
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(status='published')
        return qs

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Post.objects.filter(pk=instance.pk).update(views=instance.views + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class PostCreateView(generics.CreateAPIView):
    serializer_class = PostWriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostUpdateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostWriteSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class MyPostsView(generics.ListAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ['-created_at']

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).select_related('category').prefetch_related('tags').order_by('-created_at')


class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        post = generics.get_object_or_404(Post, slug=self.kwargs['slug'], status='published')
        serializer.save(post=post)


class FeaturedPostsView(generics.ListAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Post.objects.filter(status='published', is_featured=True).order_by('-published_at')[:6]


class SearchView(generics.ListAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        q = self.request.query_params.get('q', '').strip()
        if not q:
            return Post.objects.none()
        return Post.objects.filter(
            Q(title__icontains=q) | Q(excerpt__icontains=q) |
            Q(content__icontains=q) | Q(tags__name__icontains=q) |
            Q(category__name__icontains=q),
            status='published',
        ).distinct().order_by('-published_at')


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def newsletter_subscribe(request):
    serializer = NewsletterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Subscribed successfully.'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        published = Post.objects.filter(status='published')
        return Response({
            'total_posts': published.count(),
            'total_categories': Category.objects.count(),
            'total_tags': Tag.objects.count(),
            'total_views': published.aggregate(total=Sum('views'))['total'] or 0,
        })
