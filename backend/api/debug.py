"""Vercel serverless debug endpoint — tests each component independently."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    yield


app = FastAPI(title="Flow Debug", lifespan=lifespan)


@app.get("/api/debug")
async def debug():
    import os
    from src.app.config import settings

    result = {
        "env_checks": {},
        "db_checks": {},
        "crypto_checks": {},
        "errors": [],
    }

    # Environment
    result["env_checks"]["DATABASE_URL_set"] = bool(settings.database_url)
    result["env_checks"]["ENCRYPTION_KEY_set"] = bool(settings.encryption_key)
    result["env_checks"]["FLOW_API_KEY_set"] = bool(settings.flow_api_key)

    # DB connection
    try:
        from src.app.database import async_session_factory
        from sqlalchemy import text, select, func
        from src.app.models.tenant import Tenant

        async with async_session_factory() as session:
            r = await session.execute(text("SELECT 1 as ping"))
            result["db_checks"]["ping"] = r.scalar() == 1
            r2 = await session.execute(select(func.count(Tenant.id)))
            result["db_checks"]["tenant_count"] = r2.scalar()
    except Exception as e:
        result["db_checks"]["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        result["errors"].append(str(e)[:200])

    # Fernet
    try:
        from src.app.agent.llm import encrypt_api_key, decrypt_api_key
        enc = encrypt_api_key("test")
        dec = decrypt_api_key(enc)
        result["crypto_checks"]["fernet"] = dec == "test"
    except Exception as e:
        result["crypto_checks"]["fernet"] = f"FAIL: {str(e)[:200]}"

    # Bcrypt
    try:
        from src.app.auth.utils import hash_password, verify_password
        h = hash_password("test1234")
        result["crypto_checks"]["bcrypt_hash"] = bool(h)
        result["crypto_checks"]["bcrypt_verify"] = verify_password("test1234", h)
    except Exception as e:
        result["crypto_checks"]["bcrypt"] = f"FAIL: {str(e)[:200]}"

    return result
