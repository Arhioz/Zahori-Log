from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import auth, models, schemas

# --- OPERACIONES DE USUARIO ---

# 1. Buscar usuario por su Username
async def obtener_usuario_por_username(db: AsyncSession, username: str):
    query = select(models.User).where(models.User.username == username)
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 1.1 Buscar un usuario por su ID
async def obtener_usuario_por_id(db: AsyncSession, user_id: int):
    query = select(models.User).where(models.User.id == user_id)
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 1.2 Buscar usuario por su Email
async def obtener_usuario_por_email(db: AsyncSession, email: str):
    query = select(models.User).where(models.User.email == email)
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 1.3 Muestra todos los usuarios
async def obtener_usuarios(db: AsyncSession, skip: int = 0, limit: int = 10):
    query = (
        select(models.User)
        .offset(skip)
        .limit(limit)
    )
    resultado = await db.execute(query)
    return resultado.scalars().all()

# 2. Registrar un nuevo usuario en la base de datos
async def crear_usuario(db: AsyncSession, user: schemas.UserCreate):
    # Encriptamos la contraseña que viene del schema.
    hashed_password = auth.get_password_hash(user.password)
    
    # Creamos el objeto de SQLAlchemy basado en models.py
    nuevo_usuario = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        # is_active y role tomarán sus valores por defecto si los configuraste en models.py
    )
    
    # Lo agregamos a la sesión, guardamos y refrescamos para obtener su ID
    db.add(nuevo_usuario)
    await db.commit()
    await db.refresh(nuevo_usuario)
    
    return nuevo_usuario

# 2.1 Registra un nuevo usuario Pro sin restriccion de contraseña gracias a UserCreatePro
async def crear_usuario_pro(db: AsyncSession, user: schemas.UserCreatePro):
    hashed_password = auth.get_password_hash(user.password)

    nuevo_usuario = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    db.add(nuevo_usuario)
    await db.commit()
    return nuevo_usuario

# 3. Actualizar el password de un usuario
async def cambiar_password_usuario(db: AsyncSession, user_db: models.User, datos_nuevos: schemas.UserChangePassword):
    hashed_password = auth.get_password_hash(datos_nuevos.password)

    user_db.hashed_password = hashed_password

    await db.commit()
    await db.refresh(user_db)
    return user_db

# 3.1 Actualizar username, email y password de un usuario
async def actualizar_datos_usuario(db: AsyncSession, user_db: models.User, datos_nuevos: schemas.UserCreate):
    hashed_password = auth.get_password_hash(datos_nuevos.password)

    user_db.username = datos_nuevos.username
    user_db.email = datos_nuevos.email
    user_db.hashed_password = hashed_password
    
    await db.commit()
    await db.refresh(user_db)
    return user_db

# 3.2 Actualizar rol de usuario
async def actualizar_rol_usuario(db: AsyncSession, user_db: models.User, datos_nuevos: schemas.UserRoleUpdate):
    user_db.role = datos_nuevos.role

    await db.commit()
    await db.refresh(user_db)
    return user_db

# 4. Elimina un usuario por username de la DB
async def eliminar_usuario(db: AsyncSession, user_db: models.User):
    await db.delete(user_db)
    await db.commit()
    return user_db