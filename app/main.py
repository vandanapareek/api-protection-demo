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
from urllib.parse import unquote_plus

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
async def search(q: str = ""):
    """
    Job-search-like endpoint.
    Accepts query strings like:
      ?q=python+developer  or ?q=python%20developer
    Returns a small mocked list of job titles for a few sample queries.
    """
    # decode pluses and percent-encoding to get natural text
    q_decoded = unquote_plus(q).strip().lower()

    # small in-memory mapping of realistic job search results
    jobs = {
        "python developer": [
            "Backend Python Developer - Singapore",
            "Full Stack Engineer (Python/React) - Remote",
            "Senior Software Engineer - Django & FastAPI"
        ],
        "react engineer": [
            "Frontend React Engineer - Bangalore",
            "React + TypeScript Developer - Singapore",
            "Senior UI Engineer - Remote"
        ],
        "full stack": [
            "Full Stack Developer (Node.js + React) - Singapore",
            "Full Stack Engineer (Go + VueJS) - Remote",
            "Full Stack Software Engineer - Australia"
        ],
        "data scientist": [
            "Data Scientist - ML & Analytics - Singapore",
            "Senior Data Scientist - Remote",
            "Machine Learning Engineer - Hybrid"
        ]
    }

    # fallback: if q empty, return a few recent/job categories; if not matched, show a helpful message
    if q_decoded == "":
        sample = {
            "query": "",
            "results": [
                "Try queries like 'python developer', 'react engineer', 'full stack', 'data scientist'"
            ]
        }
        return sample

    results = jobs.get(q_decoded)
    if results:
        return {"query": q_decoded, "results": results}

    # simple fuzzy fallback: check if any keyword exists in keys
    for key in jobs:
        if key in q_decoded or any(word in q_decoded for word in key.split()):
            return {"query": q_decoded, "results": jobs[key]}

    return {"query": q_decoded, "results": [f"No results found for '{q_decoded}'"]}


@app.get("/")
async def home():
    return {"status": "ok", "info": "API protection demo"}


@app.get("/protected")
async def protected():
    """
    Explicit protected endpoint used to demonstrate rate limiting.
    Repeated fast requests to this endpoint should start getting 429 responses.
    """
    # small delay to simulate work
    await asyncio.sleep(0.005)
    return {"status": "ok", "info": "protected endpoint - rate limiting demo"}
