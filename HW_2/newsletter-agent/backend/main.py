from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from models import GenerateRequest
from orchestrator import run_pipeline

app = FastAPI(title="Newsletter Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.post("/generate")
async def generate(request: GenerateRequest) -> StreamingResponse:
    return StreamingResponse(
        run_pipeline(request.topics, request.style, request.language),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
