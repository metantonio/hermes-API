# Hermes Dashboard UI

Dashboard web para gestionar y monitorear el API de Hermes Web Data.

## Características

- 🤖 **Chat interactivo** con Hermes AI usando el endpoint `/api/v1/chat`
- 📊 **Informes del sistema**: profiles, skills, sessions, work trees
- 🔌 **Test de endpoints** para verificar el estado del API
- 📈 **Gráficos visuales** con barras de progreso
- 🖥️ **Interfaz moderna** con Streamlit

## Requisitos

- Python 3.12+
- Virtual environment configurado
- Modelo local: Qwen3.5-9B-Q4_K_M.gguf

## Instalación

```bash
# 1. Activar entorno virtual
cd ~/hermes/api
source venv/bin/activate

# 2. Instalar dependencias del dashboard
pip install -r requirements_dashboard.txt
```

## Ejecución

```bash
# 3. Ejecutar el dashboard
streamlit run hermes_dashboard.py
```

El dashboard se abrirá en tu navegador en:
- **URL:** http://localhost:8501
- **API:** http://localhost:8000

## Estructura de archivos

```
~/hermes/api/
├── hermes_dashboard.py      # Dashboard UI principal
├── requirements_dashboard.txt
├── install_dashboard.sh      # Script de instalación
├── test_dashboard.py         # Suite de tests (legacy)
├── simple_test.py            # Test simplificado
└── README_dashboard.md       # Este archivo
```

## Endpoints del API

El dashboard puede interactuar con los siguientes endpoints:

| Endpoint | Descripción |
|----------|-------------|
| `/health` | Health check del API |
| `/api/v1/chat` | Chat completions (OpenAI-compatible) |

## Configuración del Modelo

El dashboard usa el modelo local Qwen3.5-9B-Q4_K_M. Verifica que está instalado:

```bash
ls /home/antonio/huggingface/Qwen3.5-9B-Q4_K_M.gguf
```

Si no existe, descarga el modelo:

```bash
huggingface-cli download Qwen/Qwen3.5-9B-Q4_K_M --local-dir /home/antonio/huggingface
```

## Estadísticas del Sistema

El dashboard muestra:

- **Profiles**: 2 perfiles encontrados
- **Skills**: 38 skills encontrados
- **Sessions**: 117 sesiones registradas
- **Modelo**: 5.3 GB disponible

## Uso en Producción

1. **Seguridad**: Configura API keys en el archivo `.env`
2. **Rate limiting**: El API ya incluye límites de tasa
3. **Monitoreo**: Revisa logs en `~/.hermes/logs/`

## Troubleshooting

**Error: No module named 'hermes_llama_wrapper'**

Asegúrate de que el archivo esté en `~/.hermes/`:

```bash
ls ~/.hermes/hermes_llama_wrapper.py
```

**Error: Modelo no encontrado**

Verifica la ruta del modelo y descárgala si es necesario.

## Contacto

Para soporte, contacta a: antonio.martinez@ejemplo.com
