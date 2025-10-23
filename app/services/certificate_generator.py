# app/services/certificate_generator.py

from typing import Optional
from io import BytesIO  # ✅ Añadir esta importación
from app.services.certificate_templates import CertificateTemplateFactory
from app.schemas.certificate import (
    DatosEstudianteCertificado, 
    DatosProyectoCertificado, 
    DatosEventoCertificado
)
import logging

logger = logging.getLogger(__name__)

class CertificateGenerator:
    """Generador de certificados que utiliza plantillas"""
    
    def __init__(self, template_name: str = "landscape"):
        """
        Inicializa el generador con una plantilla específica
        
        Args:
            template_name: Nombre de la plantilla ('landscape', 'modern')
        """
        self.template_name = template_name
        self.template_factory = CertificateTemplateFactory()
    
    def generar_certificado(
        self,
        estudiante: DatosEstudianteCertificado,
        proyecto: DatosProyectoCertificado,
        evento: DatosEventoCertificado,
        incluir_calificacion: bool = False,
        director_evento: Optional[str] = None,
        coordinador_general: Optional[str] = None
    ) -> BytesIO:
        """
        Genera un certificado usando la plantilla especificada
        """
        try:
            # Obtener la plantilla
            template = self.template_factory.get_template(self.template_name)
            
            # Generar el certificado
            pdf_buffer = template.generar_certificado(
                estudiante=estudiante,
                proyecto=proyecto,
                evento=evento,
                incluir_calificacion=incluir_calificacion,
                director_evento=director_evento,
                coordinador_general=coordinador_general
            )
            
            logger.info(f"✅ Certificado generado con plantilla: {self.template_name}")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"❌ Error generando certificado: {e}")
            raise
    
    def obtener_nombre_archivo(self, estudiante: DatosEstudianteCertificado) -> str:
        """Genera un nombre de archivo para el certificado"""
        nombre_limpio = f"{estudiante.nombres}_{estudiante.apellidos}".lower()
        nombre_limpio = nombre_limpio.replace(' ', '_')
        # Remover caracteres especiales
        nombre_limpio = ''.join(c for c in nombre_limpio if c.isalnum() or c == '_')
        
        return f"certificado_{nombre_limpio}.pdf"
    
    def set_template(self, template_name: str):
        """Cambia la plantilla a utilizar"""
        self.template_name = template_name
        logger.info(f"🔄 Plantilla cambiada a: {template_name}")
    
    def get_available_templates(self) -> list:
        """Retorna la lista de plantillas disponibles"""
        return ["landscape", "modern"]