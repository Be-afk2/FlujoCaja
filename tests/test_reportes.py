from datetime import date


def _hoy_api() -> str:
    return date.today().strftime("%d-%m-%Y")


def _sumar(resumenes, campo):
    return sum(r[campo] for r in resumenes)


def _crear_datos_reporte(
    client, headers, crear_cuenta, crear_tipo, crear_movimiento, crear_entidad, crear_deuda, obtener_moneda
):
    moneda_id = obtener_moneda(headers)
    cuenta = crear_cuenta(headers)
    tipo = crear_tipo(headers, nombre="Reporte")
    fecha = _hoy_api()

    crear_movimiento(headers, cuenta["id"], 1000.0, tipo_id=tipo["id"], fecha=fecha)
    crear_movimiento(headers, cuenta["id"], -200.0, tipo_id=tipo["id"], fecha=fecha)

    entidad = crear_entidad(headers)
    deuda_ingreso = crear_deuda(
        headers,
        entidad["id"],
        monto=500.0,
        direccion="pagar",
        moneda_id=moneda_id,
        cuenta_inicial_id=cuenta["id"],
        fecha=fecha,
    )
    deuda_gasto = crear_deuda(
        headers,
        entidad["id"],
        monto=300.0,
        direccion="cobrar",
        moneda_id=moneda_id,
        cuenta_inicial_id=cuenta["id"],
        fecha=fecha,
    )
    return moneda_id, deuda_ingreso, deuda_gasto


def test_resumen_mensual_incluir_deudas_false_resta_desglose(
    client,
    auth_headers,
    crear_cuenta,
    crear_tipo,
    crear_movimiento,
    crear_entidad,
    crear_deuda,
    obtener_moneda,
):
    headers = auth_headers("reporte1")
    moneda_id, _, _ = _crear_datos_reporte(
        client,
        headers,
        crear_cuenta,
        crear_tipo,
        crear_movimiento,
        crear_entidad,
        crear_deuda,
        obtener_moneda,
    )
    hoy = date.today()
    params = {"anio": hoy.year, "mes": hoy.month, "moneda_id": moneda_id}

    con_deudas = client.get("/resumen/mensual", params=params, headers=headers).json()
    assert _sumar(con_deudas, "total_ingresos") == 1500.0
    assert _sumar(con_deudas, "total_gastos") == 500.0
    assert _sumar(con_deudas, "neto") == 1000.0
    assert _sumar(con_deudas, "total_ingresos_deuda") == 500.0
    assert _sumar(con_deudas, "total_gastos_deuda") == 300.0

    sin_deudas = client.get(
        "/resumen/mensual",
        params={**params, "incluir_deudas": "false"},
        headers=headers,
    ).json()
    assert _sumar(sin_deudas, "total_ingresos") == 1000.0
    assert _sumar(sin_deudas, "total_gastos") == 200.0
    assert _sumar(sin_deudas, "neto") == 800.0
    assert _sumar(sin_deudas, "total_ingresos_deuda") == 500.0
    assert _sumar(sin_deudas, "total_gastos_deuda") == 300.0


def test_resumen_anual_y_rango_incluir_deudas_false(
    client,
    auth_headers,
    crear_cuenta,
    crear_tipo,
    crear_movimiento,
    crear_entidad,
    crear_deuda,
    obtener_moneda,
):
    headers = auth_headers("reporte2")
    moneda_id, _, _ = _crear_datos_reporte(
        client,
        headers,
        crear_cuenta,
        crear_tipo,
        crear_movimiento,
        crear_entidad,
        crear_deuda,
        obtener_moneda,
    )
    hoy = date.today()

    anual = client.get(
        "/resumen/anual",
        params={
            "anio": hoy.year,
            "moneda_id": moneda_id,
            "incluir_deudas": "false",
        },
        headers=headers,
    ).json()
    assert _sumar(anual, "total_ingresos") == 1000.0
    assert _sumar(anual, "total_gastos") == 200.0

    periodo = f"{hoy.year}-{hoy.month:02d}"
    rango = client.get(
        "/resumen/rango",
        params={
            "desde": periodo,
            "hasta": periodo,
            "moneda_id": moneda_id,
            "incluir_deudas": "false",
        },
        headers=headers,
    ).json()
    assert _sumar(rango, "total_ingresos") == 1000.0
    assert _sumar(rango, "total_gastos") == 200.0


def test_filtro_movimientos_por_es_deuda(
    client,
    auth_headers,
    crear_cuenta,
    crear_tipo,
    crear_movimiento,
    crear_entidad,
    crear_deuda,
    obtener_moneda,
):
    headers = auth_headers("reporte3")
    _crear_datos_reporte(
        client,
        headers,
        crear_cuenta,
        crear_tipo,
        crear_movimiento,
        crear_entidad,
        crear_deuda,
        obtener_moneda,
    )

    solo_deuda = client.get(
        "/movimientos/", params={"es_deuda": "true"}, headers=headers
    ).json()
    assert solo_deuda["total"] == 2
    assert all(m["es_deuda"] is True for m in solo_deuda["data"])

    sin_deuda = client.get(
        "/movimientos/", params={"es_deuda": "false"}, headers=headers
    ).json()
    assert sin_deuda["total"] == 2
    assert all(m["es_deuda"] is False for m in sin_deuda["data"])


