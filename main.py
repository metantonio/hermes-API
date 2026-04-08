#!/usr/bin/env python3
"""
Hermes Web Data API
Production-ready FastAPI server with security filtering
"""

import sys
import os
from pathlib import Path

# Agregar ~/.hermes al path para importar el wrapper
HERMES_HOME = Path(os.path.expanduser("~/.hermes"))
if str(HERMES_HOME) not in sys.path:
    sys.path.insert(0, str(HERMES_HOME))

# Importar el wrapper llama.cpp
try:
    from hermes_llama_wrapper import intercept_llm_call
    print(f"✅ Hermes Llama Wrapper importado desde: {HERMES_HOME}/hermes_llama_wrapper.py")
except ImportError as e:
    print(f"⚠️ Warning: Could not import hermes_llama_wrapper: {e}")
    print("  Usando respuestas simuladas como fallback")

# ============================================================================
# Modelos de datos
# ============================================================================

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    timestamp: str
    safety_checks: Dict[str, Any]

# ============================================================================
# Servidor FastAPI
# ============================================================================

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hermes.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionar ciclo de vida del servidor"""
    logger.info("🚀 Iniciando Hermes Web Data API...")
    yield
    logger.info("👋 Deteniendo Hermes Web Data API...")

app = FastAPI(
    title="Hermes Web Data API",
    description="API para extracción de datos web con seguridad",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Servicios
# ============================================================================

from security.filtering import CredentialFilter, DataExtractor

class HermesChatService:
    """Servicio para chat con Hermes AI"""
    
    def __init__(self, filter: CredentialFilter):
        self.filter = filter
        self.conversation_cache: Dict[str, List[dict]] = {}
    
    def chat(
        self,
        request: ChatRequest,
        conversation_id: Optional[str] = None
    ) -> ChatResponse:
        """Chat con Hermes AI con filtrado de seguridad"""
        request_id = str(__import__('uuid').uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Inicializar o obtener conversación
        if not conversation_id:
            conversation_id = str(__import__('uuid').uuid4())
        
        if conversation_id not in self.conversation_cache:
            self.conversation_cache[conversation_id] = []
        
        conversation = self.conversation_cache[conversation_id]
        
        # Agregar mensaje del usuario
        user_message = {
            "role": "user",
            "content": request.message,
            "timestamp": timestamp,
            "request_id": request_id
        }
        conversation.append(user_message)
        
        # Verificar seguridad
        safety_results = {
            "contains_credentials": False,
            "contains_dangerous_links": False,
            "suggested_response": ""
        }
        
        # Filtrar mensaje del usuario
        filtered_message = self.filter.filter_string(
            request.message,
            context="user_message"
        )
        
        if filtered_message != request.message:
            # Credenciales o datos sensibles detectados
            safety_results["contains_credentials"] = True
            safety_results["suggested_response"] = (
                "No puedo proporcionar información que incluya claves API, "
                "contraseñas u otros datos sensibles. "
                "Por favor, elimínalos e inténtalo de nuevo."
            )
        
        # Verificar URLs peligrosas
        dangerous_url_pattern = r'https?://[\w-]+\.exe|\.sh|\.py|\.bat|\.cmd'
        if __import__('re').search(dangerous_url_pattern, request.message, __import__('re').IGNORECASE):
            safety_results["contains_dangerous_links"] = True
            safety_results["suggested_response"] = (
                "No puedo ayudar con la descarga o ejecución de archivos peligrosos. "
                "Por favor, elimina las URL y haz otra pregunta."
            )
        
        # Generar respuesta de Hermes
        if safety_results["suggested_response"]:
            # Retornar mensaje de seguridad
            return ChatResponse(
                message=safety_results["suggested_response"],
                conversation_id=conversation_id,
                timestamp=timestamp,
                safety_checks=safety_results
            )
        
        # Generar respuesta de IA usando Hermes local
        ai_response = self._generate_hermes_response(
            request.message,
            conversation
        )
        
        # Filtrar respuesta de IA
        filtered_response = self.filter.filter_string(
            ai_response,
            context="ai_response"
        )
        
        # Agregar a historial de conversación
        ai_message = {
            "role": "assistant",
            "content": filtered_response,
            "timestamp": timestamp,
            "request_id": request_id,
            "safety_filtered": True
        }
        conversation.append(ai_message)
        
        # Registrar conversación para auditoría
        self._log_conversation(conversation_id, user_message, ai_message)
        
        return ChatResponse(
            message=filtered_response,
            conversation_id=conversation_id,
            timestamp=timestamp,
            safety_checks=safety_results
        )
    
    def _generate_hermes_response(
        self,
        message: str,
        conversation: List[dict]
    ) -> str:
        """
        Generar respuesta de Hermes AI usando Qwen3.5 local.
        Integra con ~/.hermes/venv/hermes_llama_wrapper.py
        """
        try:
            # Construir prompt para el modelo Qwen3.5
            system_prompt = """Eres Hermes AI, un asistente inteligente especializado en:
