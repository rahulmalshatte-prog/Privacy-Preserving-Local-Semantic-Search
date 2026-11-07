from pathlib import Path

from fastapi import APIRouter

from backend.app.services.embedding_service import generate_embedding
from backend.app.services.vector_service import load_index, search_vectors
from backend.app.services.metadata_service import load_metadata


router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


@router.get("/")
def search_documents(
    query: str,
    top_k: int = 5,
    document_type: str = "ALL"
):

    # Normalize document type
    document_type = document_type.upper()

    # Validate document type
    allowed_types = ["ALL", "PDF", "DOCX", "TXT"]

    if document_type not in allowed_types:
        return {
            "query": query,
            "document_type": document_type,
            "results": []
        }

    # Generate query embedding
    query_vector = generate_embedding(query)

    # Load FAISS index
    index = load_index()

    # Check whether index is empty
    if index.ntotal == 0:
        return {
            "query": query,
            "document_type": document_type,
            "results": []
        }

    # Search indexed vectors
    distances, indices = search_vectors(
        index,
        query_vector,
        index.ntotal
    )

    # Load metadata
    metadata = load_metadata()

    MAX_DISTANCE = 1.5

    results = []

    for distance, index_number in zip(distances, indices):

        if index_number == -1:
            continue

        if distance > MAX_DISTANCE:
            continue

        for item in metadata:

            if item["index"] == index_number:

                filename = item["filename"]

                current_type = (
                    Path(filename)
                    .suffix
                    .lower()
                    .replace(".", "")
                    .upper()
                )

                # Apply document type filter
                if document_type != "ALL" and current_type != document_type:
                    break

                # Calculate similarity percentage
                similarity = (1 - float(distance) / 2) * 100

                # Keep score between 0 and 100
                similarity = max(0, min(100, similarity))

                results.append({
                    "filename": filename,
                    "filepath": item["filepath"],
                    "document_type": current_type,
                    "chunk": item["chunk"],
                    "distance": float(distance),
                    "similarity_score": round(similarity, 2)
                })

                break

        if len(results) >= top_k:
            break

    # Count matching chunks per document
    matching_chunk_counts = {}

    for result in results:

        filename = result["filename"]

        matching_chunk_counts[filename] = (
            matching_chunk_counts.get(filename, 0) + 1
        )

    # Add matching chunk count
    for result in results:

        result["matching_chunk_count"] = (
            matching_chunk_counts[result["filename"]]
        )

    return {
        "query": query,
        "document_type": document_type,
        "results": results
    }