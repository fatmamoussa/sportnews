from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
import uuid


class Article(models.Model):
    STATUS_CHOICES = (
        ("draft", "Brouillon"),
        ("published", "Publié"),
    )

    title = models.CharField("Titre", max_length=250)
    slug = models.SlugField("Slug", max_length=270, unique=True, blank=True)
    subtitle = models.CharField("Sous-titre", max_length=300, blank=True)
    content = models.TextField("Contenu")
    category = models.CharField("Catégorie", max_length=50, default="Sportif")

    cover_image = models.ImageField(
        "Image de couverture", upload_to="articles/images/", blank=True, null=True
    )
    video = models.FileField(
        "Vidéo", upload_to="articles/videos/", blank=True, null=True
    )
    video_url = models.URLField(
        "Lien vidéo (YouTube/externe)", blank=True,
        help_text="Optionnel : lien vers une vidéo hébergée ailleurs (YouTube, etc.)"
    )

    is_featured = models.BooleanField("À la une", default=False)
    status = models.CharField(
        "Statut", max_length=10, choices=STATUS_CHOICES, default="published"
    )

    published_at = models.DateTimeField("Publié le", default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True)[:250]
            if not base_slug:
                # Filet de sécurité : titre sans aucun caractère "sluggable"
                # (que des emojis/symboles, etc.)
                base_slug = f"article-{uuid.uuid4().hex[:8]}"
            slug = base_slug
            i = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("articles:detail", kwargs={"slug": self.slug})

    @property
    def comment_count(self):
        return self.comments.filter(is_approved=True).count()


class Comment(models.Model):
    article = models.ForeignKey(
        Article, related_name="comments", on_delete=models.CASCADE, verbose_name="Article"
    )
    user = models.ForeignKey(
        "auth.User", related_name="comments", on_delete=models.CASCADE,
        verbose_name="Compte", null=True, blank=True
    )
    name = models.CharField("Nom", max_length=100)
    email = models.EmailField("Email")
    content = models.TextField("Commentaire")
    is_approved = models.BooleanField("Approuvé", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"

    def __str__(self):
        return f"Commentaire de {self.name} sur {self.article}"
