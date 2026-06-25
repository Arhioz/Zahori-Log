from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import os
import database, models, crud
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
from dotenv import load_dotenv
from fastapi import HTTPException, status, Depends

# Busca el archivo .env y carga sus valores en el sistema
load_dotenv()

# Asignar variables del entorno (.env)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# --- GESTIÓN DE CONTRASEÑAS ---

# A. Convertir texto plano a Hash (para cuando el usuario se registra)
def get_password_hash(password: str) -> str:
    """Encripta una contraseña usando bcrypt."""
    # Convertimos el string a bytes
    password_bytes = password.encode('utf-8')
    # Generamos la salt (Conjunto de caracteres aleatorios únicos que se generan automáticamente antes de encriptar una contraseña) y el hash
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    # Lo devolvemos como string para guardarlo en la base de datos de forma sencilla
    return hashed_password.decode('utf-8')

# B. Verificar si una clave coincide con el hash (para el Login)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con el hash guardado."""
    # Convertimos ambos a bytes para que bcrypt pueda compararlos
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

# --- GESTIÓN DE TOKENS JWT ---

# C. Crear el Token JWT (el pasaporte digital)
def create_access_token(data: dict) -> str:
    """Genera un token JWT firmado."""
    to_encode = data.copy()
    
    # Calculamos el tiempo de expiración
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Añadimos la expiración al paquete de datos
    to_encode.update({"exp": expire})
    
    # Firmamos el token con nuestra SECRET_KEY usando PyJWT
    token_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return token_jwt

# --- MIDDLEWARE DE AUTENTICACION ---

# 1. Esto le dice a FastAPI de dónde sacar el token (de la ruta /login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# 2. Función para obtener al usuario actual a partir del Token
async def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(database.get_db)
):
    credenciales_invalidas_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Intentamos decodificar el token con PyJWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credenciales_invalidas_exception
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        # Si el token está roto, corrupto o ya expiró
        raise credenciales_invalidas_exception
        
    # Buscamos al usuario en la DB usando crud.py
    usuario = await crud.obtener_usuario_por_username(db, username=username)
    if usuario is None:
        raise credenciales_invalidas_exception
    
    return usuario

# --- VERIFICACION DE ROLES ---

# Verifica si el rol del usuario es admin
def verificar_rol_admin(usuario_actual: models.User = Depends(obtener_usuario_actual)):
    if usuario_actual.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de Administrador para realizar esta acción"
        )
    return usuario_actual

# Verifica si el rol es de editor o admin
def verificar_rol_editor(usuario_actual: models.User = Depends(obtener_usuario_actual)):
    if usuario_actual.role not in ["admin", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de Editor para realizar esta acción"
        )
    return usuario_actual

# Verifica si el rol del usuario es user
def verificar_rol_user(usuario_actual: models.User = Depends(obtener_usuario_actual)):
    if usuario_actual.role not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    return usuario_actual