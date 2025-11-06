# app/routers/admin_certificate_router.py

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse, StreamingResponse
from typing import Dict, Any
import logging

from app.services.certificate_service import CertificateService
from app.schemas.certificate import (
    GenerarCertificadoPorProyectoRequest,
    GenerarCertificadoIndividualRequest,
    EnviarCertificadosRequest,
    CertificadoGeneradoResponse,
    CertificadoIndividualResponse,
    CertificadosEnviadosResponse
)
from app.dependencies.auth import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/reportes/certificados",
    tags=["Certificados de Participación"]
)


@router.post(
    "/generar-por-proyecto",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Generar certificados para estudiantes de un proyecto"
)
async def generar_certificados_por_proyecto(
    request: GenerarCertificadoPorProyectoRequest,
    # current_user = Depends(get_current_admin_user)
):
    """
    Genera certificados de participación en PDF para todos los estudiantes 
    expositores de un proyecto específico.
    
    **Proceso:**
    1. Consulta el proyecto especificado
    2. Obtiene las identificaciones de los estudiantes del proyecto
    3. Consulta la información completa de cada estudiante
    4. Genera un certificado PDF personalizado para cada estudiante
    5. Retorna un paquete ZIP con todos los certificados
    
    **Información incluida en el certificado:**
    - Nombre completo del estudiante
    - Identificación
    - Título del proyecto expuesto
    - Nombre del evento
    - Fecha de participación
    - Programa académico
    - Firmas del Director del Evento y Coordinador General
    """
    try:
        service = CertificateService()
        resultado = await service.generar_certificados_por_proyecto(request)
        
        return {
            "status": "success",
            "mensaje": "Certificados generados correctamente",
            "data": resultado
        }
    
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "mensaje": str(e)
            }
        )
    
    except Exception as e:
        logger.error(f"Error generando certificados por proyecto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error interno al generar certificados",
                "detalles": str(e)
            }
        )


@router.post(
    "/generar-individual",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Generar certificado individual para un estudiante"
)
async def generar_certificado_individual(
    request: GenerarCertificadoIndividualRequest,
    # current_user = Depends(get_current_admin_user)
):
    """
    Genera un certificado de participación individual para un estudiante específico,
    basado en su participación en un proyecto.
    """
    try:
        service = CertificateService()
        resultado = await service.generar_certificado_individual(request)
        
        return {
            "status": "success",
            "mensaje": "Certificado generado correctamente",
            "data": resultado
        }
    
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "mensaje": str(e)
            }
        )
    
    except Exception as e:
        logger.error(f"Error generando certificado individual: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error interno al generar certificado",
                "detalles": str(e)
            }
        )


@router.post(
    "/enviar-por-correo",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Enviar certificados por correo electrónico"
)
async def enviar_certificados_por_correo(
    request: EnviarCertificadosRequest,
    # current_user = Depends(get_current_admin_user)
):
    """
    Envía los certificados generados directamente a los correos electrónicos 
    de los estudiantes.
    
    **Proceso:**
    1. Obtiene el lote de certificados generado previamente
    2. Extrae los certificados individuales del archivo ZIP
    3. Busca el correo de cada estudiante
    4. Envía cada certificado personalizado por correo
    5. Retorna estadísticas del envío (exitosos/fallidos)
    
    **Nota:** Se requiere configuración SMTP válida en variables de entorno.
    """
    try:
        logger.info(f"📧 Solicitud de envío de certificados - Lote: {request.id_lote}")
        
        service = CertificateService()
        
        # Enviar certificados
        resultado = await service.enviar_certificados_por_correo(request)
        
        # Construir mensaje de respuesta
        if resultado['enviados_exitosamente'] == resultado['total_certificados']:
            mensaje = f"Todos los certificados ({resultado['total_certificados']}) fueron enviados exitosamente"
        elif resultado['enviados_exitosamente'] > 0:
            mensaje = (
                f"Se enviaron {resultado['enviados_exitosamente']} de {resultado['total_certificados']} certificados. "
                f"{resultado['envios_fallidos']} envíos fallaron."
            )
        else:
            mensaje = f"No se pudo enviar ningún certificado. Todos los envíos ({resultado['total_certificados']}) fallaron."
        
        logger.info(f"✅ Envío completado: {mensaje}")
        
        return {
            "status": "success",
            "mensaje": mensaje,
            "data": resultado
        }
    
    except ValueError as e:
        logger.error(f"❌ Error de validación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "mensaje": str(e)
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Error enviando certificados: {str(e)}")
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error interno al enviar certificados",
                "detalles": str(e)
            }
        )

@router.get(
    "/descargar/{id}",
    summary="Descargar certificado individual o lote de certificados"
)
async def descargar_certificado_o_lote(
    id: str,
    # current_user = Depends(get_current_admin_user)
):
    """
    Descarga un certificado individual o un lote completo de certificados.
    
    **Determinación automática:**
    - Si el ID empieza con `CERT_` (pero no `CERT_IND_` o `CERT_EST_`): Se trata de un lote (ZIP)
    - Cualquier otro formato: Se trata de un certificado individual (PDF)
    
    **Importante:** Los enlaces de descarga expiran después de 7 días.
    """
    try:
        service = CertificateService()
        
        # Determinar si es lote o certificado individual por el formato del ID
        es_lote = id.startswith('CERT_') and not id.startswith('CERT_IND_') and not id.startswith('CERT_EST_')
        
        if es_lote:
            logger.info(f"📦 Descargando lote: {id}")
            nombre_archivo, buffer = await service.obtener_lote_para_descarga(id_lote=id)
            media_type = "application/zip"
            content_disposition = f'attachment; filename="{nombre_archivo}"'
            
        else:
            logger.info(f"📄 Descargando certificado individual: {id}")
            nombre_archivo, buffer = await service.obtener_certificado_para_descarga(
                id_certificado=id
            )
            media_type = "application/pdf"
            content_disposition = f'attachment; filename="{nombre_archivo}"'
        
        # Devolver archivo
        return StreamingResponse(
            buffer,
            media_type=media_type,
            headers={
                "Content-Disposition": content_disposition,
                "Content-Length": str(buffer.getbuffer().nbytes)
            }
        )
    
    except ValueError as e:
        logger.error(f"Error descargando: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "mensaje": str(e)
            }
        )
    
    except Exception as e:
        logger.error(f"Error en descarga: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error al descargar certificados",
                "detalles": str(e)
            }
        )

@router.get(
    "/lotes",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Obtener listado de lotes de certificados"
)
async def obtener_lotes_certificados(
    pagina: int = 1,
    limite: int = 20,
    # current_user = Depends(get_current_admin_user)
):
    """
    Obtiene un listado paginado de todos los lotes de certificados generados.
    
    **Información incluida:**
    - ID del lote
    - ID del proyecto
    - Nombre del proyecto
    - Evento asociado
    - Cantidad de certificados
    - Fecha de generación
    - Estado del lote
    - Información de Cloudinary
    """
    try:
        service = CertificateService()
        resultado = await service.obtener_lotes_certificados(
            pagina=pagina,
            limite=limite
        )
        
        return {
            "status": "success",
            "data": resultado
        }
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo lotes de certificados: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error interno al obtener lotes de certificados",
                "detalles": str(e)
            }
        )