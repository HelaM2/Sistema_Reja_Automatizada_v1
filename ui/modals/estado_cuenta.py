import customtkinter as ctk
from domain.models import Casa, Lote

# =========================================================
# VENTANA EMERGENTE: ESTADO DE CUENTA DETALLADO
# =========================================================
class VentanaEstadoCuenta(ctk.CTkToplevel):
    def __init__(self, master, lote_num, casa_num, db_session):
        super().__init__(master)
        
        self.title(f"Estado de Cuenta - Hogar {lote_num}-{casa_num}")
        self.geometry("650x550")
        self.minsize(500, 400)
        
        # Hacemos la ventana "modal" (bloquea la app principal hasta que se cierre)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Encabezado
        lbl_titulo = ctk.CTkLabel(self, text=f"Historial Completo | Hogar {lote_num}-{casa_num}", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_titulo.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")

        # Contenedor con Scroll
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # 1. Buscar los pagos en SQLite
        from domain.models import Casa, Lote
        casa = db_session.query(Casa).join(Lote).filter(
            Lote.numero == lote_num, Casa.numero_interior == casa_num
        ).first()

        if not casa or not casa.pagos:
            ctk.CTkLabel(scroll_frame, text="No hay transacciones registradas.", text_color="gray50").pack(pady=20)
            return

        # 2. Ordenar de más reciente a más antiguo
        pagos = sorted(casa.pagos, key=lambda x: x.id, reverse=True)

        # 3. Dibujar las tarjetas (Mismo diseño que Finanzas)
        for p in pagos:
            tarjeta = ctk.CTkFrame(scroll_frame, fg_color="gray15")
            tarjeta.pack(fill="x", pady=5, padx=5)
            
            lbl_tit = ctk.CTkLabel(tarjeta, text=p.concepto, font=ctk.CTkFont(weight="bold", size=13))
            lbl_tit.pack(anchor="w", padx=10, pady=(10, 0))
            
            txt_montos = f"Total: ${p.monto_total:,.0f} | Abonado: ${p.monto_abonado:,.0f}" 
            lbl_montos = ctk.CTkLabel(tarjeta, text=txt_montos, font=ctk.CTkFont(size=12), text_color="gray70")
            lbl_montos.pack(anchor="w", padx=10, pady=(2, 2))
            
            # Desglose de artículos y notas
            texto_detalles = ""
            if p.detalles:
                for det in p.detalles:
                    texto_detalles += f"  • {det.cantidad}x {det.descripcion} (${det.precio_unitario:,.0f} c/u)\n"
            
            if getattr(p, 'notas_internas', None):
                texto_detalles += f"  📝 Nota: {p.notas_internas}\n"
            
            if texto_detalles:
                lbl_desglose = ctk.CTkLabel(tarjeta, text=texto_detalles.strip(), font=ctk.CTkFont(size=11), text_color="#A9A9A9", justify="left")
                lbl_desglose.pack(anchor="w", padx=10, pady=(2, 5))
            
            # Semáforo individual
            liquidado = p.monto_abonado >= p.monto_total
            color_estado = "white" if liquidado else "#b8860b"
            icono = "☑" if liquidado else "⚠"
            texto_estado = "Liquidado" if liquidado else "Saldo Pendiente"
            
            txt_final = f"{p.mes_cubierto:02d}/{p.anio_cubierto} - {icono} {texto_estado}"
            lbl_estado = ctk.CTkLabel(tarjeta, text=txt_final, font=ctk.CTkFont(size=12), text_color=color_estado)
            lbl_estado.pack(anchor="e", padx=10, pady=(0, 10))
