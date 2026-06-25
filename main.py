import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import auth_router, users, animes


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


@app.get("/")
def read_root():
    return {"status": "Zahori Log API funcionando"}