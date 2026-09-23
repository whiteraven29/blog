from django.contrib import admin, messages
from django.utils import timezone

from . import newsletter
from .models import Category, Tag, Post, Comment, ContactMessage, Newsletter, NewsletterDelivery


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
    readonly_fields = ['newsletter_sent_at']
    actions = ['skip_newsletter']

    @admin.action(description="Don't email subscribers about selected posts")
    def skip_newsletter(self, request, queryset):
        count = queryset.filter(newsletter_sent_at__isnull=True).update(newsletter_sent_at=timezone.now())
        self.message_user(request, f'{count} post(s) will not be emailed to subscribers.')


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


class SubscriberStatusFilter(admin.SimpleListFilter):
    title = 'status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [('receiving', 'Receiving'), ('pending', 'Awaiting confirmation'), ('unsubscribed', 'Unsubscribed')]

    def queryset(self, request, queryset):
        if self.value() == 'receiving':
            return queryset.receiving()
        if self.value() == 'pending':
            return queryset.filter(is_active=True, confirmed_at__isnull=True)
        if self.value() == 'unsubscribed':
            return queryset.filter(is_active=False)
        return queryset


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'status', 'subscribed_at', 'confirmed_at']
    list_filter = [SubscriberStatusFilter]
    search_fields = ['email']
    # State changes go through the actions, which keep the fields consistent.
    readonly_fields = ['email', 'is_active', 'subscribed_at', 'confirmed_at', 'confirmation_sent_at', 'unsubscribed_at']
    actions = ['resend_confirmation', 'unsubscribe']

    def has_add_permission(self, request):
        # Everyone on the list has to have opted in themselves.
        return False

    @admin.display(description='Status')
    def status(self, obj):
        if not obj.is_active:
            return 'Unsubscribed'
        return 'Receiving' if obj.confirmed_at else 'Awaiting confirmation'

    @admin.action(description='Resend confirmation email')
    def resend_confirmation(self, request, queryset):
        sent = sum(
            newsletter.send_confirmation(subscriber, ignore_cooldown=True)
            for subscriber in queryset.filter(is_active=True, confirmed_at__isnull=True)
        )
        level = messages.SUCCESS if sent else messages.WARNING
        self.message_user(
            request,
            f'Sent {sent} confirmation email(s). Confirmed and unsubscribed addresses are skipped, '
            'as is anything over the hourly confirmation cap.',
            level,
        )

    @admin.action(description='Unsubscribe selected addresses')
    def unsubscribe(self, request, queryset):
        count = queryset.filter(is_active=True).update(
            is_active=False, unsubscribed_at=timezone.now(), confirmation_sent_at=None
        )
        self.message_user(request, f'Unsubscribed {count} address(es).')


@admin.register(NewsletterDelivery)
class NewsletterDeliveryAdmin(admin.ModelAdmin):
    list_display = ['post', 'subscriber', 'sent_at']
    list_filter = ['post']
    search_fields = ['subscriber__email', 'post__title']

    # A log: rows are written by send_newsletter and never edited by hand.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


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
