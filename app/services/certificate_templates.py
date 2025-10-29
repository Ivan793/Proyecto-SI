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
    """Plantilla base premium para certificados de alta calidad"""
    
    # Configuración de firmas por defecto
    DIRECTOR_EVENTO_DEFAULT = "Álvaro Oñate Bowen"
    COORDINADOR_GENERAL_DEFAULT = "Álvaro Oñate Bowen"
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()
    
    def _configurar_estilos(self):
        """Configura estilos personalizados premium para certificados"""
        
        # Estilo para el título CERTIFICADO - Diseño impactante
        self.styles.add(ParagraphStyle(
            name='TituloCertificado',
            parent=self.styles['Heading1'],
            fontSize=68,
            textColor=colors.HexColor('#1a4d2e'),
            spaceAfter=2,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=72,
            letterSpacing=2
        ))
        
        # Estilo para "Reconocimiento de Participación" - Elegante y refinado
        self.styles.add(ParagraphStyle(
            name='SubtituloCertificado',
            parent=self.styles['Normal'],
            fontSize=16,
            textColor=colors.HexColor('#2d5a3d'),
            spaceAfter=32,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=20,
            letterSpacing=0.8
        ))
        
        # Estilo para "Este certificado se otorga a" - Profesional y claro
        self.styles.add(ParagraphStyle(
            name='TextoIntroduccion',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#4a4a4a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=15
        ))
        
        # Estilo para el nombre del estudiante - Prominente y memorable
        self.styles.add(ParagraphStyle(
            name='NombreEstudiante',
            parent=self.styles['Normal'],
            fontSize=42,
            textColor=colors.HexColor('#1a3a2e'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=48,
            letterSpacing=1.2
        ))
        
        # Estilo para descripción de participación - Legible y equilibrado
        self.styles.add(ParagraphStyle(
            name='DescripcionParticipacion',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=16
        ))
        
        # Estilo para firmas manuscritas - Realista y elegante
        self.styles.add(ParagraphStyle(
            name='TextoFirmaManuscrita',
            parent=self.styles['Normal'],
            fontSize=22,
            textColor=colors.HexColor('#1a3a2e'),
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique',
            leading=26,
            spaceAfter=1,
        ))
        
        # Estilo para líneas de firma
        self.styles.add(ParagraphStyle(
            name='LineaFirma',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#1a4d2e'),
            alignment=TA_CENTER,
            spaceAfter=2,
            spaceBefore=0
        ))
        
        # Estilo para nombre de quien firma - Claro y profesional
        self.styles.add(ParagraphStyle(
            name='NombreFirma',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#1a4d2e'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=14,
            spaceAfter=0
        ))
        
        # Estilo para cargo de firma - Discreto y formal
        self.styles.add(ParagraphStyle(
            name='CargoFirma',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#555555'),
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=11
        ))


class ExpoSoftwareLandscapeTemplate(BaseCertificateTemplate):
    """
    Plantilla premium de ExpoSoftware en orientación horizontal
    Diseño de alta calidad con borde decorativo profesional
    """
    
    # Nombres de los firmantes por defecto
    DIRECTOR_EVENTO_DEFAULT = "Álvaro Oñate Bowen"
    COORDINADOR_GENERAL_DEFAULT = "Álvaro Oñate Bowen"
    
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
        Genera un certificado PDF de participación premium en orientación horizontal.
        
        Args:
            estudiante: Datos del estudiante certificado
            proyecto: Información del proyecto presentado
            evento: Detalles del evento
            incluir_calificacion: Si se debe incluir la calificación
            director_evento: Nombre del director (opcional)
            coordinador_general: Nombre del coordinador (opcional)
        
        Returns:
            BytesIO: Buffer con el PDF generado
        """
        # Crear buffer para el PDF
        buffer = BytesIO()
        
        # Crear documento en orientación horizontal con márgenes optimizados
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.4*inch,
            bottomMargin=0.4*inch
        )
        
        # Contenedor de elementos del certificado
        elementos = []
        
        # Agregar encabezado con logos institucionales
        elementos.extend(self._crear_encabezado_certificado(evento))
        
        # Agregar contenido principal del certificado
        elementos.extend(self._crear_contenido_certificado(
            estudiante=estudiante,
            proyecto=proyecto,
            evento=evento,
            incluir_calificacion=incluir_calificacion
        ))
        
        # Agregar sección de firmas
        elementos.extend(self._crear_seccion_firmas(
            director_evento=director_evento,
            coordinador_general=coordinador_general
        ))
        
        # Construir PDF con borde decorativo personalizado
        doc.build(elementos, onFirstPage=self._agregar_borde_decorativo)
        
        # Retornar buffer al inicio para lectura
        buffer.seek(0)
        return buffer
    
    def _agregar_borde_decorativo(self, canvas_obj, doc):
        """
        Agrega el borde decorativo verde premium con esquinas amarillas doradas
        Diseño inspirado en certificados institucionales de alta calidad
        """
        canvas_obj.saveState()
        
        # Paleta de colores premium institucionales
        verde_principal = colors.HexColor('#1a7b3e')
        verde_secundario = colors.HexColor('#24944b')
        amarillo_dorado = colors.HexColor('#f9c74f')
        verde_acento = colors.HexColor('#e8f5e9')
        
        # Dimensiones de la página
        width, height = landscape(letter)
        
        # Configuración de dimensiones del borde
        border_width = 18
        corner_size = 52
        inner_border_offset = 2
        
        # ============================================================
        # CAPA 1: BORDES PRINCIPALES VERDES
        # ============================================================
        
        # Borde superior - verde principal
        canvas_obj.setFillColor(verde_principal)
        canvas_obj.rect(corner_size, height - border_width, 
                       width - 2*corner_size, border_width, fill=1, stroke=0)
        
        # Borde inferior - verde principal
        canvas_obj.rect(corner_size, 0, 
                       width - 2*corner_size, border_width, fill=1, stroke=0)
        
        # Borde izquierdo - verde secundario
        canvas_obj.setFillColor(verde_secundario)
        canvas_obj.rect(0, corner_size, 
                       border_width, height - 2*corner_size, fill=1, stroke=0)
        
        # Borde derecho - verde secundario
        canvas_obj.rect(width - border_width, corner_size, 
                       border_width, height - 2*corner_size, fill=1, stroke=0)
        
        # ============================================================
        # CAPA 2: ESQUINAS DECORATIVAS DORADAS (DISEÑO EN L)
        # ============================================================
        
        canvas_obj.setFillColor(amarillo_dorado)
        
        # Esquina superior izquierda - Forma de L elegante
        path_tl = canvas_obj.beginPath()
        path_tl.moveTo(0, height)
        path_tl.lineTo(corner_size, height)
        path_tl.lineTo(corner_size, height - border_width)
        path_tl.lineTo(border_width, height - border_width)
        path_tl.lineTo(border_width, height - corner_size)
        path_tl.lineTo(0, height - corner_size)
        path_tl.close()
        canvas_obj.drawPath(path_tl, fill=1, stroke=0)
        
        # Esquina superior derecha - Forma de L elegante
        path_tr = canvas_obj.beginPath()
        path_tr.moveTo(width, height)
        path_tr.lineTo(width - corner_size, height)
        path_tr.lineTo(width - corner_size, height - border_width)
        path_tr.lineTo(width - border_width, height - border_width)
        path_tr.lineTo(width - border_width, height - corner_size)
        path_tr.lineTo(width, height - corner_size)
        path_tr.close()
        canvas_obj.drawPath(path_tr, fill=1, stroke=0)
        
        # Esquina inferior izquierda - Forma de L elegante
        path_bl = canvas_obj.beginPath()
        path_bl.moveTo(0, 0)
        path_bl.lineTo(0, corner_size)
        path_bl.lineTo(border_width, corner_size)
        path_bl.lineTo(border_width, border_width)
        path_bl.lineTo(corner_size, border_width)
        path_bl.lineTo(corner_size, 0)
        path_bl.close()
        canvas_obj.drawPath(path_bl, fill=1, stroke=0)
        
        # Esquina inferior derecha - Forma de L elegante
        path_br = canvas_obj.beginPath()
        path_br.moveTo(width, 0)
        path_br.lineTo(width, corner_size)
        path_br.lineTo(width - border_width, corner_size)
        path_br.lineTo(width - border_width, border_width)
        path_br.lineTo(width - corner_size, border_width)
        path_br.lineTo(width - corner_size, 0)
        path_br.close()
        canvas_obj.drawPath(path_br, fill=1, stroke=0)
        
        # ============================================================
        # CAPA 3: MARCO DECORATIVO INTERNO (Detalle de calidad)
        # ============================================================
        
        canvas_obj.setStrokeColor(verde_acento)
        canvas_obj.setLineWidth(1.2)
        inner_margin = border_width + inner_border_offset
        
        # Rectángulo interno decorativo con esquinas redondeadas sutiles
        canvas_obj.roundRect(
            inner_margin, 
            inner_margin, 
            width - 2*inner_margin, 
            height - 2*inner_margin,
            2,
            fill=0, 
            stroke=1
        )
        
        # ============================================================
        # CAPA 4: LÍNEA DE ACENTO ADICIONAL (Extra premium)
        # ============================================================
        
        canvas_obj.setStrokeColor(verde_principal)
        canvas_obj.setLineWidth(0.5)
        inner_margin_2 = border_width + inner_border_offset + 4
        
        # Segunda línea interna para efecto de profundidad
        canvas_obj.roundRect(
            inner_margin_2, 
            inner_margin_2, 
            width - 2*inner_margin_2, 
            height - 2*inner_margin_2,
            2,
            fill=0, 
            stroke=1
        )
        
        canvas_obj.restoreState()
    
    def _crear_encabezado_certificado(self, evento: DatosEventoCertificado) -> list:
        """
        Crea el encabezado premium del certificado con logos institucionales
        perfectamente alineados y balanceados
        """
        elementos = []
        
        # Espacio inicial para balance visual superior
        elementos.append(Spacer(1, 0.08*inch))
        
        # Obtener la ruta base del proyecto
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Rutas absolutas de los logos institucionales
        logo_upc_path = os.path.join(base_dir, "app", "assets", "upc.jpg")
        logo_facultad_path = os.path.join(base_dir, "app", "assets", "sistemas.png")
        
        # Variables para almacenar los logos
        logo_upc = None
        logo_facultad = None
        
        # Cargar logo UPC con dimensiones optimizadas - MÁS ANCHO
        try:
            if os.path.exists(logo_upc_path):
                # Logo UPC más ancho: 2.0" × 1.3" (proporción mejorada)
                logo_upc = Image(logo_upc_path, width=1.5*inch, height=1.3*inch)
                logo_upc.hAlign = 'LEFT'
                print(f"✅ Logo UPC cargado exitosamente: {logo_upc_path}")
            else:
                print(f"⚠️  Logo UPC no encontrado en: {logo_upc_path}")
        except Exception as e:
            print(f"❌ Error al cargar logo UPC: {e}")
        
        # Cargar logo de Facultad con dimensiones optimizadas - MENOS ANCHO
        try:
            if os.path.exists(logo_facultad_path):
                # Logo Facultad menos ancho: 1.4" × 1.2" (más estrecho)
                logo_facultad = Image(logo_facultad_path, width=1.9*inch, height=1.6*inch)
                logo_facultad.hAlign = 'RIGHT'
                print(f"✅ Logo Facultad cargado exitosamente: {logo_facultad_path}")
            else:
                print(f"⚠️  Logo Facultad no encontrado en: {logo_facultad_path}")
        except Exception as e:
            print(f"❌ Error al cargar logo Facultad: {e}")
        
        # Crear placeholders elegantes si los logos no se cargaron
        if logo_upc is None:
            logo_upc = Paragraph(
                '<font color="#1a4d2e" size="8"><b>[LOGO UPC]</b></font>',
                self.styles['Normal']
            )
        
        if logo_facultad is None:
            logo_facultad = Paragraph(
                '<font color="#1a4d2e" size="8"><b>[LOGO FACULTAD]</b></font>',
                self.styles['Normal']
            )
        
        # Tabla para logos con espaciado perfecto y balanceado
        datos_header = [[logo_upc, '', logo_facultad]]
        
        # Ajustar ancho de columnas para los nuevos tamaños de logos
        tabla_header = Table(
            datos_header,
            colWidths=[2.0*inch, 3.5*inch, 2.0*inch]  # Columnas ajustadas
        )
        
        # Estilos de la tabla de encabezado
        tabla_header.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (2, 0), (2, 0), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elementos.append(tabla_header)
        
        # Espacio después de logos - calculado para balance óptimo
        elementos.append(Spacer(1, 0.15*inch))
        
        # Título CERTIFICADO con estilo premium
        elementos.append(Paragraph(
            "CERTIFICADO",
            self.styles['TituloCertificado']
        ))
        
        # Subtítulo elegante y refinado
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
        """
        Crea el contenido principal del certificado con formato premium
        y redacción profesional
        """
        elementos = []
        
        # Texto introductorio elegante
        elementos.append(Paragraph(
            "Este certificado se otorga a",
            self.styles['TextoIntroduccion']
        ))
        
        # Nombre completo del estudiante con formato destacado
        nombre_completo = f"{estudiante.nombres} {estudiante.apellidos}"
        
        # Crear estilo de nombre compacto para mejor ajuste
        estilo_nombre_compacto = ParagraphStyle(
            name='NombreEstudianteCompacto',
            parent=self.styles['NombreEstudiante'],
            fontSize=42,
            leading=48,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a3a2e'),
            letterSpacing=1.2
        )
        
        elementos.append(Paragraph(
            nombre_completo,
            estilo_nombre_compacto
        ))
        
        # Descripción de participación con redacción profesional
        texto_participacion = (
            f"Por su destacada participación en la exposición de software "
            f"<b>{evento.nombre_evento}</b>, demostrando excelencia académica "
            f"y compromiso con la innovación tecnológica."
        )
        
        elementos.append(Paragraph(
            texto_participacion,
            self.styles['DescripcionParticipacion']
        ))
        
        # Espacio antes de la sección de firmas
        elementos.append(Spacer(1, 0.2*inch))
        
        return elementos
    
    def _crear_seccion_firmas(
        self,
        director_evento: Optional[str],
        coordinador_general: Optional[str]
    ) -> list:
        """
        Crea la sección de firmas con diseño profesional premium,
        incluyendo firmas manuscritas realistas SOBRE la línea
        y fecha actual
        """
        elementos = []
        
        # Usar nombres proporcionados o valores por defecto
        director = director_evento or self.DIRECTOR_EVENTO_DEFAULT
        coordinador = coordinador_general or self.COORDINADOR_GENERAL_DEFAULT
        
        # Formatear nombres para efecto de firma realista
        firma_director = self._formatear_como_firma(director)
        firma_coordinador = self._formatear_como_firma(coordinador)
        
        # CORREGIDO: Orden correcto - Firma PRIMERO, luego línea
        datos_firmas = [
            # Fila 1: Firmas manuscritas realistas (SOBRE la línea)
            [
                Paragraph(firma_director, self.styles['TextoFirmaManuscrita']),
                '',
                Paragraph(firma_coordinador, self.styles['TextoFirmaManuscrita'])
            ],
            # Fila 2: Líneas decorativas para firma (DEBAJO de la firma)
            [
                Paragraph("_________________________", self.styles['LineaFirma']),
                '',
                Paragraph("_________________________", self.styles['LineaFirma'])
            ],
            # Fila 3: Nombres de los firmantes
            [
                Paragraph(director, self.styles['NombreFirma']),
                '',
                Paragraph(coordinador, self.styles['NombreFirma'])
            ],
            # Fila 4: Cargos oficiales
            [
                Paragraph("Director del Evento", self.styles['CargoFirma']),
                '',
                Paragraph("Coordinador General", self.styles['CargoFirma'])
            ]
        ]
        
        # Crear tabla con dimensiones optimizadas
        tabla_firmas = Table(
            datos_firmas,
            colWidths=[2.5*inch, 2.0*inch, 2.5*inch],
            rowHeights=[0.4*inch, 0.2*inch, 0.25*inch, 0.2*inch]
        )
        
        # Aplicar estilos profesionales a la tabla
        tabla_firmas.setStyle(TableStyle([
            # Alineación
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Padding optimizado para cada fila
            ('TOPPADDING', (0, 0), (-1, 0), 0),      # Firmas manuscritas
            ('BOTTOMPADDING', (0, 0), (-1, 0), 2),   # Espacio antes de línea
            
            ('TOPPADDING', (0, 1), (-1, 1), 0),      # Líneas
            ('BOTTOMPADDING', (0, 1), (-1, 1), 2),   # Espacio antes de nombres
            
            ('TOPPADDING', (0, 2), (-1, 2), 0),      # Nombres
            ('BOTTOMPADDING', (0, 2), (-1, 2), 1),   # Espacio antes de cargos
            
            ('TOPPADDING', (0, 3), (-1, 3), 0),      # Cargos
            ('BOTTOMPADDING', (0, 3), (-1, 3), 0),
            
            # Padding lateral
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elementos.append(tabla_firmas)
        
        # Espacio final
        elementos.append(Spacer(1, 0.08*inch))
        
        # Fecha actual en formato elegante - CORREGIDO: usar fecha actual
        fecha_actual = datetime.now()
        fecha_formateada = self._formatear_fecha_espanol(fecha_actual)
        texto_fecha = f"Valledupar, {fecha_formateada}"
        
        elementos.append(Paragraph(
            texto_fecha,
            ParagraphStyle(
                name='TextoFecha',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#555555'),
                alignment=TA_CENTER,
                fontName='Helvetica',
                leading=10
            )
        ))
        
        return elementos
    
    def _formatear_como_firma(self, nombre_completo: str) -> str:
        """
        Formatea un nombre completo para que parezca una firma manuscrita realista
        
        Args:
            nombre_completo: Nombre completo a formatear
        
        Returns:
            str: Nombre formateado como firma realista
        """
        # Convertir a minúsculas para efecto de firma cursiva
        nombre_firma = nombre_completo.lower()
        
        # Opcional: agregar algún efecto de firma manuscrita
        palabras = nombre_firma.split()
        if len(palabras) >= 2:
            # Para nombres con apellidos, hacer un efecto de firma más realista
            nombre_firma = f"{' '.join(palabras[:-1])}  {palabras[-1]}"
        
        return nombre_firma
    
    def _formatear_fecha_espanol(self, fecha: datetime) -> str:
        """
        Formatea una fecha en español con formato elegante
        
        Args:
            fecha: Objeto datetime a formatear
        
        Returns:
            str: Fecha formateada (ej: "15 de Octubre de 2024")
        """
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
    """
    Fábrica para crear plantillas de certificados
    Permite obtener diferentes tipos de plantillas según necesidad
    """
    
    @staticmethod
    def get_template(template_name: str = "landscape"):
        """
        Obtiene una plantilla de certificado por nombre
        
        Args:
            template_name: Nombre de la plantilla ('landscape' por defecto)
        
        Returns:
            Instancia de la plantilla solicitada
        """
        templates = {
            "landscape": ExpoSoftwareLandscapeTemplate,
            "premium": ExpoSoftwareLandscapeTemplate,
            "horizontal": ExpoSoftwareLandscapeTemplate,
        }
        
        template_class = templates.get(template_name.lower(), ExpoSoftwareLandscapeTemplate)
        return template_class()