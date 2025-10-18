# app/routers/guest_router.py
from fastapi import APIRouter
from app.services.guest_service import guest_service

router = APIRouter(prefix="/invitado", tags=["Invitado"])


@router.post("/")
def crear_invitado(data: dict):
    """
    Crea un nuevo invitado junto con su usuario asociado (en cascada).
    """
    return guest_service.crear_invitado(data)


@router.get("/")
def obtener_todos_invitados():
    """
    Devuelve la lista completa de invitados.
    """
    return guest_service.obtener_invitados()


@router.put("/{id_invitado}")
def actualizar_invitado(id_invitado: str, data: dict):
    """
    Actualiza los datos de un invitado existente.
    """
    return guest_service.actualizar_invitado(id_invitado, data)


@router.delete("/{id_invitado}")
def eliminar_invitado(id_invitado: str):
    """
    Elimina un invitado por su ID.
    """
    return guest_service.eliminar_invitado(id_invitado)
