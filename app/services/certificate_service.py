# app/services/certificate_service.py

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta, timezone
from io import BytesIO
import os
import uuid
import zipfile
import logging

from app.services.certificate_generator import CertificateGenerator
from app.services.email_service import EmailService
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
        
        # ✅ CORRECCIÓN: Usar ruta relativa correcta
        self.directorio_certificados = os.path.join(
            os.getcwd(),  # Directorio actual del proyecto
            'storage',
            'certificados_temp'
        )
        self._asegurar_directorio()
    
    def _asegurar_directorio(self):
        """Crea el directorio de certificados si no existe"""
        # ✅ CORRECCIÓN: Asegurar que se cree la carpeta storage también
        storage_dir = os.path.join(os.getcwd(), 'storage')
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            logger.info(f"📁 Carpeta 'storage' creada")
        
        # Crear carpeta certificados_temp
        if not os.path.exists(self.directorio_certificados):
            os.makedirs(self.directorio_certificados)
            logger.info(f"📁 Carpeta 'certificados_temp' creada")
        
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
    
    async def _obtener_datos_estudiante(
        self,
        uid_estudiante: str
    ) -> DatosEstudianteCertificado:
        """
        Obtiene los datos del estudiante para el certificado usando el UID.
        
        Args:
            uid_estudiante: UID de Firebase Auth del estudiante
        
        Returns:
            DatosEstudianteCertificado con toda la información necesaria
        """
        
        logger.info(f"🔍 Obteniendo datos del estudiante con UID: {uid_estudiante}")
        
        # 1. Obtener el documento de estudiante usando id_usuario (que contiene el UID)
        estudiante = await self.student_repo.get_student_by_user_id(uid_estudiante)
        if not estudiante:
            logger.error(f"❌ Estudiante con UID {uid_estudiante} no encontrado en colección estudiantes")
            raise ValueError(f"Estudiante con UID {uid_estudiante} no encontrado en colección estudiantes")
        
        logger.info(f"✅ Estudiante encontrado. Código programa: {estudiante.get('codigo_programa')}")
        
        # 2. Obtener el usuario directamente usando el UID como ID de documento
        usuario = await self.user_repo.get_by_id(uid_estudiante)
        if not usuario:
            logger.error(f"❌ Usuario con UID {uid_estudiante} no encontrado en colección usuarios")
            raise ValueError(f"Usuario con UID {uid_estudiante} no encontrado en colección usuarios")
        
        logger.info(f"✅ Usuario encontrado: {usuario.get('nombres')} {usuario.get('apellidos')}")
        
        # 3. Obtener nombre del programa académico (opcional)
        nombre_programa = estudiante.get('codigo_programa')
        
        return DatosEstudianteCertificado(
            id_estudiante=uid_estudiante,
            nombres=usuario['nombres'],
            apellidos=usuario['apellidos'],
            identificacion=usuario['identificacion'],
            codigo_programa=estudiante['codigo_programa'],
            nombre_programa=nombre_programa,
            correo=usuario['correo']
        )
    
    async def _obtener_datos_proyecto(
        self,
        id_proyecto: str
    ) -> DatosProyectoCertificado:
        """
        Obtiene los datos del proyecto para el certificado.
        Maneja correctamente los tipos de datos de Firestore.
        """
        
        proyecto = await self.project_repo.get_by_id(id_proyecto)
        if not proyecto:
            raise ValueError(f"Proyecto con ID {id_proyecto} no encontrado")
        
        # ✅ CORRECCIÓN: Convertir tipo_actividad a string si es necesario
        tipo_actividad = proyecto.get('tipo_actividad')
        if tipo_actividad is not None and not isinstance(tipo_actividad, str):
            tipo_actividad = str(tipo_actividad)
        
        # Convertir calificación a string si es necesario
        calificacion = proyecto.get('calificacion')
        if calificacion is not None and not isinstance(calificacion, str):
            calificacion = str(calificacion)
        
        # Convertir fecha_subida si existe
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
        
        logger.info(f"📝 Proyecto: {datos_proyecto.titulo_proyecto}")
        logger.info(f"🎪 Evento: {datos_evento.nombre_evento}")
        
        # Obtener UIDs de estudiantes del proyecto
        uids_estudiantes = await self.project_repo.get_students_by_project(request.id_proyecto)
        
        if not uids_estudiantes:
            raise ValueError("No se encontraron estudiantes asociados al proyecto")
        
        logger.info(f"🎓 Generando certificados para {len(uids_estudiantes)} estudiante(s)")
        
        # Generar ID del lote
        id_lote = self._generar_id_lote()
        
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
        
        # Empaquetar según formato de salida
        nombre_archivo_final, buffer_final = await self._empaquetar_certificados(
            certificados_generados,
            request.formato_salida,
            datos_proyecto.titulo_proyecto
        )
        
        # Guardar en servidor
        ruta_archivo = os.path.join(self.directorio_certificados, nombre_archivo_final)
        with open(ruta_archivo, 'wb') as f:
            buffer_final.seek(0)
            f.write(buffer_final.read())
        
        # Obtener tamaño
        tamano_bytes = os.path.getsize(ruta_archivo)
        
        logger.info(f"💾 Archivo guardado: {ruta_archivo} ({tamano_bytes} bytes)")
        
        # Generar URL de descarga
        base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        url_descarga = f"{base_url}/admin/reportes/certificados/descargar/{id_lote}"
        
        # ✅ CORRECCIÓN: Guardar metadata con timezone
        fecha_generacion = datetime.now(timezone.utc)
        fecha_expiracion = fecha_generacion + timedelta(days=7)
        
        await self.certificate_repo.guardar_lote_certificados({
            'id_lote': id_lote,
            'id_proyecto': request.id_proyecto,
            'id_evento': id_evento,
            'nombre_archivo': nombre_archivo_final,
            'ruta_archivo': ruta_archivo,
            'cantidad_certificados': len(certificados_generados),
            'tamano_bytes': tamano_bytes,
            'fecha_generacion': fecha_generacion,
            'fecha_expiracion': fecha_expiracion,
            'estado': EstadoCertificadoEnum.DISPONIBLE,
            'estudiantes': [e.dict() for e in estudiantes_info]
        })
        
        logger.info(f"🎉 Certificados generados exitosamente. Lote: {id_lote}")
        
        # Preparar respuesta
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
            )
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
    
    async def generar_certificado_individual(
        self,
        request: GenerarCertificadoIndividualRequest
    ) -> Dict[str, Any]:
        """Genera un certificado individual para un estudiante"""
        
        logger.info(f"📄 Generando certificado individual para estudiante: {request.id_estudiante}")
        
        # Obtener ID del evento desde el proyecto
        id_evento = await self._obtener_id_evento_desde_proyecto(request.id_proyecto)
        
        # Obtener datos (el id_estudiante es el UID)
        datos_estudiante = await self._obtener_datos_estudiante(request.id_estudiante)
        datos_proyecto = await self._obtener_datos_proyecto(request.id_proyecto)
        datos_evento = await self._obtener_datos_evento(id_evento)
        
        # Generar PDF
        pdf_buffer = self.generator.generar_certificado(
            estudiante=datos_estudiante,
            proyecto=datos_proyecto,
            evento=datos_evento,
            incluir_calificacion=request.incluir_calificacion,
            director_evento=request.director_evento,
            coordinador_general=request.coordinador_general
        )
        
        # Generar ID y nombre de archivo
        id_certificado = self._generar_id_certificado_individual()
        nombre_archivo = self.generator.obtener_nombre_archivo(datos_estudiante)
        
        # Guardar en servidor
        ruta_archivo = os.path.join(self.directorio_certificados, nombre_archivo)
        with open(ruta_archivo, 'wb') as f:
            pdf_buffer.seek(0)
            f.write(pdf_buffer.read())
        
        tamano_bytes = os.path.getsize(ruta_archivo)
        
        # URL de descarga
        base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        url_descarga = f"{base_url}/admin/reportes/certificados/descargar/{id_certificado}"
        
        # ✅ CORRECCIÓN: Guardar metadata con timezone
        fecha_generacion = datetime.now(timezone.utc)
        fecha_expiracion = fecha_generacion + timedelta(days=7)
        
        await self.certificate_repo.guardar_certificado_individual({
            'id_certificado': id_certificado,
            'id_estudiante': request.id_estudiante,
            'id_proyecto': request.id_proyecto,
            'id_evento': id_evento,
            'nombre_archivo': nombre_archivo,
            'ruta_archivo': ruta_archivo,
            'tamano_bytes': tamano_bytes,
            'fecha_generacion': fecha_generacion,
            'fecha_expiracion': fecha_expiracion,
            'estado': EstadoCertificadoEnum.DISPONIBLE
        })
        
        logger.info(f"✅ Certificado individual generado: {nombre_archivo}")
        
        return {
            'id_certificado': id_certificado,
            'nombre_archivo': nombre_archivo,
            'url_descarga': url_descarga,
            'estudiante': EstudianteCertificadoInfo(
                nombre_completo=f"{datos_estudiante.nombres} {datos_estudiante.apellidos}",
                identificacion=datos_estudiante.identificacion,
                nombre_archivo_certificado=nombre_archivo
            ),
            'tamano_bytes': tamano_bytes,
            'fecha_generacion': fecha_generacion.isoformat()
        }
    
    async def generar_mi_certificado(
        self,
        id_estudiante_autenticado: str,
        request: GenerarMiCertificadoRequest
    ) -> Dict[str, Any]:
        """Permite a un estudiante generar su propio certificado"""
        
        logger.info(f"🎓 Estudiante {id_estudiante_autenticado} generando su certificado")
        
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
        
        # Generar PDF
        pdf_buffer = self.generator.generar_certificado(
            estudiante=datos_estudiante,
            proyecto=datos_proyecto,
            evento=datos_evento,
            incluir_calificacion=request.incluir_calificacion
        )
        
        # Generar ID
        id_certificado = f"CERT_EST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        nombre_archivo = self.generator.obtener_nombre_archivo(datos_estudiante)
        
        # Guardar
        ruta_archivo = os.path.join(self.directorio_certificados, nombre_archivo)
        with open(ruta_archivo, 'wb') as f:
            pdf_buffer.seek(0)
            f.write(pdf_buffer.read())
        
        tamano_bytes = os.path.getsize(ruta_archivo)
        
        # URL descarga
        base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        url_descarga = f"{base_url}/estudiante/certificados/descargar/{id_certificado}"
        
        # ✅ CORRECCIÓN: Guardar metadata con timezone
        fecha_generacion = datetime.now(timezone.utc)
        fecha_expiracion = fecha_generacion + timedelta(days=7)
        
        metadata = {
            'id_certificado': id_certificado,
            'id_estudiante': id_estudiante_autenticado,
            'id_proyecto': request.id_proyecto,
            'id_evento': id_evento,
            'nombre_archivo': nombre_archivo,
            'ruta_archivo': ruta_archivo,
            'tamano_bytes': tamano_bytes,
            'fecha_generacion': fecha_generacion,
            'fecha_expiracion': fecha_expiracion,
            'estado': EstadoCertificadoEnum.DISPONIBLE,
            'enviado_correo': False
        }
        
        await self.certificate_repo.guardar_certificado_individual(metadata)
        
        # Enviar por correo si se solicita
        enviado_correo = False
        correo_destino = None
        
        if request.enviar_por_correo:
            try:
                await self._enviar_certificado_por_correo(
                    pdf_buffer,
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
            except Exception as e:
                logger.error(f"Error enviando certificado por correo: {str(e)}")
        
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
            'correo_destino': correo_destino
        }
    
    async def enviar_certificados_por_correo(
        self,
        request: EnviarCertificadosRequest
    ) -> Dict[str, Any]:
        """
        Envía certificados por correo electrónico desde un lote generado previamente.
        
        Args:
            request: Datos del lote y configuración de envío
            
        Returns:
            Diccionario con resultados del envío
        """
        try:
            logger.info(f"📧 Iniciando envío de certificados - Lote: {request.id_lote}")
            
            # 1. Obtener metadata del lote
            lote = await self.certificate_repo.obtener_por_id(request.id_lote)
            
            if not lote:
                raise ValueError(f"Lote de certificados {request.id_lote} no encontrado")
            
            logger.info(f"📦 Lote encontrado: {lote.get('cantidad_certificados', 0)} certificados")
            
            # 2. Verificar que no haya expirado
            if lote.get('fecha_expiracion'):
                fecha_exp = lote['fecha_expiracion']
                if isinstance(fecha_exp, str):
                    fecha_exp = datetime.fromisoformat(fecha_exp.replace('Z', '+00:00'))
                
                if datetime.now(timezone.utc) > fecha_exp:
                    raise ValueError("El lote de certificados ha expirado")
            
            # 3. Verificar que exista el archivo ZIP
            ruta_zip = lote.get('ruta_archivo')
            if not ruta_zip or not os.path.exists(ruta_zip):
                raise ValueError("Archivo de certificados no encontrado")
            
            logger.info(f"📁 Archivo encontrado: {ruta_zip}")
            
            # 4. Extraer certificados del ZIP
            certificados_para_enviar = []
            estudiantes_en_lote = lote.get('estudiantes', [])
            
            with zipfile.ZipFile(ruta_zip, 'r') as zip_file:
                for estudiante_info in estudiantes_en_lote:
                    try:
                        nombre_archivo = estudiante_info.get('nombre_archivo_certificado')
                        
                        if not nombre_archivo:
                            logger.warning(f"⚠️ Estudiante sin nombre de archivo: {estudiante_info}")
                            continue
                        
                        # Leer el PDF del ZIP
                        pdf_content = zip_file.read(nombre_archivo)
                        
                        # Obtener datos del estudiante para el correo
                        # El estudiante_info debe tener: nombre_completo, identificacion
                        nombre_completo = estudiante_info.get('nombre_completo', 'Estudiante')
                        identificacion = estudiante_info.get('identificacion')
                        
                        # Buscar el correo del estudiante
                        correo_estudiante = await self._obtener_correo_estudiante(identificacion)
                        
                        if not correo_estudiante:
                            logger.warning(f"⚠️ No se encontró correo para {nombre_completo}")
                            continue
                        
                        certificados_para_enviar.append({
                            'correo': correo_estudiante,
                            'nombre': nombre_completo,
                            'nombre_archivo': nombre_archivo,
                            'contenido': pdf_content
                        })
                        
                        logger.info(f"✅ Preparado para {nombre_completo}: {correo_estudiante}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error extrayendo certificado para {estudiante_info.get('nombre_completo', 'desconocido')}: {str(e)}")
                        continue
            
            if not certificados_para_enviar:
                raise ValueError("No se encontraron certificados válidos para enviar")
            
            logger.info(f"📬 {len(certificados_para_enviar)} certificados listos para envío")
            
            # 5. Enviar certificados usando el servicio de email
            asunto = request.asunto or "Tu Certificado de Participación - ExpoSoftware"
            
            resultado_envio = await self.email_service.enviar_certificados_masivo(
                certificados=certificados_para_enviar,
                asunto_base=asunto,
                mensaje_personalizado=request.mensaje_personalizado
            )
            
            # 6. Actualizar estado del lote
            if resultado_envio['exitosos'] > 0:
                await self.certificate_repo.actualizar_estado(
                    request.id_lote,
                    EstadoCertificadoEnum.ENVIADO
                )
            
            logger.info(f"✅ Envío completado: {resultado_envio['exitosos']}/{resultado_envio['total']} exitosos")
            
            # 7. Preparar respuesta
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
            raise

    async def _enviar_certificado_por_correo(
        self,
        pdf_buffer: BytesIO,
        nombre_archivo: str,
        correo_destino: str,
        nombre_estudiante: str
    ) -> bool:
        """
        Envía un certificado individual por correo electrónico.
        
        Args:
            pdf_buffer: Buffer del PDF del certificado
            nombre_archivo: Nombre del archivo
            correo_destino: Correo del destinatario
            nombre_estudiante: Nombre del estudiante
            
        Returns:
            True si se envió correctamente
        """
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
        """
        Obtiene el correo electrónico de un estudiante por su identificación.
        
        Args:
            identificacion: Número de identificación del estudiante
            
        Returns:
            Correo electrónico del estudiante o None si no se encuentra
        """
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
        
        # ✅ CORRECCIÓN: Verificar expiración con timezone aware
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