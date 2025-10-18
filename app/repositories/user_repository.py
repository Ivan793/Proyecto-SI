<<<<<<< HEAD
# app/repositories/user_repository.py
from typing import Dict, List

# Simulación de base de datos en memoria
fake_users_db: List[Dict] = []

def create_user(data: Dict):
    new_user = {
        "id_usuario": f"user_{len(fake_users_db) + 1}",
        **data
    }
    fake_users_db.append(new_user)
    return {
        "mensaje": "✅ Usuario creado exitosamente (simulado)",
        "data": new_user
    }

def get_all_users():
    return fake_users_db
=======
from typing import Optional, List, Dict, Any
import logging

from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.USUARIOS, "id_usuario")

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await self.get_by_field("correo", email)

    async def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"rol": role})

    async def get_active_users(self) -> List[Dict[str, Any]]:
        return await self.get_all(filters={"activo": True})

    async def user_exists(self, user_id: str) -> bool:
        user = await self.get_by_id(user_id)
        return user is not None
>>>>>>> origin/Mateo
