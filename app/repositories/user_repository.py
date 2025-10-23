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

    # Validar existencia de correo
    async def exists_email(self, email: str) -> bool:
        user = await self.get_user_by_email(email)
        return user is not None
    
    async def get_by_identificacion(self, identificacion: str) -> Optional[dict]:
        """
        Obtiene un usuario por su número de identificación.
        
        Args:
            identificacion: Número de identificación del usuario
            
        Returns:
            Diccionario con datos del usuario o None si no existe
        """
        try:
            query = self.db.collection('usuarios').where('identificacion', '==', identificacion).limit(1)
            docs = query.stream()
            
            for doc in docs:
                usuario = doc.to_dict()
                usuario['id'] = doc.id
                return usuario
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario por identificación {identificacion}: {str(e)}")
            return None