def test_movimiento_de_deuda_no_se_edita_ni_elimina_desde_movimientos(
    client,
    auth_headers,
    crear_cuenta,
    crear_tipo,
    crear_movimiento,
    crear_entidad,
    crear_deuda,
    obtener_moneda,
):
    headers = auth_headers("reporte4")
    moneda_id, deuda_ingreso, _ = _crear_datos_reporte(
        client,
        headers,
        crear_cuenta,
        crear_tipo,
        crear_movimiento,
        crear_entidad,
        crear_deuda,
        obtener_moneda,
    )
    assert moneda_id > 0
    mov_id = deuda_ingreso["movimiento_inicial_id"]
    assert mov_id is not None

    r = client.put(f"/movimientos/{mov_id}", json={"monto": 1.0}, headers=headers)
    assert r.status_code == 400
    assert "deuda" in r.json()["error"].lower()

    r = client.delete(f"/movimientos/{mov_id}", headers=headers)
    assert r.status_code == 400
    assert "deuda" in r.json()["error"].lower()

    mov = client.get(f"/movimientos/{mov_id}", headers=headers)
    assert mov.status_code == 200
    assert mov.json()["es_deuda"] is True


def test_recalcular_resumen_reconstruye_totales_por_mes(
    client, auth_headers, crear_cuenta, crear_tipo, crear_movimiento, obtener_moneda
):
    headers = auth_headers("reporte_recalcular")
    moneda_id = obtener_moneda(headers)
    cuenta = crear_cuenta(headers)
    tipo = crear_tipo(headers, nombre="Recalculo")
    anio = date.today().year

    crear_movimiento(headers, cuenta["id"], 400.0, tipo_id=tipo["id"], fecha=f"15-01-{anio}")
    crear_movimiento(headers, cuenta["id"], 1000.0, tipo_id=tipo["id"], fecha=f"15-02-{anio}")
    crear_movimiento(headers, cuenta["id"], -250.0, tipo_id=tipo["id"], fecha=f"15-02-{anio}")

    r = client.post("/resumen/recalcular", headers=headers)
    assert r.status_code == 200, r.text
    assert "2" in r.json()["message"]

    # Idempotente: recalcular otra vez no duplica filas.
    assert client.post("/resumen/recalcular", headers=headers).status_code == 200

    filas = client.get(
        "/resumen/anual",
        params={"anio": anio, "moneda_id": moneda_id},
        headers=headers,
    ).json()
    assert len(filas) == 2
    assert _sumar(filas, "total_ingresos") == 1400.0
    assert _sumar(filas, "total_gastos") == 250.0
    assert _sumar(filas, "total_gastos_deuda") == 0.0


def test_listado_rechaza_cantidad_fuera_del_tope(client, auth_headers):
    headers = auth_headers("reporte_tope")

    excedido = client.get(
        "/movimientos/", params={"cantidad": 100000}, headers=headers
    )
    assert excedido.status_code == 422

    valido = client.get(
        "/movimientos/", params={"cantidad": 1000}, headers=headers
    )
    assert valido.status_code == 200


def test_exportar_movimientos_csv_respeta_filtros(
    client, auth_headers, crear_cuenta, crear_tipo, crear_movimiento
):
    headers = auth_headers("reporte_export")
    cuenta = crear_cuenta(headers)
    tipo = crear_tipo(headers, nombre="Export")
    crear_movimiento(
        headers,
        cuenta["id"],
        1500.0,
        tipo_id=tipo["id"],
        descripcion="Sueldo, marzo",
    )
    crear_movimiento(
        headers,
        cuenta["id"],
        -200.0,
        tipo_id=tipo["id"],
        descripcion="Luz",
    )

    r = client.get("/movimientos/exportar", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]

    lineas = r.content.decode("utf-8-sig").strip().splitlines()
    assert lineas[0] == "fecha,monto,tipo,cuenta,descripcion"
    assert len(lineas) == 3
    # El nombre del tipo/cuenta se resuelve en el servidor y la coma se escapa.
    assert any('"Sueldo, marzo"' in linea for linea in lineas)
    assert any("Export" in linea and cuenta["nombre"] in linea for linea in lineas)

    solo_gastos = client.get(
        "/movimientos/exportar", params={"es_ingreso": "false"}, headers=headers
    )
    lineas_gastos = solo_gastos.content.decode("utf-8-sig").strip().splitlines()
    assert len(lineas_gastos) == 2
    assert "Luz" in lineas_gastos[1]
