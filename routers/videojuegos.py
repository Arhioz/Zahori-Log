from fastapi import APIRouter, HTTPException, Query, Path, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from services import rawg_client
import crud, schemas, models, auth
from limiter import limiter
from database import get_db

videojuego_router = APIRouter(
    prefix="/videojuegos",
    tags=["Catálogo de Videojuegos (RAWG)"]
)

@videojuego_router.get("/buscar")
@limiter.limit("20/minute")
async def buscar_videojuego(request: Request, search: str = Query(..., description="Nombre del videojuego a buscar"), page_size: int = 5):
    """Endpoint para buscar videojuegos por coincidencia de nombre."""
    resultados = await rawg_client.buscar_videojuego_por_nombre(query=search, limite=page_size)
    if not resultados:
        raise HTTPException(status_code=404, detail="No se encontraron videojuegos con ese nombre.")
    return resultados

@videojuego_router.get("/{id_videojuego}")
@limiter.limit("20/minute")
async def obtener_videojuego_por_id(request: Request, id_videojuego: int = Path(..., description="ID oficial de RAWG")):
    """Endpoint para obtener la ficha técnica completa de un videojuego por su ID."""
    resultado = await rawg_client.buscar_videojuego_por_id(id_videojuego=id_videojuego)
    return resultado

# --- RUTAS PROTEGIDAS (LOG PERSONAL) ---

@videojuego_router.post("/mi-lista", response_model=schemas.VideojuegoLogResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def agregar_videojuego_a_mi_lista(
    request: Request,
    datos_log: schemas.VideojuegoLogCreate, 
    db: AsyncSession = Depends(get_db), 
    usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Agrega un videojuego al diario personal del usuario autenticado, asegurando su existencia local."""
    # PASO 1: Verificar si el videojuego ya está en la tabla local 'videojuegos'
    videojuego_local = await crud.obtener_videojuego_por_rawg_id(db, rawg_id=datos_log.game_id)
    
    # PASO 2: Si no existe localmente, vamos por él a RAWG y lo guardamos
    if not videojuego_local:
        # 2.1 Intentamos traerlo de RAWG de forma aislada
        try:
            datos_rawg = await rawg_client.buscar_videojuego_por_id(id_videojuego=datos_log.game_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El videojuego con ID {datos_log.game_id} no fue encontrado en la API externa de RAWG."
            )
        
        # 2.2 Si RAWG lo devolvió con éxito, intentamos guardarlo localmente sin ocultar los errores
        videojuego_local = await crud.crear_videojuego_local(db=db, rawg_data=datos_rawg)

    # PASO 3: Verificar que el usuario no tenga ya este mismo videojuego en su diario personal
    log_existente = await crud.obtener_videojuego_log_por_usuario_y_videojuego(
        db=db, user_id=usuario_actual.id, game_id=videojuego_local.id
    )
    if log_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya tienes este videojuego registrado en tu lista personal."
        )
    
    # PASO 4: Modificamos momentáneamente el ID del esquema para que use el ID local de la tabla 'videojuegos'
    # ya que 'datos_log.videojuego_id' traía el ID de RAWG, pero necesitamos el ID autonumérico local (FK)
    datos_log.game_id = videojuego_local.id

    # PASO 5: Guardar en el diario personal (videojuego_logs)
    nuevo_log = await crud.añadir_videojuego_al_log(db=db, log_data=datos_log, user_id=usuario_actual.id)
    return nuevo_log

@videojuego_router.get("/mi-lista/completa", response_model=list[schemas.VideojuegoLogResponse])
@limiter.limit("20/minute")
async def obtener_mi_lista_de_videojuegos(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Devuelve el catálogo personal completo de videojuegos del usuario autenticado."""
    mi_lista = await crud.obtener_videojuegos_de_usuario(
        db, user_id=usuario_actual.id, skip=skip, limit=limit
    )
    return mi_lista

@videojuego_router.patch("/mi-lista/estado/{log_id}", response_model=schemas.VideojuegoLogResponse)
@limiter.limit("20/minute")
async def actualizar_estado_videojuego_en_mi_lista(
    request: Request,
    log_id: int,
    datos_actualizacion: schemas.VideojuegoLogEstado,
    db: AsyncSession = Depends(get_db),
    usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Actualiza el estado de un videojuego en el diario personal."""
    log_existente = await crud.obtener_videojuego_log_por_id(db=db, log_id=log_id, user_id=usuario_actual.id)
    if not log_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El registro no existe en tu lista.")
    log_actualizado = await crud.actualizar_estado_videojuego_log(db=db, log_db=log_existente, datos_nuevos=datos_actualizacion)
    return log_actualizado

@videojuego_router.patch("/mi-lista/puntuacion/{log_id}", response_model=schemas.VideojuegoLogResponse)
@limiter.limit("20/minute")
async def actualizar_puntuacion_videojuego_en_mi_lista(
    request: Request,
    log_id: int,
    datos_actualizacion: schemas.VideojuegoLogPuntuacion,
    db: AsyncSession = Depends(get_db),
    usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Actualiza la puntuacion de un videojuego en el diario personal."""
    log_existente = await crud.obtener_videojuego_log_por_id(db=db, log_id=log_id, user_id=usuario_actual.id)
    if not log_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El registro no existe en tu lista.")
    log_actualizado = await crud.actualizar_puntuacion_videojuego_log(db=db, log_db=log_existente, datos_nuevos=datos_actualizacion)
    return log_actualizado

@videojuego_router.patch("/mi-lista/favorito/{log_id}", response_model=schemas.VideojuegoLogResponse)
@limiter.limit("20/minute")
async def actualizar_favorito_videojuego_en_mi_lista(
    request: Request, log_id: int, datos_actualizacion: schemas.VideojuegoLogFavorito,
    db: AsyncSession = Depends(get_db), usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Añade o quita un videojuego de los favoritos."""
    log_existente = await crud.obtener_videojuego_log_por_id(db=db, log_id=log_id, user_id=usuario_actual.id)
    if not log_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El registro no existe en tu lista.")
    
    log_actualizado = await crud.actualizar_favorito_videojuego_log(db=db, log_db=log_existente, is_favorite=datos_actualizacion.is_favorite)
    return log_actualizado

@videojuego_router.delete("/mi-lista/{log_id}")
@limiter.limit("20/minute")
async def eliminar_un_videojuego_del_log(
    request: Request,
    log_id: int,
    db: AsyncSession = Depends(get_db),
    usuario_actual: models.User = Depends(auth.obtener_usuario_actual)
):
    """Elimina un videojuego del diario personal"""
    log_existente = await crud.obtener_videojuego_log_por_id(db=db, log_id=log_id, user_id=usuario_actual.id)
    if not log_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El registro no existe en tu lista.")
    return await crud.eliminar_un_videojuego_log(db=db, log_db=log_existente)