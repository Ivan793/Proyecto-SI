"""
Inicialización y configuración de Firebase
"""
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)


class FirebaseClient:
    """Cliente singleton para Firebase"""
    
    _instance: Optional['FirebaseClient'] = None
    _app: Optional[firebase_admin.App] = None
    _db: Optional[firestore.Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
        return cls._instance
    
   # app/core/firebase.py
# SOLO REEMPLAZA EL MÉTODO initialize()

    def initialize(self):
        app_exists = False
        try:
            # Intenta obtener la aplicación por defecto sin un nombre
            # Si tiene éxito, significa que ya está inicializada
            firebase_admin.get_app() 
            app_exists = True
        except ValueError:
            # Si get_app() falla con ValueError, es porque NO está inicializada
            app_exists = False
        
        if not app_exists:
            try:
                # 1. Cargar las credenciales
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                
                # 2. Inicializar la app
                self._app = firebase_admin.initialize_app(cred, {
                    'databaseURL': settings.FIREBASE_DATABASE_URL
                } if settings.FIREBASE_DATABASE_URL else {})
                
                print("INFO:app.core.firebase:Firebase inicializado correctamente.")
                
            except Exception as e:
                print(f"ERROR:app.core.firebase:Error al inicializar Firebase: {e}")
                raise
        else:
            self._app = firebase_admin.get_app()
            print("INFO:app.core.firebase:Firebase ya estaba inicializado.")
    
    def get_db(self) -> firestore.Client:
        if self._db is None:
            self.initialize()
        return self._db
    
    def close(self):
        """Cierra la conexión con Firebase"""
        if self._app is not None:
            firebase_admin.delete_app(self._app)
            self._app = None
            self._db = None
            logger.info("Firebase desconectado")


# Instancia global del cliente
firebase_client = FirebaseClient()


def get_firestore_client() -> firestore.Client:
    """
    Función helper para obtener el cliente de Firestore
    
    Returns:
        Cliente de Firestore
    """
    return firebase_client.get_db()


# ==================== NOMBRES DE COLECCIONES ====================
# Centralizamos los nombres de las colecciones para evitar errores de typo

class Collections:
    """Nombres de colecciones en Firestore"""
    
    # Usuarios y roles
    USUARIOS = "usuarios"
    ESTUDIANTES = "estudiantes"
    DOCENTES = "docentes"
    INVITADOS = "invitados"
    EGRESADOS = "egresados"
    ADMINISTRATIVOS = "administrativos"  # Para administradores
    
    # Estructura académica
    PROGRAMAS = "programas"
    FACULTADES = "facultades"
    MATERIAS = "materias"
    GRUPOS = "grupos"
    DOCENTE_MATERIAS = "docente_materias"
    ESTUDIANTE_MATERIAS = "estudiante_materias"
    
    # Investigación
    LINEAS_INVESTIGACION = "lineas_investigacion"
    SUBLINEAS_INVESTIGACION = "sublineas_investigacion"
    AREAS_TEMATICAS = "areas_tematicas"
    
    # Eventos y proyectos
    EVENTOS = "eventos"  # Ferias/Convocatorias
    PROYECTOS = "proyectos"
    
    # Otros
    SECTORES = "sectores"
    ASISTENCIAS = "asistencias"
    
# ==================== AUTH (Firebase Authentication) ====================
from firebase_admin import auth
firebase_auth = auth
