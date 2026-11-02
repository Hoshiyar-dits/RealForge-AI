# ReelForge-AI — Backend Coding Guide

FastAPI + SQLAlchemy (sync) + Pydantic v2 + Alembic. Auth is email + password (JWT via PyJWT); an emailed one-time code verifies the email at sign-up.
Run: `uvicorn app.main:app --reload`. Config comes from `.env` via `python-dotenv`.

**Every new API must follow the architecture and style below exactly. Do not introduce other patterns
(no async DB, no generic base repositories, no new folder layouts, no extra frameworks) unless explicitly asked.**

---

## 1. Folder structure (feature modules)

Each feature lives in its own package under `app/`, named in lowercase plural/feature form (`users`, `auth`, `videos`, ...):

```
app/
├── __init__.py
├── main.py                     # creates FastAPI app, includes every router
├── database/
│   ├── __init__.py
│   └── database.py             # engine, localSession, Base, get_db
└── <feature>/
    ├── __init__.py
    ├── router.py               # "controller": APIRouter + endpoint functions
    ├── service.py              # business logic class: <Feature>Service
    ├── repository.py           # DB access class: <Feature>Repository
    ├── dependecies.py          # (optional) FastAPI dependencies, e.g. auth guards
    ├── dto/
    │   ├── __init__.py
    │   ├── Create<Entity>.py   # request schema
    │   └── <Entity>Response.py # response schema
    └── models/
        ├── __init__.py
        └── <entities>.py       # SQLAlchemy model, e.g. users.py -> class User
```

- Every package directory gets an **empty** `__init__.py`. Do not put code or re-exports in it.
- One DTO class per file; the **file name equals the class name** in PascalCase (`CreateUser.py` → `class CreateUser`).
- Model files are lowercase plural (`users.py`), the class is singular PascalCase (`User`).
- Layer flow is strictly: `router → service → repository → model`. Routers never touch the DB; services never build queries.
- Register every new router in `app/main.py`:
  ```python
  from app.<feature>.router import router as <feature>_router
  app.include_router(<feature>_router)
  ```
- Import new models in `alembic/env.py` (and set `target_metadata = Base.metadata`) so autogenerate sees them.

## 2. General style

- 4-space indentation, no tabs.
- Absolute imports only, always from `app.` (`from app.users.service import UserService`). No relative imports.
- Import order as in existing files: `fastapi`/third-party first, then `app.*` modules. Keep imports minimal.
- Classes are declared with empty parentheses: `class UserService():`, `class UserRepository():`.
- snake_case for functions, methods, variables; PascalCase for classes; module-level constants lowercase (`algorithm`, `secret`, `otp_expire_minutes`).
- Single blank line between methods; keep functions short and flat. Comments only where something is non-obvious.
- Config values read with `os.getenv("NAME", "default")` at module level.
- Raise `HTTPException` from the **service** layer for business errors, using `status.HTTP_...` constants
  (e.g. `409` "Email already registered", `404` "... not found", `401` "Invalid or expired code").

## 3. Model (`app/<feature>/models/<entities>.py`)

```python
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, func
from app.database.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(255))
    email = Column(String(255), nullable=False, unique=True)
    status = Column(Enum("0","1"), nullable=False, default="1")
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP)
```

- Classic `Column(...)` style (not `Mapped[]` / `mapped_column`).
- Every table has `id`, `created_at`, `updated_at`, `deleted_at` (soft delete). Status flags use `Enum("0","1")`.
- Inherit from `Base` in `app.database.database`.
- Schema changes go through Alembic migrations (`alembic revision --autogenerate -m "..."`).

## 4. DTOs (`app/<feature>/dto/*.py`)

```python
from pydantic import BaseModel, EmailStr, Field

class CreateUser(BaseModel):
    first_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    last_name: str = Field(min_length=1, max_length=255)
```

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: Optional[str]
    email: str
    created_at: Optional[datetime]
