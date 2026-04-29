from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'github', 'twitter', 'website']
    search_fields = ['user__username', 'user__email']
