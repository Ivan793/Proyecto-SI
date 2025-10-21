from typing import Optional, List, Dict, Any
import logging
from .base_repository import BaseRepository
from app.core.firebase import Collections

logger = logging.getLogger(__name__)


class GraduateRepository(BaseRepository):
    def __init__(self):
        super().__init__(Collections.EGRESADOS, "id_egresado")

    async def get_active_graduates(self) -> List[Dict[str, Any]]:
        try:
            graduates = await self.get_all(filters={"activo": True})
            logger.info(f"{len(graduates)} egresados activos obtenidos.")
            return graduates
        except Exception as e:
            logger.error(f"Error al obtener egresados activos: {e}")
            return []

    async def get_graduate_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            graduate = await self.get_by_field("id_usuario", user_id)
            if graduate:
                logger.info(f"Egresado encontrado para usuario {user_id}.")
            else:
                logger.warning(f"No se encontró egresado para usuario {user_id}.")
            return graduate
        except Exception as e:
            logger.error(f"Error al obtener egresado por usuario {user_id}: {e}")
            return None

    async def get_all_paginated(self, filters: Optional[Dict[str, Any]] = None, page: int = 1, limit: int = 20):
        try:
            all_data = await self.get_all(filters)
            total = len(all_data)
            start = (page - 1) * limit
            end = start + limit
            return all_data[start:end], total
        except Exception as e:
            logger.error(f"Error al obtener egresados paginados: {e}")
            return [], 0

    def get_user_fields(self, data: dict) -> dict:
        user_fields = {
            "nombres": data.get("nombres"),
            "apellidos": data.get("apellidos"),
            "correo": data.get("correo"),
            "contraseña": data.get("contraseña"),
            "rol": data.get("rol", "egresado"),
            "identificacion": data.get("identificacion"),
            "tipo_documento": data.get("tipo_documento"),
            "telefono": data.get("telefono"),
            "fecha_nacimiento": data.get("fecha_nacimiento"),
            "genero": data.get("genero"),
            "identidad_sexual": data.get("identidad_sexual"),
            "nacionalidad": data.get("nacionalidad"),
            "pais_residencia": data.get("pais_residencia"),
            "departamento": data.get("departamento"),
            "municipio": data.get("municipio"),
            "direccion_residencia": data.get("direccion_residencia"),
        }
        return {k: v for k, v in user_fields.items() if v is not None}
