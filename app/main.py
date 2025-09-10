import os
import time
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from app.limiter import RedisRateLimiter
from app.detectors import BehavioralDetector
from app.prometheus_metrics import REQUESTS, ALLOWED, BLOCKED, SUSPICIONS, LATENCY
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
PER_IP_CAPACITY = int(os.getenv("PER_IP_CAPACITY", "20"))
PER_IP_RATE = float(os.getenv("PER_IP_RATE", "1"))
PER_KEY_CAPACITY = int(os.getenv("PER_KEY_CAPACITY", "60"))
PER_KEY_RATE = float(os.getenv("PER_KEY_RATE", "5"))

limiter = RedisRateLimiter(REDIS_URL)
detector = BehavioralDetector(REDIS_URL)

app = FastAPI(title="API Protection Demo")


@app.on_event("startup")
async def startup():
    await limiter.init()
    await detector.init()


def client_ip(request: Request):
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host


@app.get("/metrics")
def metrics():
    # generate_latest() returns bytes; use Response to return raw bytes with proper content-type
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.middleware("http")
async def protection_middleware(request: Request, call_next):
    start = time.time()
    REQUESTS.inc()
    ip = client_ip(request)
    api_key = request.headers.get("x-api-key", "anon")
    allowed_key, tokens_key = await limiter.allow_request(f"key:{api_key}", PER_KEY_CAPACITY, PER_KEY_RATE)
    if not allowed_key:
        BLOCKED.inc()
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded (api key)"})
    allowed_ip, tokens_ip = await limiter.allow_request(f"ip:{ip}", PER_IP_CAPACITY, PER_IP_RATE)
    if not allowed_ip:
        BLOCKED.inc()
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded (ip)"})
    suspicious = await detector.record_and_check(ip, request.url.path)
    if suspicious:
        SUSPICIONS.inc()
        return JSONResponse(status_code=429, content={"detail": "Suspicious behavior detected"})
    response = await call_next(request)
    LATENCY.observe(time.time() - start)
    ALLOWED.inc()
    return response


@app.get("/search")
async def search(q: str = "test"):
    await asyncio.sleep(0.01)
    return {"q": q, "results": ["one", "two", "three"]}


@app.get("/")
async def home():
    return {"status": "ok", "info": "API protection demo"}
