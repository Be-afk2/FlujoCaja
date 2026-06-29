# FlujoCaja

## Descripcion general

**FlujoCaja** es una aplicacion personal para el control de flujo de caja y finanzas personales. Su objetivo es registrar ingresos y gastos, asociarlos a cuentas, clasificarlos por tipos y subtipos, y entregar una base para analizar como se mueve el dinero en el tiempo.

El proyecto nacio como una alternativa a registros en Excel o papel, y actualmente se encuentra en etapa de **prototipo en desarrollo**. La version actual combina una API local, una base de datos SQLite y una interfaz web ejecutada dentro de una ventana de escritorio.

## Idea principal

La idea central es construir una herramienta local para:

- Registrar movimientos de dinero.
- Distinguir ingresos y gastos.
- Clasificar movimientos por categorias personalizadas.
- Administrar cuentas del usuario, como efectivo, ahorro u otras.
- Mantener usuarios y sesiones.
- Preparar el sistema para futuras vistas de analisis, graficos y reportes.

## Estado actual

El proyecto ha evolucionado desde una aplicacion por consola hacia una arquitectura con API e interfaz grafica.

Actualmente incluye:

- Una **API REST local** construida con FastAPI.
- Una **base de datos SQLite** administrada con SQLModel.
- Una **interfaz web** en HTML, JavaScript y Tailwind CSS.
- Una **ventana de escritorio** con PyQt6 WebEngine que carga la interfaz web local.
- Una version previa por **consola/CLI**, que aun existe en el proyecto.

Algunas pantallas web todavia contienen datos de ejemplo o se encuentran en desarrollo.

## Tecnologias utilizadas

### Backend

- Python
- FastAPI
- Uvicorn
- SQLModel
- SQLAlchemy
- Pydantic
- Passlib / bcrypt

### Base de datos

- SQLite

### Interfaz

- HTML
- JavaScript
- Tailwind CSS mediante CDN
- PyQt6
- PyQt6 WebEngine

### Consola

- Rich
- Questionary

## Estructura del proyecto

```text
FlujoCaja/
|-- api/                  # API FastAPI y routers
|   |-- mainApi.py
|   |-- dependencies.py
|   `-- routers/
|-- bd/                   # Base de datos, modelos y CRUD
|   |-- database.py
|   |-- bd.py
|   |-- models/
|   `-- crud/
|-- web/                  # Interfaz web local
|   |-- index.html
|   |-- pages/
|   |-- components/
|   `-- js/
|-- menus/                # Menus de la version por consola
|-- widget/               # Utilidades visuales para consola
|-- app.py                # Entrada de la version CLI
|-- main.py               # Entrada principal actual
|-- database.db           # Base de datos SQLite local
`-- requirements.txt      # Dependencias Python
```

## Componentes principales

### `main.py`

Es el punto de entrada principal de la aplicacion actual. Se encarga de:

- Verificar o crear la base de datos.
- Iniciar la API local en `http://127.0.0.1:8000`.
- Abrir la interfaz web en una ventana de escritorio con PyQt6.
- Permitir modos de ejecucion separados para API, base de datos o web.

### `api/mainApi.py`

Define la aplicacion FastAPI, configura CORS, maneja errores HTTP e incluye los routers principales:

- Autenticacion
- Cuentas
- Gastos
- Monedas
- Tipos
- Subtipos

Varias rutas usan validacion de token mediante dependencias.

### `bd/`

Contiene la capa de datos:

- Conexion SQLite.
- Inicializacion de tablas.
- Modelos SQLModel.
- Funciones CRUD.

Modelos importantes:

- `User`: usuarios del sistema.
- `Cuenta`: cuentas financieras del usuario.
- `Registro`: ingresos o gastos registrados.
- `Tipo`: categorias principales.
- `Subtipo`: subcategorias.
- `Moneda`: monedas disponibles.
- `Sesion`: datos de sesion.

### `web/`

Contiene la interfaz visual. Incluye pantallas para:

- Carga inicial.
- Login.
- Panel de control.
- Cuentas.
- Creacion de cuentas.
- Transacciones.

La interfaz consume la API local usando `fetch` desde los archivos JavaScript.

### `app.py` 

Corresponde a la version por consola. Permite iniciar sesion, recordar usuario y entrar a menus internos usando `questionary` y `rich`.

## Instalacion

### Requisitos

- Python 3
- Entorno virtual recomendado

### Instalar dependencias

```bash
pip install -r requirements.txt
```

## Ejecucion

### Aplicacion completa

```bash
python main.py
```

Este comando inicia:

- Base de datos
- API local
- Interfaz web en ventana de escritorio

### Solo API

```bash
python main.py --api
```

### API en modo debug

```bash
python main.py --api --debug
```

### Solo base de datos

```bash
python main.py --bd
```

### Solo interfaz web

```bash
python main.py --web
```

### Version por consola (obsoleto)

```bash
python app.py
```

## API local

Por defecto, la API se ejecuta en:

```text
http://127.0.0.1:8000
```

Algunos grupos de rutas disponibles:

- `/auth`
- `/cuenta`
- `/gastos`
- `/moneda`
- `/tipos`
- `/subtipos`

## Funcionalidades actuales

- Creacion e inicio de sesion de usuarios.
- Persistencia de sesion.
- Validacion basica por token.
- Creacion y consulta de cuentas.
- Gestion de tipos, subtipos y monedas.
- Registro base de movimientos financieros.
- Interfaz web inicial con pantallas principales.
- Ejecucion local como aplicacion de escritorio.

## Pendiente / roadmap

- Completar CRUD de gastos y transacciones.
- Conectar todas las pantallas web con datos reales de la API.
- Mejorar dashboard con metricas reales.
- Agregar graficos y reportes.
- Fortalecer autenticacion y manejo de sesiones.
- Mejorar validaciones y manejo de errores.
- Preparar empaquetado como ejecutable.
- Revisar arquitectura para separar mejor API, datos e interfaz.

## Nota

Este es un proyecto personal en desarrollo. La arquitectura actual esta pensada para crecer progresivamente: primero consolidando una base local funcional y luego agregando mejores vistas, analisis financiero y una experiencia de uso mas completa.
