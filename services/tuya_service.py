# services/tuya_service.py
"""
Capa de Servicios: Integración Telemática con Tuya Smart Life.
Gestiona la comunicación con la API de Tuya Cloud Platform para otorgar 
y revocar permisos de acceso digital a los residentes directamente en 
los dispositivos IoT de la reja automatizada.
"""

import tinytuya
from abc import ABC, abstractmethod
import logging

class IIoTIntegrationService(ABC):
    """
    Interfaz abstracta (Contrato) para los servicios de integración IoT.
    Define los métodos obligatorios que cualquier proveedor de hardware 
    en la nube debe implementar para operar la reja de manera estándar.
    """
    
    @abstractmethod
    def grant_resident_access(self, tuya_virtual_id: str, tuya_user_id: str) -> bool:
        pass

    @abstractmethod
    def revoke_resident_access(self, tuya_virtual_id: str, tuya_user_id: str) -> bool:
        pass


class TuyaCloudService(IIoTIntegrationService):
    """
    Controlador concreto para la plataforma Tuya Cloud.
    Gestiona la autenticación y el envío de peticiones REST (POST, DELETE)
    para manipular los privilegios de los usuarios en la nube.
    """
    
    def __init__(self, region: str, api_key: str, api_secret: str):
        """
        Inicializa la conexión telemática con Tuya Cloud.
        
        Args:
            region (str): Región del servidor de Tuya (ej. 'us', 'eu').
            api_key (str): Credencial de acceso público proporcionada por Tuya.
            api_secret (str): Llave criptográfica secreta de la API.
            
        Raises:
            RuntimeError: Si las credenciales son inválidas o la conexión falla.
        """
        try:
            self.cloud = tinytuya.Cloud(
                apiRegion=region, 
                apiKey=api_key, 
                apiSecret=api_secret
            )
            logging.info("Enlace telemático con Tuya Cloud Platform establecido exitosamente.")
        except Exception as e:
            logging.error(f"Fallo crítico al instanciar Tuya Cloud: {e}")
            raise RuntimeError(f"Fallo de instanciación Tuya Cloud: {e}")

    def grant_resident_access(self, tuya_virtual_id: str, tuya_user_id: str) -> bool:
        """
        Inyecta una petición POST hacia la API de Tuya para otorgar permisos 
        de la aplicación Smart Life a un usuario específico en un lote virtual.
        
        Args:
            tuya_virtual_id (str): Identificador del dispositivo/lote en la nube.
            tuya_user_id (str): Identificador único (UID) del residente en Tuya.
            
        Returns:
            bool: True si Tuya confirmó la concesión, False en caso contrario.
        """
        # 1. Construcción del endpoint oficial y payload
        uri = f"/v1.0/devices/{tuya_virtual_id}/user" 
        payload = {"uid": tuya_user_id}
        logging.info(f"Despachando concesión hacia URI: {uri} para el usuario {tuya_user_id}")
        
        # 2. Despacho de la petición REST
        try:
            response = self.cloud.cloudrequest(uri, action="POST", post=payload)
            
            # 3. Validación de la respuesta del servidor
            if response and response.get('success'):
                logging.info(f"✅ Privilegios OTORGADOS para el usuario {tuya_user_id} en el Lote virtual {tuya_virtual_id}.")
                return True
            else:
                logging.error(f"❌ Rechazo en la nube de Tuya al otorgar: {response}")
                return False
        except Exception as e:
            logging.error(f"Error de red al intentar otorgar acceso: {e}")
            return False

    def revoke_resident_access(self, tuya_virtual_id: str, tuya_user_id: str) -> bool:
        """
        Inyecta una petición DELETE hacia la API de Tuya para purgar los 
        permisos de Smart Life de un residente.
        
        Args:
            tuya_virtual_id (str): Identificador del dispositivo/lote en la nube.
            tuya_user_id (str): Identificador único (UID) del residente en Tuya.
            
        Returns:
            bool: True si Tuya confirmó la revocación, False en caso contrario.
        """
        # 1. Construcción del endpoint de eliminación (incluye /share/)
        uri = f"/v1.0/devices/{tuya_virtual_id}/share/users/{tuya_user_id}"
        logging.info(f"Despachando revocación hacia URI: {uri}")
        
        # 2. Despacho de la petición REST
        try:
            response = self.cloud.cloudrequest(uri, action="DELETE")
            
            # 3. Validación de la respuesta del servidor
            if response and response.get('success'):
                logging.info(f"✅ Privilegios REVOCADOS para el usuario {tuya_user_id} del Lote virtual {tuya_virtual_id}.")
                return True
            else:
                logging.error(f"❌ Rechazo en la nube de Tuya al revocar: {response}")
                return False
        except Exception as e:
            logging.error(f"Error de red al intentar revocar acceso: {e}")
            return False