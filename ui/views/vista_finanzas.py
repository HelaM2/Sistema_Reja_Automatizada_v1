# ui/views/vista_finanzas.py
"""
Capa de Presentación: Punto de Venta y Control Financiero.
Interfaz interactiva para el registro de pagos, liquidación de adeudos, 
carga de comprobantes visuales y consulta del flujo de caja general.
Se integra directamente con los servicios de pago y notificaciones.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from datetime import datetime
from domain.models import Casa, Lote, CatalogoPrecios, Pago

class VistaFinanzas(ctk.CTkFrame):
    """
    Vista principal para la gestión financiera de la privada.
    Construye un formulario dinámico a la izquierda y un historial de 
    flujo de caja a la derecha. Soporta precarga de datos para cobros 
    generados desde el módulo de hardware o el panel de detalles.
    """
    
    def __init__(self, master, payment_service, lote_precargado=None, casa_precargada=None, hogar_str=None, payload_hardware=None):
        """
        Inicializa la vista y distribuye los paneles principales.
        
        Args:
            master: Frame contenedor padre.
            payment_service: Servicio inyectado para la gestión en BD.
            lote_precargado (int, optional): Número de lote pre-seleccionado.
            casa_precargada (str, optional): Número de casa pre-seleccionado.
            hogar_str (str, optional): Cadena formateada "Lote-Casa" pre-seleccionada.
            payload_hardware (dict, optional): Datos inyectados desde la vista de Dispositivos.
        """
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.payment_service = payment_service  
        
        titulo = ctk.CTkLabel(self, text="Control Financiero y Comprobantes", font=ctk.CTkFont(size=24, weight="bold"))
        titulo.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # 1. Configuración principal del Grid (Izquierda: Formulario | Derecha: Historial)
        self.grid_rowconfigure(1, weight=1) 
        self.grid_columnconfigure(0, weight=1, uniform="estatico")
        self.grid_columnconfigure(1, weight=1, uniform="estatico")

        # =========================================================
        # 2. PANEL IZQUIERDO: Formulario y Comprobantes
        # =========================================================
        frame_izquierdo = ctk.CTkFrame(self, fg_color="transparent")
        frame_izquierdo.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        frame_izquierdo.grid_columnconfigure(0, weight=1)
        frame_izquierdo.grid_rowconfigure(1, weight=1)

        # --- Sub-Panel: Formulario Dinámico ---
        frame_formulario = ctk.CTkFrame(frame_izquierdo)
        frame_formulario.grid(row=0, column=0, sticky="new", pady=(0, 10))
        
        self.ent_hogar = ctk.CTkEntry(frame_formulario, placeholder_text="Hogar (LT-C) Ej. 39-4")
        self.ent_hogar.pack(pady=5, padx=10, fill="x")
        
        # Disparadores de cálculos automáticos
        self.ent_hogar.bind("<Return>", self.disparar_calculos)
        self.ent_hogar.bind("<FocusOut>", self.disparar_calculos)
        
        # Ruteo inteligente del Hogar según parámetros iniciales
        if hogar_str:
            self.ent_hogar.insert(0, hogar_str)
        elif lote_precargado is not None and casa_precargada is not None:
            self.ent_hogar.insert(0, f"{lote_precargado}-{casa_precargada}")

        # Controles de Fecha (Auto-llenados con el mes actual)
        frame_fecha = ctk.CTkFrame(frame_formulario, fg_color="transparent")
        frame_fecha.pack(fill="x")
        hoy = datetime.now()
        
        self.ent_mes = ctk.CTkEntry(frame_fecha, placeholder_text="Mes", width=100)
        self.ent_mes.pack(side="left", pady=5, padx=(10, 5), expand=True, fill="x")
        self.ent_mes.insert(0, str(hoy.month))
        
        self.ent_anio = ctk.CTkEntry(frame_fecha, placeholder_text="Año", width=100)
        self.ent_anio.pack(side="right", pady=5, padx=(5, 10), expand=True, fill="x")
        self.ent_anio.insert(0, str(hoy.year))

        # Controles de Concepto y Notas
        self.var_concepto = ctk.StringVar(value="Mantenimiento")
        self.opt_concepto = ctk.CTkOptionMenu(
            frame_formulario,
            variable=self.var_concepto,
            values=["Mantenimiento", "Venta de Hardware", "Liquidación de Adeudo", "Otros"],
            command=self.disparar_calculos
        )
        self.opt_concepto.pack(pady=(5, 0), padx=10, fill="x")

        self.ent_notas = ctk.CTkEntry(frame_formulario, placeholder_text="Especifique el concepto o notas...")
        self.ent_notas.pack(pady=5, padx=10, fill="x")
        self.ent_notas.configure(state="disabled", fg_color="gray20")

        # Contenedor Dinámico: Tabla de desglose
        self.frame_tabla = ctk.CTkFrame(frame_formulario, fg_color="gray15")
        self.frame_tabla.grid_columnconfigure(1, weight=1)
        
        # Cajas Financieras (Totales)
        frame_dineros = ctk.CTkFrame(frame_formulario, fg_color="transparent")
        frame_dineros.pack(fill="x")
        
        self.ent_total = ctk.CTkEntry(frame_dineros, placeholder_text="Costo Total ($)", text_color="#b8860b")
        self.ent_total.pack(side="left", pady=5, padx=(10, 5), expand=True, fill="x")
        
        self.ent_recibido = ctk.CTkEntry(frame_dineros, placeholder_text="Monto Recibido ($)", text_color="#1B5E20")
        self.ent_recibido.pack(side="right", pady=5, padx=(5, 10), expand=True, fill="x")

        # --- Inyección de Payload (Si aplica) ---
        self.payload_actual = payload_hardware 
        
        if payload_hardware:
            self.var_concepto.set("Venta de Hardware")
            self.gestionar_caja_notas("Venta de Hardware") 
        else:
            self.var_concepto.set("Mantenimiento")
            self.gestionar_caja_notas("Mantenimiento")
            self.actualizar_desglose_mantenimiento() 
            
        btn_registrar_pago = ctk.CTkButton(
            frame_formulario, text="Registrar Transacción en BD", 
            command=self.procesar_pago, fg_color="#1B5E20", hover_color="#2E7D32"
        )
        btn_registrar_pago.pack(pady=10, padx=10, fill="x")

        # --- Sub-Panel: Área de Comprobante ---
        frame_comprobante = ctk.CTkFrame(frame_izquierdo)
        frame_comprobante.grid(row=1, column=0, sticky="nsew")
        frame_comprobante.grid_rowconfigure(0, weight=1)
        frame_comprobante.grid_columnconfigure(0, weight=1)

        self.canvas_imagen = ctk.CTkLabel(frame_comprobante, text="[ Previsualización de Comprobante ]", fg_color="gray20", corner_radius=8)
        self.canvas_imagen.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="nsew")

        btn_cargar = ctk.CTkButton(frame_comprobante, text="Cargar Comprobante", command=self.ejecutar_carga)
        btn_cargar.grid(row=1, column=0, pady=(5, 15))

        # =========================================================
        # 3. PANEL DERECHO: Historial General
        # =========================================================
        self.frame_lista = ctk.CTkScrollableFrame(self, label_text="Flujo de Caja General")
        self.frame_lista.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        self.actualizar_flujo_caja()
    
    def ejecutar_carga(self):
        """Abre un diálogo del sistema operativo para seleccionar y previsualizar una imagen."""
        ruta_archivo = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
        if ruta_archivo:
            self.ruta_imagen_temporal = ruta_archivo
            try:
                img = Image.open(ruta_archivo)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(300, 300))
                self.canvas_imagen.configure(image=ctk_img, text="")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la imagen: {e}")
    
    def dibujar_tabla(self, detalles: list):
        """Renderiza dinámicamente las filas del desglose en el frame de la tabla."""
        for widget in self.frame_tabla.winfo_children():
            widget.destroy()
            
        ctk.CTkLabel(self.frame_tabla, text="Cant.", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(self.frame_tabla, text="Artículo", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(self.frame_tabla, text="P.U.", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=5, pady=2, sticky="e")
        ctk.CTkLabel(self.frame_tabla, text="Subtotal", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, padx=5, pady=2, sticky="e")
        
        for i, item in enumerate(detalles, start=1):
            ctk.CTkLabel(self.frame_tabla, text=str(item["cant"])).grid(row=i, column=0, padx=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=item["desc"]).grid(row=i, column=1, padx=5, sticky="w")
            ctk.CTkLabel(self.frame_tabla, text=f"${item['pu']}").grid(row=i, column=2, padx=5, sticky="e")
            ctk.CTkLabel(self.frame_tabla, text=f"${item['sub']}").grid(row=i, column=3, padx=5, sticky="e")
    
    def gestionar_caja_notas(self, valor_seleccionado: str):
        """Activa/Desactiva elementos de la UI según el concepto seleccionado."""
        self.ent_notas.configure(state="normal", fg_color=["#F9F9FA", "#343638"])
        
        self.ent_total.configure(state="normal")
        self.ent_total.delete(0, 'end')
        self.ent_recibido.delete(0, 'end')
        
        if valor_seleccionado == "Venta de Hardware":
            if hasattr(self, 'payload_actual') and self.payload_actual:
                self.frame_tabla.pack(pady=10, padx=10, fill="x")
                self.dibujar_tabla(self.payload_actual["detalles"])
                self.ent_total.insert(0, str(self.payload_actual["total_calculado"]))
                self.ent_total.configure(state="readonly")
            else:
                self.frame_tabla.pack_forget() 
                
        elif valor_seleccionado in ["Mantenimiento Base", "Mantenimiento"]:
            self.frame_tabla.pack(pady=10, padx=10, fill="x")
            self.actualizar_desglose_mantenimiento()
            
        elif valor_seleccionado == "Cuotas Extraordinarias / Otros":
            self.frame_tabla.pack_forget()
    
    def actualizar_desglose_mantenimiento(self, event=None):
        """Consulta el catálogo oficial y genera un presupuesto para Mantenimiento Base/Extra."""
        concepto_actual = self.var_concepto.get()
        if concepto_actual not in ["Mantenimiento Base", "Mantenimiento"]:
            return

        self.frame_tabla.pack(pady=10, padx=10, fill="x")
        texto_lote_casa = self.ent_hogar.get().strip()
        
        # 1. Obtención de precios desde el catálogo
        try:
            db_session = self.payment_service.db_session 
        except AttributeError:
            db_session = self.master.app_controller.db_session
            
        catalogo = db_session.query(CatalogoPrecios).all()
        precios = {item.dispositivo: item.precio_unitario for item in catalogo}
        
        costo_mtto_base = precios.get("Mantenimiento Base", 200.0)
        costo_mtto_extra = precios.get("Mantenimiento Extra (WiFi)", 100.0)

        # 2. Manejo de estado vacío (Hogar no ingresado)
        if not texto_lote_casa or "-" not in texto_lote_casa:
            detalles_base = [
                {"cant": 0, "desc": "Mantenimiento Base", "pu": costo_mtto_base, "sub": 0},
                {"cant": 0, "desc": "Mantenimiento Extra (WiFi)", "pu": costo_mtto_extra, "sub": 0}
            ]
            self.dibujar_tabla(detalles_base)
            
            lbl_advertencia = ctk.CTkLabel(self.frame_tabla, text="⚠️ Ingresa un número de Hogar válido (Ej. 39-4) arriba.", text_color="#b8860b", font=ctk.CTkFont(weight="bold"))
            lbl_advertencia.grid(row=10, column=0, columnspan=4, pady=(15, 5))
            
            self.ent_total.configure(state="normal")
            self.ent_total.delete(0, 'end')
            self.ent_total.insert(0, "0.0")
            self.ent_total.configure(state="readonly")
            return

        # 3. Consulta de Casa y Cálculo en Vivo
        try:
            lote_str, casa_str = texto_lote_casa.split('-')
            num_lote = int(lote_str)
            num_casa = str(casa_str)
        except ValueError:
            return

        casa = db_session.query(Casa).join(Lote).filter(Lote.numero == num_lote, Casa.numero_interior == num_casa).first()
        if not casa: return 

        if not casa.acceso_base:
            detalles_reales = [{"cant": 0, "desc": "Mantenimiento (Requiere Acceso Base)", "pu": 0, "sub": 0}]
            total_a_pagar = 0.0
        else:
            total_wifis = len([d for d in casa.dispositivos if d.tipo_dispositivo == "WIFI_PERMIT"])
            wifi_extras = (total_wifis - 2) if total_wifis > 2 else 0
            
            sub_extra = wifi_extras * costo_mtto_extra
            total_a_pagar = costo_mtto_base + sub_extra

            detalles_reales = [
                {"cant": 1, "desc": "Mantenimiento Base", "pu": costo_mtto_base, "sub": costo_mtto_base},
                {"cant": wifi_extras, "desc": "Mantenimiento Extra (WiFi)", "pu": costo_mtto_extra, "sub": sub_extra}
            ]

        self.detalles_mantenimiento = detalles_reales
        self.dibujar_tabla(detalles_reales)
        
        self.ent_total.configure(state="normal")
        self.ent_total.delete(0, 'end')
        self.ent_total.insert(0, str(total_a_pagar))
        self.ent_total.configure(state="readonly")
     
    def procesar_pago(self):
        """Extrae, valida y delega el guardado de la transacción financiera."""
        # 1. Extracción de Datos
        hogar_str = self.ent_hogar.get().strip()
        mes_str = self.ent_mes.get().strip()
        anio_str = self.ent_anio.get().strip()
        total_str = self.ent_total.get().strip()
        recibido_str = self.ent_recibido.get().strip()
        notas_str = self.ent_notas.get().strip()

        # 2. Resolución de Conceptos
        concepto_base = self.var_concepto.get()
        detalles_para_bd = []
        ruta_imagen = getattr(self, 'ruta_imagen_temporal', None)

        if concepto_base == "Otros": 
            concepto_final = "Cuota Extraordinaria" 
        elif concepto_base == "Venta de Hardware" and hasattr(self, 'payload_actual') and self.payload_actual:
            concepto_final = "Venta de Hardware"
            detalles_para_bd = self.payload_actual["detalles"]
        elif concepto_base == "Liquidación de Adeudo": 
            concepto_final = "Liquidación de Adeudo"
            if hasattr(self, 'detalles_liquidacion'):
                detalles_para_bd = self.detalles_liquidacion
        else:
            concepto_final = "Mantenimiento Base"
            if hasattr(self, 'detalles_mantenimiento'):
                detalles_para_bd = self.detalles_mantenimiento

        # 3. Validación de Campos Vacíos
        if not all([hogar_str, mes_str, anio_str, concepto_final, total_str, recibido_str]):
            messagebox.showwarning("Formulario Incompleto", "Existen campos vacíos. Por favor, llena todos los datos.")
            return
            
        try:
            # 4. Transformación de Tipos
            partes_hogar = hogar_str.split('-')
            if len(partes_hogar) != 2:
                raise ValueError("El formato del Hogar debe ser 'Lote-Casa' (Ej. 39-4).")
                
            numero_lote = int(partes_hogar[0].strip())
            numero_casa = partes_hogar[1].strip() 
            mes = int(mes_str)
            anio = int(anio_str)
            monto_total = float(total_str)
            monto_recibido = float(recibido_str)
            
            # 5. Ejecución del Servicio de Pago (Delegación BD)
            self.payment_service.register_payment(
                numero_lote, numero_casa, concepto_final, monto_total, monto_recibido, mes, anio, 
                original_image_path=ruta_imagen, 
                detalles_compra=detalles_para_bd,
                notas_internas=notas_str if notas_str else None
            )
            
            # 6. Ejecución Condicional: Venta de Hardware
            if concepto_base == "Venta de Hardware" and hasattr(self, 'payload_actual') and self.payload_actual:
                chips = self.payload_actual.get("ids_chips", [])
                rfs = self.payload_actual.get("ids_rf", [])
                wifis = self.payload_actual.get("correos_wifi", [])
                
                app_principal = self.winfo_toplevel()
                app_principal.hardware_service.registrar_hardware_especifico(
                    numero_lote, numero_casa, chips, rfs, wifis
                )
                
                # Desbloqueo de Acceso Base si fue cobrado
                cobro_base = any("Acceso Base" in item["desc"] for item in self.payload_actual["detalles"])
                if cobro_base:
                    casa_update = self.payment_service.db_session.query(Casa).join(Lote).filter(
                        Lote.numero == numero_lote, Casa.numero_interior == numero_casa
                    ).first()
                    if casa_update:
                        casa_update.acceso_base = True
                        self.payment_service.db_session.commit()
            
            # 7. Disparo de Notificaciones (El Cartero)
            try:
                casa_db = self.payment_service.db_session.query(Casa).join(Lote).filter(
                    Lote.numero == numero_lote, Casa.numero_interior == numero_casa
                ).first()
                
                propietario = next((r for r in casa_db.residentes if r.es_propietario), None)
                correo_titular = propietario.email if propietario else None
                cartero = self.winfo_toplevel().notification_service

                if correo_titular:
                    cartero.notificar_pago(
                        destinatario=correo_titular, hogar=hogar_str, concepto=concepto_final, 
                        total=monto_total, abonado=monto_recibido, detalles=detalles_para_bd, 
                        ruta_adjunto=ruta_imagen
                    )
                
                if concepto_base == "Venta de Hardware" and hasattr(self, 'payload_actual') and self.payload_actual:
                    wifis_nuevos = self.payload_actual.get("correos_wifi", [])
                    for correo_wifi in wifis_nuevos:
                        cartero.notificar_nuevo_wifi(correo_wifi, hogar_str)
                        
            except Exception as correo_err:
                print(f"Error silencioso al despachar correos: {correo_err}")

            # 8. Limpieza de Interfaz
            messagebox.showinfo("Transacción Exitosa", "Pago registrado en la Base de Datos.")
            
            self.ent_hogar.delete(0, 'end')
            self.ent_total.configure(state="normal") 
            self.ent_total.delete(0, 'end')
            self.ent_recibido.delete(0, 'end')
            self.actualizar_flujo_caja()
            
            self.var_concepto.set("Mantenimiento Base")
            self.gestionar_caja_notas("Mantenimiento Base")
            if hasattr(self, 'frame_tabla'):
                self.frame_tabla.pack_forget() 
                self.payload_actual = None 

            self.ruta_imagen_temporal = None
            if hasattr(self, 'canvas_imagen'):
                self.canvas_imagen.configure(image=None, text="[ Previsualización de Comprobante ]")
        
        except ValueError as ve:
            messagebox.showwarning("Conflicto de Datos", f"Verifique la información ingresada:\n{ve}")
        except Exception as e:
            messagebox.showerror("Excepción Crítica", f"Error inesperado con SQLite: {e}")

    def actualizar_flujo_caja(self):
        """Consulta y renderiza las últimas 50 transacciones registradas en SQLite."""
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        try:
            db_session = self.payment_service.db_session 
        except AttributeError:
            db_session = self.master.app_controller.db_session
            
        pagos = db_session.query(Pago).order_by(Pago.id.desc()).limit(50).all()

        if not pagos:
            ctk.CTkLabel(self.frame_lista, text="No hay transacciones registradas.", text_color="gray50").pack(pady=20)
            return

        for p in pagos:
            lote_num = p.casa.lote.numero
            casa_num = str(int(p.casa.numero_interior))
            
            titulo_transaccion = f"Hogar {lote_num}-{casa_num} | {p.concepto}"
            
            tarjeta = ctk.CTkFrame(self.frame_lista, fg_color="gray15")
            tarjeta.pack(fill="x", pady=5, padx=5)
            
            lbl_tit = ctk.CTkLabel(tarjeta, text=titulo_transaccion, font=ctk.CTkFont(weight="bold", size=13))
            lbl_tit.pack(anchor="w", padx=10, pady=(10, 0))
            
            txt_montos = f"Total: ${p.monto_total:,.0f} | Abonado: ${p.monto_abonado:,.0f}" 
            lbl_montos = ctk.CTkLabel(tarjeta, text=txt_montos, font=ctk.CTkFont(size=12), text_color="gray70")
            lbl_montos.pack(anchor="w", padx=10, pady=(2, 2))
            
            texto_detalles = ""
            if p.detalles:
                for det in p.detalles:
                    texto_detalles += f"  • {det.cantidad}x {det.descripcion} (${det.precio_unitario:,.0f} c/u)\n"
            
            if getattr(p, 'notas_internas', None):
                texto_detalles += f"  📝 Nota: {p.notas_internas}\n"
            
            if texto_detalles:
                lbl_desglose = ctk.CTkLabel(tarjeta, text=texto_detalles.strip(), font=ctk.CTkFont(size=11), text_color="#A9A9A9", justify="left")
                lbl_desglose.pack(anchor="w", padx=10, pady=(2, 5))
            
            liquidado = p.monto_abonado >= p.monto_total
            color_estado = "white" if liquidado else "#b8860b"
            icono = "☑" if liquidado else "⚠"
            texto_estado = "Liquidado" if liquidado else "Saldo Pendiente"
            
            txt_final = f"{p.mes_cubierto:02d}/{p.anio_cubierto} - {icono} {texto_estado}"
            lbl_estado = ctk.CTkLabel(tarjeta, text=txt_final, font=ctk.CTkFont(size=12), text_color=color_estado)
            lbl_estado.pack(anchor="e", padx=10, pady=(0, 10))
        
    def evaluar_liquidacion(self, event=None):
        """Calcula la deuda histórica y autocompleta el formulario para liquidaciones."""
        concepto_actual = self.var_concepto.get()
        if concepto_actual != "Liquidación de Adeudo":
            return

        texto_lote_casa = self.ent_hogar.get().strip()
        if not texto_lote_casa or "-" not in texto_lote_casa:
            return

        try:
            lote_str, casa_str = texto_lote_casa.split('-')
            num_lote = int(lote_str)
            num_casa = str(casa_str)
        except ValueError:
            return

        try:
            db_session = self.payment_service.db_session 
        except AttributeError:
            db_session = self.master.app_controller.db_session

        casa = db_session.query(Casa).join(Lote).filter(Lote.numero == num_lote, Casa.numero_interior == num_casa).first()
        if not casa: return

        # 1. Barrido de Pagos Históricos
        pagos_hist = db_session.query(Pago).filter(Pago.casa_id == casa.id).all()
        cargos = sum(p.monto_total for p in pagos_hist if p.concepto != "Liquidación de Adeudo")
        abonos = sum(p.monto_abonado for p in pagos_hist)
        
        deuda_total = max(cargos - abonos, 0.0)

        # 2. Auto-rellenado de Cajas Financieras
        self.ent_total.configure(state="normal")
        self.ent_total.delete(0, 'end')
        self.ent_total.insert(0, str(deuda_total))
        self.ent_total.configure(state="readonly")
        
        self.ent_recibido.delete(0, 'end')
        self.ent_recibido.insert(0, str(deuda_total))

        # 3. Dibujo de Ticket de Liquidación
        detalles_liquidacion = [{"cant": 1, "desc": "Liquidación de Adeudo Histórico", "pu": deuda_total, "sub": deuda_total}]
        self.detalles_liquidacion = detalles_liquidacion
        self.dibujar_tabla(detalles_liquidacion)

    def disparar_calculos(self, event=None):
        """Enruta la interfaz hacia las matemáticas correctas según el concepto seleccionado."""
        concepto_actual = self.var_concepto.get()
        
        if hasattr(self, 'gestionar_caja_notas'):
            self.gestionar_caja_notas(concepto_actual)
            
        if concepto_actual == "Liquidación de Adeudo":
            self.evaluar_liquidacion()
        elif concepto_actual in ["Mantenimiento Base", "Mantenimiento"]:
            self.actualizar_desglose_mantenimiento()