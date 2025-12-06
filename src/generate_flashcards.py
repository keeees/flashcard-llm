import argparse
import csv
import json
import os
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from tqdm import tqdm
from pypdf import PdfReader
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .logger import logger


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_pdf_file(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for p in reader.pages:
        pages.append(p.extract_text() or "")
    return "\n\n".join(pages)


def load_input(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return read_pdf_file(path)
    return read_text_file(path)


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)


def extract_json_block(s: str) -> Dict:
    try:
        return json.loads(s)
    except Exception:
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(s[start : end + 1])
    return {"cards": []}


def generate_cards_with_llm(model: ChatOpenAI, chunk: str, per_chunk: int, language: str, 
                            difficulty: str = "Mixed", card_type: str = "Standard") -> List[Dict[str, str]]:
    system_prompt = (
        "You are an expert educational content creator specializing in high-quality flashcards (Quizlet style).\n"
        "Your goal is to create clear, concise, and meaningful Q&A pairs from the input text.\n\n"
        "Guidelines:\n"
        "1. **Front Side (Question)**: Should be a specific concept, term, or question that tests understanding.\n"
        "2. **Back Side (Answer)**: Should be a precise, accurate, and digestible explanation or definition.\n"
        "3. **Difficulty**: {difficulty}\n"
        "4. **Type**: {card_type} (e.g., Standard Q&A,True/False, Fill-in-the-blank)\n"
        "5. **Output Format**: JSON object with a 'cards' key containing an array of objects. "
        "Each object must have 'question', 'answer', 'tags' (list of strings), and 'type' (string).\n"
        "6. **Language**: {language}\n\n"
        "Avoid trivial questions. Focus on key concepts, dates, figures, and cause-effect relationships."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Content:\n{chunk}\n\nGenerate {n} flashcards based on the guidelines above.\nExample JSON: {example}"),
    ])
    
    example = {
        "cards": [
            {
                "question": "What is the primary function of mitochondria?", 
                "answer": "To generate energy for the cell (ATP) through cellular respiration.",
                "tags": ["Biology", "Cell Structure"],
                "type": "Standard"
            }
        ]
    }
    
    chain = prompt | model
    
    logger.info(f"Invoking LLM for chunk of size {len(chunk)}...")
    resp = chain.invoke({
        "chunk": chunk, 
        "n": per_chunk, 
        "difficulty": difficulty,
        "card_type": card_type,
        "language": language,
        "example": json.dumps(example, ensure_ascii=False)
    })
    logger.info("LLM response received.")
    
    data = extract_json_block(resp.content)
    cards = data.get("cards", [])
    result = []
    for c in cards[:per_chunk]:
        q = str(c.get("question", "")).strip()
        a = str(c.get("answer", "")).strip()
        t = c.get("tags", [])
        ct = str(c.get("type", "Standard")).strip()
        
        # Format tags as a string for CSV if needed, or keep list if handled later.
        # For now, let's just append tags to answer or keep them separate if we update CSV.
        # The user asked for "standardized flashcard structure", usually Front/Back.
        # We will append tags to the answer in brackets for visibility in standard 2-col CSV,
        # or just return them. Let's stick to 2-col CSV for compatibility but maybe append tags?
        # Actually, let's store them in the dict and update write_csv to handle them.
        
        if q and a:
            result.append({
                "question": q, 
                "answer": a,
                "tags": t,
                "type": ct
            })
    return result


def write_csv(cards: List[Dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Add header
        writer.writerow(["Question", "Answer", "Tags", "Type"])
        for c in cards:
            tags_str = ", ".join(c.get("tags", [])) if isinstance(c.get("tags"), list) else str(c.get("tags", ""))
            writer.writerow([c["question"], c["answer"], tags_str, c.get("type", "")])



def main():
    parser = argparse.ArgumentParser(prog="generate_flashcards")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="flashcards.csv")
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--chunk_size", type=int, default=2000)
    parser.add_argument("--chunk_overlap", type=int, default=200)
    parser.add_argument("--per_chunk", type=int, default=3)
    parser.add_argument("--total_cards", type=int, default=None, help="Total number of cards to generate across all chunks")
    parser.add_argument("--language", default="中文")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--difficulty", default="Mixed", help="Difficulty level (Beginner, Intermediate, Advanced, Mixed)")
    parser.add_argument("--card_type", default="Standard", help="Type of flashcards (Standard, True/False, Mixed)")
    args = parser.parse_args()

    load_dotenv()
    api_key = (
        os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("DEEPSEEK_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")

    text = load_input(Path(args.input))
    chunks = chunk_text(text, args.chunk_size, args.chunk_overlap)

    if args.total_cards is not None:
        if len(chunks) > 0:
            base_per_chunk = args.total_cards // len(chunks)
            remainder = args.total_cards % len(chunks)
        else:
            base_per_chunk = 0
            remainder = 0
    else:
        base_per_chunk = args.per_chunk
        remainder = 0

    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY or OPENAI_API_KEY")

    model = ChatOpenAI(model=args.model, api_key=api_key, base_url=base_url, temperature=args.temperature)

    all_cards: List[Dict[str, str]] = []
    for i, ch in enumerate(tqdm(chunks, desc="Generating", unit="chunk")):
        current_per_chunk = base_per_chunk + (1 if i < remainder else 0)
        if current_per_chunk <= 0:
            continue

        cards = generate_cards_with_llm(
            model, 
            ch, 
            current_per_chunk, 
            args.language, 
            difficulty=args.difficulty, 
            card_type=args.card_type
        )
        all_cards.extend(cards)

    write_csv(all_cards, Path(args.output))


if __name__ == "__main__":
    main()
