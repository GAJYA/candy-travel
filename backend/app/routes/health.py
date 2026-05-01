from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.db import SessionLocal
from app.redis_client import redis

router = APIRouter()


async def _check_db() -> tuple[str, str | None]:
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return "ok", None
    except Exception as e:
        return "fail", str(e)


async def _check_redis() -> tuple[str, str | None]:
    try:
        pong = await redis.ping()
        return ("ok" if pong else "fail"), None
    except Exception as e:
        return "fail", str(e)


@router.get("/healthz")
async def healthz() -> JSONResponse:
    db_status, db_err = await _check_db()
    redis_status, redis_err = await _check_redis()
    overall = "ok" if db_status == "ok" and redis_status == "ok" else "fail"

    body = {
        "status": overall,
        "db": db_status,
        "redis": redis_status,
        "version": settings.app_version,
    }
    if db_err:
        body["dbError"] = db_err
    if redis_err:
        body["redisError"] = redis_err

    code = 200 if overall == "ok" else 503
    return JSONResponse(body, status_code=code)
