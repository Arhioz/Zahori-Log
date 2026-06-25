from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import os

# Busca el archivo .env y carga sus valores en el sistema
load_dotenv()

# 1. Obtenemos la URL de Postgres desde el .env
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Motor asíncrono
engine = create_async_engine(DATABASE_URL)

# 3. Creador de sesiones asíncronas
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False) # Especificamos que las sesiones sean asíncronas

Base = declarative_base()



async def get_db():
    async with SessionLocal() as session: # 'async with' asegura que la sesión se cierre sola al terminar la peticion.
        yield session