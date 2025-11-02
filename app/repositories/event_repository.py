from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone
from google.cloud.firestore import FieldFilter
import logging

from .base_repository import BaseRepository
from app.core.firebase import Collections
from app.schemas.event import EventState

logger = logging.getLogger(__name__)

class EventRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.EVENTOS, "id_evento")

    # Busca evento por nombre y rango de fechas (para detectar duplicados)
    async def get_by_name_and_dates(
        self,
        nombre: str,
        fecha_inicio: date,
        fecha_fin: date
    ) -> Optional[Dict[str, Any]]:
        try:
            # Convertir dates a datetime para Firestore
            fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
            fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
            
            # Buscar eventos con el mismo nombre que se solapen en fechas
            # CORREGIDO: Usar == para nombre_evento y FieldFilter correctamente
            query = self.collection\
                .where(filter=FieldFilter("nombre_evento", "==", nombre))\
                .where(filter=FieldFilter("fecha_inicio", "<=", fecha_fin_dt))\
                .where(filter=FieldFilter("fecha_fin", ">=", fecha_inicio_dt))\
                .limit(1)
            
            docs = query.stream()
            docs_list = list(docs)
            if docs_list:
                doc = docs_list[0]
                data = doc.to_dict()
                data['id_evento'] = doc.id
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error al buscar evento por nombre y fechas: {str(e)}")
            return None

    # Obtiene todos los eventos activos
    async def get_active_events(self) -> List[Dict[str, Any]]:
        return await self.get_all(
            filters={"estado": EventState.ACTIVO.value},
            order_by="fecha_inicio"
        )

    # Obtiene eventos por estado
    async def get_events_by_state(self, estado: EventState) -> List[Dict[str, Any]]:
        return await self.get_all(
            filters={"estado": estado.value},
            order_by="fecha_inicio"
        )
    
    # Obtiene eventos en un rango de fechas - CORREGIDO
    async def get_events_by_date_range(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        estado: Optional[EventState] = None
    ) -> List[Dict[str, Any]]:
        try:
            query = self.collection
            
            # CORREGIDO: Usar FieldFilter y lógica condicional correcta
            if fecha_desde:
                fecha_desde_dt = datetime.combine(fecha_desde, datetime.min.time())
                query = query.where(filter=FieldFilter("fecha_inicio", ">=", fecha_desde_dt))
            
            if fecha_hasta:
                fecha_hasta_dt = datetime.combine(fecha_hasta, datetime.max.time())
                query = query.where(filter=FieldFilter("fecha_inicio", "<=", fecha_hasta_dt))
            
            if estado:
                query = query.where(filter=FieldFilter("estado", "==", estado.value))

            query = query.order_by("fecha_inicio")
            
            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id_evento'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error al obtener eventos por rango de fechas: {str(e)}")
            return []

    # Obtiene eventos de un año específico
    async def get_events_by_year(self, year: int) -> List[Dict[str, Any]]:
        fecha_inicio_year = date(year, 1, 1)
        fecha_fin_year = date(year, 12, 31)
        
        return await self.get_events_by_date_range(fecha_inicio_year, fecha_fin_year)

    # Obtiene los próximos eventos activos - CORREGIDO
    async def get_upcoming_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            today = datetime.now(timezone.utc)
            
            query = self.collection\
                .where(filter=FieldFilter("estado", "==", EventState.ACTIVO.value))\
                .where(filter=FieldFilter("fecha_inicio", ">=", today))\
                .order_by("fecha_inicio")\
                .limit(limit)
            
            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id_evento'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error al obtener próximos eventos: {str(e)}")
            return []

    # Cambia el estado de un evento con auditoría
    async def change_event_state(
        self,
        event_id: str,
        new_state: EventState,
        reason: Optional[str] = None,
        changed_by: Optional[str] = None
    ) -> bool:
        update_data = {
            "estado": new_state.value,
            "state_changed_at": datetime.utcnow()
        }
        
        if reason:
            update_data["state_change_reason"] = reason
        
        if changed_by:
            update_data["state_changed_by"] = changed_by
        
        return await self.update(event_id, update_data)

    # Verifica si un evento ha alcanzado su cupo máximo
    async def is_event_full(self, event_id: str) -> bool:
        event = await self.get_by_id(event_id)
        
        if not event:
            return False
        
        cupo_maximo = event.get('cupo_maximo')
        if cupo_maximo is None:
            return False  # Sin límite de cupo
        
        total_inscritos = event.get('total_inscritos', 0)
        
        return total_inscritos >= cupo_maximo

    # Obtiene un evento con información detallada
    async def get_event_with_details(self, event_id: str) -> Optional[Dict[str, Any]]:
        event = await self.get_by_id(event_id)
        
        if not event:
            return None
        
        # Aquí podrías agregar información adicional
        # como estadísticas calculadas, proyectos asociados, etc.
        
        return event