# app/main.py

import os
import sys
import logging
import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Validar y obtener ruta de credenciales
firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
if not firebase_credentials_path:
    logger.error("FIREBASE_CREDENTIALS_PATH no está configurado en .env")
    sys.exit(1)

# Verificar que el archivo existe
if not os.path.exists(firebase_credentials_path):
    logger.error(f"Archivo de credenciales no encontrado en: {firebase_credentials_path}")
    logger.info(f"Directorio actual: {os.getcwd()}")
    logger.info(f"Archivos en directorio: {os.listdir('.')}")
    sys.exit(1)

logger.info(f"Credenciales de Firebase encontradas en: {firebase_credentials_path}")

# Inicializar Firebase
try:
    import firebase_admin
    from firebase_admin import credentials
    
    cred = credentials.Certificate(firebase_credentials_path)
    firebase_admin.initialize_app(cred)
    logger.info("✅ Firebase inicializado correctamente")
    
except Exception as e:
    logger.error(f"❌ Error inicializando Firebase: {str(e)}")
    sys.exit(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando ExpoSoftware API")
    
    # Importar y registrar routers después de que Firebase esté inicializado
    routers = []
    
    # Router de reportes
    try:
        from app.routers.report_router import router as report_router
        routers.append(("Reportes", report_router, "/api/v1"))
        logger.info("✅ Report router cargado")
    except ImportError as e:
        logger.warning(f"⚠️ No se pudo cargar report_router: {str(e)}")
    
    # Router de certificados admin
    try:
        from app.routers.admin_certificate_router import router as admin_certificate_router
        routers.append(("Certificados Admin", admin_certificate_router, ""))
        logger.info("✅ Admin Certificate router cargado")
    except ImportError as e:
        logger.error(f"❌ Error cargando admin_certificate_router: {str(e)}")
        # Si hay error, cargar una versión mock para desarrollo
        try:
            from app.routers.certificate_mock_router import router as mock_certificate_router
            routers.append(("Certificados Mock", mock_certificate_router, "/api/v1"))
            logger.info("✅ Certificate Mock router cargado como fallback")
        except ImportError:
            logger.warning("⚠️ No hay fallback disponible para certificados")
    
    # Registrar todos los routers
    for name, router, prefix in routers:
        try:
            app.include_router(router, prefix=prefix)
            logger.info(f"✅ {name} router registrado en {prefix}")
        except Exception as e:
            logger.error(f"❌ Error registrando {name} router: {str(e)}")
    
    yield
    logger.info("🛑 Cerrando ExpoSoftware API")

# Crear aplicación FastAPI
app = FastAPI(
    title="API ExpoSoftware",
    description="Sistema de gestión para la Feria Tecnológica ExpoSoftware",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints básicos
@app.get("/")
async def root():
    return {
        "mensaje": "API ExpoSoftware",
        "version": "1.0.0",
        "documentacion": "/docs",
        "estado": "operativo"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ExpoSoftware API", 
        "firebase": "connected",
        "timestamp": datetime.datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🌐 Servidor iniciando en http://{host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True
    )