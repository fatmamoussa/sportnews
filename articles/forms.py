from django import forms
from django.contrib.auth.models import User
from .models import Comment, Article


INPUT_CLASS = "w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-brand"
INPUT_CLASS_RED = "w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-red-600"


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            "title", "subtitle", "content", "cover_image",
            "video", "video_url", "is_featured", "status",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Titre de l'article"}),
            "subtitle": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Sous-titre (optionnel)"}),
            "content": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 12, "placeholder": "Contenu de l'article..."}),
            "cover_image": forms.ClearableFileInput(attrs={"class": "block w-full text-sm text-gray-600"}),
            "video": forms.ClearableFileInput(attrs={"class": "block w-full text-sm text-gray-600"}),
            "video_url": forms.URLInput(attrs={"class": INPUT_CLASS, "placeholder": "https://..."}),
            "is_featured": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-brand rounded"}),
            "status": forms.Select(attrs={"class": INPUT_CLASS}),
        }


class CommentForm(forms.ModelForm):
    """Utilisé uniquement pour le contenu : le nom/email viennent du compte connecté."""
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={
                "class": INPUT_CLASS,
                "placeholder": "Votre commentaire",
                "rows": 4,
            }),
        }


class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe", widget=forms.PasswordInput(attrs={"class": INPUT_CLASS})
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe", widget=forms.PasswordInput(attrs={"class": INPUT_CLASS})
    )

    class Meta:
        model = User
        fields = ["username", "email"]
        widgets = {
            "username": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Nom d'utilisateur"}),
            "email": forms.EmailInput(attrs={"class": INPUT_CLASS, "placeholder": "Votre email"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un compte existe déjà avec cet email.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        if p1 and len(p1) < 8:
            raise forms.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False  # activé après confirmation email
        user.is_staff = False   # jamais accès dashboard pour un simple commentateur
        if commit:
            user.save()
        return user
