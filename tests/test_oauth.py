import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db
from app.models.user import User, AuthProvider
from jose import jwt

# Setup do Banco de Testes
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_oauth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_google_login_redirect():
    """Valida se o endpoint de login redireciona e define o cookie state."""
    response = client.get("/auth/google/login", follow_redirects=False)
    assert response.status_code == 302
    assert "accounts.google.com" in response.headers["location"]
    assert "oauth_state" in response.cookies

@pytest.mark.asyncio
async def test_google_callback_invalid_state():
    """Valida que o callback falha se o state for diferente do cookie."""
    client.get("/auth/google/login") # Define o cookie
    response = client.get("/auth/google/callback?code=abc&state=wrong_state")
    assert response.status_code == 400
    assert "State inv\u00e1lido" in response.json()["detail"]

@pytest.mark.asyncio
async def test_google_callback_success_new_user(httpx_mock):
    """Simula sucesso no OAuth criando um novo usuário."""
    # 1. Mock do Discovery do Google
    httpx_mock.add_response(
        url="https://accounts.google.com/.well-known/openid-configuration",
        json={
            "token_endpoint": "https://oauth2.googleapis.com/token",
            "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth"
        }
    )
    
    # 2. Mock do Token Endpoint
    # Geramos um ID Token fake (Google assina isso, aqui estamos apenas criando os claims)
    fake_id_token = jwt.encode(
        {"iss": "https://accounts.google.com", "sub": "12345", "email": "new@google.com", "aud": "seu_client_id.apps.googleusercontent.com"},
        "secret", algorithm="HS256"
    )
    
    httpx_mock.add_response(
        method="POST",
        url="https://oauth2.googleapis.com/token",
        json={"id_token": fake_id_token, "access_token": "fake_access"}
    )

    # 3. Executa o fluxo
    login_res = client.get("/auth/google/login", follow_redirects=False)
    state = login_res.cookies.get("oauth_state")
    
    response = client.get(f"/auth/google/callback?code=valid_code&state={state}")
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    
    # Verifica se usuário foi criado no banco
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "new@google.com").first()
    assert user is not None
    assert user.provider == AuthProvider.GOOGLE
    db.close()

@pytest.mark.asyncio
async def test_google_callback_link_existing_user(httpx_mock):
    """Simula sucesso no OAuth vinculando a um usuário já existente."""
    # Cria usuário local primeiro
    db = TestingSessionLocal()
    db.add(User(email="existing@google.com", provider=AuthProvider.LOCAL))
    db.commit()
    db.close()

    httpx_mock.add_response(
        url="https://accounts.google.com/.well-known/openid-configuration",
        json={"token_endpoint": "https://oauth2.googleapis.com/token"}
    )
    
    fake_id_token = jwt.encode(
        {"iss": "https://accounts.google.com", "sub": "999", "email": "existing@google.com", "aud": "seu_client_id.apps.googleusercontent.com"},
        "secret", algorithm="HS256"
    )
    
    httpx_mock.add_response(method="POST", url="https://oauth2.googleapis.com/token", json={"id_token": fake_id_token})

    login_res = client.get("/auth/google/login", follow_redirects=False)
    state = login_res.cookies.get("oauth_state")
    
    client.get(f"/auth/google/callback?code=code&state={state}")

    # Verifica se o provedor foi atualizado
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "existing@google.com").first()
    assert user.provider == AuthProvider.GOOGLE
    assert user.provider_id == "999"
    db.close()
