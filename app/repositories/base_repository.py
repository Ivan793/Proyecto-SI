from typing import Optional, List, Dict, Any, TypeVar, Generic
from google.cloud.firestore_v1 import Client
from datetime import datetime, timezone
import logging

from app.core.firebase import get_firestore_client
from app.exceptions.base_exceptions import DatabaseException, NotFoundException

# Importar para manejar los datetime de Firestore
try:
    from google.api_core.datetime_helpers import DatetimeWithNanoseconds
except ImportError:
    DatetimeWithNanoseconds = type(None)

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseRepository(Generic[T]):

    def __init__(self, collection_name: str, id_field: str = "id"):
        self.collection_name = collection_name
        self._db: Optional[Client] = None
        self.id_field = id_field

    @property
    def db(self) -> Client:
        if self._db is None:
            self._db = get_firestore_client()
        return self._db

    @property
    def collection(self):
        return self.db.collection(self.collection_name)

    # ==================== CONVERSIÓN DE DATOS FIRESTORE ====================
    def _convert_firestore_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not data:
            return data

        converted = {}
        for key, value in data.items():
            if type(value).__name__ == "DatetimeWithNanoseconds":
                converted[key] = datetime.fromisoformat(value.isoformat())
            elif isinstance(value, dict):
                converted[key] = self._convert_firestore_data(value)
            elif isinstance(value, list):
                converted[key] = [
                    self._convert_firestore_data(item) if isinstance(item, dict) else
                    datetime.fromisoformat(item.isoformat()) if type(item).__name__ == "DatetimeWithNanoseconds" else
                    item
                    for item in value
                ]
            else:
                converted[key] = value
        return converted

    # ==================== CRUD ====================

    async def create(self, data: Dict[str, Any], document_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            now = datetime.now(timezone.utc)
            data['created_at'] = now
            data['updated_at'] = now

            if document_id:
                doc_ref = self.collection.document(document_id)
                doc_ref.set(data)
                created_id = document_id
            else:
                _, doc_ref = self.collection.add(data)
                created_id = doc_ref.id

            data[self.id_field] = created_id
            logger.info(f"Documento creado en {self.collection_name}: {created_id}")
            return data

        except Exception as e:
            logger.error(f"Error al crear documento en {self.collection_name}: {str(e)}")
            raise DatabaseException(f"Error al crear registro: {str(e)}")

    async def get_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc_ref = self.collection.document(document_id)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                data[self.id_field] = doc.id
                return self._convert_firestore_data(data)

            return None

        except Exception as e:
            logger.error(f"Error al obtener documento {document_id}: {str(e)}")
            raise DatabaseException(f"Error al obtener registro: {str(e)}")

    async def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        try:
            query = self.collection

            if filters:
                for field, value in filters.items():
                    query = query.where(field, "==", value)

            if order_by:
                query = query.order_by(order_by)

            if offset:
                query = query.offset(offset)

            if limit:
                query = query.limit(limit)

            docs = query.stream()

            results = []
            for doc in docs:
                data = doc.to_dict()
                data[self.id_field] = doc.id
                results.append(self._convert_firestore_data(data))

            return results

        except Exception as e:
            logger.error(f"Error al obtener documentos de {self.collection_name}: {str(e)}")
            raise DatabaseException(f"Error al obtener registros: {str(e)}")

    async def update(self, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            doc_ref = self.collection.document(document_id)
            doc = doc_ref.get()

            if not doc.exists:
                raise NotFoundException(resource=self.collection_name, identifier=document_id)

            data['updated_at'] = datetime.now(timezone.utc)
            doc_ref.update(data)

            # Devolver el documento actualizado
            updated_doc = doc_ref.get()
            updated_data = updated_doc.to_dict()
            updated_data[self.id_field] = updated_doc.id
            return self._convert_firestore_data(updated_data)

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error al actualizar documento {document_id}: {str(e)}")
            raise DatabaseException(f"Error al actualizar registro: {str(e)}")

    async def soft_delete(self, document_id: str) -> Dict[str, Any]:
        return await self.update(document_id, {
            'estado': 'INACTIVO',
            'deleted_at': datetime.now(timezone.utc)
        })

    async def exists(self, field: str, value: Any) -> bool:
        try:
            docs = self.collection.where(field, "==", value).limit(1).stream()
            return len(list(docs)) > 0
        except Exception as e:
            logger.error(f"Error al verificar existencia: {str(e)}")
            raise DatabaseException(f"Error al verificar existencia: {str(e)}")

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        try:
            query = self.collection
            if filters:
                for field, value in filters.items():
                    query = query.where(field, "==", value)
            docs = query.stream()
            return len(list(docs))
        except Exception as e:
            logger.error(f"Error al obtener documento {document}: {e}")
            raise DatabaseException(f"Error al contar registros: {str(e)}")

    async def get_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        try:
            docs = self.collection.where(field, "==", value).limit(1).stream()
            docs_list = list(docs)

            if docs_list:
                doc = docs_list[0]
                data = doc.to_dict()
                data[self.id_field] = doc.id
                return self._convert_firestore_data(data)

            return None

        except Exception as e:
            logger.error(f"Error al buscar por {field}: {str(e)}")
            raise DatabaseException(f"Error al buscar registro: {str(e)}")

    async def batch_create(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            batch = self.db.batch()
            results = []
            now = datetime.now(timezone.utc)

            for data in documents:
                doc_ref = self.collection.document()
                data['created_at'] = now
                data['updated_at'] = now
                batch.set(doc_ref, data)
                data[self.id_field] = doc_ref.id
                results.append(data)

            batch.commit()
            logger.info(f"Batch creado: {len(results)} documentos en {self.collection_name}")
            return results

        except Exception as e:
            logger.error(f"Error en batch create: {str(e)}")
            raise DatabaseException(f"Error al crear registros en lote: {str(e)}")
