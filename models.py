from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

# 1. Tabla de Usuarios
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user") # Puede ser ej: "user", "admin", "editor"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    anime_logs = relationship("AnimeLog", back_populates="user")
    videojuego_logs = relationship("VideojuegoLog", back_populates="user")

# 2. Catálogo Local de Animes (Estructura optimizada para la API externa Jikan)
class Anime(Base):
    __tablename__ = "animes"

    id = Column(Integer, primary_key=True, index=True)
    jikan_id = Column(Integer, unique=True, index=True, nullable=False)  # ID de la API Jikan
    title = Column(String, nullable=False)
    title_japanese = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    type = Column(String, nullable=True)
    episodes = Column(Integer, default=0)
    duration = Column(String, nullable=True)
    studio = Column(MutableList.as_mutable(ARRAY(String)), nullable=True)
    aired = Column(String, nullable=True)
    genre = Column(MutableList.as_mutable(ARRAY(String)), nullable=True)
    synopsis = Column(Text, nullable=True)
    global_score = Column(Float, nullable=True)

    # Relación inversa con el Log
    user_logs = relationship("AnimeLog", back_populates="anime")

# 3. Registro Personal de Animes (Tabla Intermedia)
class AnimeLog(Base):
    __tablename__ = "anime_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    anime_id = Column(Integer, ForeignKey("animes.id", ondelete="CASCADE"), nullable=False)
    
    # Datos del Log Personal
    status = Column(String, default="Viendo")  # Viendo, Completado, En Espera, Abandonado
    current_episode = Column(Integer, default=0)
    user_rating = Column(Float, nullable=True)  # Calificación del usuario (ej. del 1 al 10)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_favorite = Column(Boolean, default=False)

    # Relaciones de SQLAlchemy
    user = relationship("User", back_populates="anime_logs")
    anime = relationship("Anime", back_populates="user_logs")

# 4. Catálogo Local de Videojuegos (Estructura optimizada para la API externa RAWG)
class Videojuego(Base):
    __tablename__ = "videojuegos"

    id = Column(Integer, primary_key=True, index=True)
    rawg_id = Column(Integer, unique=True, index=True, nullable=False)  # ID de la API RAWG
    title = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    released = Column(String, nullable=True) # <- Fecha de lanzamineto del videojuego
    genre = Column(MutableList.as_mutable(ARRAY(String)), nullable=True)
    description = Column(Text, nullable=True) # <- Guarda la descripción del juego
    developers = Column(MutableList.as_mutable(ARRAY(String)), nullable=True)
    platforms = Column(MutableList.as_mutable(ARRAY(String)), nullable=True)
    metacritic_score = Column(Float, nullable=True)

    # Relación inversa con el Log
    user_logs = relationship("VideojuegoLog", back_populates="game")

# 5. Registro Personal de Videojuegos (Tabla Intermedia)
class VideojuegoLog(Base):
    __tablename__ = "videojuego_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    game_id = Column(Integer, ForeignKey("videojuegos.id", ondelete="CASCADE"), nullable=False)
    
    # Datos del Log Personal
    status = Column(String, default="Jugando")  # Jugando, Completado, En Espera, Abandonado
    user_rating = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_favorite = Column(Boolean, default=False)

    # Relaciones de SQLAlchemy
    user = relationship("User", back_populates="videojuego_logs")
    game = relationship("Videojuego", back_populates="user_logs")