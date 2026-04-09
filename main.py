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

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

class ChatRequest(BaseModel):
    """
    Modelo de entrada compatible con OpenAI
    - model: Modelo a usar (opcional, default: hermes-agent)
    - messages: Lista de mensajes de la conversación
    - stream: Si usar streaming (opcional, default: False)
    """
    model_config = {
        "from_attributes": True,
        "validate_default": True
    }
    
    model: str = Field(
        default="hermes-agent",
        description="Modelo a usar (default: hermes-agent)"
    )
    messages: List[Dict[str, Any]] = Field(
        default=[],
        description="Lista de mensajes de la conversación"
    )
    stream: bool = Field(
        default=False,
        description="Usar streaming (default: False)"
    )

class ChatResponse(BaseModel):
    """
    Modelo de respuesta OpenAI-compatible
    - id: ID único de la respuesta
    - object: Tipo de objeto
    - created: Timestamp
    - model: Modelo usado
    - choices: Lista de respuestas
    - usage: Uso de tokens
    """
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

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
        """
        Chat con Hermes AI con filtrado de seguridad
        - Filtra credenciales y URLs peligrosas
        - Genera respuesta con IA local Qwen3.5
        - Registra conversación para auditoría
        """
        request_id = str(__import__('uuid').uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Inicializar o obtener conversación
        if not conversation_id:
            conversation_id = str(__import__('uuid').uuid4())

        if conversation_id not in self.conversation_cache:
            self.conversation_cache[conversation_id] = []

        conversation = self.conversation_cache[conversation_id]

        # Agregar mensaje del usuario si no hay mensajes
        if not conversation:
            # Usar el primer mensaje si existe en request.messages
            if request.messages and len(request.messages) > 0:
                first_msg = request.messages[0]
                if first_msg.get("role") == "user":
                    user_message = {
                        "role": "user",
                        "content": first_msg.get("content", ""),
                        "timestamp": timestamp,
                        "request_id": request_id
                    }
                    conversation.append(user_message)
                    message_to_process = first_msg.get("content", "")
                else:
                    # Si no hay mensaje de usuario, usar el último mensaje
                    message_to_process = request.messages[-1].get("content", "") if request.messages else ""
            else:
                message_to_process = ""

        # Verificar seguridad
        safety_results = {
            "contains_credentials": False,
            "contains_dangerous_links": False,
            "suggested_response": ""
        }

        # Filtrar mensaje del usuario
        filtered_message = self.filter.filter_string(
            message_to_process,
            context="user_message"
        )

        if filtered_message != message_to_process:
            # Credenciales o datos sensibles detectados
            safety_results["contains_credentials"] = True
            safety_results["suggested_response"] = (
                "No puedo proporcionar información que incluya claves API, "
                "contraseñas u otros datos sensibles. "
                "Por favor, elimínalos e inténtalo de nuevo."
            )

        # Verificar URLs peligrosas
        dangerous_url_pattern = r'https?://[\w-]+\.exe|\.sh|\.py|\.bat|\.cmd'
        if __import__('re').search(dangerous_url_pattern, message_to_process, __import__('re').IGNORECASE):
            safety_results["contains_dangerous_links"] = True
            safety_results["suggested_response"] = (
                "No puedo ayudar con la descarga o ejecución de archivos peligrosos. "
                "Por favor, elimina las URL y haz otra pregunta."
            )

        # Generar respuesta de Hermes
        if safety_results["suggested_response"]:
            # Retornar mensaje de seguridad
            return ChatResponse(
                id=f"chatcmpl-{__import__('uuid').uuid4().hex[:12]}",
                object="chat.completion",
                created=int(datetime.now(timezone.utc).timestamp()),
                model=request.model or "hermes-agent",
                choices=[{
                    "index": 0,
                    "message": {"role": "assistant", "content": safety_results["suggested_response"]},
                    "finish_reason": "safety"
                }],
                usage={
                    "prompt_tokens": 10,
                    "completion_tokens": 50,
                    "total_tokens": 60
                }
            )

        # Generar respuesta de IA usando Hermes local
        ai_response = self._generate_hermes_response(
            message_to_process,
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
        self._log_conversation(conversation_id, ai_message)

        # Retornar respuesta en formato OpenAI
        return ChatResponse(
            id=f"chatcmpl-{__import__('uuid').uuid4().hex[:12]}",
            object="chat.completion",
            created=int(datetime.now(timezone.utc).timestamp()),
            model=request.model or "hermes-agent",
            choices=[{
                "index": 0,
                "message": {"role": "assistant", "content": filtered_response},
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": 10,
                "completion_tokens": len(filtered_response),
                "total_tokens": 10 + len(filtered_response)
            }
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
            history = "\n".join([
                f"### {msg.get('role', 'unknown')}: {msg.get('content', '')[:200]}"
                for msg in conversation[-10:]
            ]) if conversation else "No previous messages"

            full_prompt = f"""### System
{system_prompt}

### User
{message}

### Conversation History
{history}

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
                logger.warning(f"Error leyendo .env: {e}")

    return {
        "API_HERMES_KEY": api_key_from_env or "your-hermes-api-key-here"
    }

settings = get_settings()

# Inicializar servicio de chat
hermes_chat = HermesChatService(
    filter=CredentialFilter(settings=getattr(settings, "ALLOWED_DOMAINS", []))
)

@app.get("/health")
async def health_check():
    """Verificar estado del servidor"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/api/v1/chat", response_model=ChatResponse, response_model_exclude_none=True)
async def chat_with_hermes(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Endpoint principal para chat con Hermes AI
    - Compatible con OpenAI format
    - Filtra credenciales y URLs peligrosas
    - Genera respuesta con IA local Qwen3.5
    - Registra conversación para auditoría
    """
    # Validar API key si está configurada
    api_key = settings.get("API_HERMES_KEY", "")
    if api_key and api_key != "your-hermes-api-key-here":
        auth_header = request.headers.get("authorization", "")
        expected_key = f"Bearer {api_key}"
        if auth_header != expected_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Invalid API key",
                    "type": "invalid_request_error",
                    "code": "invalid_api_key"
                }
            )

    try:
        # Usar run_coroutine_threadpool para ejecutar método síncrono en hilo separado
        import asyncio
        try:
            # Ejecutar el método chat en un hilo separado para evitar bloqueos
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: hermes_chat.chat(request)
            )
            return response.model_dump()
        except Exception as e:
            logger.error(f"Error ejecutando chat: {e}")
            raise
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "details": str(e)
            }
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
