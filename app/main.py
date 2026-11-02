from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.users.router import router as user_router
from app.auth.router import router as auth_router
from app.products.router import router as product_router
from app.roles.router import router as role_router
from app.assistant.router import router as assistant_router
import os

# front-end addresses allowed to call this API from the browser, comma separated
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(role_router)
app.include_router(assistant_router)

@app.get('/')
def health():
    return {"status":"Project health is OK."}
