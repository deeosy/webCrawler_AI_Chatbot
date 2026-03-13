from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import index_urls, chat as process_chat
from jobs import vector_store

app = FastAPI(title="Website RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class URLRequest(BaseModel):
    urls: List[str]


class ChatRequest(BaseModel):
    query: str


class IndexResponse(BaseModel):
    success: bool
    chunks: int
    message: str


class ChatResponse(BaseModel):
    answer: str
    context_limited: bool


@app.get("/")
async def root():
    return {"message": "Website RAG Chatbot API"}


@app.post("/index", response_model=IndexResponse)
async def index_urls_endpoint(request: URLRequest):
    try:
        chunks = index_urls(request.urls)
        return IndexResponse(
            success=True,
            chunks=chunks,
            message=f"Successfully indexed {chunks} chunks of content!",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if vector_store.is_empty():
        raise HTTPException(
            status_code=400, detail="No content indexed. Please add URLs first."
        )

    try:
        answer, limited = process_chat(request.query)
        return ChatResponse(answer=answer, context_limited=limited)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def status():
    return {
        "indexed": not vector_store.is_empty(),
        "chunks": len(vector_store.chunks) if hasattr(vector_store, "chunks") else 0,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
