import re


def clean_text(text: str) -> str:
    """Clean extracted document text."""

    # Replace multiple spaces with a single space
    text = re.sub(r"\s+", " ", text)

    # Remove leading and trailing spaces
    text = text.strip()

    return text


def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """Split text into smaller chunks."""

    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks