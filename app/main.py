from fastapi import FastAPI
from sqlalchemy import text
from fastapi.responses import JSONResponse
from .router import auth, user, portfolio
from .database import session_object
import redis.asyncio as redis
from .config import settings
import time
from .logging_config import log_middleware

redis_client = redis.from_url(settings.redis_url, decode_responses=True)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Welcome to the Crypto Tracker API"}


app.include_router(user.router)
app.include_router(auth.router)
app.include_router(portfolio.router)


@app.get("/health")
async def health_check(session: session_object):
    try:
        await session.execute(text("SELECT 1"))
        redis_client.ping()
        return {"status": "healthy", "database": "up", "redis": "up"}
    except Exception as e:
        return JSONResponse(
            status_code=503, content={"status": "unhealthy", "reason": str(e)}
        )


@app.middleware("http")
async def add_logging(request, call_next):
    return await log_middleware(request, call_next)
