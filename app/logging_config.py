import logging
import json
import time
from fastapi import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Crypto_api")


async def log_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time

    log_data = {
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": round(process_time * 1000, 2),
        "user_agent": request.headers.get("user-agent"),
    }

    logger.info(json.dumps(log_data))

    return response
