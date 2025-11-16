"""Run the FastAPI backend server."""
import sys
from pathlib import Path

# Add parent directory to path so we can import backend package
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)]
    )
