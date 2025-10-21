from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from app.repositories.event_repository import EventRepository
from app.schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventState,
    EventStateChange
)
from app.exceptions.event_exceptions import (
    EventNotFoundException,
    EventAlreadyExistsException,
    InvalidEventDatesException,
    InvalidEventStateTransitionException,
    EventNotActiveException
)

logger = logging.getLogger(__name__)


class EventService:
    """Servicio para gestión de eventos"""
    
    def __init__(self):
        self.repository = EventRepository()

# Crea un nuevo evento
    async def create_event(
        self,
        event_data: EventCreate,
        created_by: str
    ) -> EventResponse:
        """
        Crea un nuevo evento
        """
        try:
            logger.debug(f"Iniciando creación de evento: {event_data.nombre_evento}")
            
            # VALIDACIÓN DE FECHAS
            if event_data.fecha_inicio > event_data.fecha_fin:
                raise InvalidEventDatesException(
                    "La fecha de inicio no puede ser posterior a la fecha de fin"
                )
            
            # Manejar timezones para la comparación
            hoy = datetime.now(timezone.utc) if event_data.fecha_inicio.tzinfo else datetime.now()
            
            if event_data.fecha_inicio < hoy:
                raise InvalidEventDatesException(
                    "La fecha de inicio no puede ser en el pasado"
                )

            # Validar que no exista un evento con el mismo nombre en fechas solapadas
            existing = await self.repository.get_by_name_and_dates(
                nombre=event_data.nombre_evento,
                fecha_inicio=event_data.fecha_inicio,
                fecha_fin=event_data.fecha_fin
            )
            
            if existing:
                raise EventAlreadyExistsException()
            
            # Preparar datos para crear
            event_dict = event_data.model_dump()
            event_dict.update({
                "estado": EventState.ACTIVO.value,
                "total_inscritos": 0,
                "total_proyectos": 0,
                "created_by": created_by,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            
            # Crear evento - Firebase generará el ID automáticamente
            event_id = await self.repository.create(event_dict)
            
            # Obtener el evento creado
            created_event = await self.repository.get_by_id(event_id)
            
            if not created_event:
                raise EventNotFoundException(event_id)
            
            # Agregar el ID generado automáticamente a los datos
            created_event["id_evento"] = event_id
            
            logger.info(f"Evento creado: {event_id} por {created_by}")
            
            return EventResponse(**created_event)
            
        except Exception as e:
            logger.error(f"Error en create_event: {str(e)}", exc_info=True)
            raise

# Obtiene un evento por su ID
    async def get_event_by_id(self, event_id: str) -> EventResponse:
        event = await self.repository.get_by_id(event_id)
        
        if not event:
            raise EventNotFoundException(event_id)
        
        return EventResponse(**event)

# Obtiene eventos con filtros
    async def get_all_events(
        self,
        estado: Optional[EventState] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        ano: Optional[int] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[EventResponse], int]:
        # Construir filtros
        filters = {}
        if estado:
            filters["estado"] = estado.value
        
        # Obtener eventos
        if ano:
            events = await self.repository.get_events_by_year(ano)
        elif fecha_desde or fecha_hasta:
            events = await self.repository.get_events_by_date_range(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                estado=estado
            )
        elif filters:
            events = await self.repository.get_all(filters=filters)
        else:
            events = await self.repository.get_all(order_by="fecha_inicio")
        
        # Aplicar filtro de estado si no se aplicó antes
        if estado and not filters:
            events = [e for e in events if e.get("estado") == estado.value]
        
        # Paginación
        total = len(events)
        start = (page - 1) * limit
        end = start + limit
        paginated_events = events[start:end]
        
        # Convertir a EventResponse
        event_responses = [EventResponse(**event) for event in paginated_events]
        
        return event_responses, total

# Actualiza un evento existente
    async def update_event(
        self,
        event_id: str,
        event_data: EventUpdate,
        updated_by: str
    ) -> EventResponse:
        # Verificar que el evento existe
        existing_event = await self.repository.get_by_id(event_id)
        if not existing_event:
            raise EventNotFoundException(event_id)
        
        # VALIDACIÓN DE FECHAS EN ACTUALIZACIÓN
        update_dict = event_data.model_dump(exclude_none=True)
        
        fecha_inicio = update_dict.get('fecha_inicio', existing_event.get('fecha_inicio'))
        fecha_fin = update_dict.get('fecha_fin', existing_event.get('fecha_fin'))
        
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise InvalidEventDatesException(
                "La fecha de inicio no puede ser posterior a la fecha de fin"
            )
        
        if update_dict:
            update_dict["updated_by"] = updated_by
            await self.repository.update(event_id, update_dict)
        
        # Obtener evento actualizado
        updated_event = await self.repository.get_by_id(event_id)
        
        logger.info(f"Evento actualizado: {event_id} por {updated_by}")
        
        return EventResponse(**updated_event)

# Cambia el estado de un evento
    async def change_event_state(
        self,
        event_id: str,
        state_change: EventStateChange,
        changed_by: str
    ) -> EventResponse:
        # Verificar que el evento existe
        event = await self.repository.get_by_id(event_id)
        if not event:
            raise EventNotFoundException(event_id)
        
        current_state = event.get("estado")
        new_state = state_change.estado
        
        # Validar transiciones de estado válidas
        valid_transitions = {
            EventState.ACTIVO: [EventState.INACTIVO, EventState.FINALIZADO],
            EventState.INACTIVO: [EventState.ACTIVO],
            EventState.FINALIZADO: []  # No se puede cambiar desde FINALIZADO
        }
        
        current_state_enum = EventState(current_state)
        if new_state not in valid_transitions.get(current_state_enum, []):
            raise InvalidEventStateTransitionException(current_state, new_state.value)
        
        # Cambiar estado
        await self.repository.change_event_state(
            event_id=event_id,
            new_state=new_state,
            reason=state_change.razon,
            changed_by=changed_by
        )
        
        # Obtener evento actualizado
        updated_event = await self.repository.get_by_id(event_id)
        
        logger.info(
            f"Estado de evento cambiado: {event_id} de {current_state} a {new_state.value} "
            f"por {changed_by}"
        )
        
        return EventResponse(**updated_event)

# Obtiene todos los eventos activos
    async def get_active_events(self) -> List[EventResponse]:
        events = await self.repository.get_active_events()
        return [EventResponse(**event) for event in events]

# Obtiene los próximos eventos
    async def get_upcoming_events(self, limit: int = 5) -> List[EventResponse]:
        events = await self.repository.get_upcoming_events(limit=limit)
        return [EventResponse(**event) for event in events]

#Verifica la capacidad de un evento
    async def check_event_capacity(self, event_id: str) -> Dict[str, Any]:
        event = await self.repository.get_by_id(event_id)
        
        if not event:
            raise EventNotFoundException(event_id)
        
        cupo_maximo = event.get("cupo_maximo")
        total_inscritos = event.get("total_inscritos", 0)
        
        return {
            "evento_id": event_id,
            "cupo_maximo": cupo_maximo,
            "total_inscritos": total_inscritos,
            "cupos_disponibles": cupo_maximo - total_inscritos if cupo_maximo else None,
            "esta_lleno": await self.repository.is_event_full(event_id),
            "tiene_limite": cupo_maximo is not None
        }

#Incrementa el contador de inscritos (Hacer para RegistrationService)
    """async def increment_registrations(self, event_id: str) -> bool:
        
        event = await self.repository.get_by_id(event_id)
        
        if not event:
            raise EventNotFoundException(event_id)
        
        # VERIFICAR QUE EL EVENTO ESTÉ ACTIVO 
        if event.get("estado") != EventState.ACTIVO.value:
            raise EventNotActiveException(event.get("nombre_evento"))
        
        # Verificar si hay cupo
        if await self.repository.is_event_full(event_id):
            from app.exceptions.event_exceptions import EventFullException
            raise EventFullException(event.get("nombre_evento"))
        
        new_total = event.get("total_inscritos", 0) + 1
        
        return await self.repository.update_event_statistics(
            event_id=event_id,
            total_inscritos=new_total
        )
    """

#Incrementa el contador de proyectos ( Hacer para ProjectService) 
    """async def increment_projects(self, event_id: str) -> bool:
        
        event = await self.repository.get_by_id(event_id)
        
        if not event:
            raise EventNotFoundException(event_id)
        
        # VERIFICAR QUE EL EVENTO ESTÉ ACTIVO
        if event.get("estado") != EventState.ACTIVO.value:
            raise EventNotActiveException(event.get("nombre_evento"))
        
        new_total = event.get("total_proyectos", 0) + 1
        
        return await self.repository.update_event_statistics(
            event_id=event_id,
            total_proyectos=new_total
        )
    """

#Valida si un evento está disponible para inscripciones usar para RegistrationService(algo asi)
    async def validate_event_for_registration(self, event_id: str) -> bool:
        event = await self.repository.get_by_id(event_id)
        
        if not event:
            raise EventNotFoundException(event_id)
        
        # Verificar estado activo
        if event.get("estado") != EventState.ACTIVO.value:
            raise EventNotActiveException(event.get("nombre_evento"))
        
        # Verificar fechas
        hoy = datetime.today()
        fecha_inicio = event.get("fecha_inicio")
        fecha_fin = event.get("fecha_fin")
        
        if hoy < fecha_inicio:
            raise EventNotActiveException(
                f"El evento '{event.get('nombre_evento')}' aún no ha comenzado"
            )
        
        if hoy > fecha_fin:
            raise EventNotActiveException(
                f"El evento '{event.get('nombre_evento')}' ya ha finalizado"
            )
        
        # Verificar cupo
        if await self.repository.is_event_full(event_id):
            from app.exceptions.event_exceptions import EventFullException
            raise EventFullException(event.get("nombre_evento"))
        
        return True