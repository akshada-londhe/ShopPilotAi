"""Unit tests for auth_users module and auth router endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth_users import create_user, authenticate_user, get_user_by_token, delete_user, _prepare_password

client = TestClient(app)

TEST_EMAIL = "test_unit_user@example.com"
TEST_NAME = "Unit Test User"
TEST_PASS = "securepassword123"


@pytest.fixture(autouse=True)
def cleanup():
    """Ensure test user is cleaned up before and after each test."""
    delete_user(TEST_EMAIL)
    yield
    delete_user(TEST_EMAIL)


def test_prepare_password_truncation():
    """Verify password preparation truncates long passwords without crashing."""
    short = _prepare_password("hello123")
    assert short == "hello123"

    long_pass = "a" * 100
    prepared = _prepare_password(long_pass)
    assert len(prepared.encode("utf-8")) <= 72


def test_create_and_authenticate_user():
    """Test user creation, token issuance, and authentication."""
    user = create_user(TEST_NAME, TEST_EMAIL, TEST_PASS)
    assert user["name"] == TEST_NAME
    assert user["email"] == TEST_EMAIL.lower()
    assert "token" in user

    # Authenticate with correct credentials
    authed = authenticate_user(TEST_EMAIL, TEST_PASS)
    assert authed["user_id"] == user["user_id"]
    assert "token" in authed

    # Verify token
    verified = get_user_by_token(authed["token"])
    assert verified is not None
    assert verified["email"] == TEST_EMAIL.lower()


def test_authenticate_wrong_password():
    """Test authentication failure on wrong password."""
    create_user(TEST_NAME, TEST_EMAIL, TEST_PASS)
    with pytest.raises(ValueError, match="Incorrect password"):
        authenticate_user(TEST_EMAIL, "wrongpassword")


def test_create_duplicate_user():
    """Test failure when registering duplicate email."""
    create_user(TEST_NAME, TEST_EMAIL, TEST_PASS)
    with pytest.raises(ValueError, match="already exists"):
        create_user(TEST_NAME, TEST_EMAIL, TEST_PASS)


def test_signup_endpoint():
    """Test POST /auth/signup API endpoint."""
    res = client.post(
        "/auth/signup",
        json={"name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASS},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == TEST_EMAIL.lower()
    assert "token" in data


def test_signin_endpoint():
    """Test POST /auth/signin API endpoint."""
    create_user(TEST_NAME, TEST_EMAIL, TEST_PASS)
    res = client.post(
        "/auth/signin",
        json={"email": TEST_EMAIL, "password": TEST_PASS},
    )
    assert res.status_code == 200
    data = res.json()
    assert "token" in data

    # Test /auth/me endpoint with token
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {data['token']}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == TEST_EMAIL.lower()
