from .translations import STRINGS, AVAILABLE_LANGUAGES


def site_language(request):
    lang = request.session.get("site_lang", "fr")
    if lang not in STRINGS:
        lang = "fr"
    return {
        "site_lang": lang,
        "site_dir": "rtl" if lang == "ar" else "ltr",
        "s": STRINGS[lang],
        "available_languages": AVAILABLE_LANGUAGES,
    }
