from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from generate_flashcards import chunk_text, generate_cards_with_llm, simulate_cards

# Load environment variables
load_dotenv()

app = FastAPI()

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
    simulate: bool = False
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
        
        if not req.simulate and not api_key:
             raise HTTPException(status_code=500, detail="Missing API Key")
             
        model = None
        if not req.simulate:
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
                
            if req.simulate:
                cards = simulate_cards(ch, current_per_chunk, i)
            else:
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
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
