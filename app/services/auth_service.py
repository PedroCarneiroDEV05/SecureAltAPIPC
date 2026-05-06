from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, RefreshToken
from app.schemas.user_schema import UserCreate
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.bootstrap_admin import email_is_config_admin
from app.core.config import settings


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado",
        )

    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        provider="local",
        is_admin=email_is_config_admin(str(user.email)),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not user.hashed_password:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_user_refresh_token(db: Session, user_id: int) -> str:
    """Cria um refresh token e salva apenas seu hash no banco."""
    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_token = RefreshToken(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return raw_token


def refresh_access_token(db: Session, refresh_token: str):
    """Rotaciona o refresh token e detecta reuso de tokens revogados."""
    token_hash = hash_refresh_token(refresh_token)
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if not db_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    if db_token.revoked:
        # Reuso de token revogado: encerra todas as sessões do usuário.
        db.query(RefreshToken).filter(RefreshToken.user_id == db_token.user_id).update({"revoked": True})
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Alerta de segurança: Token já utilizado. Todas as sessões foram encerradas.",
        )

    if db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        db_token.revoked = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")

    db_token.revoked = True
    db.commit()

    new_access_token = create_access_token(data={"sub": db_token.user.email})
    new_refresh_token = create_user_refresh_token(db, user_id=db_token.user_id)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
