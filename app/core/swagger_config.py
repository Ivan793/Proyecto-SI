from typing import Dict, Any

# Ejemplos comunes reutilizables
COMMON_EXAMPLES = {
    "user_id": "U8Lp4X91rQt99pK3mD5s",
    "teacher_id": "TEElkzBShoDC6beuFjHE", 
    "student_id": "A3Df7H29mLp93sN1xT8q",
    "event_id": "EV7Tz5A23fWx19oK9jK1a",
    "project_id": "P4Tz5A23fWx19oK9jK1a",
    "subject_code": "MAT101",
    "faculty_id": "FAC_ING",
    "program_code": "ING_SIS",
    "group_code": 101,
    
}

# Ejemplos específicos por esquema
SCHEMA_EXAMPLES: Dict[str, Dict[str, Any]] = {
    "UserCreate": {
        "tipo_documento": "CC",
        "identificacion": "1023456789",
        "nombres": "David José",
        "apellidos": "Rodríguez González",
        "genero": "Hombre",
        "identidad_sexual": "Heterosexual",
        "fecha_nacimiento": "2000-06-03",
        "nacionalidad": "Colombiana",
        "pais_residencia": "Colombia",
        "departamento": "Cesar",
        "municipio": "Valledupar",
        "ciudad_residencia": "Valledupar",
        "direccion_residencia": "Calle 45 #22-10, Barrio San José",
        "telefono": "+57301343343",
        "correo": "david.rodriguez@unicesar.edu.co",
        "contraseña": "Usuario123#",
        "rol": "Estudiante"
    },
    
    "EventCreate": {
        "nombre_evento": "ExpoSoftware 2025-II",
        "descripcion": "Exposición de proyectos del primer semestre 2025",
        "fecha_inicio": "2025-10-30T00:00:00",
        "fecha_fin": "2025-11-01T23:59:59",
        "lugar": "Auditorio Principal UPC",
        "cupo_maximo": 100,
    },
    
    "SubjectCreate": {
        "codigo_materia": "PROG3",
        "nombre_materia": "Programación III",
        "ciclo_semestral": "Ciclo Profesional"
    },
    
    "GroupCreate": {
        "codigo_grupo": 101,
        "codigo_materia": "PROG3"
    },
    
    "TeacherSubjectCreate": {
        "id_docente": "TEElkzBShoDC6beuFjHE",
        "codigo_materia": "MAT101",
        "codigo_grupo": 202
    },
    
    "ResearchLineCreate": {
        "codigo_linea": 1,
        "nombre_linea": "Tecnologías de la Información y la comunicación"
    },
    
    "SubResearchLineCreate": {
        "nombre_sublinea": "Sistemas de información",
        "codigo_linea": 1
    },
    
    "ThematicAreaCreate": {
        "nombre_area": "Desarrollo de sistemas de información",
        "codigo_sublinea": 1
    },
    
    "ProyectoCreate": {
        "id_docente": "DOC001",
        "id_estudiante": "EST001", 
        "id_docente_materia": "DOCMAT001",
        "codigo_linea": 101,
        "codigo_sublinea": 202,
        "titulo_proyecto": "Sistema de Gestión Académica",
        "tipo_actividad": 1,
        "formato_pdf": "PDF",
        "calificacion": "4.5"
    },
    "FacultyCreate": {
        "id_facultad": "FAC_ING",
        "nombre_facultad": "Ingenierías y Tecnologías"
    },
    
    "ProgramCreate": {
        "codigo_programa": "ING_SIS",
        "nombre_programa": "Ingeniería de Sistemas",
        "id_facultad": "FAC_ING"
    },
}

# Respuestas de ejemplo para Swagger
RESPONSE_EXAMPLES = {
    "SuccessResponse": {
        "summary": "Respuesta exitosa",
        "value": {
            "status": "success",
            "message": "Operación realizada exitosamente",
            "data": {"id": "abc123", "name": "Ejemplo"},
            "code": "SUCCESS"
        }
    },
    
    "ErrorResponse": {
        "summary": "Error de validación",
        "value": {
            "status": "error",
            "message": "Datos de entrada inválidos",
            "errors": [
                {
                    "field": "correo",
                    "message": "El formato del correo es inválido",
                    "type": "value_error.email",
                    "value": "correo_invalido"
                }
            ],
            "code": "VALIDATION_ERROR",
            "timestamp": "2025-01-15T10:30:00Z",
            "path": "/api/v1/usuarios"
        }
    },
    
    "PaginatedResponse": {
        "summary": "Respuesta paginada",
        "value": {
            "status": "success", 
            "message": "Datos obtenidos correctamente",
            "data": [
                {"id": "1", "nombre": "Elemento 1"},
                {"id": "2", "nombre": "Elemento 2"}
            ],
            "pagination": {
                "page": 1,
                "limit": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": True,
                "has_prev": False
            },
            "code": "SUCCESS"
        }
    }
}

def get_example_for_schema(schema_name: str) -> Dict[str, Any]:
    """Obtiene el ejemplo para un esquema específico"""
    return SCHEMA_EXAMPLES.get(schema_name, {})

def get_response_example(response_type: str) -> Dict[str, Any]:
    """Obtiene el ejemplo para un tipo de respuesta"""
    return RESPONSE_EXAMPLES.get(response_type, {})