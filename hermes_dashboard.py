#!/usr/bin/env python3
"""
Hermes Dashboard UI
Interfaz web en Python para monitorear y usar el API de Hermes

Características:
- Endpoint /api/v1/chat interactivo
- Mostrar profiles, skills, sessions, work trees
- Información del sistema Hermes
"""

import streamlit as st
import json
import os
import sqlite3
import urllib.request
import urllib.error
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import hashlib

# Agregar ~/.hermes al path para encontrar hermes_wrapper
hermes_dir = Path.home() / ".hermes"
if hermes_dir.exists() and str(hermes_dir) not in sys.path:
    sys.path.insert(0, str(hermes_dir))

from hermes_wrapper import HermesAgent, get_hermes_info

# ============================================================================
# Configuración de página
# ============================================================================

st.set_page_config(
    page_title="Hermes Dashboard",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-title {font-size: 2.5rem; font-weight: bold; color: #1f77b4;}
    .section-title {font-size: 1.5rem; font-weight: bold; margin-top: 2rem;}
    .api-response {background-color: #f0f7ff; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;}
    .status-ok {color: #28a745; font-weight: bold;}
    .status-error {color: #dc3545; font-weight: bold;}
    .endpoint-info {background-color: #f8f9fa; border-left: 4px solid #17a2b8; padding: 1rem; margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Funciones de utilidad
# ============================================================================

def get_hermes_info():
    """Obtener información básica del sistema Hermes"""
    hermes_home = Path.home() / ".hermes"
    
    info = {
        "version": "1.0.0",
        "home": str(hermes_home),
        "config_file": hermes_home / "config.yaml",
        "config_exists": (hermes_home / "config.yaml").exists(),
        "gateway_running": False,
        "gateway_pid": None
    }
    
    # Verificar estado del gateway
    if (hermes_home / "gateway.pid").exists():
        try:
            with open(hermes_home / "gateway.pid", "r") as f:
                pid = f.read().strip()
                if pid:
                    import subprocess
                    result = subprocess.run(["ps", "aux", "|", "grep", "|", pid], 
                                           capture_output=True, text=True)
                    info["gateway_running"] = bool(result.returncode == 0 and len(result.stdout) > 0)
                    info["gateway_pid"] = pid
        except:
            pass
    
    return info

def get_profiles():
    """Obtener lista de perfiles"""
    profiles_path = Path.home() / ".hermes" / "profiles"
    profiles = []
    
    if profiles_path.exists():
        for item in profiles_path.iterdir():
            if item.is_dir():
                profile_info = {
                    "name": item.name,
                    "path": str(item),
                    "created": item.stat().st_ctime,
                    "modified": item.stat().st_mtime
                }
                
                # Intentar leer información adicional
                try:
                    with open(item / "info.json", "r") as f:
                        profile_info["metadata"] = json.load(f)
                except:
                    pass
                
                profiles.append(profile_info)
    
    return profiles

def get_skills():
    """Obtener lista de skills"""
    skills_path = Path.home() / ".hermes" / "skills"
    skills = []
    
    if skills_path.exists():
        for item in skills_path.iterdir():
            if item.is_dir():
                skill_info = {
                    "name": item.name,
                    "path": str(item),
                    "category": item.name.split("-")[0] if "-" in item.name else "misc",
                    "has_bundled": (item / ".bundled_manifest").exists()
                }
                skills.append(skill_info)
    
    return skills

def get_sessions():
    """Obtener estadísticas de sesiones"""
    sessions_path = Path.home() / ".hermes" / "sessions"
    sessions = []
    
    if sessions_path.exists():
        for item in sessions_path.glob("*.json"):
            filename = item.name
            date_part = filename.split("_")[0] if "_" in filename else "unknown"
            
            session_info = {
                "filename": filename,
                "size_bytes": item.stat().st_size,
                "created": item.stat().st_ctime,
                "date": date_part[:10] if date_part != "unknown" else "unknown"
            }
            sessions.append(session_info)
    
    return sessions

def get_work_trees():
    """Obtener información de work trees"""
    work_trees = []
    
    profiles_path = Path.home() / ".hermes" / "profiles"
    if profiles_path.exists():
        for item in profiles_path.iterdir():
            if item.is_dir():
                work_path = item / "work"
                if work_path.exists():
                    work_trees.append({
                        "profile": item.name,
                        "path": str(work_path),
                        "items": len(list(work_path.iterdir()))
                    })
    
    return work_trees

def call_api_endpoint(endpoint, data=None, method="GET", api_key=None):
    """
    Llamar a endpoint del API de Hermes en puerto 8642
    
    Parámetros:
        endpoint: Endpoint del API (ej: /health, /v1/models)
        data: Datos JSON para POST/PUT
        method: Método HTTP (GET, POST, etc.)
        api_key: API key para autenticación (si None, usa la del .env)
    
    Retorna:
        Dict con el resultado
    """
    # URL base del API (puerto 8642 - Hermes API)
    base_url = "http://127.0.0.1:8642"
    url = f"{base_url}{endpoint}"
    
    headers = {}
    if data and method in ["POST", "PUT", "PATCH"]:
        headers["Content-Type"] = "application/json"
    
    # Obtener API key por defecto desde ~/.hermes/api/.env
    if not api_key:
        default_key = get_default_api_key()
        if default_key:
            api_key = default_key
    
    # Autenticación si se proporciona API key
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        request = urllib.request.Request(url, 
                                         data=json.dumps(data).encode() if data else None, 
                                         headers=headers, 
                                         method=method)
        
        with urllib.request.urlopen(request, timeout=10) as response:
            result = response.read().decode()
            return {
                "success": True, 
                "data": result, 
                "status": response.status,
                "url": url
            }
    except urllib.error.URLError as e:
        return {
            "success": False, 
            "error": str(e.reason) if hasattr(e, 'reason') else str(e),
            "url": url
        }
    except Exception as e:
        return {
            "success": False, 
            "error": str(e),
            "url": url
        }

def get_default_api_key():
    """
    Leer la API key por defecto desde ~/hermes/api/.env
    
    Retorna:
        API key o None si no se encuentra
    """
    env_path = Path("/home/antonio/hermes/api/.env")
    
    if not env_path.exists():
        return None
    
    try:
        with open(env_path, "r") as f:
            content = f.read()
        
        # Buscar la variable API_HERMES_KEY
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("API_HERMES_KEY="):
                # Extraer el valor (todo después del =)
                api_key = line.split("=", 1)[1].strip()
                # Quitar comillas si las hay
                if api_key.startswith('"') and api_key.endswith('"'):
                    api_key = api_key[1:-1]
                elif api_key.startswith("'") and api_key.endswith("'"):
                    api_key = api_key[1:-1]
                return api_key if api_key else None
    except Exception as e:
        print(f"Error leyendo API key: {e}")
    
    return None


def chat_with_hermes(message, api_key=None):
    """
    Chat interactivo con Hermes AI
    
    Parámetros:
        message: El mensaje a enviar a Hermes
        api_key: API key para autenticación (si None, usa la del .env)
    
    Retorna:
        Dict con el resultado del chat
    """
    if not message.strip():
        return None
    
    try:
        # Construir URL del endpoint (puerto 8642)
        endpoint = f"http://127.0.0.1:8642/v1/chat/completions"
        
        payload = {
            "model": "hermes-agent",
            "messages": [{"role": "user", "content": message}]
        }
        
        # Obtener API key por defecto desde ~/.hermes/api/.env
        if not api_key:
            default_key = get_default_api_key()
            if default_key:
                api_key = default_key
            else:
                # Fallback a variable de entorno o key por defecto
                api_key = os.environ.get("API_SERVER_KEY", "sk-her...2026")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(request, timeout=30) as response:
            result_data = response.read().decode()
            return {
                "success": True, 
                "data": result_data, 
                "status": response.status
            }
            
    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": getattr(e, 'reason', str(e)) if hasattr(e, 'reason') else str(e)
        }
    except Exception as e:
        return {
            "success": False, 
            "error": str(e)
        }

# ============================================================================
# Gestión de respuestas (RESPONSES)
# ============================================================================

RESPONSES_DB_PATH = Path.home() / ".hermes" / "responses" / "responses.db"

def init_responses_db():
    """Inicializar base de datos SQLite para respuestas"""
    RESPONSES_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(RESPONSES_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id TEXT PRIMARY KEY,
        model TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending',
        metadata TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def save_response(response_data, model, metadata=None):
    """Guardar una respuesta en la base de datos"""
    init_responses_db()
    
    # Generar ID único si no se proporciona
    if not response_data.get("id"):
        timestamp = datetime.now().isoformat()
        unique_id = hashlib.md5(f"{timestamp}{random.randint(1000, 9999)}".encode()).hexdigest()[:12]
        response_data["id"] = unique_id
    
    conn = sqlite3.connect(RESPONSES_DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT OR REPLACE INTO responses (id, model, metadata)
        VALUES (?, ?, ?)
        """, (
            response_data.get("id"),
            model,
            json.dumps(metadata) if metadata else None
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def get_response(id):
    """Obtener una respuesta por ID"""
    init_responses_db()
    
    conn = sqlite3.connect(RESPONSES_DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, model, status, created_at, metadata FROM responses WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        if row:
            result = {
                "id": row[0],
                "model": row[1],
                "status": row[2],
                "created_at": row[3],
                "metadata": json.loads(row[4]) if row[4] else None
            }
            return result
        return None
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def update_response_status(id, status, metadata=None):
    """Actualizar el estado de una respuesta"""
    init_responses_db()
    
    conn = sqlite3.connect(RESPONSES_DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        UPDATE responses 
        SET status = ?, metadata = ? 
        WHERE id = ?
        """, (status, json.dumps(metadata) if metadata else None, id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def get_all_responses():
    """Obtener todas las respuestas"""
    init_responses_db()
    
    conn = sqlite3.connect(RESPONSES_DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        SELECT id, model, status, created_at, metadata 
        FROM responses 
        ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        responses = []
        
        for row in rows:
            response = {
                "id": row[0],
                "model": row[1],
                "status": row[2],
                "created_at": row[3],
                "metadata": json.loads(row[4]) if row[4] else None
            }
            responses.append(response)
        
        return responses
    except Exception as e:
        return []
    finally:
        conn.close()

# ============================================================================
# Obtener modelos del API
# ============================================================================

def get_models_from_api():
    """Obtener lista de modelos disponibles en el API"""
    result = call_api_endpoint("/v1/models", api_key=None)
    
    if result.get("success"):
        try:
            data = json.loads(result["data"])
            return data
        except:
            return None
    return result

# ============================================================================
# Sidebar - Información del sistema
# ============================================================================

with st.sidebar:
    st.markdown("### 🦉 Hermes Dashboard")
    st.markdown(f"**Versión:** 1.0.0")
    
    # Estado del sistema
    info = get_hermes_info()
    
    st.markdown("#### 📊 Estado del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        status = "✅" if info["gateway_running"] else "⚪"
        st.write(f"**Gateway:** {status}")
        if info["gateway_pid"]:
            st.write(f"**PID:** `{info['gateway_pid']}`")
    
    with col2:
        st.write(f"**API:** {status if info['gateway_running'] else '❌'}")
        if not info["gateway_running"]:
            st.caption("El gateway API no está activo")
    
    st.markdown("---")
    
    # Configurar API key
    st.markdown("#### 🔑 API Configuration")
    api_key = st.text_input(
        "API_HERMES_KEY",
        type="password",
        help="Ingresa tu API key de Hermes"
    )
    
    st.markdown("---")
    
    # Mostrar información del sistema
    st.markdown("#### 📁 Información del Sistema")
    
    st.write(f"**Hermes Home:** `{info['home']}`")
    st.write(f"**Config:** {info['config_exists']}")
    
    if info["config_exists"]:
        st.code("""
config.yaml:
  model_path: Qwen3.5-9B-Q4_K_M
  n_ctx: 8192
        """, language="yaml")
    
    st.markdown("---")
    
    # Contadores rápidos
    st.markdown("#### 📈 Contadores")
    
    profiles = get_profiles()
    skills = get_skills()
    sessions = get_sessions()
    
    st.write(f"**Profiles:** {len(profiles)}")
    st.write(f"**Skills:** {len(skills)}")
    st.write(f"**Sessions:** {len(sessions)}")

# ============================================================================
# Header
# ============================================================================

st.markdown('<p class="main-title">🦉 Hermes Dashboard UI</p>', unsafe_allow_html=True)
st.markdown("Interfaz de gestión para el API de Hermes Web Data")

# ============================================================================
# Sección 1: API Chat
# ============================================================================

st.markdown('<p class="section-title">🤖 Chat con Hermes AI</p>', unsafe_allow_html=True)

message = st.text_area(
    "Ingresa tu mensaje:",
    height=150,
    placeholder="Escribe tu pregunta o solicitud aquí...",
    key="chat_input"
)

if st.button("📤 Enviar Mensaje", type="primary"):
    if message.strip():
        with st.spinner("Procesando con Hermes AI..."):
            result = chat_with_hermes(message, api_key=api_key if api_key else None)
            
            if result and result.get("success"):
                try:
                    data = json.loads(result["data"])
                    st.success("✅ Respuesta de Hermes:")
                    st.markdown(f"```{data.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}```")
                except:
                    st.success("✅ Respuesta de Hermes:")
                    st.markdown(result["data"])
                
                # Guardar conversación
                timestamp = datetime.now().isoformat()
                conversation_file = Path.home() / ".hermes" / "chat_history" / f"chat_{timestamp.replace(':', '-')}.json"
                chat_history_path = conversation_file.parent
                chat_history_path.mkdir(parents=True, exist_ok=True)
                
                try:
                    history = []
                    if conversation_file.exists():
                        with open(conversation_file, "r") as f:
                            history = json.load(f)
                    
                    history.append({
                        "timestamp": timestamp,
                        "user": message.strip(),
                        "assistant": result.get("data", "")
                    })
                    
                    with open(conversation_file, "w") as f:
                        json.dump(history, f, indent=2)
                except Exception as e:
                    st.error(f"Error guardando historial: {e}")
            else:
                error = result.get("error", "Unknown error") if result else "Error desconocido"
                st.error(f"❌ Error: {error}")

# ============================================================================
# Sección 2: API Testing
# ============================================================================

st.markdown('<p class="section-title">🔌 Testear Endpoints API</p>', unsafe_allow_html=True)

# Test del endpoint /health
with st.expander("🏥 Testear /health (Health Check)", expanded=True):
    health_result = call_api_endpoint("/health", api_key=api_key if api_key else None)
    
    if health_result.get("success"):
        health_data = json.loads(health_result["data"])
        status_icon = "✅" if health_data.get("status") == "ok" else "❌"
        
        st.markdown(f"**{status_icon} Status:** {health_data.get('status', 'unknown')}")
        st.markdown(f"**API:** {health_data.get('platform', 'unknown')}")
        
        if health_result.get("status") == "ok":
            st.success("El API está funcionando correctamente")
    else:
        st.error(f"Error conectando al API: {health_result.get('error', 'Unknown error')}")
        st.info("📌 Nota: El API debe estar corriendo en puerto 8642")

# Test del endpoint POST /v1/responses
with st.expander("💾 POST /v1/responses (Guardar Respuesta)", expanded=False):
    response_id = st.text_input(
        "ID de la respuesta:",
        help="Generar automáticamente o ingresar un ID personalizado"
    )
    
    model_name = st.text_input(
        "Modelo:",
        value="hermes-agent",
        help="Nombre del modelo usado"
    )
    
    metadata = st.text_area(
        "Metadata (JSON)",
        help="Información adicional sobre la respuesta"
    )
    
    if st.button("💾 Guardar Respuesta", type="secondary"):
        if response_id.strip() or not response_id.strip():
            data = {
                "id": response_id.strip() if response_id.strip() else None,
                "model": model_name,
                "metadata": metadata
            }
            
            success = save_response(data, model_name, metadata)
            
            if success:
                st.success("✅ Respuesta guardada correctamente")
                
                # Actualizar estado en el API
                status_result = call_api_endpoint(
                    f"/v1/responses/{data.get('id')}",
                    data=json.dumps({
                        "id": data.get("id"),
                        "model": model_name,
                        "status": "saved",
                        "metadata": metadata
                    }),
                    method="POST",
                    api_key=api_key if api_key else None
                )
                
                if status_result.get("success"):
                    st.info("✅ Estado actualizado en el API")
                else:
                    st.warning(f"⚠️ Error actualizando API: {status_result.get('error')}")
            else:
                st.error("❌ Error guardando respuesta")
        else:
            st.warning("⚠️ Por favor, ingresa un ID válido")

# Obtener y mostrar respuestas guardadas
with st.expander("📂 Respuestas Guardadas", expanded=False):
    responses = get_all_responses()
    
    if not responses:
        st.info("No hay respuestas guardadas")
    else:
        st.write(f"**{len(responses)} respuestas encontradas:**")
        
        # Agrupar por modelo
        by_model = defaultdict(list)
        for resp in responses:
            by_model[resp["model"]].append(resp)
        
        for model, resp_list in by_model.items():
            st.markdown(f"**📁 {model}:**")
            for resp in resp_list[:5]:
                status_icon = "✅" if resp["status"] == "saved" else "⏳"
                st.write(f"  • {status_icon} **{resp['id']}** - {resp['status'][:20]}")

# ============================================================================
# Sección 3: Informes del Sistema
# ============================================================================

st.markdown('<p class="section-title">📊 Informes del Sistema</p>', unsafe_allow_html=True)

# 3.1 Profiles
with st.expander("👤 Profiles", expanded=False):
    profiles = get_profiles()
    
    if not profiles:
        st.info("No se encontraron perfiles")
    else:
        st.write(f"**{len(profiles)} profiles encontrados:**")
        
        for i, profile in enumerate(profiles, 1):
            with st.expander(f"{i}. {profile['name']}"):
                st.code(f"""
name: {profile['name']}
path: {profile['path']}
created: {datetime.fromtimestamp(profile['created']).strftime('%Y-%m-%d %H:%M:%S')}
                """)

# 3.2 Skills
with st.expander("🎨 Skills", expanded=False):
    skills = get_skills()
    
    if not skills:
        st.info("No se encontraron skills")
    else:
        # Agrupar por categoría
        categories = {}
        for skill in skills:
            cat = skill["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(skill)
        
        for category, skill_list in categories.items():
            st.markdown(f"**📁 {category.title()}:**")
            
            for skill in skill_list:
                icon = "✅" if skill["has_bundled"] else "⚪"
                st.write(f"  • {icon} **{skill['name']}**")

# 3.3 Sessions
with st.expander("📅 Sessions", expanded=False):
    sessions = get_sessions()
    
    if not sessions:
        st.info("No hay sesiones registradas")
    else:
        # Mostrar resumen
        st.write(f"**{len(sessions)} sesiones encontradas**")
        
        # Agrupar por fecha
        from collections import defaultdict
        by_date = defaultdict(list)
        for session in sessions:
            date = session["date"]
            by_date[date].append(session)
        
        for date in sorted(by_date.keys(), reverse=True):
            sessions_today = by_date[date]
            total_size = sum(s["size_bytes"] for s in sessions_today)
            
            st.markdown(f"**📆 {date}:** {len(sessions_today)} sesiones, {total_size / 1024:.1f} KB")
            
            for session in sessions_today[:5]:  # Mostrar máximo 5 por fecha
                icon = "📊" if session["size_bytes"] > 100000 else "📄"
                st.write(f"  • {icon} **{session['filename']}** - {session['size_bytes'] / 1024:.1f} KB")

# 3.4 Work Trees
with st.expander("🌳 Work Trees", expanded=False):
    work_trees = get_work_trees()
    
    if not work_trees:
        st.info("No se encontraron work trees activos")
    else:
        st.write(f"**{len(work_trees)} work trees encontrados:**")
        
        for tree in work_trees:
            st.write(f"  • **{tree['profile']}**: {tree['items']} items")

# ============================================================================
# Sección 4: Información Adicional
# ============================================================================

st.markdown('<p class="section-title">ℹ️ Información Adicional</p>', unsafe_allow_html=True)

# 4.1 Estado del Modelo
with st.expander("🧠 Estado del Modelo"):
    model_path = "/home/antonio/huggingface/Qwen3.5-9B-Q4_K_M.gguf"
    model_exists = os.path.exists(model_path)
    
    st.write(f"**Modelo:** Qwen3.5-9B-Q4_K_M")
    st.write(f"**Path:** `{model_path}`")
    st.write(f"**Existe:** {'✅ Sí' if model_exists else '❌ No'}")
    
    if model_exists:
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        st.write(f"**Tamaño:** {file_size:.1f} MB")
    else:
        st.warning("El modelo no está encontrado. Verifica que la ruta es correcta.")

# 4.2 Endpoints Disponibles
with st.expander("🔗 Endpoints del API", expanded=True):
    endpoints = [
        {
            "path": "/health", 
            "method": "GET", 
            "description": "Health check del servidor"
        },
        {
            "path": "/v1/models", 
            "method": "GET", 
            "description": "Obtener lista de modelos disponibles"
        },
        {
            "path": "/v1/responses", 
            "method": "POST", 
            "description": "Guardar una nueva respuesta"
        },
        {
            "path": "/v1/responses/{id}", 
            "method": "GET/PUT", 
            "description": "Obtener o actualizar una respuesta"
        }
    ]
    
    st.write("**Endpoints disponibles:**")
    for endpoint in endpoints:
        st.code(f"""
Path: {endpoint['path']}
Method: {endpoint['method']}
Description: {endpoint['description']}
        """)

# 4.3 Comandos Útiles
with st.expander("🛠️ Comandos Útiles"):
    st.write("""
Para iniciar el API de Hermes:

```bash
cd ~/hermes/api
source venv/bin/activate
python main.py
```

El servidor se inicia en http://127.0.0.1:8642

Para ver el historial del chat:
```bash
ls ~/.hermes/chat_history/
```
    """)

# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
st.caption(
    "🦉 Hermes Dashboard UI v1.0.0 | "
    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"API Status: {'✅ Online' if info.get('gateway_running') else '❌ Offline'}"
)

# ============================================================================
# Inicialización
# ============================================================================

# Inicializar base de datos de respuestas
init_responses_db()

# Verificar si el API está corriendo al iniciar
def check_api_status():
    """Verificar estado del API al cargar"""
    try:
        url = "http://127.0.0.1:8642/health"
        response = urllib.request.urlopen(url, timeout=2)
        data = json.loads(response.read().decode())
        
        if data.get("status") == "ok":
            return True
    except:
        pass
    
    return False

# Mostrar estado inicial
if check_api_status():
    st.sidebar.success("✅ API Hermes está online en puerto 8642")
else:
    st.sidebar.info("⚠️ El API no está corriendo en puerto 8642")
    st.sidebar.info("Inicia el API con: `python ~/hermes/api/main.py`")