```

- Request DTOs: `Create<Entity>`, `Update<Entity>`, `<Action>Request` (e.g. `LoginRequest`). Validate with `Field(...)`.
- Response DTOs: `<Entity>Response` / `<Action>Response`, with `model_config = ConfigDict(from_attributes=True)` when built from ORM objects.
- Never return sensitive fields (e.g. OTP codes, tokens other than in `LoginResponse`) in a response DTO.

## 5. Repository (`app/<feature>/repository.py`)

```python
from app.database.database import get_db
from app.users.models.users import User
from fastapi import Depends
from sqlalchemy.orm import Session
class UserRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create(self, data):
        try:
            user = User(
                first_name=data.first_name,
                last_name=data.last_name,
                email=data.email,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            raise

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
```

- Session injected via constructor: `db: Session = Depends(get_db)`.
- Only DB work here: no `HTTPException`, no hashing, no business rules.
- Writes: `add` → `commit` → `refresh` inside `try`, `rollback()` and re-`raise` on `Exception`.
- Reads always exclude soft-deleted rows: `Model.deleted_at.is_(None)`. Use `self.db.query(...)` style.
- Method names: `create`, `update`, `delete` (soft: set `deleted_at`), `get_by_id`, `get_by_<field>`, `list`.

## 6. Service (`app/<feature>/service.py`)

```python
from fastapi import Depends, HTTPException
from app.users.repository import UserRepository

class UserService():
    def __init__(self, repository: UserRepository = Depends()):
        self.repository = repository

    def create_user(self, data):
        if self.repository.get_by_email(data.email):
            raise HTTPException(status_code=409, detail="Email already registered")
        return self.repository.create(data)
```

- Repository injected via constructor: `repository: <Feature>Repository = Depends()`.
- Holds validation/business rules and raises `HTTPException`.
- Method names are verb-first and descriptive: `create_user`, `get_profile`, `validate_login`.
- Shared helpers (e.g. `hash_code`, `utc_now`) are defined once at module level and imported elsewhere — don't recreate them.
- A service may inject another feature's service or repository via `Depends()` (e.g. `AuthService` uses `UserService`, `MailService`).
- Only call repository methods that actually exist; add them to the repository first.

## 7. Router / controller (`app/<feature>/router.py`)

```python
from fastapi import APIRouter, Depends, status
from app.users.dto.CreateUser import CreateUser
from app.users.dto.UserResponse import UserResponse
from app.users.service import UserService
from app.auth.dependecies import get_current_user

router = APIRouter(prefix="/user", tags=['user'])

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: CreateUser, service: UserService = Depends()):
    return service.create_user(data)

@router.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return current_user
```

- Module-level `router = APIRouter(prefix="/<feature>", tags=['<feature>'])`.
- Endpoints are plain `def` (sync), one line of body: delegate to the service and return.
- Always set `response_model`; set `status_code=status.HTTP_201_CREATED` for creates.
- Request body param is named `data`; service param is `service: <Feature>Service = Depends()`.
- Protected endpoints add `current_user = Depends(get_current_user)` from `app.auth.dependecies`.
- Paths are lowercase kebab-case (`/sign-up`, `/me`).

## 8. Auth (password + email codes)

Users sign up with a password and verify their email with a code. Login is email + password only (no code).
Passwords are hashed with `pwdlib` (argon2) via `hash_password` / `verify_password` in `app/users/service.py` — reuse them.

| Endpoint | Body | Returns |
|---|---|---|
| `POST /sign-up` | `CreateUser` (first_name, last_name, email, password ≥ 8) | `UserResponse` 201, emails a `verify_email` code |
| `POST /verify-email` | `VerifyCodeRequest` (email, code) | `LoginResponse` (sets `users.email_verified_at`) |
| `POST /verify-email/resend` | `ResendVerificationRequest` (email) | `MessageResponse` |
| `POST /login` | `LoginRequest` (email, password) | `LoginResponse` (401 bad credentials, 403 email not verified) |

- Codes: 6 digits from `secrets`, stored **HMAC-SHA256 hashed** in `otp_codes` (`app/auth/models/otp_codes.py`),
  `purpose` is `verify_email`. Valid `OTP_EXPIRY_MINUTES` (default 5), single use, max `OTP_MAX_ATTEMPTS`
  (default 5) wrong tries; requesting a new code soft-deletes older ones. All of this lives in `AuthService.send_code` /
  `AuthService.check_code` + `OtpRepository` — reuse them, don't duplicate code logic.
- Time comparisons use `utc_now()` (naive UTC) from `app/auth/service.py`.
- Email goes through `MailService().send(to, subject, body)` in `app/mail/service.py` (SMTP via `SMTP_HOST`, `SMTP_PORT`,
  `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `MAIL_FROM`). Inject it with `Depends()`; never call `smtplib` elsewhere.
