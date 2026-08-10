# ui/views/vista_lotes.py
"""
Capa de Presentación: Dashboard de Gestión Vecinal.
Renderiza la cuadrícula espacial de la privada (Lotes y Casas). 
Implementa un motor de repintado suave para actualizar el estado 
financiero y la información de contacto en tiempo real.
"""

import customtkinter as ctk
from domain.models import Lote, Casa
from domain.business_rules import evaluar_estado_financiero
from ui.components.panel_detalle import PanelDetalleCasa

# Prevención de Importaciones Circulares
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.app_controller import SistemaRejaApp

class VistaLotes(ctk.CTkFrame):
    """
    Vista principal interactiva.
    Aloja el scroll de viviendas y gestiona la invocación y animación 
    del panel lateral de detalles para operaciones CRUD.
    """
    
    def __init__(self, master, app_controller: 'SistemaRejaApp'):
        """
        Inicializa la cuadrícula y prepara el panel lateral oculto.
        
        Args:
            master: Frame contenedor padre.
            app_controller (SistemaRejaApp): Orquestador principal para navegación y servicios.
        """
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.app_controller = app_controller
        self.db_session = self.app_controller.db_session
        
        # 1. Configuración de expansión de la cuadrícula principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 2. Contenedor dinámico (Scroll) para alojar las tarjetas
        self.scroll_lotes = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_lotes.grid(row=0, column=0, sticky="nsew")
        self.scroll_lotes.grid_columnconfigure(0, weight=1)
        
        self.lbl_titulo_scroll = ctk.CTkLabel(
            self.scroll_lotes, 
            text="Gestión Vecinal", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.lbl_titulo_scroll.grid(row=0, column=0, pady=(0, 20), sticky="w")

        # 3. Instanciación del panel lateral deslizante (Estado inicial: Oculto)
        self.panel_lateral = PanelDetalleCasa(self, comando_cerrar=self.ocultar_panel, app_controller=app_controller)
        self.panel_ancho = 350
        self.pos_x = self.panel_ancho 
        self.animacion_activa = False

        # 4. Detonador del motor de renderizado inicial
        self.cargar_tarjetas()

    def cargar_tarjetas(self):
        """
        Motor de renderizado.
        Limpia la cuadrícula actual, ejecuta una consulta relacional a SQLite 
        y dibuja las tarjetas actualizadas evaluando reglas de negocio en vivo.
        """
        # 1. Limpieza de memoria: Destrucción de widgets obsoletos
        for widget in self.scroll_lotes.winfo_children():
            if widget != self.lbl_titulo_scroll:
                widget.destroy()

        # 2. Función de inyección de eventos por tarjeta
        def bind_clic_tarjeta(widget, num_lote, num_casa):
            widget.bind("<Button-1>", lambda event, l=num_lote, c=num_casa: self.mostrar_panel(l, c))
            for child in widget.winfo_children():
                bind_clic_tarjeta(child, num_lote, num_casa)

        # 3. Consulta de datos topológicos (Lotes y Casas)
        lotes_reales = self.db_session.query(Lote).order_by(Lote.numero).all()

        # 4. Ciclo de dibujo espacial
        for idx, lote in enumerate(lotes_reales, start=1):
            
            frame_lote = ctk.CTkFrame(self.scroll_lotes)
            frame_lote.grid(row=idx, column=0, pady=10, sticky="ew")
            
            # Restricción 'uniform': Obliga a las columnas a mantener idéntica proporción geométrica
            frame_lote.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="columna_estandar")

            lbl_lote = ctk.CTkLabel(frame_lote, text=f"LOTE {lote.numero:02d}", font=ctk.CTkFont(weight="bold", size=16))
            lbl_lote.grid(row=0, column=0, columnspan=4, pady=10)

            for col_idx, casa in enumerate(lote.casas):
                
                # Restricción geométrica: Altura fija sin propagación de tamaño interno
                frame_casa = ctk.CTkFrame(frame_lote, fg_color=("gray75", "gray25"), cursor="hand2", height=145)
                frame_casa.grid(row=1, column=col_idx, padx=10, pady=10, sticky="nsew")
                frame_casa.pack_propagate(False) 
                
                # 5. Evaluación de Reglas de Negocio
                txt_estado, color_fondo, _ = evaluar_estado_financiero(casa)
                
                lbl_estado = ctk.CTkLabel(
                    frame_casa, text=txt_estado, fg_color=color_fondo, 
                    corner_radius=8, font=ctk.CTkFont(size=10, weight="bold"), padx=8, pady=2
                )
                lbl_estado.pack(anchor="e", padx=5, pady=(5, 0))
                
                # 6. Extracción y validación de entidades (Protección contra strings nulos)
                propietario = next((r for r in casa.residentes if r.es_propietario), None)
                
                if propietario:
                    nombre_txt = propietario.nombre_completo if propietario.nombre_completo and propietario.nombre_completo != "nan" else "Sin registro"
                    tel_txt = propietario.telefono if propietario.telefono and propietario.telefono != "nan" else "S/R"
                    mail_txt = propietario.email if propietario.email and propietario.email != "nan" else "S/R"
                else:
                    nombre_txt, tel_txt, mail_txt = "Sin registro", "S/R", "S/R"

                # 7. Truncamiento visual preventivo
                nombre_display = nombre_txt[:18] + "..." if len(nombre_txt) > 18 else nombre_txt
                mail_display = mail_txt[:20] + "..." if len(mail_txt) > 20 else mail_txt

                ctk.CTkLabel(frame_casa, text=f"Resp: {nombre_display}").pack(anchor="w", padx=10)
                ctk.CTkLabel(frame_casa, text=f"Cel: {tel_txt}").pack(anchor="w", padx=10)
                ctk.CTkLabel(frame_casa, text=f"Email: {mail_display}").pack(anchor="w", padx=10, pady=(0, 10))

                # 8. Anclaje de eventos
                bind_clic_tarjeta(frame_casa, lote.numero, casa.numero_interior)

    def mostrar_panel(self, num_lote: int, num_casa: str):
        """
        Dispara la carga de datos específicos y desencadena la animación de entrada.
        
        Args:
            num_lote (int): Identificador del lote seleccionado.
            num_casa (str): Identificador de la casa seleccionada.
        """
        self.panel_lateral.actualizar_datos(num_lote, num_casa)
        
        # Interrupción de seguridad si el usuario estaba editando un registro distinto
        if self.panel_lateral.modo_edicion:
            self.panel_lateral.toggle_edicion()
            
        if self.pos_x == self.panel_ancho and not self.animacion_activa:
            self.animacion_activa = True
            self.animar_entrada()

    def animar_entrada(self):
        """Calcula el offset y desliza el panel lateral hacia la izquierda de la pantalla."""
        if self.pos_x > 0:
            self.pos_x -= 25  
            self.panel_lateral.place(relx=1.0, x=self.pos_x, rely=0, relheight=1.0, anchor="ne")
            self.after(15, self.animar_entrada)
        else:
            self.pos_x = 0
            self.panel_lateral.place(relx=1.0, x=0, rely=0, relheight=1.0, anchor="ne")
            self.animacion_activa = False

    def animar_salida(self):
        """Calcula el offset y desliza el panel lateral hacia la derecha ocultándolo de la vista."""
        if self.pos_x < self.panel_ancho:
            self.pos_x += 25  
            self.panel_lateral.place(relx=1.0, x=self.pos_x, rely=0, relheight=1.0, anchor="ne")
            self.after(15, self.animar_salida)
        else:
            self.pos_x = self.panel_ancho
            self.panel_lateral.place_forget() 
            self.animacion_activa = False

    def ocultar_panel(self):
        """Función delegada para el botón de cierre. Gestiona la restauración de estados."""
        if self.pos_x == 0 and not self.animacion_activa:
            # Prevención de sobrescritura accidental de base de datos al cerrar el panel
            if self.panel_lateral.modo_edicion:
                self.panel_lateral.toggle_edicion()
            self.animacion_activa = True
            self.animar_salida()