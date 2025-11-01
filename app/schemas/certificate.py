# app/schemas/certificate.py
"""
Schemas para el módulo de certificados.
Corrige validación de tipos de Firestore.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class EstadoCertificadoEnum(str, Enum):
    """Estados posibles de un certificado"""
    DISPONIBLE = "disponible"
    EXPIRADO = "expirado"
    ENVIADO = "enviado"


class FormatoSalidaEnum(str, Enum):
    """Formatos de salida para certificados"""
    PDF_INDIVIDUAL = "pdf_individual"
    ZIP = "zip"
    PDF_COMBINADO = "pdf_combinado"


# ==================== SCHEMAS DE DATOS ====================

class DatosEstudianteCertificado(BaseModel):
    """Datos del estudiante para el certificado"""
    id_estudiante: str
    nombres: str
    apellidos: str
    identificacion: str
    codigo_programa: str
    nombre_programa: Optional[str] = None
    correo: str


class DatosProyectoCertificado(BaseModel):
    """Datos del proyecto para el certificado"""
    id_proyecto: str
    titulo_proyecto: str
    tipo_actividad: str
    calificacion: Optional[Union[str, float, int]] = None  # ✅ Acepta string, float o int
    fecha_subida: Optional[datetime] = None
    
    @field_validator('calificacion', mode='before')
    @classmethod
    def convertir_calificacion(cls, v):
        """Convierte calificación a string si viene como número"""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return str(v)
        return v


class DatosEventoCertificado(BaseModel):
    """Datos del evento para el certificado"""
    id_evento: str
    nombre_evento: str
    fecha_inicio: Union[datetime, str]  # ✅ Acepta datetime o string
    fecha_fin: Optional[Union[datetime, str]] = None
    lugar: Optional[str] = None
    
    @field_validator('fecha_inicio', 'fecha_fin', mode='before')
    @classmethod
    def convertir_fecha(cls, v):
        """Convierte fechas de Firestore a datetime"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except:
                return v
        return v


# ==================== REQUESTS ====================

class GenerarCertificadoPorProyectoRequest(BaseModel):
    """Request para generar certificados por proyecto"""
    id_proyecto: str = Field(..., description="ID del proyecto")
    id_evento: Optional[str] = Field(None, description="ID del evento (opcional)")
    incluir_calificacion: bool = Field(False, description="Incluir calificación en certificado")
    director_evento: Optional[str] = Field(None, description="Nombre del director del evento")
    coordinador_general: Optional[str] = Field(None, description="Nombre del coordinador general")
    formato_salida: FormatoSalidaEnum = Field(
        FormatoSalidaEnum.ZIP,
        description="Formato de salida de los certificados"
    )



class GenerarCertificadoIndividualRequest(BaseModel):
    """Request para generar certificado individual"""
    id_estudiante: str = Field(..., description="ID del estudiante")
    id_proyecto: str = Field(..., description="ID del proyecto")
    incluir_calificacion: bool = Field(False, description="Incluir calificación")
    director_evento: Optional[str] = None
    coordinador_general: Optional[str] = None


class GenerarMiCertificadoRequest(BaseModel):
    """Request para que un estudiante genere su propio certificado"""
    id_proyecto: str = Field(..., description="ID del proyecto")
    incluir_calificacion: bool = Field(False, description="Incluir calificación")
    enviar_por_correo: bool = Field(False, description="Enviar por correo automáticamente")


class EnviarCertificadosRequest(BaseModel):
    """Request para enviar certificados por correo"""
    id_lote: str = Field(..., description="ID del lote de certificados")
    asunto: Optional[str] = Field(None, description="Asunto del correo")
    mensaje_personalizado: Optional[str] = Field(None, description="Mensaje adicional")


# ==================== RESPONSES ====================

class EstudianteCertificadoInfo(BaseModel):
    """Información de estudiante en respuesta"""
    nombre_completo: str
    identificacion: str
    nombre_archivo_certificado: str


class ProyectoCertificadoInfo(BaseModel):
    """Información de proyecto en respuesta"""
    titulo: str
    evento: str
    calificacion: Optional[str] = None


class CertificadoGeneradoResponse(BaseModel):
    """Response de certificado generado"""
    id_lote: str
    nombre_archivo: str
    url_descarga: str
    cantidad_certificados: int
    estudiantes: List[EstudianteCertificadoInfo]
    tamano_bytes: int
    fecha_generacion: str
    expira_en: str
    proyecto: ProyectoCertificadoInfo


class CertificadoIndividualResponse(BaseModel):
    """Response de certificado individual"""
    id_certificado: str
    nombre_archivo: str
    url_descarga: str
    estudiante: EstudianteCertificadoInfo
    tamano_bytes: int
    fecha_generacion: str


class MiCertificadoResponse(BaseModel):
    """Response para certificado de estudiante"""
    id_certificado: str
    nombre_archivo: str
    url_descarga: str
    proyecto: ProyectoCertificadoInfo
    tamano_bytes: int
    fecha_generacion: str
    expira_en: str
    enviado_correo: bool
    correo_destino: Optional[str] = None


class CertificadosEnviadosResponse(BaseModel):
    """Response de envío de certificados"""
    enviado_a: List[str]
    fecha_envio: str
    cantidad_enviados: int


class MisCertificadosResponse(BaseModel):
    """Response con listado de certificados del estudiante"""
    certificados: List[dict]
    paginacion: dict


class ProyectosDisponiblesResponse(BaseModel):
    """Response con proyectos disponibles para certificado"""
    proyectos: List[dict]
    total: int


class CertificadoMetadata(BaseModel):
    """Metadata de certificado almacenado"""
    id_certificado: str
    id_estudiante: str
    id_proyecto: str
    id_evento: str
    nombre_archivo: str
    ruta_archivo: str
    tamano_bytes: int
    fecha_generacion: datetime
    fecha_expiracion: datetime
    estado: EstadoCertificadoEnum
    enviado_correo: bool = False