- Extracción de datos web
- Investigación y búsqueda de información
- Análisis de datos
- Respuestas concisas y precisas

Responde de manera útil, precisa y segura. Mantén un tono profesional."""
            
            # Construir mensaje completo con historial de conversación
            full_prompt = f"""### System
{system_prompt}

### User
{message}

### Conversation History
{conversation[-5:] if conversation else 'No previous messages'}

### Assistant
"""
            
            # Llamar al modelo local
            response = intercept_llm_call(
                prompt=full_prompt,
                temperature=0.7,
                max_tokens=1024
            )
            return response.strip()
            
        except Exception as e:
            # Manejar errores gracefulmente
            logger.error(f"Error en Hermes AI: {e}")
            return "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo más tarde."
    
    def _log_conversation(
        self,
        conversation_id: str,
        user_message: dict,
        ai_message: dict
    ):
        """Registrar conversación para auditoría"""
        try:
            # Log para auditoría
            logger.info(f"Conversación registrada: ID={conversation_id}")
        except Exception as e:
            # No fallar la funcionalidad principal
            logger.warning(f"Registro de conversación falló: {e}")

# ============================================================================
# Configuración y servicios
# ============================================================================

def get_settings():
    """Obtener configuración"""
    # Cargar API_HERMES_KEY desde el archivo .env si no está en el entorno
    api_key_from_env = os.getenv("API_HERMES_KEY")
    if not api_key_from_env or api_key_from_env in ["your-hermes-api-key-here", ""]:
        # Intentar cargar desde archivo .env
        env_file = Path(os.path.expanduser("~/.hermes/api/.env"))
        if env_file.exists():
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        if line.startswith("API_HERMES_KEY="):
                            # Limpiar la línea y extraer el valor
                            value = line.split("=", 1)[1].strip()
                            # Eliminar comillas si existen
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            # Verificar que no sea un valor por defecto
                            if value and value not in ["change-me-local-dev-work", ""]:
                                api_key_from_env = value
                                break
            except Exception as e:
                logger.warning(f"Error leyendo archivo .env: {e}")
    
    class Settings:
        AUDIT_ENABLED = False
        AUDIT_ENDPOINT = ""
        API_HERMES_KEY = api_key_from_env or os.getenv("API_HERMES_KEY", "your-hermes-api-key-here")
    return Settings()

# Inicializar servicios
settings = get_settings()
credential_filter = CredentialFilter(settings)
data_extractor = DataExtractor()
hermes_chat = HermesChatService(credential_filter)

# Rutas principales
@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "Hermes Web Data API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Verificar estado del servidor"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/api/v1/chat")
async def chat_with_hermes(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Endpoint principal para chat con Hermes AI
    - Filtra credenciales y URLs peligrosas
    - Genera respuesta con IA local Qwen3.5
    - Registra conversación para auditoría
    """
    # Validar API key si está configurada
    if settings.API_HERMES_KEY and settings.API_HERMES_KEY != "your-hermes-api-key-here":
        auth_header = request.headers.get("authorization", "")
        expected_key = f"Bearer {settings.API_HERMES_KEY}"
        if auth_header != expected_key:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API key", "type": "invalid_request_error", "code": "invalid_api_key"}
            )
    
    try:
        response = hermes_chat.chat(request)
        return response.model_dump()
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "details": str(e)}
        )

@app.post("/api/v1/extract")
async def extract_data(url: str, max_pages: int = 5):
    """
    Extraer datos de una URL específica
    - Filtra credenciales en el contenido
    - Detecta enlaces peligrosos
    - Limita profundidad de navegación
    """
    try:
        result = data_extractor.extract(url, max_pages=max_pages)
        return result
    except Exception as e:
        logger.error(f"Error en extracción: {e}")
        raise

# ============================================================================
# Inicialización
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    import getpass
    
    # Leer configuración de entorno
    HERMES_HOME = Path(os.path.expanduser("~/.hermes"))
    config_file = HERMES_HOME / ".hermes" / "config.yaml"
    
    if config_file.exists():
        logger.info(f"Configuración encontrada: {config_file}")
    else:
        logger.warning("Configuración no encontrada, usando defaults")
    
    # Iniciar servidor
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
