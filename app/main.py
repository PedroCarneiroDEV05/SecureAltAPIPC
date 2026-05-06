from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.bootstrap_admin import ensure_bootstrap_admin
from app.db.database import SessionLocal, engine, Base, ensure_users_is_admin_column
from app.routes import auth, oauth
from app.core.config import settings

Base.metadata.create_all(bind=engine)
ensure_users_is_admin_column()
_db = SessionLocal()
try:
    ensure_bootstrap_admin(_db)
finally:
    _db.close()

app = FastAPI(
    title=settings.APP_NAME,
    debug=(str(settings.ENVIRONMENT).lower() == "development"),
    version="1.0.0",
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(oauth.router)


@app.get("/")
def root():
    return {"message": "Bem-vindo ao Sistema de Autenticação API", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
