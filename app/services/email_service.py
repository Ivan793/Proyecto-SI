import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional, Union
from datetime import datetime
from io import BytesIO
import os
import logging

logger = logging.getLogger(__name__)


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
        
        logger.info(f"📧 EmailService inicializado - Server: {self.smtp_server}:{self.smtp_port}")
    
    async def enviar_con_adjunto(
        self,
        destinatario: str,
        asunto: str,
        cuerpo_html: str,
        nombre_adjunto: str,
        contenido_adjunto: bytes,
        tipo_adjunto: str = 'application/pdf'
    ) -> dict:
        """
        Envía un correo con un adjunto (usado para certificados individuales).
        
        Args:
            destinatario: Email del destinatario
            asunto: Asunto del correo
            cuerpo_html: Cuerpo del correo en HTML
            nombre_adjunto: Nombre del archivo adjunto
            contenido_adjunto: Contenido del archivo en bytes
            tipo_adjunto: Tipo MIME del adjunto
            
        Returns:
            Diccionario con información del envío
        """
        try:
            logger.info(f"📤 Enviando certificado a: {destinatario}")
            
            # Validar configuración
            if not self.validar_configuracion():
                raise ValueError("Configuración de email incompleta. Verifica las variables de entorno.")
            
            # Crear mensaje
            mensaje = MIMEMultipart()
            mensaje['From'] = self.from_email
            mensaje['To'] = destinatario
            mensaje['Subject'] = asunto
            mensaje['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Agregar cuerpo HTML
            mensaje.attach(MIMEText(cuerpo_html, 'html'))
            
            # Adjuntar archivo
            adjunto = MIMEApplication(contenido_adjunto, _subtype=tipo_adjunto.split('/')[-1])
            adjunto.add_header(
                'Content-Disposition',
                'attachment',
                filename=nombre_adjunto
            )
            mensaje.attach(adjunto)
            
            # Enviar correo
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as servidor:
                servidor.starttls()
                servidor.login(self.smtp_user, self.smtp_password)
                servidor.send_message(mensaje)
            
            logger.info(f"✅ Correo enviado exitosamente a {destinatario}")
            
            return {
                'exitoso': True,
                'enviado_a': destinatario,
                'fecha_envio': datetime.now().isoformat(),
                'mensaje': 'Correo enviado exitosamente'
            }
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Error de autenticación SMTP: {str(e)}")
            return {
                'exitoso': False,
                'error': 'Error de autenticación. Verifica usuario y contraseña SMTP.',
                'mensaje': 'Error de autenticación con el servidor de correo'
            }
        except smtplib.SMTPException as e:
            logger.error(f"❌ Error SMTP: {str(e)}")
            return {
                'exitoso': False,
                'error': str(e),
                'mensaje': 'Error al enviar el correo'
            }
        except Exception as e:
            logger.error(f"❌ Error inesperado: {str(e)}")
            return {
                'exitoso': False,
                'error': str(e),
                'mensaje': 'Error inesperado al enviar el correo'
            }
    
    async def enviar_certificados_masivo(
        self,
        certificados: List[dict],
        asunto_base: str = "Tu Certificado de Participación - ExpoSoftware",
        mensaje_personalizado: Optional[str] = None
    ) -> dict:
        """
        Envía certificados de forma masiva a múltiples estudiantes.
        
        Args:
            certificados: Lista de diccionarios con estructura:
                - correo: Email del estudiante
                - nombre: Nombre del estudiante
                - nombre_archivo: Nombre del archivo PDF
                - contenido: BytesIO con el PDF
            asunto_base: Asunto base del correo
            mensaje_personalizado: Mensaje adicional personalizado
            
        Returns:
            Diccionario con estadísticas del envío
        """
        exitosos = []
        fallidos = []
        
        logger.info(f"📨 Iniciando envío masivo de {len(certificados)} certificados")
        
        for cert in certificados:
            try:
                correo = cert['correo']
                nombre = cert['nombre']
                nombre_archivo = cert['nombre_archivo']
                contenido = cert['contenido']
                
                # Construir mensaje HTML personalizado
                cuerpo_html = self._construir_cuerpo_certificado(
                    nombre_estudiante=nombre,
                    mensaje_personalizado=mensaje_personalizado
                )
                
                # Enviar certificado
                resultado = await self.enviar_con_adjunto(
                    destinatario=correo,
                    asunto=asunto_base,
                    cuerpo_html=cuerpo_html,
                    nombre_adjunto=nombre_archivo,
                    contenido_adjunto=contenido,
                    tipo_adjunto='application/pdf'
                )
                
                if resultado['exitoso']:
                    exitosos.append({
                        'correo': correo,
                        'nombre': nombre,
                        'fecha_envio': resultado['fecha_envio']
                    })
                    logger.info(f"✅ Enviado a: {nombre} ({correo})")
                else:
                    fallidos.append({
                        'correo': correo,
                        'nombre': nombre,
                        'error': resultado.get('error', 'Error desconocido')
                    })
                    logger.error(f"❌ Fallo envío a: {nombre} ({correo})")
                    
            except Exception as e:
                logger.error(f"❌ Error procesando certificado para {cert.get('correo', 'desconocido')}: {str(e)}")
                fallidos.append({
                    'correo': cert.get('correo', 'desconocido'),
                    'nombre': cert.get('nombre', 'desconocido'),
                    'error': str(e)
                })
        
        total = len(certificados)
        logger.info(f"📊 Resumen: {len(exitosos)}/{total} exitosos, {len(fallidos)}/{total} fallidos")
        
        return {
            'total': total,
            'exitosos': len(exitosos),
            'fallidos': len(fallidos),
            'detalles_exitosos': exitosos,
            'detalles_fallidos': fallidos,
            'fecha_envio': datetime.now().isoformat()
        }
    
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
    
    def _construir_cuerpo_certificado(
        self,
        nombre_estudiante: str,
        mensaje_personalizado: Optional[str] = None
    ) -> str:
        """
        Construye el cuerpo HTML del correo para certificados.
        
        Args:
            nombre_estudiante: Nombre del estudiante
            mensaje_personalizado: Mensaje adicional personalizado
            
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
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background-color: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #0d5028 0%, #2d8f4d 100%);
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header p {{
                    margin: 5px 0 0 0;
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 18px;
                    color: #0d5028;
                    margin-bottom: 20px;
                }}
                .message {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #0d5028;
                }}
                .highlight {{
                    background-color: #fff3cd;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #ffd700;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #0d5028;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .icon {{
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="icon">🎓</div>
                    <h1>ExpoSoftware</h1>
                    <p>Facultad de Ingeniería de Sistemas</p>
                </div>
                <div class="content">
                    <p class="greeting">Estimado(a) <strong>{nombre_estudiante}</strong>,</p>
                    
                    <div class="message">
                        <p>¡Felicitaciones! Adjunto encontrarás tu <strong>Certificado de Participación</strong> en ExpoSoftware.</p>
                        {f'<p style="margin-top: 15px;">{mensaje_personalizado}</p>' if mensaje_personalizado else ''}
                    </div>
                    
                    <div class="highlight">
                        <p style="margin: 0;">
                            📄 <strong>El certificado está adjunto en formato PDF</strong><br>
                            Puedes descargarlo e imprimirlo cuando lo necesites.
                        </p>
                    </div>
                    
                    <p>Este certificado valida tu participación y el esfuerzo dedicado a tu proyecto.</p>
                    
                    <p style="margin-top: 30px;">
                        <strong>¡Gracias por ser parte de ExpoSoftware!</strong>
                    </p>
                </div>
                <div class="footer">
                    <p>
                        <strong>Universidad Popular del Cesar</strong><br>
                        Facultad de Ingeniería de Sistemas<br>
                        Este es un correo automático, por favor no responder.
                    </p>
                    <p style="margin-top: 10px; color: #999;">
                        © {datetime.now().year} ExpoSoftware - Todos los derechos reservados
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _construir_cuerpo_email(self, mensaje_personalizado: str) -> str:
        """
        Construye el cuerpo HTML del correo para reportes.
        
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
                        🔎 Revise el archivo adjunto para ver el reporte completo.
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
        valido = all([
            self.smtp_server,
            self.smtp_port,
            self.smtp_user,
            self.smtp_password,
            self.from_email
        ])
        
        if not valido:
            logger.warning("⚠️ Configuración de email incompleta")
            logger.debug(f"SMTP_SERVER: {bool(self.smtp_server)}")
            logger.debug(f"SMTP_PORT: {bool(self.smtp_port)}")
            logger.debug(f"SMTP_USER: {bool(self.smtp_user)}")
            logger.debug(f"SMTP_PASSWORD: {bool(self.smtp_password)}")
            logger.debug(f"FROM_EMAIL: {bool(self.from_email)}")
        
        return valido
    
    async def probar_conexion(self) -> dict:
        """
        Prueba la conexión con el servidor SMTP.
        
        Returns:
            Diccionario con el resultado de la prueba
        """
        try:
            logger.info("🔍 Probando conexión SMTP...")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as servidor:
                servidor.starttls()
                servidor.login(self.smtp_user, self.smtp_password)
            
            logger.info("✅ Conexión SMTP exitosa")
            
            return {
                'exitoso': True,
                'mensaje': 'Conexión exitosa con el servidor SMTP'
            }
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Error de autenticación: {str(e)}")
            return {
                'exitoso': False,
                'error': str(e),
                'mensaje': 'Error de autenticación. Verifica usuario y contraseña.'
            }
        except Exception as e:
            logger.error(f"❌ Error de conexión: {str(e)}")
            return {
                'exitoso': False,
                'error': str(e),
                'mensaje': 'Error al conectar con el servidor SMTP'
            }