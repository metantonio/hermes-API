# Hermes Web Data API

A production-ready, secure API for web data extraction with comprehensive security measures to prevent credential/key leakage.

## 📋 Features

- **Secure Data Extraction**: Extract data from websites with automatic credential filtering
- **Comprehensive Security**: Prevents API keys, passwords, and sensitive data leakage
- **Production-Ready**: Built with FastAPI, PostgreSQL, Redis, and more
- **Audit Logging**: Complete audit trail for compliance
- **Rate Limiting**: Built-in rate limiting and circuit breakers
- **CORS Protection**: Configurable CORS with security headers

## 🚀 Quick Start

### 1. Clone and Install

```bash
# Clone the repository
git clone <repository-url>
cd hermes/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Configure Database

```bash
# Option A: PostgreSQL (recommended for production)
# Create database:
createdb hermes
# Update DB_URL in .env: postgresql://user:password@localhost/hermes

# Option B: SQLite (development only)
# Uncomment in .env: DB_URL=sqlite:///./hermes.db
```

### 3. Start Server

```bash
# Development mode (with auto-reload)
python startup.py --debug

# Production mode
python startup.py --no-reload

# Specify custom host/port
python startup.py --host 127.0.0.1 --port 8080
```

### 4. Test API

```bash
# Health check
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Test extraction endpoint
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "fields": [
      {"name": "title", "path": "$.title"}
    ]
  }'
```

## 🔐 Security Architecture

### What's Protected

| Data Type | Protection Level | Action |
|-----------|------------------|--------|
| API Keys | 🔴 Critical | Redacted & filtered |
| Passwords | 🔴 Critical | Redacted & filtered |
| Private Keys | 🔴 Critical | Pattern detection & blocking |
| Credit Cards | 🟡 High | PII filtering |
| Email/Phone | 🟡 High | PII filtering |
| Dangerous URLs | 🟡 High | Pattern blocking |

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Input Validation                                    │
│  - URL format validation                                     │
│  - Domain whitelist check                                    │
│  - Request size limits                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Network Security                                  │
│  - HTTPS only (enforced)                                    │
│  - Rate limiting                                           │
│  - CORS configuration                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Content Filtering                                 │
│  - Credential detection & redaction                         │
│  - API key pattern matching                                │
│  - PII filtering                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Audit & Monitoring                                │
│  - Request logging                                         │
│  - Security alert tracking                                 │
│  - Compliance reporting                                    │
└─────────────────────────────────────────────────────────────┘
```

## 📊 API Endpoints

### Core Endpoints

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|------------|
| `/health` | GET | Health check | - |
| `/api/v1/extract` | POST | Extract data from URL | 60 req/min |
| `/api/v1/chat` | POST | Chat with Hermes AI | 30 req/min |
| `/api/v1/search` | GET | Search websites | 120 req/min |
| `/api/v1/metadata` | GET | Get site metadata | 300 req/min |
| `/api/v1/audit` | GET | View audit logs | 60 req/min |

### Example Request/Response

```bash
# Extract data from a website
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/products",
    "fields": [
      {"name": "product_name", "path": "$.title"},
      {"name": "price", "path": "$.price"}
    ],
    "options": {
      "timeout": 30,
      "respect_robots": true
    }
  }'

# Response
{
  "success": true,
  "request_id": "req_abc123",
  "data": {
    "product_name": "Widget A",
    "price": 29.99
  },
  "metadata": {
    "extraction_time_ms": 1250,
    "data_classification": "public"
  }
}
```

## 🛠️ Development

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

### Code Style

```bash
# Format code
black .

# Check imports
isort .

# Lint
flake8 .
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new field"

# Apply migration
alembic upgrade head
```

## 📦 Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "startup.py"]
```

### Docker Compose

```yaml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_URL=postgresql://user:pass@db/hermes
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=hermes
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hermes-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: hermes-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DB_URL
          valueFrom:
            secretKeyRef:
              name: hermes-db
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: hermes-api
spec:
  selector:
    matchLabels:
      app: hermes-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

## 📈 Monitoring

### Metrics Endpoint

```bash
# Prometheus metrics (if configured)
curl http://localhost:8000/metrics
```

### Logging

```bash
# View logs
tail -f logs/api.log

# Search logs
grep "ERROR" logs/api.log | tail -100
```

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `Connection refused` | Check if server is running: `curl http://localhost:8000/health` |
| `Permission denied` | Check file permissions: `chmod 755 .env` |
| `Database connection error` | Verify DB_URL in .env and check PostgreSQL is running |
| `Rate limit exceeded` | Wait for rate limit window or increase limits in .env |
| `CORS error` | Configure ALLOWED_ORIGINS in .env |

### Debug Mode

```bash
# Run with debug logging
DEBUG=true python startup.py

# Enable detailed error messages
LOG_LEVEL=DEBUG
```

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [Security Best Practices](https://cheatsheetseries.owasp.org/)
- [API Security Checklist](https://github.com/veracode/api-security-checklist)

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Support

- Issues: [GitHub Issues](https://github.com/yourorg/hermes-api/issues)
- Documentation: [Read the Docs](https://hermes-api.readthedocs.io/)
- Community: [Discord](https://discord.gg/hermes-api)

## 📝 Changelog

### v1.0.0 (2026-04-07)

**Initial Release**
- Core API endpoints
- Security filtering layer
- Audit logging
- PostgreSQL support
- Docker deployment
- Kubernetes support