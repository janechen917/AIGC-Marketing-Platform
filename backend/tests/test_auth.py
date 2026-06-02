def test_register_login_me_flow(client):
    register_payload = {
        "email": "tester@example.com",
        "password": "Password123",
    }
    r1 = client.post("/api/auth/register", json=register_payload)
    assert r1.status_code == 201
    user = r1.json()
    assert user["email"] == "tester@example.com"
    assert user["role"] == "user"

    r2 = client.post(
        "/api/auth/login",
        data={"username": "tester@example.com", "password": "Password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r2.status_code == 200
    login_data = r2.json()
    assert login_data["token_type"] == "bearer"
    assert "access_token" in login_data

    token = login_data["access_token"]
    r3 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    me = r3.json()
    assert me["email"] == "tester@example.com"


def test_register_conflict(client):
    payload = {"email": "dup@example.com", "password": "Password123"}
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 409
