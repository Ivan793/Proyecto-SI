from .base_exceptions import NotFoundException, ConflictException, DependencyException, ValidationException

class SectorNotFoundException(NotFoundException):
    """Sector no encontrado"""
    
    def __init__(self, sector_id: str):
        super().__init__(
            resource="Sector",
            identifier=sector_id
        )


class SectorAlreadyExistsException(ConflictException):
    """Sector ya existe"""
    
    def __init__(self, sector_name: str):
        super().__init__(
            message=f"Ya existe un sector con el nombre '{sector_name}'",
            conflict_field="nombre_sector"
        )


class SectorHasDependenciesException(DependencyException):
    """Sector tiene dependencias activas"""
    
    def __init__(self, sector_id: str):
        super().__init__(
            message=f"No se puede eliminar o desactivar el sector '{sector_id}' porque tiene dependencias activas"
        )


class InvalidSectorDataException(ValidationException):
    """Datos de sector inválidos"""
    
    def __init__(self, field: str, message: str = "Datos de sector inválidos"):
        super().__init__(
            message=message,
            field=field
        )
