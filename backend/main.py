import os

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auth import create_token, get_username, validate_credentials
from db import init_db
from routers.board import router as board_router
from routers.ai import router as ai_router
from ai import chat

from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Annotated


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(board_router)
app.include_router(ai_router)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/login")
def login(body: LoginRequest):
    if not validate_credentials(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": create_token(body.username)}


@app.get("/api/me")
def me(username: Annotated[str, Depends(get_username)]):
    return {"username": username}


@app.post("/api/ai/ping")
async def ai_ping(username: Annotated[str, Depends(get_username)]):
    reply = await chat([{"role": "user", "content": "What is 2+2? Reply with just the number."}])
    return {"reply": reply}


# Serve the Next.js static export. Only mounted when the build exists (Docker).
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
