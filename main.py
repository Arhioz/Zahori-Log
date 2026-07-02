import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from slowapi.errors import RateLimitExceeded
from limiter import limiter
from routers import auth_router, users, animes, videojuegos


load_dotenv()

# Inicializamos la aplicación FastAPI
app = FastAPI(
    title="Zahori Log API",
    description="Backend profesional para el seguimiento de catálogos y logs personales de Animes y Videojuegos.",
    version="1.0.0",
    contact={
        "name": "Arhioz Developer",
        "email": "arhioz@zahorilog.com",
    }
)

# --- CONFIGURACION RATE LIMITING ---
# 1. Asignamos el limitador al estado de la aplicación
app.state.limiter = limiter

# 2. Configuramos qué responder cuando alguien excede el límite (Error 429)
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Demasiadas peticiones",
            "mensaje": "Has superado el límite de peticiones permitido. Por favor, intenta más tarde."
        }
    )

# --- CONFIGURACIÓN CORS ---
# Obtenemos la cadena del .env y la convertimos en lista
origins_raw = os.getenv("ALLOWED_ORIGINS") 
origins = origins_raw.split(",") 

# Agregamos el middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            
    allow_credentials=True,           
    allow_methods=["*"],              
    allow_headers=["*"],              
)

# --- INCLUSIÓN DE ROUTERS ---
app.include_router(auth_router.auth_router)
app.include_router(users.user_router)
app.include_router(animes.anime_router)
app.include_router(videojuegos.videojuego_router)


@app.get("/")
def read_root():
    return {"status": "Zahori Log API funcionando"}