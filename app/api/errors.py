from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    for error in errors:
        loc = error.get("loc", ())
        if "complaint" in loc:
            msg = str(error.get("msg", "")).lower()
            if "empty" in msg or error.get("type") == "string_too_short":
                return JSONResponse(
                    status_code=422,
                    content={"detail": "Complaint cannot be empty"},
                )
    return JSONResponse(status_code=400, content={"detail": "Invalid request payload"})


async def generic_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
