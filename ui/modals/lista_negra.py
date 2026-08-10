# ui/modals/lista_negra.py
"""
Módulo responsable de la interfaz gráfica y la lógica de negocio para la 
gestión de morosos. Incluye la generación de reportes y el envío automatizado 
de correos electrónicos mediante SMTP.
"""

import customtkinter as ctk
from tkinter import messagebox
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from domain.models import Casa
from domain.business_rules import evaluar_estado_financiero

class VentanaListaNegra(ctk.CTkToplevel):
    """
    Ventana emergente (Modal) que escanea la base de datos en busca de viviendas
    con estado 'Restringido', genera un reporte visual de dispositivos a revocar
    y permite enviar dicho reporte a un administrador vía correo electrónico.
    """
    
    def __init__(self, master, db_session):
        """
        Inicializa la ventana modal y bloquea la interacción con la aplicación principal.
        
        Args:
            master: La ventana o frame padre que invoca este modal.
            db_session: Sesión activa de SQLAlchemy para consultas a la BD.
        """
        super().__init__(master)
        self.db_session = db_session
        
        # 1. Configuración base de la ventana
        self.title("Lista Negra de Morosos")
        self.geometry("700x600")
        self.transient(master.winfo_toplevel())
        self.grab_set()
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 2. Construcción de la cabecera y controles de envío
        frame_top = ctk.CTkFrame(self, fg_color="transparent")
        frame_top.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        
        ctk.CTkLabel(frame_top, text="Lista Definitiva de Suspensión", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        
        self.ent_correo = ctk.CTkEntry(frame_top, placeholder_text="correo_admin@gmail.com", width=200)
        self.ent_correo.pack(side="left", padx=(20, 10))
        
        btn_enviar = ctk.CTkButton(frame_top, text="Enviar Reporte", fg_color="#1f6aa5", command=self.enviar_correo)
        btn_enviar.pack(side="left")

        # 3. Área de visualización dinámica
        self.scroll_lista = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_lista.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Variable string que almacenará el cuerpo del correo a enviar
        self.texto_reporte = "🚨 REPORTE DE SUSPENSIÓN - REJA AUTOMATIZADA 🚨\n\n"
        
        # 4. Disparador de análisis de datos
        self.generar_lista()

    def generar_lista(self):
        """
        Consulta todas las viviendas en la base de datos, evalúa su estado
        financiero y renderiza tarjetas visuales para aquellas con adeudos. 
        Construye simultáneamente el texto plano para el reporte SMTP.
        """
        todas_las_casas = self.db_session.query(Casa).all()
        hay_morosos = False
        
        # 1. Iteración y filtrado de morosos
        for casa in todas_las_casas:
            estado_financiero, _, deuda = evaluar_estado_financiero(casa)
            
            if estado_financiero == "🛑 Restringido":
                hay_morosos = True
                
                # 2. Construcción de la tarjeta UI
                tarjeta = ctk.CTkFrame(self.scroll_lista, fg_color="#4A1010")
                tarjeta.pack(fill="x", pady=5)
                
                if deuda > 0:
                    texto_tit = f"Hogar {casa.lote.numero}-{casa.numero_interior} (Deuda: ${deuda:,.0f})"
                else:
                    texto_tit = f"Hogar {casa.lote.numero}-{casa.numero_interior} (Falta de Mantenimiento)"
                    
                ctk.CTkLabel(tarjeta, text=texto_tit, font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
                
                # 3. Anexar datos al cuerpo del correo electrónico
                self.texto_reporte += f"🏠 {texto_tit}\n"

                # 4. Extracción y formateo de dispositivos afectados
                correos = [d.identificador_hardware for d in casa.dispositivos if d.tipo_dispositivo == "WIFI_PERMIT"]
                rfids = [d.identificador_hardware.replace('RFID-', '') for d in casa.dispositivos if d.tipo_dispositivo == "RFID"]
                
                if correos:
                    f_mails = ctk.CTkFrame(tarjeta, fg_color="transparent")
                    f_mails.pack(fill="x", padx=10, pady=2)
                    ctk.CTkLabel(f_mails, text="Correos a revocar:").pack(side="left")
                    
                    for c in correos:
                        self.texto_reporte += f"  ✉️ {c}\n"
                        btn = ctk.CTkButton(f_mails, text=f"Copiar: {c}", height=20, width=150, font=ctk.CTkFont(size=11), fg_color="gray30",
                                            command=lambda mail=c: self.copiar_texto(mail))
                        btn.pack(side="left", padx=5)

                if rfids:
                    txt_chips = f"Chips a desactivar: {', '.join(rfids)}"
                    ctk.CTkLabel(tarjeta, text=txt_chips).pack(anchor="w", padx=10, pady=(2, 5))
                    self.texto_reporte += f"  🏷️ {txt_chips}\n"
                    
                self.texto_reporte += "-"*30 + "\n"

        # 5. Manejo de estado vacío (Todo en orden)
        if not hay_morosos:
            ctk.CTkLabel(self.scroll_lista, text="No hay casas en estado Restringido.", font=ctk.CTkFont(size=14)).pack(pady=20)
            self.texto_reporte += "No hay acciones pendientes. Todos los vecinos están al corriente."

    def copiar_texto(self, texto):
        """
        Limpia el portapapeles del sistema operativo y anexa el texto seleccionado.
        """
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.update()

    def enviar_correo(self):
        """
        Autentica la sesión con los servidores de Google y despacha el reporte 
        de suspensión en formato de texto plano al correo destino.
        """
        destinatario = self.ent_correo.get().strip()
        
        # 1. Validación de captura
        if not destinatario:
            messagebox.showwarning("Dato Requerido", "Ingrese el correo destino para enviar la lista.")
            return

        # 2. Credenciales del sistema
        remitente = "reja10cedros@gmail.com" 
        password_app = "wniajllwisspzzvc" 
        
        try:
            # 3. Estructuración del paquete MIME
            msg = MIMEMultipart()
            msg['From'] = remitente
            msg['To'] = destinatario
            msg['Subject'] = "Lista Negra - Auditoría IoT Reja"
            
            cuerpo = MIMEText(self.texto_reporte, 'plain', 'utf-8')
            msg.attach(cuerpo)
            
            # 4. Handshake y transmisión SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(remitente, password_app)
            server.send_message(msg)
            server.quit()
            
            messagebox.showinfo("Transmisión Exitosa", f"El reporte fue enviado a ({destinatario}) correctamente.")
            
        except Exception as e:
            messagebox.showerror("Fallo de Transmisión", f"Error al despachar el correo SMTP: {e}")