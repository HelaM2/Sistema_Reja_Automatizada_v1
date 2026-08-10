# domain/models.py
"""
Capa de Dominio: Esquema Relacional de la Base de Datos.
Define las entidades del sistema utilizando SQLAlchemy ORM. Incluye lógica 
de encriptación transparente y las estructuras para gestión financiera, 
control de accesos IoT y bitácoras de mantenimiento de la reja.
"""

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator
from typing import List, Optional
from core.security import encrypt_data, decrypt_data
from datetime import date

class EncryptedString(TypeDecorator):
    """
    Decorador de tipos personalizado para SQLAlchemy.
    Intercepta las operaciones I/O de la base de datos para aplicar cifrado de 
    envoltura, protegiendo datos sensibles (teléfonos, correos) en reposo.
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Encripta el dato justo antes de guardarlo en SQLite."""
        return encrypt_data(value) if value else None

    def process_result_value(self, value, dialect):
        """Desencripta el dato automáticamente al leerlo de SQLite."""
        return decrypt_data(value) if value else None

class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos ORM."""
    pass

# =======================================================
# 1. TABLAS DE CONTABILIDAD Y FINANZAS
# =======================================================
class CatalogoPrecios(Base):
    """
    Diccionario de precios oficiales del sistema.
    Evita que los costos (ej. Mantenimiento, Chips) estén "hardcodeados" en el código.
    """
    __tablename__ = "catalogo_precios"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dispositivo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False)


class DetallePago(Base):
    """
    Desglose atómico de un pago (El ticket de compra).
    Permite saber exactamente cuántos chips o conceptos se cobraron en un solo recibo.
    """
    __tablename__ = "detalles_pago"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pago_id: Mapped[int] = mapped_column(ForeignKey("pagos.id"))
    
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relación bidireccional
    pago: Mapped["Pago"] = relationship("Pago", back_populates="detalles")


class Pago(Base):
    """
    Cabecera de la transacción financiera.
    Representa el comprobante global de un movimiento realizado por una vivienda.
    """
    __tablename__ = "pagos"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    casa_id: Mapped[int] = mapped_column(ForeignKey("casas.id"))
    
    concepto: Mapped[str] = mapped_column(String(255), nullable=False)
    monto_total: Mapped[float] = mapped_column(Float, nullable=False)
    monto_abonado: Mapped[float] = mapped_column(Float, nullable=False)
    mes_cubierto: Mapped[int] = mapped_column(Integer, nullable=False)
    anio_cubierto: Mapped[int] = mapped_column(Integer, nullable=False)
    ruta_comprobante: Mapped[Optional[str]] = mapped_column(String(500))
    estado: Mapped[str] = mapped_column(String(20), default="LIQUIDADO")
    notas_internas: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Relaciones
    casa: Mapped["Casa"] = relationship("Casa", back_populates="pagos")
    detalles: Mapped[List["DetallePago"]] = relationship("DetallePago", back_populates="pago", cascade="all, delete-orphan")


# =======================================================
# 2. TABLAS DE INFRAESTRUCTURA RESIDENCIAL
# =======================================================
class Lote(Base):
    """
    Agrupación geoespacial. Representa el bloque o terreno que puede 
    contener una o múltiples viviendas (Casas).
    """
    __tablename__ = "lotes"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numero: Mapped[int] = mapped_column(unique=True, nullable=False)
    tuya_virtual_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    
    casas: Mapped[List["Casa"]] = relationship("Casa", back_populates="lote", cascade="all, delete-orphan")


class Casa(Base):
    """
    Entidad central del sistema. Representa una vivienda individual y es el 
    nodo que conecta a residentes, pagos y dispositivos IoT.
    """
    __tablename__ = "casas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lotes.id"))
    numero_interior: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Estados de acceso
    acceso_base: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estado_tuya: Mapped[str] = mapped_column(String(20), default="Vigente", nullable=False)
    
    # Relaciones bidireccionales
    lote: Mapped["Lote"] = relationship("Lote", back_populates="casas")
    residentes: Mapped[List["Residente"]] = relationship("Residente", back_populates="casa")
    pagos: Mapped[List["Pago"]] = relationship("Pago", back_populates="casa")
    dispositivos: Mapped[List["Dispositivo"]] = relationship("Dispositivo", back_populates="casa")


class Residente(Base):
    """
    Representa a las personas físicas que habitan o administran una vivienda.
    Contiene la información de contacto encriptada para el envío de notificaciones.
    """
    __tablename__ = "residentes"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    casa_id: Mapped[int] = mapped_column(ForeignKey("casas.id"))
    
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(EncryptedString(255))
    email: Mapped[Optional[str]] = mapped_column(EncryptedString(255))
    es_propietario: Mapped[bool] = mapped_column(Boolean, default=True)
    tuya_uid: Mapped[Optional[str]] = mapped_column(String(100))
    
    casa: Mapped["Casa"] = relationship("Casa", back_populates="residentes")


class Dispositivo(Base):
    """
    Inventario IoT. Registra identificadores físicos (Chips RFID, Controles RF) 
    o lógicos (Correos de App) autorizados para abrir la reja.
    """
    __tablename__ = "dispositivos"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    casa_id: Mapped[int] = mapped_column(ForeignKey("casas.id"))
    
    identificador_hardware: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_dispositivo: Mapped[str] = mapped_column(String(50), nullable=False)
    
    casa: Mapped["Casa"] = relationship("Casa", back_populates="dispositivos")


# =======================================================
# 3. NUEVAS TABLAS: MÓDULO DE MANTENIMIENTO MECATRÓNICO
# =======================================================
class MantenimientoPreventivo(Base):
    """
    Bitácora de rutinas programadas. 
    Ideal para el checklist semestral de la reja (lubricación de pistones, 
    revisión de tarjetas electrónicas, ajustes mecánicos).
    """
    __tablename__ = "mantenimiento_preventivo"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha_ejecucion: Mapped[date] = mapped_column(Date, default=date.today)
    responsable: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Checklist mecánico/electrónico (Booleanos)
    chk_pistones_lubricados: Mapped[bool] = mapped_column(Boolean, default=False)
    chk_tarjeta_limpia: Mapped[bool] = mapped_column(Boolean, default=False)
    chk_sensores_alineados: Mapped[bool] = mapped_column(Boolean, default=False)
    chk_fuente_poder: Mapped[bool] = mapped_column(Boolean, default=False)
    
    observaciones: Mapped[Optional[str]] = mapped_column(String(500))


class MantenimientoCorrectivo(Base):
    """
    Bitácora de incidencias y reparaciones.
    Registra fallos esporádicos, choques en la reja o reemplazo de piezas dañadas.
    """
    __tablename__ = "mantenimiento_correctivo"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fecha_reporte: Mapped[date] = mapped_column(Date, default=date.today)
    
    falla_reportada: Mapped[str] = mapped_column(String(255), nullable=False)
    diagnostico_tecnico: Mapped[Optional[str]] = mapped_column(String(500))
    solucion_aplicada: Mapped[Optional[str]] = mapped_column(String(500))
    costo_reparacion: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Estado: 'Pendiente', 'En Progreso', 'Solucionado'
    estado: Mapped[str] = mapped_column(String(50), default="Pendiente")