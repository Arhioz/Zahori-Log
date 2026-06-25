from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
#from limiter import limiter
import auth, crud, models, schemas
from database import get_db

user_router = APIRouter(
    prefix="/users",
    tags=["Usuarios"]
)


# --- ENDPOINT PARA CREAR NUEVO USUARIO ---

@user_router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
#@limiter.limit("3/hour")
async def crear_nuevo_usuario(request: Request, usuario: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """Endpont para crear nuevo usuario"""
    # 1. Verificamos si existe
    db_usuario = await crud.obtener_usuario_por_username(db, username=usuario.username)
    if db_usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El usuario {usuario.username} ya exite")
    # 2. Creamos el usuario en la DB
    nuevo_usuario = await crud.crear_usuario(db=db, user=usuario)
    return nuevo_usuario

@user_router.post("/register_pro", response_model=schemas.UserResponsePro, status_code=status.HTTP_201_CREATED)
#@limiter.limit("10/hour")
async def crear_nuevo_usuario_pro(request: Request, usuario: schemas.UserCreatePro, db: AsyncSession = Depends(get_db), admin: models.User = Depends(auth.verificar_rol_admin)):
    """Endpoint para crear un usuario sin restricciones de nombre de usuario y contraseña"""
    # 1. Verificamos si existe
    db_usuario = await crud.obtener_usuario_por_username(db, username=usuario.username)
    if db_usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El usuario {usuario.username} ya exite")
    # 2. Creamos el usuario en la DB
    nuevo_usuario = await crud.crear_usuario_pro(db=db, user=usuario)
    return nuevo_usuario

@user_router.get("/", response_model=list[schemas.UserSimpleResponse])
#@limiter.limit("50/minute")
async def obtener_todos_los_usuarios(request: Request, db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 10, admin: models.User = Depends(auth.verificar_rol_admin)):
    """Endpoint para obtener a todos los usuarios"""
    return await crud.obtener_usuarios(db, skip=skip, limit=limit)

@user_router.patch("/{usuario_id}/change_password", response_model=schemas.UserSimpleResponse)
#@limiter.limit("10/minute")
async def cambiar_password_de_un_usuario(request: Request, usuario_id: int, datos: schemas.UserChangePassword, db: AsyncSession = Depends(get_db), usuario: models.User = Depends(auth.obtener_usuario_actual)):
    """Endpoint para actualizar password de un usuario"""
    encontrado = await crud.obtener_usuario_por_id(db, user_id=usuario_id)
    if encontrado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if usuario.role != "admin" and usuario.id != encontrado.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para realizar esta accion")
    resultado = await crud.cambiar_password_usuario(db=db, user_db=encontrado, datos_nuevos=datos)
    return resultado

@user_router.put("/{usuario_id}", response_model=schemas.UserSimpleResponse)
#@limiter.limit("10/minute")
async def actualizar_datos_de_un_usuario(request: Request, usuario_id: int, datos: schemas.UserCreate, db: AsyncSession = Depends(get_db), usuario: models.User = Depends(auth.obtener_usuario_actual)):
    """Endpoint para actualizar los datos de un usuario"""
    encontrado = await crud.obtener_usuario_por_id(db, user_id=usuario_id)
    if encontrado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if usuario.role != "admin" and usuario.id != encontrado.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para realizar esta accion")
    resultado = await crud.actualizar_datos_usuario(db=db, user_db=encontrado, datos_nuevos=datos)
    return resultado

@user_router.delete("/{usuario_id}")
async def eliminar_un_usuario(usuario_id: int, db: AsyncSession = Depends(get_db), admin: models.User = Depends(auth.verificar_rol_admin)):
    """Endpoint para eliminar un usuario"""
    encontrado = await crud.obtener_usuario_por_id(db, user_id=usuario_id)
    if encontrado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    encontrado_respaldo = encontrado
    try:    
        return await crud.eliminar_usuario(db=db, user_db=encontrado)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"ERROR CRÍTICO al borrar usuario {encontrado_respaldo.username}: {str(e)}")

@user_router.patch("/{usuario_id}/role", response_model=schemas.UserResponse)
async def cambiar_rol_usuario(request: Request, usuario_id: int, datos: schemas.UserRoleUpdate, db: AsyncSession = Depends(get_db), admin: models.User = Depends(auth.verificar_rol_admin)):
    """Endpoint para cambiar de rol a un usuario"""
    encontrado = await crud.obtener_usuario_por_id(db, user_id=usuario_id)
    if not encontrado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    resultado = await crud.actualizar_rol_usuario(db=db, user_db=encontrado, datos_nuevos=datos)
    return resultado