# Flashcard Generator

Creates a CSV of flashcards from a PDF or text file using DeepSeek via LangChain.

## Setup
- Ensure Python 3.10+.
- Install dependencies (pip): `python3 -m pip install -r requirements.txt`.
- Install/run with uv (recommended):
  - Ensure uv is installed (see https://docs.astral.sh/uv/)
  - Ephemeral run with pyproject: `uv run python src/generate_flashcards.py --input sample_input.txt --simulate`
  - Or create venv and install: `uv venv && source .venv/bin/activate && uv pip install -r requirements.txt`
- Set API key: `export DEEPSEEK_API_KEY=YOUR_KEY`.

## Usage
- Generate from text (pip): `python3 src/generate_flashcards.py --input sample_input.txt --output flashcards.csv`.
- Generate from text (uv): `uv run python src/generate_flashcards.py --input sample_input.txt --output flashcards.csv`.
- Generate from PDF (pip): `python3 src/generate_flashcards.py --input your.pdf --output flashcards.csv`.
- Generate from PDF (uv): `uv run python src/generate_flashcards.py --input your.pdf --output flashcards.csv`.
- Optional flags:
  - `--model deepseek-chat` or `deepseek-reasoner`
  - `--language 中文` or `English`
  - `--chunk_size 2000 --chunk_overlap 200`
  - `--per_chunk 3`
  - `--temperature 0.2`
  - `--simulate` to run without LLM for a dry run

Output CSV format: one row per card, `question,answer`.
