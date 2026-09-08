"""Parse resume files (PDF/DOCX/TXT) into raw text."""
from __future__ import annotations
import io
from typing import Optional


def parse_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception:  # pragma: no cover
        return ""
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(pages).strip()
    except Exception:
        return ""


def parse_docx(data: bytes) -> str:
    try:
        import docx  # python-docx
    except Exception:  # pragma: no cover
        return ""
    try:
        doc = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs).strip()
    except Exception:
        return ""


def parse_txt(data: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return data.decode(enc).strip()
        except Exception:
            continue
    return ""


def parse_resume(filename: str, data: bytes) -> str:
    """Parse a resume file based on extension, returning raw text (may be empty)."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return parse_pdf(data)
    if name.endswith(".docx"):
        return parse_docx(data)
    if name.endswith(".txt"):
        return parse_txt(data)
    # Try heuristically
    text = parse_pdf(data)
    if text:
        return text
    text = parse_docx(data)
    if text:
        return text
    return parse_txt(data)


def is_scanned_pdf(filename: str, data: bytes) -> bool:
    if not filename.lower().endswith(".pdf"):
        return False
    return len(parse_pdf(data)) < 30
