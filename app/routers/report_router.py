from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import date

from app.schemas.report import (
    GenerarReporteRequest,
    EnviarReporteRequest,
    GenerarYEnviarReporteRequest,
    ReporteGeneradoResponse,
    ReporteEnviadoResponse,
    HistorialReportesResponse,
    SuccessResponse,
    ErrorResponse
)
from app.services.report_service import ReportService


router = APIRouter(
    prefix="/admin/reportes",
    tags=["Generación de Reportes PDF"]
)

# Instancia del servicio
report_service = ReportService()


@router.post(
    "/generar-pdf",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar reporte en PDF",
    description="""
    Genera un reporte en formato PDF basado en filtros personalizados.
    
    **Todos los filtros son opcionales y pueden combinarse libremente.**
    """
)
async def generar_reporte_pdf(request: GenerarReporteRequest):
    """
    Endpoint para generar un reporte PDF.
    
    Args:
        request: Datos de la solicitud con filtros y configuración
        
    Returns:
        Información del reporte generado
    """
    try:
        resultado = await report_service.generar_reporte(
            filtros=request.filtros,
            titulo_reporte=request.titulo_reporte,
            incluir_graficos=request.incluir_graficos,
            guardar_en_servidor=True
        )
        
        # Eliminar pdf_buffer de la respuesta si existe
        resultado.pop('pdf_buffer', None)
        
        return SuccessResponse(
            status="success",
            mensaje="Reporte generado correctamente",
            data=resultado
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "mensaje": str(e)
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error interno del servidor",
                "detalles": str(e)
            }
        )


@router.post(
    "/enviar-pdf",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Enviar reporte PDF por correo electrónico",
    description="""
    Envía un reporte PDF previamente generado a uno o varios destinatarios.
    El reporte debe haber sido generado previamente usando el endpoint `/generar-pdf`.
    """
)
async def enviar_reporte_pdf(request: EnviarReporteRequest):
    """
    Endpoint para enviar un reporte por correo.
    
    Args:
        request: Datos de la solicitud con información del envío
        
    Returns:
        Información del envío realizado
    """
    try:
        resultado = await report_service.enviar_reporte(
            id_reporte=request.id_reporte,
            correo_destino=request.correo_destino,
            asunto=request.asunto,
            mensaje_personalizado=request.mensaje_personalizado,
            copias=request.copias,
            copias_ocultas=request.copias_ocultas
        )
        
        return SuccessResponse(
            status="success",
            mensaje="Reporte enviado correctamente",
            data=resultado
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "mensaje": str(e)
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error al enviar el reporte",
                "detalles": str(e)
            }
        )


@router.post(
    "/generar-y-enviar-pdf",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar y enviar reporte en una sola operación",
    description="""
    Genera un reporte PDF y lo envía automáticamente por correo electrónico.
    Combina las funcionalidades de generación y envío en un solo proceso.
    """
)
async def generar_y_enviar_reporte_pdf(request: GenerarYEnviarReporteRequest):
    """
    Endpoint para generar y enviar un reporte en una sola operación.
    
    Args:
        request: Datos de la solicitud con filtros y configuración de envío
        
    Returns:
        Información del reporte generado y enviado
    """
    try:
        resultado = await report_service.generar_y_enviar_reporte(
            filtros=request.filtros,
            correo_destino=request.correo_destino,
            titulo_reporte=request.titulo_reporte,
            asunto=request.asunto,
            mensaje_personalizado=request.mensaje_personalizado,
            incluir_graficos=request.incluir_graficos,
            copias=request.copias,
            guardar_reporte=request.guardar_reporte
        )
        
        return SuccessResponse(
            status="success",
            mensaje="Reporte generado y enviado correctamente",
            data=resultado
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "mensaje": str(e)
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error al generar y enviar el reporte",
                "detalles": str(e)
            }
        )


@router.get(
    "/descargar/{id_reporte}",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    summary="Descargar reporte PDF generado",
    description="""
    Descarga un reporte PDF previamente generado.
    El enlace de descarga expira después de 24 horas.
    """
)
async def descargar_reporte_pdf(id_reporte: str):
    """
    Endpoint para descargar un reporte PDF.
    
    Args:
        id_reporte: ID único del reporte
        
    Returns:
        Archivo PDF para descarga
    """
    try:
        nombre_archivo, pdf_buffer = await report_service.obtener_reporte_para_descarga(
            id_reporte
        )
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_archivo}"'
            }
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "mensaje": str(e)
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error al descargar el reporte",
                "detalles": str(e)
            }
        )


@router.get(
    "/historial",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Historial de reportes generados",
    description="""
    Consulta el historial de reportes generados por el usuario.
    Permite filtrar por fecha y tipo de reporte.
    """
)
async def obtener_historial_reportes(
    fecha_desde: Optional[date] = Query(None, description="Fecha inicial del rango"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha final del rango"),
    limite: int = Query(20, ge=1, le=100, description="Cantidad de registros por página"),
    pagina: int = Query(1, ge=1, description="Número de página")
):
    """
    Endpoint para obtener el historial de reportes.
    
    Args:
        fecha_desde: Fecha inicial del rango (opcional)
        fecha_hasta: Fecha final del rango (opcional)
        limite: Cantidad de registros por página
        pagina: Número de página
        
    Returns:
        Listado de reportes con paginación
    """
    try:
        resultado = await report_service.obtener_historial(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limite=limite,
            pagina=pagina
        )
        
        return SuccessResponse(
            status="success",
            mensaje="Historial obtenido correctamente",
            data=resultado
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error al obtener el historial",
                "detalles": str(e)
            }
        )


@router.delete(
    "/eliminar/{id_reporte}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminar reporte generado",
    description="Elimina un reporte PDF del servidor antes de su expiración automática"
)
async def eliminar_reporte(id_reporte: str):
    """
    Endpoint para eliminar un reporte.
    
    Args:
        id_reporte: ID único del reporte a eliminar
        
    Returns:
        Confirmación de eliminación
    """
    try:
        resultado = await report_service.eliminar_reporte(id_reporte)
        
        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "mensaje": "El reporte no existe"
                }
            )
        
        return SuccessResponse(
            status="success",
            mensaje="Reporte eliminado correctamente",
            data=None
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "mensaje": str(e)
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error al eliminar el reporte",
                "detalles": str(e)
            }
        )


# Endpoint opcional para tareas de mantenimiento
@router.post(
    "/limpiar-expirados",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Limpiar reportes expirados",
    description="Elimina todos los reportes que han superado su tiempo de expiración",
    include_in_schema=False  # No mostrar en la documentación pública
)
async def limpiar_reportes_expirados():
    """
    Endpoint para limpiar reportes expirados.
    
    Este endpoint debe ser llamado por un proceso programado (cron job)
    o puede ser protegido con autenticación adicional.
    
    Returns:
        Cantidad de reportes eliminados
    """
    try:
        cantidad_eliminados = await report_service.limpiar_reportes_expirados()
        
        return SuccessResponse(
            status="success",
            mensaje=f"Se eliminaron {cantidad_eliminados} reportes expirados",
            data={"reportes_eliminados": cantidad_eliminados}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "mensaje": "Error al limpiar reportes expirados",
                "detalles": str(e)
            }
        )