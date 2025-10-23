# app/repositories/certificate_repository.py

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.repositories.base_repository import BaseRepository


class CertificateRepository(BaseRepository):
    """Repositorio para gestión de certificados"""
    
    def __init__(self):
        super().__init__('certificados')
    
    async def guardar_lote_certificados(
        self,
        datos_lote: Dict[str, Any]
    ) -> str:
        """
        Guarda información de un lote de certificados generados.
        
        Args:
            datos_lote: Diccionario con la información del lote
            
        Returns:
            ID del lote guardado
        """
        id_lote = datos_lote.get('id_lote')
        
        documento = {
            'id_lote': id_lote,
            'id_proyecto': datos_lote.get('id_proyecto'),
            'id_evento': datos_lote.get('id_evento'),
            'nombre_archivo': datos_lote.get('nombre_archivo'),
            'ruta_archivo': datos_lote.get('ruta_archivo'),
            'cantidad_certificados': datos_lote.get('cantidad_certificados'),
            'tamano_bytes': datos_lote.get('tamano_bytes'),
            'fecha_generacion': datos_lote.get('fecha_generacion'),
            'fecha_expiracion': datos_lote.get('fecha_expiracion'),
            'estado': datos_lote.get('estado'),
            'estudiantes': datos_lote.get('estudiantes', []),
            'tipo': 'lote',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        await self.create(documento, document_id=id_lote)
        return id_lote
    
    async def guardar_certificado_individual(
        self,
        datos_certificado: Dict[str, Any]
    ) -> str:
        """
        Guarda información de un certificado individual.
        
        Args:
            datos_certificado: Diccionario con la información del certificado
            
        Returns:
            ID del certificado guardado
        """
        id_certificado = datos_certificado.get('id_certificado')
        
        documento = {
            'id_certificado': id_certificado,
            'id_estudiante': datos_certificado.get('id_estudiante'),
            'id_proyecto': datos_certificado.get('id_proyecto'),
            'id_evento': datos_certificado.get('id_evento'),
            'nombre_archivo': datos_certificado.get('nombre_archivo'),
            'ruta_archivo': datos_certificado.get('ruta_archivo'),
            'tamano_bytes': datos_certificado.get('tamano_bytes'),
            'fecha_generacion': datos_certificado.get('fecha_generacion'),
            'fecha_expiracion': datos_certificado.get('fecha_expiracion'),
            'estado': datos_certificado.get('estado'),
            'enviado_correo': datos_certificado.get('enviado_correo', False),
            'fecha_envio': datos_certificado.get('fecha_envio'),
            'tipo': 'individual',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        await self.create(documento, document_id=id_certificado)
        return id_certificado
    
    async def obtener_por_id(
        self,
        id_certificado: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un certificado por su ID.
        
        Args:
            id_certificado: ID del certificado
            
        Returns:
            Diccionario con los datos del certificado o None
        """
        return await self.get_by_id(id_certificado)
    
    async def obtener_por_estudiante(
        self,
        id_estudiante: str,
        limite: int = 20,
        pagina: int = 1
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Obtiene todos los certificados de un estudiante.
        
        Args:
            id_estudiante: ID del estudiante
            limite: Cantidad de registros por página
            pagina: Número de página
            
        Returns:
            Tupla con (lista de certificados, total de registros)
        """
        # Obtener todos los certificados del estudiante
        certificados = await self.get_all(
            filters={'id_estudiante': id_estudiante}
        )
        
        # Ordenar por fecha de generación (más recientes primero)
        certificados.sort(
            key=lambda x: x.get('fecha_generacion', datetime.min),
            reverse=True
        )
        
        total = len(certificados)
        
        # Paginar
        inicio = (pagina - 1) * limite
        fin = inicio + limite
        certificados_paginados = certificados[inicio:fin]
        
        # Enriquecer con estado actualizado
        for cert in certificados_paginados:
            if cert.get('fecha_expiracion'):
                if datetime.now() > cert['fecha_expiracion']:
                    cert['estado'] = 'expirado'
                    # Actualizar en la base de datos
                    await self.update(
                        cert['id_certificado'],
                        {'estado': 'expirado'}
                    )
        
        return certificados_paginados, total
    
    async def verificar_certificado_valido(
        self,
        id_estudiante: str,
        id_proyecto: str
    ) -> bool:
        """
        Verifica si existe un certificado válido para un estudiante y proyecto.
        
        Args:
            id_estudiante: ID del estudiante
            id_proyecto: ID del proyecto
            
        Returns:
            True si existe un certificado válido
        """
        certificados = await self.get_all(filters={
            'id_estudiante': id_estudiante,
            'id_proyecto': id_proyecto
        })
        
        # Verificar si alguno está aún válido
        for cert in certificados:
            if cert.get('estado') == 'disponible':
                if cert.get('fecha_expiracion'):
                    if datetime.now() <= cert['fecha_expiracion']:
                        return True
        
        return False
    
    async def actualizar_estado_envio(
        self,
        id_certificado: str,
        enviado: bool
    ) -> bool:
        """
        Actualiza el estado de envío de un certificado.
        
        Args:
            id_certificado: ID del certificado
            enviado: True si fue enviado
            
        Returns:
            True si se actualizó correctamente
        """
        return await self.update(id_certificado, {
            'enviado_correo': enviado,
            'fecha_envio': datetime.now() if enviado else None,
            'updated_at': datetime.now()
        })
    
    async def actualizar_estado(
        self,
        id_certificado: str,
        nuevo_estado: str
    ) -> bool:
        """
        Actualiza el estado de un certificado.
        
        Args:
            id_certificado: ID del certificado
            nuevo_estado: Nuevo estado
            
        Returns:
            True si se actualizó correctamente
        """
        return await self.update(id_certificado, {
            'estado': nuevo_estado,
            'updated_at': datetime.now()
        })
    
    async def obtener_certificados_expirados(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los certificados que han expirado.
        
        Returns:
            Lista de certificados expirados
        """
        todos_certificados = await self.get_all()
        
        expirados = []
        fecha_actual = datetime.now()
        
        for cert in todos_certificados:
            if cert.get('estado') == 'disponible':
                if cert.get('fecha_expiracion'):
                    if fecha_actual > cert['fecha_expiracion']:
                        expirados.append(cert)
        
        return expirados
    
    async def eliminar_certificado(
        self,
        id_certificado: str
    ) -> bool:
        """
        Elimina un certificado de la base de datos.
        
        Args:
            id_certificado: ID del certificado a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        return await self.delete(id_certificado)
    
    async def obtener_por_lote(
        self,
        id_lote: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un lote de certificados.
        
        Args:
            id_lote: ID del lote
            
        Returns:
            Diccionario con la información del lote
        """
        lote = await self.get_by_id(id_lote)
        
        if lote and lote.get('tipo') == 'lote':
            return lote
        
        return None
    
    async def obtener_estadisticas_certificados(
        self,
        id_evento: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de certificados generados.
        
        Args:
            id_evento: Filtrar por evento específico
            fecha_desde: Fecha inicial del rango
            fecha_hasta: Fecha final del rango
            
        Returns:
            Diccionario con estadísticas
        """
        filters = {}
        if id_evento:
            filters['id_evento'] = id_evento
        
        certificados = await self.get_all(filters=filters)
        
        # Filtrar por fechas si se proporcionan
        if fecha_desde or fecha_hasta:
            certificados_filtrados = []
            for cert in certificados:
                fecha_gen = cert.get('fecha_generacion')
                if fecha_gen:
                    if fecha_desde and fecha_gen < fecha_desde:
                        continue
                    if fecha_hasta and fecha_gen > fecha_hasta:
                        continue
                    certificados_filtrados.append(cert)
            certificados = certificados_filtrados
        
        # Calcular estadísticas
        total_certificados = len(certificados)
        total_individuales = sum(1 for c in certificados if c.get('tipo') == 'individual')
        total_lotes = sum(1 for c in certificados if c.get('tipo') == 'lote')
        total_enviados = sum(1 for c in certificados if c.get('enviado_correo'))
        total_disponibles = sum(1 for c in certificados if c.get('estado') == 'disponible')
        total_expirados = sum(1 for c in certificados if c.get('estado') == 'expirado')
        
        # Tamaño total
        tamano_total = sum(c.get('tamano_bytes', 0) for c in certificados)
        
        return {
            'total_certificados': total_certificados,
            'total_individuales': total_individuales,
            'total_lotes': total_lotes,
            'total_enviados': total_enviados,
            'total_disponibles': total_disponibles,
            'total_expirados': total_expirados,
            'tamano_total_bytes': tamano_total,
            'tamano_total_mb': round(tamano_total / (1024 * 1024), 2)
        }