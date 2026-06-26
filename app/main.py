import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.api.routes import router
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper())

app = FastAPI(
    title="QueueStorm Investigator API",
    description=(
        "AI/API support copilot for digital finance ticket investigation. "
        "Hybrid rules + OpenRouter architecture. "
        "Never requests credentials or promises unauthorized refunds."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(router)
