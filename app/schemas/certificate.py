# app/schemas/certificate.py

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FormatoSalidaEnum(str, Enum):
    """Formatos de salida para certificados"""
    PDF_INDIVIDUAL = "pdf_individual"
    ZIP = "zip"
    PDF_COMBINADO = "pdf_combinado"


class EstadoCertificadoEnum(str, Enum):
    """Estados posibles de un certificado"""
    DISPONIBLE = "disponible"
    EXPIRADO = "expirado"
    ENVIADO = "enviado"


# ==================== REQUESTS ====================

class GenerarCertificadoPorProyectoRequest(BaseModel):
    """Request para generar certificados de un proyecto"""
    id_proyecto: str
    id_evento: Optional[str] = None
    incluir_calificacion: bool = Field(default=False)
    director_evento: Optional[str] = Field(None, max_length=100)
    coordinador_general: Optional[str] = Field(None, max_length=100)
    formato_salida: FormatoSalidaEnum = Field(default=FormatoSalidaEnum.ZIP)


class GenerarCertificadoPorEventoRequest(BaseModel):
    """Request para generar certificados de un evento completo"""
    id_evento: str
    incluir_calificacion: bool = Field(default=False)
    director_evento: Optional[str] = Field(None, max_length=100)
    coordinador_general: Optional[str] = Field(None, max_length=100)
    agrupar_por_proyecto: bool = Field(default=True)


class GenerarCertificadoIndividualRequest(BaseModel):
    """Request para generar certificado individual"""
    id_estudiante: str
    id_proyecto: str
    incluir_calificacion: bool = Field(default=False)
    director_evento: Optional[str] = Field(None, max_length=100)
    coordinador_general: Optional[str] = Field(None, max_length=100)


class GenerarMiCertificadoRequest(BaseModel):
    """Request para que un estudiante genere su certificado"""
    id_proyecto: str
    enviar_por_correo: bool = Field(default=False)
    incluir_calificacion: bool = Field(default=True)


class EnviarCertificadosRequest(BaseModel):
    """Request para enviar certificados por correo"""
    id_lote: str
    asunto: Optional[str] = Field(
        None,
        max_length=150,
        description="Asunto del correo"
    )
    mensaje_personalizado: Optional[str] = Field(None, max_length=500)
    enviar_copia_coordinador: bool = Field(default=False)
    correo_coordinador: Optional[EmailStr] = None

    @validator('correo_coordinador')
    def validar_correo_coordinador(cls, correo, values):
        """Valida que se proporcione correo si se solicita copia"""
        if values.get('enviar_copia_coordinador') and not correo:
            raise ValueError(
                'Debe proporcionar correo_coordinador si enviar_copia_coordinador es True'
            )
        return correo


class ReenviarCertificadoRequest(BaseModel):
    """Request para reenviar certificado"""
    correo_alternativo: Optional[EmailStr] = None


# ==================== RESPONSES ====================

class EstudianteCertificadoInfo(BaseModel):
    """Información de estudiante en certificado"""
    nombre_completo: str
    identificacion: str
    nombre_archivo_certificado: str


class ProyectoCertificadoInfo(BaseModel):
    """Información de proyecto en certificado"""
    titulo: str
    evento: str
    calificacion: Optional[str] = None


class CertificadoGeneradoResponse(BaseModel):
    """Response al generar certificados"""
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
    """Response al generar mi certificado"""
    id_certificado: str
    nombre_archivo: str
    url_descarga: str
    proyecto: ProyectoCertificadoInfo
    tamano_bytes: int
    fecha_generacion: str
    expira_en: str
    enviado_correo: bool
    correo_destino: Optional[str] = None


class EstadoEnvioEstudiante(BaseModel):
    """Estado de envío por estudiante"""
    nombre: str
    correo: str
    estado: str  # "enviado" o "fallido"


class CertificadosEnviadosResponse(BaseModel):
    """Response al enviar certificados"""
    total_enviados: int
    total_fallidos: int
    enviados_a: List[EstadoEnvioEstudiante]
    fecha_envio: str


class ProyectoDisponibleInfo(BaseModel):
    """Información de proyecto disponible para certificado"""
    id_proyecto: str
    titulo_proyecto: str
    tipo_actividad: str
    evento: dict
    calificacion: Optional[str] = None
    tiene_certificado: bool
    fecha_expone: Optional[str] = None


class MisCertificadosItem(BaseModel):
    """Item de certificado en listado"""
    id_certificado: str
    nombre_archivo: str
    proyecto: dict
    fecha_generacion: str
    estado: EstadoCertificadoEnum
    url_descarga: Optional[str] = None
    tamano_bytes: int


class PaginacionCertificados(BaseModel):
    """Paginación para certificados"""
    total: int
    pagina_actual: int
    total_paginas: int
    limite: int


class MisCertificadosResponse(BaseModel):
    """Response del listado de certificados"""
    certificados: List[MisCertificadosItem]
    paginacion: PaginacionCertificados


class ProyectosDisponiblesResponse(BaseModel):
    """Response de proyectos disponibles"""
    proyectos: List[ProyectoDisponibleInfo]
    total: int


# ==================== MODELOS INTERNOS ====================

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
    calificacion: Optional[str] = None
    fecha_subida: Optional[datetime] = None


class DatosEventoCertificado(BaseModel):
    """Datos del evento para el certificado"""
    id_evento: str
    nombre_evento: str
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    lugar: Optional[str] = None


class CertificadoMetadata(BaseModel):
    """Metadata de un certificado generado"""
    id_certificado: str
    id_estudiante: str
    id_proyecto: str
    id_evento: str
    nombre_archivo: str
    ruta_archivo: str
    fecha_generacion: datetime
    fecha_expiracion: datetime
    estado: EstadoCertificadoEnum
    tamano_bytes: int
    enviado_correo: bool = False
    fecha_envio: Optional[datetime] = None