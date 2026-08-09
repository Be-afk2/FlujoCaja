def test_crear_usuario(client, registrar_usuario):
    usuario = registrar_usuario("ana")
    assert "id" in usuario
    assert usuario["name"] == "ana"
    assert "passw" not in usuario
    assert "apellido" not in usuario


def test_login_ok(client, registrar_usuario, login):
    registrar_usuario("bruno")
    data = login("bruno")
    assert "token" in data
    assert data["user"]["name"] == "bruno"


def test_login_credenciales_invalidas(client, registrar_usuario):
    registrar_usuario("carla")
    r = client.post("/auth/login", json={"name": "carla", "passw": "incorrecta", "recordar": False})
    assert r.status_code == 401
    assert r.headers.get("www-authenticate") == "Bearer"


def test_sesion_actual(client, auth_headers):
    headers = auth_headers("diego")
    r = client.get("/auth", headers=headers)
    assert r.status_code == 200
    assert r.json()["user"]["name"] == "diego"


def test_logout(client, auth_headers):
    headers = auth_headers("elena")
    r = client.delete("/auth", headers=headers)
    assert r.status_code == 200

    r = client.get("/auth", headers=headers)
    assert r.status_code == 401
