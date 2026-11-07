from pathlib import Path

import fitz
from docx import Document


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""

    text = ""

    with fitz.open(file_path) as pdf_document:
        for page in pdf_document:
            text += page.get_text()

    return text


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""

    document = Document(file_path)

    text = []

    for paragraph in document.paragraphs:
        text.append(paragraph.text)

    return "\n".join(text)


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from a TXT file."""

    with open(file_path, "rb") as file:
        content = file.read()

    if content.startswith((b"\xff\xfe", b"\xfe\xff")):
        return content.decode("utf-16")

    if content.startswith(b"\xef\xbb\xbf"):
        return content.decode("utf-8-sig")

    try:
        return content.decode("utf-8")

    except UnicodeDecodeError:
        return content.decode("cp1252")


def extract_text(file_path: str) -> str:
    """Extract text based on the document file type."""

    path_obj = Path(file_path)
    extension = path_obj.suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(str(path_obj))

    elif extension == ".docx":
        return extract_text_from_docx(str(path_obj))

    elif extension == ".txt":
        return extract_text_from_txt(str(path_obj))

    else:
        raise ValueError(
            f"Unsupported file type '{extension}'. "
            "Only PDF, DOCX, and TXT files are supported."
        )