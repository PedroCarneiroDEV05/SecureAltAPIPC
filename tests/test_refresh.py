import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db
from app.models.user import User, RefreshToken

# Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_refresh.db"
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

def test_refresh_token_rotation():
    """Valida que o refresh token é rotacionado (antigo invalidado, novo gerado)."""
    # 1. Login inicial
    client.post("/auth/register", json={"email": "refresh@test.com", "password": "password"})
    login_res = client.post("/auth/login", data={"username": "refresh@test.com", "password": "password"})
    old_refresh_token = login_res.json()["refresh_token"]

    # 2. Primeiro Refresh (Sucesso)
    refresh_res = client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
    assert refresh_res.status_code == 200
    new_refresh_token = refresh_res.json()["refresh_token"]
    assert new_refresh_token != old_refresh_token

    # 3. Verifica no banco se o antigo foi revogado
    db = TestingSessionLocal()
    # Buscamos pelo hash do token antigo (simulando a lógica do service)
    from app.core.security import hash_refresh_token
    old_hash = hash_refresh_token(old_refresh_token)
    old_token_db = db.query(RefreshToken).filter(RefreshToken.token_hash == old_hash).first()
    assert old_token_db.revoked is True
    db.close()

def test_refresh_token_reuse_detection():
    """TESTE DE SEGURANÇA: Se um token revogado for reusado, todas as sessões caem."""
    client.post("/auth/register", json={"email": "security@test.com", "password": "password"})
    
    # Gera dois tokens (duas sessões)
    res1 = client.post("/auth/login", data={"username": "security@test.com", "password": "password"})
    res2 = client.post("/auth/login", data={"username": "security@test.com", "password": "password"})
    
    token_v1 = res1.json()["refresh_token"]
    token_sessao_2 = res2.json()["refresh_token"]

    # Usa o token_v1 uma vez (ele vira v2 e o v1 é revogado)
    client.post("/auth/refresh", json={"refresh_token": token_v1})

    # Tenta usar o token_v1 (já revogado) de novo -> ATAQUE DE REPLAY DETECTADO
    replay_res = client.post("/auth/refresh", json={"refresh_token": token_v1})
    assert replay_res.status_code == 401
    assert "Alerta de seguran\u00e7a" in replay_res.json()["detail"]

    # Verifica se a Sessão 2 também foi revogada automaticamente
    db = TestingSessionLocal()
    tokens_revogados = db.query(RefreshToken).filter(RefreshToken.revoked == True).count()
    # Devem existir 3 tokens revogados: o v1 (normal), o v2 (pela detecção) e a Sessão 2 (pela detecção)
    # Na verdade, todos os tokens desse user_id devem estar revoked=True
    total_tokens = db.query(RefreshToken).count()
    assert tokens_revogados == total_tokens
    db.close()
