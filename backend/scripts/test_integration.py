"""End-to-end integration test script for ShopPilot AI APIs and wirings."""

import sys
import json
import urllib.request
import urllib.error

BACKEND_URL = "http://localhost:8001"
API_KEY = "gg"

def run_test(name, fn):
    try:
        fn()
        print(f"  [OK] {name}")
        return True
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        return False

print("=== Running ShopPilot AI Integration Tests ===")

results = []

def test_health():
    req = urllib.request.Request(f"{BACKEND_URL}/health")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data.get("status") == "ok"

results.append(run_test("GET /health endpoint", test_health))

import uuid

def test_auth_signup():
    url = f"{BACKEND_URL}/auth/signup"
    test_email = f"e2e_{uuid.uuid4().hex[:8]}@example.com"
    payload = json.dumps({
        "name": "Integration Test User",
        "email": test_email,
        "password": "IntegrationPassword123"
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        data = json.loads(resp.read().decode())
        assert "token" in data
        assert data["email"] == test_email

results.append(run_test("POST /auth/signup endpoint", test_auth_signup))

def test_auth_signin():
    url = f"{BACKEND_URL}/auth/signin"
    payload = json.dumps({
        "email": "e2e_integration_test@example.com",
        "password": "IntegrationPassword123"
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "token" in data
        token = data["token"]
        
        # Test /auth/me with Bearer token
        me_req = urllib.request.Request(f"{BACKEND_URL}/auth/me", headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(me_req) as me_resp:
            assert me_resp.status == 200
            me_data = json.loads(me_resp.read().decode())
            assert me_data["email"] == "e2e_integration_test@example.com"

results.append(run_test("POST /auth/signin and GET /auth/me endpoints", test_auth_signin))

def test_search_api():
    url = f"{BACKEND_URL}/api/v1/search"
    payload = json.dumps({"query": "best wireless noise canceling headphones under 5000"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        lines = resp.read().decode().split("\n\n")
        assert len(lines) > 0
        events = [json.loads(line.replace("data: ", "")) for line in lines if line.startswith("data: ")]
        assert len(events) > 0
        assert events[0]["event"] in ["progress", "needs_clarification", "result"]

results.append(run_test("POST /api/v1/search SSE streaming endpoint", test_search_api))

def test_saved_api():
    url = f"{BACKEND_URL}/api/v1/saved"
    req = urllib.request.Request(url, headers={"X-API-Key": API_KEY})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "products" in data

results.append(run_test("GET /api/v1/saved ChromaDB endpoint", test_saved_api))

print("===============================================")
if all(results):
    print("ALL INTEGRATION TESTS PASSED SUCCESSFULLY! [OK]")
    sys.exit(0)
else:
    print("SOME INTEGRATION TESTS FAILED [FAIL]")
    sys.exit(1)
