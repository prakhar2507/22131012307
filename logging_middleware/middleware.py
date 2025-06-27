from datetime import datetime
from fastapi import Request, Response, FastAPI
from logging_middleware.logger import log

class LoggingMiddleware:
    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, request: Request, call_next):
        start_time = datetime.utcnow()
        log("backend", "info", "middleware", f"Incoming request: {request.method} {request.url}")
        response: Response = await call_next(request)
        duration = (datetime.utcnow() - start_time).total_seconds()
        log("backend", "info", "middleware", f"Response {response.status_code} for {request.method} {request.url} in {duration:.3f}s")
        return response
