"""FastAPI backend service for the resume RAG chatbot (port 8080)."""
import logging
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import acquisition, config, generator
from .pipeline import pipeline
from .sessions import UnknownSession, sessions

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    pipeline.start()
    yield
    pipeline.stop()


app = FastAPI(title="Resume RAG API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Which of the visitor's own chats this message belongs to.
    conversation_id: str = Field(min_length=1, max_length=64)


class Source(BaseModel):
    section: str
    source: str
    score: float
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    mode: Literal["llm", "extractive"]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "ready": pipeline.ready}


@app.get("/api/status")
def status() -> dict:
    return pipeline.status()


@app.post("/api/reindex")
def reindex() -> dict:
    """Force a rebuild. The watcher does this automatically when the sources change."""
    try:
        pipeline.rebuild()
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return pipeline.status()


@app.post("/api/admin/resume")
async def upload_resume(request: Request) -> dict:
    """Replace the resume with the PDF sent as the request body, then re-index."""
    data = await request.body()
    if not data:
        raise HTTPException(status_code=422, detail="No file received.")
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="That file is larger than 10 MB.")
    try:
        backup = await run_in_threadpool(acquisition.replace_resume, data)
        await run_in_threadpool(pipeline.rebuild)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {**pipeline.status(), "backup": backup.name if backup else None}


@app.post("/api/session")
def create_session() -> dict:
    """Start a private session for one visitor. Its id is the key to their chats."""
    return {"session_id": sessions.create()}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, x_session_id: str = Header(default="")) -> ChatResponse:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message is empty.")
    # History is looked up by the caller's own session id and never taken from the
    # request, so a visitor can only ever continue their own conversations.
    try:
        history = sessions.history(x_session_id, request.conversation_id)
    except UnknownSession as error:
        raise HTTPException(status_code=401, detail="Session expired.") from error

    try:
        hits = pipeline.search(message)
        # A follow-up like "and its tech stack?" matches little on its own; retry it
        # with the previous question attached and keep whichever retrieves better.
        previous = next((t["content"] for t in reversed(history) if t["role"] == "user"), None)
        if previous and hits[0][1] < config.FOLLOW_UP_SCORE:
            with_context = pipeline.search(f"{previous} {message}")
            if with_context[0][1] > hits[0][1]:
                hits = with_context
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    answer, mode = generator.answer(message, history, hits)
    try:
        sessions.append(x_session_id, request.conversation_id, message, answer)
    except UnknownSession:
        pass  # expired while answering; the visitor still gets this reply
    sources = [
        Source(section=chunk.section, source=chunk.source, score=round(score, 3), text=chunk.text)
        for chunk, score in hits
        if score >= config.MIN_SCORE
    ]
    return ChatResponse(answer=answer, sources=sources, mode=mode)
