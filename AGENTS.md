# FlujoCaja — AGENTS.md

## Entrypoints

- `main.py` — main app: starts DB → API (Uvicorn on `127.0.0.1:8000`) → PyQt6 WebEngine desktop window
- `app.py` — legacy CLI, still present under `menus/` and `widget/`

## Run commands

```powershell
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt     # dev only (pytest, httpx, ruff)
python main.py                  # full app (BD + API + web)
python main.py --api            # API only
python main.py --api --debug    # API with debug logging
python main.py --bd             # DB init only
python main.py --web            # web shell only
python -m pytest tests -v       # run tests (or .\run_tests.ps1)
python -m ruff check tests api/mainApi.py   # lint scoped (or .\run_lint.ps1)
```

## Architecture

- **Backend:** FastAPI (`api/mainApi.py`), routers in `api/routers/`
- **DB:** SQLite (`database.db`), SQLModel (`bd/models/`), CRUD in `bd/crud/`
- **Frontend:** static HTML/JS/Tailwind via CDN in `web/`, loaded by PyQt6 WebEngine
- **Auth:** simple SQLite token (single-session, no JWT). Bearer token via `Authorization` header. Validated against `sesion` table.
  - Unprotected routes: `/auth/*` (login, register, session check), `/health`
  - Protected routes (require `Depends(validate_token)`): `/movimientos`, `/tipos`, `/subtipos`, `/cuentas`, `/monedas`, `/resumen`, `/entidades`, `/deudas`, `/deudas-mensuales`, `/health/token`, `/auth/me`, `/datos`
- **Session:** Single session row in DB. Auth via `Authorization: Bearer <token>`, validated by `validate_token()` in `api/dependencies.py` which resolves the `User`. Legacy `obtener_sesion()` still present but deprecated.
- `database.db` is gitignored; auto-created on first run.

## Key refactors (Fase 4 — API mantenible)

- Routes renamed: `/cuenta` → `/cuentas`, `/moneda` → `/monedas`, `/auth/create` → `/auth/register`, `/auth/life/*` → `/health/*`
- DTOs introduced: `CuentaResponse`, `MonedaResponse`, `MovimientoListResponse`, `TipoListResponse`, `TipoDetailResponse`; `response_model` on every endpoint
- `RequestValidationError` handler normalizes 422 to `{"error", "status", "path", "details"}`
- Auth errors return 401 with `WWW-Authenticate` header
- CORS restricted to `["http://127.0.0.1:8000", "http://localhost:8000"]`
- `FastAPI(title=..., description=..., version="0.4.0")` with `tags` on all routers
- All POST creation endpoints have `status_code=201`

## Key refactors (Fase 8 — Perfil, contraseña, backup/restaurar)

- `/auth/me` GET returns current user (DTO `MeResponse`); PUT updates `name`/`apellido` (`UserProfileUpdate`, 400 si vacío); PUT `/auth/me/password` valida contraseña actual (`PasswordChange`, bcrypt)
- `actualizar_perfil` / `cambiar_contrasena` in `bd/crud/user.py` — **convierten `user_id` str → `UUID`** antes de `session.get` (User.id es UUID)
- `/datos/backup` GET → SQLite `src.backup(dst)` a archivo temporal + `FileResponse` (se auto-elimina vía `BackgroundTask`)
- `/datos/restaurar` POST multipart (`UploadFile`) → valida header SQLite, `engine.dispose()`, reemplaza `database.db`, `PRAGMA integrity_check`
- `python-multipart` añadido a `requirements.txt` (necesario para `UploadFile`)
- Frontend: botones backup/restaurar activos en `ajustes.html`, helpers `downloadFile()`/`uploadFile()` en `funciones.js`

## Key refactors (Fase 9 — Entidades y deudas)

- Modelos `Entidad`, `Deuda`, `PagoDeuda`; `Movimiento.es_deuda`; desglose `total_ingresos_deuda`/`total_gastos_deuda` en `ResumenMensual`.
- CRUD atómico en `bd/crud/entidad.py` / `bd/crud/deuda.py`: deuda/pago + movimiento + saldo + resumen en la misma transacción.
- Reglas: montos siempre positivos, signo según `direccion` (`cobrar`/`pagar`); `pendiente = monto_original − abonos`; estados `pendiente|vencida|pagada`; sobrepago → 400.
- API: `/entidades` (listar con saldos por moneda, detalle, CRUD; DELETE bloqueado si tiene deudas) y `/deudas` (CRUD, `POST/PUT/DELETE /deudas/{id}/pagos`, filtros `entidad_id`/`direccion`/`estado`).
- `PagoDeudaResponse.moneda_distinta` se calcula comparando la moneda de la cuenta con la de la deuda (sin conversión); el detalle de entidad no lo incluye, el frontend lo deduce con `cuentas`.
- Editar deuda con abonos: solo permite `descripcion`/`vencimiento`; `monto_original`/`moneda_id`/`direccion` quedan bloqueados.
- Frontend: `web/pages/deudas.html` + `web/js/deudas.js` + `web/css/deudas.css`; dos paneles, filtros por moneda/tipo/dirección/estado, modales de entidad/deuda/pago y confirmaciones de borrado.
- Sidebar: ítem "Deudas" en `web/components/sidemenu.html`; helpers `cargarSelectorMonedas()`/`escaparHtml()` y `cargarSelectorCuentas()` con `data-moneda` en `funciones.js`.
- Fechas de escritura en `dd-mm-YYYY` (`fechaParaAPI`); respuestas de la API en ISO.

