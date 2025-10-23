# app/services/certificate_generator.py

from datetime import datetime
from typing import Dict, Any, Optional
from io import BytesIO
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    Frame,
    PageTemplate,
    BaseDocTemplate
)
from reportlab.pdfgen import canvas

from app.schemas.certificate import (
    DatosEstudianteCertificado,
    DatosProyectoCertificado,
    DatosEventoCertificado
)


class CertificateGenerator:
    """Generador de certificados PDF para ExpoSoftware"""
    
    # Configuración de firmas
    DIRECTOR_EVENTO_DEFAULT = "Dr. Roberto Carlos Pérez"
    COORDINADOR_GENERAL_DEFAULT = "Ing. Ana María González"
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()
    
    def _configurar_estilos(self):
        """Configura estilos personalizados para certificados"""
        
        # Estilo para el título principal
        self.styles.add(ParagraphStyle(
            name='TituloCertificado',
            parent=self.styles['Heading1'],
            fontSize=36,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=42
        ))
        
        # Estilo para "Certifica que"
        self.styles.add(ParagraphStyle(
            name='CertificaQue',
            parent=self.styles['Normal'],
            fontSize=16,
            textColor=colors.HexColor('#424242'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=20
        ))
        
        # Estilo para el nombre del estudiante
        self.styles.add(ParagraphStyle(
            name='NombreEstudiante',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=28
        ))
        
        # Estilo para información del proyecto
        self.styles.add(ParagraphStyle(
            name='InfoProyecto',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#424242'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=18
        ))
        
        # Estilo para firmas
        self.styles.add(ParagraphStyle(
            name='Firma',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#424242'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para cargo de firmas
        self.styles.add(ParagraphStyle(
            name='CargoFirma',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
    
    def generar_certificado(
        self,
        estudiante: DatosEstudianteCertificado,
        proyecto: DatosProyectoCertificado,
        evento: DatosEventoCertificado,
        incluir_calificacion: bool = False,
        director_evento: Optional[str] = None,
        coordinador_general: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Genera un certificado PDF de participación.
        
        Args:
            estudiante: Datos del estudiante
            proyecto: Datos del proyecto
            evento: Datos del evento
            incluir_calificacion: Si incluir la calificación
            director_evento: Nombre del director (opcional)
            coordinador_general: Nombre del coordinador (opcional)
            output_path: Ruta para guardar (opcional)
            
        Returns:
            BytesIO con el PDF generado
        """
        # Crear buffer
        buffer = BytesIO()
        
        # Crear documento en orientación horizontal
        doc = SimpleDocTemplate(
            buffer if not output_path else output_path,
            pagesize=landscape(letter),
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Contenedor de elementos
        elementos = []
        
        # Agregar borde decorativo
        elementos.extend(self._crear_encabezado_certificado(evento))
        
        # Agregar contenido principal
        elementos.extend(self._crear_contenido_certificado(
            estudiante=estudiante,
            proyecto=proyecto,
            evento=evento,
            incluir_calificacion=incluir_calificacion
        ))
        
        # Agregar firmas
        elementos.extend(self._crear_seccion_firmas(
            director_evento=director_evento,
            coordinador_general=coordinador_general,
            fecha_evento=evento.fecha_inicio
        ))
        
        # Construir PDF
        doc.build(elementos)
        
        # Retornar buffer
        if not output_path:
            buffer.seek(0)
            return buffer
        
        return None
    
    def _crear_encabezado_certificado(
        self,
        evento: DatosEventoCertificado
    ) -> list:
        """Crea el encabezado del certificado"""
        elementos = []
        
        # Logo de la universidad (si existe)
        # logo_path = "path/to/logo.png"
        # if os.path.exists(logo_path):
        #     logo = Image(logo_path, width=1*inch, height=1*inch)
        #     elementos.append(logo)
        
        elementos.append(Spacer(1, 0.3*inch))
        
        # Título de la institución
        elementos.append(Paragraph(
            "UNIVERSIDAD POPULAR DEL CESAR",
            self.styles['Normal']
        ))
        elementos.append(Paragraph(
            "Facultad de Ingeniería de Sistemas",
            self.styles['Normal']
        ))
        
        elementos.append(Spacer(1, 0.4*inch))
        
        # Título CERTIFICADO
        elementos.append(Paragraph(
            "CERTIFICADO",
            self.styles['TituloCertificado']
        ))
        
        elementos.append(Paragraph(
            f"DE PARTICIPACIÓN - {evento.nombre_evento}",
            self.styles['Normal']
        ))
        
        elementos.append(Spacer(1, 0.4*inch))
        
        return elementos
    
    def _crear_contenido_certificado(
        self,
        estudiante: DatosEstudianteCertificado,
        proyecto: DatosProyectoCertificado,
        evento: DatosEventoCertificado,
        incluir_calificacion: bool
    ) -> list:
        """Crea el contenido principal del certificado"""
        elementos = []
        
        # "Certifica que"
        elementos.append(Paragraph(
            "La Facultad de Ingeniería de Sistemas certifica que:",
            self.styles['CertificaQue']
        ))
        
        elementos.append(Spacer(1, 0.2*inch))
        
        # Nombre del estudiante
        nombre_completo = f"{estudiante.nombres} {estudiante.apellidos}"
        elementos.append(Paragraph(
            nombre_completo.upper(),
            self.styles['NombreEstudiante']
        ))
        
        # Identificación
        elementos.append(Paragraph(
            f"Identificado(a) con C.C. No. {estudiante.identificacion}",
            self.styles['InfoProyecto']
        ))
        
        elementos.append(Spacer(1, 0.3*inch))
        
        # Texto de participación
        texto_participacion = (
            f"Participó como <b>EXPOSITOR(A)</b> en {evento.nombre_evento}, "
            f"presentando el proyecto:"
        )
        elementos.append(Paragraph(
            texto_participacion,
            self.styles['InfoProyecto']
        ))
        
        elementos.append(Spacer(1, 0.1*inch))
        
        # Título del proyecto
        elementos.append(Paragraph(
            f'<b>"{proyecto.titulo_proyecto}"</b>',
            self.styles['InfoProyecto']
        ))
        
        # Tipo de actividad
        elementos.append(Paragraph(
            f"Modalidad: {proyecto.tipo_actividad.title()}",
            self.styles['InfoProyecto']
        ))
        
        # Calificación (si se incluye)
        if incluir_calificacion and proyecto.calificacion:
            elementos.append(Paragraph(
                f"Calificación obtenida: <b>{proyecto.calificacion}</b>",
                self.styles['InfoProyecto']
            ))
        
        elementos.append(Spacer(1, 0.2*inch))
        
        # Fecha del evento
        fecha_evento = evento.fecha_inicio.strftime("%d de %B de %Y")
        fecha_evento = self._formatear_fecha_espanol(evento.fecha_inicio)
        
        elementos.append(Paragraph(
            f"Realizado el {fecha_evento}",
            self.styles['InfoProyecto']
        ))
        
        if evento.lugar:
            elementos.append(Paragraph(
                f"en {evento.lugar}",
                self.styles['InfoProyecto']
            ))
        
        elementos.append(Spacer(1, 0.5*inch))
        
        return elementos
    
    def _crear_seccion_firmas(
        self,
        director_evento: Optional[str],
        coordinador_general: Optional[str],
        fecha_evento: datetime
    ) -> list:
        """Crea la sección de firmas"""
        elementos = []
        
        # Usar nombres por defecto si no se proporcionan
        director = director_evento or self.DIRECTOR_EVENTO_DEFAULT
        coordinador = coordinador_general or self.COORDINADOR_GENERAL_DEFAULT
        
        # Crear tabla para firmas
        datos_firmas = [
            ['_' * 40, '_' * 40],
            [director, coordinador],
            ['Director del Evento', 'Coordinador General']
        ]
        
        tabla_firmas = Table(
            datos_firmas,
            colWidths=[3.5*inch, 3.5*inch],
            rowHeights=[0.5*inch, 0.3*inch, 0.3*inch]
        )
        
        tabla_firmas.setStyle(TableStyle([
            # Alineación
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Líneas de firma
            ('LINEABOVE', (0, 1), (-1, 1), 1, colors.black),
            
            # Fuentes
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 11),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica'),
            ('FONTSIZE', (0, 2), (-1, 2), 9),
            
            # Colores
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#424242')),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#666666')),
            
            # Espaciado
            ('TOPPADDING', (0, 1), (-1, 2), 8),
            ('BOTTOMPADDING', (0, 1), (-1, 2), 4),
        ]))
        
        elementos.append(tabla_firmas)
        
        elementos.append(Spacer(1, 0.3*inch))
        
        # Fecha de expedición
        fecha_actual = datetime.now()
        fecha_expedicion = self._formatear_fecha_espanol(fecha_actual)
        
        elementos.append(Paragraph(
            f"<i>Expedido en Valledupar, {fecha_expedicion}</i>",
            self.styles['Normal']
        ))
        
        return elementos
    
    def _formatear_fecha_espanol(self, fecha: datetime) -> str:
        """Formatea una fecha en español"""
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        dia = fecha.day
        mes = meses[fecha.month]
        anio = fecha.year
        
        return f"{dia} de {mes} de {anio}"
    
    def obtener_nombre_archivo(self, estudiante: DatosEstudianteCertificado) -> str:
        """
        Genera el nombre del archivo del certificado.
        
        Args:
            estudiante: Datos del estudiante
            
        Returns:
            Nombre del archivo
        """
        nombre_limpio = f"{estudiante.nombres}_{estudiante.apellidos}".lower()
        nombre_limpio = nombre_limpio.replace(' ', '_')
        # Remover caracteres especiales
        nombre_limpio = ''.join(c for c in nombre_limpio if c.isalnum() or c == '_')
        
        return f"certificado_{nombre_limpio}.pdf"