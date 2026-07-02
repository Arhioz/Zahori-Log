from slowapi import Limiter
from slowapi.util import get_remote_address

# Inicializamos el limitador usando la dirección IP del usuario para identificarlo
limiter = Limiter(key_func=get_remote_address)