# Flujo de caja — Plan de trabajo ordenado (Python + SQLite)

## Visión general
Proyecto de registro y reporte de gastos con backend en Python usando SQLite y frontend de escritorio en Python (Tkinter). Diseñar capas: datos (SQLite), lógica (servicios/repository), API/local access, UI (Tkinter).

## Prioridad (mínimo viable -> mejoras)
1. Modelo de datos y acceso (SQLite)  x
2. CRUD básico backend (servicios/repository)
3. UI mínima: login y formulario modal para registrar gasto
4. Listado/Reporte de gastos con filtros
5. Gestión de tipos de gasto
6. Robustez, tests y documentación
7. Mejoras UX/funcionalidades avanzadas

---

## Backend (SQLite, consola / servicios locales)
1. Planificar la base de datos (esquema SQLite)
   - Entidades: Usuario(id, username, password_hash, created_at) x
   - Gasto(id, user_id, monto, fecha, categoria_id, descripcion, created_at) x
   - TipoGasto(id, nombre, descripcion, created_at) x
   - Constraints: foreign keys, índices en user_id y fecha x
2. Crear la base de datos
   - Script de inicialización (schema.sql) o migraciones simples x 
   - Asegurar guardo de bd en %appdata% 
3. Capa de acceso a datos
   - Implementar repository usando sqlite3 o SQLAlchemy (recomiendo sqlite3 + queries simples para desktop)  x
   - Funciones: crear_usuario, autenticar_usuario, crear_gasto, listar_gastos(filtros), crear_tipo_gasto, listar_tipos x
4. Servicios / lógica de negocio
   - Validaciones (monto positivo, fecha válida, categoría existente) x 
   - Manejo de transacciones y errores
5. API local opcional
   - Si se quiere separar UI/Backend: pequeño API con Flask o FastAPI (endpoints POST/GET)
   - Endpoints mínimos: POST /auth, POST /users, POST /gastos, GET /gastos, POST /tipo-gastos, GET /tipo-gastos
6. Robustez backend
   - Validación y sanitización
   - Manejo de errores consistente
   - Tests unitarios para repositorios y servicios
   - Documentación (README, OpenAPI si se creó API)

---

## Front (Tkinter) — tareas mapeadas al backend
Nota: la UI puede consumir directamente la capa de repositorio si no hay API HTTP.

1. Estructura general / bootstrap
   - App principal con gestor de ventanas (ventana con botón que abre modal completo)
   - Carpeta gui/ con módulos: auth.py, gastos.py, tipos.py, dashboard.py, services_client.py
2. Autenticación (consumir create/auth)
   - Login dialog (username, password) -> llama a autenticar_usuario
   - Registro dialog opcional -> create usuario
   - Guardar sesión en memoria (user_id, token si hay API)
3. Formulario modal "Registrar gasto" (mapeado a POST /gastos o crear_gasto)
   - Campos: Monto (Entry numérico), Fecha (Entry/DatePicker), Categoría (Combobox cargada desde listar_tipos), Descripción (Text)
   - Validaciones: monto > 0, fecha en formato válido, categoría seleccionada
   - Botones: Guardar (llama a crear_gasto), Cancelar
   - Modal debe ser Toplevel con grab_set() y wait_window() (ya hay ejemplo)
4. Gestión de "Tipo de gasto" (mapeado a POST/GET tipo-gastos)
   - Diálogo para crear tipo (nombre, descripción)
   - Selector reutilizable: actualizar combobox en formularios al crear un nuevo tipo
5. Dashboard / Lista de gastos (mapeado a GET /gastos)
   - Tabla/listbox con columnas: fecha, monto, categoría, descripción
   - Filtros: rango de fecha, categoría, monto mínimo/máximo
   - Paginación o scroll
   - Exportar a CSV opcional
6. Integración UI <-> Backend
   - services_client.py que llama a repositorio o API (funciones sincrónicas)
   - Manejo de errores con toasts/dialogs
   - Indicadores de carga (cursor o estado) para operaciones largas
7. Validaciones y UX
   - Mensajes de error claros en formularios
   - Confirmación al eliminar/editar gasto
   - Validaciones en cliente además de backend
8. Tests y calidad
   - Tests unitarios para lógica UI mínima y servicios (pueden mockear repositorio)
   - Scripts: run_app.bat, init_db.py
9. Documentación/instalación
   - README con pasos: crear entorno, pip install, init_db.py, run_app.bat
   - Ejemplos de uso y estructura de carpetas

---

## Tareas auxiliares / scripts
- init_db.py: crear DB y seeds
- run_app.bat: activar venv y ejecutar main.py
- requirements.txt (si hay paquetes: flask/fastapi/sqlalchemy/pyyaml)
- tests/ con pytest para backend y lógica

---

## Siguientes pasos sugeridos (inmediatos)
1. Crear schema.sql / init_db.py con tablas y seeds.
2. Implementar pequeño repositorio sqlite3 con funciones básicas (crear/leer).
3. Esqueleto UI: ventana principal con botón que abre modal "Registrar gasto" (formulario completo).
4. Conectar formulario al repositorio y verificar inserciones en DB.
