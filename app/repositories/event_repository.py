
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import logging

from .base_repository import BaseRepository
from app.core.firebase import Collections
from app.schemas.event import EventState

logger = logging.getLogger(__name__)


class EventRepository(BaseRepository):
    
    def __init__(self):
        super().__init__(Collections.EVENTOS, "id_evento")

#Busca evento por nombre y rango de fechas (para detectar duplicados)
    async def get_by_name_and_dates(
        self,
        nombre: str,
        fecha_inicio: date,
        fecha_fin: date
    ) -> Optional[Dict[str, Any]]:
        try:
            # Buscar eventos con el mismo nombre que se solapen en fechas
            docs = self.collection\
                .where("nombre_evento", "==", nombre)\
                .where("fecha_inicio", "<=", fecha_fin)\
                .where("fecha_fin", ">=", fecha_inicio)\
                .limit(1)\
                .stream()
            
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

#Obtiene eventos por estado
    async def get_events_by_state(self, estado: EventState) -> List[Dict[str, Any]]:

        return await self.get_all(
            filters={"estado": estado.value},
            order_by="fecha_inicio"
        )
    
# Obtiene eventos en un rango de fechas
    async def get_events_by_date_range(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        estado: Optional[EventState] = None
    ) -> List[Dict[str, Any]]:

        try:
            query = self.collection
            
            if fecha_desde:
                fecha_desde_dt = datetime.combine(fecha_desde, datetime.min.time())
            query = query.where("fecha_inicio", ">=", fecha_desde_dt)
            
            if fecha_hasta:
                fecha_hasta_dt = datetime.combine(fecha_hasta, datetime.max.time())
            query = query.where("fecha_inicio", "<=", fecha_hasta_dt)
            
            if estado:
                query = query.where("estado", "==", estado.value)

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

# Obtiene eventos de un año especifico
    async def get_events_by_year(self, year: int) -> List[Dict[str, Any]]:
        fecha_inicio_year = date(year, 1, 1)
        fecha_fin_year = date(year, 12, 31)
        
        return await self.get_events_by_date_range(fecha_inicio_year, fecha_fin_year)

# Obtiene los proximos eventos activos
    async def get_upcoming_events(self, limit: int = 5) -> List[Dict[str, Any]]:

        try:
            today = date.today()
            
            docs = self.collection\
                .where("estado", "==", EventState.ACTIVO.value)\
                .where("fecha_inicio", ">=", today)\
                .order_by("fecha_inicio")\
                .limit(limit)\
                .stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id_evento'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error al obtener próximos eventos: {str(e)}")
            return []

# Actualiza las estadísticas de un evento
    """
    async def update_event_statistics(
        self,
        event_id: str,
        total_inscritos: Optional[int] = None,
        total_proyectos: Optional[int] = None
    ) -> bool:
        update_data = {}
        
        if total_inscritos is not None:
            update_data['total_inscritos'] = total_inscritos
        
        if total_proyectos is not None:
            update_data['total_proyectos'] = total_proyectos
        
        if update_data:
            return await self.update(event_id, update_data)
        
        return False
    """

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