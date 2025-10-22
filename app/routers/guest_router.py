from fastapi import APIRouter, HTTPException, status
from app.services.guest_service import GuestService
from app.schemas.guest import GuestCreateWithUser, GuestResponse, GuestUpdate

router = APIRouter(
    prefix="/api/v1/admin/invitados",
    tags=["Invitados"]
)

guest_service = GuestService()

# Crear invitado + usuario
@router.post(
    "",
    response_model=GuestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear invitado con usuario (CASCADA)"
)
async def create_guest_with_user(guest_data: GuestCreateWithUser):
    try:
        return await guest_service.create_guest_with_user(guest_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ✅ Obtener solo invitados activos
@router.get(
    "",
    response_model=list[GuestResponse],
    summary="Listar todos los invitados activos"
)
async def get_all_guests():
    guests, _ = await guest_service.get_all_guests(active_only=True)
    return guests


# Obtener invitado por ID
@router.get(
    "/{guest_id}",
    response_model=GuestResponse,
    summary="Obtener invitado por ID"
)
async def get_guest(guest_id: str):
    try:
        return await guest_service.get_guest(guest_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# Actualizar invitado
@router.put(
    "/{guest_id}",
    response_model=GuestResponse,
    summary="Actualizar invitado"
)
async def update_guest(guest_id: str, guest_data: GuestUpdate):
    """
    Actualiza los datos de un invitado existente (no permite cambiar correo, cédula ni programa).
    """
    try:
        return await guest_service.update_guest(guest_id, guest_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Desactivar invitado (Eliminar lógico)
@router.delete(
    "/{guest_id}",
    summary="Desactivar invitado"
)
async def deactivate_guest(guest_id: str, reason: str = "Desactivado por administrador"):
    """
    Desactiva un invitado (no se elimina de la base de datos).
    """
    try:
        await guest_service.deactivate_guest(guest_id, reason)
        return {"status": "success", "message": f"Invitado {guest_id} desactivado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
