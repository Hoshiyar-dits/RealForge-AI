from fastapi import FastAPI
from app.users.router import router as user_router
from app.auth.router import router as auth_router
from app.products.router import router as product_router
from app.roles.router import router as role_router
from app.assistant.router import router as assistant_router

app = FastAPI()

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(role_router)
app.include_router(assistant_router)

@app.get('/')
def health():
    return {"status":"Project health is OK."}