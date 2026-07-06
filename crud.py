from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
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


# --- OPERACIONES DE ANIME (CATÁLOGO LOCAL) ---

async def obtener_anime_por_jikan_id(db: AsyncSession, jikan_id: int):
    """Busca un anime en el catálogo local usando el ID oficial de Jikan."""
    query = select(models.Anime).where(models.Anime.jikan_id == jikan_id)
    resultado = await db.execute(query)
    return resultado.scalars().first()

async def crear_anime_local(db: AsyncSession, jikan_data: dict):
    """Guarda un nuevo anime en el catálogo local con los datos de Jikan."""
    # Extraemos de la respuesta de Jikan lo necesario para tu modelo
    nuevo_anime = models.Anime(
        jikan_id=jikan_data.get("mal_id"),
        title=jikan_data.get("title"),
        title_japanese=jikan_data.get("title_japanese"),
        image_url=jikan_data.get("images", {}).get("jpg", {}).get("image_url"),
        type=jikan_data.get("type"),
        episodes=jikan_data.get("episodes"),
        duration=jikan_data.get("duration"),
        studio=[estudio["name"] for estudio in jikan_data["studios"]],
        aired=jikan_data.get("aired", {}).get("string"),
        genre = [genero["name"] for genero in jikan_data["genres"]], # List comprehension, permite crear nuevas listas de forma concisa y elegante aplicando una expresión a cada elemento de un iterable existente (como otra lista o un rango)
        synopsis=jikan_data.get("synopsis"),
        global_score=jikan_data.get("score")
    )
    db.add(nuevo_anime)
    await db.commit()
    await db.refresh(nuevo_anime)
    return nuevo_anime


# --- OPERACIONES DE ANIME LOG (Log Personal) ---

