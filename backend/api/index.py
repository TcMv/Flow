"""Vercel Python serverless entry point for Flow FastAPI backend."""
from __future__ import annotations

import os
import sys

# Add the project root (backend/) to sys.path so `src` package is findable
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ── Import the FastAPI app ─────────────────────────────────────────
from src.app.main import app  # noqa: E402

# ASGI handler — Vercel expects a module-level `app`
