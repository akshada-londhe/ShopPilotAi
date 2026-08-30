import os
import sys

# Ensure backend directory is in sys.path for app module imports
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set ChromaDB to write to Vercel's writable /tmp directory
os.environ["CHROMA_PERSIST_DIR"] = "/tmp/chroma"

from app.main import app

# Export app for Vercel Python serverless entrypoint
__all__ = ["app"]
