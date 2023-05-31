from django.contrib import admin
from .models import Follow


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Админка подписчика."""

    list_display = ("user", "author")
    list_filter = ("user", "author")
    search_fields = ("user", "author")
