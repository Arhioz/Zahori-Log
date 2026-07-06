from fastapi import APIRouter, HTTPException, Query, Path, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from services import jikan_client
import crud, schemas, models, auth
from limiter import limiter
from database import get_db

anime_router = APIRouter(
    prefix="/animes",
    tags=["Catálogo de Animes (Jikan)"]
)

@anime_router.get("/buscar")
@limiter.limit("20/minute")
async def buscar_anime(request: Request, q: str = Query(..., description="Nombre del anime a buscar"), limite: int = 5):
    """Endpoint para buscar animes por coincidencia de nombre."""
    resultados = await jikan_client.buscar_anime_por_nombre(query=q, limite=limite)
    if not resultados:
        raise HTTPException(status_code=404, detail="No se encontraron animes con ese nombre.")
    return resultados

@anime_router.get("/{id_anime}")
@limiter.limit("20/minute")
async def obtener_anime_por_id(request: Request, id_anime: int = Path(..., description="ID oficial de Jikan")):
    """Endpoint para obtener la ficha técnica completa de un anime por su ID."""
    resultado = await jikan_client.buscar_anime_por_id(id_anime=id_anime)
    return resultado

# --- RUTAS PROTEGIDAS (LOG PERSONAL) ---

@anime_router.post("/mi-lista", response_model=schemas.AnimeLogResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def agregar_anime_a_mi_lista(
    request: Request,
    datos_log: schemas.AnimeLogCreate, 
    db: AsyncSession = Depends(get_db), 
    usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Agrega un anime al diario personal del usuario autenticado, asegurando su existencia local."""
    # PASO 1: Verificar si el anime ya está en la tabla local 'animes'
    anime_local = await crud.obtener_anime_por_jikan_id(db, jikan_id=datos_log.anime_id)
    
    # PASO 2: Si no existe localmente, vamos por él a Jikan y lo guardamos
    if not anime_local:
        # 2.1 Intentamos traerlo de Jikan de forma aislada
        try:
            datos_jikan = await jikan_client.buscar_anime_por_id(id_anime=datos_log.anime_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El anime con ID {datos_log.anime_id} no fue encontrado en la API externa de Jikan."
            )
        
        # 2.2 Si Jikan lo devolvió con éxito, intentamos guardarlo localmente sin ocultar los errores
        anime_local = await crud.crear_anime_local(db=db, jikan_data=datos_jikan)

    # PASO 3: Verificar que el usuario no tenga ya este mismo anime en su diario personal
    log_existente = await crud.obtener_anime_log_por_usuario_y_anime(
        db=db, user_id=usuario_actual.id, anime_id=anime_local.id
    )
    if log_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya tienes este anime registrado en tu lista personal."
        )
    
    # PASO 4: Modificamos momentáneamente el ID del esquema para que use el ID local de la tabla 'animes'
    # ya que 'datos_log.anime_id' traía el ID de Jikan, pero necesitamos el ID autonumérico local (FK)
    datos_log.anime_id = anime_local.id

    # PASO 5: Guardar en el diario personal (anime_logs)
    nuevo_log = await crud.añadir_anime_al_log(db=db, log_data=datos_log, user_id=usuario_actual.id)
    return nuevo_log

@anime_router.get("/mi-lista/completa", response_model=list[schemas.AnimeLogResponse])
@limiter.limit("20/minute")
async def obtener_mi_lista_de_animes(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Devuelve el catálogo personal completo de animes del usuario autenticado."""
    mi_lista = await crud.obtener_animes_de_usuario(
        db, user_id=usuario_actual.id, skip=skip, limit=limit
    )
    return mi_lista

@anime_router.patch("/mi-lista/estado/{log_id}", response_model=schemas.AnimeLogResponse)
@limiter.limit("20/minute")
async def actualizar_estado_anime_en_mi_lista(
    request: Request,
    log_id: int,
    datos_actualizacion: schemas.AnimeLogEstado,
    db: AsyncSession = Depends(get_db),
    usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Actualiza el estado de un anime en el diario personal."""
    log_existente = await crud.obtener_anime_log_por_id(db=db, log_id=log_id, user_id=usuario_actual.id)
    if not log_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El registro no existe en tu lista.")
    log_actualizado = await crud.actualizar_estado_anime_log(db=db, log_db=log_existente, datos_nuevos=datos_actualizacion)
    return log_actualizado

@anime_router.patch("/mi-lista/puntuacion/{log_id}", response_model=schemas.AnimeLogResponse)
@limiter.limit("20/minute")
async def actualizar_puntuacion_anime_en_mi_lista(
    request: Request,
    log_id: int,
    datos_actualizacion: schemas.AnimeLogPuntuacion,
    db: AsyncSession = Depends(get_db),
    usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Actualiza la puntuacion de un anime en el diario personal."""
    log_existente = await crud.obtener_anime_log_por_id(db=db, log_id=log_id, user_id=usuario_actual.id)
    if not log_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El registro no existe en tu lista.")
    log_actualizado = await crud.actualizar_puntuacion_anime_log(db=db, log_db=log_existente, datos_nuevos=datos_actualizacion)
    return log_actualizado

@anime_router.patch("/mi-lista/favorito/{log_id}", response_model=schemas.AnimeLogResponse)
@limiter.limit("20/minute")
async def actualizar_favorito_anime_en_mi_lista(
    request: Request, log_id: int, datos_actualizacion: schemas.AnimeLogFavorito,
    db: AsyncSession = Depends(get_db), usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Añade o quita un anime de los favoritos."""
    log_existente = await crud.obtener_anime_log_por_id(db=db, log_id=log_id, user_id=usuario_actual.id)
    if not log_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El registro no existe en tu lista.")
    
    log_actualizado = await crud.actualizar_favorito_anime_log(db=db, log_db=log_existente, is_favorite=datos_actualizacion.is_favorite)
    return log_actualizado

@anime_router.delete("/mi-lista/{log_id}")
@limiter.limit("20/minute")
async def eliminar_un_anime_del_log(
    request: Request,
    log_id: int,
    db: AsyncSession = Depends(get_db),
    usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Elimina un anime del diario personal"""
    log_existente = await crud.obtener_anime_log_por_id(db=db, log_id=log_id, user_id=usuario_actual.id)
    if not log_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El registro no existe en tu lista.")
    return await crud.eliminar_un_anime_log(db=db, log_db=log_existente)