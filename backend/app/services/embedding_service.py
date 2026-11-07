from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

# Load the model from local cache only
model = SentenceTransformer(
    MODEL_NAME,
    local_files_only=True
)


def generate_embedding(text: str) -> list[float]:
    """
    Generate a normalized 384-dimensional embedding locally.
    """

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()