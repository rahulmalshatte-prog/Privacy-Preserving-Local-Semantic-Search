from pathlib import Path


# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]


# Application information
APP_NAME = "Privacy-Preserving Local Semantic Search Engine"
APP_VERSION = "1.0.0"


# Local data directories
DATA_DIR = BASE_DIR / "data"

DOCUMENTS_DIR = DATA_DIR / "documents"

DATABASE_DIR = DATA_DIR / "database"

INDEXES_DIR = BASE_DIR / "backend" / "indexes"


# Create directories if they don't exist
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
INDEXES_DIR.mkdir(parents=True, exist_ok=True)