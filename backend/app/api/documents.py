import re
import uuid
import zipfile

from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.config import DOCUMENTS_DIR
from backend.app.services.document_service import extract_text
from backend.app.services.text_service import clean_text, chunk_text
from backend.app.services.embedding_service import generate_embedding
from backend.app.services.vector_service import (
    add_vectors,
    save_index,
    rebuild_index
)
from backend.app.services.metadata_service import (
    load_metadata,
    save_metadata
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_filename(filename: str) -> str:
    """Validate and sanitize uploaded filenames."""

    # Handle both Windows and Linux path separators
    filename = filename.replace("\\", "/").split("/")[-1]

    if not filename or filename.startswith("."):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename."
        )

    if len(filename) > 120:
        raise HTTPException(
            status_code=400,
            detail="Filename is too long."
        )

    if ".." in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename."
        )

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ -]*", filename):
        raise HTTPException(
            status_code=400,
            detail="Filename contains invalid characters."
        )

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX and TXT files are allowed."
        )

    return filename


def validate_file_content(file_path: Path, extension: str):
    """Validate actual file content."""

    if extension == ".pdf":

        with open(file_path, "rb") as file:
            signature = file.read(5)

        if signature != b"%PDF-":
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file."
            )

    elif extension == ".docx":

        try:
            with zipfile.ZipFile(file_path, "r") as archive:

                required_files = {
                    "[Content_Types].xml",
                    "word/document.xml"
                }

                if not required_files.issubset(set(archive.namelist())):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid DOCX document."
                    )

                if archive.testzip() is not None:
                    raise HTTPException(
                        status_code=400,
                        detail="DOCX file is corrupted."
                    )

        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=400,
                detail="Invalid DOCX file."
            )

    elif extension == ".txt":

        with open(file_path, "rb") as file:
            content = file.read()

        try:
            if content.startswith((b"\xff\xfe", b"\xfe\xff")):
                content.decode("utf-16")

            elif content.startswith(b"\xef\xbb\xbf"):
                content.decode("utf-8-sig")

            else:
                try:
                    content.decode("utf-8")
                except UnicodeDecodeError:
                    content.decode("cp1252")

        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid text file encoding."
            )


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required."
        )

    filename = validate_filename(file.filename)

    extension = Path(filename).suffix.lower()

    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    file_path = DOCUMENTS_DIR / filename

    # Prevent accidental overwriting
    if file_path.exists():
        raise HTTPException(
            status_code=409,
            detail="A document with this filename already exists."
        )

    # Create a temporary file with the correct extension
    temp_path = DOCUMENTS_DIR / (
        f".upload_{uuid.uuid4().hex}{extension}"
    )

    total_size = 0

    try:

        # Save upload temporarily and enforce size limit
        with open(temp_path, "wb") as buffer:

            while True:

                chunk = await file.read(64 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File size exceeds the 10 MB limit."
                    )

                buffer.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        # Validate actual file content
        validate_file_content(temp_path, extension)

        # Extract document text
        try:
            extracted_text = extract_text(str(temp_path))

        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Unable to read the uploaded document."
            )

        cleaned_text = clean_text(extracted_text)

        if not cleaned_text:
            raise HTTPException(
                status_code=400,
                detail="No readable text found in the document."
            )

        # Divide text into chunks
        chunks = chunk_text(cleaned_text)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Unable to generate document chunks."
            )

        # Generate embeddings
        try:
            embeddings = [
                generate_embedding(chunk)
                for chunk in chunks
            ]

        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Embedding generation failed."
            )

        # Load existing metadata
        metadata = load_metadata()

        # Move validated file to permanent storage
        temp_path.replace(file_path)

        try:

            # Rebuild existing FAISS index
            index = rebuild_index(metadata)

            starting_index = index.ntotal

            # Add new document embeddings
            add_vectors(index, embeddings)

            save_index(index)

            # Add new metadata records
            for position, chunk in enumerate(chunks):

                metadata.append({
                    "index": starting_index + position,
                    "filename": filename,
                    "filepath": str(file_path),
                    "chunk": chunk
                })

            save_metadata(metadata)

        except Exception:

            # Remove uploaded file if indexing fails
            if file_path.exists():
                file_path.unlink()

            # Restore the previous index from metadata
            try:
                rebuild_index(metadata)
            except Exception:
                pass

            raise HTTPException(
                status_code=500,
                detail="Document indexing failed. Please try again."
            )

        return {
            "filename": filename,
            "content_type": file.content_type,
            "text_length": len(cleaned_text),
            "chunk_count": len(chunks),
            "embedding_dimension": 384,
            "message": "Document uploaded and indexed successfully."
        }

    finally:

        # Remove temporary file if it still exists
        if temp_path.exists():
            temp_path.unlink()

        await file.close()


@router.get("/")
def list_documents():

    metadata = load_metadata()

    documents = {}

    for item in metadata:

        filename = item["filename"]

        if filename not in documents:
            documents[filename] = {
                "filename": filename,
                "chunk_count": 0
            }

        documents[filename]["chunk_count"] += 1

    return {
        "documents": list(documents.values())
    }



@router.delete("/{filename}")
def delete_document(filename: str):

    filename = Path(filename).name

    metadata = load_metadata()

    matching_documents = [
        item
        for item in metadata
        if item["filename"] == filename
    ]

    if not matching_documents:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    updated_metadata = [
        item
        for item in metadata
        if item["filename"] != filename
    ]

    rebuild_index(updated_metadata)

    save_metadata(updated_metadata)

    file_path = DOCUMENTS_DIR / filename

    if file_path.exists():
        file_path.unlink()

    return {
        "filename": filename,
        "message": "Document deleted successfully."
    }


@router.get("/{filename}/preview")
def preview_document(filename: str):

    filename = Path(filename).name

    file_path = DOCUMENTS_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    try:
        extracted_text = extract_text(str(file_path))

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read the document."
        )

    cleaned_text = clean_text(extracted_text)

    return {
        "filename": filename,
        "text": cleaned_text,
        "text_length": len(cleaned_text),
        "message": "Document preview retrieved successfully."
    }