from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, validator
from datetime import datetime, timedelta
from logging_middleware.logger import log
from logging_middleware.middleware import LoggingMiddleware
import string
import random
import uvicorn
import sys
import os

# --- Data Models ---
class ShortURLRequest(BaseModel):
    url: HttpUrl
    validity: int = 30  # minutes
    shortcode: str | None = None

    @validator('shortcode')
    def check_shortcode(cls, v):
        if v and not v.isalnum():
            raise ValueError('shortcode must be alphanumeric')
        if v and len(v) > 10:
            raise ValueError('shortcode too long')
        return v

class ShortURLInfo(BaseModel):
    original_url: HttpUrl
    created_at: datetime
    expiry: datetime
    clicks: int
    click_details: list[dict]

# --- Application Setup ---
app = FastAPI()
logger = log()
app.middleware('http')(LoggingMiddleware(app, logger))

# --- In-Memory Storage ---
storage: dict[str, ShortURLInfo] = {}

# --- Utility Functions ---
def generate_shortcode(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if code not in storage:
            return code

# --- API Endpoints ---
@app.post('/shorturls', status_code=status.HTTP_201_CREATED)
async def create_short_url(req: ShortURLRequest):
    # Determine shortcode
    code = req.shortcode or generate_shortcode()
    if code in storage:
        raise HTTPException(status_code=409, detail='Shortcode already in use')

    now = datetime.utcnow()
    expiry = now + timedelta(minutes=req.validity)

    storage[code] = ShortURLInfo(
        original_url=req.url,
        created_at=now,
        expiry=expiry,
        clicks=0,
        click_details=[]
    )
    BASE_URL = "http://localhost:8000"
    short_link = f"{BASE_URL}/{code}"
    return {"shortLink": short_link, "expiry": expiry.isoformat() + 'Z'}

@app.get('/{code}')
async def redirect(code: str, request: Request):
    info = storage.get(code)
    if not info:
        raise HTTPException(status_code=404, detail='Shortcode not found')
    if datetime.utcnow() > info.expiry:
        raise HTTPException(status_code=410, detail='Shortcode expired')

    # Record click
    info.clicks += 1
    info.click_details.append({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'referrer': request.headers.get('referer'),
        'ip': request.client.host
    })
    return RedirectResponse(info.original_url)

@app.get('/shorturls/{code}')
async def get_stats(code: str):
    info = storage.get(code)
    if not info:
        raise HTTPException(status_code=404, detail='Shortcode not found')

    return {
        'original_url': info.original_url,
        'created_at': info.created_at.isoformat() + 'Z',
        'expiry': info.expiry.isoformat() + 'Z',
        'clicks': info.clicks,
        'click_details': info.click_details
    }

# --- Run Application ---
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
