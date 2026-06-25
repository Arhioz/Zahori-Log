import httpx
from fastapi import HTTPException, status

# Definimos la URL base de la API oficial de Jikan
JIKAN_BASE_URL = "https://api.jikan.moe/v4"

async def buscar_anime_por_nombre(query: str, limite: int = 5):
    """
    Se conecta a la API de Jikan para buscar animes por su nombre (Query Parameters).
    Retorna una lista con los resultados obtenidos.
    """
    # Construimos la URL final: https://api.jikan.moe/v4/anime
    url = f"{JIKAN_BASE_URL}/anime"
    
    # Preparamos los parámetros (query parameters) de búsqueda exclusivos para Jikan (?q=Naruto&limit=5)
    """
    La anatomía de esa cadena "?q=Naruto&limit=5" funciona así:
        ? (El iniciador): Le indica al servidor web "A partir de aquí, la URL 
        ya no es una ruta o carpeta, sino una lista de filtros que quiero aplicar"
        q=Naruto (Filtro 1): Busca textos que coincidan con "Naruto".
        & (El pegamento): Sirve para separar múltiples filtros. Significa "Y además..."
        limit=5 (Filtro 2): Entrégame solo los primeros 5 resultados de tu búsqueda.
    """
    parametros = {"q": query, "limit": limite}

    # Abrimos una sesión asíncrona como si abriéramos un navegador invisible
    async with httpx.AsyncClient() as client:
        try:
            # Hacemos la petición GET a Jikan
            response = await client.get(url, params=parametros)
            
            # Esto lanza un error automático si Jikan responde con 404 o 500
            response.raise_for_status() 
            
            # Convertimos la respuesta de texto a un diccionario de Python
            data = response.json()
            
            # Jikan siempre envuelve los resultados dentro de una llave llamada "data"
            return data.get("data", [])
            """
            "data": Le dice a Python "Busca la llave llamada 'data' y entrégame 
            lo que tenga adentro".
            """
            """
            [] (Lista vacía): Es tu salvavidas. Si por alguna razón Jikan cambia 
            su estructura o la respuesta viene vacía y la llave "data" no 
            existe, en lugar de que tu programa colapse con un terrible 
            error (KeyError), Python simplemente te devolverá una lista vacía []. 
            Tu código seguirá funcionando sin romperse.
            """
            
        except httpx.HTTPStatusError as e:
            # Si Jikan nos da un error específico (ej. límite de peticiones excedido)
            raise HTTPException(
                status_code=e.response.status_code, 
                detail="Error al consultar la información en Jikan."
            )
        except httpx.RequestError:
            # Si no tenemos internet o el servidor de Jikan está caído por completo
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="El servicio de catálogo de anime no está disponible en este momento."
            )
        
async def buscar_anime_por_id(id_anime: int):
    """Busca un anime específico usando su ID exacto (Path Parameters)"""
    url = f"{JIKAN_BASE_URL}/anime/{id_anime}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}) # Si es un solo anime, suele venir como diccionario
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El anime con ID {id_anime} no existe en Jikan.")
            raise HTTPException(status_code=e.response.status_code, detail="Error al consultar Jikan.")
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Servicio de Jikan no disponible.")