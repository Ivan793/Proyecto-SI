# app/services/pdf_generator.py

# Importaciones estándar de Python
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import os
from io import BytesIO

# Importaciones de ReportLab para generación de PDFs
## Configuración básica
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

## Estilos y elementos de documento
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,  # Clase base para documentos
    Paragraph,         # Texto con formato
    Spacer,           # Espaciado vertical
    Table,            # Tablas
    TableStyle,       # Estilos de tabla
    PageBreak,        # Salto de página
    Image             # Imágenes
)

## Gráficos y visualizaciones
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie

# Constantes
NO_ESPECIFICADO = 'No especificado'
NO_ESPECIFICADA = 'No especificada'
SIN_TITULO = 'Sin título'
SIN_LINEA = 'Sin línea'

# Mapeo de líneas de investigación
LINEAS_INVESTIGACION = {
    0: "Tecnologías de la Información y la Comunicación",
    1: "Transformación Digital"
}

# Colores para gráficos
COLORES_GRAFICOS = [
    colors.HexColor('#1976d2'),
    colors.HexColor('#64b5f6'),
    colors.HexColor('#90caf9'),
    colors.HexColor('#bbdefb')
]


class PDFGenerator:
    """Generador de reportes en PDF con formato profesional"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._configurar_estilos_personalizados()
    
    def _configurar_estilos_personalizados(self):
        """Configura estilos personalizados para el PDF"""
        
        # Estilo para título principal
        self.styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para texto normal
        self.styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6
        ))
        
        # Estilo para información destacada
        self.styles.add(ParagraphStyle(
            name='Destacado',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1976d2'),
            fontName='Helvetica-Bold'
        ))
    
    def generar_reporte(
        self,
        datos: List[Dict[str, Any]],
        titulo: str,
        filtros_aplicados: Dict[str, Any],
        estadisticas: Dict[str, Any],
        incluir_graficos: bool = True,
        output_path: Optional[str] = None
    ) -> Optional[BytesIO]:
        """
        Genera un reporte PDF completo.
        
        Args:
            datos: Lista de proyectos a incluir
            titulo: Título del reporte
            filtros_aplicados: Filtros utilizados para generar el reporte
            estadisticas: Estadísticas calculadas
            incluir_graficos: Si incluir gráficos estadísticos
            output_path: Ruta donde guardar el PDF (opcional)
            
        Returns:
            BytesIO con el contenido del PDF si output_path es None,
            None si el PDF se guarda en archivo
        """
        # Crear buffer para el PDF
        buffer = BytesIO()
        
        # Crear documento
        doc = SimpleDocTemplate(
            buffer if not output_path else output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Contenedor de elementos
        elementos = []
        
        # Agregar encabezado
        elementos.extend(self._crear_encabezado(titulo))
        
        # Agregar información de filtros
        elementos.extend(self._crear_seccion_filtros(filtros_aplicados))
        
        # Agregar resumen estadístico
        elementos.extend(self._crear_resumen_estadistico(estadisticas))
        
        # Agregar gráficos si está habilitado
        if incluir_graficos and estadisticas['total_proyectos'] > 0:
            elementos.extend(self._crear_graficos(estadisticas))
        
        # Agregar salto de página antes del listado
        elementos.append(PageBreak())
        
        # Agregar listado detallado de proyectos
        elementos.extend(self._crear_listado_proyectos(datos))
        
        # Agregar pie de página
        elementos.extend(self._crear_pie_pagina())
        
        # Construir PDF
        doc.build(elementos)
        
        # Retornar buffer
        if not output_path:
            buffer.seek(0)
            return buffer
        
        return None
    
    def _crear_encabezado(self, titulo: str) -> List:
        """Crea el encabezado del reporte"""
        elementos = []
        
        # Logo y título (si tienes logo, agrégalo aquí)
        elementos.append(Paragraph(
            "ExpoSoftware - Facultad de Ingeniería de Sistemas",
            self.styles['Normal']
        ))
        elementos.append(Spacer(1, 0.2 * inch))
        
        # Título principal
        elementos.append(Paragraph(titulo, self.styles['TituloPrincipal']))
        elementos.append(Spacer(1, 0.1 * inch))
        
        # Fecha de generación
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        elementos.append(Paragraph(
            f"<b>Fecha de generación:</b> {fecha_actual}",
            self.styles['Normal']
        ))
        elementos.append(Spacer(1, 0.3 * inch))
        
        return elementos
    
    def _crear_seccion_filtros(self, filtros: Dict[str, Any]) -> List:
        """Crea la sección de filtros aplicados"""
        elementos = []
        
        elementos.append(Paragraph("Filtros Aplicados", self.styles['Subtitulo']))
        
        # Crear tabla con filtros
        filtros_texto = []
        
        if filtros.get('tipo_persona'):
            filtros_texto.append(['Tipo de Persona:', filtros['tipo_persona']])
        
        if filtros.get('codigo_programa'):
            filtros_texto.append(['Programa:', filtros['codigo_programa']])
        
        if filtros.get('codigo_materia'):
            filtros_texto.append(['Materia:', filtros['codigo_materia']])
        
        if filtros.get('semestre'):
            filtros_texto.append(['Semestre:', str(filtros['semestre'])])
        
        if filtros.get('tipo_actividad'):
            filtros_texto.append(['Tipo de Actividad:', filtros['tipo_actividad']])
        
        if filtros.get('fecha_desde'):
            filtros_texto.append(['Desde:', str(filtros['fecha_desde'])])
        
        if filtros.get('fecha_hasta'):
            filtros_texto.append(['Hasta:', str(filtros['fecha_hasta'])])
        
        if filtros.get('codigo_linea') is not None:
            lineas = {
                0: "Tecnologías de la Información y la Comunicación",
                1: "Transformación Digital"
            }
            filtros_texto.append([
                'Línea de Investigación:', 
                lineas.get(filtros['codigo_linea'], 'No especificada')
            ])
        
        if not filtros_texto:
            elementos.append(Paragraph(
                "No se aplicaron filtros específicos (todos los proyectos)",
                self.styles['TextoNormal']
            ))
        else:
            tabla = Table(filtros_texto, colWidths=[2.5 * inch, 4 * inch])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1976d2')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            elementos.append(tabla)
        
        elementos.append(Spacer(1, 0.3 * inch))
        
        return elementos
    
    def _crear_resumen_estadistico(self, estadisticas: Dict[str, Any]) -> List:
        """Crea el resumen estadístico"""
        elementos = []
        
        elementos.append(Paragraph("Resumen Estadístico", self.styles['Subtitulo']))
        
        # Total de proyectos
        elementos.append(Paragraph(
            f"<b>Total de proyectos encontrados:</b> {estadisticas['total_proyectos']}",
            self.styles['Destacado']
        ))
        elementos.append(Spacer(1, 0.2 * inch))
        
        # Distribución por tipo de actividad
        if estadisticas.get('por_tipo_actividad'):
            elementos.append(Paragraph(
                "<b>Distribución por Tipo de Actividad:</b>",
                self.styles['TextoNormal']
            ))
            
            data = [['Tipo', 'Cantidad', '%']]
            total = estadisticas['total_proyectos']
            
            for tipo, cantidad in estadisticas['por_tipo_actividad'].items():
                porcentaje = (cantidad / total * 100) if total > 0 else 0
                data.append([tipo, str(cantidad), f"{porcentaje:.1f}%"])
            
            tabla = Table(data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elementos.append(tabla)
            elementos.append(Spacer(1, 0.2 * inch))
        
        return elementos
    
    def _crear_graficos(self, estadisticas: Dict[str, Any]) -> List:
        """Crea gráficos estadísticos"""
        elementos = []
        
        elementos.append(PageBreak())
        elementos.append(Paragraph("Análisis Gráfico", self.styles['Subtitulo']))
        elementos.append(Spacer(1, 0.2 * inch))
        
        # Gráfico de barras - Proyectos por tipo de actividad
        if estadisticas.get('por_tipo_actividad'):
            drawing = Drawing(400, 250)
            chart = VerticalBarChart()
            chart.x = 50
            chart.y = 50
            chart.height = 150
            chart.width = 300
            
            datos = estadisticas['por_tipo_actividad']
            chart.data = [list(datos.values())]
            chart.categoryAxis.categoryNames = list(datos.keys())
            
            chart.valueAxis.valueMin = 0
            chart.valueAxis.valueMax = max(datos.values()) + 2 if datos else 10
            chart.valueAxis.valueStep = 1
            
            chart.bars[0].fillColor = colors.HexColor('#1976d2')
            
            drawing.add(chart)
            elementos.append(drawing)
            elementos.append(Spacer(1, 0.2 * inch))
        
        # Gráfico circular - Distribución por línea de investigación
        if estadisticas.get('por_linea') and len(estadisticas['por_linea']) > 0:
            elementos.append(Paragraph(
                "Distribución por Línea de Investigación",
                self.styles['TextoNormal']
            ))
            
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 150
            pie.y = 50
            pie.width = 150
            pie.height = 150
            
            datos = estadisticas['por_linea']
            pie.data = list(datos.values())
            pie.labels = list(datos.keys())
            
            pie.slices.strokeWidth = 0.5
            colores = [
                colors.HexColor('#1976d2'),
                colors.HexColor('#64b5f6'),
                colors.HexColor('#90caf9'),
                colors.HexColor('#bbdefb')
            ]
            
            for i, color in enumerate(colores[:len(datos)]):
                pie.slices[i].fillColor = color
            
            drawing.add(pie)
            elementos.append(drawing)
            elementos.append(Spacer(1, 0.3 * inch))
        
        return elementos
    
    def _obtener_info_usuario(self, usuario_data: Dict[str, Any]) -> str:
        """Obtiene el nombre completo de un usuario"""
        nombres = usuario_data.get('nombres', '')
        apellidos = usuario_data.get('apellidos', '')
        nombre_completo = f"{nombres} {apellidos}".strip()
        return nombre_completo or NO_ESPECIFICADO

    def _obtener_info_estudiante(self, proyecto: Dict[str, Any]) -> List[List[str]]:
        """Obtiene la información del estudiante"""
        info = []
        if estudiante := proyecto.get('estudiante'):
            usuario = estudiante.get('usuario', {})
            nombre_completo = self._obtener_info_usuario(usuario)
            info.append(['Estudiante:', nombre_completo])
            
            if semestre := estudiante.get('semestre'):
                info.append(['Semestre:', f"{semestre}°"])
        return info

    def _obtener_info_docente(self, proyecto: Dict[str, Any]) -> List[List[str]]:
        """Obtiene la información del docente"""
        info = []
        if docente := proyecto.get('docente'):
            usuario = docente.get('usuario', {})
            nombre_completo = self._obtener_info_usuario(usuario)
            info.append(['Docente:', nombre_completo])
        return info

    def _obtener_info_materia(self, proyecto: Dict[str, Any]) -> List[List[str]]:
        """Obtiene la información de la materia"""
        info = []
        if materia := proyecto.get('materia'):
            info.append([
                'Materia:',
                materia.get('nombre_materia', NO_ESPECIFICADA)
            ])
        return info

    def _obtener_info_investigacion(self, proyecto: Dict[str, Any]) -> List[List[str]]:
        """Obtiene la información de línea y sublínea de investigación"""
        info = []
        if linea := proyecto.get('linea_investigacion'):
            info.append([
                'Línea:',
                linea.get('nombre_linea', NO_ESPECIFICADA)
            ])
        
        if sublinea := proyecto.get('sublinea_investigacion'):
            info.append([
                'Sublínea:',
                sublinea.get('nombre_sublinea', NO_ESPECIFICADA)
            ])
        return info

    def _crear_tabla_proyecto(self, info_proyecto: List[List[str]]) -> Table:
        """Crea una tabla con la información del proyecto"""
        tabla = Table(info_proyecto, colWidths=[2 * inch, 4.5 * inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        return tabla

    def _crear_listado_proyectos(self, datos: List[Dict[str, Any]]) -> List:
        """Crea el listado detallado de proyectos"""
        elementos = []
        
        elementos.append(Paragraph(
            "Listado Detallado de Proyectos",
            self.styles['Subtitulo']
        ))
        elementos.append(Spacer(1, 0.2 * inch))
        
        if not datos:
            elementos.append(Paragraph(
                "No se encontraron proyectos con los filtros aplicados.",
                self.styles['TextoNormal']
            ))
            return elementos
        
        for idx, proyecto in enumerate(datos, 1):
            # Encabezado del proyecto
            elementos.append(Paragraph(
                f"<b>Proyecto #{idx}: {proyecto.get('titulo_proyecto', SIN_TITULO)}</b>",
                self.styles['Destacado']
            ))
            
            # Recopilar información del proyecto
            info_proyecto = []
            
            # Tipo de actividad
            if tipo := proyecto.get('tipo_actividad'):
                info_proyecto.append(['Tipo de Actividad:', tipo])
            
            # Agregar información de estudiante, docente, materia e investigación
            info_proyecto.extend(self._obtener_info_estudiante(proyecto))
            info_proyecto.extend(self._obtener_info_docente(proyecto))
            info_proyecto.extend(self._obtener_info_materia(proyecto))
            info_proyecto.extend(self._obtener_info_investigacion(proyecto))
            
            # Fecha de subida
            if fecha := proyecto.get('fecha_subida'):
                fecha_str = fecha.strftime("%d/%m/%Y") if isinstance(fecha, datetime) else str(fecha)
                info_proyecto.append(['Fecha de Subida:', fecha_str])
            
            # Crear y agregar tabla si hay información
            if info_proyecto:
                elementos.append(self._crear_tabla_proyecto(info_proyecto))
            
            elementos.append(Spacer(1, 0.25 * inch))
        
        return elementos
    
    def _crear_pie_pagina(self) -> List:
        """Crea el pie de página del reporte"""
        elementos = []
        
        elementos.append(Spacer(1, 0.5 * inch))
        elementos.append(Paragraph(
            "_______________________________________________________________",
            self.styles['Normal']
        ))
        elementos.append(Paragraph(
            "<i>Reporte generado automáticamente por el Sistema ExpoSoftware</i>",
            self.styles['Normal']
        ))
        elementos.append(Paragraph(
            f"<i>Universidad Popular del Cesar - {datetime.now().year}</i>",
            self.styles['Normal']
        ))
        
        return elementos
    
    def obtener_tamano_archivo(self, buffer: BytesIO) -> int:
        """
        Obtiene el tamaño del archivo PDF en bytes.
        
        Args:
            buffer: Buffer con el contenido del PDF
            
        Returns:
            Tamaño en bytes
        """
        buffer.seek(0, os.SEEK_END)
        tamano = buffer.tell()
        buffer.seek(0)
        return tamano