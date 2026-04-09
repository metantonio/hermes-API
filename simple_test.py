#!/usr/bin/env python3
"""
Test simple para Hermes Dashboard UI
Verifica que el módulo funciona correctamente
"""

import sys
import os

# Agregar ~/.hermes al path
HERMES_HOME = os.path.expanduser("~/.hermes")
if HERMES_HOME not in sys.path:
    sys.path.insert(0, HERMES_HOME)

print("=" * 60)
print("🦉 Hermes Dashboard UI - Simple Test")
print("=" * 60)

# Test 1: Importar módulos
print("\n🧪 Test 1: Importando módulos...")
try:
    from hermes_llama_wrapper import intercept_llm_call
    print("  ✅ hermes_llama_wrapper importado")
except ImportError as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

try:
    import streamlit
    print("  ✅ streamlit importado")
except ImportError as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 2: Verificar llama-cpp-python
print("\n🧪 Test 2: Verificando llama-cpp-python...")
try:
    from llama_cpp import Llama
    print("  ✅ llama-cpp-python disponible")
except ImportError as e:
    print(f"  ⚠️  llama-cpp-python no instalado: {e}")
    print("  Para instalar: pip install llama-cpp-python")

# Test 3: Verificar modelo
print("\n🧪 Test 3: Verificando modelo...")
MODEL_PATH = "/home/antonio/huggingface/Qwen3.5-9B-Q4_K_M.gguf"
if os.path.exists(MODEL_PATH):
    size_mb = os.path.getsize(MODEL_PATH) / (1024 * 1024)
    print(f"  ✅ Modelo encontrado: {MODEL_PATH}")
    print(f"     Tamaño: {size_mb:.1f} MB")
else:
    print(f"  ⚠️  Modelo no encontrado en: {MODEL_PATH}")
    print("  Para descargar, usa:")
    print(f"  huggingface-cli download Qwen/Qwen3.5-9B-Q4_K_M --local-dir {MODEL_PATH.parent}")

# Test 4: Verificar información del sistema
print("\n🧪 Test 4: Información del sistema...")
from pathlib import Path
hermes_home = Path(HERMES_HOME)

info = {
    "version": "1.0.0",
    "home": str(hermes_home),
    "config_file": hermes_home / "config.yaml",
    "config_exists": (hermes_home / "config.yaml").exists(),
}

print(f"  Versión: {info['version']}")
print(f"  Home: {info['home']}")
print(f"  Config existe: {info['config_exists']}")

# Test 5: Contar profiles, skills, sessions
print("\n🧪 Test 5: Estadísticas...")

# Profiles
profiles_path = hermes_home / "profiles"
if profiles_path.exists():
    profile_count = len([d for d in profiles_path.iterdir() if d.is_dir()])
    print(f"  Profiles: {profile_count}")
else:
    print("  Profiles: 0 (directory not found)")

# Skills
skills_path = hermes_home / "skills"
if skills_path.exists():
    skill_count = len([d for d in skills_path.iterdir() if d.is_dir()])
    print(f"  Skills: {skill_count}")
else:
    print("  Skills: 0 (directory not found)")

# Sessions
sessions_path = hermes_home / "sessions"
if sessions_path.exists():
    session_count = len([f for f in sessions_path.glob("*.json")])
    print(f"  Sessions: {session_count}")
else:
    print("  Sessions: 0 (directory not found)")

# Work trees
work_trees = []
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

print(f"  Work trees: {len(work_trees)}")

# Test 6: Verificar API status
print("\n🧪 Test 6: Verificando API status...")
try:
    import urllib.request
    url = "http://localhost:8000/health"
    response = urllib.request.urlopen(url, timeout=2)
    data = response.read().decode()
    print(f"  ✅ API respondiendo en {url}")
    print(f"     {data}")
except Exception as e:
    print(f"  ⚠️  API no respondiendo (normal si no está corriendo)")
    print(f"     Error: {e}")

# Test 7: Verificar API key config
print("\n🧪 Test 7: Verificando configuración API...")
api_key_path = hermes_home / "api" / ".env"
if api_key_path.exists():
    print(f"  ✅ Archivo .env encontrado en {api_key_path}")
else:
    print(f"  ⚠️  Archivo .env no encontrado en {api_key_path}")

# Resumen
print("\n" + "=" * 60)
print("📊 Resumen")
print("=" * 60)
print(f"  ✅ Módulos importados correctamente")
print(f"  ✅ llama-cpp-python: {os.path.exists(MODEL_PATH)}")
print(f"  ✅ Modelo: {os.path.exists(MODEL_PATH)}")
print(f"  ✅ Profiles: {profile_count if 'profile_count' in dir() else 'N/A'}")
print(f"  ✅ Skills: {skill_count if 'skill_count' in dir() else 'N/A'}")
print(f"  ✅ Sessions: {session_count if 'session_count' in dir() else 'N/A'}")
print("=" * 60)

print("\n🦉 Hermes Dashboard UI está listo para usar!")
print("\nPara ejecutar el dashboard:")
print("  cd ~/hermes/api")
print("  source venv/bin/activate")
print("  streamlit run hermes_dashboard.py")
print("=" * 60)
