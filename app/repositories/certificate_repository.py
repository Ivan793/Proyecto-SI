# app/repositories/certificate_repository.py

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
import logging

from app.repositories.base_repository import BaseRepository
from app.core.firebase import get_firestore_client

logger = logging.getLogger(__name__)


class CertificateRepository(BaseRepository):
    """Repositorio para gestión de certificados en Firestore"""
    
    def __init__(self):
        super().__init__('certificados')
        # ✅ CORRECCIÓN: Usar _db en lugar de db para la propiedad interna
        self._db = get_firestore_client()
        self.lotes_collection = 'certificados_lotes'

    @property
    def db(self):
        """Acceso de solo lectura al cliente Firestore"""
        return self._db
    
    async def guardar_lote_certificados(self, datos_lote: Dict[str, Any]) -> str:
        """
        Guarda la metadata de un lote de certificados generados.
        
        Args:
            datos_lote: Diccionario con información del lote
            
        Returns:
            ID del lote guardado
        """
        try:
            id_lote = datos_lote.get('id_certificado')  # ✅ Cambiar a id_certificado
            
            # Guardar en Firestore
            doc_ref = self._db.collection(self.lotes_collection).document(id_lote)
            doc_ref.set(datos_lote)
            
            logger.info(f"✅ Lote de certificados guardado: {id_lote}")
            return id_lote
            
        except Exception as e:
            logger.error(f"❌ Error guardando lote de certificados: {str(e)}")
            raise
    
    async def guardar_certificado_individual(self, datos_certificado: Dict[str, Any]) -> str:
        """
        Guarda la metadata de un certificado individual.
        
        Args:
            datos_certificado: Diccionario con información del certificado
            
        Returns:
            ID del certificado guardado
        """
        try:
            id_certificado = datos_certificado.get('id_certificado')
            
            # Guardar en Firestore
            doc_ref = self._db.collection(self.collection_name).document(id_certificado)
            doc_ref.set(datos_certificado)
            
            logger.info(f"✅ Certificado individual guardado: {id_certificado}")
            return id_certificado
            
        except Exception as e:
            logger.error(f"❌ Error guardando certificado individual: {str(e)}")
            raise
    
    async def obtener_por_id(self, id_certificado: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un certificado o lote por su ID.
        Busca primero en lotes, luego en certificados individuales.
        
        Args:
            id_certificado: ID del certificado o lote
            
        Returns:
            Diccionario con los datos o None si no existe
        """
        try:
            # Buscar en lotes
            doc_ref = self._db.collection(self.lotes_collection).document(id_certificado)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            
            # Buscar en certificados individuales
            doc_ref = self._db.collection(self.collection_name).document(id_certificado)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo certificado {id_certificado}: {str(e)}")
            return None
    
    async def obtener_por_estudiante(
        self,
        id_estudiante: str,
        limite: int = 20,
        pagina: int = 1
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Obtiene los certificados de un estudiante con paginación.
        
        Args:
            id_estudiante: ID del estudiante
            limite: Cantidad de resultados por página
            pagina: Número de página
            
        Returns:
            Tupla con (lista de certificados, total)
        """
        try:
            offset = (pagina - 1) * limite
            
            # Consultar certificados del estudiante
            query = (
                self._db.collection(self.collection_name)
                .where('id_estudiante', '==', id_estudiante)
                .order_by('fecha_generacion', direction='DESCENDING')
                .limit(limite)
                .offset(offset)
            )
            
            docs = query.stream()
            certificados = []
            
            for doc in docs:
                cert = doc.to_dict()
                cert['id'] = doc.id
                certificados.append(cert)
            
            # Contar total
            total_query = (
                self._db.collection(self.collection_name)
                .where('id_estudiante', '==', id_estudiante)
            )
            total = len(list(total_query.stream()))
            
            return certificados, total
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo certificados del estudiante {id_estudiante}: {str(e)}")
            return [], 0
    
    async def verificar_certificado_valido(
        self,
        id_estudiante: str,
        id_proyecto: str
    ) -> bool:
        """
        Verifica si existe un certificado válido (no expirado) para un estudiante en un proyecto.
        
        Args:
            id_estudiante: ID del estudiante
            id_proyecto: ID del proyecto
            
        Returns:
            True si existe un certificado válido
        """
        try:
            query = (
                self._db.collection(self.collection_name)
                .where('id_estudiante', '==', id_estudiante)
                .where('id_proyecto', '==', id_proyecto)
                .where('estado', '==', 'disponible')
            )
            
            docs = list(query.stream())
            
            if not docs:
                return False
            
            # Verificar que no esté expirado
            for doc in docs:
                cert = doc.to_dict()
                fecha_exp = cert.get('fecha_expiracion')
                
                if fecha_exp:
                    if isinstance(fecha_exp, str):
                        fecha_exp = datetime.fromisoformat(fecha_exp.replace('Z', '+00:00'))
                    
                    if datetime.now(timezone.utc) < fecha_exp:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error verificando certificado válido: {str(e)}")
            return False
    
    async def actualizar_estado(self, id_lote: str, nuevo_estado: str) -> bool:
        """
        Actualiza el estado de un lote de certificados.
        
        Args:
            id_lote: ID del lote
            nuevo_estado: Nuevo estado (disponible, enviado, expirado)
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            doc_ref = self._db.collection(self.lotes_collection).document(id_lote)
            doc_ref.update({
                'estado': nuevo_estado,
                'fecha_actualizacion': datetime.now(timezone.utc)
            })
            logger.info(f"✅ Estado del lote {id_lote} actualizado a: {nuevo_estado}")
            return True
        except Exception as e:
            logger.error(f"❌ Error actualizando estado del lote {id_lote}: {str(e)}")
            return False
    
    async def actualizar_estado_envio(self, id_certificado: str, enviado: bool) -> bool:
        """
        Actualiza el estado de envío por correo de un certificado individual.
        
        Args:
            id_certificado: ID del certificado
            enviado: True si fue enviado por correo
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            doc_ref = self._db.collection(self.collection_name).document(id_certificado)
            doc_ref.update({
                'enviado_correo': enviado,
                'fecha_envio': datetime.now(timezone.utc) if enviado else None
            })
            logger.info(f"✅ Estado de envío del certificado {id_certificado} actualizado")
            return True
        except Exception as e:
            logger.error(f"❌ Error actualizando estado de envío del certificado {id_certificado}: {str(e)}")
            return False
    
    async def limpiar_certificados_expirados(self) -> int:
        """
        Marca como expirados los certificados cuya fecha de expiración haya pasado.
        
        Returns:
            Cantidad de certificados actualizados
        """
        try:
            ahora = datetime.now(timezone.utc)
            
            # Buscar certificados expirados en lotes
            query_lotes = (
                self._db.collection(self.lotes_collection)
                .where('estado', '==', 'disponible')
                .where('fecha_expiracion', '<', ahora)
            )
            
            docs_lotes = list(query_lotes.stream())
            actualizados = 0
            
            for doc in docs_lotes:
                doc.reference.update({'estado': 'expirado'})
                actualizados += 1
            
            # Buscar certificados individuales expirados
            query_individuales = (
                self._db.collection(self.collection_name)
                .where('estado', '==', 'disponible')
                .where('fecha_expiracion', '<', ahora)
            )
            
            docs_individuales = list(query_individuales.stream())
            
            for doc in docs_individuales:
                doc.reference.update({'estado': 'expirado'})
                actualizados += 1
            
            if actualizados > 0:
                logger.info(f"🗑️ {actualizados} certificados marcados como expirados")
            
            return actualizados
            
        except Exception as e:
            logger.error(f"❌ Error limpiando certificados expirados: {str(e)}")
            return 0
        
    # Agregar este método en la clase CertificateRepository

    async def obtener_lotes_paginados(
        self,
        pagina: int = 1,
        limite: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Obtiene lotes de certificados con paginación.
        
        Args:
            pagina: Número de página
            limite: Cantidad de resultados por página
            
        Returns:
            Tupla con (lista de lotes, total)
        """
        try:
            offset = (pagina - 1) * limite
            
            # Consultar lotes de certificados
            query = (
                self._db.collection(self.lotes_collection)
                .order_by('fecha_generacion', direction='DESCENDING')
                .limit(limite)
                .offset(offset)
            )
            
            docs = query.stream()
            lotes = []
            
            for doc in docs:
                lote = doc.to_dict()
                lote['id'] = doc.id
                lotes.append(lote)
            
            # Contar total
            total_query = self._db.collection(self.lotes_collection)
            total = len(list(total_query.stream()))
            
            logger.info(f"✅ {len(lotes)} lotes obtenidos (página {pagina})")
            
            return lotes, total
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo lotes paginados: {str(e)}")
            return [], 0