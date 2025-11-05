# app/services/certificate_service.py

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta, timezone
from io import BytesIO
import os
import uuid
import zipfile
import logging
import requests 
from app.services.certificate_generator import CertificateGenerator
from app.services.email_service import EmailService
from app.services.pdf_service import pdf_service  # ✅ NUEVO: Importar servicio de Cloudinary
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.proyect_repository import ProyectoRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.event_repository import EventRepository

from app.schemas.certificate import (
    DatosEstudianteCertificado,
    DatosProyectoCertificado,
    DatosEventoCertificado,
    EstadoCertificadoEnum,
    FormatoSalidaEnum,
    GenerarCertificadoPorProyectoRequest,
    GenerarCertificadoIndividualRequest,
    GenerarMiCertificadoRequest,
    EnviarCertificadosRequest,
    EstudianteCertificadoInfo,
    ProyectoCertificadoInfo
)

logger = logging.getLogger(__name__)


class CertificateService:
    """Servicio principal para gestión de certificados"""
    
    def __init__(self):
        self.generator = CertificateGenerator()
        self.email_service = EmailService()
        self.certificate_repo = CertificateRepository()
        self.project_repo = ProyectoRepository()
        self.student_repo = StudentRepository()
        self.user_repo = UserRepository()
        self.event_repo = EventRepository()
        self.pdf_service = pdf_service  # ✅ NUEVO: Servicio de Cloudinary
        
        # Usar /tmp para Lambda (fallback local)
        self.directorio_certificados = "/tmp/certificados_temp"
        self._asegurar_directorio()
    
    def _asegurar_directorio(self):
        """Crea el directorio de certificados si no existe"""
        if not os.path.exists(self.directorio_certificados):
            os.makedirs(self.directorio_certificados)
            logger.info(f"📁 Directorio creado: {self.directorio_certificados}")
        
        logger.info(f"📂 Directorio de certificados: {self.directorio_certificados}")
    
    def _generar_id_lote(self) -> str:
        """Genera un ID único para el lote de certificados"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"CERT_{timestamp}"
    
    def _generar_id_certificado_individual(self) -> str:
        """Genera un ID único para un certificado individual"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"CERT_IND_{timestamp}_{unique_id}"
    
    def _obtener_base_url(self) -> str:
        """Obtiene la URL base de la API según el entorno"""
        from app.core.config import get_settings
        settings = get_settings()
        
        # Intentar obtener de variable de entorno primero
        if settings.API_BASE_URL:
            return settings.API_BASE_URL.rstrip('/')
        
        # Si estamos en Lambda, usar la URL de Lambda
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
            return "https://z6gasdnp5zp6v6egg4kg3jsitu0ffcqu.lambda-url.us-east-1.on.aws"
        
        # Fallback para desarrollo local
        return "http://localhost:8000"
    
    async def _obtener_datos_estudiante(
        self,
        id_estudiante: str
    ) -> DatosEstudianteCertificado:
        """
        Obtiene los datos del estudiante para el certificado usando el ID del documento estudiante.
        """
        
        logger.info(f"🔍 Obteniendo datos del estudiante con ID documento: {id_estudiante}")
        
        estudiante = await self.student_repo.get_by_id(id_estudiante)
        if not estudiante:
            logger.error(f"❌ Estudiante con ID {id_estudiante} no encontrado")
            raise ValueError(f"Estudiante con ID {id_estudiante} no encontrado")
        
        logger.info(f"✅ Estudiante encontrado. Código programa: {estudiante.get('codigo_programa')}")
        
        uid_usuario = estudiante.get('id_usuario')
        if not uid_usuario:
            logger.error(f"❌ Estudiante {id_estudiante} no tiene id_usuario asociado")
            raise ValueError(f"El estudiante no tiene un usuario asociado")
        
        logger.info(f"🔗 UID de usuario encontrado: {uid_usuario}")
        
        usuario = await self.user_repo.get_by_id(uid_usuario)
        if not usuario:
            logger.error(f"❌ Usuario con UID {uid_usuario} no encontrado")
            raise ValueError(f"Usuario con UID {uid_usuario} no encontrado")
        
        primer_nombre = usuario.get('primer_nombre', '')
        segundo_nombre = usuario.get('segundo_nombre', '')
        primer_apellido = usuario.get('primer_apellido', '')
        segundo_apellido = usuario.get('segundo_apellido', '')
        
        nombres = f"{primer_nombre} {segundo_nombre}".strip()
        apellidos = f"{primer_apellido} {segundo_apellido}".strip()
        
        if not primer_nombre or not primer_apellido:
            logger.error(f"❌ Usuario {uid_usuario} no tiene nombres/apellidos completos")
            raise ValueError(f"El usuario no tiene datos completos")
        
        logger.info(f"✅ Usuario encontrado: {nombres} {apellidos}")
        
        identificacion = usuario.get('identificacion', '')
        correo = usuario.get('correo', '')
        nombre_programa = estudiante.get('codigo_programa', '')
        
        return DatosEstudianteCertificado(
            id_estudiante=id_estudiante,
            nombres=nombres,
            apellidos=apellidos,
            identificacion=identificacion,
            codigo_programa=estudiante.get('codigo_programa', ''),
            nombre_programa=nombre_programa,
            correo=correo
        )
    
    async def _obtener_datos_proyecto(
        self,
        id_proyecto: str
    ) -> DatosProyectoCertificado:
        """Obtiene los datos del proyecto para el certificado."""
        
        proyecto = await self.project_repo.get_by_id(id_proyecto)
        if not proyecto:
            raise ValueError(f"Proyecto con ID {id_proyecto} no encontrado")
        
        tipo_actividad = proyecto.get('tipo_actividad')
        if tipo_actividad is not None and not isinstance(tipo_actividad, str):
            tipo_actividad = str(tipo_actividad)
        
        calificacion = proyecto.get('calificacion')
        if calificacion is not None and not isinstance(calificacion, str):
            calificacion = str(calificacion)
        
        fecha_subida = proyecto.get('fecha_subida')
        if fecha_subida and isinstance(fecha_subida, str):
            try:
                fecha_subida = datetime.fromisoformat(fecha_subida.replace('Z', '+00:00'))
            except:
                fecha_subida = None
        
        return DatosProyectoCertificado(
            id_proyecto=id_proyecto,
            titulo_proyecto=proyecto['titulo_proyecto'],
            tipo_actividad=tipo_actividad,
            calificacion=calificacion,
            fecha_subida=fecha_subida
        )
    
    async def _obtener_datos_evento(
        self,
        id_evento: str
    ) -> DatosEventoCertificado:
        """Obtiene los datos del evento para el certificado"""
        
        evento = await self.event_repo.get_by_id(id_evento)
        if not evento:
            raise ValueError(f"Evento con ID {id_evento} no encontrado")
        
        return DatosEventoCertificado(
            id_evento=id_evento,
            nombre_evento=evento['nombre_evento'],
            fecha_inicio=evento['fecha_inicio'],
            fecha_fin=evento.get('fecha_fin'),
            lugar=evento.get('lugar')
        )
    
    async def _obtener_id_evento_desde_proyecto(
        self,
        id_proyecto: str
    ) -> str:
        """Obtiene el ID del evento asociado al proyecto"""
        
        proyecto = await self.project_repo.get_by_id(id_proyecto)
        if not proyecto:
            raise ValueError("Proyecto no encontrado")
        
        id_evento = proyecto.get('id_evento')
        if not id_evento:
            raise ValueError("El proyecto no está asociado a ningún evento")
        
        return id_evento
    
    async def generar_certificados_por_proyecto(
        self,
        request: GenerarCertificadoPorProyectoRequest
    ) -> Dict[str, Any]:
        """
        Genera certificados para todos los estudiantes de un proyecto.
        ✅ AHORA SUBE A CLOUDINARY AUTOMÁTICAMENTE
        """
        logger.info(f"📋 Generando certificados para proyecto: {request.id_proyecto}")
        
        # Obtener ID del evento
        id_evento = request.id_evento
        if not id_evento:
            id_evento = await self._obtener_id_evento_desde_proyecto(request.id_proyecto)
        
        logger.info(f"📅 ID Evento: {id_evento}")
        
        # Obtener datos del proyecto y evento
        datos_proyecto = await self._obtener_datos_proyecto(request.id_proyecto)
        datos_evento = await self._obtener_datos_evento(id_evento)
        
        logger.info(f"📄 Proyecto: {datos_proyecto.titulo_proyecto}")
        logger.info(f"🎪 Evento: {datos_evento.nombre_evento}")
        
        # Obtener UIDs de estudiantes del proyecto
        uids_estudiantes = await self.project_repo.get_students_by_project(request.id_proyecto)
        
        if not uids_estudiantes:
            raise ValueError("No se encontraron estudiantes asociados al proyecto")
        
        logger.info(f"🎓 Generando certificados para {len(uids_estudiantes)} estudiante(s)")
        
        # ✅ 1. GENERAR ID DEL LOTE PRIMERO
        id_lote = self._generar_id_lote()
        logger.info(f"🆔 ID Lote generado: {id_lote}")
        
        # Lista para almacenar certificados generados
        certificados_generados = []
        estudiantes_info = []
        
        # Generar certificado para cada estudiante
        for uid_estudiante in uids_estudiantes:
            try:
                logger.info(f"📄 Procesando estudiante UID: {uid_estudiante}")
                
                datos_estudiante = await self._obtener_datos_estudiante(uid_estudiante)
                
                # Generar PDF
                pdf_buffer = self.generator.generar_certificado(
                    estudiante=datos_estudiante,
                    proyecto=datos_proyecto,
                    evento=datos_evento,
                    incluir_calificacion=request.incluir_calificacion,
                    director_evento=request.director_evento,
                    coordinador_general=request.coordinador_general
                )
                
                # Nombre del archivo
                nombre_archivo = self.generator.obtener_nombre_archivo(datos_estudiante)
                
                certificados_generados.append({
                    'buffer': pdf_buffer,
                    'nombre': nombre_archivo,
                    'estudiante': datos_estudiante
                })
                
                estudiantes_info.append(EstudianteCertificadoInfo(
                    nombre_completo=f"{datos_estudiante.nombres} {datos_estudiante.apellidos}",
                    identificacion=datos_estudiante.identificacion,
                    nombre_archivo_certificado=nombre_archivo
                ))
                
                logger.info(f"✅ Certificado generado para: {datos_estudiante.nombres} {datos_estudiante.apellidos}")
                
            except Exception as e:
                logger.error(f"❌ Error generando certificado para estudiante {uid_estudiante}: {str(e)}")
                logger.exception(e)
                continue
        
        if not certificados_generados:
            raise ValueError("No se pudo generar ningún certificado")
        
        logger.info(f"📦 Empaquetando {len(certificados_generados)} certificado(s)")
        
        # ✅ 2. EMPAQUETAR CERTIFICADOS
        nombre_archivo_final, buffer_final = await self._empaquetar_certificados(
            certificados_generados,
            request.formato_salida,
            datos_proyecto.titulo_proyecto
        )
        
        # ✅ 3. GUARDAR LOCALMENTE (FALLBACK)
        ruta_archivo_local = os.path.join(self.directorio_certificados, nombre_archivo_final)
        with open(ruta_archivo_local, 'wb') as f:
            buffer_final.seek(0)
            f.write(buffer_final.read())
        
        tamano_bytes = os.path.getsize(ruta_archivo_local)
        logger.info(f"💾 Archivo guardado localmente: {ruta_archivo_local} ({tamano_bytes} bytes)")
        
        # ✅ 4. SUBIR ZIP A CLOUDINARY (AHORA id_lote YA EXISTE)
        cloudinary_info = None
        url_descarga_cloudinary = None
        
        try:
            # Preparar metadata para Cloudinary
            metadata_cloudinary = {
                'id_lote': id_lote,  # ✅ AHORA SÍ EXISTE
                'id_proyecto': request.id_proyecto,
                'id_evento': id_evento,
                'cantidad_certificados': len(certificados_generados),
                'fecha_generacion': datetime.now(timezone.utc).isoformat(),
                'proyecto': datos_proyecto.titulo_proyecto,
                'evento': datos_evento.nombre_evento
            }
            
            # Subir lote a Cloudinary
            buffer_final.seek(0)
            resultado_cloudinary = await self.pdf_service.subir_lote_certificados(
                certificados=[{
                    'buffer': buffer_final,
                    'nombre': nombre_archivo_final,
                    'estudiante': {'id': id_lote}
                }],
                nombre_lote=id_lote,
                metadata_comun=metadata_cloudinary
            )
            
            # Verificar resultado y extraer URL
            if resultado_cloudinary and resultado_cloudinary.get('tipo') == 'cloudinary':
                cloudinary_info = resultado_cloudinary
                
                # Extraer URL correctamente
                if cloudinary_info.get('certificados') and len(cloudinary_info['certificados']) > 0:
                    url_descarga_cloudinary = cloudinary_info['certificados'][0].get('url')
                    logger.info(f"☁️ Lote subido a Cloudinary: {url_descarga_cloudinary}")
                else:
                    logger.warning(f"⚠️ Respuesta de Cloudinary sin URL de certificado")
            else:
                logger.warning(f"⚠️ Cloudinary no configurado - usando almacenamiento local")
                
        except Exception as e:
            logger.error(f"❌ Error subiendo a Cloudinary: {str(e)}")
            logger.exception(e)
            logger.warning(f"⚠️ Continuando con almacenamiento local solamente")
        
        # ✅ 5. GENERAR URL DE DESCARGA
        base_url = self._obtener_base_url()
        
        # Prioridad: URL de Cloudinary > URL local
        if url_descarga_cloudinary:
            url_descarga = url_descarga_cloudinary
            logger.info(f"🔗 Usando URL de Cloudinary")
        else:
            url_descarga = f"{base_url}/api/v1/admin/reportes/certificados/descargar/{id_lote}"
            logger.info(f"🔗 Usando URL local: {url_descarga}")
        
        # ✅ 6. GUARDAR METADATA CON TIMEZONE
        fecha_generacion = datetime.now(timezone.utc)
        fecha_expiracion = fecha_generacion + timedelta(days=7)
        
        # ✅ 7. GUARDAR EN FIREBASE
        metadata_certificado = {
            'id_certificado': id_lote,
            'id_lote': id_lote,
            'id_estudiante': uids_estudiantes,  # Array de UIDs
            'id_proyecto': request.id_proyecto,
            'id_evento': id_evento,
            'nombre_archivo': nombre_archivo_final,
            'ruta_archivo': url_descarga_cloudinary if url_descarga_cloudinary else ruta_archivo_local,
            'fecha_generacion': fecha_generacion,
            'fecha_expiracion': fecha_expiracion,
            'estado': EstadoCertificadoEnum.DISPONIBLE,
            # ✅ AGREGAR ESTE CAMPO CON LA INFO COMPLETA DE ESTUDIANTES
            'estudiantes': [
                {
                    'id_estudiante': est.id_estudiante,
                    'nombre_completo': est.nombre_completo,
                    'identificacion': est.identificacion,
                    'nombre_archivo_certificado': est.nombre_archivo_certificado
                }
                for est in estudiantes_info
            ],
            'cantidad_certificados': len(certificados_generados),
            'cloudinary': {
                'subido': cloudinary_info is not None and cloudinary_info.get('tipo') == 'cloudinary',
                'url': url_descarga_cloudinary,
                'tipo': cloudinary_info.get('tipo', 'local') if cloudinary_info else 'local'
            }
        }
        
        await self.certificate_repo.guardar_lote_certificados(metadata_certificado)
        
        logger.info(f"🎉 Certificados generados exitosamente. Lote: {id_lote}")
        
        # ✅ 8. PREPARAR RESPUESTA
        return {
            'id_lote': id_lote,
            'nombre_archivo': nombre_archivo_final,
            'url_descarga': url_descarga,
            'cantidad_certificados': len(certificados_generados),
            'estudiantes': estudiantes_info,
            'tamano_bytes': tamano_bytes,
            'fecha_generacion': fecha_generacion.isoformat(),
            'expira_en': '7 días',
            'proyecto': ProyectoCertificadoInfo(
                titulo=datos_proyecto.titulo_proyecto,
                evento=datos_evento.nombre_evento,
                calificacion=datos_proyecto.calificacion if request.incluir_calificacion else None
            ),
            'cloudinary_subido': cloudinary_info is not None and cloudinary_info.get('tipo') == 'cloudinary',
            'tipo_descarga': 'cloudinary' if url_descarga_cloudinary else 'local'
        }

    async def generar_certificado_individual(
        self,
        request: GenerarCertificadoIndividualRequest
    ) -> Dict[str, Any]:
        """
        Genera un certificado individual para un estudiante.
        ✅ AHORA SUBE A CLOUDINARY AUTOMÁTICAMENTE
        """
        
        logger.info(f"📄 Generando certificado individual para estudiante: {request.id_estudiante}")
        
        # ✅ 1. GENERAR ID DEL CERTIFICADO PRIMERO
        id_certificado = self._generar_id_certificado_individual()
        logger.info(f"🆔 ID Certificado generado: {id_certificado}")
        
        # Obtener ID del evento desde el proyecto
        id_evento = await self._obtener_id_evento_desde_proyecto(request.id_proyecto)
        
        # Obtener datos
        datos_estudiante = await self._obtener_datos_estudiante(request.id_estudiante)
        datos_proyecto = await self._obtener_datos_proyecto(request.id_proyecto)
        datos_evento = await self._obtener_datos_evento(id_evento)
        
        logger.info(f"👤 Estudiante: {datos_estudiante.nombres} {datos_estudiante.apellidos}")
        logger.info(f"📄 Proyecto: {datos_proyecto.titulo_proyecto}")
        
        # ✅ 2. GENERAR PDF
        pdf_buffer = self.generator.generar_certificado(
            estudiante=datos_estudiante,
            proyecto=datos_proyecto,
            evento=datos_evento,
            incluir_calificacion=request.incluir_calificacion,
            director_evento=request.director_evento,
            coordinador_general=request.coordinador_general
        )
        
        nombre_archivo = self.generator.obtener_nombre_archivo(datos_estudiante)
        logger.info(f"📝 Nombre archivo: {nombre_archivo}")
        
        # ✅ 3. LEER EL CONTENIDO DEL PDF UNA SOLA VEZ
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read()
        logger.info(f"📦 PDF generado: {len(pdf_content)} bytes")
        
        # ✅ 4. GUARDAR LOCALMENTE (FALLBACK)
        ruta_archivo_local = os.path.join(self.directorio_certificados, nombre_archivo)
        with open(ruta_archivo_local, 'wb') as f:
            f.write(pdf_content)
        
        tamano_bytes = len(pdf_content)
        logger.info(f"💾 Archivo guardado localmente: {ruta_archivo_local} ({tamano_bytes} bytes)")
        
        # ✅ 5. SUBIR A CLOUDINARY (CON BUFFER NUEVO)
        cloudinary_info = None
        url_descarga_cloudinary = None
        
        try:
            # Preparar metadata
            metadata_cloudinary = {
                'id_certificado': id_certificado,
                'id_estudiante': request.id_estudiante,
                'id_proyecto': request.id_proyecto,
                'id_evento': id_evento,
                'fecha_generacion': datetime.now(timezone.utc).isoformat(),
                'estudiante': f"{datos_estudiante.nombres} {datos_estudiante.apellidos}",
                'identificacion': datos_estudiante.identificacion,
                'proyecto': datos_proyecto.titulo_proyecto,
                'evento': datos_evento.nombre_evento
            }
            
            # ✅ CREAR UN NUEVO BUFFER CON EL CONTENIDO
            pdf_buffer_cloudinary = BytesIO(pdf_content)
            
            # ✅ Subir como lote de un solo certificado
            resultado_cloudinary = await self.pdf_service.subir_lote_certificados(
                certificados=[{
                    'buffer': pdf_buffer_cloudinary,  # ✅ BUFFER NUEVO
                    'nombre': nombre_archivo,
                    'estudiante': datos_estudiante.__dict__
                }],
                nombre_lote=id_certificado,
                metadata_comun=metadata_cloudinary
            )
            
            # Verificar resultado y extraer URL
            if resultado_cloudinary and resultado_cloudinary.get('tipo') == 'cloudinary':
                cloudinary_info = resultado_cloudinary
                
                # Extraer URL del primer certificado
                if cloudinary_info.get('certificados') and len(cloudinary_info['certificados']) > 0:
                    url_descarga_cloudinary = cloudinary_info['certificados'][0].get('url')
                    logger.info(f"☁️ Certificado subido a Cloudinary: {url_descarga_cloudinary}")
                else:
                    logger.warning(f"⚠️ Respuesta de Cloudinary sin URL")
            else:
                logger.warning(f"⚠️ Cloudinary no configurado - usando almacenamiento local")
                
        except Exception as e:
            logger.error(f"❌ Error subiendo a Cloudinary: {str(e)}")
            logger.exception(e)
            logger.warning(f"⚠️ Continuando con almacenamiento local solamente")
        
        # ✅ 6. GENERAR URL DE DESCARGA
        base_url = self._obtener_base_url()
        
        # Prioridad: URL de Cloudinary > URL local
        if url_descarga_cloudinary:
            url_descarga = url_descarga_cloudinary
            logger.info(f"🔗 Usando URL de Cloudinary")
        else:
            url_descarga = f"{base_url}/api/v1/admin/reportes/certificados/descargar/{id_certificado}"
            logger.info(f"🔗 Usando URL local: {url_descarga}")
        
        # ✅ 7. GUARDAR METADATA CON TIMEZONE
        fecha_generacion = datetime.now(timezone.utc)
        fecha_expiracion = fecha_generacion + timedelta(days=7)
        
        # ✅ 8. GUARDAR EN FIREBASE
        metadata_certificado = {
            'id_certificado': id_certificado,
            'id_lote': None,
            'id_estudiante': [request.id_estudiante],
            'id_proyecto': request.id_proyecto,
            'id_evento': id_evento,
            'nombre_archivo': nombre_archivo,
            'ruta_archivo': url_descarga_cloudinary if url_descarga_cloudinary else ruta_archivo_local,
            'fecha_generacion': fecha_generacion,
            'fecha_expiracion': fecha_expiracion,
            'estado': EstadoCertificadoEnum.DISPONIBLE,
            'cloudinary': {
                'subido': cloudinary_info is not None and cloudinary_info.get('tipo') == 'cloudinary',
                'url': url_descarga_cloudinary,
                'tipo': cloudinary_info.get('tipo', 'local') if cloudinary_info else 'local'
            }
        }
        
        await self.certificate_repo.guardar_certificado_individual(metadata_certificado)
        
        logger.info(f"✅ Certificado individual generado: {nombre_archivo}")
        
        # ✅ 9. PREPARAR RESPUESTA
        return {
            'id_certificado': id_certificado,
            'nombre_archivo': nombre_archivo,
            'url_descarga': url_descarga,
            'estudiante': EstudianteCertificadoInfo(
                nombre_completo=f"{datos_estudiante.nombres} {datos_estudiante.apellidos}",
                identificacion=datos_estudiante.identificacion,
                nombre_archivo_certificado=nombre_archivo
            ),
            'proyecto': ProyectoCertificadoInfo(
                titulo=datos_proyecto.titulo_proyecto,
                evento=datos_evento.nombre_evento,
                calificacion=datos_proyecto.calificacion if request.incluir_calificacion else None
            ),
            'tamano_bytes': tamano_bytes,
            'fecha_generacion': fecha_generacion.isoformat(),
            'expira_en': '7 días',
            'cloudinary_subido': cloudinary_info is not None and cloudinary_info.get('tipo') == 'cloudinary',
            'tipo_descarga': 'cloudinary' if url_descarga_cloudinary else 'local'
        }
    
    def _crear_zip_certificados(self, certificados: List[Dict]) -> BytesIO:
        """Crea un archivo ZIP con todos los certificados"""
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for cert in certificados:
                cert['buffer'].seek(0)
                zipf.writestr(cert['nombre_archivo'], cert['buffer'].read())
        
        zip_buffer.seek(0)
        return zip_buffer
    
    async def _empaquetar_certificados(
        self,
        certificados: List[Dict],
        formato: FormatoSalidaEnum,
        titulo_proyecto: str
    ) -> tuple[str, BytesIO]:
        """Empaqueta los certificados según el formato especificado"""
        
        if formato == FormatoSalidaEnum.PDF_INDIVIDUAL and len(certificados) == 1:
            # Un solo PDF
            return certificados[0]['nombre'], certificados[0]['buffer']
        
        elif formato == FormatoSalidaEnum.ZIP:
            # Crear ZIP con todos los certificados
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            titulo_limpio = titulo_proyecto.lower().replace(' ', '_')[:30]
            nombre_zip = f"certificados_{titulo_limpio}_{timestamp}.zip"
            
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for cert in certificados:
                    cert['buffer'].seek(0)
                    zipf.writestr(cert['nombre'], cert['buffer'].read())
            
            zip_buffer.seek(0)
            return nombre_zip, zip_buffer
        
        else:
            # PDF_COMBINADO - concatenar todos los PDFs
            # Por ahora retornamos ZIP, implementación de merge requiere pypdf
            return await self._empaquetar_certificados(
                certificados,
                FormatoSalidaEnum.ZIP,
                titulo_proyecto
            )
    
    
    async def generar_mi_certificado(
        self,
        id_estudiante_autenticado: str,
        request: GenerarMiCertificadoRequest
    ) -> Dict[str, Any]:
        """
        Permite a un estudiante generar su propio certificado.
        ✅ AHORA SUBE A CLOUDINARY AUTOMÁTICAMENTE
        """
        
        logger.info(f"🎓 Estudiante {id_estudiante_autenticado} generando su certificado")
        
        # ✅ 1. GENERAR ID PRIMERO
        id_certificado = f"CERT_EST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🆔 ID Certificado generado: {id_certificado}")
        
        # Verificar que el proyecto pertenece al estudiante
        proyecto = await self.project_repo.get_by_id(request.id_proyecto)
        if not proyecto:
            raise ValueError("El proyecto especificado no existe")
        
        # Verificar que el estudiante está en el proyecto
        estudiantes_proyecto = proyecto.get('id_estudiantes', [])
        estudiante_encontrado = False
        
        for est_info in estudiantes_proyecto:
            if isinstance(est_info, dict):
                if est_info.get('id_estudiante') == id_estudiante_autenticado:
                    estudiante_encontrado = True
                    break
            elif isinstance(est_info, str) and est_info == id_estudiante_autenticado:
                estudiante_encontrado = True
                break
        
        if not estudiante_encontrado:
            raise ValueError("No tienes permiso para generar este certificado")
        
        # Verificar que el proyecto está asociado a un evento
        id_evento = proyecto.get('id_evento')
        if not id_evento:
            raise ValueError("El proyecto no está asociado a ningún evento")
        
        # Obtener datos
        datos_estudiante = await self._obtener_datos_estudiante(id_estudiante_autenticado)
        datos_proyecto = await self._obtener_datos_proyecto(request.id_proyecto)
        datos_evento = await self._obtener_datos_evento(id_evento)
        
        logger.info(f"👤 Estudiante: {datos_estudiante.nombres} {datos_estudiante.apellidos}")
        logger.info(f"📄 Proyecto: {datos_proyecto.titulo_proyecto}")
        
        # ✅ 2. GENERAR PDF
        pdf_buffer = self.generator.generar_certificado(
            estudiante=datos_estudiante,
            proyecto=datos_proyecto,
            evento=datos_evento,
            incluir_calificacion=request.incluir_calificacion
        )
        
        nombre_archivo = self.generator.obtener_nombre_archivo(datos_estudiante)
        logger.info(f"📝 Nombre archivo: {nombre_archivo}")
        
        # ✅ 3. LEER EL CONTENIDO DEL PDF UNA SOLA VEZ
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read()
        logger.info(f"📦 PDF generado: {len(pdf_content)} bytes")
        
        # ✅ 4. GUARDAR LOCALMENTE (FALLBACK)
        ruta_archivo_local = os.path.join(self.directorio_certificados, nombre_archivo)
        with open(ruta_archivo_local, 'wb') as f:
            f.write(pdf_content)
        
        tamano_bytes = len(pdf_content)
        logger.info(f"💾 Archivo guardado localmente: {ruta_archivo_local} ({tamano_bytes} bytes)")
        
        # ✅ 5. SUBIR A CLOUDINARY (CON BUFFER NUEVO)
        cloudinary_info = None
        url_descarga_cloudinary = None
        
        try:
            # Preparar metadata
            metadata_cloudinary = {
                'id_certificado': id_certificado,
                'id_estudiante': id_estudiante_autenticado,
                'id_proyecto': request.id_proyecto,
                'id_evento': id_evento,
                'fecha_generacion': datetime.now(timezone.utc).isoformat(),
                'estudiante': f"{datos_estudiante.nombres} {datos_estudiante.apellidos}",
                'identificacion': datos_estudiante.identificacion,
                'tipo': 'autogenerado',
                'proyecto': datos_proyecto.titulo_proyecto,
                'evento': datos_evento.nombre_evento
            }
            
            # ✅ CREAR UN NUEVO BUFFER CON EL CONTENIDO
            pdf_buffer_cloudinary = BytesIO(pdf_content)
            
            # ✅ Subir como lote de un solo certificado
            resultado_cloudinary = await self.pdf_service.subir_lote_certificados(
                certificados=[{
                    'buffer': pdf_buffer_cloudinary,  # ✅ BUFFER NUEVO
                    'nombre': nombre_archivo,
                    'estudiante': datos_estudiante.__dict__
                }],
                nombre_lote=id_certificado,
                metadata_comun=metadata_cloudinary
            )
            
            # Verificar resultado y extraer URL
            if resultado_cloudinary and resultado_cloudinary.get('tipo') == 'cloudinary':
                cloudinary_info = resultado_cloudinary
                
                # Extraer URL del primer certificado
                if cloudinary_info.get('certificados') and len(cloudinary_info['certificados']) > 0:
                    url_descarga_cloudinary = cloudinary_info['certificados'][0].get('url')
                    logger.info(f"☁️ Certificado subido a Cloudinary: {url_descarga_cloudinary}")
                else:
                    logger.warning(f"⚠️ Respuesta de Cloudinary sin URL")
            else:
                logger.warning(f"⚠️ Cloudinary no configurado - usando almacenamiento local")
                    
        except Exception as e:
            logger.error(f"❌ Error subiendo a Cloudinary: {str(e)}")
            logger.exception(e)
            logger.warning(f"⚠️ Continuando con almacenamiento local solamente")
        
        # ✅ 6. GENERAR URL DE DESCARGA
        base_url = self._obtener_base_url()
        
        # Prioridad: URL de Cloudinary > URL local
        if url_descarga_cloudinary:
            url_descarga = url_descarga_cloudinary
            logger.info(f"🔗 Usando URL de Cloudinary")
        else:
            url_descarga = f"{base_url}/api/v1/estudiante/certificados/descargar/{id_certificado}"
            logger.info(f"🔗 Usando URL local: {url_descarga}")
        
        # ✅ 7. GUARDAR METADATA CON TIMEZONE
        fecha_generacion = datetime.now(timezone.utc)
        fecha_expiracion = fecha_generacion + timedelta(days=7)
        
        # ✅ 8. GUARDAR EN FIREBASE
        metadata = {
            'id_certificado': id_certificado,
            'id_estudiante': id_estudiante_autenticado,
            'id_proyecto': request.id_proyecto,
            'id_evento': id_evento,
            'nombre_archivo': nombre_archivo,
            'ruta_archivo': url_descarga_cloudinary if url_descarga_cloudinary else ruta_archivo_local,
            'tamano_bytes': tamano_bytes,
            'fecha_generacion': fecha_generacion,
            'fecha_expiracion': fecha_expiracion,
            'estado': EstadoCertificadoEnum.DISPONIBLE,
            'enviado_correo': False,
            'cloudinary': {
                'subido': cloudinary_info is not None and cloudinary_info.get('tipo') == 'cloudinary',
                'url': url_descarga_cloudinary,
                'tipo': cloudinary_info.get('tipo', 'local') if cloudinary_info else 'local'
            }
        }
        
        await self.certificate_repo.guardar_certificado_individual(metadata)
        
        logger.info(f"✅ Certificado autogenerado guardado en Firebase")
        
        # ✅ 9. ENVIAR POR CORREO SI SE SOLICITA
        enviado_correo = False
        correo_destino = None
        
        if request.enviar_por_correo:
            try:
                # ✅ CREAR OTRO BUFFER NUEVO PARA EL CORREO
                pdf_buffer_correo = BytesIO(pdf_content)
                
                await self._enviar_certificado_por_correo(
                    pdf_buffer_correo,
                    nombre_archivo,
                    datos_estudiante.correo,
                    datos_estudiante.nombres
                )
                enviado_correo = True
                correo_destino = datos_estudiante.correo
                
                # Actualizar metadata
                await self.certificate_repo.actualizar_estado_envio(
                    id_certificado,
                    True
                )
                
                logger.info(f"📧 Certificado enviado por correo a: {correo_destino}")
                
            except Exception as e:
                logger.error(f"❌ Error enviando certificado por correo: {str(e)}")
                logger.exception(e)
        
        # ✅ 10. PREPARAR RESPUESTA
        return {
            'id_certificado': id_certificado,
            'nombre_archivo': nombre_archivo,
            'url_descarga': url_descarga,
            'proyecto': ProyectoCertificadoInfo(
                titulo=datos_proyecto.titulo_proyecto,
                evento=datos_evento.nombre_evento,
                calificacion=datos_proyecto.calificacion if request.incluir_calificacion else None
            ),
            'tamano_bytes': tamano_bytes,
            'fecha_generacion': fecha_generacion.isoformat(),
            'expira_en': '7 días',
            'enviado_correo': enviado_correo,
            'correo_destino': correo_destino,
            'cloudinary_subido': cloudinary_info is not None and cloudinary_info.get('tipo') == 'cloudinary',
            'tipo_descarga': 'cloudinary' if url_descarga_cloudinary else 'local'
        }
    
    async def enviar_certificados_por_correo(
        self,
        request: EnviarCertificadosRequest
    ) -> Dict[str, Any]:
        """
        Envía certificados por correo electrónico desde un lote generado previamente.
        Soporta descarga desde Cloudinary si el archivo local no existe.
        """ 
        
        try:
            logger.info(f"📧 Iniciando envío de certificados - Lote: {request.id_lote}")
            
            # 1. Obtener metadata del lote
            lote = await self.certificate_repo.obtener_por_id(request.id_lote)
            
            if not lote:
                raise ValueError(f"Lote de certificados {request.id_lote} no encontrado")
            
            cantidad_certificados = lote.get('cantidad_certificados', 0)
            student_ids = lote.get('id_estudiante', [])  # IDs de estudiantes
            
            logger.info(f"📦 Lote encontrado: {cantidad_certificados} certificados")
            logger.info(f"👥 IDs de estudiantes en lote: {len(student_ids)}")
            
            # ✅ VERIFICAR QUE HAYA ESTUDIANTES
            if not student_ids:
                raise ValueError("El lote no contiene información de estudiantes. Regenere el lote.")
            
            # ✅ OBTENER INFORMACIÓN COMPLETA DE CADA ESTUDIANTE
            estudiantes_completos = []
            for student_id in student_ids:
                try:
                    estudiante_info = await self._obtener_datos_estudiante(student_id)
                    estudiantes_completos.append({
                        'id_estudiante': student_id,
                        'nombre_completo': f"{estudiante_info.nombres} {estudiante_info.apellidos}",
                        'identificacion': estudiante_info.identificacion,
                        'correo': estudiante_info.correo,
                        'nombre_archivo_certificado': self.generator.obtener_nombre_archivo(estudiante_info)
                    })
                    logger.info(f"✅ Estudiante encontrado: {estudiante_info.nombres} {estudiante_info.apellidos} - {estudiante_info.correo}")
                except Exception as e:
                    logger.error(f"❌ Error obteniendo datos del estudiante {student_id}: {str(e)}")
                    continue
            
            if not estudiantes_completos:
                raise ValueError("No se pudo obtener información de ningún estudiante")
            
            logger.info(f"👥 Estudiantes con información completa: {len(estudiantes_completos)}")
            
            # 2. Verificar que no haya expirado
            if lote.get('fecha_expiracion'):
                fecha_exp = lote['fecha_expiracion']
                if isinstance(fecha_exp, str):
                    fecha_exp = datetime.fromisoformat(fecha_exp.replace('Z', '+00:00'))
                
                if datetime.now(timezone.utc) > fecha_exp:
                    raise ValueError("El lote de certificados ha expirado")
            
            # 3. Obtener archivo ZIP (local o desde Cloudinary)
            ruta_zip = lote.get('ruta_archivo')
            archivo_temporal = None
            
            # ✅ SI NO EXISTE LOCALMENTE, DESCARGAR DE CLOUDINARY
            if not ruta_zip or not os.path.exists(ruta_zip):
                logger.warning(f"⚠️ Archivo local no encontrado: {ruta_zip}")
                
                url_cloudinary = lote.get('cloudinary', {}).get('url')
                
                if not url_cloudinary:
                    raise ValueError("No se encontró URL de Cloudinary. El archivo no está disponible.")
                
                logger.info(f"☁️ Descargando desde Cloudinary: {url_cloudinary}")
                
                try:
                    response = requests.get(url_cloudinary, timeout=30)
                    response.raise_for_status()
                    
                    # Guardar temporalmente
                    archivo_temporal = os.path.join(
                        self.directorio_certificados,
                        f"temp_{request.id_lote}.zip"
                    )
                    
                    with open(archivo_temporal, 'wb') as f:
                        f.write(response.content)
                    
                    ruta_zip = archivo_temporal
                    logger.info(f"✅ Archivo descargado exitosamente ({len(response.content)} bytes)")
                    
                except requests.RequestException as e:
                    logger.error(f"❌ Error descargando de Cloudinary: {str(e)}")
                    raise ValueError(f"No se pudo descargar el archivo de certificados: {str(e)}")
            else:
                logger.info(f"📁 Usando archivo local: {ruta_zip}")
            
            # 4. Extraer y preparar certificados
            certificados_para_enviar = []
            
            try:
                with zipfile.ZipFile(ruta_zip, 'r') as zip_file:
                    archivos_en_zip = zip_file.namelist()
                    logger.info(f"📋 Archivos en ZIP: {len(archivos_en_zip)} - {archivos_en_zip[:3]}...")
                    
                    for estudiante_info in estudiantes_completos:
                        try:
                            nombre_archivo = estudiante_info.get('nombre_archivo_certificado')
                            nombre_completo = estudiante_info.get('nombre_completo', 'Estudiante')
                            correo_estudiante = estudiante_info.get('correo')
                            
                            if not nombre_archivo:
                                logger.warning(f"⚠️ {nombre_completo} sin nombre de archivo")
                                continue
                            
                            if not correo_estudiante:
                                logger.warning(f"⚠️ {nombre_completo} sin correo electrónico")
                                continue
                            
                            # Verificar que existe en el ZIP
                            if nombre_archivo not in archivos_en_zip:
                                logger.warning(f"⚠️ Archivo no encontrado en ZIP: {nombre_archivo}")
                                continue
                            
                            # Leer PDF
                            pdf_content = zip_file.read(nombre_archivo)
                            logger.info(f"✅ Leído: {nombre_archivo} ({len(pdf_content)} bytes)")
                            
                            certificados_para_enviar.append({
                                'correo': correo_estudiante,
                                'nombre': nombre_completo,
                                'nombre_archivo': nombre_archivo,
                                'contenido': pdf_content
                            })
                            
                            logger.info(f"✅ Preparado: {nombre_completo} → {correo_estudiante}")
                            
                        except Exception as e:
                            logger.error(f"❌ Error procesando {estudiante_info.get('nombre_completo')}: {str(e)}")
                            continue
                            
            except zipfile.BadZipFile:
                raise ValueError("El archivo no es un ZIP válido o está corrupto")
            finally:
                # Limpiar archivo temporal
                if archivo_temporal and os.path.exists(archivo_temporal):
                    try:
                        os.remove(archivo_temporal)
                        logger.info("🗑️ Archivo temporal eliminado")
                    except:
                        pass
            
            if not certificados_para_enviar:
                raise ValueError("No se pudieron preparar certificados para envío")
            
            logger.info(f"📬 {len(certificados_para_enviar)} certificados listos")
            
            # 5. Enviar certificados
            asunto = request.asunto or "Tu Certificado de Participación - ExpoSoftware"
            
            resultado_envio = await self.email_service.enviar_certificados_masivo(
                certificados=certificados_para_enviar,
                asunto_base=asunto,
                mensaje_personalizado=request.mensaje_personalizado
            )
            
            # 6. Actualizar estado
            if resultado_envio['exitosos'] > 0:
                await self.certificate_repo.actualizar_estado(
                    request.id_lote,
                    EstadoCertificadoEnum.ENVIADO
                )
            
            logger.info(f"✅ Envío completado: {resultado_envio['exitosos']}/{resultado_envio['total']}")
            
            return {
                'id_lote': request.id_lote,
                'total_certificados': resultado_envio['total'],
                'enviados_exitosamente': resultado_envio['exitosos'],
                'envios_fallidos': resultado_envio['fallidos'],
                'detalles_exitosos': resultado_envio['detalles_exitosos'],
                'detalles_fallidos': resultado_envio['detalles_fallidos'],
                'fecha_envio': resultado_envio['fecha_envio']
            }
            
        except Exception as e:
            logger.error(f"❌ Error en envío de certificados: {str(e)}")
            logger.exception(e)
            raise

    def _obtener_nombre_archivo_desde_estudiante(self, estudiante_info: dict) -> str:
        """
        Genera el nombre del archivo del certificado basado en la información del estudiante.
        """
        nombres = estudiante_info.get('nombres', '').replace(' ', '_')
        apellidos = estudiante_info.get('apellidos', '').replace(' ', '_')
        identificacion = estudiante_info.get('identificacion', '')
        
        nombre_archivo = f"certificado_{nombres}_{apellidos}_{identificacion}.pdf".lower()
        # Limpiar caracteres especiales
        nombre_archivo = ''.join(c for c in nombre_archivo if c.isalnum() or c in ['_', '.', '-'])
        
        return nombre_archivo

    async def _enviar_certificado_por_correo(
        self,
        pdf_buffer: BytesIO,
        nombre_archivo: str,
        correo_destino: str,
        nombre_estudiante: str
    ) -> bool:
        """Envía un certificado individual por correo electrónico."""
        try:
            pdf_buffer.seek(0)
            pdf_content = pdf_buffer.read()
            
            await self.email_service.enviar_certificado_individual(
                destinatario=correo_destino,
                nombre_estudiante=nombre_estudiante,
                nombre_archivo=nombre_archivo,
                contenido_pdf=pdf_content
            )
            
            logger.info(f"✅ Certificado enviado por correo a: {correo_destino}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando certificado por correo a {correo_destino}: {str(e)}")
            return False

    async def _obtener_correo_estudiante(self, identificacion: str) -> Optional[str]:
        """Obtiene el correo electrónico de un estudiante por su identificación."""
        try:
            # Buscar usuario por identificación
            usuario = await self.user_repo.get_by_identificacion(identificacion)
            
            if usuario and 'correo' in usuario:
                return usuario['correo']
            
            logger.warning(f"⚠️ No se encontró correo para identificación: {identificacion}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo correo de estudiante {identificacion}: {str(e)}")
            return None

    async def obtener_certificado_para_descarga(
        self,
        id_certificado: str,
        id_estudiante: Optional[str] = None
    ) -> tuple[str, BytesIO]:
        """
        Obtiene un certificado para descarga.
        Si id_estudiante se proporciona, valida que sea el propietario.
        """
        
        certificado = await self.certificate_repo.obtener_por_id(id_certificado)
        
        if not certificado:
            raise ValueError("El certificado no existe o ha expirado")
        
        # Validar propiedad si es estudiante
        if id_estudiante and certificado.get('id_estudiante') != id_estudiante:
            raise ValueError("No tienes permiso para descargar este certificado")
        
        # Verificar expiración con timezone aware
        if certificado.get('fecha_expiracion'):
            fecha_exp = certificado['fecha_expiracion']
            
            # Convertir a datetime si es necesario
            if isinstance(fecha_exp, str):
                fecha_exp = datetime.fromisoformat(fecha_exp.replace('Z', '+00:00'))
            
            # Comparar con datetime timezone-aware
            if datetime.now(timezone.utc) > fecha_exp:
                raise ValueError("El enlace de descarga ha expirado")
        
        # Cargar archivo
        ruta_archivo = certificado.get('ruta_archivo')
        if not ruta_archivo or not os.path.exists(ruta_archivo):
            logger.error(f"❌ Archivo no encontrado: {ruta_archivo}")
            raise ValueError("El archivo del certificado no está disponible")
        
        logger.info(f"📥 Descargando certificado desde: {ruta_archivo}")
        
        with open(ruta_archivo, 'rb') as f:
            pdf_buffer = BytesIO(f.read())
        
        return certificado['nombre_archivo'], pdf_buffer
    
    async def obtener_mis_certificados(
        self,
        id_estudiante: str,
        pagina: int = 1,
        limite: int = 20
    ) -> Dict[str, Any]:
        """Obtiene el listado de certificados de un estudiante"""
        
        certificados, total = await self.certificate_repo.obtener_por_estudiante(
            id_estudiante=id_estudiante,
            limite=limite,
            pagina=pagina
        )
        
        total_paginas = (total + limite - 1) // limite
        
        return {
            'certificados': certificados,
            'paginacion': {
                'total': total,
                'pagina_actual': pagina,
                'total_paginas': total_paginas,
                'limite': limite
            }
        }
    
    async def obtener_proyectos_disponibles(
        self,
        id_estudiante: str
    ) -> Dict[str, Any]:
        """Obtiene proyectos del estudiante elegibles para certificado"""
        
        # Obtener todos los proyectos del estudiante
        proyectos = await self.project_repo.get_by_student(id_estudiante)
        
        proyectos_disponibles = []
        
        for proyecto in proyectos:
            # Verificar que tenga evento asociado
            if not proyecto.get('id_evento'):
                continue
            
            # Obtener datos del evento
            evento = await self.event_repo.get_by_id(proyecto['id_evento'])
            if not evento:
                continue
            
            # Verificar si ya tiene certificado válido
            tiene_certificado = await self.certificate_repo.verificar_certificado_valido(
                id_estudiante=id_estudiante,
                id_proyecto=proyecto['id_proyecto']
            )
            
            proyectos_disponibles.append({
                'id_proyecto': proyecto['id_proyecto'],
                'titulo_proyecto': proyecto['titulo_proyecto'],
                'tipo_actividad': proyecto['tipo_actividad'],
                'evento': {
                    'id_evento': evento['id_evento'],
                    'nombre_evento': evento['nombre_evento'],
                    'fecha_evento': evento['fecha_inicio']
                },
                'calificacion': proyecto.get('calificacion'),
                'tiene_certificado': tiene_certificado,
                'fecha_expone': proyecto.get('fecha_exposicion')
            })
        
        return {
            'proyectos': proyectos_disponibles,
            'total': len(proyectos_disponibles)
        }
    
    async def obtener_lotes_certificados(
        self,
        pagina: int = 1,
        limite: int = 20
    ) -> Dict[str, Any]:
        """
        Obtiene un listado paginado de lotes de certificados con información completa.
        
        Args:
            pagina: Número de página
            limite: Cantidad de resultados por página
            
        Returns:
            Dict con listado de lotes y información de paginación
        """
        try:
            logger.info(f"📋 Obteniendo lotes de certificados - Página: {pagina}, Límite: {limite}")
            
            # Obtener lotes desde el repositorio
            lotes, total = await self.certificate_repo.obtener_lotes_paginados(
                pagina=pagina,
                limite=limite
            )
            
            logger.info(f"✅ {len(lotes)} lotes encontrados")
            
            # Enriquecer información de cada lote
            lotes_enriquecidos = []
            
            for lote in lotes:
                try:
                    # Obtener información del proyecto
                    proyecto_info = {}
                    if lote.get('id_proyecto'):
                        proyecto = await self.project_repo.get_by_id(lote['id_proyecto'])
                        if proyecto:
                            proyecto_info = {
                                'nombre_proyecto': proyecto.get('titulo_proyecto', 'Proyecto no encontrado'),
                                'tipo_actividad': proyecto.get('tipo_actividad'),
                                'calificacion': proyecto.get('calificacion')
                            }
                    
                    # Obtener información del evento
                    evento_info = {}
                    if lote.get('id_evento'):
                        evento = await self.event_repo.get_by_id(lote['id_evento'])
                        if evento:
                            evento_info = {
                                'nombre_evento': evento.get('nombre_evento', 'Evento no encontrado'),
                                'fecha_inicio': evento.get('fecha_inicio'),
                                'fecha_fin': evento.get('fecha_fin'),
                                'lugar': evento.get('lugar')
                            }
                    
                    # Construir lote enriquecido
                    lote_enriquecido = {
                        'id_lote': lote.get('id_lote') or lote.get('id_certificado'),
                        'id_proyecto': lote.get('id_proyecto'),
                        'proyecto': proyecto_info,
                        'evento': evento_info,
                        'cantidad_certificados': lote.get('cantidad_certificados', 0),
                        'nombre_archivo': lote.get('nombre_archivo'),
                        'fecha_generacion': lote.get('fecha_generacion'),
                        'fecha_expiracion': lote.get('fecha_expiracion'),
                        'estado': lote.get('estado', 'desconocido'),
                        'cloudinary_subido': lote.get('cloudinary', {}).get('subido', False),
                        'url_descarga': lote.get('cloudinary', {}).get('url') or f"{self._obtener_base_url()}/admin/reportes/certificados/descargar/{lote.get('id_lote') or lote.get('id_certificado')}",
                        'estudiantes': lote.get('id_estudiante', [])  # Array de IDs de estudiantes
                    }
                    
                    lotes_enriquecidos.append(lote_enriquecido)
                    
                except Exception as e:
                    logger.error(f"❌ Error enriqueciendo información del lote {lote.get('id_lote')}: {str(e)}")
                    # Agregar lote básico si hay error
                    lote_basico = {
                        'id_lote': lote.get('id_lote') or lote.get('id_certificado'),
                        'id_proyecto': lote.get('id_proyecto'),
                        'proyecto': {'nombre_proyecto': 'Error al cargar información'},
                        'evento': {'nombre_evento': 'Error al cargar información'},
                        'cantidad_certificados': lote.get('cantidad_certificados', 0),
                        'nombre_archivo': lote.get('nombre_archivo'),
                        'fecha_generacion': lote.get('fecha_generacion'),
                        'estado': lote.get('estado', 'desconocido'),
                        'cloudinary_subido': False,
                        'url_descarga': f"{self._obtener_base_url()}/admin/reportes/certificados/descargar/{lote.get('id_lote') or lote.get('id_certificado')}",
                        'estudiantes': lote.get('id_estudiante', [])
                    }
                    lotes_enriquecidos.append(lote_basico)
                    continue
            
            # Calcular paginación
            total_paginas = (total + limite - 1) // limite if total > 0 else 1
            
            return {
                'lotes': lotes_enriquecidos,
                'paginacion': {
                    'total': total,
                    'pagina_actual': pagina,
                    'total_paginas': total_paginas,
                    'limite': limite,
                    'siguiente_pagina': pagina + 1 if pagina < total_paginas else None,
                    'pagina_anterior': pagina - 1 if pagina > 1 else None
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo lotes de certificados: {str(e)}")
            raise