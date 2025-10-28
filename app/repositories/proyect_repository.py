from app.repositories.base_repository import BaseRepository
from app.exceptions.base_exceptions import DatabaseException, NotFoundException
from app.services.cloudinary_service import upload_pdf_to_cloudinary
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ProyectoRepository(BaseRepository):
    def __init__(self):
        super().__init__(collection_name="proyectos", id_field="id_proyecto")

    async def create_with_pdf(self, data: dict, archivo) -> str:
        """
        Crea un nuevo proyecto subiendo obligatoriamente un archivo PDF a Cloudinary.
        """
        if not archivo:
            raise ValueError("Debe subir un archivo PDF para crear el proyecto.")

        try:
            # Subir el PDF
            pdf_url = await upload_pdf_to_cloudinary(archivo)

            # Agregar metadata
            data["archivo_pdf"] = pdf_url
            data["fecha_subida"] = datetime.now(timezone.utc).isoformat()
            data["activo"] = True

            return await super().create(data)
        except Exception as e:
            logger.error(f"Error al crear proyecto: {e}")
            raise DatabaseException(f"No se pudo crear el proyecto: {str(e)}")

    async def update_with_pdf(self, proyecto_id: str, data: dict, archivo=None) -> bool:
        """
        Actualiza los datos de un proyecto. Si se envía un nuevo PDF, se reemplaza.
        """
        try:
            if archivo:
                pdf_url = await upload_pdf_to_cloudinary(archivo)
                data["archivo_pdf"] = pdf_url

            return await super().update(proyecto_id, data)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error al actualizar proyecto {proyecto_id}: {e}")
            raise DatabaseException("No se pudo actualizar el proyecto")