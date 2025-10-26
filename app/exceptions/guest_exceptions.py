from .base_exceptions import NotFoundException, ConflictException, DependencyException


class GuestNotFoundException(NotFoundException):
    def __init__(self, guest_id: str):
        super().__init__(resource="Invitado", identifier=guest_id)


class GuestAlreadyExistsException(ConflictException):
    def __init__(self, user_id: str):
        super().__init__(
            message=f"Ya existe un invitado asociado al usuario {user_id}",
            conflict_field="id_usuario"
        )


class GuestHasDependenciesException(DependencyException):
    def __init__(self, guest_id: str):
        super().__init__(
            message=f"No se puede eliminar o desactivar el invitado {guest_id} porque tiene dependencias activas"
        )
