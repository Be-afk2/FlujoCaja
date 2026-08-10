# FlujoCaja

Aplicación local para control de flujo de caja y finanzas personales. Permite registrar ingresos y gastos, asociarlos a cuentas, clasificarlos por tipos y subtipos, y analizar la evolución del dinero en el tiempo.

## Estado

El proyecto comenzó como un prototipo CLI y evolucionó a una arquitectura con **API REST** (FastAPI), **interfaz web** (HTML+JS+Tailwind) y **ventana de escritorio** (PyQt6 WebEngine). La versión CLI heredada se conserva pero no está activa por defecto.

El frontend web está **completamente conectado a la API** con datos reales: autenticación, dashboard, cuentas, movimientos, categorías y ajustes (perfil, moneda, tema y backup). Versión actual: **0.4.0**.

> ⚠ Pendiente: empaquetado como aplicación de escritorio distribuible (ver roadmap en `porHacer.md`, Fase 8).

## Tecnologías

- **Backend:** Python, FastAPI, Uvicorn
- **Base de datos:** SQLite, SQLModel, SQLAlchemy, Alembic
- **Validación:** Pydantic, Passlib (bcrypt)
- **Frontend:** HTML, JavaScript, Tailwind CSS (vía CDN)
- **Escritorio:** PyQt6, PyQt6-WebEngine
- **CLI heredada:** Rich, Questionary

## Funcionalidades

- Creación e inicio de sesión de usuarios con contraseñas hasheadas (bcrypt)
- Sesión persistente con token opaco en SQLite (`Authorization: Bearer`)
- Gestión de perfil y cambio de contraseña (`GET/PUT /auth/me`, `PUT /auth/me/password`)
- CRUD completo de movimientos (crear, leer, actualizar, eliminar)
- Importación y exportación de movimientos por CSV
- Filtros por fecha, cuenta, tipo, subtipo, ingreso/gasto y paginación
- Validación de pertenencia: cada movimiento pertenece a un usuario
- Subtipo validado contra el tipo al que pertenece
- Actualización y reversión de saldos al crear/editar/eliminar movimientos
- Resumen mensual/anual por rango de fechas (mantenido incrementalmente)
- Dashboard web con métricas: saldo por cuenta, ingresos/gastos, flujo neto mensual, gráficos de evolución y categorías
- CRUD de cuentas, tipos, subtipos y monedas con interfaz web
- Backup y restauración de la base de datos desde la interfaz
- Página de ajustes: perfil, contraseña, monedas, tema claro/oscuro, sesión y acerca de
- Base de datos migrada automáticamente a `%APPDATA%/FlujoCaja/`

## Arquitectura

```
FlujoCaja/
├── api/                        # API REST (FastAPI)
│   ├── mainApi.py              # App FastAPI, CORS, error handlers, routers
│   ├── dependencies.py         # validate_token (Bearer → User)
│   └── routers/                # auth, cuentas, monedas, movimientos, tipos, subtipos, resumen, datos
│       └── dtos/               # Pydantic DTOs de entrada/salida
├── bd/                         # Capa de persistencia
│   ├── database.py             # engine, init_db
│   ├── bd.py                   # bootstrap y migración legacy
│   ├── bootstrap.py            # Semillas iniciales (monedas, tipos, etc.)
│   ├── migrations.py           # Detección de tablas existentes
│   ├── models/                 # SQLModel: User, Cuenta, Movimiento, Tipo, Subtipo, Moneda, Sesion, ResumenMensual
│   └── crud/                   # CRUD por entidad (movimiento, cuenta, tipo, etc.)
├── web/                        # Frontend estático
│   ├── index.html              # Página de inicio (validación de sesión)
│   ├── pages/                  # login, CrearCuenta, panelControl, cuentas, transacciones, categoria, ajustes
│   ├── components/             # Componentes HTML reutilizables (sidemenu)
│   └── js/                     # funciones, notificaciones, loadmenu, login, index, panelControl, cuentas, transacciones, categorias, ajustes, validacion
├── alembic/                    # Migraciones de esquema
├── menus/                      # CLI heredada
├── widget/                     # Utilidades visuales CLI heredadas
├── planes/                     # Planes de refactor y roadmap técnico
├── tools/                      # Utilidades (mcp.py — helper para grafo de conocimiento MCP)
├── tests/                      # Suite pytest (conftest, auth, cuentas, movimientos, import, datos, aislamiento, unit)
├── main.py                     # Entrypoint principal (BD + API + ventana)
├── app.py                      # Entrypoint CLI heredado
├── config.py                   # Configuración centralizada (rutas, puerto, debug)
├── pyproject.toml              # Config de pytest y ruff
├── requirements.txt
├── requirements-dev.txt        # Dependencias de desarrollo (pytest, httpx, ruff)
├── run_tests.ps1               # Ejecuta los tests
└── run_lint.ps1                # Ejecuta el lint
```

