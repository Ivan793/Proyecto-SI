from app.exceptions.base_exceptions import NotFoundException, ConflictException

class ProyectoNotFoundException(NotFoundException):
    def __init__(self, proyecto_id: str):
        super().__init__(resource="Proyecto", identifier=proyecto_id)

class ProyectoConflictException(ConflictException):
    def __init__(self, message: str):
        super().__init__(message=message, conflict_field="titulo_proyecto")
