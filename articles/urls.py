from django.urls import path, register_converter
from . import views
from .converters import UnicodeSlugConverter

register_converter(UnicodeSlugConverter, "uslug")

app_name = "articles"

urlpatterns = [
    path("", views.article_list, name="list"),
    path("article/<uslug:slug>/", views.article_detail, name="detail"),

    # Commentaires
    path("commentaire/<int:comment_id>/modifier/", views.comment_edit, name="comment_edit"),
    path("commentaire/<int:comment_id>/supprimer/", views.comment_delete, name="comment_delete"),

    # Langue
    path("langue/<str:lang_code>/", views.set_language, name="set_language"),

    # Espace journaliste
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/nouveau/", views.article_create, name="create"),
    path("dashboard/<uslug:slug>/modifier/", views.article_update, name="update"),
    path("dashboard/<uslug:slug>/supprimer/", views.article_delete, name="delete"),
]
