import secrets
import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.core.config import settings
from app.models.user import User, AuthProvider
from app.bootstrap_admin import email_is_config_admin
from app.services import auth_service

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


def generate_state_token() -> str:
    """Gera um token aleatório para proteção CSRF."""
    return secrets.token_urlsafe(32)


async def get_google_auth_url(state: str) -> str:
    """Gera a URL de autorização do Google OAuth."""
    async with httpx.AsyncClient() as client:
        response = await client.get(GOOGLE_DISCOVERY_URL)
        config = response.json()
        authorization_endpoint = config.get("authorization_endpoint")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }

    query_params = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{authorization_endpoint}?{query_params}"


async def get_google_tokens(code: str):
    """Troca o código de autorização pelos tokens do Google."""
    async with httpx.AsyncClient() as client:
        response = await client.get(GOOGLE_DISCOVERY_URL)
        token_endpoint = response.json().get("token_endpoint")

        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        token_response = await client.post(token_endpoint, data=data)
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falha ao trocar código por tokens no Google",
            )
        return token_response.json()


async def validate_google_id_token(id_token: str) -> dict:
    """
    Valida claims essenciais do ID Token.

    Em produção, a assinatura deve ser validada com as chaves públicas do Google.
    """
    try:
        payload = jwt.get_unverified_claims(id_token)

        if payload.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            raise JWTError("Issuer inválido")

        if payload.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise JWTError("Audience inválida")

        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token do Google inválido: {str(e)}",
        )


def authenticate_or_create_google_user(db: Session, profile: dict) -> User:
    """Vincula conta existente por e-mail ou cria novo usuário Google."""
    email = profile.get("email")
    google_id = profile.get("sub")

    user = auth_service.get_user_by_email(db, email)

    if user:
        if email_is_config_admin(email):
            user.is_admin = True
            db.commit()
            db.refresh(user)
        if user.provider != AuthProvider.GOOGLE:
            user.provider = AuthProvider.GOOGLE
            user.provider_id = google_id
            db.commit()
            db.refresh(user)
        return user

    new_user = User(
        email=email,
        provider=AuthProvider.GOOGLE,
        provider_id=google_id,
        hashed_password=None,
        is_admin=email_is_config_admin(email),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
