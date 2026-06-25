# 1. La base: Usamos Python 3.12 versión "slim" (ligera)
FROM python:3.12-slim

# 2. El directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Instalacion de dependencias del sistema operativo (Compiladores y drivers para Postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiamos e instalamos el archivo de librerías para instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos todo el resto de nuestro código a la carpeta /app del contenedor
COPY . .

# 6. El comando para arrancar la API cuando el contenedor inicie
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]