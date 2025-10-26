import qrcode
import base64
import logging
from io import BytesIO
from app.repositories.assistence_repository import AssistenceRepository
from app.repositories.user_repository import UserRepository
from app.repositories.event_repository import EventRepository

logger = logging.getLogger(__name__)

class AssistenceService:

    def __init__(self):
        self.repository = AssistenceRepository()
        self.user_repo = UserRepository()
        self.event_repo = EventRepository()

    async def generar_qr_evento(self, id_evento: str, url_front: str) -> dict | None:
        """
        Genera un código QR que contiene la URL para el registro de asistencia
        del evento y lo devuelve como una cadena base64.
        """
        try:
            event = await self.event_repo.get_by_id(id_evento)
            if not event:
                return {"error": "Evento no encontrado", "status": 404}

            url_qr = f"{url_front}/registro-asistencia/{id_evento}"

            qr_img = qrcode.make(url_qr)
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            return {"url_qr": url_qr, "qr_image": qr_base64}

        except Exception as e:
            logger.error(f"Error al generar QR del evento: {str(e)}")
            return None

    async def registrar_asistencia(self, id_evento: str, correo: str):
        """
        Registra la asistencia de un usuario a un evento, validando existencia del evento y del usuario.
        """
        try:
            user = await self.user_repo.get_user_by_email(correo)
            if not user:
                return {"error": "Usuario no encontrado", "status": 404}
            print(user)
            event = await self.event_repo.get_by_id(id_evento)
            if not event:
                return {"error": "Evento no encontrado", "status": 404}

            id_usuario = user.get("id") or user.get("uid")  # depende de cómo guardes el ID
            datos = {
                "id_usuario": id_usuario,
                "correo": correo,
            }

            resultado = self.assistence_repo.agregar_asistencia(id_evento, datos)
            return {"mensaje": "Asistencia registrada correctamente", "resultado": resultado}

        except Exception as e:
            logging.error(f"Error al registrar asistencia: {str(e)}")
            return {"error": "Error interno del servidor", "status": 500}