# FlujoCaja

Aplicación local para control de flujo de caja y finanzas personales. Permite registrar ingresos y gastos, asociarlos a cuentas, clasificarlos por tipos y subtipos, y analizar la evolución del dinero en el tiempo.

## Estado actual

El proyecto pasó de un prototipo CLI a una arquitectura con API REST, interfaz web y ventana de escritorio.

Actualmente incluye:

- **API REST local** con FastAPI
- **Base de datos SQLite** administrada con SQLModel
- **Interfaz web** en HTML, JavaScript y Tailwind CSS (CDN)
- **Ventana de escritorio** con PyQt6 WebEngine
- **Versión CLI heredada** (`app.py`, `menus/`, `widget/`) conservada pero no activa por defecto

## Arquitectura

```
FlujoCaja/
├── api/                    # API FastAPI
│   ├── mainApi.py          # App FastAPI, CORS, error handlers, routers
│   ├── dependencies.py     # validate_token (Bearer → User)
│   └── routers/            # auth, cuentas, monedas, movimientos, tipos, subtipos, resumen
│       └── dtos/           # Pydantic DTOs de entrada/salida
├── bd/                     # Capa de persistencia
│   ├── database.py         # engine, init_db
│   ├── bd.py               # bootstrap, migración legacy
│   ├── bootstrap.py        # Semillas iniciales (monedas, tipos, etc.)
│   ├── migrations.py       # Detección de tablas existentes
│   ├── models/             # SQLModel: User, Cuenta, Movimiento, Tipo, Subtipo, Moneda, Sesion
│   └── crud/               # Funciones CRUD por entidad
├── web/                    # Frontend estático
│   ├── index.html
│   ├── pages/              # login, CrearCuenta, panelControl, cuentas, movimientos
│   ├── components/         # Componentes HTML reutilizables
│   └── js/                 # funciones.js, validacion.js, login.js, CrearCuenta.js, index.js
├── menus/                  # CLI heredada
├── widget/                 # Utilidades visuales CLI heredadas
├── planes/                 # Planes de refactor (fase4-api-mantenible.md)
├── tools/                  # Utilidades (mcp.py — helper para grafo MCP)
├── main.py                 # Entrypoint principal
├── app.py                  # Entrypoint CLI heredado
├── config.py               # Configuración centralizada (rutas, puerto, debug)
└── requirements.txt
```

## Rutas de la API

| Prefijo | Autenticación | Recursos |
|---------|---------------|----------|
| `/auth` | Libre | `POST /register`, `POST /login`, `GET /`, `DELETE /` |
| `/health` | Libre | `GET /`, `GET /token?token=...` |
| `/movimientos` | Bearer token | CRUD completo con filtros y paginación |
| `/cuentas` | Bearer token | CRUD de cuentas + tipos de cuenta |
| `/monedas` | Bearer token | CRUD de monedas |
| `/tipos` | Bearer token | CRUD de tipos |
| `/subtipos` | Bearer token | CRUD de subtipos + filtro por tipo |
| `/resumen` | Bearer token | Resúmenes anual, mensual, por rango |

Todas las respuestas de error siguen el formato `{"error", "status", "path"}`.

## Instalación

```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py              # App completa (BD + API + ventana)
python main.py --api        # Solo API
python main.py --api --debug # API con logging detallado
python main.py --bd         # Solo inicializar BD
python main.py --web        # Solo interfaz web
python app.py               # CLI heredada
```

## Funcionalidades implementadas

- Creación e inicio de sesión de usuarios (contraseñas hasheadas con bcrypt)
- Persistencia de sesión con token opaco en SQLite
- Validación de token en rutas protegidas via `Authorization: Bearer`
- CRUD completo de movimientos (crear, leer, actualizar, eliminar)
- Filtros por fecha, cuenta, tipo, subtipo, ingreso/gasto y paginación
- Validación de pertenencia: cuenta debe ser del usuario autenticado
- Subtipo validado contra el tipo al que pertenece
- Actualización y reversión de saldos al crear/editar/eliminar movimientos
- Resumen mensual/anual por rango de fechas
- Dashboard web con métricas básicas
- Base de datos migrada automáticamente a `%APPDATA%/FlujoCaja/`

## Tecnologías

- Python / FastAPI / Uvicorn
- SQLModel / SQLAlchemy / Pydantic
- Passlib (bcrypt)
- HTML / JavaScript / Tailwind CSS (CDN)
- PyQt6 / PyQt6-WebEngine
- Rich / Questionary (CLI heredada)

## Roadmap

Ver `porHacer.md` para el detalle completo. Prioridades actuales:

1. Conectar todas las pantallas web con datos reales
2. Agregar tests (pytest con BD temporal)
3. Dashboard con gráficos y reportes
4. Exportación/importación CSV
5. Empaquetado como ejecutable (PyInstaller)
