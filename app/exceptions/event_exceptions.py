from .base_exceptions import AppException, NotFoundException, ConflictException, ValidationException
from app.core.response_codes import ResponseCode


class EventNotFoundException(NotFoundException):
    """Evento no encontrado"""
    
    def __init__(self, event_id: str):
        super().__init__(
            resource="Evento",
            identifier=event_id,
            code=ResponseCode.NOT_FOUND
        )

class EventAlreadyExistsException(ConflictException):
    """Evento ya existe"""
    
    def __init__(
        self,
        message: str = "Ya existe un evento con ese nombre en las fechas especificadas",
        conflict_field: str = "nombre"
    ):
        super().__init__(
            message=message,
            conflict_field=conflict_field,
            code=ResponseCode.ALREADY_EXISTS
        )

class EventFullException(ConflictException):
    """Evento lleno"""
    
    def __init__(self, event_name: str):
        super().__init__(
            message=f"El evento '{event_name}' ha alcanzado su cupo máximo",
            code=ResponseCode.LIMIT_EXCEEDED
        )

class InvalidEventDatesException(ValidationException):
    """Fechas de evento inválidas"""
    
    def __init__(
        self,
        message: str = "Las fechas del evento no son válidas"
    ):
        super().__init__(
            message=message,
            code=ResponseCode.INVALID_DATE_RANGE
        )

class InvalidEventStateTransitionException(ConflictException):
    """Transición de estado inválida"""
    
    def __init__(
        self,
        current_state: str,
        target_state: str
    ):
        message = f"No se puede cambiar el estado de '{current_state}' a '{target_state}'"
        super().__init__(
            message=message,
            code=ResponseCode.INVALID_STATE
        )

class EventNotActiveException(ConflictException):
    """Evento no está activo"""
    
    def __init__(self, event_name: str):
        super().__init__(
            message=f"El evento '{event_name}' no está activo",
            code=ResponseCode.INVALID_OPERATION
        )