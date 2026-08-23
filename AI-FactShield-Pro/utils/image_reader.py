def extract_text_from_image(path):
    try:
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(path))
    except Exception:
        return "OCR is not configured. Install Tesseract OCR and pytesseract to enable image text extraction."
