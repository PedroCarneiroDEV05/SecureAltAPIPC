import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db

# Banco de dados de teste (em memória)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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

def test_register_user():
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login_user():
    # Primeiro registra
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "loginpassword"}
    )
    
    # Tenta login
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "loginpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password():
    client.post(
        "/auth/register",
        json={"email": "wrong@example.com", "password": "correctpassword"}
    )
    
    response = client.post(
        "/auth/login",
        data={"username": "wrong@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou senha incorretos"

def test_register_duplicate_email():
    client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "password"}
    )
    response = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "password"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email já cadastrado"

def test_access_protected_route():
    # Registra e loga
    client.post(
        "/auth/register",
        json={"email": "protected@example.com", "password": "password"}
    )
    login_response = client.post(
        "/auth/login",
        data={"username": "protected@example.com", "password": "password"}
    )
    token = login_response.json()["access_token"]
    
    # Acessa /me
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "protected@example.com"

def test_access_protected_route_invalid_token():
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401