## Rutas de la API

| Prefijo | Auth | Recursos |
|---------|------|----------|
| `/auth` | Libre | `POST /register`, `POST /login`, `GET /`, `DELETE /` |
| `/auth/me` | Bearer | `GET /`, `PUT /`, `PUT /password` (perfil y contraseña) |
| `/health` | Libre | `GET /`, `GET /token` |
| `/movimientos` | Bearer | CRUD completo con filtros y paginación + `POST /importar` |
| `/cuentas` | Bearer | CRUD de cuentas + tipos de cuenta |
| `/monedas` | Bearer | CRUD de monedas |
| `/tipos` | Bearer | CRUD de tipos |
| `/subtipos` | Bearer | CRUD de subtipos + filtro por tipo |
| `/resumen` | Bearer | Resúmenes anual, mensual, por rango |
| `/datos` | Bearer | `GET /backup`, `POST /restaurar` |

Todas las respuestas de error siguen el formato `{"error", "status", "path"}`.

## Instalación

```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt   # solo para desarrollo (pytest, httpx, ruff)
```

## Ejecución

```bash
python main.py               # App completa (BD + API + ventana)
python main.py --api         # Solo API
python main.py --api --debug # API con logging detallado + hot-reload
python main.py --bd          # Solo inicializar BD
python main.py --web         # Solo ventana web
python app.py                # CLI heredada
```

Una vez iniciada la API, abre `http://127.0.0.1:8000/` en tu navegador para ver la interfaz web.

## Desarrollo y tests

```bash
python -m pytest tests -v          # ejecutar la suite de tests (o .\run_tests.ps1)
python -m ruff check tests api/mainApi.py   # lint (o .\run_lint.ps1)
```

La suite usa una base SQLite temporal aislada (override de `%APPDATA%` en `tests/conftest.py`) y cubre: autenticación, cuentas, movimientos, saldos, resúmenes, importación CSV, backup/restauración y aislamiento entre usuarios.

## Modelo de datos

- **User** — id (UUID), name, apellido, passw (bcrypt)
- **Sesion** — user_id → User, token
- **Cuenta** — id, nombre, descripcion, tipo_id → TipoCuenta, moneda_id → Moneda, saldo, user_id → User
- **Moneda** — id, nombre, simbolo
- **Tipo** — id, nombre
- **Subtipo** — id, nombre, tipo_id → Tipo
- **Movimiento** — id, fecha, monto, descripcion, cuenta_id, tipo_id, subtipo_id, user_id, es_ingreso (calculado)
- **ResumenMensual** — user_id, cuenta_id, anio, mes, total_ingresos, total_gastos, neto (mantenido incrementalmente)

## Licencia

Este repositorio se publica únicamente con fines de demostración y portafolio.
No se autoriza la reutilización, distribución o uso comercial del código sin permiso expreso del autor.
