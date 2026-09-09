class UnicodeSlugConverter:
    """
    Comme le convertisseur 'slug' standard de Django, mais accepte aussi
    les caractères Unicode (arabe, etc.) — nécessaire car nos slugs sont
    générés avec slugify(allow_unicode=True) pour les titres en arabe.
    """
    regex = r"[-\w]+"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
