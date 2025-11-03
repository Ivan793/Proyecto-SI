from fastapi import APIRouter, Depends, Query, status, Request
from typing import Optional, Dict, Any
from datetime import date, datetime
import logging

from app.exceptions.event_exceptions import EventAlreadyExistsException, EventFullException, EventNotActiveException, EventNotFoundException, InvalidEventDatesException, InvalidEventStateTransitionException
from app.services.event_service import EventService
from app.schemas.event import (
    EventCreate,
    EventUpdate,
    EventState,
    EventStateChange
)
from app.schemas.common import PaginationParams
from app.dependencies.auth_dependencies import get_current_admin_user, optional_authentication
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    success_response, created_response, paginated_response, 
    updated_response, not_found_response, conflict_response,
    bad_request_response, internal_server_error_response,
    message_response
)
from app.utils.swagger_docs import ResponseDocumentation
from app.core.response_codes import ResponseCode

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Eventos - Admin"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo evento",
    description="Crea una nueva feria/convocatoria de ExpoSoftware",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def create_event(
    request: Request,  
    event_data: EventCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = EventService()
        event = await service.create_event(event_data, current_admin["user_id"])
        
        logger.info(f"Evento creado: {event.id_evento} por {current_admin['nombre_completo']}")
        
        return created_response(
            data=event.model_dump(),
            message="Evento creado exitosamente"
        )
        
    except EventAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except InvalidEventDatesException as e:
        return bad_request_response(message=str(e))
    except Exception as e:
        logger.error(f"Error inesperado creando evento: {str(e)}")
        return internal_server_error_response()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Listar eventos con filtros",
    description="Obtiene lista de eventos con opciones de filtrado y paginación",
    responses=ResponseDocumentation.get_paginated_response()
)
@admin_rate_limit()
async def get_events(
    request: Request,
    estado: Optional[EventState] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Filtrar desde fecha"),
    fecha_hasta: Optional[date] = Query(None, description="Filtrar hasta fecha"),
    ano: Optional[int] = Query(None, description="Filtrar por año específico"),
    params: PaginationParams = Depends(),
    _: Dict[str, Any] = Depends(optional_authentication)
):
    try:
        service = EventService()
        events, total = await service.get_all_events(
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            ano=ano,
            page=params.page,
            limit=params.limit
        )

        return paginated_response(
            data=[event.model_dump() for event in events],
            page=params.page,
            limit=params.limit,
            total_items=total,
            message="Eventos obtenidos exitosamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo eventos: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Obtener detalles de un evento",
    description="Obtiene información completa de un evento específico",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_event_by_id(
    request: Request,
    id: str,
    _: Dict[str, Any] = Depends(optional_authentication)
):
    try:
        service = EventService()
        event = await service.get_event_by_id(id)
        
        return success_response(
            data=event.model_dump(),
            message="Evento obtenido correctamente"
        )
        
    except EventNotFoundException as e:
        return not_found_response("Evento", id)
    except Exception as e:
        logger.error(f"Error obteniendo evento {id}: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Actualizar evento",
    description="Actualiza la información de un evento existente",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def update_event(
    request: Request,
    id: str,
    event_data: EventUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = EventService()
        event = await service.update_event(id, event_data, current_admin["user_id"])
        
        logger.info(f"Evento actualizado: {id} por {current_admin['nombre_completo']}")
        
        return updated_response(
            data=event.model_dump(),
            message="Evento actualizado exitosamente"
        )
        
    except EventNotFoundException as e:
        return not_found_response("Evento", id)
    except InvalidEventDatesException as e:
        return bad_request_response(message=str(e))
    except Exception as e:
        logger.error(f"Error actualizando evento {id}: {str(e)}")
        return internal_server_error_response()


@router.patch(
    "/{id}/estado",
    status_code=status.HTTP_200_OK,
    summary="Cambiar estado del evento",
    description="Cambia el estado de un evento (ACTIVO/INACTIVO/FINALIZADO)",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def change_event_state(
    request: Request,
    id: str,
    state_change: EventStateChange,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = EventService()
        event = await service.change_event_state(
            event_id=id,
            state_change=state_change,
            changed_by=current_admin["user_id"]
        )

        audit_info = {
            "cambio_realizado_por": current_admin["user_id"],
            "nombre_admin": current_admin["nombre_completo"],
            "fecha_cambio": datetime.utcnow().isoformat(),
            "estado_nuevo": state_change.estado.value,
            "razon": state_change.razon,
        }

        return success_response(
            data={
                "evento": event.model_dump(),
                "auditoria": audit_info
            },
            message=f"Estado del evento cambiado a {state_change.estado.value}"
        )
        
    except EventNotFoundException as e:
        return not_found_response("Evento", id)
    except InvalidEventStateTransitionException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error cambiando estado del evento {id}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{id}/capacidad",
    status_code=status.HTTP_200_OK,
    summary="Verificar capacidad del evento",
    description="Obtiene información sobre la capacidad y disponibilidad de cupos",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def check_event_capacity(
    request: Request,
    id: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = EventService()
        capacity_info = await service.check_event_capacity(id)

        return success_response(
            data=capacity_info,
            message="Información de capacidad obtenida correctamente"
        )
        
    except EventNotFoundException as e:
        return not_found_response("Evento", id)
    except Exception as e:
        logger.error(f"Error verificando capacidad del evento {id}: {str(e)}")
        return internal_server_error_response()
    

@router.get(
    "/proximos/listado",
    status_code=status.HTTP_200_OK,
    summary="Obtener próximos eventos",
    description="Obtiene los próximos eventos activos ordenados por fecha",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_upcoming_events(
    request: Request,
    limit: int = Query(5, ge=1, le=20, description="Límite de eventos a obtener"),
    _: Dict[str, Any] = Depends(optional_authentication)
):
    try:
        service = EventService()
        events = await service.get_upcoming_events(limit=limit)
        
        return success_response(
            data=[event.model_dump() for event in events],
            message="Próximos eventos obtenidos exitosamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo próximos eventos: {str(e)}")
        return internal_server_error_response()
    

@router.get(
    "/estadisticas/generales",
    status_code=status.HTTP_200_OK,
    summary="Estadísticas generales de eventos",
    description="Obtiene estadísticas generales de todos los eventos",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_events_statistics(
    request: Request,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = EventService()
        
        events, total = await service.get_all_events(page=1, limit=1000)
        
        total_eventos = total
        eventos_activos = len([e for e in events if e.estado == EventState.ACTIVO])
        eventos_inactivos = len([e for e in events if e.estado == EventState.INACTIVO])
        eventos_finalizados = len([e for e in events if e.estado == EventState.FINALIZADO])
        
        total_inscritos = sum(event.total_inscritos for event in events)
        total_proyectos = sum(event.total_proyectos for event in events)
        
        hoy = datetime.now().date()
        proximos_eventos = len([
            e for e in events 
            if e.estado == EventState.ACTIVO and e.fecha_inicio.date() >= hoy
        ])
        
        statistics = {
            "total_eventos": total_eventos,
            "eventos_activos": eventos_activos,
            "eventos_inactivos": eventos_inactivos,
            "eventos_finalizados": eventos_finalizados,
            "proximos_eventos": proximos_eventos,
            "total_inscritos": total_inscritos,
            "total_proyectos": total_proyectos,
            "promedio_inscritos_por_evento": round(total_inscritos / total_eventos, 2) if total_eventos > 0 else 0,
            "promedio_proyectos_por_evento": round(total_proyectos / total_eventos, 2) if total_eventos > 0 else 0
        }
        
        return success_response(
            data=statistics,
            message="Estadísticas obtenidas exitosamente"
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de eventos: {str(e)}")
        return internal_server_error_response()

# (HACER PARA REGISTRATIONSERVICE ALGO ASI)
"""
@router.post(
    "/{id}/incrementar-inscritos",
    status_code=status.HTTP_200_OK,
    summary="Incrementar contador de inscritos",
    description="Incrementa en 1 el contador de participantes inscritos en el evento"
)
@admin_rate_limit()
async def increment_registrations(
    request: Request,
    id: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = EventService()
        result = await service.increment_registrations(id)
        
        if result:
            return success_response(
                data={"incrementado": True},
                message="Contador de inscritos incrementado exitosamente"
            )
        else:
            return bad_request_response(
                message="No se pudo incrementar el contador de inscritos"
            )
            
    except EventNotFoundException as e:
        return not_found_response("Evento", id)
    except EventNotActiveException as e:
        return conflict_response(message=str(e))
    except EventFullException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error incrementando inscritos del evento {id}: {str(e)}")
        return internal_server_error_response()
"""

# (HACER PARA PROJECTSERVICE)
""""
@router.post(
    "/{id}/incrementar-proyectos",
    status_code=status.HTTP_200_OK,
    summary="Incrementar contador de proyectos",
    description="Incrementa en 1 el contador de proyectos registrados en el evento"
)
@admin_rate_limit()
async def increment_projects(
    request: Request,
    id: str,
    _: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = EventService()
        result = await service.increment_projects(id)
        
        if result:
            return success_response(
                data={"incrementado": True},
                message="Contador de proyectos incrementado exitosamente"
            )
        else:
            return bad_request_response(
                message="No se pudo incrementar el contador de proyectos"
            )
            
    except EventNotFoundException as e:
        return not_found_response("Evento", id)
    except EventNotActiveException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error incrementando proyectos del evento {id}: {str(e)}")
        return internal_server_error_response()
"""