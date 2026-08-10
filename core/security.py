# core/security.py
from cryptography.fernet import Fernet

# LLAVE ESTÁTICA DE DESARROLLO (Fase 1)
# Ahora el encriptador y el desencriptador usarán siempre esta misma cerradura.
SECRET_KEY = b'QBgEnBN6Rz5_ZYNN_sP3-Ax3OwLjWIZJjeVmLCJ__Gw='
_cipher_suite = Fernet(SECRET_KEY)

def encrypt_data(plain_text: str) -> str:
    """Aplica cifrado AES al texto plano."""
    if not plain_text:
        return plain_text
    return _cipher_suite.encrypt(plain_text.encode('utf-8')).decode('utf-8')

def decrypt_data(cipher_text: str) -> str:
    """Descifra el payload criptográfico hacia texto plano."""
    if not cipher_text:
        return cipher_text
    try:
        return _cipher_suite.decrypt(cipher_text.encode('utf-8')).decode('utf-8')
    except Exception:
        # Tolerancia a fallos en caso de datos pre-existentes sin cifrar
        return cipher_text