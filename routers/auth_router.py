from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

import auth, crud, schemas
from limiter import limiter
from database import get_db

auth_router = APIRouter(
    tags=["Autenticación"]
)

# Habilita el boton "Authorize" en swagger
@auth_router.post("/token", response_model=schemas.Token)
@limiter.limit("5/minute")
async def login_para_obtener_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # 1. Buscamos al usuario por su username
    usuario = await crud.obtener_usuario_por_username(db, username=form_data.username)
    
    # 2. Verificamos que el usuario exista y la contraseña sea correcta
    if not usuario or not auth.verify_password(form_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Si todo es correcto, generamos el pasaporte (Token JWT)
    access_token = auth.create_access_token(data={"sub": usuario.username})
    
    # 4. Devolvemos el token al usuario
    return {"access_token": access_token, "token_type": "bearer"}