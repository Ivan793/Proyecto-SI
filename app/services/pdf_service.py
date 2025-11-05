# app/services/pdf_service.py

import os
import logging
from io import BytesIO
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import json

import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class PDFService:
    """
    Servicio especializado para gestión de archivos PDF en Cloudinary.
    Optimizado para certificados y documentos académicos.
    """
    
    def __init__(self):
        """Inicializa la configuración de Cloudinary"""
        # PRIMERO: Definir atributos
        self.folder_base = settings.CLOUDINARY_STORAGE_FOLDER
        self.folder_certificados = f"{self.folder_base}/{settings.CLOUDINARY_CERTIFICATES_FOLDER}"
        self.folder_reportes = f"{self.folder_base}/{settings.CLOUDINARY_REPORTS_FOLDER}"
        self.folder_temporal = f"{self.folder_base}/temporal"
        
        # LUEGO: Configurar Cloudinary
        self._configurar_cloudinary()
    
    def _configurar_cloudinary(self):
        """Configura las credenciales de Cloudinary"""
        try:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True
            )
            logger.info("✅ Cloudinary configurado correctamente")
            logger.info(f"📁 Folder base: {self.folder_base}")
        except Exception as e:
            logger.error(f"❌ Error configurando Cloudinary: {str(e)}")
            # No lanzamos excepción para permitir funcionamiento sin Cloudinary
    
    def _esta_configurado(self) -> bool:
        """Verifica si Cloudinary está configurado correctamente"""
        return all([
            settings.CLOUDINARY_CLOUD_NAME,
            settings.CLOUDINARY_API_KEY,
            settings.CLOUDINARY_API_SECRET
        ])
    
    async def subir_certificado(
        self,
        pdf_buffer: BytesIO,
        nombre_archivo: str,
        metadata: Optional[Dict[str, Any]] = None,
        folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sube un certificado PDF a Cloudinary con metadata específica.
        
        Args:
            pdf_buffer: Buffer del PDF
            nombre_archivo: Nombre del archivo
            metadata: Metadatos adicionales
            folder: Carpeta en Cloudinary (opcional)
            
        Returns:
            Dict con información del archivo subido
        """
        if not self._esta_configurado():
            logger.warning("⚠️ Cloudinary no configurado - omitiendo subida")
            return self._simular_subida(pdf_buffer, nombre_archivo, metadata)
        
        try:
            # Preparar opciones de upload
            upload_folder = folder or self.folder_certificados
            public_id = nombre_archivo.replace('.pdf', '')
            
            upload_options = {
                "resource_type": "raw",
                "folder": upload_folder,
                "public_id": public_id,
                "tags": ["certificado", "academico", "exposoftware"],
                "use_filename": True,
                "unique_filename": False,
            }
            
            # Agregar metadata si existe
            if metadata:
                upload_options["context"] = f"metadata={json.dumps(metadata)}"
            
            # Subir archivo
            pdf_buffer.seek(0)
            result = cloudinary.uploader.upload(
                pdf_buffer,
                **upload_options
            )
            
            logger.info(f"✅ Certificado subido a Cloudinary: {result['public_id']}")
            
            return {
                'public_id': result['public_id'],
                'secure_url': result['secure_url'],
                'url': result['url'],
                'format': result.get('format', 'pdf'),
                'bytes': result['bytes'],
                'created_at': result['created_at'],
                'resource_type': result['resource_type'],
                'folder': result.get('folder', upload_folder),
                'version': result.get('version'),
                'signature': result.get('signature'),
                'type': 'cloudinary'
            }
            
        except Exception as e:
            logger.error(f"❌ Error subiendo certificado a Cloudinary: {str(e)}")
            # Fallback: simular subida
            return self._simular_subida(pdf_buffer, nombre_archivo, metadata)
    
    async def subir_lote_certificados(
        self,
        certificados: List[Dict],
        nombre_lote: str,
        metadata_comun: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sube un lote de certificados a Cloudinary.
        
        Args:
            certificados: Lista de dicts con 'buffer' y 'nombre'
            nombre_lote: Identificador del lote
            metadata_comun: Metadata común para todos los certificados
            
        Returns:
            Dict con resultados del lote
        """
        if not self._esta_configurado():
            logger.warning("⚠️ Cloudinary no configurado - omitiendo subida de lote")
            return self._simular_subida_lote(certificados, nombre_lote, metadata_comun)
        
        try:
            folder_lote = f"{self.folder_certificados}/lotes/{nombre_lote}"
            resultados = []
            
            for cert in certificados:
                try:
                    # Agregar metadata específica del certificado
                    metadata_cert = metadata_comun.copy() if metadata_comun else {}
                    metadata_cert.update({
                        'lote': nombre_lote,
                        'timestamp': datetime.now().isoformat(),
                        'estudiante_id': cert.get('estudiante', {}).get('id_estudiante', ''),
                        'estudiante_nombre': f"{cert.get('estudiante', {}).get('nombres', '')} {cert.get('estudiante', {}).get('apellidos', '')}".strip()
                    })
                    
                    # Subir certificado individual
                    resultado = await self.subir_certificado(
                        pdf_buffer=cert['buffer'],
                        nombre_archivo=cert['nombre'],
                        metadata=metadata_cert,
                        folder=folder_lote
                    )
                    
                    resultados.append({
                        'nombre_archivo': cert['nombre'],
                        'public_id': resultado['public_id'],
                        'url': resultado['secure_url'],
                        'estudiante': cert.get('estudiante', {}),
                        'exitoso': True
                    })
                    
                except Exception as e:
                    logger.error(f"❌ Error subiendo certificado {cert.get('nombre')}: {str(e)}")
                    resultados.append({
                        'nombre_archivo': cert.get('nombre'),
                        'error': str(e),
                        'exitoso': False
                    })
                    continue
            
            logger.info(f"✅ Lote {nombre_lote} procesado: {len([r for r in resultados if r['exitoso']])}/{len(resultados)} exitosos")
            
            return {
                'lote': nombre_lote,
                'total_certificados': len(certificados),
                'subidos_exitosamente': len([r for r in resultados if r['exitoso']]),
                'errores': len([r for r in resultados if not r['exitoso']]),
                'folder': folder_lote,
                'certificados': resultados,
                'fecha_subida': datetime.now().isoformat(),
                'tipo': 'cloudinary'
            }
            
        except Exception as e:
            logger.error(f"❌ Error subiendo lote de certificados: {str(e)}")
            return self._simular_subida_lote(certificados, nombre_lote, metadata_comun)
    
    async def descargar_pdf(
        self,
        public_id: str,
        resource_type: str = "raw"
    ) -> Tuple[str, BytesIO]:
        """
        Descarga un PDF desde Cloudinary.
        
        Args:
            public_id: ID público del recurso
            resource_type: Tipo de recurso (raw para PDF)
            
        Returns:
            Tuple (nombre_archivo, buffer_del_pdf)
        """
        if not self._esta_configurado():
            logger.warning("⚠️ Cloudinary no configurado - no se puede descargar")
            raise ValueError("Cloudinary no está configurado")
        
        try:
            # Generar URL de descarga
            url, options = cloudinary_url(
                public_id,
                resource_type=resource_type,
                flags="attachment"
            )
            
            # Descargar contenido
            import requests
            response = requests.get(url)
            response.raise_for_status()
            
            # Crear buffer
            pdf_buffer = BytesIO(response.content)
            nombre_archivo = f"{public_id.split('/')[-1]}.pdf"
            
            logger.info(f"✅ PDF descargado desde Cloudinary: {public_id}")
            
            return nombre_archivo, pdf_buffer
            
        except Exception as e:
            logger.error(f"❌ Error descargando PDF {public_id}: {str(e)}")
            raise
    
    async def generar_url_descarga(
        self,
        public_id: str,
        expiracion_minutos: int = 60,
        nombre_archivo: Optional[str] = None
    ) -> str:
        """
        Genera una URL de descarga directa para un PDF.
        
        Args:
            public_id: ID público del recurso
            expiracion_minutos: Minutos hasta que expire la URL (Cloudinary no expira URLs por defecto)
            nombre_archivo: Nombre personalizado para descarga
            
        Returns:
            URL de descarga
        """
        if not self._esta_configurado():
            logger.warning("⚠️ Cloudinary no configurado - generando URL simulada")
            return f"/api/certificados/descargar/{public_id}"
        
        try:
            # Opciones para la URL
            options = {
                "resource_type": "raw",
                "secure": True
            }
            
            # Agregar nombre de archivo si se especifica
            if nombre_archivo:
                options["attachment"] = nombre_archivo
            
            # Generar URL
            url, _ = cloudinary_url(public_id, **options)
            
            logger.info(f"✅ URL de descarga generada para: {public_id}")
            
            return url
            
        except Exception as e:
            logger.error(f"❌ Error generando URL de descarga: {str(e)}")
            raise
    
    async def eliminar_pdf(
        self,
        public_id: str,
        resource_type: str = "raw"
    ) -> bool:
        """
        Elimina un PDF de Cloudinary.
        
        Args:
            public_id: ID público del recurso
            resource_type: Tipo de recurso
            
        Returns:
            True si se eliminó correctamente
        """
        if not self._esta_configurado():
            logger.warning("⚠️ Cloudinary no configurado - omitiendo eliminación")
            return True
        
        try:
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type
            )
            
            if result.get('result') == 'ok':
                logger.info(f"✅ PDF eliminado de Cloudinary: {public_id}")
                return True
            else:
                logger.warning(f"⚠️ No se pudo eliminar PDF: {public_id} - {result.get('result')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error eliminando PDF {public_id}: {str(e)}")
            return False
    
    async def obtener_informacion_recurso(
        self,
        public_id: str,
        resource_type: str = "raw"
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene información detallada de un recurso en Cloudinary.
        
        Args:
            public_id: ID público del recurso
            resource_type: Tipo de recurso
            
        Returns:
            Dict con información del recurso o None si no existe
        """
        if not self._esta_configurado():
            logger.warning("⚠️ Cloudinary no configurado - no se puede obtener información")
            return None
        
        try:
            result = cloudinary.api.resource(
                public_id,
                resource_type=resource_type
            )
            
            return {
                'public_id': result['public_id'],
                'secure_url': result['secure_url'],
                'bytes': result['bytes'],
                'format': result['format'],
                'created_at': result['created_at'],
                'folder': result.get('folder'),
                'context': result.get('context', {}),
                'tags': result.get('tags', [])
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo información del recurso {public_id}: {str(e)}")
            return None
    
    async def listar_certificados(
        self,
        prefix: Optional[str] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Lista certificados en Cloudinary.
        
        Args:
            prefix: Prefijo para filtrar por folder
            max_results: Máximo número de resultados
            
        Returns:
            Dict con lista de certificados
        """
        if not self._esta_configurado():
            logger.warning("⚠️ Cloudinary no configurado - no se pueden listar certificados")
            return {'recursos': [], 'total': 0}
        
        try:
            # Construir parámetros de búsqueda
            search_params = {
                "resource_type": "raw",
                "type": "upload",
                "max_results": max_results
            }
            
            if prefix:
                search_params["prefix"] = f"{self.folder_certificados}/{prefix}"
            else:
                search_params["prefix"] = self.folder_certificados
            
            # Ejecutar búsqueda
            result = cloudinary.api.resources(**search_params)
            
            recursos = []
            for recurso in result.get('resources', []):
                recursos.append({
                    'public_id': recurso['public_id'],
                    'secure_url': recurso['secure_url'],
                    'bytes': recurso['bytes'],
                    'format': recurso['format'],
                    'created_at': recurso['created_at'],
                    'folder': recurso.get('folder')
                })
            
            return {
                'recursos': recursos,
                'total': len(recursos)
            }
            
        except Exception as e:
            logger.error(f"❌ Error listando certificados: {str(e)}")
            return {'recursos': [], 'total': 0}
    
    def _simular_subida(
        self,
        pdf_buffer: BytesIO,
        nombre_archivo: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Simula una subida cuando Cloudinary no está configurado"""
        pdf_buffer.seek(0)
        content = pdf_buffer.read()
        
        return {
            'public_id': f"local_{nombre_archivo.replace('.pdf', '')}",
            'secure_url': f"/api/certificados/local/{nombre_archivo}",
            'url': f"/api/certificados/local/{nombre_archivo}",
            'format': 'pdf',
            'bytes': len(content),
            'created_at': datetime.now().isoformat(),
            'resource_type': 'raw',
            'folder': 'local',
            'type': 'local',
            'metadata': metadata or {}
        }
    
    def _simular_subida_lote(
        self,
        certificados: List[Dict],
        nombre_lote: str,
        metadata_comun: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Simula subida de lote cuando Cloudinary no está configurado"""
        resultados = []
        
        for cert in certificados:
            resultados.append({
                'nombre_archivo': cert['nombre'],
                'public_id': f"local_{cert['nombre'].replace('.pdf', '')}",
                'url': f"/api/certificados/local/{cert['nombre']}",
                'estudiante': cert.get('estudiante', {}),
                'exitoso': True,
                'type': 'local'
            })
        
        return {
            'lote': nombre_lote,
            'total_certificados': len(certificados),
            'subidos_exitosamente': len(certificados),
            'errores': 0,
            'folder': f"local/lotes/{nombre_lote}",
            'certificados': resultados,
            'fecha_subida': datetime.now().isoformat(),
            'tipo': 'local'
        }

# Instancia global del servicio
pdf_service = PDFService()