from typing import Any, Dict, Optional
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
        self.assistence_repo = AssistenceRepository()
        self.user_repo = UserRepository()
        self.event_repo = EventRepository()

    async def generar_qr_evento(self, id_evento: str, url_front: str) -> dict | None:
        """
        Genera un código QR que contiene la URL para el registro de asistencia
        del evento y lo devuelve como una cadena base64.
        """
        try:
            # Verificar que el evento existe
            event = await self.event_repo.get_by_id(id_evento)
            if not event:
                return {"error": "Evento no encontrado", "status": 404}
            
            # Validar estado del evento
            if event.get("estado") != "ACTIVO":
                return {
                    "error": f"El evento no está activo (estado: {event.get('estado')})",
                    "status": 400
                }

            # Construir URL para escaneo del QR
            url_qr = f"{url_front}/asistencia/registrar/{id_evento}"

            # Generar código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            qr.add_data(url_qr)
            qr.make(fit=True)

            # Convertir a imagen
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            logger.info(f"QR generado para evento {id_evento}")

            return {
                "url_qr": url_qr,
                "qr_base64": qr_base64,
                "evento_nombre": event.get("nombre_evento"),
                "evento_id": id_evento
            }

        except Exception as e:
            logger.error(f"Error al generar QR del evento: {str(e)}")
            return None

    async def registrar_asistencia(self, id_evento: str, correo: str):
        """
        Registra la asistencia de un usuario a un evento,
        validando existencia del evento, estado y que el usuario esté registrado.
        """
        try:
            # Verificar que el evento existe
            event = await self.event_repo.get_by_id(id_evento)
            if not event:
                return {"error": "Evento no encontrado", "status": 404}

            # Verificar estado del evento
            if event.get("estado") != "ACTIVO":
                return {
                    "error": f"No se puede registrar asistencia. Evento {event.get('estado')}",
                    "status": 400
                }
            
            # Normalizar correo
            correo = correo.lower().strip()

            # Verificar si ya registró asistencia
            ya_existe = await self.assistence_repo.verificar_asistencia_duplicada(
                id_evento, 
                correo
            )
            if ya_existe:
                return {
                    "error": "Ya registraste asistencia en este evento",
                    "status": 409
                }
            
            # Buscar usuario
            user = await self.user_repo.get_user_by_email(correo)

            # Si el usuario no existe, no se permite el registro
            if not user:
                logger.warning(f"Correo no registrado intentando registrar asistencia: {correo}")
                return {
                    "error": "El correo no está registrado en el sistema. No puedes registrar asistencia.",
                    "status": 403
                }

            # Si el usuario existe pero está inactivo
            if not user.get("activo", True):
                logger.warning(f"Usuario inactivo intentando registrar asistencia: {correo}")
                return {
                    "error": "Tu cuenta de usuario está inactiva. No puedes registrar asistencia.",
                    "status": 403
                }

            logger.info(f"Usuario activo confirmado: {correo}")

            # Preparar datos de asistencia
            datos = {
                "correo": correo,
                "id_usuario": user.get("id_usuario"),
                "nombre_completo": f"{user.get('primer_nombre', '')} {user.get('segundo_nombre', '')} "
                                   f"{user.get('primer_apellido', '')} {user.get('segundo_apellido', '')}".strip()            }

            # Registrar asistencia en subcolección
            resultado = await self.assistence_repo.agregar_asistencia(id_evento, datos)
            
            if not resultado:
                return {"error": "Error al registrar asistencia", "status": 500}

            # Actualizar contador en evento
            total_asistencias = await self.assistence_repo.contar_asistencias(id_evento)
            await self.event_repo.update(id_evento, {
                "total_inscritos": total_asistencias
            })

            logger.info(f"Asistencia registrada: {correo} -> Evento {id_evento}")

            return {
                "mensaje": "Asistencia registrada correctamente",
                "data": resultado,
                "status": 201
            }

        except Exception as e:
            logger.error(f"Error al registrar asistencia: {str(e)}")
            return {"error": "Error interno del servidor", "status": 500}
        

    async def obtener_asistencias_evento(
            self, 
            id_evento: str,
            limit: Optional[int] = 100
        ) -> Dict[str, Any]:
            """
            Obtiene todas las asistencias de un evento.
            """
            try:
                # Verificar que el evento existe
                event = await self.event_repo.get_by_id(id_evento)
                if not event:
                    return {"error": "Evento no encontrado", "status": 404}

                # Obtener asistencias
                asistencias = await self.assistence_repo.obtener_asistencias(
                    id_evento, 
                    limit=limit
                )
                
                total = await self.assistence_repo.contar_asistencias(id_evento)

                return {
                    "evento": event.get("nombre_evento"),
                    "total_asistencias": total,
                    "asistencias": asistencias,
                    "status": 200
                }

            except Exception as e:
                logger.error(f"Error obteniendo asistencias: {str(e)}")
                return {"error": "Error interno del servidor", "status": 500}