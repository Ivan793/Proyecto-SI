import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.firebase import firebase_client, Collections

logger = logging.getLogger(__name__)


class AssistenceRepository:
    def __init__(self):
        self.collection = firebase_client.get_db().collection(Collections.EVENTOS)

    async def agregar_asistencia(self, id_evento: str, datos: dict)-> Optional[Dict[str, Any]]:
        """
        Agrega una nueva asistencia en la subcolección 'asistentes' del evento.
        """
        try:

            # Agregar timestamp
            datos["fecha_registro"] = datetime.now(timezone.utc)
            
            # Referencia a la subcolección de asistentes
            asistentes_ref = self.collection.document(id_evento).collection(Collections.ASISTENCIAS)

            # Agregar documento
            doc_ref = asistentes_ref.document()  # Esto crea una referencia con ID automático
            # Ejecutar la operación de Firestore en un hilo
            await asyncio.to_thread(doc_ref.set, datos)
            logger.info(f"Asistencia agregada correctamente al evento {id_evento}, ID: {doc_ref.id}")
            

            return {
                "id_asistencia": doc_ref.id,
                "id_evento": id_evento,
                **datos
            }

        except Exception as e:
            logger.error(f"Error al registrar asistencia: {str(e)}")
            return None
        

    async def verificar_asistencia_duplicada(
            self, 
            id_evento: str, 
            correo: str
        ) -> bool:
            """
            Verifica si un correo ya registró asistencia en el evento.
            """
            try:
                asistentes_ref = self.collection.document(id_evento).collection(Collections.ASISTENCIAS)
                
                # Buscar si ya existe el correo
                query = asistentes_ref.where("correo", "==", correo.lower()).limit(1)
                docs = await asyncio.to_thread(lambda: list(query.stream()))
                
                # Convertir a lista y verificar
                return any(True for _ in docs)
                
            except Exception as e:
                logger.error(f"Error verificando asistencia duplicada: {str(e)}")
                return False

    async def obtener_asistencias(
        self, 
        id_evento: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las asistencias de un evento.
        """
        try:
            asistentes_ref = self.collection.document(id_evento).collection(Collections.ASISTENCIAS)
            
            query = asistentes_ref.order_by("fecha_registro", direction="DESCENDING")
            
            if limit:
                query = query.limit(limit)
            
            docs = await asyncio.to_thread(lambda: list(query.stream()))
            
            asistencias = []
            for doc in docs:
                data = doc.to_dict()
                data["id_asistencia"] = doc.id
                asistencias.append(data)
            
            return asistencias
            
        except Exception as e:
            logger.error(f"Error obteniendo asistencias: {str(e)}")
            return []

    async def contar_asistencias(self, id_evento: str) -> int:
        """
        Cuenta el total de asistencias de un evento.
        """
        try:
            asistentes_ref = self.collection.document(id_evento).collection(Collections.ASISTENCIAS)            
            docs = await asyncio.to_thread(lambda: list(asistentes_ref.stream()))
            return len(docs)
            
        except Exception as e:
            logger.error(f"Error contando asistencias: {str(e)}")
            return 0
