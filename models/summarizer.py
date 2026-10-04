def summarize(text, max_chars=180):
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars].rsplit(" ", 1)[0] + "..."
