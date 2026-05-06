from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from app.db.database import get_db
from app.services import oauth_service, auth_service
from app.core.security import create_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth/google", tags=["Google OAuth"])

# Cookies seguros exigem HTTPS; em desenvolvimento local usam HTTP.
_COOKIE_SECURE = str(settings.ENVIRONMENT).lower() == "production"

# OAuth só é habilitado com credenciais reais do Google.
_GOOGLE_CONFIGURED = bool(
    settings.GOOGLE_CLIENT_ID
    and settings.GOOGLE_CLIENT_ID not in ("", "seu_client_id.apps.googleusercontent.com")
    and settings.GOOGLE_CLIENT_SECRET
    and settings.GOOGLE_CLIENT_SECRET not in ("", "seu_client_secret")
)


def _require_google():
    """Bloqueia o fluxo quando o OAuth não está configurado."""
    if not _GOOGLE_CONFIGURED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Google OAuth não está configurado. "
                "Defina GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET no arquivo .env."
            ),
        )


@router.get("/login")
async def google_login(response: Response, _: None = Depends(_require_google)):
    state = oauth_service.generate_state_token()
    auth_url = await oauth_service.get_google_auth_url(state)

    redirect_response = RedirectResponse(url=auth_url)
    redirect_response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="lax",
        max_age=600,
    )
    return redirect_response


@router.get("/callback")
async def google_callback(
    request: Request,
    response: Response,
    code: str,
    state: str,
    db: Session = Depends(get_db),
    _: None = Depends(_require_google),
):
    """Valida o retorno do Google e cria a sessão local."""
    # Proteção CSRF: o state da URL deve bater com o cookie HTTPOnly.
    state_cookie = request.cookies.get("oauth_state")
    if not state_cookie or state_cookie != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State inválido ou expirado. Possível ataque CSRF.",
        )

    tokens = await oauth_service.get_google_tokens(code)
    id_token = tokens.get("id_token")

    profile = await oauth_service.validate_google_id_token(id_token)
    user = oauth_service.authenticate_or_create_google_user(db, profile)

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = auth_service.create_user_refresh_token(db, user_id=user.id)

    redirect_url = f"{settings.FRONTEND_URL}/auth-callback#access_token={access_token}"
    redirect_response = RedirectResponse(url=redirect_url)

    redirect_response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    redirect_response.delete_cookie(key="oauth_state")

    return redirect_response
