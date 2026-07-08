from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import re

# Le indicamos a Pydantic que lea los modelos de SQLAlchemy como si fueran diccionarios
class BaseConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- SCHEMAS DE USUARIO ---

# Esquema base con lo que todo usuario comparte
class UserBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="Nombre de usuario único", examples=["User_01"])
    email: EmailStr = Field(..., description="Correo electrónico válido", examples=["example@email.com"])

# Lo que pedimos cuando un usuario se registra (Aquí viaja la contraseña en texto plano)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Contraseña de acceso seguro")

    # La Regex para la contraseña:
    # 8 caracteres, 1 mayúscula, 1 número, 1 símbolo especial
    @field_validator('password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[#@$!%*?&]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial (#@$!%*?&)')
        return v

# Lo que le respondemos al cliente (¡NUNCA devolvemos la contraseña ni el hash!)
class UserResponse(UserBase):
    id: int
    is_active: bool
    role: str = Field(..., examples=["user"])
    created_at: datetime

class UserSimpleResponse(BaseConfigModel):
    id: int
    username: str = Field(..., examples=["itadori_kun"])
    email: str       
    role: str

# Schema para crear usuario sin restricciones de contraseña.
class UserCreatePro(BaseConfigModel):
    username: str
    email: EmailStr
    password: str

class UserResponsePro(UserBase):
    id: int
    is_active: bool
    role: str = Field(..., examples=["admin"])
    created_at: datetime


# --- SCHEMAS DE AUTENTICACIÓN (LOGIN) ---

# Lo que el cliente envía para iniciar sesión
class UserLogin(BaseModel):
    username: str
    password: str

class UserRoleUpdate(BaseConfigModel):
    role: str = Field(..., pattern=r'^(admin|editor|user)$', examples=["editor"])

class UserChangePassword(BaseConfigModel):
    password: str = Field(
        ..., 
        min_length=8,
        examples=["A123456!"]
    )

    @field_validator('password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[#@$!%*?&]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial (#@$!%*?&)')
        return v

# El formato que tendrá la respuesta al iniciar sesión de manera exitosa
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# El esquema de los datos que van dentro del token (el payload)
class TokenData(BaseModel):
    username: Optional[str] = None


# --- SCHEMAS DE ANIMES (Catálogo Global) ---

class AnimeBase(BaseConfigModel):
    jikan_id: int
    title: str = Field(..., min_length=1, max_length=150, examples=["Jujutsu Kaisen"])
    title_japanese: Optional[str] = Field(..., min_length=1, max_length=150)
    image_url: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    # gt=0 asegura que sea mayor a 0.
    episodes: Optional[int] = Field(default=None, gt=0, examples=[24])
    duration: Optional[str] = Field(default=None)
    studio: Optional[list[str]] = Field(..., examples=["MAPPA, Gainax"])
    aired: Optional[str] = Field(default=None)
    genre: Optional[list[str]] = Field(..., examples=["Action, Sci-Fi"])
    synopsis: Optional[str] = Field(default=None)
    global_score: Optional[float] = Field(default=None, ge=0, le=10)

class AnimeCreate(AnimeBase):
    pass

class AnimeResponse(AnimeBase):
    id: int

class AnimeRatingUpdate(BaseConfigModel): # <--- Esquema específico solo para actualizar la puntuacion
    puntuacion: float = Field(..., ge=0, le=10) # Validación: entre 0 y 10


# --- SCHEMA DE VIDEOJUEGOS (Catálogo Global) ---

class VideojuegoBase(BaseConfigModel):
    rawg_id: int
    title: str = Field(..., min_length=1, max_length=150, examples=["Nier Automata"])
    image_url: Optional[str] = Field(default=None)
    released: Optional[str] = Field(default=None)
    genre: Optional[list[str]] = Field(..., examples=["Adventure, Indie"])
    description: Optional[str] = Field(default=None)
    developers: Optional[list[str]] = Field(default=None)
    platforms: Optional[list[str]] = Field(..., examples=["PC, PlayStation"])
    metacritic_score: Optional[float] = Field(default=None, ge=0, le=100)

class VideojuegoCreate(VideojuegoBase):
    pass

class VideojuegoResponse(VideojuegoBase):
    id: int

class VideojuegoRatingUpdate(BaseConfigModel):
    puntuacion: float = Field(..., ge=0, le=10) # Validación: entre 0 y 10


# --- SCHEMAS DE ANIME LOGS (El registro personal del usuario) ---

class AnimeLogBase(BaseConfigModel):
    status: str = Field(default="Viendo", examples=["Viendo", "Completado", "En Espera", "Abandonado"])
    user_rating: Optional[float] = Field(default=None, ge=0, le=10)
    is_favorite: bool = False

class AnimeLogCreate(AnimeLogBase):
    anime_id: int = Field(..., description="El ID del anime que el usuario quiere agregar a su lista")

class AnimeLogResponse(AnimeLogBase):
    id: int
    anime: AnimeResponse  # Aquí anidamos el anime para saber qué estamos viendo
    user: UserSimpleResponse # Estos campos se veran de forma anidada en la response body del endpoint

class AnimeLogEstado(BaseConfigModel):
    status: str = Field(default="Viendo", examples=["Viendo", "Completado", "En Espera", "Abandonado"])

class AnimeLogPuntuacion(BaseConfigModel):
    user_rating: Optional[float] = Field(default=None, ge=0, le=10)

class AnimeLogFavorito(BaseConfigModel):
    is_favorite: bool

# --- SCHEMA DE VIDEOJUEGO LOGS (El registro personal del usuario) ---

class VideojuegoLogBase(BaseConfigModel):
    status: str = Field(default="Jugando", examples=["Jugando", "Completado", "En Espera", "Abandonado"])
    user_rating: Optional[float] = Field(default=None, ge=0, le=10)
    is_favorite: bool = False

class VideojuegoLogCreate(VideojuegoLogBase):
    game_id: int

class VideojuegoLogResponse(VideojuegoLogBase):
    id: int
    game: VideojuegoResponse
    user: UserSimpleResponse

class VideojuegoLogEstado(BaseConfigModel):
    status: str = Field(default="Viendo", examples=["Viendo", "Completado", "En Espera", "Abandonado"])

class VideojuegoLogPuntuacion(BaseConfigModel):
    user_rating: Optional[float] = Field(default=None, ge=0, le=10)

class VideojuegoLogFavorito(BaseConfigModel):
    is_favorite: bool