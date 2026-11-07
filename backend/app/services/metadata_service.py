import json
import os

from backend.app.config import INDEXES_DIR


METADATA_FILE = INDEXES_DIR / "document_metadata.json"


def save_metadata(metadata: list[dict]):
    """Save document metadata locally and safely."""

    INDEXES_DIR.mkdir(parents=True, exist_ok=True)

    temp_file = METADATA_FILE.with_suffix(".tmp")

    try:
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(
                metadata,
                file,
                indent=4,
                ensure_ascii=False
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_file, METADATA_FILE)

    finally:
        if temp_file.exists():
            temp_file.unlink()


def load_metadata() -> list[dict]:
    """Load document metadata from disk."""

    if not METADATA_FILE.exists():
        return []

    with open(METADATA_FILE, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    if not isinstance(metadata, list):
        raise ValueError("Invalid metadata format.")

    return metadata