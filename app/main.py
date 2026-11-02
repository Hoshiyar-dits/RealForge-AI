from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.users.router import router as user_router
from app.auth.router import router as auth_router
from app.products.router import router as product_router
from app.roles.router import router as role_router
from app.assistant.router import router as assistant_router
from app.database.config import cors_origins

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
