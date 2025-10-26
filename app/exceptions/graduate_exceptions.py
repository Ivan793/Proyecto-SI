from .base_exceptions import NotFoundException, ConflictException, DependencyException


class GraduateNotFoundException(NotFoundException):
    def __init__(self, graduate_id: str):
        super().__init__(resource="Egresado", identifier=graduate_id)


class GraduateAlreadyExistsException(ConflictException):
    def __init__(self, user_id: str):
        super().__init__(
            message=f"Ya existe un egresado asociado al usuario {user_id}",
            conflict_field="id_usuario"
        )


class GraduateHasDependenciesException(DependencyException):
    def __init__(self, graduate_id: str):
        super().__init__(
            message=f"No se puede eliminar o desactivar el egresado {graduate_id} porque tiene dependencias activas"
        )
