"""
Companion's local API server.

Run with (from the folder containing this file):
    uvicorn server:app --reload --port 8000

The frontend (java.js) calls POST /chat and expects {"reply": "..."}.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from avcore import Avcore
from store import MemoryStore
from training_data import save_correction, correction_count
from youtube import search_youtube
from microsoft import get_recent_emails, get_upcoming_events

app = FastAPI(title="Companion Core")

# Frontend is served from a local file / dev server — allow it to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this once the frontend has a fixed origin
    allow_methods=["*"],
    allow_headers=["*"],
)

avcore = Avcore()
memory = MemoryStore()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"  # single-user for now; ready for multi-session later


class ChatResponse(BaseModel):
    reply: str


class CorrectionRequest(BaseModel):
    question: str
    original_answer: str
    corrected_answer: str


class CorrectionResponse(BaseModel):
    saved: bool
    total_corrections: int


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = memory.get_history(req.session_id)
    reply = avcore.generate(req.message, history=history)

    memory.add_message(req.session_id, "user", req.message)
    memory.add_message(req.session_id, "assistant", reply)

    return ChatResponse(reply=reply)


@app.post("/train/correction", response_model=CorrectionResponse)
def train_correction(req: CorrectionRequest):
    save_correction(req.question, req.original_answer, req.corrected_answer)
    return CorrectionResponse(saved=True, total_corrections=correction_count())


@app.get("/tools/youtube/search")
def youtube_search(q: str, max_results: int = 5):
    return {"results": search_youtube(q, max_results)}


@app.get("/tools/microsoft/emails")
def microsoft_emails(limit: int = 5):
    return {"results": get_recent_emails(limit)}


@app.get("/tools/microsoft/events")
def microsoft_events(limit: int = 5):
    return {"results": get_upcoming_events(limit)}


@app.get("/health")
def health():
    return {"status": "ok", "model": avcore.model_name}