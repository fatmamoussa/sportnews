from django.contrib import admin
from .models import Article, Comment


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("name", "email", "content", "is_approved", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "is_featured", "published_at")
    list_filter = ("status", "is_featured", "category")
    search_fields = ("title", "subtitle", "content")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CommentInline]
    date_hierarchy = "published_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("name", "article", "is_approved", "created_at")
    list_filter = ("is_approved",)
    search_fields = ("name", "email", "content")
