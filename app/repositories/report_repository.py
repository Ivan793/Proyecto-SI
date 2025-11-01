from typing import List, Dict, Optional, Any
from datetime import datetime, date
from firebase_admin import firestore
from app.schemas.report import FiltrosReporte


class ReportRepository:
    """Repositorio para consultas de datos de reportes"""
    
    def __init__(self):
        self.db = firestore.client()
    
    async def obtener_datos_por_filtros(
        self, 
        filtros: FiltrosReporte
    ) -> List[Dict[str, Any]]:
        """
        Obtiene datos de la base de datos aplicando los filtros especificados.
        
        Args:
            filtros: Objeto con los filtros a aplicar
            
        Returns:
            Lista de documentos que cumplen los filtros
        """
        resultados = []
        
        # Consulta principal a proyectos
        query = self.db.collection('proyectos')
        
        # Aplicar filtros uno por uno
        if filtros.id_proyecto:
            query = query.where('id_proyecto', '==', filtros.id_proyecto)
        
        if filtros.id_docente:
            query = query.where('id_docente', '==', filtros.id_docente)
        
        if filtros.id_estudiante:
            query = query.where('id_estudiante', '==', filtros.id_estudiante)
        
        if filtros.codigo_linea is not None:
            query = query.where('codigo_linea', '==', filtros.codigo_linea)
        
        if filtros.codigo_sublinea is not None:
            query = query.where('codigo_sublinea', '==', filtros.codigo_sublinea)
        
        if filtros.tipo_actividad:
            query = query.where('tipo_actividad', '==', filtros.tipo_actividad)
        
        # Ejecutar consulta
        docs = query.stream()
        
        for doc in docs:
            proyecto_data = doc.to_dict()
            proyecto_data['id'] = doc.id
            
            # Enriquecer datos con información relacionada
            proyecto_enriquecido = await self._enriquecer_proyecto(
                proyecto_data, 
                filtros
            )
            
            if proyecto_enriquecido:
                resultados.append(proyecto_enriquecido)
        
        # Aplicar filtros de fecha después de obtener los datos
        if filtros.fecha_desde or filtros.fecha_hasta:
            resultados = self._filtrar_por_fechas(
                resultados, 
                filtros.fecha_desde, 
                filtros.fecha_hasta
            )
        
        return resultados
    
    async def _enriquecer_proyecto(
        self, 
        proyecto: Dict[str, Any], 
        filtros: FiltrosReporte
    ) -> Optional[Dict[str, Any]]:
        """
        Enriquece los datos del proyecto con información relacionada.
        
        Args:
            proyecto: Datos básicos del proyecto
            filtros: Filtros adicionales a aplicar
            
        Returns:
            Proyecto enriquecido o None si no cumple filtros
        """
        try:
            # Obtener información del estudiante
            if proyecto.get('id_estudiante'):
                estudiante_doc = self.db.collection('estudiantes').document(
                    proyecto['id_estudiante']
                ).get()
                
                if estudiante_doc.exists:
                    estudiante_data = estudiante_doc.to_dict()
                    
                    # Aplicar filtro de semestre si existe
                    if filtros.semestre and estudiante_data.get('semestre') != filtros.semestre:
                        return None
                    
                    # Aplicar filtro de programa si existe
                    if filtros.codigo_programa and estudiante_data.get('codigo_programa') != filtros.codigo_programa:
                        return None
                    
                    # Obtener datos del usuario del estudiante
                    if estudiante_data.get('id_usuario'):
                        usuario_doc = self.db.collection('usuarios').document(
                            estudiante_data['id_usuario']
                        ).get()
                        
                        if usuario_doc.exists:
                            usuario_data = usuario_doc.to_dict()
                            estudiante_data['usuario'] = {
                                'nombres': usuario_data.get('nombres'),
                                'apellidos': usuario_data.get('apellidos'),
                                'correo': usuario_data.get('correo')
                            }
                    
                    proyecto['estudiante'] = estudiante_data
            
            # Obtener información del docente
            if proyecto.get('id_docente'):
                docente_doc = self.db.collection('docentes').document(
                    proyecto['id_docente']
                ).get()
                
                if docente_doc.exists:
                    docente_data = docente_doc.to_dict()
                    
                    # Aplicar filtro de programa del docente si existe
                    if filtros.codigo_programa and docente_data.get('codigo_programa') != filtros.codigo_programa:
                        return None
                    
                    # Obtener datos del usuario del docente
                    if docente_data.get('id_usuario'):
                        usuario_doc = self.db.collection('usuarios').document(
                            docente_data['id_usuario']
                        ).get()
                        
                        if usuario_doc.exists:
                            usuario_data = usuario_doc.to_dict()
                            docente_data['usuario'] = {
                                'nombres': usuario_data.get('nombres'),
                                'apellidos': usuario_data.get('apellidos'),
                                'correo': usuario_data.get('correo')
                            }
                    
                    proyecto['docente'] = docente_data
            
            # Obtener información de materia si existe relación
            if proyecto.get('id_docente_materia'):
                docente_materia_doc = self.db.collection('docente_materias').document(
                    proyecto['id_docente_materia']
                ).get()
                
                if docente_materia_doc.exists:
                    docente_materia_data = docente_materia_doc.to_dict()
                    
                    # Aplicar filtro de materia si existe
                    if filtros.codigo_materia and docente_materia_data.get('codigo_materia') != filtros.codigo_materia:
                        return None
                    
                    # Obtener información de la materia
                    if docente_materia_data.get('codigo_materia'):
                        materia_doc = self.db.collection('materias').document(
                            docente_materia_data['codigo_materia']
                        ).get()
                        
                        if materia_doc.exists:
                            proyecto['materia'] = materia_doc.to_dict()
            
            # Obtener información de línea de investigación
            if proyecto.get('codigo_linea') is not None:
                linea_doc = self.db.collection('linea_investigacion').document(
                    str(proyecto['codigo_linea'])
                ).get()
                
                if linea_doc.exists:
                    proyecto['linea_investigacion'] = linea_doc.to_dict()
            
            # Obtener información de sublínea de investigación
            if proyecto.get('codigo_sublinea') is not None:
                sublinea_doc = self.db.collection('sublinea_investigacion').document(
                    str(proyecto['codigo_sublinea'])
                ).get()
                
                if sublinea_doc.exists:
                    proyecto['sublinea_investigacion'] = sublinea_doc.to_dict()
            
            return proyecto
            
        except Exception as e:
            print(f"Error enriqueciendo proyecto: {str(e)}")
            return None
    
    def _filtrar_por_fechas(
        self, 
        resultados: List[Dict[str, Any]], 
        fecha_desde: Optional[date], 
        fecha_hasta: Optional[date]
    ) -> List[Dict[str, Any]]:
        """
        Filtra resultados por rango de fechas.
        
        Args:
            resultados: Lista de proyectos
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            
        Returns:
            Lista filtrada
        """
        if not fecha_desde and not fecha_hasta:
            return resultados
        
        resultados_filtrados = []
        
        for proyecto in resultados:
            fecha_subida = proyecto.get('fecha_subida')
            
            if fecha_subida:
                # Convertir a date si es datetime
                if isinstance(fecha_subida, datetime):
                    fecha_proyecto = fecha_subida.date()
                elif isinstance(fecha_subida, date):
                    fecha_proyecto = fecha_subida
                else:
                    continue
                
                # Aplicar filtros de fecha
                if fecha_desde and fecha_proyecto < fecha_desde:
                    continue
                
                if fecha_hasta and fecha_proyecto > fecha_hasta:
                    continue
                
                resultados_filtrados.append(proyecto)
        
        return resultados_filtrados
    
    async def obtener_estadisticas(
        self, 
        datos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calcula estadísticas generales de los datos.
        
        Args:
            datos: Lista de proyectos
            
        Returns:
            Diccionario con estadísticas
        """
        if not datos:
            return {
                'total_proyectos': 0,
                'por_tipo_actividad': {},
                'por_linea': {},
                'por_programa': {},
                'por_semestre': {}
            }
        
        estadisticas = {
            'total_proyectos': len(datos),
            'por_tipo_actividad': {},
            'por_linea': {},
            'por_programa': {},
            'por_semestre': {}
        }
        
        # Agrupar por tipo de actividad
        for proyecto in datos:
            tipo = proyecto.get('tipo_actividad', 'No especificado')
            estadisticas['por_tipo_actividad'][tipo] = \
                estadisticas['por_tipo_actividad'].get(tipo, 0) + 1
            
            # Agrupar por línea de investigación
            if proyecto.get('linea_investigacion'):
                nombre_linea = proyecto['linea_investigacion'].get('nombre_linea', 'Sin línea')
                estadisticas['por_linea'][nombre_linea] = \
                    estadisticas['por_linea'].get(nombre_linea, 0) + 1
            
            # Agrupar por programa
            if proyecto.get('estudiante', {}).get('codigo_programa'):
                codigo_prog = proyecto['estudiante']['codigo_programa']
                estadisticas['por_programa'][codigo_prog] = \
                    estadisticas['por_programa'].get(codigo_prog, 0) + 1
            
            # Agrupar por semestre
            if proyecto.get('estudiante', {}).get('semestre'):
                semestre = proyecto['estudiante']['semestre']
                estadisticas['por_semestre'][f"Semestre {semestre}"] = \
                    estadisticas['por_semestre'].get(f"Semestre {semestre}", 0) + 1
        
        return estadisticas
    
    async def guardar_reporte_generado(
        self, 
        reporte_info: Dict[str, Any]
    ) -> str:
        """
        Guarda información de un reporte generado.
        
        Args:
            reporte_info: Información del reporte
            
        Returns:
            ID del documento creado
        """
        reporte_ref = self.db.collection('reportes_generados').document()
        reporte_ref.set(reporte_info)
        return reporte_ref.id
    
    async def obtener_reporte_por_id(self, id_reporte: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un reporte por su ID.
        
        Args:
            id_reporte: ID del reporte
            
        Returns:
            Datos del reporte o None
        """
        doc = self.db.collection('reportes_generados').document(id_reporte).get()
        
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        
        return None
    
    async def obtener_historial_reportes(
        self, 
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        limite: int = 20,
        pagina: int = 1
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Obtiene el historial de reportes generados.
        
        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            limite: Registros por página
            pagina: Número de página
            
        Returns:
            Tupla con (lista de reportes, total de registros)
        """
        query = self.db.collection('reportes_generados').order_by(
            'fecha_generacion', 
            direction=firestore.Query.DESCENDING
        )
        
        # Aplicar filtros de fecha si existen
        if fecha_desde:
            query = query.where('fecha_generacion', '>=', fecha_desde)
        
        if fecha_hasta:
            query = query.where('fecha_generacion', '<=', fecha_hasta)
        
        # Obtener total de registros
        total = len(list(query.stream()))
        
        # Aplicar paginación
        offset = (pagina - 1) * limite
        query = query.limit(limite).offset(offset)
        
        reportes = []
        for doc in query.stream():
            reporte = doc.to_dict()
            reporte['id'] = doc.id
            reportes.append(reporte)
        
        return reportes, total
    
    async def eliminar_reporte(self, id_reporte: str) -> bool:
        """
        Elimina un reporte del sistema.
        
        Args:
            id_reporte: ID del reporte
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            self.db.collection('reportes_generados').document(id_reporte).delete()
            return True
        except Exception as e:
            print(f"Error eliminando reporte: {str(e)}")
            return False