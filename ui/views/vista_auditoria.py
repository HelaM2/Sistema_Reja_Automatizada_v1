# ui/views/vista_auditoria.py
"""
Capa de Presentación: Auditoría IoT y Conciliación de Accesos.
Vista de control central que compara el estado financiero real de las viviendas
contra los permisos activos en la nube de Tuya. Genera tareas para 
sincronización manual y dispara notificaciones masivas de bloqueo o reactivación.
"""

import customtkinter as ctk
from domain.models import Casa
from domain.business_rules import evaluar_estado_financiero
from ui.modals.lista_negra import VentanaListaNegra

class VistaAuditoria(ctk.CTkFrame):
    """
    Panel interactivo de auditoría.
    Muestra métricas generales de la cerrada y genera dinámicamente un checklist
    de acciones pendientes (bloqueos o reactivaciones) basadas en la morosidad.
    """
    
    def __init__(self, master, app_controller=None):
        """
        Inicializa la vista, sus componentes métricos y extrae la sesión 
        de base de datos desde el contenedor principal.
        
        Args:
            master: Frame contenedor padre.
            app_controller: Orquestador principal (opcional, para escalabilidad).
        """
        super().__init__(master, corner_radius=0, fg_color="transparent")
        
        # 1. Extracción segura de la sesión de base de datos
        try:
            self.db_session = master.winfo_toplevel().db_session
        except AttributeError:
            self.db_session = None

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(3, weight=1)

        # 2. Construcción de Cabecera
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        frame_header.grid_columnconfigure(0, weight=1)
        
        titulo = ctk.CTkLabel(frame_header, text="Centro de Auditoría IoT y Accesos", font=ctk.CTkFont(size=24, weight="bold"))
        titulo.pack(anchor="w")
        subtitulo = ctk.CTkLabel(frame_header, text="Gestor de Tareas Pendientes para Sincronización Manual en la App Tuya", text_color="gray60")
        subtitulo.pack(anchor="w")

        btn_lista_negra = ctk.CTkButton(
            frame_header, text="Ver Lista Negra & Enviar Correo", 
            fg_color="#8B0000", hover_color="#5C0000", 
            font=ctk.CTkFont(weight="bold"), command=self.abrir_lista_negra
        )
        btn_lista_negra.pack(anchor="e", pady=(0, 10))

        # 3. Dashboard de Resumen (Métricas)
        self.frame_dashboard = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_dashboard.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        self.frame_dashboard.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_dash_vigentes = self.crear_tarjeta_metrica(self.frame_dashboard, 0, "Casas Vigentes", "0", "#104A20")
        self.lbl_dash_restringidos = self.crear_tarjeta_metrica(self.frame_dashboard, 1, "Restringidas", "0", "#4A1010")
        self.lbl_dash_desinc = self.crear_tarjeta_metrica(self.frame_dashboard, 2, "⚠️ Desincronizados", "0", "#b8860b")

        # 4. Checklist Interactivo (Columnas de Acción)
        lbl_bloqueo = ctk.CTkLabel(self, text="🛑 Pendientes de Bloqueo en Tuya", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_bloqueo.grid(row=2, column=0, sticky="n", pady=(0, 10))
        
        self.scroll_bloqueos = ctk.CTkScrollableFrame(self, fg_color="gray15")
        self.scroll_bloqueos.grid(row=3, column=0, sticky="nsew", padx=(0, 10))

        lbl_reactiva = ctk.CTkLabel(self, text="🟢 Pendientes de Reactivación", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_reactiva.grid(row=2, column=1, sticky="n", pady=(0, 10))
        
        self.scroll_reactivaciones = ctk.CTkScrollableFrame(self, fg_color="gray15")
        self.scroll_reactivaciones.grid(row=3, column=1, sticky="nsew", padx=(10, 0))

        # 5. Ejecución del motor lógico inicial
        self.analizar_sincronizacion()

    def crear_tarjeta_metrica(self, padre, col: int, titulo: str, valor: str, color: str):
        """Genera dinámicamente un bloque visual para el dashboard superior."""
        tarjeta = ctk.CTkFrame(padre, fg_color=color, corner_radius=10)
        tarjeta.grid(row=0, column=col, padx=10, sticky="ew")
        
        ctk.CTkLabel(tarjeta, text=titulo, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        lbl_valor = ctk.CTkLabel(tarjeta, text=valor, font=ctk.CTkFont(size=28, weight="bold"))
        lbl_valor.pack(pady=(0, 15))
        return lbl_valor

    def analizar_sincronizacion(self):
        """
        Motor de Conciliación: Extrae todas las casas, calcula su estatus 
        financiero en tiempo real y lo compara contra el estado registrado 
        en la nube (Tuya). Genera tareas si detecta discrepancias.
        """
        # 1. Limpieza de contenedores visuales
        for widget in self.scroll_bloqueos.winfo_children(): widget.destroy()
        for widget in self.scroll_reactivaciones.winfo_children(): widget.destroy()

        if not self.db_session: return

        todas_las_casas = self.db_session.query(Casa).all()
        
        c_vigentes = 0
        c_restringidas = 0
        c_desincronizados = 0

        # 2. Barrido analítico de toda la privada
        for casa in todas_las_casas:
            estado_financiero, _, _ = evaluar_estado_financiero(casa)
            
            # Filtro estricto: Las casas sin servicio (N/A) no se auditan
            if estado_financiero == "🔳 N/A":
                continue 
            
            debe_tener_acceso = estado_financiero in ["🟢 Vigente", "⚠️ Parcial"]
            
            if debe_tener_acceso:
                c_vigentes += 1
            else:
                c_restringidas += 1

            # 3. Detección de Discrepancias Físico-Digitales
            tiene_acceso_tuya = (casa.estado_tuya == "Vigente")

            if not debe_tener_acceso and tiene_acceso_tuya:
                # Falso Positivo: Deudor con acceso activo -> Requiere Bloqueo
                c_desincronizados += 1
                self.crear_tarea_checklist(self.scroll_bloqueos, casa, "Bloquear", "#8B0000")
                
            elif debe_tener_acceso and not tiene_acceso_tuya:
                # Falso Negativo: Pagador con acceso bloqueado -> Requiere Reactivación
                c_desincronizados += 1
                self.crear_tarea_checklist(self.scroll_reactivaciones, casa, "Reactivar", "#104A20")

        # 4. Actualización del Dashboard
        self.lbl_dash_vigentes.configure(text=str(c_vigentes))
        self.lbl_dash_restringidos.configure(text=str(c_restringidas))
        self.lbl_dash_desinc.configure(text=str(c_desincronizados))
        
        # 5. Interfaz de Confirmación Visual
        if c_desincronizados == 0:
            ctk.CTkLabel(self.scroll_bloqueos, text="✅ Todo sincronizado", text_color="gray50").pack(pady=20)
            ctk.CTkLabel(self.scroll_reactivaciones, text="✅ Todo sincronizado", text_color="gray50").pack(pady=20)

    def crear_tarea_checklist(self, contenedor, casa: Casa, accion: str, color_btn: str):
        """
        Construye una tarjeta interactiva detallando los dispositivos físicos 
        y lógicos de una casa para facilitar su gestión manual en Tuya.
        """
        tarjeta = ctk.CTkFrame(contenedor, fg_color="gray20")
        tarjeta.pack(fill="x", pady=5, padx=5)
        
        texto_info = f"Hogar {casa.lote.numero}-{casa.numero_interior}"
        ctk.CTkLabel(tarjeta, text=texto_info, font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w", padx=10, pady=(10, 0))
        
        # Extracción del inventario IoT afectado
        correos = [d.identificador_hardware for d in casa.dispositivos if d.tipo_dispositivo == "WIFI_PERMIT"]
        rfids = [d.identificador_hardware.replace('RFID-', '') for d in casa.dispositivos if d.tipo_dispositivo == "RFID"]
        
        detalles = ""
        if correos: detalles += f"✉️ Correos: {', '.join(correos)}\n"
        if rfids: detalles += f"🏷️ Chips: {', '.join(rfids)}\n"
        if not detalles: detalles = "Sin hardware registrado."
        
        ctk.CTkLabel(tarjeta, text=detalles.strip(), text_color="gray70", justify="left", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=5)

        btn = ctk.CTkButton(
            tarjeta, text=f"Marcar como {accion} en Tuya", fg_color=color_btn, 
            command=lambda c=casa: self.marcar_sincronizado(c)
        )
        btn.pack(anchor="e", padx=10, pady=(0, 10))

    def marcar_sincronizado(self, casa: Casa):
        """
        Sella la conciliación actualizando el estado_tuya en la base de datos 
        y dispara automáticamente las notificaciones a los afectados.
        """
        # 1. Resolución de Estado Objetivo
        estado_financiero, _, _ = evaluar_estado_financiero(casa)
        debe_tener_acceso = estado_financiero in ["🟢 Vigente", "⚠️ Parcial"]
        
        nuevo_estado = "Vigente" if debe_tener_acceso else "Restringido"
        casa.estado_tuya = nuevo_estado
        
        self.db_session.commit()
        
        # 2. Enrutamiento de Notificaciones Multicanal
        try:
            propietario = next((r for r in casa.residentes if r.es_propietario), None)
            correo_titular = propietario.email if propietario else None
            hogar_str = f"{casa.lote.numero}-{casa.numero_interior}"
            
            # Consolidación de destinatarios únicos (Evita spam)
            destinatarios = []
            if correo_titular and correo_titular.strip() not in ["S/R", "nan", ""]:
                destinatarios.append(correo_titular.strip())
                
            correos_wifi = [d.identificador_hardware for d in casa.dispositivos if d.tipo_dispositivo == "WIFI_PERMIT"]
            for cw in correos_wifi:
                if cw and cw.strip() not in destinatarios:
                    destinatarios.append(cw.strip())
            
            # Despacho en lote
            cartero = self.winfo_toplevel().notification_service
            for dest in destinatarios:
                if nuevo_estado == "Restringido":
                    cartero.notificar_bloqueo(dest, hogar_str)
                else:
                    cartero.notificar_reactivacion(dest, hogar_str)
                    
        except Exception as e:
            print(f"Error al enviar notificación de auditoría: {e}")

        # 3. Refresco Visual
        self.analizar_sincronizacion()

    def abrir_lista_negra(self):
        """Instancia la ventana modal para la generación del reporte global de morosos."""
        VentanaListaNegra(self, self.db_session)