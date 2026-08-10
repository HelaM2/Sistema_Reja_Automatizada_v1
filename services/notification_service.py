# services/notification_service.py
"""
Capa de Servicios: Enrutamiento y Envío de Notificaciones (El Cartero).
Gestiona la comunicación unidireccional con los residentes vía correo 
electrónico (SMTP). Se encarga de enviar recibos de pago, avisos de 
auditoría (bloqueos/reactivaciones) y manuales de instalación.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

class NotificationService:
    """
    Servicio dedicado al ensamblaje y transmisión de correos electrónicos.
    Soporta inyección de HTML dinámico y adjuntos de múltiples formatos (PDF, Imágenes).
    """

    def __init__(self):
        """
        Inicializa el servicio configurando las credenciales de autenticación SMTP.
        """
        # 🚨 Asegúrate de usar tu contraseña real en producción 🚨
        self.remitente = "reja10cedros@gmail.com"
        self.password_app = "wniajllwisspzzvc"

    def _enviar_correo_base(self, destinatario: str, asunto: str, mensaje_html: str, ruta_adjunto: str = None) -> tuple:
        """
        Motor principal de transmisión SMTP. Filtra correos inválidos, ensambla 
        el paquete MIME y despacha el mensaje al servidor de Google.
        
        Args:
            destinatario (str): Correo electrónico del residente.
            asunto (str): Título del correo.
            mensaje_html (str): Cuerpo del mensaje con formato HTML.
            ruta_adjunto (str, optional): Ruta absoluta o relativa hacia un archivo a adjuntar.
            
        Returns:
            tuple: (bool, str) Indicando el éxito/fracaso y un mensaje descriptivo.
        """
        # 1. Filtro de seguridad para correos no registrados o nulos
        if not destinatario or destinatario.strip() in ["S/R", "nan", ""]:
            return False, "Sin correo registrado (S/R). Operación ignorada."

        try:
            # 2. Ensamblaje de la cabecera del correo
            msg = MIMEMultipart()
            msg['From'] = f"Administración Reja 10 Cedros <{self.remitente}>"
            msg['To'] = destinatario
            msg['Subject'] = asunto
            
            # 3. Inyección del cuerpo HTML
            msg.attach(MIMEText(mensaje_html, 'html', 'utf-8'))
            
            # 4. Procesamiento de archivos adjuntos (I/O)
            if ruta_adjunto and os.path.exists(ruta_adjunto):
                with open(ruta_adjunto, 'rb') as f:
                    file_data = f.read()
                
                nombre_archivo = os.path.basename(ruta_adjunto)
                
                # Detección y empaquetado por extensión
                if nombre_archivo.lower().endswith('.pdf'):
                    adjunto = MIMEApplication(file_data, Name=nombre_archivo)
                    adjunto['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
                    msg.attach(adjunto)
                else:
                    # Fallback a formato de imagen para comprobantes de pago
                    adjunto = MIMEImage(file_data, name=nombre_archivo)
                    msg.attach(adjunto)
            
            # 5. Handshake y transmisión SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.remitente, self.password_app)
            server.send_message(msg)
            server.quit()
            
            return True, "Notificación enviada con éxito."
        except Exception as e:
            return False, f"Error al enviar: {str(e)}"    
    
    # ========================================================
    # 1. PLANTILLAS TRANSACCIONALES (DISPOSITIVOS Y FINANZAS)
    # ========================================================
    
    def notificar_edicion_dispositivo(self, destinatario: str, hogar: str, nuevo_dispositivo: str, tipo: str) -> tuple:
        """
        Informa al residente sobre la modificación de un identificador de hardware/software.
        """
        asunto = "Actualización de Dispositivo - Reja 10 Cedros"
        html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2 style="color: #b8860b;">Actualización de Dispositivo</h2>
            <p>Estimado residente del <b>Hogar {hogar}</b>,</p>
            <p>Le informamos que el registro de su dispositivo ha sido modificado en el sistema:</p>
            <ul>
                <li><b>Tipo de Acceso:</b> {tipo}</li>
                <li><b>Nuevo Identificador Activo:</b> {nuevo_dispositivo}</li>
            </ul>
            <p>El acceso ya se encuentra operativo con este nuevo registro.</p>
            <hr style="border: 1px solid #eee;">
            <p style="font-size: 12px; color: #777;">Este es un mensaje automático generado por el Sistema de Administración.</p>
        </div>
        """
        return self._enviar_correo_base(destinatario, asunto, html)
    
    def notificar_baja_dispositivo(self, destinatario: str, hogar: str, dispositivo: str) -> tuple:
        """
        Alerta al residente sobre la revocación permanente de un dispositivo del sistema.
        """
        asunto = "Dispositivo Dado de Baja - Reja 10 Cedros"
        html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2 style="color: #8B0000;">Baja de Dispositivo</h2>
            <p>Estimado residente del <b>Hogar {hogar}</b>,</p>
            <p>Le informamos que el siguiente dispositivo ha sido <b>eliminado y desactivado</b> de nuestro sistema de acceso:</p>
            <ul>
                <li><b>Identificador Revocado:</b> {dispositivo}</li>
            </ul>
            <p>Este dispositivo ya no podrá abrir la reja automatizada.</p>
            <hr style="border: 1px solid #eee;">
            <p style="font-size: 12px; color: #777;">Este es un mensaje automático generado por el Sistema de Administración.</p>
        </div>
        """
        return self._enviar_correo_base(destinatario, asunto, html)

    def notificar_pago(self, destinatario: str, hogar: str, concepto: str, total: float, abonado: float, detalles: list, ruta_adjunto: str = None) -> tuple:
        """
        Genera y envía un recibo electrónico detallado tras el registro de un pago en la base de datos.
        """
        # 1. Evaluación del estado financiero de la transacción
        estado_pago = "☑ LIQUIDADO" if abonado >= total else "⚠️ PAGO PARCIAL"
        color_estado = "#104A20" if abonado >= total else "#b8860b"
        
        # 2. Renderizado dinámico del carrito de compras
        filas_html = ""
        for item in detalles:
            filas_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{item['cant']}x {item['desc']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${item['sub']:,.2f}</td>
            </tr>
            """

        asunto = f"Recibo de Pago: {concepto} - Hogar {hogar}"
        html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">
            <h2 style="color: #1f6aa5; border-bottom: 2px solid #1f6aa5; padding-bottom: 10px;">Recibo Electrónico</h2>
            <p>Estimado responsable del <b>Hogar {hogar}</b>,</p>
            <p>Hemos registrado un pago en su estado de cuenta bajo el concepto de <b>{concepto}</b>.</p>
            
            <h3 style="color: {color_estado};">{estado_pago}</h3>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px; background-color: #f9f9fa;">
                <thead>
                    <tr style="background-color: #eee;">
                        <th style="padding: 8px; text-align: left;">Artículo / Descripción</th>
                        <th style="padding: 8px; text-align: right;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                </tbody>
                <tfoot>
                    <tr>
                        <td style="padding: 8px; font-weight: bold; text-align: right;">Total a Pagar:</td>
                        <td style="padding: 8px; font-weight: bold; text-align: right;">${total:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold; text-align: right; color: #104A20;">Monto Recibido:</td>
                        <td style="padding: 8px; font-weight: bold; text-align: right; color: #104A20;">${abonado:,.2f}</td>
                    </tr>
                </tfoot>
            </table>
            <p style="margin-top: 20px;"><i>Si usted proporcionó un comprobante (foto o captura), este ha sido adjuntado a este correo.</i></p>
            <hr style="border: 1px solid #eee;">
            <p style="font-size: 12px; color: #777;">Este es un documento de control interno sin validez fiscal oficial.</p>
        </div>
        """
        return self._enviar_correo_base(destinatario, asunto, html, ruta_adjunto)

    def notificar_nuevo_wifi(self, destinatario: str, hogar: str) -> tuple:
        """
        Despacha el correo de bienvenida a nuevos usuarios de la App Tuya Smart Life.
        Incluye instrucciones precisas y enlaza el Manual de Usuario en PDF.
        """
        asunto = "Guía de Instalación: Acceso Vehicular Smart Life - Reja 10 Cedros"
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
            <div style="background-color: #f8fafc; padding: 20px; border-bottom: 1px solid #e2e8f0;">
                <h2 style="margin: 0; color: #0f172a; font-size: 18px;">Activación de Acceso Móvil</h2>
                <p style="margin: 5px 0 0 0; color: #64748b; font-size: 14px;">Unidad: {hogar}</p>
            </div>
            
            <div style="padding: 20px;">
                <p style="color: #334155; font-size: 14px; margin-top: 0;">Estimado residente,</p>
                <p style="color: #334155; font-size: 14px;">Le informamos que este correo electrónico se ha registrado en el sistema central para operar la reja automatizada de la privada.</p>
                
                <div style="background-color: #f1f5f9; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #0f172a; font-size: 15px;">Pasos para activar su acceso:</h3>
                    <ol style="color: #475569; font-size: 14px; padding-left: 20px; margin-bottom: 0;">
                        <li style="margin-bottom: 10px;">Descargue la aplicación <strong>Smart Life</strong> desde su tienda de aplicaciones (iOS o Android).</li>
                        <li style="margin-bottom: 10px;">Cree una cuenta nueva o inicie sesión utilizando <strong>exactamente este correo electrónico</strong>. <i>(Si utiliza un correo distinto, la reja no abrirá)</i>.</li>
                        <li style="margin-bottom: 10px;">Dentro de la app, vaya a la opción inferior <strong>"Yo"</strong> > <strong>"Gestión del hogar"</strong> y guarde su entorno con el nombre <strong>"Mi Casa"</strong>.</li>
                        <li>Regrese a la pestaña principal de <strong>"Mi hogar"</strong>, seleccione <strong>"Gestión de dispositivos"</strong> en la parte superior y presione "Agregar al hogar" en el portón que le aparecerá en pantalla.</li>
                    </ol>
                </div>
                
                <p style="color: #475569; font-size: 13px;"><i>Si tiene alguna duda, no le aparece el portón o se atasca en algún paso, <strong>por favor consulte el Manual de Usuario en PDF adjunto</strong> a este correo, donde encontrará las instrucciones con imágenes detalladas de cada pantalla.</i></p>
                
                <!-- CAJA DE ADVERTENCIA: USO DE DATOS -->
                <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px; margin-top: 20px; font-size: 13px; color: #92400e;">
                    <strong>⚠️ Aviso de Uso Responsable:</strong><br>
                    La reja funciona mediante un chip de datos móviles financiado por el mantenimiento vecinal. Le pedimos <b>tocar el botón virtual una sola vez</b> (la reja responderá automáticamente). Presionarlo múltiples veces de forma innecesaria agota los datos del sistema rápidamente, lo cual obligaría a contratar un plan más costoso y generaría un aumento en la cuota de mantenimiento para todos.
                </div>
                
                <!-- CAJA DE NOTA: PAGOS -->
                <div style="background-color: #f8fafc; border-left: 4px solid #94a3b8; padding: 12px; margin-top: 15px; font-size: 13px; color: #475569;">
                    <strong>Nota administrativa:</strong> El acceso solo será válido mientras el hogar se encuentre al corriente con sus pagos de mantenimiento.
                </div>
                
            </div>
            <div style="background-color: #f8fafc; padding: 15px 20px; border-top: 1px solid #e2e8f0; text-align: center;">
                <p style="margin: 0; font-size: 11px; color: #94a3b8;">Mensaje generado automáticamente por el Sistema de Control.<br>No responda a esta dirección de correo.</p>
            </div>
        </div>
        """
        
        # Anclaje de ruta para el documento adjunto
        ruta_pdf = os.path.join("manual_usuario", "manual_usuario.pdf")
        
        return self._enviar_correo_base(destinatario, asunto, html, ruta_adjunto=ruta_pdf)

    # ========================================================
    # 2. PLANTILLAS DE AUDITORÍA Y SINCRONIZACIÓN (TUYA)
    # ========================================================

    def notificar_bloqueo(self, destinatario: str, hogar: str) -> tuple:
        """
        Informa al residente sobre la suspensión temporal de sus permisos físicos y digitales por adeudo.
        """
        asunto = "Suspensión de Accesos (Aviso Administrativo)"
        html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2 style="color: #8B0000;">Aviso de Suspensión Temporal</h2>
            <p>Estimado residente del <b>Hogar {hogar}</b>,</p>
            <p>Le informamos que debido a una falta de renovación en el servicio de mantenimiento, sus privilegios de acceso (App y Chips) han sido <b>suspendidos</b>.</p>
            <p>Para reactivar sus dispositivos, le solicitamos amablemente regularizar su estado de cuenta a la brevedad. Una vez registrado el pago, el sistema restablecerá sus accesos automáticamente.</p>
            <hr style="border: 1px solid #eee;">
            <p style="font-size: 12px; color: #777;">Si considera que esto es un error, por favor contacte a la administración.</p>
        </div>
        """
        return self._enviar_correo_base(destinatario, asunto, html)

    def notificar_reactivacion(self, destinatario: str, hogar: str) -> tuple:
        """
        Comunica al residente el restablecimiento total de sus permisos de acceso a la cerrada.
        """
        asunto = "Accesos Restablecidos - Reja 10 Cedros"
        html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2 style="color: #104A20;">Accesos Restablecidos</h2>
            <p>Estimado residente del <b>Hogar {hogar}</b>,</p>
            <p>Le confirmamos que su estado de cuenta se encuentra regularizado. <b>Todos sus accesos (App y Chips) han sido restablecidos</b> y operan con normalidad.</p>
            <p>Gracias por su valioso apoyo al proyecto vecinal.</p>
            <hr style="border: 1px solid #eee;">
            <p style="font-size: 12px; color: #777;">Este es un mensaje automático generado por el Sistema de Administración.</p>
        </div>
        """
        return self._enviar_correo_base(destinatario, asunto, html)