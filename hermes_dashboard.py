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
from pathlib import Path
from datetime import datetime
import sqlite3
import urllib.request
import urllib.error
import sys
from pathlib import Path

# Agregar ~/.hermes al path para encontrar hermes_wrapper
hermes_dir = Path.home() / ".hermes"
if hermes_dir.exists() and str(hermes_dir) not in sys.path:
    sys.path.insert(0, str(hermes_dir))

from hermes_wrapper import HermesAgent, get_hermes_info

# Configuración de página
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
            # Obtener fecha del archivo
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
    
    # Buscar directorios 'work' en profiles
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

def call_api_endpoint(endpoint, data=None, method="GET"):
    """Llamar a endpoint del API de Hermes"""
    try:
        # URL base del API (usamos localhost)
        base_url = "http://localhost:8000"
        url = f"{base_url}{endpoint}"
        
        headers = {}
        if data and method == "POST":
            headers["Content-Type"] = "application/json"
            headers["Authorization"] = "Bearer apikey"  # Verificar API key
            
        request = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, 
                                         headers=headers, method=method)
        
        with urllib.request.urlopen(request, timeout=10) as response:
            result = response.read().decode()
            return {"success": True, "data": result, "status": response.status}
            
    except urllib.error.URLError as e:
        return {"success": False, "error": str(e.reason) if hasattr(e, 'reason') else str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def chat_with_hermes(message, agent: HermesAgent = None):
    """
    Chat interactivo con Hermes AI usando el endpoint del API
    
    Parámetros:
        message: El mensaje a enviar a Hermes
        agent: Instancia de HermesAgent (opcional, se crea una nueva si no se proporciona)
    
    Retorna:
        Dict con el resultado del chat
    """
    if not message.strip():
        return None
    
    # Crear instancia del agente si no se proporciona
    if agent is None:
        agent = HermesAgent()
    
    # Usar el endpoint del API para el chat
    try:
        data = {
            "model": "hermes-agent",
            "messages": [{"role": "user", "content": message}]
        }
        
        result = agent._make_request("/api/v1/chat", method="POST", data=data)
        
        if result["success"]:
            try:
                response_data = json.loads(result["data"])
                if "choices" in response_data and response_data["choices"]:
                    return {
                        "success": True,
                        "response": response_data["choices"][0]["content"].strip()
                    }
                else:
                    return {
                        "success": False,
                        "error": "Respuesta del API no válida"
                    }
            except (json.JSONDecodeError, IndexError) as e:
                return {
                    "success": False,
                    "error": f"Error parseando respuesta: {str(e)}"
                }
        else:
            return {
                "success": False,
                "error": result.get("error", "Error desconocido")
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

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
    
    # Inicializar agente Hermes si no existe
    if 'hermes_agent' not in locals():
        hermes_agent = HermesAgent()
    
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
        st.code(f"""
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
    
    # Mini gráficos con barras
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bar = st.progress(len(profiles) / max(len(profiles) + 1, 1))
        st.caption("Profiles: ✅" if profiles else "Profiles: ⚪")
    
    with col2:
        bar = st.progress(len(skills) / max(len(skills) + 1, 1))
        st.caption("Skills: ✅" if skills else "Skills: ⚪")
    
    with col3:
        bar = st.progress(len(sessions) / max(len(sessions) + 1, 1))
        st.caption("Sessions: ✅" if sessions else "Sessions: ⚪")

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
            result = chat_with_hermes(message)
            
            if result and result.get("success"):
                st.success("✅ Respuesta de Hermes:")
                st.markdown(f"```{result['response']}```")
                
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
                        "assistant": result["response"]
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
with st.expander("🏥 Testear /health (Health Check)"):
    health_result = call_api_endpoint("/health")
    
    if health_result.get("success"):
        health_data = json.loads(health_result["data"])
        status_icon = "✅" if health_data.get("status") == "healthy" else "❌"
        
        st.markdown(f"**{status_icon} Status:** {health_data.get('status', 'unknown')}")
        st.markdown(f"**Timestamp:** {health_data.get('timestamp', 'unknown')}")
        
        if health_result.get("status") == "healthy":
            st.success("El API está funcionando correctamente")
    else:
        st.error(f"Error conectando al API: {health_result.get('error', 'Unknown error')}")
        st.info("📌 Nota: El API debe estar corriendo en localhost:8000")

# Test del endpoint /api/v1/chat
with st.expander("💬 Testear /api/v1/chat"):
    test_message = st.text_input(
        "Mensaje de prueba:",
        value="Hola, ¿cómo estás?",
        key="test_chat_input"
    )
    
    if st.button("📤 Enviar Test Chat"):
        if test_message.strip():
            chat_result = call_api_endpoint(
                "/api/v1/chat",
                data=json.dumps({
                    "model": "hermes-agent",
                    "messages": [{"role": "user", "content": test_message}]
                }),
                method="POST"
            )
            
            if chat_result.get("success"):
                chat_data = json.loads(chat_result["data"])
                st.success("✅ Respuesta del API:")
                st.json(chat_data)
            else:
                st.error(f"❌ Error API: {chat_result.get('error', 'Unknown error')}")

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
                
                if "metadata" in profile:
                    st.json(profile["metadata"])

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
                st.code(f"""
name: {skill['name']}
category: {skill['category']}
has_bundled: {skill['has_bundled']}
                """)

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
            st.code(f"""
profile: {tree['profile']}
path: {tree['path']}
items: {tree['items']}
            """)

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
with st.expander("🔗 Endpoints del API"):
    endpoints = [
        {"path": "/health", "method": "GET", "description": "Health check del servidor"},
        {"path": "/api/v1/chat", "method": "POST", "description": "Chat con Hermes AI"},
        {"path": "/api/v1/extract", "method": "POST", "description": "Extraer datos de URL"}
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

El servidor se inicia en http://localhost:8000

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

# Verificar si el API está corriendo al iniciar
def check_api_status():
    """Verificar estado del API al cargar"""
    try:
        url = "http://localhost:8000/health"
        response = urllib.request.urlopen(url, timeout=2)
        data = json.loads(response.read().decode())
        
        if data.get("status") == "healthy":
            st.sidebar.success("✅ API Hermes está online")
            return True
    except:
        pass
    
    st.sidebar.info("⚠️ El API no está corriendo en localhost:8000")
    st.sidebar.info("Inicia el API con: `python ~/hermes/api/main.py`")
    
    return False

check_api_status()
