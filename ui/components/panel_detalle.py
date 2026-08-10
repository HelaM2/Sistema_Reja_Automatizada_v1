# ui/components/panel_detalle.py
"""
Capa de Presentación: Componente Lateral de Detalles.
Proporciona una interfaz gráfica deslizable para inspeccionar y editar la 
información de una vivienda específica dentro de la cerrada. Actúa como un 
sub-controlador para derivar acciones hacia los módulos financieros y de hardware.
"""

import customtkinter as ctk
from domain.models import Casa, Lote, Residente
from domain.business_rules import evaluar_estado_financiero
from ui.modals.estado_cuenta import VentanaEstadoCuenta

# Prevención de Importaciones Circulares
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.app_controller import SistemaRejaApp

class PanelDetalleCasa(ctk.CTkFrame):
    """
    Panel interactivo para la gestión focalizada de una casa.
    Permite operaciones CRUD sobre los datos de contacto del titular y 
    muestra resúmenes del estado de cuenta y dispositivos IoT vinculados.
    """
    
    def __init__(self, master, comando_cerrar, app_controller: 'SistemaRejaApp'):
        """
        Inicializa el panel lateral y sus componentes visuales.
        
        Args:
            master: El frame contenedor padre.
            comando_cerrar (callable): Función a ejecutar para ocultar el panel con animación.
            app_controller (SistemaRejaApp): Instancia del orquestador principal para navegación.
        """
        super().__init__(master, width=350, corner_radius=0, fg_color="gray15")
        self.app_controller = app_controller
        self.db_session = self.app_controller.db_session
        
        self.current_lote = None
        self.current_casa = None
        self.modo_edicion = False
        
        self.grid_rowconfigure(6, weight=1) 
        
        # 1. Encabezado
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        frame_header.grid_columnconfigure(0, weight=1)
        
        self.lbl_titulo = ctk.CTkLabel(frame_header, text="Hogar X-X", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_titulo.grid(row=0, column=0, sticky="w")
        
        btn_cerrar = ctk.CTkButton(frame_header, text="X", width=30, fg_color="#8B0000", hover_color="#5C0000", command=comando_cerrar)
        btn_cerrar.grid(row=0, column=1, sticky="e")

        # 2. Información de Contacto
        self.frame_contacto = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_contacto.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        self.frame_contacto.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_contacto, text="Titular:").grid(row=0, column=0, sticky="w", padx=(0,5))
        ctk.CTkLabel(self.frame_contacto, text="Cel:").grid(row=1, column=0, sticky="w", padx=(0,5))
        ctk.CTkLabel(self.frame_contacto, text="Email:").grid(row=2, column=0, sticky="w", padx=(0,5))

        self.lbl_titular = ctk.CTkLabel(self.frame_contacto, text="", anchor="w")
        self.lbl_titular.grid(row=0, column=1, sticky="ew")
        self.lbl_tel = ctk.CTkLabel(self.frame_contacto, text="", anchor="w")
        self.lbl_tel.grid(row=1, column=1, sticky="ew")
        self.lbl_mail = ctk.CTkLabel(self.frame_contacto, text="", anchor="w")
        self.lbl_mail.grid(row=2, column=1, sticky="ew")
        
        self.ent_titular = None
        self.ent_tel = None
        self.ent_mail = None

        # 3. Resumen Financiero
        lbl_finanzas_tit = ctk.CTkLabel(self, text="Estado Financiero", font=ctk.CTkFont(weight="bold"), text_color="#1f6aa5")
        lbl_finanzas_tit.grid(row=2, column=0, sticky="w", padx=20, pady=(15, 5))
        
        self.frame_resumen_financiero = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_resumen_financiero.grid(row=3, column=0, sticky="ew", padx=20)
        
        self.lbl_estado_visual = ctk.CTkLabel(self.frame_resumen_financiero, text="", corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"), padx=10, pady=4)
        self.lbl_estado_visual.pack(anchor="w", pady=(0, 10))

        self.frame_mini_historial = ctk.CTkFrame(self.frame_resumen_financiero, fg_color="transparent")
        self.frame_mini_historial.pack(fill="x")

        self.btn_estado_cuenta = ctk.CTkButton(self.frame_resumen_financiero, text="Ver Estado de Cuenta", fg_color="gray30", hover_color="gray20", command=self.abrir_estado_cuenta)
        self.btn_estado_cuenta.pack(fill="x", pady=(10, 5))
        
        # 4. Inventario de Hardware
        lbl_disp_tit = ctk.CTkLabel(self, text="Inventario de Dispositivos", font=ctk.CTkFont(weight="bold"), text_color="#1f6aa5")
        lbl_disp_tit.grid(row=4, column=0, sticky="w", padx=20, pady=(15, 0))
        
        self.lbl_dispositivos = ctk.CTkLabel(self, text="Cargando...", justify="left")
        self.lbl_dispositivos.grid(row=5, column=0, sticky="nw", padx=20, pady=5)
        
        # 5. Botones de Acción y Enrutamiento
        self.btn_editar = ctk.CTkButton(self, text="Editar Información", fg_color="#b8860b", hover_color="#8b6508", command=self.toggle_edicion) 
        self.btn_editar.grid(row=7, column=0, pady=(10, 5), padx=20, sticky="ew")

        btn_pago = ctk.CTkButton(self, text="Registrar Pago", fg_color="#104A20", hover_color="#006400", command=self.ir_a_pagos)
        btn_pago.grid(row=8, column=0, pady=5, padx=20, sticky="ew")
        
        btn_editar_disp = ctk.CTkButton(self, text="Editar Dispositivos", fg_color="#1f6aa5", hover_color="#144870", command=self.ir_a_dispositivos)
        btn_editar_disp.grid(row=9, column=0, pady=(5, 20), padx=20, sticky="ew")

    def toggle_edicion(self):
        """
        Alterna la interfaz de contacto entre modo de lectura (Labels) y 
        modo de edición (Entries). Gestiona la actualización atómica en SQLite.
        """
        if not self.modo_edicion:
            # 1. Habilitar Modo Edición
            self.modo_edicion = True
            self.btn_editar.configure(text="Guardar Información", fg_color="#104A20", hover_color="#006400")
            
            t_titular = self.lbl_titular.cget("text")
            t_titular = "" if t_titular in ["Sin registro", "nan"] else t_titular
            
            t_tel = self.lbl_tel.cget("text")
            t_tel = "" if t_tel in ["S/R", "nan"] else t_tel
            
            t_mail = self.lbl_mail.cget("text")
            t_mail = "" if t_mail in ["S/R", "nan"] else t_mail

            self.lbl_titular.grid_remove()
            self.lbl_tel.grid_remove()
            self.lbl_mail.grid_remove()

            self.ent_titular = ctk.CTkEntry(self.frame_contacto, height=25)
            self.ent_titular.insert(0, t_titular)
            self.ent_titular.grid(row=0, column=1, sticky="ew", pady=2)

            self.ent_tel = ctk.CTkEntry(self.frame_contacto, height=25)
            self.ent_tel.insert(0, t_tel)
            self.ent_tel.grid(row=1, column=1, sticky="ew", pady=2)

            self.ent_mail = ctk.CTkEntry(self.frame_contacto, height=25)
            self.ent_mail.insert(0, t_mail)
            self.ent_mail.grid(row=2, column=1, sticky="ew", pady=2)
            
        else:
            # 2. Guardar Datos y Deshabilitar Edición
            nuevo_titular = self.ent_titular.get().strip()
            nuevo_tel = self.ent_tel.get().strip()
            nuevo_mail = self.ent_mail.get().strip()
            
            casa = self.db_session.query(Casa).join(Lote).filter(
                Lote.numero == self.current_lote, Casa.numero_interior == self.current_casa
            ).first()

            propietario = next((r for r in casa.residentes if r.es_propietario), None)
            
            if propietario:
                propietario.nombre_completo = nuevo_titular if nuevo_titular else "Sin registro"
                propietario.telefono = nuevo_tel if nuevo_tel else None
                propietario.email = nuevo_mail if nuevo_mail else None
            else:
                nuevo_prop = Residente(
                    casa_id=casa.id, 
                    nombre_completo=nuevo_titular if nuevo_titular else "Sin registro", 
                    telefono=nuevo_tel if nuevo_tel else None, 
                    email=nuevo_mail if nuevo_mail else None, 
                    es_propietario=True
                )
                self.db_session.add(nuevo_prop)
                
            self.db_session.commit()
            
            self.ent_titular.destroy()
            self.ent_tel.destroy()
            self.ent_mail.destroy()

            # 3. Refresco Visual Asíncrono
            self.actualizar_datos(self.current_lote, self.current_casa)
            self.master.cargar_tarjetas() 
            
            self.modo_edicion = False
            self.btn_editar.configure(text="Editar Información", fg_color="#b8860b", hover_color="#8b6508")
        
    def actualizar_datos(self, num_lote: int, num_casa: str):
        """
        Consulta la base de datos para la vivienda objetivo y formatea la 
        información para inyectarla en los componentes visuales del panel.
        
        Args:
            num_lote (int): Identificador del lote de la vivienda.
            num_casa (str): Identificador interior de la vivienda.
        """
        self.current_lote = int(num_lote)
        self.current_casa = str(num_casa)
        self.lbl_titulo.configure(text=f"Hogar {self.current_lote}-{self.current_casa}")
        
        # 1. Consulta Principal
        casa = self.db_session.query(Casa).join(Lote).filter(
            Lote.numero == self.current_lote,
            Casa.numero_interior == self.current_casa
        ).first()

        if not casa:
            return

        # 2. Renderizado de Datos de Contacto
        propietario = next((r for r in casa.residentes if r.es_propietario), None)
        
        if propietario:
            nom = propietario.nombre_completo if propietario.nombre_completo and propietario.nombre_completo != "nan" else "Sin registro"
            tel = propietario.telefono if propietario.telefono and propietario.telefono != "nan" else "S/R"
            mail = propietario.email if propietario.email and propietario.email != "nan" else "S/R"
        else:
            nom, tel, mail = "Sin registro", "S/R", "S/R"
            
        self.lbl_titular.configure(text=nom)
        self.lbl_titular.grid()
        self.lbl_tel.configure(text=tel)
        self.lbl_tel.grid()
        self.lbl_mail.configure(text=mail)
        self.lbl_mail.grid()
        
        # 3. Renderizado Financiero y Semáforo Visual
        txt_estado, color_fondo, deuda_total = evaluar_estado_financiero(casa)
        
        if txt_estado == "🔳 N/A":
            self.lbl_estado_visual.configure(text="🔳 N/A (Sin Servicio)", fg_color=color_fondo)
            self.btn_estado_cuenta.configure(state="disabled")
        else:
            if deuda_total > 0:
                self.lbl_estado_visual.configure(text=f"{txt_estado} (Deuda: ${deuda_total:,.2f})", fg_color=color_fondo)
            else:
                self.lbl_estado_visual.configure(text=txt_estado, fg_color=color_fondo)
                
            self.btn_estado_cuenta.configure(state="normal" if casa.pagos else "disabled")

        # 4. Renderizado de Historial de Transacciones (Últimas 3)
        for widget in self.frame_mini_historial.winfo_children():
            widget.destroy()

        if casa.pagos:
            ultimos_pagos = sorted(casa.pagos, key=lambda x: x.id, reverse=True)[:3]
            
            for p in ultimos_pagos:
                liquidado = p.monto_abonado >= p.monto_total
                icono = "☑" if liquidado else "⚠"
                color_texto = "white" if liquidado else "#b8860b"
                
                txt_concepto = p.concepto
                if len(txt_concepto) > 22: 
                    txt_concepto = txt_concepto[:19] + "..." 
                
                texto_fila = f"{p.mes_cubierto:02d}/{p.anio_cubierto} - {txt_concepto}"
                
                lbl_fila = ctk.CTkLabel(self.frame_mini_historial, text=f"{icono} {texto_fila}", text_color=color_texto, font=ctk.CTkFont(size=11))
                lbl_fila.pack(anchor="w", padx=15, pady=2)
        else:
            ctk.CTkLabel(self.frame_mini_historial, text="No hay transacciones previas.", text_color="gray50", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=2)
        
        # 5. Renderizado de Inventario IoT
        rfid = [d for d in casa.dispositivos if d.tipo_dispositivo == "RFID"]
        rf = [d for d in casa.dispositivos if d.tipo_dispositivo == "RF_VEHICULAR"]
        wifi = [d for d in casa.dispositivos if d.tipo_dispositivo == "WIFI_PERMIT"]

        estado_base = "Habilitado" if casa.acceso_base else "Deshabilitado"
        disp_txt = f"• Acceso Base: {estado_base}\n"

        disp_txt += f"• Chips Peatonales ({len(rfid)}):"
        if rfid:
            ids_rfid = [d.identificador_hardware.replace('RFID-', '') for d in rfid]
            disp_txt += f"\n  - {', '.join(ids_rfid)}\n"
        else:
            disp_txt += " Ninguno\n"

        disp_txt += f"• Controles Vehiculares ({len(rf)}):"
        if rf:
            ids_rf = [d.identificador_hardware.replace('RF-', '') for d in rf]
            disp_txt += f"\n  - {', '.join(ids_rf)}\n"
        else:
            disp_txt += " Ninguno\n"

        disp_txt += f"• Accesos WiFi ({len(wifi)}):"
        if wifi:
            for w in wifi:
                disp_txt += f"\n  - {w.identificador_hardware}"
        else:
            disp_txt += " Ninguno"

        self.lbl_dispositivos.configure(text=disp_txt)
        
    def ir_a_pagos(self):
        """Redirige al módulo de Finanzas inyectando el contexto de la casa actual."""
        self.app_controller.cargar_vista("finanzas", lote_precargado=self.current_lote, casa_precargada=self.current_casa)
        
    def ir_a_dispositivos(self):
        """Redirige al módulo de Dispositivos en modo 'Baja', inyectando el contexto actual."""
        self.app_controller.cargar_vista(
            "dispositivos", 
            lote_precargado=self.current_lote, 
            casa_precargada=self.current_casa,
            modo_inicial="Baja de Dispositivos"
        )       
    
    def abrir_estado_cuenta(self):
        """Instancia la ventana modal con el historial transaccional completo."""
        VentanaEstadoCuenta(self, self.current_lote, self.current_casa, self.db_session)