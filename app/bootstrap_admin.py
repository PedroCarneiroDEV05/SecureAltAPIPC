import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, AuthProvider

logger = logging.getLogger("app.bootstrap_admin")
DEV_ADMIN_EMAIL = "admin@example.com"
DEV_ADMIN_PASSWORD = "admin123"


def email_is_config_admin(email: str | None) -> bool:
    if not email or not settings.ADMIN_EMAIL or not str(settings.ADMIN_EMAIL).strip():
        return False
    return email.strip().lower() == str(settings.ADMIN_EMAIL).strip().lower()


def ensure_bootstrap_admin(db: Session) -> None:
    env = str(settings.ENVIRONMENT).lower()
    admin_email_cfg = str(settings.ADMIN_EMAIL).strip() if settings.ADMIN_EMAIL else ""

    if env == "production" and not admin_email_cfg:
        logger.warning(
            "ADMIN_EMAIL is not set in production. "
            "Set ADMIN_EMAIL in your environment so designated accounts can be promoted to admin."
        )

    if admin_email_cfg:
        user = db.query(User).filter(User.email == admin_email_cfg).first()
        if user and not user.is_admin:
            user.is_admin = True
            db.commit()

    if env != "development":
        return

    existing = db.query(User).filter(User.email == DEV_ADMIN_EMAIL).first()
    if existing:
        if not existing.is_admin:
            existing.is_admin = True
            db.commit()
        return

    admin = User(
        email=DEV_ADMIN_EMAIL,
        hashed_password=get_password_hash(DEV_ADMIN_PASSWORD),
        provider=AuthProvider.LOCAL,
        is_admin=True,
    )
    db.add(admin)
    db.commit()
