"""
Document parser for Contract Reviewer.
Handles PDF, DOCX, images (OCR), and plain text files.
"""

import io


def parse_uploaded_file(uploaded_file) -> str:
    """Parse an uploaded file and return its text content."""
    name = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()

    # --- PDF ---
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
            if text:
                return text
        except Exception:
            pass

        # pypdf returned nothing — try OCR
        try:
            from PIL import Image
            import pytesseract
            try:
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(raw, first_page=1, last_page=20)
                ocr_parts = [pytesseract.image_to_string(img) for img in images]
                text = "\n".join(ocr_parts).strip()
                if text:
                    return text
            except ImportError:
                pass
        except ImportError:
            pass

        return "[PDF text extraction returned empty. This may be a scanned document — try exporting pages as images and uploading those.]"

    # --- DOCX ---
    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(io.BytesIO(raw))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except ImportError:
            return "[DOCX support requires python-docx — install it with: pip install python-docx]"
        except Exception as e:
            return f"[Error parsing DOCX: {str(e)[:150]}]"

    # --- Images (OCR) ---
    if name.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp")):
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(io.BytesIO(raw))
            text = pytesseract.image_to_string(img)
            return text.strip() if text.strip() else "[Image uploaded but no text detected by OCR]"
        except ImportError:
            return "[Image uploaded but OCR not available — install Tesseract]"
        except Exception as e:
            return f"[OCR error: {str(e)[:150]}]"

    # --- Text / fallback ---
    try:
        return raw.decode("utf-8", errors="replace")
    except Exception as e:
        return f"[Error reading {uploaded_file.name}: {str(e)[:150]}]"
