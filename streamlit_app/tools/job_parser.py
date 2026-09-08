"""Parse job description files (TXT/PDF) to raw text."""
from __future__ import annotations
from .resume_parser import parse_pdf, parse_txt


def parse_job_file(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return parse_pdf(data)
    return parse_txt(data)
