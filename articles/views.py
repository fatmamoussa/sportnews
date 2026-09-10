from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings

from .models import Article, Comment
from .forms import CommentForm, ArticleForm, SignUpForm


def is_author(user):
    """Seuls les comptes 'auteur' (is_staff) accèdent au tableau de bord —
    les comptes visiteurs créés pour commenter n'y ont jamais accès."""
    return user.is_authenticated and user.is_staff


def article_list(request):
    articles_qs = Article.objects.filter(status="published").exclude(slug="")

    query = request.GET.get("q", "").strip()
    if query:
        articles_qs = articles_qs.filter(
            Q(title__icontains=query) | Q(content__icontains=query) | Q(subtitle__icontains=query)
        )

    featured = articles_qs.filter(is_featured=True).first()
    others = articles_qs.exclude(pk=featured.pk) if featured else articles_qs

    paginator = Paginator(others, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "featured": featured,
        "page_obj": page_obj,
        "query": query,
    }
    return render(request, "articles/article_list.html", context)


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, status="published")
    comments = article.comments.filter(is_approved=True)

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.info(request, "Connectez-vous ou créez un compte pour commenter.")
            return redirect(f"{reverse('login')}?next={article.get_absolute_url()}")

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.user = request.user
            comment.name = request.user.username
            comment.email = request.user.email
            comment.save()
            messages.success(request, "Votre commentaire a été publié.")
            return redirect(article.get_absolute_url())
    else:
        form = CommentForm()

    related = Article.objects.filter(
        status="published", category=article.category
    ).exclude(pk=article.pk).exclude(slug="")[:3]

    context = {
        "article": article,
        "comments": comments,
        "form": form,
        "related": related,
    }
    return render(request, "articles/article_detail.html", context)


# --- Inscription des visiteurs (pour pouvoir commenter) ---

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_confirmation_email(request, user)
            return render(request, "registration/check_email.html", {"email": user.email})
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


def _send_confirmation_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    confirm_path = reverse("confirm_email", kwargs={"uidb64": uid, "token": token})
    confirm_url = request.build_absolute_uri(confirm_path)

    subject = "Confirmez votre compte SportNews Live"
    message = (
        f"Bonjour {user.username},\n\n"
        f"Cliquez sur ce lien pour confirmer votre email et activer votre compte :\n"
        f"{confirm_url}\n\n"
        f"Si vous n'êtes pas à l'origine de cette inscription, ignorez cet email."
    )

    if settings.MAILJET_API_KEY and settings.MAILJET_API_SECRET:
        from mailjet_rest import Client
        mailjet = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET), version="v3.1")
        data = {
            "Messages": [{
                "From": {
                    "Email": settings.MAILJET_FROM_EMAIL,
                    "Name": settings.MAILJET_FROM_NAME,
                },
                "To": [{"Email": user.email}],
                "Subject": subject,
                "TextPart": message,
            }]
        }
        result = mailjet.send.create(data=data)
        if result.status_code != 200:
            raise Exception(f"Mailjet a refusé l'envoi : {result.status_code} — {result.json()}")
    elif settings.RESEND_API_KEY:
        import resend
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": [user.email],
            "subject": subject,
            "text": message,
        })
    else:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


def confirm_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        auth_login(request, user)
        messages.success(request, "Votre compte est confirmé. Vous pouvez maintenant commenter !")
        return redirect("articles:list")

    return render(request, "registration/confirm_invalid.html")


# --- Espace journaliste (réservé aux comptes auteur, is_staff) ---

@user_passes_test(is_author, login_url="login")
def dashboard(request):
    articles = Article.objects.all().order_by("-created_at")
    return render(request, "articles/dashboard.html", {"articles": articles})


@user_passes_test(is_author, login_url="login")
def article_create(request):
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save()
            messages.success(request, "Article publié avec succès.")
            return redirect("articles:dashboard")
    else:
        form = ArticleForm()
    return render(request, "articles/article_form.html", {"form": form, "is_edit": False})


@user_passes_test(is_author, login_url="login")
def article_update(request, slug):
    article = get_object_or_404(Article, slug=slug)
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "Article mis à jour.")
            return redirect("articles:dashboard")
    else:
        form = ArticleForm(instance=article)
    return render(request, "articles/article_form.html", {"form": form, "is_edit": True, "article": article})


@user_passes_test(is_author, login_url="login")
def article_delete(request, slug):
    article = get_object_or_404(Article, slug=slug)
    if request.method == "POST":
        article.delete()
        messages.success(request, "Article supprimé.")
        return redirect("articles:dashboard")
    return render(request, "articles/article_confirm_delete.html", {"article": article})


# --- Gestion des commentaires ---

def _can_manage_comment(request, comment):
    """Le journaliste (compte auteur) peut tout supprimer ; le titulaire
    du compte qui a écrit le commentaire peut gérer le sien."""
    if request.user.is_authenticated and request.user.is_staff:
        return True
    return request.user.is_authenticated and comment.user_id == request.user.id


def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    # Seul le titulaire du compte auteur du commentaire peut le modifier (pas le journaliste)
    if not (request.user.is_authenticated and comment.user_id == request.user.id):
        messages.error(request, "Vous ne pouvez modifier que vos propres commentaires.")
        return redirect(comment.article.get_absolute_url())

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, "Commentaire modifié.")
            return redirect(comment.article.get_absolute_url())
    else:
        form = CommentForm(instance=comment)

    return render(request, "articles/comment_edit.html", {"form": form, "comment": comment})


def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if not _can_manage_comment(request, comment):
        messages.error(request, "Vous n'avez pas le droit de supprimer ce commentaire.")
        return redirect(comment.article.get_absolute_url())

    article_url = comment.article.get_absolute_url()
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Commentaire supprimé.")
        return redirect(article_url)
    return render(request, "articles/comment_confirm_delete.html", {"comment": comment})


# --- Choix de la langue du site ---

def set_language(request, lang_code):
    from .translations import STRINGS
    if lang_code in STRINGS:
        request.session["site_lang"] = lang_code
    next_url = request.META.get("HTTP_REFERER") or "/"
    return redirect(next_url)


# --- Page d'erreur CSRF personnalisée (session expirée) ---

def csrf_failure(request, reason=""):
    return render(request, "403_csrf.html", status=403)