- JWT (PyJWT) payload: `{"sub": str(user.id), "exp": ...}`; secret `JWT_SECRET_KEY`, algorithm env `ALOGORITHM` (default `HS256`), expiry `ACCESS_TOKEN_EXPIRY` minutes. Build tokens only via `AuthService.create_token`.
- Use `get_current_user` (in `app/auth/dependecies.py`) to protect routes; do not re-implement token decoding.
- Authorization is permission-based RBAC (`app/roles/`): users → roles → permissions (no direct user permissions).
  Guard endpoints with `current_user = Depends(require_permissions("<resource>.<action>"))` (e.g. `product.view`), never by role name.
  Roles and permissions are only created by the seeder — there is no API to create/update/delete them.
  New permissions go into `default_permissions` / `default_roles` in `app/seeders/roles_seeder.py`; run `python -m app.seeders.roles_seeder`.
  The only role APIs are syncs (replace the whole set): `PUT /role/{role_id}/permissions` (`permission_ids`, `role.manage`)
  and `PUT /user/{user_id}/roles` (`role_ids`, `user.manage`).
  Seeders live in `app/seeders/`. `python -m app.seeders` (or `app.seeders.admin_seeder`) seeds roles, then creates a verified default admin from the constants in
  `app/seeders/admin_seeder.py` (`admin_email`, `admin_password`, ...) and gives it the `admin` role.

## 9. RAG + role agents (local Ollama via LangChain)

All AI runs on local Ollama (`OLLAMA_BASE_URL`, chat `OLLAMA_CHAT_MODEL` default `llama3.2`, embeddings
`OLLAMA_EMBEDDING_MODEL` default `nomic-embed-text`, `OLLAMA_NUM_CTX` default 8192). No hosted LLM APIs.

- Vector store: Chroma persisted in `CHROMA_DIR` (default `chroma_db`), collection `CHROMA_COLLECTION`.
  Only `app/knowledge/repository.py` (`KnowledgeRepository`) touches Chroma; `KnowledgeService` loads files
  (pdf/docx/txt/md), chunks them (`RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP`) and adds/removes vectors.
  Chunk metadata: `document_id`, `doc_type`, `title`, `product_id`, `page` — chunk ids are `"{document_id}-{i}"`.
- Documents are part of the `products` module (`app/products/models/documents.py`), always tied to a product, under
  `/product/{product_id}/documents`. Vectors follow them: upload ingests immediately (`ProductService.ingest`, failure →
  `ingest_status="failed"`, retry via `.../ingest`), update re-ingests, document delete and product delete remove vectors
  (`remove_document` / `remove_product`).
- Agents live in `app/assistant/service.py`: `agent_profiles` holds one profile per role (`product`, `technician`, `admin`)
  with its allowed `doc_types`, tools and system prompt. Customers' `product` agent never sees `repair_guide` chunks.
  Endpoints `POST /assistant/{product,technician,admin}-chat` are guarded by `assistant.<role>` permissions.
  Add a new role agent by adding a profile + endpoint + permission, not a new code path.
- Specifications, parts, how they work and repair steps are NOT tables: they live only in the product's documents and are
  answered from the vector store. Don't add tables or CRUD for them.
- `POST /product` is multipart: `CreateProduct` form fields + optional `files`. With files, `AssistantService.extract_product`
  fills only the empty product fields (name, model number, brand, category, description); the files are stored as the
  product's documents and ingested.

## 10. Checklist for a new API

1. Model in `app/<feature>/models/` (+ Alembic migration).
2. DTOs in `app/<feature>/dto/` — one class per file, file name = class name.
3. Repository methods (DB only, soft-delete aware, commit/rollback on writes).
4. Service methods (rules + `HTTPException`).
5. Router endpoints (thin, `response_model`, `Depends()` injection).
6. Empty `__init__.py` in every new package; include router in `app/main.py`.
