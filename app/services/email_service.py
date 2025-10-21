
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional, Union
from datetime import datetime
from io import BytesIO
import os


class EmailService:
    """Servicio para envío de correos electrónicos"""
    
    def __init__(
        self,
        smtp_server: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        from_email: str = None
    ):
        """
        Inicializa el servicio de correo.
        
        Args:
            smtp_server: Servidor SMTP
            smtp_port: Puerto SMTP
            smtp_user: Usuario SMTP
            smtp_password: Contraseña SMTP
            from_email: Email remitente
        """
        # Obtener configuración de variables de entorno o parámetros
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD')
        self.from_email = from_email or os.getenv('FROM_EMAIL') or self.smtp_user
    
    async def enviar_reporte(
        self,
        destinatarios: Union[str, List[str]],
        asunto: str,
        nombre_archivo: str,
        contenido_pdf: BytesIO,
        mensaje_personalizado: Optional[str] = None,
        copias: Optional[List[str]] = None,
        copias_ocultas: Optional[List[str]] = None
    ) -> dict:
        """
        Envía un reporte PDF por correo electrónico.
        
        Args:
            destinatarios: Email(s) de destino
            asunto: Asunto del correo
            nombre_archivo: Nombre del archivo PDF
            contenido_pdf: BytesIO con el contenido del PDF
            mensaje_personalizado: Mensaje adicional en el cuerpo
            copias: Lista de emails en copia (CC)
            copias_ocultas: Lista de emails en copia oculta (BCC)
            
        Returns:
            Diccionario con información del envío
        """
        # Normalizar destinatarios a lista
        if isinstance(destinatarios, str):
            destinatarios = [destinatarios]
        
        # Crear mensaje
        mensaje = MIMEMultipart()
        mensaje['From'] = self.from_email
        mensaje['To'] = ', '.join(destinatarios)
        mensaje['Subject'] = asunto
        mensaje['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        # Agregar copias si existen
        if copias:
            mensaje['Cc'] = ', '.join(copias)
        
        # Construir cuerpo del correo
        cuerpo_html = self._construir_cuerpo_email(
            mensaje_personalizado or "Adjunto encontrará el reporte solicitado."
        )
        
        mensaje.attach(MIMEText(cuerpo_html, 'html'))
        
        # Adjuntar PDF
        contenido_pdf.seek(0)
        adjunto = MIMEApplication(contenido_pdf.read(), _subtype='pdf')
        adjunto.add_header(
            'Content-Disposition',
            'attachment',
            filename=nombre_archivo
        )
        mensaje.attach(adjunto)
        
        # Preparar lista completa de destinatarios
        todos_destinatarios = destinatarios.copy()
        if copias:
            todos_destinatarios.extend(copias)
        if copias_ocultas:
            todos_destinatarios.extend(copias_ocultas)
        
        # Enviar correo
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as servidor:
                servidor.starttls()
                servidor.login(self.smtp_user, self.smtp_password)
                servidor.send_message(mensaje)
            
            return {
                'exitoso': True,
                'enviado_a': destinatarios,
                'fecha_envio': datetime.now().isoformat(),
                'mensaje': 'Correo enviado exitosamente'
            }
            
        except smtplib.SMTPException as e:
            return {
                'exitoso': False,
                'error': str(e),
                'mensaje': 'Error al enviar el correo'
            }
        except Exception as e:
            return {
                'exitoso': False,
                'error': str(e),
                'mensaje': 'Error inesperado al enviar el correo'
            }
    
    def _construir_cuerpo_email(self, mensaje_personalizado: str) -> str:
        """
        Construye el cuerpo HTML del correo.
        
        Args:
            mensaje_personalizado: Mensaje del usuario
            
        Returns:
            HTML del cuerpo del correo
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #1976d2;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f5f5f5;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .mensaje {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                    border-left: 4px solid #1976d2;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                }}
                .destacado {{
                    color: #1976d2;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ExpoSoftware</h1>
                    <p>Facultad de Ingeniería de Sistemas</p>
                </div>
                <div class="content">
                    <h2>Reporte de Proyectos</h2>
                    <div class="mensaje">
                        <p>{mensaje_personalizado}</p>
                    </div>
                    <p>
                        El archivo PDF adjunto contiene la información detallada 
                        solicitada sobre los proyectos de ExpoSoftware.
                    </p>
                    <p class="destacado">
                        📎 Revise el archivo adjunto para ver el reporte completo.
                    </p>
                    <div class="footer">
                        <p>
                            Este es un correo automático generado por el Sistema ExpoSoftware.<br>
                            Universidad Popular del Cesar - {datetime.now().year}
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def validar_configuracion(self) -> bool:
        """
        Valida que la configuración SMTP esté completa.
        
        Returns:
            True si la configuración es válida
        """
        return all([
            self.smtp_server,
            self.smtp_port,
            self.smtp_user,
            self.smtp_password,
            self.from_email
        ])
    
    async def probar_conexion(self) -> dict:
        """
        Prueba la conexión con el servidor SMTP.
        
        Returns:
            Diccionario con el resultado de la prueba
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as servidor:
                servidor.starttls()
                servidor.login(self.smtp_user, self.smtp_password)
            
            return {
                'exitoso': True,
                'mensaje': 'Conexión exitosa con el servidor SMTP'
            }
        except Exception as e:
            return {
                'exitoso': False,
                'error': str(e),
                'mensaje': 'Error al conectar con el servidor SMTP'
            }