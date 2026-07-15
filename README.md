# FlujoCaja

Aplicación local para control de flujo de caja y finanzas personales. Permite registrar ingresos y gastos, asociarlos a cuentas, clasificarlos por tipos y subtipos, y analizar la evolución del dinero en el tiempo.

## Estado

El proyecto comenzó como un prototipo CLI y evolucionó a una arquitectura con **API REST** (FastAPI), **interfaz web** (HTML+JS+Tailwind) y **ventana de escritorio** (PyQt6 WebEngine). La versión CLI heredada se conserva pero no está activa por defecto.

> ⚠ El frontend web está en fase activa de conexión con la API. Actualmente login y registro funcionan con datos reales; el resto de pantallas se están migrando de HTML estático a datos vivos.

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
- CRUD completo de movimientos (crear, leer, actualizar, eliminar)
- Filtros por fecha, cuenta, tipo, subtipo, ingreso/gasto y paginación
- Validación de pertenencia: cada movimiento pertenece a un usuario
- Subtipo validado contra el tipo al que pertenece
- Actualización y reversión de saldos al crear/editar/eliminar movimientos
- Resumen mensual/anual por rango de fechas
- Dashboard web con métricas básicas
- Base de datos migrada automáticamente a `%APPDATA%/FlujoCaja/`

## Arquitectura

```
FlujoCaja/
├── api/                        # API REST (FastAPI)
│   ├── mainApi.py              # App FastAPI, CORS, error handlers, routers
│   ├── dependencies.py         # validate_token (Bearer → User)
│   └── routers/                # auth, cuentas, monedas, movimientos, tipos, subtipos, resumen
│       └── dtos/               # Pydantic DTOs de entrada/salida
├── bd/                         # Capa de persistencia
│   ├── database.py             # engine, init_db
│   ├── bd.py                   # bootstrap y migración legacy
│   ├── bootstrap.py            # Semillas iniciales (monedas, tipos, etc.)
│   ├── migrations.py           # Detección de tablas existentes
│   ├── models/                 # SQLModel: User, Cuenta, Movimiento, Tipo, Subtipo, Moneda, Sesion
│   └── crud/                   # CRUD por entidad (movimiento, cuenta, tipo, etc.)
├── web/                        # Frontend estático
│   ├── index.html              # Página de inicio (validación de sesión)
│   ├── pages/                  # login, CrearCuenta, panelControl, cuentas, transacciones
│   ├── components/             # Componentes HTML reutilizables (sidemenu)
│   └── js/                     # funciones.js, validacion.js, login.js, CrearCuenta.js, index.js
├── alembic/                    # Migraciones de esquema
├── menus/                      # CLI heredada
├── widget/                     # Utilidades visuales CLI heredadas
├── planes/                     # Planes de refactor y roadmap técnico
├── tools/                      # Utilidades (mcp.py — helper para grafo de conocimiento MCP)
├── main.py                     # Entrypoint principal (BD + API + ventana)
├── app.py                      # Entrypoint CLI heredado
├── config.py                   # Configuración centralizada (rutas, puerto, debug)
├── AGENTS.md                   # Notas técnicas para sesiones de IA
└── requirements.txt
```

## Rutas de la API

| Prefijo | Auth | Recursos |
|---------|------|----------|
| `/auth` | Libre | `POST /register`, `POST /login`, `GET /`, `DELETE /` |
| `/health` | Libre | `GET /`, `GET /token` |
| `/movimientos` | Bearer | CRUD completo con filtros y paginación |
| `/cuentas` | Bearer | CRUD de cuentas + tipos de cuenta |
| `/monedas` | Bearer | CRUD de monedas |
| `/tipos` | Bearer | CRUD de tipos |
| `/subtipos` | Bearer | CRUD de subtipos + filtro por tipo |
| `/resumen` | Bearer | Resúmenes anual, mensual, por rango |

Todas las respuestas de error siguen el formato `{"error", "status", "path"}`.

## Instalación

```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
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

## Modelo de datos

- **User** — id (UUID), name, passw (bcrypt)
- **Sesion** — user_id → User, token
- **Cuenta** — id, nombre, tipo_cuenta_id, usuario_id → User
- **Moneda** — id, nombre, simbolo
- **Tipo** — id, nombre
- **Subtipo** — id, nombre, tipo_id → Tipo
- **Movimiento** — id, fecha, monto, descripcion, cuenta_id, tipo_id, subtipo_id, moneda_id, es_ingreso (calculado)

## Licencia

Este repositorio se publica únicamente con fines de demostración y portafolio.
No se autoriza la reutilización, distribución o uso comercial del código sin permiso expreso del autor.
