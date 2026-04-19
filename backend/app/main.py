from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.chat import stream_chat
from app.config import settings
from app.rate_limit import check_rate_limit

# from app.rate_limit import check_rate_limit

_FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Digital Twin API", docs_url=None, redoc_url=None)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Incoming chat request."""

    message: str = Field(..., min_length=1, max_length=500)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


# Routes
@app.get("/api/health")
async def health() -> dict:
    """Health check for Cloud Run."""
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request) -> StreamingResponse:
    """Stream a chat response from the digital twin."""
    # Rate limiting.
    client_ip = request.headers.get(
        "x-forwarded-for", request.client.host if request.client else None
    )
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()

    is_limited, retry_after = check_rate_limit(client_ip)
    if is_limited:
        return JSONResponse(
            status_code=429,
            content={"error": "Too many requests. Please try again shortly."},
            headers={"Retry-After": str(retry_after)},
        )

    return StreamingResponse(
        stream_chat(req.message, req.session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store"},
    )


# Serve frontend static files at root
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
