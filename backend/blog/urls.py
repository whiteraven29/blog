from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('tags/', views.TagListView.as_view(), name='tag-list'),
    # fixed-segment routes must come before <slug> patterns
    path('posts/', views.PostListView.as_view(), name='post-list'),
    path('posts/featured/', views.FeaturedPostsView.as_view(), name='post-featured'),
    path('posts/create/', views.PostCreateView.as_view(), name='post-create'),
    path('posts/mine/', views.MyPostsView.as_view(), name='my-posts'),
    path('posts/<slug:slug>/', views.PostDetailView.as_view(), name='post-detail'),
    path('posts/<slug:slug>/comments/', views.CommentCreateView.as_view(), name='comment-create'),
    path('posts/<slug:slug>/edit/', views.PostUpdateView.as_view(), name='post-update'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('newsletter/', views.newsletter_subscribe, name='newsletter'),
    path('stats/', views.StatsView.as_view(), name='stats'),
]
