from app.services.guest_service import guest_service
from app.schemas.guest import GuestCreate


def crear_invitado_controlador(data: GuestCreate):
    return guest_service.crear_invitado(data)


def obtener_todos_invitados_controlador():
    return guest_service.obtener_invitados()


def actualizar_invitado_controlador(id_invitado: str, data: dict):
    return guest_service.actualizar_invitado(id_invitado, data)


def eliminar_invitado_controlador(id_invitado: str):
    return guest_service.eliminar_invitado(id_invitado)
