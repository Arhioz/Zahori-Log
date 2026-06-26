from fastapi import APIRouter, HTTPException, Query, Path
from services import jikan_client

anime_router = APIRouter(
    prefix="/animes",
    tags=["Catálogo de Animes (Jikan)"]
)

@anime_router.get("/buscar")
async def buscar_anime(q: str = Query(..., description="Nombre del anime a buscar"), limite: int = 5):
    """Endpoint para buscar animes por coincidencia de nombre."""
    resultados = await jikan_client.buscar_anime_por_nombre(query=q, limite=limite)
    
    if not resultados:
        raise HTTPException(status_code=404, detail="No se encontraron animes con ese nombre.")
    
    return resultados

@anime_router.get("/{id_anime}")
async def obtener_anime_por_id(id_anime: int = Path(..., description="ID oficial de Jikan")):
    """Endpoint para obtener la ficha técnica completa de un anime por su ID."""
    resultado = await jikan_client.buscar_anime_por_id(id_anime=id_anime)
    return resultado