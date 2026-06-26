from fastapi import APIRouter, HTTPException, Query, Path
from services import rawg_client

videojuego_router = APIRouter(
    prefix="/videojuegos",
    tags=["Catálogo de Videojuegos (RAWG)"]
)

@videojuego_router.get("/buscar")
async def buscar_videojuego(search: str = Query(..., description="Nombre del videojuego a buscar"), page_size: int = 5):
    """Endpoint para buscar videojuegos por coincidencia de nombre."""
    resultados = await rawg_client.buscar_videojuego_por_nombre(query=search, limite=page_size)
    
    if not resultados:
        raise HTTPException(status_code=404, detail="No se encontraron videojuegos con ese nombre.")
    
    return resultados

@videojuego_router.get("/{id_videojuego}")
async def obtener_videojuego_por_id(id_videojuego: int = Path(..., description="ID oficial de RAWG")):
    """Endpoint para obtener la ficha técnica completa de un videojuego por su ID."""
    resultado = await rawg_client.buscar_videojuego_por_id(id_videojuego=id_videojuego)
    return resultado