## Key refactors (Fase 10 — Deudas mensuales)

- Modelos `DeudaMensual` (plantilla), `CuotaMensual` (ocurrencia) y `PagoCuotaMensual` (pago 1:1 con cuota y movimiento); `Entidad.deudas_mensuales`. Exportados en `bd/models/__init__.py`.
- Modalidades: `recurrente` (`monto_modo=fijo`, usa `monto_cuota`) y `cuotas` (`monto_modo=calculado`, usa `monto_total` + `cuotas_totales`). Plantilla `activa|cancelada`; cuota `pendiente|pagada|cancelada`; `estado_pago` en pagadas `antes_de_tiempo|al_dia|atrasada`.
- Reglas puras en `bd/domain/deuda_mensual.py`: días 1-31 ajustados al último del mes; si `dia_limite < dia_aparicion` el límite cae al mes siguiente; la primera cuota siempre pertenece al mes de `fecha_inicio`; recurrente genera hasta `max(mes actual + 1, mes inicio + 1)`; plan genera N cuotas y la última absorbe el ajuste de centavos; "futura" = `fecha_aparicion > hoy`.
- CRUD en `bd/crud/deudaMensual.py`: las lecturas no sincronizan ni escriben cuotas. `POST /deudas-mensuales/sincronizar` genera cuotas faltantes de forma idempotente y batcheada; el frontend lo llama al entrar a Inicio, Deudas y Deudas mensuales. Cuota/pago/movimiento se crean o eliminan en la misma transacción, actualizando saldo y `ResumenMensual`. Pago completo (no parcial); el movimiento mensual siempre es gasto (`monto` negativo), `es_deuda=True` y usa el tipo/subtipo de la plantilla.
- Edición: cambios estructurales (`modalidad`, `fecha_inicio`, `cuotas_totales`, `monto_total`) bloqueados si hay pagos; el resto solo afecta cuotas futuras impagas. Cancelar conserva pagadas y cancela futuras impagas. Eliminar borra cuotas/pagos/movimientos y revierte saldos. `pagar-lote` es todo-o-nada.
- Entidades: `GET /entidades/{id}` incluye `deudas_mensuales` con detalle y pagos; los saldos las suman como `en_contra` (recurrente: solo cuotas ya aparecidas; plan: todas las impagas); `deudas_pendientes` y `proximo_vencimiento` también las consideran; DELETE de entidad bloqueado si tiene plantillas mensuales.
- API `/deudas-mensuales` (protegida): CRUD de plantillas, `GET /proximas?dias=7&moneda_id=`, `GET /resumen?moneda_id=`, `POST /{id}/cancelar`, `POST /pagar-lote`, `POST /cuotas/{cuota_id}/pagar`, `PUT|DELETE /cuotas/{cuota_id}/pagos/{pago_id}`. DTOs en `api/routers/dtos/deudaMensualDto.py`; fechas de entrada `dd-mm-YYYY`, respuestas ISO.
- Migración `alembic/versions/20261114_0004_deudas_mensuales.py` (`down_revision=0003`): crea `deudamensual`, `cuotamensual`, `pagocuotamensual`, índices y FKs; agregadas a `APP_TABLES`. Sin `ondelete`; el CRUD elimina en orden. `bd/migrations.py` lleva la base a `head` al iniciar (BD local actual en 0005).
- Frontend: `web/pages/deudasMensuales.html` + `web/js/deudasMensuales.js` + `web/css/deudasMensuales.css`; sidebar con badge de vencidas; `deudas.js` muestra resumen y sección mensual por entidad; `panelControl.js` muestra pagos de los próximos 7 días con modal de pago rápido.
- Tests: `tests/test_deudas_mensuales.py` cubre recurrente, estados de pago, movimiento/saldo/resumen, plan y centavos, lote, cancelar/editar/eliminar, entidad, aislamiento y orden de `/proximas`; fixtures `crear_deuda_mensual`/`obtener_tipo_deudas` en `tests/conftest.py`.

