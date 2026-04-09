#!/bin/bash
# Script de instalación para Hermes Dashboard UI

set -e

echo "============================================================"
echo "🦉 Hermes Dashboard UI - Instalación"
echo "============================================================"

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements_dashboard.txt"

# Verificar Python
echo ""
echo "📊 Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "  ✅ Python $PYTHON_VERSION detectado"
else
    echo "  ❌ Error: Python 3 no encontrado"
    exit 1
fi

# Verificar virtual environment
echo ""
echo "📊 Verificando entorno virtual..."
if [ -d "$VENV_DIR" ]; then
    echo "  ✅ Entorno virtual encontrado: $VENV_DIR"
else
    echo "  ⚠️  Creando entorno virtual..."
    python3 -m venv "$VENV_DIR"
    echo "  ✅ Entorno virtual creado"
fi

# Activar entorno virtual
echo ""
echo "📊 Activando entorno virtual..."
source "$VENV_DIR/bin/activate"

# Instalar dependencias
echo ""
echo "📊 Instalando dependencias..."
if [ -f "$REQUIREMENTS_FILE" ]; then
    pip install -r "$REQUIREMENTS_FILE"
    echo "  ✅ Dependencias instaladas"
else
    echo "  ⚠️  Archivo requirements_dashboard.txt no encontrado"
    echo "  Instalando dependencias básicas..."
    pip install streamlit numpy pandas sqlalchemy pydantic
    echo "  ✅ Dependencias básicas instaladas"
fi

# Verificar módulos necesarios
echo ""
echo "📊 Verificando módulos..."

modules_ok=true

if python3 -c "import streamlit; print('  ✅ streamlit')" 2>/dev/null; then
    :
else
    echo "  ❌ streamlit no instalado"
    modules_ok=false
fi

if python3 -c "from hermes_llama_wrapper import intercept_llm_call" 2>/dev/null; then
    echo "  ✅ hermes_llama_wrapper"
else
    echo "  ⚠️  hermes_llama_wrapper no encontrado en ~/.hermes/"
fi

# Verificar modelo
echo ""
echo "📊 Verificando modelo Qwen3.5-9B..."
MODEL_PATH="/home/antonio/huggingface/Qwen3.5-9B-Q4_K_M.gguf"
if [ -f "$MODEL_PATH" ]; then
    MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
    echo "  ✅ Modelo encontrado: $MODEL_SIZE"
else
    echo "  ⚠️  Modelo no encontrado en: $MODEL_PATH"
    echo ""
    echo "  Para descargar el modelo, usa:"
    echo "  huggingface-cli download Qwen/Qwen3.5-9B-Q4_K_M --local-dir /home/antonio/huggingface"
fi

# Crear directorios necesarios
echo ""
echo "📊 Creando directorios..."
mkdir -p ~/.hermes/sessions
mkdir -p ~/.hermes/chat_history

echo ""
echo "============================================================"
echo "🦉 Hermes Dashboard UI instalado correctamente!"
echo "============================================================"
echo ""
echo "Para ejecutar el dashboard:"
echo "  cd ~/hermes/api"
echo "  source venv/bin/activate"
echo "  streamlit run hermes_dashboard.py"
echo ""
echo "El dashboard se abrirá en: http://localhost:8501"
echo ""
echo "Para más información, revisa: README_dashboard.md"
echo "============================================================"
