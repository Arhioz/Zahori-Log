# 🎌 Proyecto: Zahori Log API

Un backend profesional construido con **FastAPI** para la gestión de catálogos y diarios personales de entretenimiento (Anime y Videojuegos). 

Esta API permite a los usuarios registrarse, buscar información en tiempo real conectándose a APIs externas (Jikan y RAWG), y guardar un registro detallado de su progreso, estado y calificación en su base de datos personal.

## 🛡️ Características Principales

* **Autenticación Segura:** Registro de usuarios e inicio de sesión utilizando hashing de contraseñas (`bcrypt`) y tokens de acceso (`JWT`).
* **Integración de APIs de Terceros:** Consumo asíncrono de la **Jikan API** (Catálogo de Anime) y la **RAWG API** (Catálogo de Videojuegos) mediante `httpx`.
* **Carga Perezosa e Inteligente (Eager Loading):** Manejo eficiente de relaciones en base de datos para prevenir problemas de asincronía y optimizar el rendimiento.
* **Base de Datos Asíncrona:** Operaciones no bloqueantes hacia PostgreSQL utilizando `asyncpg` y `SQLAlchemy 2.0`.
* **Migraciones Controladas:** Gestión del historial de la base de datos a través de `Alembic`.
* **Entorno Dockerizado:** Infraestructura lista para levantar en cualquier equipo mediante `Docker Compose`.

## 🛠️ Tecnologías (Tech Stack)

* **Framework:** FastAPI
* **Lenguaje:** Python 3.12+
* **Base de Datos:** PostgreSQL
* **ORM & Migraciones:** SQLAlchemy (Async) & Alembic
* **Contenedores:** Docker & Docker Compose
* **Validación de Datos:** Pydantic

## ⚙️ Instalación y Ejecución Local

### 1. Clonar el repositorio
```bash
git clone [https://github.com/TU_USUARIO/zahori-log.git](https://github.com/TU_USUARIO/zahori-log.git)
```
```bash
cd zahori-log
```

### 2. **Crear y activar entorno virtual de Python**
**Linux**
```bash
python3 -m venv venv
```
```bash
source env/bin/activate
```
**Windows**
```bash
python -m venv venv
```
```bash
 .\env\Scripts\Activate.ps1
 ```

### 3. **Configurar Variables de Entorno**
Crea un archivo .env en la raíz del proyecto basándote en el archivo de ejemplo:
```bash
cp .env.example .env
```
Abre el archivo .env y coloca tus credenciales (incluyendo tu API Key de RAWG).

### 4. Levantar con Docker Compose (Recomendado)
Asegúrate de tener Docker instalado y ejecutándose. Luego, en tu terminal, corre:

```bash
docker compose up -d --build
```
Esto levantará dos contenedores: la base de datos de PostgreSQL y la API de FastAPI.

### 5. Aplicar las migraciones
Para crear las tablas en la base de datos, ejecuta Alembic dentro del contenedor de la API:
```bash
docker exec -it zahorilog-api-contenedor alembic upgrade head
```

## 📖 Uso y Documentación

Una vez que los contenedores estén corriendo, FastAPI genera automáticamente una documentación interactiva (Swagger UI) donde puedes probar todos los endpoints.

- **Swagger UI:** Navega a http://localhost:8000/docs

## 🚀 Flujo básico de prueba:

1. Crea un usuario en POST /users/register.

2. Haz login en POST /token para obtener tu JWT (o usa el botón verde "Authorize" en Swagger).

3. Busca un anime en GET /animes/buscar.

4. Añádelo a tu lista personal en POST /animes/mi-lista usando el ID obtenido.

---
Desarrollado por ***Arhioz***