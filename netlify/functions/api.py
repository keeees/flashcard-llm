import sys
import os
from mangum import Mangum

# Add the current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Add the project root to sys.path for local development
# This allows importing 'src' when running from project root or function dir
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)

try:
    from src.api import app
except ImportError as e:
    # Fallback app for debugging if import fails
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def catch_all(path_name: str):
        return JSONResponse({
            "error": f"Import failed: {str(e)}",
            "sys_path": sys.path,
            "cwd": os.getcwd(),
            "files_in_current_dir": os.listdir(current_dir) if os.path.exists(current_dir) else [],
            "files_in_root": os.listdir(project_root) if os.path.exists(project_root) else []
        }, status_code=500)

handler = Mangum(app)
