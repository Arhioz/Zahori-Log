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
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario único", examples=["User_01"])
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
    role: str = Field(..., examples=["user"])
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
    titulo: str = Field(..., min_length=1, max_length=150, examples=["Jujutsu Kaisen"])
    sinopsis: Optional[str] = Field(default=None)
    # gt=0 asegura que sea mayor a 0.
    episodios: Optional[int] = Field(default=None, gt=0, examples=[24])
    categoria: str = Field(..., examples=["Acción, Sobrenatural"])
    # La puntuación aquí sería el promedio global (opcional)
    puntuacion_global: Optional[float] = Field(default=None, ge=0, le=10)

class AnimeCreate(AnimeBase):
    pass

class AnimeResponse(AnimeBase):
    id: int

class AnimeRatingUpdate(BaseConfigModel): # <--- Esquema específico solo para actualizar la puntuacion
    puntuacion: float = Field(..., ge=0, le=10) # Validación: entre 0 y 10


# --- SCHEMA DE VIDEOJUEGOS (Catálogo Global) ---

class VideojuegoBase(BaseConfigModel):
    titulo: str = Field(..., min_length=1, max_length=150, examples=["Nier Automata"])
    sinopsis: Optional[str] = Field(default=None)
    categoria: str = Field(..., examples=["Hack n Slash"])
    puntuacion_global: Optional[float] = Field(default=None, ge=0, le=10)

class VideojuegoCreate(VideojuegoBase):
    pass

class VideojuegoResponse(VideojuegoBase):
    id: int

class VideojuegoRatingUpdate(BaseConfigModel):
    puntuacion: float = Field(..., ge=0, le=10) # Validación: entre 0 y 10


# --- SCHEMAS DE ANIME LOGS (El registro personal del usuario) ---

class AnimeLogBase(BaseConfigModel):
    visto: bool = Field(default=False)
    puntuacion_personal: Optional[float] = Field(default=None, ge=0, le=10)

class AnimeLogCreate(AnimeLogBase):
    anime_id: int = Field(..., description="El ID del anime que el usuario quiere agregar a su lista")

class AnimeLogResponse(AnimeLogBase):
    id: int
    anime: AnimeResponse  # Aquí anidamos el anime para saber qué estamos viendo
    user: UserSimpleResponse # ¡Aquí sí va el dueño! Porque este registro es suyo.


# --- SCHEMA DE VIDEOJUEGO LOGS (El registro personal del usuario) ---

class VideojuegoLogBase(BaseConfigModel):
    terminado: bool = Field(default=False)
    puntuacion_personal: Optional[float] = Field(default=None, ge=0, le=10)

class VideojuegoLogCreate(VideojuegoLogBase):
    videojuego_id: int

class VideojuegoLogResponse(VideojuegoLogBase):
    id: int
    videojuego: VideojuegoResponse
    user: UserSimpleResponse