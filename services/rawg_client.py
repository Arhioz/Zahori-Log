import os
from dotenv import load_dotenv
import httpx
from fastapi import HTTPException, status

# Cargamos las variables del .env para poder leer la API Key
load_dotenv()

# Definimos la URL base y traemos la llave segura
RAWG_BASE_URL = "https://api.rawg.io/api"
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

async def buscar_videojuego_por_nombre(query: str, limite: int = 5):
    """
    Busca videojuegos en RAWG por coincidencia de nombre.
    """
    if not RAWG_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="API Key de RAWG no configurada en el servidor."
        )

    url = f"{RAWG_BASE_URL}/games"
    
    # RAWG requiere la llave, el término de búsqueda ('search') y el límite ('page_size')
    parametros = {"key": RAWG_API_KEY, "search": query, "page_size": limite}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=parametros)
            response.raise_for_status()
            data = response.json()
            
            # RAWG devuelve la lista de juegos dentro de la llave "results"
            return data.get("results", [])
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Error al consultar la información en RAWG."
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="El servicio de catálogo de videojuegos no está disponible en este momento."
            )

async def buscar_videojuego_por_id(id_videojuego: int):
    """
    Obtiene la ficha técnica completa de un videojuego por su ID exacto.
    """
    if not RAWG_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="API Key de RAWG no configurada en el servidor."
        )

    url = f"{RAWG_BASE_URL}/games/{id_videojuego}"
    
    # Incluso buscando por ID en la ruta, RAWG exige la llave
    parametros = {"key": RAWG_API_KEY}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=parametros)
            response.raise_for_status()
            
            # Como es un solo juego, no viene envuelto en una lista, nos devuelve el diccionario directo
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"Videojuego con ID {id_videojuego} no encontrado en RAWG."
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Error al consultar el videojuego en RAWG."
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="El servicio de catálogo de videojuegos no está disponible en este momento."
            )