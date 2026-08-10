# ui/app_controller.py
"""
Capa de Presentación: Orquestador Principal y Enrutador (App Controller).
Define la ventana base de la aplicación, construye el menú de navegación 
lateral (Sidebar), inicializa los servicios del backend y gestiona el 
ciclo de vida y enrutamiento dinámico de las vistas principales.
"""

import customtkinter as ctk

# Importación de Servicios de Backend y Base de Datos
from core.database import SessionLocal
from services.payment_service import PaymentService
from services.hardware_service import HardwareService
from services.notification_service import NotificationService

# Importación de las Vistas a Enrutar
from ui.views.vista_lotes import VistaLotes
from ui.views.vista_dispositivos import VistaDispositivos
from ui.views.vista_finanzas import VistaFinanzas
from ui.views.vista_auditoria import VistaAuditoria

# Configuraciones Globales de UI
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SistemaRejaApp(ctk.CTk):
    """
    Controlador Frontal de la interfaz gráfica.
    Hereda de CTk para crear la ventana principal y actúa como el inyector de
    dependencias central para pasar los servicios a cada vista hija.
    """
    
    def __init__(self):
        """
        Inicializa la ventana principal, establece el sistema de grillas, 
        construye el menú lateral e instancia la conexión a la base de datos.
        """
        super().__init__()

        # 1. Configuración de la Ventana Principal
        self.title("Sistema de Reja Automatizada")
        self.geometry("1100x700")
        self.minsize(1100, 700)

        # 2. Layout (Grid System) Principal: 1 Fila, 2 Columnas
        # Columna 0: Sidebar (Fija) | Columna 1: Contenido Dinámico (Expansible)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 3. Construcción del Sidebar (Menú Lateral)
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Empuja elementos hacia arriba

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Reja Admin\nFase 1", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # 4. Definición de Botones de Navegación
        self.btn_lotes = ctk.CTkButton(self.sidebar_frame, text="Gestión Vecinal", command=lambda: self.cargar_vista("lotes"))
        self.btn_lotes.grid(row=1, column=0, padx=20, pady=10)

        self.btn_dispositivos = ctk.CTkButton(self.sidebar_frame, text="Dispositivos", command=lambda: self.cargar_vista("dispositivos"))
        self.btn_dispositivos.grid(row=2, column=0, padx=20, pady=10)

        self.btn_finanzas = ctk.CTkButton(self.sidebar_frame, text="Finanzas", command=lambda: self.cargar_vista("finanzas"))
        self.btn_finanzas.grid(row=3, column=0, padx=20, pady=10)

        self.btn_auditoria = ctk.CTkButton(
            self.sidebar_frame, 
            text="Auditoría IoT", 
            command=lambda: self.cargar_vista("auditoria"),
            fg_color="#8B0000", 
            hover_color="#5C0000"
        )
        self.btn_auditoria.grid(row=4, column=0, padx=20, pady=10)

        # 5. Configuración del Área de Contenido Dinámico
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        # Puntero para almacenar el frame actual renderizado
        self.vista_actual = None
        
        # 6. Inicialización de Sesión BD y Servicios Backend (Inyección de Dependencias)
        self.db_session = SessionLocal()
        self.payment_service = PaymentService(self.db_session)
        self.hardware_service = HardwareService(self.db_session)
        self.notification_service = NotificationService()
        
        # 7. Arranque Inicial
        self.cargar_vista("lotes")

    def limpiar_contenido(self):
        """
        Destruye de forma segura el widget de la vista actual en pantalla 
        para liberar memoria gráfica antes de inyectar una nueva vista.
        """
        if self.vista_actual is not None:
            self.vista_actual.destroy()

    def cargar_vista(self, nombre_vista: str, **kwargs):
        """
        Enrutador visual que construye y posiciona la vista solicitada, inyectando
        los servicios necesarios y aceptando parámetros dinámicos (kwargs) para pre-cargar datos.
        
        Args:
            nombre_vista (str): Identificador de la vista a cargar ('lotes', 'dispositivos', etc.).
            **kwargs: Parámetros opcionales enviados a las vistas (ej. lote_precargado).
        """
        # 1. Purga de la vista anterior
        self.limpiar_contenido()
        
        # 2. Inyección de dependencias y renderizado condicional
        if nombre_vista == "lotes":
            # Se pasa 'self' como app_controller para permitir la navegación interactiva
            self.vista_actual = VistaLotes(self.main_content_frame, app_controller=self)
            
        elif nombre_vista == "dispositivos":
            self.vista_actual = VistaDispositivos(self.main_content_frame, self.hardware_service, **kwargs)
            
        elif nombre_vista == "finanzas":
            self.vista_actual = VistaFinanzas(self.main_content_frame, self.payment_service, **kwargs)
            
        elif nombre_vista == "auditoria":
            self.vista_actual = VistaAuditoria(self.main_content_frame)
            
        # 3. Anclaje de la nueva vista al Grid del área principal
        if self.vista_actual:
            self.vista_actual.grid(row=0, column=0, sticky="nsew")