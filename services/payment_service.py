# services/payment_service.py
"""
Capa de Servicios: Procesamiento Financiero y Comprobantes.
Maneja la lógica de negocio para el registro de pagos, liquidación de adeudos,
almacenamiento de comprobantes en disco y el desglose atómico de cada transacción.
"""

import os
from datetime import datetime
from PIL import Image
from sqlalchemy.orm import Session
from domain.models import Casa, Pago, Lote, DetallePago

class PaymentService:
    """
    Controlador transaccional para operaciones financieras.
    Aísla la lógica de base de datos y procesamiento de archivos de la interfaz gráfica.
    """
    
    def __init__(self, db_session: Session):
        """
        Inicializa el servicio inyectando la sesión de base de datos y configurando
        el directorio raíz para los comprobantes.
        
        Args:
            db_session (Session): Sesión activa de SQLAlchemy.
        """
        self.db_session = db_session
        self.base_dir = "comprobantes"

    def register_payment(self, numero_lote: int, numero_casa: str, concepto: str, 
                         monto_total: float, monto_recibido: float, mes: int, anio: int, 
                         original_image_path: str, detalles_compra: list = None, 
                         notas_internas: str = None) -> Pago:
        """
        Orquesta el flujo transaccional, guarda el desglose exacto de la compra
        y procesa el comprobante de pago en el almacenamiento local.
        
        Args:
            numero_lote (int): Número del lote de la vivienda.
            numero_casa (str): Número interior de la vivienda.
            concepto (str): Categoría del pago (ej. 'Mantenimiento Base', 'Venta de Hardware').
            monto_total (float): Costo total calculado de la transacción.
            monto_recibido (float): Cantidad real pagada por el residente.
            mes (int): Mes que cubre el pago.
            anio (int): Año que cubre el pago.
            original_image_path (str): Ruta temporal de la imagen del comprobante (puede ser None).
            detalles_compra (list, optional): Lista de diccionarios con el desglose de artículos.
            notas_internas (str, optional): Anotaciones o detalles extra sobre el pago.
            
        Returns:
            Pago: La instancia del modelo Pago recién creada y guardada.
            
        Raises:
            ValueError: Si la combinación Lote-Casa no existe en la BD.
            IOError: Si hay un error al procesar o guardar la imagen del comprobante.
            RuntimeError: Si falla la transacción en SQLite.
        """
        # 1. Búsqueda y Validación de la Entidad Casa
        casa = self.db_session.query(Casa).join(Lote).filter(
            Lote.numero == numero_lote,
            Casa.numero_interior == numero_casa
        ).first()

        if not casa:
            raise ValueError("Infracción de Integridad Referencial: La vivienda especificada no existe.")
            
        # 2. Determinación del Estado Financiero
        estado_pago = "LIQUIDADO" if monto_recibido >= monto_total else "SALDO PENDIENTE"

        # 3. Procesamiento y Almacenamiento del Comprobante (I/O)
        relative_path = None
        
        if original_image_path:
            timestamp = datetime.now()
            year_folder = timestamp.strftime("%Y")
            month_folder = f"{mes:02d}"
            
            target_dir = os.path.join(self.base_dir, year_folder, month_folder)
            os.makedirs(target_dir, exist_ok=True)
            
            file_ext = ".jpg"
            time_str = timestamp.strftime("%Y%m%d%H%M%S")
            filename = f"LOTE{casa.lote_id}_CASA{casa.numero_interior}_{month_folder}-{year_folder}_{time_str}{file_ext}"
            relative_path = os.path.join(target_dir, filename).replace("\\", "/")

            try:
                with Image.open(original_image_path) as img:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(relative_path, format="JPEG", quality=75)
            except Exception as e:
                raise IOError(f"Falla crítica en procesamiento de imagen: {e}")

        # 4. Inserción de la Transacción en la Base de Datos
        try:
            nuevo_pago = Pago(
                casa_id=casa.id,
                concepto=concepto,
                monto_total=monto_total,
                monto_abonado=monto_recibido,
                mes_cubierto=mes,
                anio_cubierto=anio,
                ruta_comprobante=relative_path,
                estado=estado_pago,
                notas_internas=notas_internas
            )
            self.db_session.add(nuevo_pago)
            self.db_session.flush()

            # 5. Desglose de Artículos Individuales (DetallePago)
            if detalles_compra:
                for item in detalles_compra:
                    # Se filtran los renglones en ceros preventivamente
                    if item["cant"] > 0: 
                        detalle = DetallePago(
                            pago_id=nuevo_pago.id,
                            cantidad=item["cant"],
                            descripcion=item["desc"],
                            precio_unitario=item["pu"],
                            subtotal=item["sub"]
                        )
                        self.db_session.add(detalle)

            # 6. Sello de la Transacción Atómica
            self.db_session.commit()
            return nuevo_pago
            
        except Exception as e:
            self.db_session.rollback()
            # Reversión de I/O: Borra la imagen si falló la inyección en la base de datos
            if relative_path and os.path.exists(relative_path):
                os.remove(relative_path)
            raise RuntimeError(f"El motor SQLite reportó un fallo: {e}")