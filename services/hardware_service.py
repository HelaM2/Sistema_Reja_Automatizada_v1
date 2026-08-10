# services/hardware_service.py
"""
Capa de Servicios: Gestión de Inventario IoT.
Maneja la lógica de negocio para la asignación, registro y validación 
de hardware físico (Chips, Controles) y lógico (Accesos Wi-Fi) 
vinculados a las viviendas de la privada.
"""

from sqlalchemy.orm import Session
from domain.models import Casa, Lote, Dispositivo

class HardwareService:
    """
    Controlador transaccional para operaciones CRUD sobre los dispositivos IoT.
    Aísla la lógica de base de datos de las vistas de la interfaz gráfica.
    """
    
    def __init__(self, db_session: Session):
        """
        Inicializa el servicio inyectando la sesión de base de datos.
        
        Args:
            db_session (Session): Sesión activa de SQLAlchemy.
        """
        self.db_session = db_session

    def registrar_hardware_especifico(self, num_lote: int, num_casa: str, chips: list, rfs: list, wifis: list) -> bool:
        """
        Registra múltiples dispositivos en la base de datos vinculándolos a una casa específica.
        
        Args:
            num_lote (int): Número de lote de la vivienda.
            num_casa (str): Número interior de la vivienda.
            chips (list): Lista de cadenas con los IDs de los chips peatonales.
            rfs (list): Lista de cadenas con los IDs de los controles vehiculares.
            wifis (list): Lista de cadenas con los correos electrónicos para acceso a la App.
            
        Returns:
            bool: True si la transacción fue exitosa.
            
        Raises:
            ValueError: Si la combinación de Lote-Casa no existe en la BD.
            RuntimeError: Si ocurre un fallo durante el commit en SQLite.
        """
        # 1. Búsqueda de la entidad Casa usando JOIN relacional
        casa = self.db_session.query(Casa).join(Lote).filter(
            Lote.numero == num_lote, 
            Casa.numero_interior == num_casa
        ).first()
        
        if not casa:
            raise ValueError(f"Error: El Hogar {num_lote}-{num_casa} no existe en la base de datos.")
        
        # 2. Insertar Chips Peatonales (RFID)
        for chip_id in chips:
            nuevo_rfid = Dispositivo(casa_id=casa.id, identificador_hardware=chip_id, tipo_dispositivo="RFID")
            self.db_session.add(nuevo_rfid)

        # 3. Insertar Controles Vehiculares (RF_VEHICULAR)
        for rf_id in rfs:
            nuevo_rf = Dispositivo(casa_id=casa.id, identificador_hardware=rf_id, tipo_dispositivo="RF_VEHICULAR")
            self.db_session.add(nuevo_rf)

        # 4. Insertar Accesos WiFi (WIFI_PERMIT)
        for correo in wifis:
            nuevo_wifi = Dispositivo(casa_id=casa.id, identificador_hardware=correo, tipo_dispositivo="WIFI_PERMIT")
            self.db_session.add(nuevo_wifi)

        # 5. Ejecución de la Transacción Atómica
        try:
            self.db_session.commit()
            return True
        except Exception as e:
            self.db_session.rollback()
            raise RuntimeError(f"Fallo transaccional al registrar el hardware: {e}")