import logging
from datetime import datetime
from app.core.firebase import firebase_client, Collections

logger = logging.getLogger(__name__)


class AssistenceRepository:
    def __init__(self):
        self.collection = firebase_client.get_db().collection(Collections.EVENTOS)

    def agregar_asistencia(self, id_evento: str, datos: dict):
        """
        Agrega una nueva asistencia en la subcolección 'asistentes' del evento.
        """
        try:
            asistentes_ref = self.collection.document(id_evento).collection("asistentes")
            datos["fecha_registro"] = datetime.utcnow()

            doc_ref, _ = asistentes_ref.add(datos)
            logger.info(f"Asistencia agregada correctamente al evento {id_evento}")

            return {"id": doc_ref.id}

        except Exception as e:
            logger.error(f"Error al registrar asistencia: {str(e)}")
            return None
