from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, validator
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_middleware.logger import log  # Import reusable logger function
from logging_middleware.middleware import LoggingMiddleware  # Custom middleware
import string
import random
import uvicorn

# --- Config ---
BASE_URL = "http://localhost:8000"  # Replace with domain when deployed

# --- Data Models ---
class ShortURLRequest(BaseModel):
    url: HttpUrl
    validity: int = 30  # Validity in minutes
    shortcode: str | None = None

    # Validate custom shortcode input
    @validator('shortcode')
    def check_shortcode(cls, v):
        if v and not v.isalnum():
            raise ValueError('Shortcode must be alphanumeric')
        if v and len(v) > 10:
            raise ValueError('Shortcode too long (max 10 chars)')
        return v

class ShortURLInfo(BaseModel):
    original_url: HttpUrl
    created_at: datetime
    expiry: datetime
    clicks: int
    click_details: list[dict]  # Track time, referrer, IP for each click

# --- FastAPI App Setup ---
app = FastAPI()
app.middleware('http')(LoggingMiddleware(app))  # Attach custom logging middleware

# --- In-Memory Store for URLs ---
storage: dict[str, ShortURLInfo] = {}

# --- Utility: Generate Unique Shortcode ---
def generate_shortcode(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if code not in storage:
            return code

# --- Endpoint: Create Short URL ---
@app.post('/shorturls', status_code=status.HTTP_201_CREATED)
async def create_short_url(req: ShortURLRequest):
    code = req.shortcode or generate_shortcode()
    if code in storage:
        log("backend", "error", "handler", f"Shortcode already exists: {code}")
        raise HTTPException(status_code=409, detail="Shortcode already in use")

    now = datetime.utcnow()
    expiry = now + timedelta(minutes=req.validity)

    storage[code] = ShortURLInfo(
        original_url=req.url,
        created_at=now,
        expiry=expiry,
        clicks=0,
        click_details=[]
    )

    short_link = f"{BASE_URL}/{code}"
    log("backend", "info", "handler", f"Short URL created: {short_link}")
    return {"shortLink": short_link, "expiry": expiry.isoformat() + 'Z'}

# --- Endpoint: Redirect to Original URL ---
@app.get('/{code}')
async def redirect(code: str, request: Request):
    info = storage.get(code)
    if not info:
        log("backend", "warn", "handler", f"Shortcode not found: {code}")
        raise HTTPException(status_code=404, detail="Shortcode not found")
    if datetime.utcnow() > info.expiry:
        log("backend", "warn", "handler", f"Shortcode expired: {code}")
        raise HTTPException(status_code=410, detail="Shortcode expired")

    # Track click
    info.clicks += 1
    info.click_details.append({
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "referrer": request.headers.get("referer"),
        "ip": request.client.host
    })

    log("backend", "info", "handler", f"Redirecting {code} to {info.original_url}")
    return RedirectResponse(info.original_url)

# --- Endpoint: Get URL Statistics ---
@app.get('/shorturls/{code}')
async def get_stats(code: str):
    info = storage.get(code)
    if not info:
        log("backend", "warn", "handler", f"Stats not found: {code}")
        raise HTTPException(status_code=404, detail="Shortcode not found")

    log("backend", "info", "handler", f"Stats retrieved for {code}")
    return {
        "original_url": info.original_url,
        "created_at": info.created_at.isoformat() + 'Z',
        "expiry": info.expiry.isoformat() + 'Z',
        "clicks": info.clicks,
        "click_details": info.click_details
    }

# --- Run App ---
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)