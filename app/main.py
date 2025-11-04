# app/main.py

import os
import sys
import logging
import datetime
from contextlib import asynccontextmanager
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Cargar variables de entorno primero
load_dotenv()

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Intentar cargar módulos avanzados (opcionales)
ADVANCED_FEATURES = False
try:
    from app.core.config import settings
    from app.core.rate_limiter import limiter, rate_limit_exceeded_handler
    from app.exceptions.handlers import register_exception_handlers
    from slowapi.errors import RateLimitExceeded
    ADVANCED_FEATURES = True
    
    # Actualizar nivel de logging si settings está disponible
    logging.getLogger().setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
    logger.info("✅ Características avanzadas cargadas (rate limiting, handlers)")
except ImportError as e:
    logger.warning(f"⚠️ Características avanzadas no disponibles: {e}")

# Validar credenciales de Firebase
firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
if not firebase_credentials_path:
    logger.error("FIREBASE_CREDENTIALS_PATH no está configurado en .env")
    sys.exit(1)

if not os.path.exists(firebase_credentials_path):
    logger.error(f"Archivo de credenciales no encontrado en: {firebase_credentials_path}")
    logger.info(f"Directorio actual: {os.getcwd()}")
    logger.info(f"Archivos en directorio: {os.listdir('.')}")
    sys.exit(1)

logger.info(f"Credenciales de Firebase encontradas en: {firebase_credentials_path}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando ExpoSoftware API")
    
    # === INICIALIZACIÓN DE FIREBASE ===
    try:
        # Intentar usar firebase_client si existe
        try:
            from app.core.firebase import firebase_client
            firebase_client.initialize()
            logger.info("✅ Firebase inicializado vía firebase_client")
        except ImportError:
            # Fallback: inicialización directa
            import firebase_admin
            from firebase_admin import credentials
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_credentials_path)
                firebase_admin.initialize_app(cred)
                logger.info("✅ Firebase inicializado directamente")
    except Exception as e:
        logger.error(f"❌ Error CRÍTICO al inicializar Firebase: {e}")
        raise
    
    # === REGISTRO DE ROUTERS ===
    routers = []
    
    # Intentar importar router API centralizado primero
    router_centralizado_cargado = False
    try:
        from app.routers import router as api_router
        routers.append(("API Principal", api_router, ""))
        router_centralizado_cargado = True
        logger.info("✅ Router API centralizado cargado")
    except ImportError as e:
        logger.info(f"ℹ️ Router centralizado no disponible: {e}")
    
    # Si no hay router centralizado, cargar routers individuales
    if not router_centralizado_cargado:
        logger.info("📦 Cargando routers individuales...")
        
        # Router de reportes
        try:
            from app.routers.report_router import router as report_router
            routers.append(("Reportes", report_router, "/api/v1"))
            logger.info("✅ Report router cargado")
        except ImportError as e:
            logger.warning(f"⚠️ No se pudo cargar report_router: {e}")
        
        # Router de certificados admin
        try:
            from app.routers.admin_certificate_router import router as admin_certificate_router
            routers.append(("Certificados Admin", admin_certificate_router, ""))
            logger.info("✅ Admin Certificate router cargado")
        except ImportError as e:
            logger.warning(f"⚠️ No se pudo cargar admin_certificate_router: {e}")
            
            # Fallback: router mock inline
            fallback_router = APIRouter(
                prefix="/admin/reportes/certificados",
                tags=["Certificados"]
            )
            
            @fallback_router.get("/")
            async def mock_certificates_list():
                return {
                    "status": "development",
                    "message": "Módulo de certificados en desarrollo",
                    "certificates": []
                }
            
            @fallback_router.post("/generar-por-proyecto")
            async def mock_generate_certificates():
                return {
                    "status": "info",
                    "message": "Módulo de certificados en desarrollo"
                }
            
            routers.append(("Certificados Fallback", fallback_router, ""))
            logger.info("✅ Certificate Fallback router creado")
    
    # Registrar todos los routers
    for name, router, prefix in routers:
        try:
            app.include_router(router, prefix=prefix)
            prefix_display = prefix if prefix else "/"
            logger.info(f"✅ {name} router registrado en '{prefix_display}'")
        except Exception as e:
            logger.error(f"❌ Error registrando {name} router: {e}")
    
    # Listar rutas registradas
    try:
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        logger.info(f"📋 RUTAS REGISTRADAS ({len(routes)}): {routes}")
    except Exception as e:
        logger.error(f"Error al listar rutas: {e}")
    
    yield
    
    # === CIERRE ===
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

# Configurar características avanzadas si están disponibles
if ADVANCED_FEATURES:
    try:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
        register_exception_handlers(app)
        logger.info("✅ Rate limiting y exception handlers configurados")
    except Exception as e:
        logger.warning(f"⚠️ No se pudieron configurar características avanzadas: {e}")

# Endpoints básicos
@app.get("/", tags=["Health"])
async def root():
    return {
        "mensaje": "API ExpoSoftware",
        "version": "1.0.0",
        "documentacion": "/docs",
        "estado": "operativo"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de health check con verificación de Firebase"""
    firebase_status = "disconnected"
    
    try:
        # Intentar verificar con firebase_client
        try:
            from app.core.firebase import firebase_client
            firebase_status = "connected" if getattr(firebase_client, '_app', None) else "disconnected"
        except ImportError:
            # Fallback: verificar con firebase_admin directamente
            import firebase_admin
            firebase_status = "connected" if firebase_admin._apps else "disconnected"
    except Exception as e:
        logger.error(f"Error verificando estado de Firebase: {e}")
    
    return {
        "status": "healthy",
        "service": "ExpoSoftware API",
        "firebase": firebase_status,
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