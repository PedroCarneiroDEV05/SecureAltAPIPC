import json

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.deps.auth_deps import get_current_user
from app.schemas.user_schema import UserCreate, UserResponse, Token
from app.services import auth_service
from app.core.security import create_access_token
from app.core.admin_guard import require_admin
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Cookies seguros exigem HTTPS; em desenvolvimento local usam HTTP.
_COOKIE_SECURE = str(settings.ENVIRONMENT).lower() == "production"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return auth_service.create_user(db, user)


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    content_type = (request.headers.get("content-type") or "").lower()
    email = None
    login_password = None

    if "application/json" in content_type:
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corpo JSON inválido",
            )
        if isinstance(payload, dict):
            email = payload.get("email")
            login_password = payload.get("password")
    else:
        form_data = await request.form()
        email = form_data.get("username") or form_data.get("email")
        login_password = form_data.get("password")

    if not email or not login_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Credenciais ausentes",
        )

    user = auth_service.authenticate_user(db, email, login_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = auth_service.create_user_refresh_token(db, user_id=user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Issues a new access + refresh token pair using the HTTPOnly cookie.
    Returns 401 if the cookie is absent, expired, or already revoked (replay detection).
    """
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token ausente",
        )

    result = auth_service.refresh_access_token(db, raw_token)

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    return result


@router.post("/logout")
def logout(response: Response):
    """Remove o cookie de refresh token."""
    response.delete_cookie(key="refresh_token", samesite="lax")
    return {"message": "Logout realizado com sucesso"}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/admin/check")
def admin_check_dev_only(_admin: User = Depends(require_admin)):
    """Diagnóstico disponível apenas em desenvolvimento."""
    if str(settings.ENVIRONMENT).lower() != "development":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"status": "ok", "admin": True}