## Key refactors (Fase 11 — Rendimiento)

- Migración `alembic/versions/20261118_0005_indices_rendimiento.py` (`down_revision=0004`, head actual): índices compuestos `movimiento (user_id, fecha)`, `(user_id, cuenta_id, fecha)`, `(user_id, tipo_id, fecha)`, `(user_id, es_deuda, fecha)`, `cuotamensual (user_id, estado, fecha_limite)` y `pagocuotamensual (user_id, fecha)`.
- Se eliminó `ix_movimiento_es_deuda` (simple): ninguna consulta filtra por `es_deuda` sin `user_id`. El compuesto también sirve a `es_deuda=false` (dashboard).
- Los índices se declaran con `sa.Index` en `__table_args__` de `bd/models/movimiento.py` y `bd/models/deudaMensual.py`, así `alembic check` queda limpio y `create_all` (tests) los genera.
- Medición de referencia (35k movimientos / 7.2k cuotas): lista de movimientos 94x, resumen mensual 35x, filtro por tipo 56x, filtro `es_deuda` 89x, dashboard 14x.
- Descartados por medición: índice parcial de `es_deuda`, `(deuda_mensual_id, estado)` en cuotas, `(user_id, fecha_limite)` en cuotas y `sesion.token` (la sesión se lee con `first()`, sin filtro por token).
- **Ojo**: `bd/migrations.py` corre `alembic upgrade head` al iniciar; una instalación nueva llega a 0005 sin pasos manuales.

## Key refactors (Fase 5 — Frontend conectado)

- Token storage unified: `guardarToken()`, `obtenerToken()`, `cerrarSesion()` in `funciones.js`
- Bearer token auto-injected in every `request()` via `Authorization` header (except `PUBLIC_PATHS`)
- `health/token` changed from query-param to `Depends(validate_token)` (Bearer)
- `funciones.js` cleaned: removed demo event listeners, unused `get()` `data` param (127 lines)

## Configuración SQLite (Fase 11.4)

- `bd/database.py` configura cada conexión con WAL, `synchronous=NORMAL`, claves foráneas y `busy_timeout=5000`; el engine usa `check_same_thread=False` y timeout de 5 s para el threadpool de Uvicorn.
- Backup intenta `wal_checkpoint(TRUNCATE)` y usa `sqlite3.Connection.backup`. Restaurar valida una copia temporal con `integrity_check`, dispone el engine, elimina sidecars `-wal`/`-shm` obsoletos y reemplaza `database.db` atómicamente.

## Notable quirks

- `User.id` is `uuid.UUID`; other model PKs are `int`.
- Password hashing uses `passlib.hash.bcrypt`.
- `Movimiento.es_ingreso` inferred from `monto > 0`.
- Tailwind configured via inline `<script>` in `index.html` (no build step).
- Frontend uses `sessionStorage` for token (key: `auth_token`) and `localStorage` for `remember_session` flag.
- `obtener_usuario_por_token()` only checks the **first** `Sesion` row → single active session by design; isolation tests log in users sequentially.
- **No usar `backdrop-filter`/`backdrop-blur` en el frontend:** en Qt WebEngine/Windows provoca parpadeo de toda la vista al interactuar (bug de compositor GPU). Usar fondos translúcidos sin blur.
- `DeudaMensual` no tiene `direccion`: pagar una cuota mensual siempre crea un **gasto** (`monto` negativo), aunque la plantilla esté ligada a una entidad.
- `PagoCuotaMensual.cuota_id` y `movimiento_id` son únicos → una cuota admite un solo pago; el pago debe ser completo (`validar_monto_pago`).
- Editar un pago recalcula `CuotaMensual.estado_pago`; eliminar un pago devuelve la cuota a `pendiente` y borra el movimiento.
- `moneda_distinta` solo avisa si la cuenta de pago usa otra moneda; no hay conversión, igual que en Deudas.
- Las cuotas recurrentes se sincronizan al abrir Inicio, Deudas o Deudas mensuales mediante `POST /deudas-mensuales/sincronizar`; las lecturas API son de solo lectura. El badge del sidebar cachea el resumen por 30 segundos y se invalida tras cambios en deudas mensuales.

## Tests (Fase 6)

