# ui/views/vista_dispositivos.py
"""
Capa de Presentación: Gestor de Dispositivos e Inventario IoT.
Interfaz dinámica para la validación, alta, edición y baja de identificadores 
de hardware (Chips Peatonales, Controles Vehiculares) y accesos digitales (Wi-Fi).
Se integra con los servicios financieros y de notificaciones.
"""

import customtkinter as ctk
from tkinter import messagebox
from domain.models import Casa, Lote, Dispositivo, CatalogoPrecios

class VistaDispositivos(ctk.CTkScrollableFrame):
    """
    Vista principal para la administración del hardware residencial.
    Construye formularios dinámicos que se adaptan según el modo de operación
    (Alta o Baja) y el número de dispositivos solicitados.
    """
    
    def __init__(self, master, hardware_service, lote_precargado=None, casa_precargada=None, modo_inicial="Alta de Dispositivos"):
        """
        Inicializa la vista y sus contenedores principales.
        
        Args:
            master: Frame contenedor padre.
            hardware_service: Servicio inyectado para la gestión de dispositivos.
            lote_precargado (int, optional): Lote a inyectar automáticamente en el buscador.
            casa_precargada (str, optional): Casa a inyectar automáticamente en el buscador.
            modo_inicial (str, optional): Define si la vista arranca en "Alta" o "Baja".
        """
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.hardware_service = hardware_service
        self.grid_columnconfigure(0, weight=1)
        
        titulo = ctk.CTkLabel(self, text="Validación y Edición de Hardware", font=ctk.CTkFont(size=24, weight="bold"))
        titulo.grid(row=0, column=0, pady=(0, 20))

        # 1. Contenedor Superior (Buscador y Selector de Operación)
        self.contenedor_superior = ctk.CTkFrame(self, fg_color="transparent")
        self.contenedor_superior.grid(row=1, column=0, sticky="n")
        self.contenedor_superior.grid_columnconfigure(0, weight=1)
        self.contenedor_superior.grid_columnconfigure(1, weight=1)

        lbl_hogar = ctk.CTkLabel(self.contenedor_superior, text="Hogar (LT-C):", font=ctk.CTkFont(size=14))
        lbl_hogar.grid(row=0, column=0, pady=10, padx=20, sticky="e")
        
        self.ent_hogar = ctk.CTkEntry(self.contenedor_superior, placeholder_text="Ej. 39-4", width=150)
        self.ent_hogar.grid(row=0, column=1, pady=10, padx=20, sticky="w")
        
        # Disparadores (Triggers) para recargar la vista al confirmar la casa
        self.ent_hogar.bind("<Return>", lambda event: self.cambiar_modalidad(self.opt_modo.get()))
        self.ent_hogar.bind("<FocusOut>", lambda event: self.cambiar_modalidad(self.opt_modo.get()))
        
        if lote_precargado is not None and casa_precargada is not None:
            self.ent_hogar.insert(0, f"{lote_precargado}-{casa_precargada}")

        lbl_modo = ctk.CTkLabel(self.contenedor_superior, text="Operación:", font=ctk.CTkFont(size=14))
        lbl_modo.grid(row=1, column=0, pady=10, padx=20, sticky="e")
        
        self.opt_modo = ctk.CTkOptionMenu(
            self.contenedor_superior, 
            values=["Alta de Dispositivos", "Baja de Dispositivos"], 
            width=200, 
            command=self.cambiar_modalidad
        )
        self.opt_modo.grid(row=1, column=1, pady=10, padx=20, sticky="w")
        self.opt_modo.set(modo_inicial)

        ctk.CTkLabel(self, text="-"*80, text_color="gray40").grid(row=2, column=0, pady=10)

        # 2. Área Dinámica (Donde se inyectan los formularios generados)
        self.area_dinamica = ctk.CTkFrame(self, fg_color="transparent")
        self.area_dinamica.grid(row=3, column=0, sticky="nsew", padx=20)
        self.area_dinamica.grid_columnconfigure(0, weight=1)

        # 3. Arranque inicial
        self.cambiar_modalidad(modo_inicial)

    def cambiar_modalidad(self, modo_seleccionado: str):
        """Limpia el área dinámica y construye la interfaz solicitada."""
        for widget in self.area_dinamica.winfo_children():
            widget.destroy()

        if modo_seleccionado == "Alta de Dispositivos":
            self.construir_vista_alta()
        else:
            self.construir_vista_baja()

    # =========================================================
    # MODO ALTA: REGISTRO Y CÁLCULO FINANCIERO
    # =========================================================
    def construir_vista_alta(self):
        """
        Genera el formulario interactivo para dar de alta nuevos dispositivos.
        Despliega selectores numéricos que generan cajas de texto dinámicamente.
        """
        opciones_numericas = [str(i) for i in range(11)]
        opciones_wifi_base = [str(i) for i in range(2, 11)] 
        ancho_combo = 70 

        # 1. Selector de Acceso Base
        self.var_acceso_base = ctk.BooleanVar(value=True) 
        chk_base = ctk.CTkCheckBox(
            self.area_dinamica, text="Acceso Base", variable=self.var_acceso_base, 
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#1f6aa5", 
            command=self.sincronizar_wifi_base
        )
        chk_base.pack(anchor="w", padx=40, pady=(15, 10))

        # 2. Generador de Chips Peatonales
        ctk.CTkLabel(self.area_dinamica, text="Chips Peatonales", font=ctk.CTkFont(size=16, weight="bold"), text_color="#1f6aa5").pack(anchor="w", padx=40, pady=(10, 5))
        frame_chips_ctrl = ctk.CTkFrame(self.area_dinamica, fg_color="transparent")
        frame_chips_ctrl.pack(fill="x", padx=60, pady=5)
        ctk.CTkLabel(frame_chips_ctrl, text="Cantidad:").pack(side="left", padx=(0, 10))
        
        self.opt_chips = ctk.CTkOptionMenu(frame_chips_ctrl, values=opciones_numericas, command=self.generar_campos_chips, width=ancho_combo)
        self.opt_chips.pack(side="left")
        
        self.frame_campos_chips = ctk.CTkFrame(self.area_dinamica, fg_color="transparent")
        self.frame_campos_chips.pack(fill="x", padx=80)

        # 3. Generador de Controles Vehiculares
        ctk.CTkLabel(self.area_dinamica, text="Controles Vehiculares", font=ctk.CTkFont(size=16, weight="bold"), text_color="#1f6aa5").pack(anchor="w", padx=40, pady=(20, 5))
        frame_rf_ctrl = ctk.CTkFrame(self.area_dinamica, fg_color="transparent")
        frame_rf_ctrl.pack(fill="x", padx=60, pady=5)
        ctk.CTkLabel(frame_rf_ctrl, text="Cantidad:").pack(side="left", padx=(0, 10))
        
        self.opt_rf = ctk.CTkOptionMenu(frame_rf_ctrl, values=opciones_numericas, command=self.generar_campos_rf, width=ancho_combo)
        self.opt_rf.pack(side="left")
        
        self.frame_campos_rf = ctk.CTkFrame(self.area_dinamica, fg_color="transparent")
        self.frame_campos_rf.pack(fill="x", padx=80)

        # 4. Generador de Accesos Wi-Fi
        ctk.CTkLabel(self.area_dinamica, text="Accesos WiFi", font=ctk.CTkFont(size=16, weight="bold"), text_color="#1f6aa5").pack(anchor="w", padx=40, pady=(20, 5))
        frame_wifi_ctrl = ctk.CTkFrame(self.area_dinamica, fg_color="transparent")
        frame_wifi_ctrl.pack(fill="x", padx=60, pady=5)
        ctk.CTkLabel(frame_wifi_ctrl, text="Cantidad:").pack(side="left", padx=(0, 10))
        
        self.opt_wifi = ctk.CTkOptionMenu(frame_wifi_ctrl, values=opciones_wifi_base, command=self.generar_campos_wifi, width=ancho_combo)
        self.opt_wifi.pack(side="left")
        
        self.frame_campos_wifi = ctk.CTkFrame(self.area_dinamica, fg_color="transparent")
        self.frame_campos_wifi.pack(fill="x", padx=80)

        # 5. Botón de Procesamiento
        btn_registrar = ctk.CTkButton(
            self.area_dinamica, text="Calcular Finanzas y Proceder", 
            height=40, font=ctk.CTkFont(weight="bold"), command=self.calcular_y_redirigir_finanzas
        )
        btn_registrar.pack(pady=40)

        # 6. Inicialización de interfaz visual
        self.opt_chips.set("1")
        self.opt_rf.set("1")
        self.opt_wifi.set("2")
        self.generar_campos_chips("1")
        self.generar_campos_rf("1")
        self.generar_campos_wifi("2")
        self.after(50, self.limpiar_hack_espaciado)
    
    def sincronizar_wifi_base(self):
        """Forza un mínimo de 2 cuentas Wi-Fi permitidas si el cobro de Acceso Base está activo."""
        if self.var_acceso_base.get():
            self.opt_wifi.configure(values=[str(i) for i in range(2, 11)])
            if int(self.opt_wifi.get()) < 2:
                self.opt_wifi.set("2")
                self.generar_campos_wifi("2")
        else:
            self.opt_wifi.configure(values=[str(i) for i in range(11)])
    
    def calcular_y_redirigir_finanzas(self):
        """
        Extrae los datos capturados, realiza validaciones anti-duplicados estrictas 
        (locales y en SQLite), calcula el costo total interactuando con el Catálogo de 
        Precios y enruta el 'payload' hacia la vista de Finanzas para el cobro.
        """
        hogar_str = self.ent_hogar.get().strip()
        
        if not hogar_str:
            messagebox.showwarning("Dato Requerido", "Por favor, ingresa el número de Hogar (LT-C) antes de proceder.")
            return
            
        qty_chips = int(self.opt_chips.get())
        qty_rf = int(self.opt_rf.get())
        qty_wifi = int(self.opt_wifi.get())
        cobrar_base = self.var_acceso_base.get()
        
        # 1. Extracción de Identificadores (UI a Memoria)
        def extraer_valores(frame_contenedor):
            valores = []
            for child_frame in frame_contenedor.winfo_children():
                for widget in child_frame.winfo_children():
                    if isinstance(widget, ctk.CTkEntry):
                        val = widget.get().strip()
                        if val: valores.append(val)
            return valores

        nuevos_chips = extraer_valores(self.frame_campos_chips)
        nuevos_rf = extraer_valores(self.frame_campos_rf)
        nuevos_wifi = extraer_valores(self.frame_campos_wifi)

        if len(nuevos_chips) != qty_chips or len(nuevos_rf) != qty_rf or len(nuevos_wifi) != qty_wifi:
            messagebox.showwarning("Campos Incompletos", "Debes llenar todos los identificadores de hardware generados.")
            return

        # 2. Validación Anti-Duplicados Locales (En la misma captura)
        if len(nuevos_chips) != len(set(nuevos_chips)):
            messagebox.showwarning("Duplicados Locales", "Has escrito el mismo ID en más de un Chip Peatonal.")
            return
        if len(nuevos_rf) != len(set(nuevos_rf)):
            messagebox.showwarning("Duplicados Locales", "Has escrito el mismo ID en más de un Control Vehicular.")
            return
        if len(nuevos_wifi) != len(set(nuevos_wifi)):
            messagebox.showwarning("Correos Repetidos", "Has escrito el mismo correo Wi-Fi más de una vez. Cada acceso debe ser único.")
            return

        # 3. Validación de Integridad Referencial en SQLite
        try:
            lote_str, casa_str = hogar_str.split('-')
            num_lote = int(lote_str)
            num_casa = str(casa_str)
        except ValueError:
            messagebox.showwarning("Formato Inválido", "El formato del Hogar debe ser 'Lote-Casa' (Ej. 39-4).")
            return

        db_session = self.winfo_toplevel().db_session

        casa = db_session.query(Casa).join(Lote).filter(
            Lote.numero == num_lote,
            Casa.numero_interior == num_casa
        ).first()

        if not casa:
            messagebox.showerror("No Encontrado", f"El hogar {hogar_str} no existe en la base de datos.")
            return

        # REGLA A: Prevención de cobro doble por Acceso Base
        if cobrar_base and casa.acceso_base:
            messagebox.showwarning("Regla de Negocio", f"Operación Abortada: El hogar {hogar_str} ya tiene su Acceso Base pagado y registrado.")
            return

        # REGLA B: Prevención de colisiones de Hardware Físico en BD
        duplicados_msg = []
        if nuevos_chips:
            dup_chips = db_session.query(Dispositivo.identificador_hardware).filter(
                Dispositivo.identificador_hardware.in_(nuevos_chips),
                Dispositivo.tipo_dispositivo == "RFID"
            ).all()
            if dup_chips:
                duplicados_msg.append("Chips Peatonales: " + ", ".join([d[0] for d in dup_chips]))

        if nuevos_rf:
            dup_rf = db_session.query(Dispositivo.identificador_hardware).filter(
                Dispositivo.identificador_hardware.in_(nuevos_rf),
                Dispositivo.tipo_dispositivo == "RF_VEHICULAR"
            ).all()
            if dup_rf:
                duplicados_msg.append("Controles Vehiculares: " + ", ".join([d[0] for d in dup_rf]))

        if duplicados_msg:
            mensaje_alerta = "\n".join(duplicados_msg)
            messagebox.showerror("IDs Duplicados", f"Operación Abortada: Los siguientes dispositivos ya existen en la BD:\n\n{mensaje_alerta}")
            return

        # REGLA C: Prevención de colisiones de Hardware Lógico (Cuentas Tuya)
        if nuevos_wifi:
            duplicados_wifi = db_session.query(Dispositivo.identificador_hardware).filter(
                Dispositivo.identificador_hardware.in_(nuevos_wifi),
                Dispositivo.tipo_dispositivo == "WIFI_PERMIT"
            ).all()
            if duplicados_wifi:
                lista_dup = ", ".join([d[0] for d in duplicados_wifi])
                messagebox.showerror("Correos Duplicados", f"Operación Abortada: Los siguientes correos ya tienen acceso:\n\n{lista_dup}")
                return

        # 4. Cálculo Financiero (Construcción del Ticket)
        catalogo = db_session.query(CatalogoPrecios).all()
        precios = {item.dispositivo: item.precio_unitario for item in catalogo}
        
        total = 0
        elementos = [] 
        
        if cobrar_base:
            pu = precios.get("Acceso Base (Pistones y 2 WiFi)", 400.0)
            total += pu
            elementos.append({"cant": 1, "desc": "Acceso Base (Pistones y 2 WiFi)", "pu": pu, "sub": pu})
            
        if qty_chips > 0:
            pu = precios.get("Chip Peatonal", 100.0)
            subtotal = qty_chips * pu
            total += subtotal
            elementos.append({"cant": qty_chips, "desc": "Chip Peatonal", "pu": pu, "sub": subtotal})
            
        if qty_rf > 0:
            pu = precios.get("Control Vehicular", 250.0)
            subtotal = qty_rf * pu
            total += subtotal
            elementos.append({"cant": qty_rf, "desc": "Control Vehicular", "pu": pu, "sub": subtotal})
            
        wifi_extras = (qty_wifi - 2) if cobrar_base else qty_wifi
        if wifi_extras > 0:
            pu = precios.get("Acceso WiFi Extra", 200.0)
            subtotal = wifi_extras * pu
            total += subtotal
            elementos.append({"cant": wifi_extras, "desc": "Acceso WiFi Extra", "pu": pu, "sub": subtotal})

        if total == 0:
            messagebox.showinfo("Inventario", "No hay hardware para cobrar.")
            return

        # 5. Estructuración del Payload y Enrutamiento
        payload = {
            "tipo_concepto": "Venta de Hardware",
            "detalles": elementos,
            "total_calculado": total,
            "ids_chips": nuevos_chips,   
            "ids_rf": nuevos_rf,         
            "correos_wifi": nuevos_wifi  
        }
        
        app_principal = self.winfo_toplevel()
        app_principal.cargar_vista("finanzas", hogar_str=hogar_str, payload_hardware=payload)
    
    def limpiar_hack_espaciado(self):
        """Restaura los valores por defecto de los combos tras renderizar el frame dinámico."""
        if self.winfo_exists():
            self.opt_chips.set("0")
            self.opt_rf.set("0")
            min_wifi = "2" if self.var_acceso_base.get() else "0"
            self.opt_wifi.set(min_wifi)
            self.generar_campos_chips("0")
            self.generar_campos_rf("0")
            self.generar_campos_wifi(min_wifi)
    
    def generar_campos_chips(self, cantidad: str):
        """Inyecta entradas de texto dinámicas para los IDs de Chips."""
        for w in self.frame_campos_chips.winfo_children(): w.destroy()
        for i in range(int(cantidad)):
            f = ctk.CTkFrame(self.frame_campos_chips, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=f"ID Chip #{i+1}:", width=100, anchor="e").pack(side="left", padx=5)
            ctk.CTkEntry(f, placeholder_text=f"Ej. {i+1}", width=120).pack(side="left")

    def generar_campos_rf(self, cantidad: str):
        """Inyecta entradas de texto dinámicas para los Controles Vehiculares."""
        for w in self.frame_campos_rf.winfo_children(): w.destroy()
        for i in range(int(cantidad)):
            f = ctk.CTkFrame(self.frame_campos_rf, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=f"ID Control #{i+1}:", width=100, anchor="e").pack(side="left", padx=5)
            ctk.CTkEntry(f, placeholder_text=f"Ej. {i+1}", width=120).pack(side="left")

    def generar_campos_wifi(self, cantidad: str):
        """Inyecta entradas de texto dinámicas para los correos electrónicos Wi-Fi."""
        for w in self.frame_campos_wifi.winfo_children(): w.destroy()
        for i in range(int(cantidad)):
            f = ctk.CTkFrame(self.frame_campos_wifi, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=f"Acceso #{i+1}:", width=100, anchor="e").pack(side="left", padx=5)
            ctk.CTkEntry(f, placeholder_text="vecino@correo.com", width=250).pack(side="left")

    # =========================================================
    # MODO BAJA / EDICIÓN: AUDITORÍA DE INVENTARIO
    # =========================================================
    def construir_vista_baja(self):
        """
        Consulta la base de datos real e inyecta la lista de dispositivos 
        asignados a una vivienda, permitiendo su eliminación o modificación 'inline'.
        """
        hogar_str = self.ent_hogar.get().strip()

        # 1. Preparación de estructura temporal
        datos_reales = {
            "Chips Peatonales": [],
            "Controles Vehiculares": [],
            "Accesos WiFi": []
        }
        estado_acceso_base = False
        casa_encontrada = None

        # 2. Búsqueda Relacional en SQLite
        if hogar_str and "-" in hogar_str:
            try:
                lote_str, casa_str = hogar_str.split('-')
                num_lote = int(lote_str)
                num_casa = str(casa_str)

                db_session = self.winfo_toplevel().db_session

                casa_encontrada = db_session.query(Casa).join(Lote).filter(
                    Lote.numero == num_lote,
                    Casa.numero_interior == num_casa
                ).first()

                if casa_encontrada:
                    estado_acceso_base = casa_encontrada.acceso_base
                    for disp in casa_encontrada.dispositivos:
                        if disp.tipo_dispositivo == "RFID":
                            datos_reales["Chips Peatonales"].append(f"ID: {disp.identificador_hardware}")
                        elif disp.tipo_dispositivo == "RF_VEHICULAR":
                            datos_reales["Controles Vehiculares"].append(f"ID: {disp.identificador_hardware}")
                        elif disp.tipo_dispositivo == "WIFI_PERMIT":
                            datos_reales["Accesos WiFi"].append(disp.identificador_hardware)
            except ValueError:
                pass 

        # 3. Renderizado del Estado de Infraestructura (Acceso Base)
        frame_base = ctk.CTkFrame(self.area_dinamica, fg_color="transparent")
        frame_base.pack(fill="x", padx=40, pady=(10, 20))
        
        ctk.CTkLabel(frame_base, text="Acceso Base (Pistones):", font=ctk.CTkFont(size=16, weight="bold"), text_color="#1f6aa5").pack(side="left", padx=(0, 15))
        
        if casa_encontrada:
            if estado_acceso_base:
                lbl_estado_base = ctk.CTkLabel(frame_base, text="✅ Pagado", font=ctk.CTkFont(weight="bold"), text_color="#104A20")
            else:
                lbl_estado_base = ctk.CTkLabel(frame_base, text="❌ No adquirido", font=ctk.CTkFont(weight="bold"), text_color="#4A1010")
            lbl_estado_base.pack(side="left")
        else:
            ctk.CTkLabel(self.area_dinamica, text="⚠️ Ingresa un número de Hogar válido (Ej. 39-4) arriba y presiona Enter.", text_color="#b8860b").pack(pady=10)

        # 4. Renderizado Dinámico de Categorías y Dispositivos
        for categoria, elementos in datos_reales.items():
            ctk.CTkLabel(self.area_dinamica, text=categoria, font=ctk.CTkFont(size=16, weight="bold"), text_color="#1f6aa5").pack(anchor="w", padx=40, pady=(20, 5))

            if not elementos:
                ctk.CTkLabel(self.area_dinamica, text="No hay dispositivos registrados en esta categoría.", text_color="gray50").pack(anchor="w", padx=60)
                continue

            for item in elementos:
                frame_item = ctk.CTkFrame(self.area_dinamica, fg_color="gray15")
                frame_item.pack(fill="x", padx=60, pady=3)
                
                lbl_item = ctk.CTkLabel(frame_item, text=item, font=ctk.CTkFont(size=14))
                lbl_item.pack(side="left", padx=15, pady=8)
                
                btn_eliminar = ctk.CTkButton(frame_item, text="Eliminar", width=70, fg_color="#8B0000", hover_color="#5C0000")
                btn_eliminar.pack(side="right", padx=(5, 15), pady=8)
                
                btn_editar = ctk.CTkButton(frame_item, text="Editar", width=70, fg_color="#b8860b", hover_color="#8b6508")
                btn_editar.pack(side="right", padx=5, pady=8)
                
                if categoria == "Accesos WiFi":
                    btn_copiar = ctk.CTkButton(frame_item, text="Copiar", width=60, fg_color="gray30", hover_color="gray20",
                                               command=lambda l=lbl_item: self.copiar_portapapeles(l))
                    btn_copiar.pack(side="right", padx=5, pady=8)

                # Anclaje de eventos y referencias para manipulación local
                btn_editar.configure(command=lambda b=btn_editar, l=lbl_item, f=frame_item, c=categoria: self.toggle_edicion(b, l, f, c))
                btn_eliminar.configure(command=lambda l=lbl_item, c=categoria, f=frame_item: self.confirmar_eliminacion(l, c, f))

    def confirmar_eliminacion(self, lbl, categoria: str, frame_item):
        """
        Purga un dispositivo específico de la base de datos tras confirmación
        del administrador y dispara alertas automatizadas vía correo.
        """
        texto_actual = lbl.cget("text")
        registro_limpio = texto_actual.replace("ID: ", "").strip()
        
        respuesta = messagebox.askyesno("Auditoría Crítica", f"¿Estás seguro de revocar permanentemente este acceso de la base de datos?\n\nDispositivo: {categoria}\nRegistro: {registro_limpio}\n\nEsta acción no se puede deshacer.")
        if respuesta:
            db_session = self.winfo_toplevel().db_session
            disp = db_session.query(Dispositivo).filter(Dispositivo.identificador_hardware == registro_limpio).first()
            
            if disp:
                # 1. Extracción de contexto (Titular y Hogar) antes de borrar
                propietario = next((r for r in disp.casa.residentes if r.es_propietario), None)
                correo = propietario.email if propietario else None
                hogar_str = f"{disp.casa.lote.numero}-{disp.casa.numero_interior}"
                
                # 2. Eliminación Atómica
                db_session.delete(disp)
                db_session.commit()
                frame_item.destroy()
                
                # 3. Disparo de Notificación Administrativa (El Cartero)
                if correo:
                    cartero = self.winfo_toplevel().notification_service
                    cartero.notificar_baja_dispositivo(correo, hogar_str, registro_limpio)
                
                messagebox.showinfo("Éxito", "El dispositivo ha sido eliminado.")
            else:
                messagebox.showerror("Error", "No se encontró el dispositivo en la base de datos.")

    def copiar_portapapeles(self, lbl):
        """Copia el identificador del dispositivo al portapapeles del sistema operativo."""
        texto = lbl.cget("text")
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.update() 
    
    def toggle_edicion(self, btn, lbl, frame, categoria: str):
        """
        Alterna la interfaz entre modo lectura y caja de texto para modificar
        el ID de un dispositivo existente. Ejecuta validaciones estrictas y
        envía correos automatizados según la naturaleza del cambio.
        """
        db_session = self.winfo_toplevel().db_session
        
        if btn.cget("text") == "Editar":
            # 1. Habilitar Modo Edición
            texto_actual = lbl.cget("text")
            texto_limpio = texto_actual.replace("ID: ", "").strip()
            
            btn._original_id = texto_limpio
            
            if categoria != "Accesos WiFi":
                lbl.configure(text="ID: ")
            else:
                lbl.configure(text="")
                
            entry = ctk.CTkEntry(frame, width=180)
            entry.insert(0, texto_limpio)
            entry.pack(side="left", padx=(0, 10))
            
            btn._entry_ref = entry 
            btn.configure(text="Guardar", fg_color="#104A20", hover_color="#006400")
            
        else:
            # 2. Validar y Guardar Modificación
            nuevo_texto = btn._entry_ref.get().strip()
            original_id = getattr(btn, '_original_id', None)
            
            if categoria != "Accesos WiFi":
                try:
                    int(nuevo_texto)
                except ValueError:
                    messagebox.showwarning("Error de Captura", "El ID del dispositivo debe contener únicamente números.")
                    return 
            
            # 3. Blindaje de Integridad y Duplicidad en BD
            if nuevo_texto != original_id:
                duplicado = db_session.query(Dispositivo).filter(Dispositivo.identificador_hardware == nuevo_texto).first()
                
                if duplicado:
                    if categoria == "Accesos WiFi":
                        messagebox.showerror("Correo Duplicado", f"Operación Abortada: El correo '{nuevo_texto}' ya está registrado en el sistema.")
                    else:
                        messagebox.showerror("ID Duplicado", f"Operación Abortada: El ID '{nuevo_texto}' ya está asignado a otro dispositivo.")
                    return 
                
                # 4. Actualización del Registro Físico
                dispositivo_db = db_session.query(Dispositivo).filter(Dispositivo.identificador_hardware == original_id).first()
                
                if dispositivo_db:
                    propietario = next((r for r in dispositivo_db.casa.residentes if r.es_propietario), None)
                    correo = propietario.email if propietario else None
                    hogar_str = f"{dispositivo_db.casa.lote.numero}-{dispositivo_db.casa.numero_interior}"
                    
                    dispositivo_db.identificador_hardware = nuevo_texto
                    try:
                        db_session.commit()
                        
                        # 5. Enrutamiento de Correos Automatizados
                        cartero = self.winfo_toplevel().notification_service
                        
                        if correo:
                            cartero.notificar_edicion_dispositivo(correo, hogar_str, nuevo_texto, categoria)
                            
                        if categoria == "Accesos WiFi":
                            # Ruteo especial: Baja del antiguo usuario, Alta (Instrucciones) al nuevo.
                            cartero.notificar_baja_dispositivo(original_id, hogar_str, original_id)
                            cartero.notificar_nuevo_wifi(nuevo_texto, hogar_str)
                            
                    except Exception as e:
                        db_session.rollback()
                        messagebox.showerror("Error SQL", f"No se pudo actualizar: {e}")
                        return

            # 6. Restauración de Interfaz UI
            btn._entry_ref.destroy()
            
            texto_final = f"ID: {nuevo_texto}" if categoria != "Accesos WiFi" else nuevo_texto
            lbl.configure(text=texto_final)
            
            btn.configure(text="Editar", fg_color="#b8860b", hover_color="#8b6508")