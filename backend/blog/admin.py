from django.contrib import admin
from .models import Category, Tag, Post, Comment, ContactMessage, Newsletter


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'difficulty', 'is_featured', 'views', 'published_at']
    list_filter = ['status', 'difficulty', 'is_featured', 'category']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    filter_horizontal = ['tags']
    date_hierarchy = 'published_at'
    ordering = ['-created_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'post', 'is_approved', 'created_at']
    list_filter = ['is_approved']
    actions = ['approve_comments', 'hide_comments']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = 'Show selected comments'

    def hide_comments(self, request, queryset):
        queryset.update(is_approved=False)
    hide_comments.short_description = 'Hide selected comments'


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at', 'is_active']
    list_filter = ['is_active']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'name', 'email', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    # An inbox, not a draft: the submitted text is never edited in place.
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at']
    actions = ['mark_read', 'mark_unread']

    @admin.action(description='Mark selected messages as read')
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description='Mark selected messages as unread')
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)