- `pytest` + `httpx` + `ruff` in `requirements-dev.txt`; config in `pyproject.toml`.
- `tests/conftest.py` sets `os.environ["APPDATA"]` to a temp dir **before** importing app modules, so the global `engine` binds to a temp SQLite; an autouse `reset_db` fixture drops/recreates schema + seeds per test.
- API tests (`test_auth`, `test_cuentas`, `test_movimientos`, `test_aislamiento`, `test_entidades`, `test_deudas`, `test_deudas_mensuales`, `test_reportes`) use `TestClient`; unit tests (`test_movimiento_unit`) call `bd/crud/*` directly (saldo + `ResumenMensual`).
- `tests/conftest.py` incluye fixtures `crear_entidad`, `crear_deuda`, `crear_pago`, `obtener_moneda`, `crear_deuda_mensual` y `obtener_tipo_deudas`.
- Estado actual: 86 tests pasan, incluidos 13 de deudas mensuales.
- Se ejecutó además un E2E del flujo de deudas mensuales vía `TestClient` sobre BD temporal; la prueba visual en PyQt6 WebEngine sigue pendiente.
- Dates sent to the API use `dd-mm-YYYY` (parsed by `DateFromString`).
- Lint is scoped to `tests/` + `api/mainApi.py` (ruff `select = ["E", "F", "I"]`).

## Key refactors (Fase 7 — Reportes y análisis)

- `POST /movimientos/importar` recibe `{"filas": [MovimientoImport]}` y crea movimientos en bulk (`crear_movimientos_bulk` en `bd/crud/movimiento.py`); devuelve `{"importados", "errores": [{"fila", "error"}]}` — sin auto-rollback, el usuario decide.
- DTO `MovimientoImport` (monto, fecha, tipo_id, cuenta_id, descripcion) en `api/routers/dtos/movimientoDto.py`.
- Dashboard: card "Flujo Neto Mensual" (ingresos - gastos del mes, verde/rojo según signo).
- Transacciones: filtros por cuenta + rango de fecha (`filtroCuenta`, `filtroDesde`, `filtroHasta` → query params `cuenta_id`, `fecha_desde`, `fecha_hasta`), botones Exportar CSV (descarga con BOM UTF-8 para Excel) e Importar CSV (mapea nombres de cuenta/tipo → ids, acepta fechas ISO o `dd-mm-YYYY`).

## What's missing / planned

See `porhacer3.md` for the current roadmap. Pending: cerrar `10.10 Archivos principales`, prueba manual end-to-end de deudas mensuales y Fase 7.5 (inteligencia financiera) de `PorHacerv2.md`.

## MCP Knowledge Graph (codebase-memory-mcp)

El proyecto usa un grafo de conocimiento MCP (`codebase-memory-mcp`) para responder consultas estructurales sin leer archivos uno por uno.

**Nombre MCP de este proyecto:** `C-Users-cleoe-OneDrive-Documentos-GitHub-FlujoCaja`. Usa este nombre exacto al llamar herramientas MCP; el nombre corto `FlujoCaja` no se reconoce. Antes de indexar, consulta `list_projects` o intenta consultar el grafo con el nombre exacto para confirmar que sigue disponible.

**Regla:** Antes de usar `Grep`/`Glob`/`Read`, consultar primero el grafo MCP.

### Helper (portable)

El script `tools/mcp.py` es portable: se para en el directorio raíz de cualquier proyecto indexado y funciona automáticamente. También puedes copiarlo a `%USERPROFILE%\.local\bin\mcp.py` para usarlo globalmente.

```powershell
# Desde el directorio del proyecto (auto-detecta)
python ruta/a/tools/mcp.py search <patron>
python ruta/a/tools/mcp.py query "<cypher>"
python ruta/a/tools/mcp.py trace <funcion>
python ruta/a/tools/mcp.py arch
python ruta/a/tools/mcp.py code <patron>
python ruta/a/tools/mcp.py schema
python ruta/a/tools/mcp.py projects
python ruta/a/tools/mcp.py index   # re-indexar

# Para este proyecto, si la herramienta requiere nombre explícito
python ruta/a/tools/mcp.py -p C-Users-cleoe-OneDrive-Documentos-GitHub-FlujoCaja search "<patron>"

# Para otro proyecto (por nombre)
python ruta/a/tools/mcp.py -p Otro-Proyecto search "class .*"
```

### Consultas Cypher útiles

```cypher
MATCH (f:Function) RETURN f.name, f.file_path, f.signature LIMIT 20
MATCH (c:Class) RETURN c.name, c.file_path
MATCH ()-[r:CALLS]->() RETURN r.callee, count(*) as calls ORDER BY calls DESC
MATCH (f:Function {is_entry_point: true}) RETURN f.name, f.file_path
```

### Info de contacto

- El MCP server usa SQLite en `~/.cache/codebase-memory-mcp/`
- Auto-sync: el watcher detecta cambios automáticamente
- `-p <project>` sobreescribe el proyecto autodetectado
