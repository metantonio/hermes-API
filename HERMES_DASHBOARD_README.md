# Hermes Dashboard UI

Interfaz web en Python para monitorear y usar el API de Hermes Web Data.

## Características

### 🤖 Chat con Hermes AI
- Interfaz conversacional directa
- Respuestas usando modelo Qwen3.5-9B local
- Historial de conversaciones guardado automáticamente

### 🔌 Testing de Endpoints API
- Health check del servidor
- Test directo del endpoint `/api/v1/chat`
- Verificación de estado del API

### 📊 Informes del Sistema
- **Profiles**: Informar sobre perfiles configurados
- **Skills**: Lista de skills disponibles y su estado
- **Sessions**: Estadísticas de sesiones activas
- **Work Trees**: Información de work trees activos

### 🧠 Estado del Sistema
- Verificación del modelo Qwen3.5
- Status del gateway
- Información de configuración

## Instalación

### 1. Activar entorno virtual

```bash
cd ~/hermes/api
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements_dashboard.txt
```

### 3. Verificar modelo

Asegúrate de que el modelo Qwen3.5 esté disponible:

```bash
ls -lh /home/antonio/huggingface/Qwen3.5-9B-Q4_K_M.gguf
```

## Ejecución

### Opción 1: Ejecutar directamente

```bash
python hermes_dashboard.py
```

### Opción 2: Usar CLI de Streamlit

```bash
streamlit run hermes_dashboard.py
```

El servidor se abrirá automáticamente en tu navegador.

## Endpoints del API

El dashboard puede testear los siguientes endpoints:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Health check del servidor |
| `/api/v1/chat` | POST | Chat con Hermes AI |
| `/api/v1/extract` | POST | Extraer datos de URL |

## Configuración

### API Key

Configura tu API key en el sidebar del dashboard. Puedes ingresarla directamente o usar un archivo `.env`.

### Modelo Local

Por defecto usa: `Qwen3.5-9B-Q4_K_M.gguf`

Para cambiar el modelo, edita `hermes_llama_wrapper.py`:

```python
MODEL_PATH = "/ruta/a/tu/modelo.gguf"
```

## Estructura de Directorios

```
~/hermes/api/
├── main.py                    # API FastAPI principal
├── hermes_dashboard.py        # Dashboard UI
├── requirements_dashboard.txt # Dependencias del dashboard
└── HERMES_DASHBOARD_README.md # Este archivo
```

## Comandos Útiles

### Verificar estado del API

```bash
curl http://localhost:8000/health
```

### Ver historial de chat

```bash
ls -la ~/.hermes/chat_history/
cat ~/.hermes/chat_history/*.json
```

### Reiniciar el API

```bash
cd ~/hermes/api
source venv/bin/activate
python main.py
```

## Troubleshooting

### Error: "API no respondiendo"

1. Verifica que el API está corriendo:
   ```bash
   ps aux | grep python
   ```

2. Reinicia el API:
   ```bash
   pkill -f "python main.py"
   python main.py
   ```

### Error: "Modelo no encontrado"

Asegúrate de que la ruta del modelo es correcta:

```bash
ls /home/antonio/huggingface/Qwen3.5-9B-Q4_K_M.gguf
```

Si no existe, descarga el modelo desde Hugging Face:

```bash
huggingface-cli download Qwen/Qwen3.5-9B-Q4_K_M --local-dir /home/antonio/huggingface/
```

## Créditos

- **FastAPI** - API framework
- **Streamlit** - UI framework
- **llama-cpp-python** - Inferencia de modelos
- **Hermes AI** - Framework de agent

## Licencia

MIT License

---

Para más información, visita la documentación de Hermes:
https://github.com/NousResearch/hermes
