import os
import sys

# =========================================================
# FASE 2: ANCLAJE DE DIRECTORIO PARA PYINSTALLER (.exe)
# =========================================================
# Este bloque fuerza a que el programa siempre busque la base de datos 
# y los comprobantes justo al lado del archivo main.exe.
if getattr(sys, 'frozen', False):
    directorio_raiz = os.path.dirname(sys.executable)
    os.chdir(directorio_raiz)
else:
    directorio_raiz = os.path.dirname(os.path.abspath(__file__))
    os.chdir(directorio_raiz)

# =========================================================
# FASE 3: IMPORTACIONES INTERNAS (Post-Anclaje)
# =========================================================
from core.database import init_db
from ui.app_controller import SistemaRejaApp

# =========================================================
# FASE 4 Y 5: BOOTSTRAPPER Y ENERGIZACIÓN
# =========================================================
def application_entrypoint():
    """
    Controlador de Arranque. Asegura que la base de datos SQLite
    esté lista antes de levantar el mainloop de CustomTkinter.
    """
    try:
        print(">>> [SISTEMA] Conectando a SQLite y verificando integridad...")
        init_db()
    except Exception as hardware_err:
        print(f">>> [ERROR CRÍTICO] Colapso durante el anclaje a la base de datos SQLite: {hardware_err}")
        return  # Aborta el inicio si no hay base de datos
    
    print(">>> [SISTEMA] Energizando Interfaz Gráfica (UI)...")
    app = SistemaRejaApp()
    app.mainloop()

if __name__ == "__main__":
    application_entrypoint()