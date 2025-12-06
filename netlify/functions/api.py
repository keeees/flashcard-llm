import sys
import os
from mangum import Mangum

# Ensure we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.api import app
except ImportError as e:
    # Fallback app for debugging
    from fastapi import FastAPI
    app = FastAPI()
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def catch_all(path_name: str):
        return {"error": f"Import failed: {str(e)}", "sys_path": sys.path}

handler = Mangum(app)
