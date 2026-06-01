"""Minimal test — see if Vercel Python serverless works at all."""
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "minimal-ok"}