# 1. Buscar si el usuario ya tiene este anime registrado en su lista
async def obtener_anime_log_por_usuario_y_anime(db: AsyncSession, user_id: int, anime_id: int):
    """Verifica si un anime específico ya está en la lista de un usuario específico."""
    query = select(models.AnimeLog).where(
        models.AnimeLog.user_id == user_id,
        models.AnimeLog.anime_id == anime_id
    )
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 2. Agregar un nuevo anime al historial del usuario
async def añadir_anime_al_log(db: AsyncSession, log_data: schemas.AnimeLogCreate, user_id: int):
    """Crea el registro de un anime en el diario personal del usuario."""
    # Usamos **log_data.model_dump() para desempacar los datos del schema (anime_id, visto, puntuacion_personal)
    nuevo_log = models.AnimeLog(
        **log_data.model_dump(),
        user_id=user_id # Asignamos al dueño (el usuario que hizo la petición)
    )
    db.add(nuevo_log)
    await db.commit()
    
    # Le decimos que traiga las relaciones 'anime' y 'user'.
    query = (
        select(models.AnimeLog)
        .where(models.AnimeLog.id == nuevo_log.id)
        .options(
            selectinload(models.AnimeLog.anime),
            selectinload(models.AnimeLog.user)
        )
    )
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 3. Obtener toda la lista personal de animes de un usuario
async def obtener_animes_de_usuario(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    """Devuelve el catálogo personal completo de animes de un usuario."""
    query = (
        select(models.AnimeLog)
        .where(models.AnimeLog.user_id == user_id)
        .options(
            selectinload(models.AnimeLog.anime),  # <--- Precargamos el anime
            selectinload(models.AnimeLog.user)    # <--- Precargamos el usuario
        )
        .offset(skip)
        .limit(limit)
    )
    resultado = await db.execute(query)
    return resultado.scalars().all()

# 4. Obtener un registro específico del log
async def obtener_anime_log_por_id(db: AsyncSession, log_id: int, user_id: int):
    """Busca un registro específico en el log asegurando que pertenezca al usuario autenticado."""
    query = (
        select(models.AnimeLog)
        .where(models.AnimeLog.id == log_id, models.AnimeLog.user_id == user_id)
        .options(
            selectinload(models.AnimeLog.anime),
            selectinload(models.AnimeLog.user)
        )
    )
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 5. Actualizar registro del log
async def actualizar_estado_anime_log(db: AsyncSession, log_db: models.AnimeLog, datos_nuevos: schemas.AnimeLogEstado):
    """Actualiza el estado de un anime en el diario personal."""
    log_db.status = datos_nuevos.status
    await db.commit()
    await db.refresh(log_db)
    return log_db

# 6. Actualizar puntuacion del anime en el log
async def actualizar_puntuacion_anime_log(db: AsyncSession, log_db: models.AnimeLog, datos_nuevos: schemas.AnimeLogPuntuacion):
    """Actualiza la puntuacion de un anime en el diario personal."""
    log_db.user_rating = datos_nuevos.user_rating
    await db.commit()
    await db.refresh(log_db)
    return log_db

# 7. Actualizar estado favorito del anime en el log
async def actualizar_favorito_anime_log(db: AsyncSession, log_db: models.AnimeLog, is_favorite: bool):
    """Actualiza el estado de favorito de un anime en el diario personal."""
    log_db.is_favorite = is_favorite
    await db.commit()
    await db.refresh(log_db)
    return log_db

#8. Eliminar un anime del log
async def eliminar_un_anime_log(db: AsyncSession, log_db: models.AnimeLog):
    """Elimina un anime del diario personal"""
    await db.delete(log_db)
    await db.commit()
    return {"message": "Anime eliminado del diario personal"}

# --- OPERACIONES DE VIDEOJUEGO (CATÁLOGO LOCAL) ---

async def obtener_videojuego_por_rawg_id(db: AsyncSession, rawg_id: int):
    """Busca un videojuego en el catálogo local usando el ID oficial de RAWG."""
    query = select(models.Videojuego).where(models.Videojuego.rawg_id == rawg_id)
    resultado = await db.execute(query)
    return resultado.scalars().first()

async def crear_videojuego_local(db: AsyncSession, rawg_data: dict):
    """Guarda un nuevo videojuego en el catálogo local con los datos de RAWG."""
    # Extraemos de la respuesta de RAWG lo necesario para tu modelo
    nuevo_videojuego = models.Videojuego(
        rawg_id=rawg_data.get("id"),
        title=rawg_data.get("name"),
        image_url=rawg_data.get("background_image"),
        released=rawg_data.get("released"),
        genre = [genero["name"] for genero in rawg_data["genres"]],
        description=rawg_data.get("description"),
        developers=[desarrollador["name"] for desarrollador in rawg_data["developers"]],
        platforms = [item["platform"]["name"] for item in rawg_data["platforms"]],
        metacritic_score = rawg_data.get("metacritic")
    )
    db.add(nuevo_videojuego)
    await db.commit()
    await db.refresh(nuevo_videojuego)
    return nuevo_videojuego

# --- OPERACIONES DE VIDEOJUEGO LOG (Log Personal) ---

# 1. Buscar si el usuario ya tiene este anime registrado en su lista
async def obtener_videojuego_log_por_usuario_y_videojuego(db: AsyncSession, user_id: int, game_id: int):
    """Verifica si un videojuego específico ya está en la lista de un usuario específico."""
    query = select(models.VideojuegoLog).where(
        models.VideojuegoLog.user_id == user_id,
        models.VideojuegoLog.game_id == game_id
    )
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 2. Agregar un nuevo anime al historial del usuario
async def añadir_videojuego_al_log(db: AsyncSession, log_data: schemas.VideojuegoLogCreate, user_id: int):
    """Crea el registro de un videojuego en el diario personal del usuario."""
    # Usamos **log_data.model_dump() para desempacar los datos del schema (videojuego_id, jugando, puntuacion_personal)
    nuevo_log = models.VideojuegoLog(
        **log_data.model_dump(),
        user_id=user_id
    )
    db.add(nuevo_log)
    await db.commit()
    
    # Le decimos que traiga las relaciones 'videojuego' y 'user'.
    query = (
        select(models.VideojuegoLog)
        .where(models.VideojuegoLog.id == nuevo_log.id)
        .options(
            selectinload(models.VideojuegoLog.game),
            selectinload(models.VideojuegoLog.user)
        )
    )
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 3. Obtener toda la lista personal de videojuegos de un usuario
async def obtener_videojuegos_de_usuario(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    """Devuelve el catálogo personal completo de videojuegos de un usuario."""
    query = (
        select(models.VideojuegoLog)
        .where(models.VideojuegoLog.user_id == user_id)
        .options(
            selectinload(models.VideojuegoLog.game),  # <--- Precargamos el videojuego
            selectinload(models.VideojuegoLog.user)    # <--- Precargamos el usuario
        )
        .offset(skip)
        .limit(limit)
    )
    resultado = await db.execute(query)
    return resultado.scalars().all()

# 4. Obtener un registro específico del log
async def obtener_videojuego_log_por_id(db: AsyncSession, log_id: int, user_id: int):
    """Busca un registro específico en el log asegurando que pertenezca al usuario autenticado."""
    query = (
        select(models.VideojuegoLog)
        .where(models.VideojuegoLog.id == log_id, models.VideojuegoLog.user_id == user_id)
        .options(
            selectinload(models.VideojuegoLog.game),
            selectinload(models.VideojuegoLog.user)
        )
    )
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 5. Actualizar registro del log
async def actualizar_estado_videojuego_log(db: AsyncSession, log_db: models.VideojuegoLog, datos_nuevos: schemas.VideojuegoLogEstado):
    """Actualiza el estado de un videojuego en el diario personal."""
    log_db.status = datos_nuevos.status
    await db.commit()
    await db.refresh(log_db)
    return log_db

# 6. Actualizar puntuacion del videojuego en el log
async def actualizar_puntuacion_videojuego_log(db: AsyncSession, log_db: models.VideojuegoLog, datos_nuevos: schemas.VideojuegoLogPuntuacion):
    """Actualiza la puntuacion de un videojuego en el diario personal."""
    log_db.user_rating = datos_nuevos.user_rating
    await db.commit()
    await db.refresh(log_db)
    return log_db

# 7. Actualizar estado favorito del videojuego en el log
async def actualizar_favorito_videojuego_log(db: AsyncSession, log_db: models.VideojuegoLog, is_favorite: bool):
    """Actualiza el estado de favorito de un videojuego en el diario personal."""
    log_db.is_favorite = is_favorite
    await db.commit()
    await db.refresh(log_db)
    return log_db

#8. Eliminar un videojuego del log
async def eliminar_un_videojuego_log(db: AsyncSession, log_db: models.VideojuegoLog):
    """Elimina un videojuego del diario personal"""
    await db.delete(log_db)
    await db.commit()
    return {"message": "Videojuego eliminado del diario personal"}