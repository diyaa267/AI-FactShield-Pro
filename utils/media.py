"""Multimodal extraction helpers. Optional dependencies fail gracefully."""
from pathlib import Path
import os


def extract_pdf_text(path):
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception as exc:
        return f"PDF extraction failed: {exc}"


def extract_image_text(path):
    try:
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(path), lang="eng+hin+guj").strip()
    except Exception:
        try:
            import pytesseract
            from PIL import Image
            return pytesseract.image_to_string(Image.open(path)).strip()
        except Exception:
            return ""


def extract_video_text(path):
    """Extract OCR text from representative frames when OpenCV + Tesseract exist."""
    try:
        import cv2
        import pytesseract
        cap = cv2.VideoCapture(str(path))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 25)
        duration = total / fps if fps else 0
        points = [0, duration * .25, duration * .5, duration * .75] if duration else [0]
        texts = []
        for sec in points:
            cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
            ok, frame = cap.read()
            if ok:
                text = pytesseract.image_to_string(frame).strip()
                if text:
                    texts.append(text)
        cap.release()
        return "\n".join(texts)
    except Exception:
        return ""


def extract_audio_text(path):
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(str(path)) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except Exception:
        return ""
