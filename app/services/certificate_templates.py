# app/services/certificate_templates.py

from datetime import datetime
from typing import Optional
from io import BytesIO
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.pdfgen import canvas

from app.schemas.certificate import (
    DatosEstudianteCertificado,
    DatosProyectoCertificado,
    DatosEventoCertificado
)


class BaseCertificateTemplate:
    """Plantilla base para certificados"""
    
    # Configuración de firmas por defecto
    DIRECTOR_EVENTO_DEFAULT = "Director del Evento"
    COORDINADOR_GENERAL_DEFAULT = "Coordinador General"
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()
    
    def _configurar_estilos(self):
        """Configura estilos personalizados para certificados"""
        
        # Estilo para el título CERTIFICADO
        self.styles.add(ParagraphStyle(
            name='TituloCertificado',
            parent=self.styles['Heading1'],
            fontSize=54,
            textColor=colors.HexColor('#0d5028'),
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=58
        ))
        
        # Estilo para "Reconocimiento de Participación"
        self.styles.add(ParagraphStyle(
            name='SubtituloCertificado',
            parent=self.styles['Normal'],
            fontSize=19,
            textColor=colors.HexColor('#2c5f3f'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=23
        ))
        
        # Estilo para "Este certificado se otorga a"
        self.styles.add(ParagraphStyle(
            name='TextoIntroduccion',
            parent=self.styles['Normal'],
            fontSize=13,
            textColor=colors.HexColor('#424242'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=17
        ))
        
        # Estilo para el nombre del estudiante
        self.styles.add(ParagraphStyle(
            name='NombreEstudiante',
            parent=self.styles['Normal'],
            fontSize=38,
            textColor=colors.HexColor('#0d5028'),
            spaceAfter=25,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=44
        ))
        
        # Estilo para descripción de participación
        self.styles.add(ParagraphStyle(
            name='DescripcionParticipacion',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=16
        ))
        
        # Estilo para firmas
        self.styles.add(ParagraphStyle(
            name='TextoFirma',
            parent=self.styles['Normal'],
            fontSize=13,
            textColor=colors.HexColor('#0d5028'),
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=17
        ))
        
        # Estilo para nombre de quien firma
        self.styles.add(ParagraphStyle(
            name='NombreFirma',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#0d5028'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=14
        ))
        
        # Estilo para cargo de firma
        self.styles.add(ParagraphStyle(
            name='CargoFirma',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#424242'),
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=13
        ))


class ExpoSoftwareLandscapeTemplate(BaseCertificateTemplate):
    """Plantilla moderna de ExpoSoftware en orientación horizontal con borde verde"""
    
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
        Genera un certificado PDF de participación en orientación horizontal.
        """
        # Crear buffer
        buffer = BytesIO()
        
        # Crear documento en orientación horizontal
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.7*inch,
            leftMargin=0.7*inch,
            topMargin=0.65*inch,
            bottomMargin=0.6*inch
        )
        
        # Contenedor de elementos
        elementos = []
        
        # Agregar encabezado con logos en esquinas
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
        
        # Construir PDF con borde personalizado
        doc.build(elementos, onFirstPage=self._agregar_borde_decorativo)
        
        # Retornar buffer
        buffer.seek(0)
        return buffer
    
    def _agregar_borde_decorativo(self, canvas_obj, doc):
        """Agrega el borde decorativo verde con esquinas amarillas"""
        canvas_obj.saveState()
        
        # Colores más vivos
        verde_oscuro = colors.HexColor('#0d5028')
        verde_medio = colors.HexColor('#2d8f4d')
        amarillo = colors.HexColor('#ffd700')
        
        # Dimensiones de la página
        width, height = landscape(letter)
        
        # Grosor del borde
        border_width = 18
        corner_size = 55
        
        # Borde verde principal - superior
        canvas_obj.setFillColor(verde_oscuro)
        canvas_obj.rect(corner_size, height - border_width, 
                       width - 2*corner_size, border_width, fill=1, stroke=0)
        
        # Borde verde principal - inferior
        canvas_obj.rect(corner_size, 0, 
                       width - 2*corner_size, border_width, fill=1, stroke=0)
        
        # Borde verde medio - izquierdo
        canvas_obj.setFillColor(verde_medio)
        canvas_obj.rect(0, corner_size, 
                       border_width, height - 2*corner_size, fill=1, stroke=0)
        
        # Borde verde medio - derecho
        canvas_obj.rect(width - border_width, corner_size, 
                       border_width, height - 2*corner_size, fill=1, stroke=0)
        
        # Esquinas amarillas
        canvas_obj.setFillColor(amarillo)
        
        # Esquina superior izquierda
        path_tl = canvas_obj.beginPath()
        path_tl.moveTo(0, height)
        path_tl.lineTo(corner_size, height)
        path_tl.lineTo(corner_size, height - border_width)
        path_tl.lineTo(border_width, height - border_width)
        path_tl.lineTo(border_width, height - corner_size)
        path_tl.lineTo(0, height - corner_size)
        path_tl.close()
        canvas_obj.drawPath(path_tl, fill=1, stroke=0)
        
        # Esquina superior derecha
        path_tr = canvas_obj.beginPath()
        path_tr.moveTo(width, height)
        path_tr.lineTo(width - corner_size, height)
        path_tr.lineTo(width - corner_size, height - border_width)
        path_tr.lineTo(width - border_width, height - border_width)
        path_tr.lineTo(width - border_width, height - corner_size)
        path_tr.lineTo(width, height - corner_size)
        path_tr.close()
        canvas_obj.drawPath(path_tr, fill=1, stroke=0)
        
        # Esquina inferior izquierda
        path_bl = canvas_obj.beginPath()
        path_bl.moveTo(0, 0)
        path_bl.lineTo(0, corner_size)
        path_bl.lineTo(border_width, corner_size)
        path_bl.lineTo(border_width, border_width)
        path_bl.lineTo(corner_size, border_width)
        path_bl.lineTo(corner_size, 0)
        path_bl.close()
        canvas_obj.drawPath(path_bl, fill=1, stroke=0)
        
        # Esquina inferior derecha
        path_br = canvas_obj.beginPath()
        path_br.moveTo(width, 0)
        path_br.lineTo(width, corner_size)
        path_br.lineTo(width - border_width, corner_size)
        path_br.lineTo(width - border_width, border_width)
        path_br.lineTo(width - corner_size, border_width)
        path_br.lineTo(width - corner_size, 0)
        path_br.close()
        canvas_obj.drawPath(path_br, fill=1, stroke=0)
        
        canvas_obj.restoreState()
    
    def _crear_encabezado_certificado(self, evento: DatosEventoCertificado) -> list:
        """Crea el encabezado del certificado con logos en esquinas"""
        elementos = []
        
        # Espacio inicial pequeño
        elementos.append(Spacer(1, 0.1*inch))
        
        # Obtener la ruta base del proyecto
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Rutas absolutas de los logos
        logo_upc_path = os.path.join(base_dir, "app", "assets", "upc.jpg")
        logo_facultad_path = os.path.join(base_dir, "app", "assets", "sistemas.png")
        
        # Crear imágenes de los logos
        logo_upc = None
        logo_facultad = None
        
        try:
            if os.path.exists(logo_upc_path):
                # Logo UPC más ancho y rectangular
                logo_upc = Image(logo_upc_path, width=1.7*inch, height=1.05*inch)
                print(f"✅ Logo UPC cargado: {logo_upc_path}")
            else:
                print(f"❌ Logo UPC no encontrado: {logo_upc_path}")
        except Exception as e:
            print(f"❌ Error cargando logo UPC: {e}")
        
        try:
            if os.path.exists(logo_facultad_path):
                # Logo Facultad más alto
                logo_facultad = Image(logo_facultad_path, width=1.25*inch, height=1.55*inch)
                print(f"✅ Logo Facultad cargado: {logo_facultad_path}")
            else:
                print(f"❌ Logo Facultad no encontrado: {logo_facultad_path}")
        except Exception as e:
            print(f"❌ Error cargando logo Facultad: {e}")
        
        # Si no se pudieron cargar logos, crear placeholders
        if logo_upc is None:
            logo_upc = Paragraph('[UPC]', self.styles['Normal'])
        
        if logo_facultad is None:
            logo_facultad = Paragraph('[SIS]', self.styles['Normal'])
        
        # Tabla para logos - centrados verticalmente
        datos_header = [[logo_upc, '', logo_facultad]]
        
        tabla_header = Table(
            datos_header,
            colWidths=[2*inch, 4.5*inch, 2*inch]
        )
        
        tabla_header.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elementos.append(tabla_header)
        
        # Espacio después de logos
        elementos.append(Spacer(1, 0.25*inch))
        
        # Título CERTIFICADO
        elementos.append(Paragraph(
            "CERTIFICADO",
            self.styles['TituloCertificado']
        ))
        
        # Subtítulo
        elementos.append(Paragraph(
            "Reconocimiento de Participación",
            self.styles['SubtituloCertificado']
        ))
        
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
        
        # Texto introductorio
        elementos.append(Paragraph(
            "Este certificado se otorga a",
            self.styles['TextoIntroduccion']
        ))
        
        # Nombre del estudiante
        nombre_completo = f"{estudiante.nombres} {estudiante.apellidos}"
        elementos.append(Paragraph(
            nombre_completo,
            self.styles['NombreEstudiante']
        ))
        
        # Descripción de participación
        texto_participacion = (
            f"Por su destacada participación en la exposición de software "
            f"<b>{evento.nombre_evento}</b>."
        )
        elementos.append(Paragraph(
            texto_participacion,
            self.styles['DescripcionParticipacion']
        ))
        
        # Espacio antes de firmas
        elementos.append(Spacer(1, 0.35*inch))
        
        return elementos
    
    def _crear_seccion_firmas(
        self,
        director_evento: Optional[str],
        coordinador_general: Optional[str],
        fecha_evento: datetime
    ) -> list:
        """Crea la sección de firmas con estilo cursivo"""
        elementos = []
        
        # Usar nombres por defecto si no se proporcionan
        director = director_evento or self.DIRECTOR_EVENTO_DEFAULT
        coordinador = coordinador_general or self.COORDINADOR_GENERAL_DEFAULT
        
        # Espacios para firmas - bien alineados
        datos_firmas = [
            [
                Paragraph("<i>/Firma/</i>", self.styles['TextoFirma']),
                '',
                Paragraph("<i>/Firma/</i>", self.styles['TextoFirma'])
            ],
            [
                Paragraph(director, self.styles['NombreFirma']),
                '',
                Paragraph(coordinador, self.styles['NombreFirma'])
            ],
            [
                Paragraph("Director del Evento", self.styles['CargoFirma']),
                '',
                Paragraph("Coordinador General", self.styles['CargoFirma'])
            ]
        ]
        
        tabla_firmas = Table(
            datos_firmas,
            colWidths=[2.6*inch, 2.3*inch, 2.6*inch],
            rowHeights=[0.4*inch, 0.3*inch, 0.25*inch]
        )
        
        tabla_firmas.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elementos.append(tabla_firmas)
        
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


class CertificateTemplateFactory:
    """Fábrica para crear plantillas de certificados"""
    
    @staticmethod
    def get_template(template_name: str = "landscape"):
        """
        Obtiene una plantilla por nombre
        
        Args:
            template_name: 'landscape' (por defecto)
        """
        templates = {
            "landscape": ExpoSoftwareLandscapeTemplate
        }
        
        template_class = templates.get(template_name, ExpoSoftwareLandscapeTemplate)
        return template_class()