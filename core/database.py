# core/database.py
"""
Capa de Infraestructura: Conexión y Configuración de SQLite.
Se encarga de establecer la conexión con la base de datos física, manejando
dinámicamente las rutas absolutas para garantizar la compatibilidad tanto en el
entorno de desarrollo (VS Code) como en el empaquetado final (PyInstaller).
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from domain.models import Base

# =========================================================
# 1. RADAR INTELIGENTE PARA LA BASE DE DATOS (.exe vs VS Code)
# =========================================================
# Este bloque evalúa el entorno de ejecución para anclar la ruta del archivo .db
if getattr(sys, 'frozen', False):
    # Si el código se está ejecutando desde el main.exe compilado, 
    # la raíz es exactamente la misma carpeta donde el usuario dio doble clic.
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Si se está ejecutando en VS Code, la raíz es un nivel arriba de la carpeta 'core'
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. Configuración de la URL de conexión
DB_PATH = os.path.join(BASE_DIR, "residencial.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 3. Motor de SQLAlchemy
# 'check_same_thread': False es requerido estrictamente en SQLite cuando se 
# opera desde múltiples hilos gráficos (ej. CustomTkinter y ventanas modales).
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# 4. Fábrica de Sesiones
# Se inyectará esta sesión en los servicios (payment_service, hardware_service)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Compila la metadata del ORM y materializa las tablas relacionales 
    en el archivo físico 'residencial.db' si no existen previamente.
    Debe invocarse en la secuencia de arranque de la aplicación.
    """
    Base.metadata.create_all(bind=engine)
    print(f">>> [LOG] Base de datos enlazada correctamente en: {DB_PATH}")