"""
Collects human corrections into a training dataset.
 
Every time a team member fixes one of Avcore's answers in the UI, it lands
here as one line of JSONL — the standard format for LoRA fine-tuning data.
Each line: {"prompt": "...", "response": "...", "original_response": "...", "created_at": "..."}
 
`original_response` is kept for reference/debugging but the fine-tuning
script should train on `prompt` -> `response` (the corrected one) only.
"""
 
import json
from pathlib import Path
from datetime import datetime, timezone
 
DATA_PATH = Path(__file__).parent / "corrections.jsonl"
 
 
def save_correction(question: str, original_answer: str, corrected_answer: str):
    record = {
        "prompt": question,
        "response": corrected_answer,
        "original_response": original_answer,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(DATA_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record
 
 
def load_corrections() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
 
 
def correction_count() -> int:
    return len(load_corrections())