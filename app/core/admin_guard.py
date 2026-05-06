from fastapi import Depends, HTTPException, status

from app.deps.auth_deps import get_current_user
from app.models.user import User


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Requires an authenticated admin. Use via Depends(require_admin) on admin-only routes."""
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return current_user
