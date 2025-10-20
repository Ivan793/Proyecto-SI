from typing import List, Optional, Dict, Any
import logging
from firebase_admin import auth as firebase_auth

from app.repositories.guest_repository import GuestRepository
from app.repositories.user_repository import UserRepository
from app.schemas.guest import (
    GuestCreateWithUser,
    GuestCreateWithExistingUser,
    GuestUpdate,
    GuestResponse,
    GuestWithUserResponse
)
from app.schemas.user import UserCreate
from app.exceptions.guest_exceptions import (
    GuestNotFoundException,
    GuestAlreadyExistsException
)
from app.exceptions.user_exceptions import UserNotFoundException, UserAlreadyExistsException

logger = logging.getLogger(__name__)

class GuestService:
    """
    Servicio para la gestión de invitados.
    Los invitados pueden ser creados directamente o asociados a usuarios existentes.
    No requiere permisos de administrador.
    """

    def __init__(self):
        self.guest_repo = GuestRepository()
        self.user_repo = UserRepository()

    async def create_guest_with_user(
        self,
        guest_data: GuestCreateWithUser
    ) -> GuestResponse:
        """
        Crea un invitado con un nuevo usuario en Firebase Authentication y Firestore.
        """

        usuario_data = guest_data.usuario

        # Validar que el correo no exista
        existing_user = await self.user_repo.get_user_by_email(usuario_data.correo)
        if existing_user:
            raise UserAlreadyExistsException("correo", usuario_data.correo)

        try:
            # Crear usuario en Firebase Authentication
            firebase_user = firebase_auth.create_user(
                email=usuario_data.correo,
                password=usuario_data.contraseña,
                display_name=f"{usuario_data.nombres} {usuario_data.apellidos}",
                disabled=False
            )

            user_id = firebase_user.uid
            logger.info(f"Usuario invitado creado en Firebase Auth: {user_id}")

            # Crear usuario en Firestore con rol "Invitado"
            user_dict = usuario_data.model_dump(exclude={"contraseña"})
            user_dict.update({
                "estado": "ACTIVO",
                "rol": "Invitado"
            })
            await self.user_repo.create(user_dict, document_id=user_id)
            logger.info(f"Usuario invitado registrado en Firestore: {user_id}")

            # Crear registro de invitado asociado
            guest_dict = {
                "id_usuario": user_id,
                "id_evento": guest_data.id_evento,
                "institucion": guest_data.institucion,
                "activo": True
            }

            guest_id = await self.guest_repo.create(guest_dict)
            logger.info(f"Invitado creado y vinculado: {guest_id} -> {user_id}")

            guest = await self.guest_repo.get_by_id(guest_id)
            return GuestResponse(**guest)

        except Exception as e:
            # Rollback si falla algo
            if 'firebase_user' in locals():
                try:
                    firebase_auth.delete_user(firebase_user.uid)
                    logger.warning(f"Usuario eliminado de Firebase por rollback: {firebase_user.uid}")
                except Exception as rollback_error:
                    logger.error(f"Error en rollback: {rollback_error}")

            logger.error(f"Error creando invitado con usuario: {str(e)}")
            raise

    async def create_guest_with_existing_user(
        self,
        guest_data: GuestCreateWithExistingUser
    ) -> GuestResponse:
        """
        Crea un invitado asociado a un usuario existente.
        """

        # Verificar que el usuario exista
        user = await self.user_repo.get_by_id(guest_data.id_usuario)
        if not user:
            raise UserNotFoundException(guest_data.id_usuario)

        # Verificar que no esté ya registrado como invitado
        existing_guest = await self.guest_repo.get_guest_by_user_id(guest_data.id_usuario)
        if existing_guest:
            raise GuestAlreadyExistsException(guest_data.id_usuario)

        # Crear el invitado
        guest_dict = guest_data.model_dump()
        guest_id = await self.guest_repo.create(guest_dict)

        guest = await self.guest_repo.get_by_id(guest_id)
        return GuestResponse(**guest)

    async def get_guest(self, guest_id: str) -> GuestResponse:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise GuestNotFoundException(guest_id)
        return GuestResponse(**guest)

    async def get_guest_with_user(self, guest_id: str) -> GuestWithUserResponse:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise GuestNotFoundException(guest_id)

        user = await self.user_repo.get_by_id(guest["id_usuario"])
        if not user:
            raise UserNotFoundException(guest["id_usuario"])

        return GuestWithUserResponse(
            invitado=GuestResponse(**guest),
            usuario=user
        )

    async def get_all_guests(
        self,
        active_only: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[GuestResponse], int]:
        filters = {"activo": True} if active_only else {}
        guests = await self.guest_repo.get_all(filters=filters)

        total = len(guests)
        start = (page - 1) * limit
        end = start + limit
        paginated_guests = guests[start:end]

        return [GuestResponse(**g) for g in paginated_guests], total

    async def update_guest(
        self,
        guest_id: str,
        guest_data: GuestUpdate
    ) -> GuestResponse:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise GuestNotFoundException(guest_id)

        update_dict = guest_data.model_dump(exclude_none=True)
        if update_dict:
            await self.guest_repo.update(guest_id, update_dict)

        updated_guest = await self.guest_repo.get_by_id(guest_id)
        return GuestResponse(**updated_guest)

    async def deactivate_guest(self, guest_id: str, reason: str) -> bool:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise GuestNotFoundException(guest_id)

        return await self.guest_repo.update(guest_id, {
            "activo": False,
            "razon_desactivacion": reason
        })

    async def activate_guest(self, guest_id: str) -> bool:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise GuestNotFoundException(guest_id)

        return await self.guest_repo.update(guest_id, {"activo": True})

    async def get_guests_by_event(self, event_id: str) -> List[GuestResponse]:
        guests = await self.guest_repo.get_guests_by_event(event_id)
        return [GuestResponse(**g) for g in guests]

    async def get_guest_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.guest_repo.get_guest_by_user_id(user_id)
