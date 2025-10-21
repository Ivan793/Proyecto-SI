
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Union
from datetime import date
from enum import Enum


class TipoPersonaEnum(str, Enum):
    """Tipos de persona válidos en el sistema"""
    ESTUDIANTE = "Estudiante"
    DOCENTE = "Docente"
    INVITADO = "Invitado"
    EGRESADO = "Egresado"


class TipoActividadEnum(str, Enum):
    """Tipos de actividad académica"""
    POSTER = "póster"
    TALLER = "taller"
    PONENCIA = "ponencia"
    CONFERENCIA = "conferencia"
    ARTICULO = "articulo"


class CodigoLineaEnum(int, Enum):
    """Líneas de investigación"""
    TIC = 0  # Tecnologías de la Información y la Comunicación
    TRANSFORMACION_DIGITAL = 1  # Transformación Digital


class FiltrosReporte(BaseModel):
    """Filtros para generar reportes personalizados"""
    tipo_persona: Optional[TipoPersonaEnum] = None
    codigo_programa: Optional[str] = None
    codigo_materia: Optional[str] = None
    semestre: Optional[int] = Field(None, ge=1, le=10)
    id_docente: Optional[str] = None
    id_estudiante: Optional[str] = None
    id_proyecto: Optional[str] = None
    codigo_linea: Optional[CodigoLineaEnum] = None
    codigo_sublinea: Optional[int] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    tipo_actividad: Optional[TipoActividadEnum] = None

    @validator('fecha_hasta')
    def validar_rango_fechas(cls, fecha_hasta, values):
        """Valida que fecha_hasta sea posterior a fecha_desde"""
        fecha_desde = values.get('fecha_desde')
        if fecha_desde and fecha_hasta and fecha_hasta < fecha_desde:
            raise ValueError(
                'La fecha final no puede ser anterior a la fecha inicial'
            )
        return fecha_hasta

    class Config:
        use_enum_values = True


class GenerarReporteRequest(BaseModel):
    """Request para generar un reporte PDF"""
    filtros: FiltrosReporte
    titulo_reporte: Optional[str] = Field(None, max_length=100)
    incluir_graficos: bool = Field(default=True)


class EnviarReporteRequest(BaseModel):
    """Request para enviar un reporte por correo"""
    id_reporte: str
    correo_destino: Union[EmailStr, List[EmailStr]]
    asunto: Optional[str] = Field(None, max_length=150)
    mensaje_personalizado: Optional[str] = Field(None, max_length=500)
    copias: Optional[List[EmailStr]] = None
    copias_ocultas: Optional[List[EmailStr]] = None


class GenerarYEnviarReporteRequest(BaseModel):
    """Request para generar y enviar reporte en una sola operación"""
    filtros: FiltrosReporte
    correo_destino: Union[EmailStr, List[EmailStr]]
    titulo_reporte: Optional[str] = Field(None, max_length=100)
    asunto: Optional[str] = Field(None, max_length=150)
    mensaje_personalizado: Optional[str] = Field(None, max_length=500)
    incluir_graficos: bool = Field(default=True)
    copias: Optional[List[EmailStr]] = None
    guardar_reporte: bool = Field(default=False)


class ReporteGeneradoResponse(BaseModel):
    """Response al generar un reporte exitosamente"""
    id_reporte: str
    nombre_archivo: str
    url_descarga: str
    tamano_bytes: int
    fecha_generacion: str
    expira_en: str
    total_registros: int


class ReporteEnviadoResponse(BaseModel):
    """Response al enviar un reporte exitosamente"""
    enviado_a: List[str]
    fecha_envio: str
    id_envio: str


class HistorialReporte(BaseModel):
    """Información de un reporte en el historial"""
    id_reporte: str
    nombre_archivo: str
    fecha_generacion: str
    filtros_aplicados: dict
    total_registros: int
    tamano_bytes: int
    estado: str  # disponible, expirado, enviado
    enviado_a: Optional[List[str]] = None


class PaginacionResponse(BaseModel):
    """Información de paginación"""
    total: int
    pagina_actual: int
    total_paginas: int
    limite: int


class HistorialReportesResponse(BaseModel):
    """Response del historial de reportes"""
    reportes: List[HistorialReporte]
    paginacion: PaginacionResponse


class ErrorDetail(BaseModel):
    """Detalle de un error de validación"""
    campo: str
    mensaje: str


class ErrorResponse(BaseModel):
    """Response estándar para errores"""
    status: str = "error"
    mensaje: str
    errores: Optional[List[ErrorDetail]] = None


class SuccessResponse(BaseModel):
    """Response estándar para respuestas exitosas"""
    status: str = "success"
    mensaje: str
    data: Optional[dict] = None