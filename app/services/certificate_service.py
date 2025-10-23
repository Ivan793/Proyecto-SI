# app/services/certificate_service.py

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from io import BytesIO
import os
import uuid
import zipfile
import logging

from app.services.certificate_generator import CertificateGenerator
from app.services.email_service import EmailService
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.proyect_repository import ProyectRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.event_repository import EventRepository

from app.schemas.certificate import (
    DatosEstudianteCertificado,
    DatosProyectoCertificado,
    DatosEventoCertificado,
    CertificadoMetadata,
    EstadoCertificadoEnum,
    FormatoSalidaEnum,
    GenerarCertificadoPorProyectoRequest,
    GenerarCertificadoPorEventoRequest,
    GenerarCertificadoIndividualRequest,
    GenerarMiCertificadoRequest,
    EnviarCertificadosRequest,
    CertificadoGeneradoResponse,
    CertificadoIndividualResponse,
    MiCertificadoResponse,
    CertificadosEnviadosResponse,
    EstudianteCertificadoInfo,
    ProyectoCertificadoInfo,
    MisCertificadosResponse,
    ProyectosDisponiblesResponse
)

logger = logging.getLogger(__name__)


class CertificateService:
    """Servicio principal para gestión de certificados"""
    
    def __init__(self):
        self.generator = CertificateGenerator()
        self.email_service = EmailService()
        self.certificate_repo = CertificateRepository()
        self.project_repo = ProyectRepository()
        self.student_repo = StudentRepository()
        self.user_repo = UserRepository()
        self.event_repo = EventRepository()
        
        self.directorio_certificados = os.getenv(
            'CERTIFICADOS_DIR',
            'certificados_temp'
        )
        self._asegurar_directorio()
    
    def _asegurar_directorio(self):
        """Crea el directorio de certificados si no existe"""
        if not os.path.exists(self.directorio_certificados):
            os.makedirs(self.directorio_certificados)
    
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
        id_estudiante: str
    ) -> DatosEstudianteCertificado:
        """Obtiene los datos del estudiante para el certificado"""
        
        # Obtener estudiante
        estudiante = await self.student_repo.get_by_id(id_estudiante)
        if not estudiante:
            raise ValueError(f"Estudiante con ID {id_estudiante} no encontrado")
        
        # Obtener usuario asociado
        usuario = await self.user_repo.get_by_id(estudiante['id_usuario'])
        if not usuario:
            raise ValueError(f"Usuario asociado al estudiante no encontrado")
        
        # Obtener programa académico (opcional)
        nombre_programa = None
        if estudiante.get('codigo_programa'):
            # Aquí podrías obtener el nombre del programa desde otra colección
            nombre_programa = estudiante.get('codigo_programa')
        
        return DatosEstudianteCertificado(
            id_estudiante=id_estudiante,
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
        """Obtiene los datos del proyecto para el certificado"""
        
        proyecto = await self.project_repo.get_by_id(id_proyecto)
        if not proyecto:
            raise ValueError(f"Proyecto con ID {id_proyecto} no encontrado")
        
        return DatosProyectoCertificado(
            id_proyecto=id_proyecto,
            titulo_proyecto=proyecto['titulo_proyecto'],
            tipo_actividad=proyecto['tipo_actividad'],
            calificacion=proyecto.get('calificacion'),
            fecha_subida=proyecto.get('fecha_subida')
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
        
        # Buscar en la colección de proyectos-eventos o en el proyecto mismo
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
        logger.info(f"Generando certificados para proyecto: {request.id_proyecto}")
        
        # Obtener ID del evento
        id_evento = request.id_evento
        if not id_evento:
            id_evento = await self._obtener_id_evento_desde_proyecto(request.id_proyecto)
        
        # Obtener datos del proyecto y evento
        datos_proyecto = await self._obtener_datos_proyecto(request.id_proyecto)
        datos_evento = await self._obtener_datos_evento(id_evento)
        
        # Obtener estudiantes del proyecto
        estudiantes_ids = await self.project_repo.get_students_by_project(request.id_proyecto)
        
        if not estudiantes_ids:
            raise ValueError("No se encontraron estudiantes asociados al proyecto")
        
        # Generar ID del lote
        id_lote = self._generar_id_lote()
        
        # Lista para almacenar certificados generados
        certificados_generados = []
        estudiantes_info = []
        
        # Generar certificado para cada estudiante
        for id_estudiante in estudiantes_ids:
            try:
                datos_estudiante = await self._obtener_datos_estudiante(id_estudiante)
                
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
                
                logger.info(f"Certificado generado para: {datos_estudiante.nombres}")
                
            except Exception as e:
                logger.error(f"Error generando certificado para estudiante {id_estudiante}: {str(e)}")
                continue
        
        if not certificados_generados:
            raise ValueError("No se pudo generar ningún certificado")
        
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
        
        # Generar URL de descarga
        base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        url_descarga = f"{base_url}/admin/reportes/certificados/descargar/{id_lote}"
        
        # Guardar metadata
        fecha_generacion = datetime.now()
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
        
        logger.info(f"Generando certificado individual para estudiante: {request.id_estudiante}")
        
        # Obtener ID del evento desde el proyecto
        id_evento = await self._obtener_id_evento_desde_proyecto(request.id_proyecto)
        
        # Obtener datos
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
        
        # Guardar metadata
        fecha_generacion = datetime.now()
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
        
        logger.info(f"Estudiante {id_estudiante_autenticado} generando su certificado")
        
        # Verificar que el proyecto pertenece al estudiante
        proyecto = await self.project_repo.get_by_id(request.id_proyecto)
        if not proyecto:
            raise ValueError("El proyecto especificado no existe")
        
        if proyecto.get('id_estudiante') != id_estudiante_autenticado:
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
        
        # Guardar metadata
        fecha_generacion = datetime.now()
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
    
    async def _enviar_certificado_por_correo(
        self,
        pdf_buffer: BytesIO,
        nombre_archivo: str,
        correo_destino: str,
        nombre_estudiante: str,
        asunto: Optional[str] = None,
        mensaje_personalizado: Optional[str] = None
    ):
        """Envía un certificado por correo electrónico"""
        
        asunto_final = asunto or "Tu Certificado de Participación - ExpoSoftware"
        
        mensaje_html = f"""
        <html>
            <body>
                <h2>Certificado de Participación</h2>
                <p>Estimado(a) {nombre_estudiante},</p>
                <p>Adjunto encontrarás tu certificado de participación en ExpoSoftware.</p>
                {f'<p>{mensaje_personalizado}</p>' if mensaje_personalizado else ''}
                <p>¡Felicitaciones por tu participación!</p>
                <br>
                <p>Atentamente,</p>
                <p><strong>Facultad de Ingeniería de Sistemas</strong><br>
                Universidad Popular del Cesar</p>
            </body>
        </html>
        """
        
        pdf_buffer.seek(0)
        
        await self.email_service.enviar_con_adjunto(
            destinatario=correo_destino,
            asunto=asunto_final,
            cuerpo_html=mensaje_html,
            nombre_adjunto=nombre_archivo,
            contenido_adjunto=pdf_buffer.read(),
            tipo_adjunto='application/pdf'
        )
    
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
        
        # Verificar expiración
        if certificado.get('fecha_expiracion'):
            if datetime.now() > certificado['fecha_expiracion']:
                raise ValueError("El enlace de descarga ha expirado")
        
        # Cargar archivo
        ruta_archivo = certificado.get('ruta_archivo')
        if not ruta_archivo or not os.path.exists(ruta_archivo):
            raise ValueError("El archivo del certificado no está disponible")
        
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