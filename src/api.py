from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from .generate_flashcards import chunk_text, generate_cards_with_llm
from .logger import logger

# Load environment variables
load_dotenv()

app = FastAPI()

# Middleware for logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"Path: {request.url.path} Method: {request.method} Status: {response.status_code} Duration: {process_time:.2f}s"
    )
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class GenerateRequest(BaseModel):
    text: str
    difficulty: str = "Mixed"
    card_type: str = "Standard"
    total_cards: int = 10
    language: str = "中文"

class Flashcard(BaseModel):
    question: str
    answer: str
    tags: List[str]
    type: str

class GenerateResponse(BaseModel):
    cards: List[Flashcard]

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_flashcards(req: GenerateRequest):
    logger.info(f"Received generation request. Text length: {len(req.text)}, Total cards: {req.total_cards}")
    try:
        # Configuration
        chunk_size = 2000
        chunk_overlap = 200
        
        # Chunk text
        chunks = chunk_text(req.text, chunk_size, chunk_overlap)
        
        if not chunks:
            return {"cards": []}

        # Calculate cards per chunk
        base_per_chunk = req.total_cards // len(chunks) if len(chunks) > 0 else 0
        remainder = req.total_cards % len(chunks) if len(chunks) > 0 else 0
        
        # Setup Model
        api_key = (
            os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("DEEPSEEK_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        )
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
        
        if not api_key:
             raise HTTPException(status_code=500, detail="Missing API Key")
             
        model = ChatOpenAI(
            model="deepseek-chat", 
            api_key=api_key, 
            base_url=base_url, 
            temperature=0.2
        )
            
        all_cards = []
        for i, ch in enumerate(chunks):
            current_per_chunk = base_per_chunk + (1 if i < remainder else 0)
            if current_per_chunk <= 0:
                continue
                
            cards = generate_cards_with_llm(
                model, 
                ch, 
                current_per_chunk, 
                req.language, 
                difficulty=req.difficulty, 
                card_type=req.card_type
            )
            
            # Normalize cards to match Pydantic model
            for c in cards:
                # Ensure tags is a list
                tags = c.get("tags", [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",")]
                
                all_cards.append(Flashcard(
                    question=c.get("question", ""),
                    answer=c.get("answer", ""),
                    tags=tags,
                    type=c.get("type", "Standard")
                ))
                
        return {"cards": all_cards}

    except Exception as e:
        logger.error(f"Error generating flashcards: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Serve Frontend (SPA support)
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"

if frontend_build_path.exists():
    # Mount static assets (JS/CSS)
    static_assets_path = frontend_build_path / "static"
    if static_assets_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_assets_path)), name="static_assets")

    # Serve root index.html
    @app.get("/")
    async def serve_root():
        index_path = frontend_build_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Index not found")

    # Catch-all for other files (manifest.json, etc.) or SPA routes
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # 1. Check if file exists in build directory (e.g. manifest.json, favicon.ico)
        possible_file = frontend_build_path / full_path
        try:
            possible_file = possible_file.resolve()
            if str(possible_file).startswith(str(frontend_build_path.resolve())) and possible_file.is_file():
                return FileResponse(possible_file)
        except Exception:
            pass

        # 2. If path starts with api/, return 404 (don't serve index.html for API errors)
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        # 3. Fallback to index.html for SPA routing
        index_path = frontend_build_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        raise HTTPException(status_code=404, detail="Frontend not found")
else:
    logger.warning("Frontend build directory not found. Static files will not be served.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3001)
