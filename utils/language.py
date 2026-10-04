def language_label(text):
    if any("\u0A80" <= c <= "\u0AFF" for c in text):
        return "Gujarati"
    if any("\u0900" <= c <= "\u097F" for c in text):
        return "Hindi"
    return "English"
