import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.users.router import router as user_router
from app.auth.router import router as auth_router
from app.products.router import router as product_router
from app.roles.router import router as role_router
from app.assistant.router import router as assistant_router
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from app.database.config import cors_origins

app = FastAPI()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10/minute"]
)

# Register limiter
app.state.limiter = limiter

# Register 429 exception handler
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

# Apply rate limiting globally
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

# a handler for a specific exception runs inside the CORS middleware, so the front-end gets a readable JSON error
# instead of the plain 500 that FastAPI sends without CORS headers
@app.exception_handler(SQLAlchemyError)
def database_error(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Database error, please try again"})

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(role_router)
app.include_router(assistant_router)

@app.get('/')
def health():
    return {"status":"Project health is OK."}
