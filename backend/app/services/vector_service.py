import faiss
import numpy as np

from backend.app.config import INDEXES_DIR

VECTOR_DIMENSION = 384

INDEX_FILE = INDEXES_DIR / "document_vectors.index"


def create_index():
    """Create a FAISS index for normalized vectors."""
    return faiss.IndexFlatL2(VECTOR_DIMENSION)


def add_vectors(index, vectors: list[list[float]]):
    """Add normalized embedding vectors to FAISS."""

    if not vectors:
        return index

    vector_array = np.array(vectors, dtype="float32")

    index.add(vector_array)

    return index


def search_vectors(index, query_vector: list[float], top_k: int = 3):
    """Search for the most similar vectors."""

    if index.ntotal == 0:
        return [], []

    query_array = np.array(
        [query_vector],
        dtype="float32"
    )

    k = min(top_k, index.ntotal)

    distances, indices = index.search(query_array, k)

    return distances[0].tolist(), indices[0].tolist()


def save_index(index):
    """Save the FAISS index locally."""

    INDEX_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    faiss.write_index(index, str(INDEX_FILE))


def load_index():
    """Load the saved FAISS index."""

    if INDEX_FILE.exists():
        return faiss.read_index(str(INDEX_FILE))

    return create_index()


def rebuild_index(metadata: list[dict]):
    """
    Rebuild the complete FAISS index
    using normalized embeddings.
    """

    from backend.app.services.embedding_service import generate_embedding

    index = create_index()

    for position, item in enumerate(metadata):

        embedding = generate_embedding(item["chunk"])

        add_vectors(index, [embedding])

        item["index"] = position

    save_index(index)

    return index