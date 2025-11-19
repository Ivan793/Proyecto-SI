import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
import io
import logging
import os

logger = logging.getLogger("cloudinary_service")

# Cargar credenciales desde variables de entorno
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dnlmloos6"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "636328951124317"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "DGb6Q2o-EeMl6caj-xUz8wIMTew"),
    secure=True
)


async def upload_pdf_to_cloudinary(file: UploadFile) -> str:

    """
    Sube un archivo (PDF u otro) a Cloudinary y devuelve la URL pública.
    Si ocurre un error, lanza una excepción controlada.
    """
    try:
        # Leer el contenido del archivo en memoria
        file_content = await file.read()

        # Subir archivo a Cloudinary
        upload_result = cloudinary.uploader.upload(
            io.BytesIO(file_content),
            resource_type="raw",      # 'raw' permite subir cualquier tipo de archivo, no solo imágenes
            folder="proyectos",       # Carpeta donde se almacenarán los archivos
            public_id=file.filename.split('.')[0],  # Nombre sin extensión
            overwrite=True
        )

        # Validar respuesta
        if not upload_result or "secure_url" not in upload_result:
            raise RuntimeError("No se obtuvo URL de Cloudinary")

        # Devolver la URL segura
        return upload_result["secure_url"]

    except Exception as e:
        logger.error(f" Error subiendo archivo a Cloudinary: {e}")
        raise RuntimeError(f"Error al subir archivo a Cloudinary: {str(e)}")