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


def simulate_cards(chunk: str, per_chunk: int) -> List[Dict[str, str]]:
    sentences = [x.strip() for x in chunk.replace("\n", " ").split("。") if x.strip()]
    cards = []
    for i, s in enumerate(sentences[:per_chunk]):
        q = f"这段内容的要点是什么？({i+1})"
        a = s
        cards.append({"question": q, "answer": a})
    return cards


def generate_cards_with_llm(model: ChatOpenAI, chunk: str, per_chunk: int, language: str) -> List[Dict[str, str]]:
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "你是学习辅助助手。根据输入内容生成高质量的'问答式'学习卡片。"
            "每张卡片包含'question'和'answer'字段。输出JSON对象，键名为'cards'，值为数组。"
            "要求: 问题简洁明确，答案准确凝练；避免无关信息；语言使用为" + language,
        ),
        (
            "human",
            "内容:\n{chunk}\n\n生成{n}张卡片，JSON格式示例: {example}",
        ),
    ])
    example = {"cards": [{"question": "问题", "answer": "答案"}]}
    chain = prompt | model
    resp = chain.invoke({"chunk": chunk, "n": per_chunk, "example": json.dumps(example, ensure_ascii=False)})
    data = extract_json_block(resp.content)
    cards = data.get("cards", [])
    result = []
    for c in cards[:per_chunk]:
        q = str(c.get("question", "")).strip()
        a = str(c.get("answer", "")).strip()
        if q and a:
            result.append({"question": q, "answer": a})
    return result


def write_csv(cards: List[Dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for c in cards:
            writer.writerow([c["question"], c["answer"]])


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
    parser.add_argument("--simulate", action="store_true")
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

    if not args.simulate and not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY or OPENAI_API_KEY")

    model = None
    if not args.simulate:
        model = ChatOpenAI(model=args.model, api_key=api_key, base_url=base_url, temperature=args.temperature)

    all_cards: List[Dict[str, str]] = []
    for i, ch in enumerate(tqdm(chunks, desc="Generating", unit="chunk")):
        current_per_chunk = base_per_chunk + (1 if i < remainder else 0)
        if current_per_chunk <= 0:
            continue

        if args.simulate:
            cards = simulate_cards(ch, current_per_chunk)
        else:
            cards = generate_cards_with_llm(model, ch, current_per_chunk, args.language)
        all_cards.extend(cards)

    write_csv(all_cards, Path(args.output))


if __name__ == "__main__":
    main()
