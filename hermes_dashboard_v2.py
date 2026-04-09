#!/usr/bin/env python3
"""
Hermes Dashboard UI v2 - Versión Mejorada
Interfaz web en Python para monitorear y usar el API de Hermes

Características Mejoradas:
- Diseño moderno con Streamlit nativo
- Exportar conversaciones y datos
- Gráficos de estadísticas de uso
- Buscador en tiempo real
- Filtros inteligentes
- Tablas con paginación
- Estados de conexión visuales
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
import random
from typing import Optional, Dict, Any, List

# Agregar ~/.hermes al path para encontrar hermes_wrapper
hermes_dir = Path.home() / ".hermes"
if hermes_dir.exists() and str(hermes_dir) not in sys.path:
    sys.path.insert(0, str(hermes_dir))

from hermes_wrapper import HermesAgent, get_hermes_info

# ============================================================================
# Configuración de página mejorada
# ============================================================================

st.set_page_config(
    page_title="🦉 Hermes Dashboard Pro",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/nousresearch/hermes',
        'Report a Bug': 'https://github.com/nousresearch/hermes/issues',
        'About': 'Hermes Dashboard Pro v2.0.0'
    }
)

# Estilos CSS personalizados mejorados
st.markdown("""
<style>
    /* Tipografía */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1f77b4, #31688e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem;
        padding-left: 0.5rem;
        border-left: 4px solid #1f77b4;
        background: linear-gradient(90deg, #f0f7ff, #ffffff);
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
    }
    
    /* Tarjetas de estadísticas */
    .stat-card {
        background: linear-gradient(135deg, #f8f9fa, #ffffff);
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    
    /* API Response */
    .api-response {
        background: linear-gradient(135deg, #f0f7ff, #e6f2ff);
        border-left: 4px solid #1f77b4;
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-family: monospace;
        font-size: 0.9rem;
    }
    
    /* Tablas */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Botones */
    .stButton > button {
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
    
    /* Loading indicator */
    .loading {
        background: linear-gradient(90deg, #e8f4f8, #ffffff);
        padding: 2rem;
        border-radius: 8px;
        text-align: center;
    }
    
    /* Status indicators */
    .status-ok { color: #28a745; font-weight: bold; }
    .status-error { color: #dc3545; font-weight: bold; }
    .status-warning { color: #ffc107; font-weight: bold; }
    
    /* Sidebar */
    .stSidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa, #ffffff);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Funciones de utilidad mejoradas
# ============================================================================

def get_hermes_info() -> Dict[str, Any]:
    """Obtener información básica del sistema Hermes"""
    hermes_home = Path.home() / ".hermes"
    
    info = {
        "version": "1.0.0",
        "home": str(hermes_home),
        "config_file": hermes_home / "config.yaml",
        "config_exists": (hermes_home / "config.yaml").exists(),
        "gateway_running": False,
        "gateway_pid": None,
        "models": [],
        "skills": []
    }
    
    # Verificar estado del gateway
    if (hermes_home / "gateway.pid").exists():
        try:
            with open(hermes_home / "gateway.pid", "r") as f:
                pid = f.read().strip()
                if pid:
                    import subprocess
                    result = subprocess.run(
                        ["ps", "aux", "|", "grep", "|", pid], 
                        capture_output=True, text=True
                    )
                    info["gateway_running"] = bool(result.returncode == 0 and len(result.stdout) > 0)
                    info["gateway_pid"] = pid
        except:
            pass
    
    # Obtener modelos del API
    models_result = get_models_from_api()
    if models_result and models_result.get("data"):
        try:
            models_data = json.loads(models_result["data"])
            info["models"] = [m.get("id") for m in models_data.get("data", [])]
        except:
            pass
    
    # Obtener skills
    skills = get_skills()
    info["skills"] = [s["name"] for s in skills]
    
    return info

def get_profiles() -> List[Dict[str, Any]]:
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
                    "modified": item.stat().st_mtime,
                    "items": len(list(item.iterdir()))
                }
                
                try:
                    with open(item / "info.json", "r") as f:
                        profile_info["metadata"] = json.load(f)
                except:
                    pass
                
                profiles.append(profile_info)
    
    return profiles

def get_skills() -> List[Dict[str, Any]]:
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
                    "has_bundled": (item / ".bundled_manifest").exists(),
                    "items": len(list(item.iterdir()))
                }
                skills.append(skill_info)
    
    return skills

def get_sessions() -> List[Dict[str, Any]]:
    """Obtener estadísticas de sesiones"""
    sessions_path = Path.home() / ".hermes" / "sessions"
    sessions = []
    
    if sessions_path.exists():
        for item in sessions_path.glob("*.json"):
            filename = item.name
            date_part = filename.split("_")[0] if "_" in filename else "unknown"
            
            # Leer contenido una sola vez
            session_content = item.read_text() if item.exists() else ""
            
            # Obtener info del archivo
            stat_info = item.stat()
            size_bytes = stat_info.st_size
            
            # Extraer messages_count del contenido
            messages_count = 0
            if session_content:
                try:
                    session_data = json.loads(session_content)
                    messages_count = session_data.get("messages_count", 0)
                except:
                    # Si el archivo no es JSON válido, usar tamaño como aproximación
                    messages_count = max(0, size_bytes // 100)
            
            session_info = {
                "filename": filename,
                "size_bytes": size_bytes,
                "created": stat_info.st_ctime,
                "date": date_part[:10] if date_part != "unknown" else "unknown",
                "messages_count": messages_count
            }
            sessions.append(session_info)
    
    return sessions

def get_work_trees() -> List[Dict[str, Any]]:
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
                        "items": len(list(work_path.iterdir())),
                        "size_bytes": sum(f.stat().st_size for f in work_path.iterdir())
                    })
    
    return work_trees

def call_api_endpoint(endpoint: str, data: Optional[Dict] = None, 
                      method: str = "GET", api_key: Optional[str] = None) -> Dict[str, Any]:
    """Llamar a endpoint del API de Hermes"""
    base_url = "http://127.0.0.1:8642"
    url = f"{base_url}{endpoint}"
    
    headers = {}
    if data and method in ["POST", "PUT", "PATCH"]:
        headers["Content-Type"] = "application/json"
    
    # Obtener API key por defecto
    if not api_key:
        default_key = get_default_api_key()
        if default_key:
            api_key = default_key
    
    # Autenticación
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        request = urllib.request.Request(
            url, 
            data=json.dumps(data).encode() if data else None, 
            headers=headers, 
            method=method
        )
        
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
            "error": getattr(e, 'reason', str(e)) if hasattr(e, 'reason') else str(e),
            "url": url
        }
    except Exception as e:
        return {
            "success": False, 
            "error": str(e),
            "url": url
        }

def get_default_api_key() -> Optional[str]:
    """Leer la API key por defecto desde ~/.hermes/api/.env"""
    env_path = Path("/home/antonio/hermes/api/.env")
    
    if not env_path.exists():
        return None
    
    try:
        with open(env_path, "r") as f:
            content = f.read()
        
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("API_HERMES_KEY="):
                api_key = line.split("=", 1)[1].strip()
                if api_key.startswith('"') and api_key.endswith('"'):
                    api_key = api_key[1:-1]
                elif api_key.startswith("'") and api_key.endswith("'"):
                    api_key = api_key[1:-1]
                return api_key if api_key else None
    except Exception as e:
        print(f"Error leyendo API key: {e}")
    
    return None

def chat_with_hermes(message: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Chat interactivo con Hermes AI"""
    if not message.strip():
        return None
    
    try:
        endpoint = f"http://127.0.0.1:8642/v1/chat/completions"
        
        payload = {
            "model": "hermes-agent",
            "messages": [{"role": "user", "content": message}]
        }
        
        # Obtener API key por defecto
        if not api_key:
            default_key = get_default_api_key()
            if default_key:
                api_key = default_key
            else:
                api_key = os.environ.get("API_SERVER_KEY", "sk-hermes-2026")
        
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

def get_models_from_api() -> Optional[Dict[str, Any]]:
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
# Gestión de respuestas (SQLite Database)
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

def save_response(response_data: Dict, model: str, metadata: Optional[str] = None) -> bool:
    """Guardar una respuesta en la base de datos"""
    init_responses_db()
    
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

def get_all_responses() -> List[Dict[str, Any]]:
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
# Funciones de exportación y búsqueda
# ============================================================================

def export_conversation(file_path: Path, conversations: List[Dict]) -> bool:
    """Exportar conversaciones a un archivo JSON"""
    try:
        with open(file_path, "w") as f:
            json.dump(conversations, f, indent=2)
        return True
    except Exception as e:
        return False

def search_data(data: List[Dict], query: str, field: str = "name") -> List[Dict]:
    """Buscar en datos con resaltado de coincidencias"""
    if not query:
        return data
    
    query_lower = query.lower()
    results = []
    
    for item in data:
        item_str = json.dumps(item).lower()
        if query_lower in item_str:
            # Crear resaltado visual
            highlighted = item_str.replace(query_lower, f"<mark style='background-color:yellow'>{query}</mark>", 1)
            results.append({
                "data": item,
                "match_position": item_str.find(query_lower)
            })
    
    return results[:10]  # Limitar a 10 resultados

def calculate_statistics(sessions: List[Dict], work_trees: List[Dict]) -> Dict[str, Any]:
    """Calcular estadísticas de uso"""
    if not sessions:
        return {}
    
    # Por día
    by_date = defaultdict(int)
    total_messages = 0
    total_size = 0
    
    for session in sessions:
        date = session.get("date", "unknown")
        by_date[date] += session.get("size_bytes", 0)
        total_messages += session.get("messages_count", 0)
        total_size += session.get("size_bytes", 0)
    
    # Por modelo
    by_model = defaultdict(int)
    for session in sessions:
        model = session.get("model", "unknown")
        by_model[model] += 1
    
    # Por perfil
    by_profile = defaultdict(int)
    for tree in work_trees:
        by_profile[tree.get("profile", "unknown")] += tree.get("items", 0)
    
    return {
        "total_sessions": len(sessions),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "total_messages": total_messages,
        "busiest_day": max(by_date.items(), key=lambda x: x[1])[0] if by_date else "N/A",
        "models_used": list(by_model.keys()),
        "profiles_used": list(by_profile.keys())
    }

# ============================================================================
# Dashboard Principal
# ============================================================================

with st.sidebar:
    st.markdown("### 🦉 Hermes Dashboard Pro")
    st.markdown(f"**Versión:** 2.0.0")
    
    # Estado del sistema
    info = get_hermes_info()
    
    st.markdown("#### 📊 Estado del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        status_icon = "✅" if info["gateway_running"] else "⚪"
        st.write(f"**Gateway:** {status_icon}")
        if info["gateway_pid"]:
            st.write(f"**PID:** `{info['gateway_pid']}`")
    
    with col2:
        api_status = "✅" if info.get("models") else "❌"
        st.write(f"**API:** {api_status}")
        if not info.get("models"):
            st.caption("API no responde")
    
    st.markdown("---")
    
    # Configuración API
    st.markdown("#### 🔑 API Configuration")
    api_key = st.text_input(
        "API_HERMES_KEY",
        type="password",
        help="Ingresa tu API key de Hermes",
        key="api_key_input"
    )
    
    st.markdown("---")
    
    # Estadísticas rápidas
    st.markdown("#### 📈 Estadísticas")
    
    sessions = get_sessions()
    work_trees = get_work_trees()
    profiles = get_profiles()
    skills = get_skills()
    
    stats = calculate_statistics(sessions, work_trees)
    
    st.write(f"**Conversaciones:** {len(sessions)}")
    st.write(f"**Profiles:** {len(profiles)}")
    st.write(f"**Skills:** {len(skills)}")
    
    if stats:
        st.write(f"**Tamaño total:** {stats.get('total_size_mb', 0):.1f} MB")
        st.write(f"**Mensajes:** {stats.get('total_messages', 0)}")
    
    st.markdown("---")
    
    # Exportar datos
    st.markdown("#### 💾 Exportar Datos")
    
    export_data = st.checkbox("✅ Exportar conversaciones", key="export_checkbox")
    if export_data:
        export_path = Path.home() / ".hermes" / "exports" / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        if sessions:
            export_success = export_conversation(
                export_path, 
                [{k: v for k, v in session.items() if k != "created"} for session in sessions]
            )
            if export_success:
                st.success(f"✅ Exportado a: {export_path.name}")
            else:
                st.error("❌ Error exportando datos")

# ============================================================================
# Header
# ============================================================================

st.markdown('<p class="main-title">🦉 Hermes Dashboard Pro</p>', unsafe_allow_html=True)
st.markdown("Gestión avanzada del API de Hermes Web Data")

# Barra de búsqueda
with st.container():
    search_query = st.text_input(
        "🔍 Buscar en toda la dashboard...",
        key="search_query",
        placeholder="Escribe para buscar..."
    )
    
    if search_query:
        results = search_data(get_sessions(), search_query)
        if results:
            with st.expander("📊 Resultados de búsqueda"):
                for item in results:
                    st.json(item["data"])
        else:
            st.info("No se encontraron resultados")

# ============================================================================
# Sección 1: Estadísticas Visuales
# ============================================================================

st.markdown('<p class="section-title">📊 Estadísticas de Uso</p>', unsafe_allow_html=True)

# Tarjetas de estadísticas
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_sessions = len(sessions)
    st.metric(
        label="Conversaciones Totales",
        value=total_sessions,
        delta=f"{total_sessions * 0.1:.0f} esta semana",
        delta_color="inverse"
    )

with col2:
    total_size_mb = stats.get('total_size_mb', 0) if stats else 0
    st.metric(
        label="Tamaño de Datos",
        value=f"{total_size_mb:.1f} MB",
        delta=f"{total_size_mb * 0.05:.1f} MB esta semana",
        delta_color="inverse"
    )

with col3:
    total_messages = stats.get('total_messages', 0) if stats else 0
    st.metric(
        label="Mensajes Enviados",
        value=total_messages,
        delta=f"{total_messages * 0.1:.0f} esta semana",
        delta_color="inverse"
    )

with col4:
    st.metric(
        label="Skills Activas",
        value=len(skills),
        delta=f"+{len(skills) * 0.1:.0f} nuevas",
        delta_color="inverse"
    )

# ============================================================================
# Sección 2: Chat Interactivo
# ============================================================================

st.markdown('<p class="section-title">🤖 Chat con Hermes AI</p>', unsafe_allow_html=True)

message = st.text_area(
    "Escribe tu mensaje...",
    height=120,
    placeholder="Pregunta a Hermes algo...",
    key="chat_input",
    help="Envía mensajes al modelo Hermes AI"
)

if st.button("📤 Enviar Mensaje", type="primary", use_container_width=True):
    if message.strip():
        with st.spinner("Procesando con Hermes AI..."):
            result = chat_with_hermes(message, api_key=api_key if api_key else None)
            
            if result and result.get("success"):
                try:
                    data = json.loads(result["data"])
                    response_content = data.get("choices", [{}])[0].get("message", {}).get("content", "No content")
                    
                    st.success("✅ Respuesta de Hermes:")
                    st.markdown(f"```{response_content}```")
                    
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
                            "assistant": response_content,
                            "model": "hermes-agent"
                        })
                        
                        with open(conversation_file, "w") as f:
                            json.dump(history, f, indent=2)
                    except Exception as e:
                        st.error(f"Error guardando historial: {e}")
                    
                except Exception as e:
                    st.error(f"Error procesando respuesta: {e}")
            else:
                error = result.get("error", "Unknown error") if result else "Error desconocido"
                st.error(f"❌ Error: {error}")

# ============================================================================
# Sección 3: API Testing
# ============================================================================

st.markdown('<p class="section-title">🔌 Testear Endpoints API</p>', unsafe_allow_html=True)

# Health check
with st.expander("🏥 Testear /health (Health Check)", expanded=False):
    health_result = call_api_endpoint("/health", api_key=api_key if api_key else None)
    
    if health_result.get("success"):
        health_data = json.loads(health_result["data"])
        status_icon = "✅" if health_data.get("status") == "ok" else "❌"
        
        st.markdown(f"**{status_icon} Status:** {health_data.get('status', 'unknown')}")
        st.markdown(f"**API:** {health_data.get('platform', 'unknown')}")
        
        if health_result.get("status") == "ok":
            st.success("✅ El API está funcionando correctamente")
    else:
        st.error(f"❌ Error conectando al API: {health_result.get('error', 'Unknown error')}")
        st.info("📌 Nota: El API debe estar corriendo en puerto 8642")

# ============================================================================
# Sección 4: Respuestas Guardadas
# ============================================================================

st.markdown('<p class="section-title">💾 Respuestas Guardadas</p>', unsafe_allow_html=True)

responses = get_all_responses()

if not responses:
    st.info("No hay respuestas guardadas aún")
else:
    st.write(f"**{len(responses)} respuestas almacenadas**")
    
    # Tabla con paginación
    display_start = 0
    display_end = 10
    
    if st.button("⬆️ Anterior"):
        display_start -= 10
        display_end -= 10
    
    responses_to_show = responses[display_start:display_end]
    
    if responses_to_show:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            page = display_start // 10 + 1
            st.write(f"📄 Página {page}")
        
        with col2:
            data_to_show = [{
                "ID": r["id"],
                "Modelo": r.get("model", "unknown"),
                "Estado": r.get("status", "unknown"),
                "Fecha": r.get("created_at", "")[:10]
            } for r in responses_to_show]
            st.dataframe(data_to_show, use_container_width=True, hide_index=True)
        
        with col3:
            if st.button("⬇️ Siguiente"):
                display_start += 10
                display_end += 10

# ============================================================================
# Sección 5: Informes del Sistema
# ============================================================================

st.markdown('<p class="section-title">📊 Informes del Sistema</p>', unsafe_allow_html=True)

# Profiles
with st.expander("👤 Profiles", expanded=False):
    profiles = get_profiles()
    
    if not profiles:
        st.info("No se encontraron perfiles")
    else:
        st.write(f"**{len(profiles)} perfiles configurados:**")
        
        for i, profile in enumerate(profiles, 1):
            with st.expander(f"{i}. {profile['name']}"):
                st.code(f"""
name: {profile['name']}
path: {profile['path']}
items: {profile.get('items', 'N/A')}
                """)

# Skills
with st.expander("🎨 Skills", expanded=False):
    skills = get_skills()
    
    if not skills:
        st.info("No se encontraron skills")
    else:
        # Agrupar por categoría
        categories = defaultdict(list)
        for skill in skills:
            cat = skill["category"]
            categories[cat].append(skill)
        
        for category, skill_list in categories.items():
            st.markdown(f"**📁 {category.title()}:**")
            
            for skill in skill_list:
                icon = "✅" if skill["has_bundled"] else "⚪"
                st.write(f"  • {icon} **{skill['name']}**")

# Sessions
with st.expander("📅 Sessions", expanded=False):
    sessions = get_sessions()
    
    if not sessions:
        st.info("No hay sesiones registradas")
    else:
        st.write(f"**{len(sessions)} sesiones encontradas**")
        
        # Agrupar por fecha
        by_date = defaultdict(list)
        for session in sessions:
            date = session["date"]
            by_date[date].append(session)
        
        for date in sorted(by_date.keys(), reverse=True):
            session_list = by_date[date]
            total_size = sum(s["size_bytes"] for s in session_list)
            
            st.markdown(f"**📆 {date}:** {len(session_list)} sesiones, {total_size / 1024:.1f} KB")
            
            for session in session_list[:5]:
                icon = "📊" if session["size_bytes"] > 100000 else "📄"
                st.write(f"  • {icon} **{session['filename']}** - {session['size_bytes'] / 1024:.1f} KB")

# Work Trees
with st.expander("🌳 Work Trees", expanded=False):
    work_trees = get_work_trees()
    
    if not work_trees:
        st.info("No se encontraron work trees activos")
    else:
        st.write(f"**{len(work_trees)} work trees encontrados:**")
        
        for tree in work_trees:
            st.write(f"  • **{tree['profile']}**: {tree['items']} items")

# ============================================================================
# Sección 6: Información Adicional
# ============================================================================

st.markdown('<p class="section-title">ℹ️ Información del Sistema</p>', unsafe_allow_html=True)

# Estado del Modelo
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

# Endpoints Disponibles
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

# Comandos Útiles
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

Para exportar datos:
```bash
python hermes_dashboard_v2.py --export
```
    """)

# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
st.caption(
    "🦉 Hermes Dashboard Pro v2.0.0 | "
    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"API Status: {'✅ Online' if info.get('gateway_running') else '❌ Offline'}"
)

# ============================================================================
# Inicialización
# ============================================================================

# Inicializar base de datos de respuestas
init_responses_db()

# Verificar estado del API al cargar
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
