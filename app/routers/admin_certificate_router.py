# app/routers/admin_certificate_router.py

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse, StreamingResponse
from typing import Dict, Any
import logging

from app.services.certificate_service import CertificateService
from app.schemas.certificate import (
    GenerarCertificadoPorProyectoRequest,
    GenerarCertificadoPorEventoRequest,
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
    "/generar-por-evento",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Generar certificados para todos los estudiantes de un evento"
)
async def generar_certificados_por_evento(
    request: GenerarCertificadoPorEventoRequest,
    # current_user = Depends(get_current_admin_user)
):
    """
    Genera certificados de participación para todos los estudiantes expositores 
    que participaron en un evento específico.
    
    Este endpoint recorre todos los proyectos del evento y genera certificados 
    para cada estudiante expositor.
    """
    try:
        service = CertificateService()
        # Implementar lógica para generar por evento
        # Por ahora retornamos un placeholder
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "status": "error",
                "mensaje": "Funcionalidad en desarrollo"
            }
        )
    
    except Exception as e:
        logger.error(f"Error generando certificados por evento: {str(e)}")
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
    
    Cada estudiante recibe su certificado individual en su correo institucional.
    """
    try:
        service = CertificateService()
        # Implementar lógica de envío
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "status": "error",
                "mensaje": "Funcionalidad en desarrollo"
            }
        )
    
    except Exception as e:
        logger.error(f"Error enviando certificados: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error interno al enviar certificados",
                "detalles": str(e)
            }
        )


@router.get(
    "/descargar/{id_lote}",
    summary="Descargar lote de certificados"
)
async def descargar_lote_certificados(
    id_lote: str,
    # current_user = Depends(get_current_admin_user)
):
    """
    Descarga un archivo ZIP con los certificados generados previamente.
    
    **Importante:** El enlace de descarga expira después de 7 días.
    """
    try:
        service = CertificateService()
        nombre_archivo, buffer = await service.obtener_certificado_para_descarga(
            id_certificado=id_lote
        )
        
        return StreamingResponse(
            buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_archivo}"'
            }
        )
    
    except ValueError as e:
        logger.error(f"Error descargando certificados: {str(e)}")
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