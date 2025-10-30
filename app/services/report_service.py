# app/services/report_service.py

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from io import BytesIO
import os
import uuid

from app.repositories.report_repository import ReportRepository
from app.services.pdf_generator import PDFGenerator
from app.services.email_service import EmailService
from app.schemas.report import (
    FiltrosReporte,
    ReporteGeneradoResponse,
    ReporteEnviadoResponse
)


class ReportService:
    """Servicio principal para gestión de reportes"""
    
    def __init__(self):
        self.repository = ReportRepository()
        self.pdf_generator = PDFGenerator()
        self.email_service = EmailService()
        self.directorio_reportes = os.getenv(
            'REPORTES_DIR',
            'reportes_temp'
        )
        self._asegurar_directorio()
    
    def _asegurar_directorio(self):
        """Crea el directorio de reportes si no existe"""
        if not os.path.exists(self.directorio_reportes):
            os.makedirs(self.directorio_reportes)
    
    def _generar_id_reporte(self) -> str:
        """
        Genera un ID único para el reporte.
        
        Returns:
            ID del reporte en formato RPT_YYYYMMDD_HHMMSS_uuid
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"RPT_{timestamp}_{unique_id}"
    
    def _generar_nombre_archivo(self, titulo: Optional[str] = None) -> str:
        """
        Genera el nombre del archivo PDF.
        
        Args:
            titulo: Título personalizado (opcional)
            
        Returns:
            Nombre del archivo
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if titulo:
            # Limpiar título para nombre de archivo
            titulo_limpio = titulo.lower()
            titulo_limpio = titulo_limpio.replace(' ', '_')
            titulo_limpio = ''.join(
                c for c in titulo_limpio 
                if c.isalnum() or c in ('_', '-')
            )
            return f"reporte_{titulo_limpio}_{timestamp}.pdf"
        
        return f"reporte_proyectos_{timestamp}.pdf"
    
    async def generar_reporte(
        self,
        filtros: FiltrosReporte,
        titulo_reporte: Optional[str] = None,
        incluir_graficos: bool = True,
        guardar_en_servidor: bool = True
    ) -> Dict[str, Any]:
        """
        Genera un reporte PDF basado en los filtros proporcionados.
        
        Args:
            filtros: Filtros para la consulta
            titulo_reporte: Título personalizado del reporte
            incluir_graficos: Si incluir gráficos estadísticos
            guardar_en_servidor: Si guardar el archivo en el servidor
            
        Returns:
            Diccionario con información del reporte generado
        """
        # Obtener datos filtrados
        datos = await self.repository.obtener_datos_por_filtros(filtros)
        
        if not datos:
            raise ValueError("No se encontraron registros con los filtros aplicados")
        
        # Calcular estadísticas
        estadisticas = await self.repository.obtener_estadisticas(datos)
        
        # Preparar título
        titulo_final = titulo_reporte or "Reporte de Proyectos ExpoSoftware"
        
        # Generar PDF
        pdf_buffer = self.pdf_generator.generar_reporte(
            datos=datos,
            titulo=titulo_final,
            filtros_aplicados=filtros.dict(exclude_none=True),
            estadisticas=estadisticas,
            incluir_graficos=incluir_graficos
        )
        
        # Generar identificadores
        id_reporte = self._generar_id_reporte()
        nombre_archivo = self._generar_nombre_archivo(titulo_reporte)
        
        # Guardar en servidor si se requiere
        ruta_archivo = None
        url_descarga = None
        
        if guardar_en_servidor:
            ruta_archivo = os.path.join(self.directorio_reportes, nombre_archivo)
            
            with open(ruta_archivo, 'wb') as f:
                pdf_buffer.seek(0)
                f.write(pdf_buffer.read())
                pdf_buffer.seek(0)
            
            # Generar URL de descarga
            base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
            url_descarga = f"{base_url}/admin/reportes/descargar/{id_reporte}"
        
        # Obtener tamaño del archivo
        tamano_bytes = self.pdf_generator.obtener_tamano_archivo(pdf_buffer)
        
        # Guardar información del reporte en la base de datos
        fecha_generacion = datetime.now()
        fecha_expiracion = fecha_generacion + timedelta(hours=24)
        
        info_reporte = {
            'id_reporte': id_reporte,
            'nombre_archivo': nombre_archivo,
            'ruta_archivo': ruta_archivo,
            'tamano_bytes': tamano_bytes,
            'fecha_generacion': fecha_generacion,
            'fecha_expiracion': fecha_expiracion,
            'filtros_aplicados': filtros.dict(exclude_none=True),
            'total_registros': len(datos),
            'estado': 'disponible',
            'titulo_reporte': titulo_final,
            'incluyo_graficos': incluir_graficos
        }
        
        await self.repository.guardar_reporte_generado(info_reporte)
        
        # Preparar respuesta
        return {
            'id_reporte': id_reporte,
            'nombre_archivo': nombre_archivo,
            'url_descarga': url_descarga,
            'tamano_bytes': tamano_bytes,
            'fecha_generacion': fecha_generacion.isoformat(),
            'expira_en': '24 horas',
            'total_registros': len(datos),
            'pdf_buffer': pdf_buffer  # Para uso interno
        }
    
    async def enviar_reporte(
        self,
        id_reporte: str,
        correo_destino: Union[str, List[str]],
        asunto: Optional[str] = None,
        mensaje_personalizado: Optional[str] = None,
        copias: Optional[List[str]] = None,
        copias_ocultas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Envía un reporte previamente generado por correo electrónico.
        
        Args:
            id_reporte: ID del reporte a enviar
            correo_destino: Email(s) de destino
            asunto: Asunto del correo
            mensaje_personalizado: Mensaje adicional
            copias: Emails en copia (CC)
            copias_ocultas: Emails en copia oculta (BCC)
            
        Returns:
            Diccionario con información del envío
        """
        # Obtener información del reporte
        reporte = await self.repository.obtener_reporte_por_id(id_reporte)
        
        if not reporte:
            raise ValueError("El reporte especificado no existe o ha expirado")
        
        # Verificar si ha expirado
        if reporte.get('fecha_expiracion'):
            if datetime.now() > reporte['fecha_expiracion']:
                raise ValueError("El enlace del reporte ha expirado")
        
        # Cargar archivo PDF
        ruta_archivo = reporte.get('ruta_archivo')
        
        if not ruta_archivo or not os.path.exists(ruta_archivo):
            raise ValueError("El archivo del reporte no está disponible")
        
        with open(ruta_archivo, 'rb') as f:
            pdf_buffer = BytesIO(f.read())
        
        # Preparar asunto
        asunto_final = asunto or f"Reporte ExpoSoftware - {reporte.get('titulo_reporte', 'Proyectos')}"
        
        # Enviar correo
        resultado_envio = await self.email_service.enviar_reporte(
            destinatarios=correo_destino,
            asunto=asunto_final,
            nombre_archivo=reporte['nombre_archivo'],
            contenido_pdf=pdf_buffer,
            mensaje_personalizado=mensaje_personalizado,
            copias=copias,
            copias_ocultas=copias_ocultas
        )
        
        if not resultado_envio.get('exitoso'):
            raise Exception(resultado_envio.get('mensaje', 'Error al enviar el correo'))
        
        # Generar ID de envío
        id_envio = f"ENV_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Normalizar destinatarios para respuesta
        if isinstance(correo_destino, str):
            correo_destino = [correo_destino]
        
        return {
            'enviado_a': correo_destino,
            'fecha_envio': datetime.now().isoformat(),
            'id_envio': id_envio
        }
    
    async def generar_y_enviar_reporte(
        self,
        filtros: FiltrosReporte,
        correo_destino: Union[str, List[str]],
        titulo_reporte: Optional[str] = None,
        asunto: Optional[str] = None,
        mensaje_personalizado: Optional[str] = None,
        incluir_graficos: bool = True,
        copias: Optional[List[str]] = None,
        guardar_reporte: bool = False
    ) -> Dict[str, Any]:
        """
        Genera y envía un reporte en una sola operación.
        
        Args:
            filtros: Filtros para generar el reporte
            correo_destino: Email(s) de destino
            titulo_reporte: Título del reporte
            asunto: Asunto del correo
            mensaje_personalizado: Mensaje adicional
            incluir_graficos: Si incluir gráficos
            copias: Emails en copia (CC)
            guardar_reporte: Si guardar el reporte en el servidor
            
        Returns:
            Diccionario con información del reporte y envío
        """
        # Generar reporte
        resultado_generacion = await self.generar_reporte(
            filtros=filtros,
            titulo_reporte=titulo_reporte,
            incluir_graficos=incluir_graficos,
            guardar_en_servidor=guardar_reporte
        )
        
        # Preparar asunto
        asunto_final = asunto or f"Reporte ExpoSoftware - {titulo_reporte or 'Proyectos'}"
        
        # Enviar por correo
        pdf_buffer = resultado_generacion.pop('pdf_buffer')
        
        resultado_envio = await self.email_service.enviar_reporte(
            destinatarios=correo_destino,
            asunto=asunto_final,
            nombre_archivo=resultado_generacion['nombre_archivo'],
            contenido_pdf=pdf_buffer,
            mensaje_personalizado=mensaje_personalizado,
            copias=copias
        )
        
        if not resultado_envio.get('exitoso'):
            raise Exception(resultado_envio.get('mensaje', 'Error al enviar el correo'))
        
        # Normalizar destinatarios
        if isinstance(correo_destino, str):
            correo_destino = [correo_destino]
        
        # Preparar respuesta combinada
        return {
            'id_reporte': resultado_generacion['id_reporte'],
            'enviado_a': correo_destino,
            'fecha_generacion': resultado_generacion['fecha_generacion'],
            'fecha_envio': datetime.now().isoformat(),
            'url_descarga': resultado_generacion.get('url_descarga'),
            'total_registros': resultado_generacion['total_registros']
        }
    
    async def obtener_reporte_para_descarga(self, id_reporte: str) -> tuple[str, BytesIO]:
        """
        Obtiene un reporte para descarga.
        
        Args:
            id_reporte: ID del reporte
            
        Returns:
            Tupla con (nombre_archivo, contenido_pdf)
        """
        # Obtener información del reporte
        reporte = await self.repository.obtener_reporte_por_id(id_reporte)
        
        if not reporte:
            raise ValueError("El reporte no existe o el enlace ha expirado")
        
        # Verificar expiración
        if reporte.get('fecha_expiracion'):
            if datetime.now() > reporte['fecha_expiracion']:
                raise ValueError("El enlace de descarga ha expirado")
        
        # Cargar archivo
        ruta_archivo = reporte.get('ruta_archivo')
        
        if not ruta_archivo or not os.path.exists(ruta_archivo):
            raise ValueError("El archivo del reporte no está disponible")
        
        with open(ruta_archivo, 'rb') as f:
            pdf_buffer = BytesIO(f.read())
        
        return reporte['nombre_archivo'], pdf_buffer
    
    async def obtener_historial(
        self,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        limite: int = 20,
        pagina: int = 1
    ) -> Dict[str, Any]:
        """
        Obtiene el historial de reportes generados.
        
        Args:
            fecha_desde: Fecha inicial del rango
            fecha_hasta: Fecha final del rango
            limite: Cantidad de registros por página
            pagina: Número de página
            
        Returns:
            Diccionario con reportes y paginación
        """
        reportes, total = await self.repository.obtener_historial_reportes(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limite=limite,
            pagina=pagina
        )
        
        # Calcular total de páginas
        total_paginas = (total + limite - 1) // limite
        
        return {
            'reportes': reportes,
            'paginacion': {
                'total': total,
                'pagina_actual': pagina,
                'total_paginas': total_paginas,
                'limite': limite
            }
        }
    
    async def eliminar_reporte(self, id_reporte: str) -> bool:
        """
        Elimina un reporte del sistema.
        
        Args:
            id_reporte: ID del reporte a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        # Obtener información del reporte
        reporte = await self.repository.obtener_reporte_por_id(id_reporte)
        
        if not reporte:
            raise ValueError("El reporte no existe")
        
        # Eliminar archivo físico si existe
        ruta_archivo = reporte.get('ruta_archivo')
        if ruta_archivo and os.path.exists(ruta_archivo):
            try:
                os.remove(ruta_archivo)
            except Exception as e:
                print(f"Error eliminando archivo: {str(e)}")
        
        # Eliminar de la base de datos
        return await self.repository.eliminar_reporte(id_reporte)
    
    async def limpiar_reportes_expirados(self) -> int:
        """
        Limpia reportes que han expirado.
        
        Returns:
            Cantidad de reportes eliminados
        """
        # Esta función puede ejecutarse como tarea programada
        fecha_actual = datetime.now()
        eliminados = 0
        
        # Obtener todos los reportes (se puede optimizar con consulta específica)
        reportes, _ = await self.repository.obtener_historial_reportes(
            limite=1000,
            pagina=1
        )
        
        for reporte in reportes:
            if reporte.get('fecha_expiracion'):
                if fecha_actual > reporte['fecha_expiracion']:
                    try:
                        await self.eliminar_reporte(reporte['id'])
                        eliminados += 1
                    except Exception as e:
                        print(f"Error eliminando reporte expirado: {str(e)}")
        
        return eliminados