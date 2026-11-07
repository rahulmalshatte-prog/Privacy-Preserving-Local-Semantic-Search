from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.documents import router as documents_router
from backend.app.api.search import router as search_router


app = FastAPI(
    title="Privacy-Preserving Local Semantic Search Engine",
    description="A local semantic search engine for private documents.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(documents_router)
app.include_router(search_router)


@app.get("/")
def root():
    return {
        "message": "Privacy-Preserving Local Semantic Search Engine API is running!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }