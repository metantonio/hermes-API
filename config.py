"""
Hermes Web Data API - Configuration and Settings
================================================
Production-ready configuration with security defaults.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Set, Dict, List, Optional, Any
import re

# ============================================================================
# Security Constants - API Keys and Tokens
# ============================================================================

SENSITIVE_PATTERNS: Dict[str, List[str]] = {
    "api_keys": [
        r'(?i)(api[_-]?key|apikey|access[_-]?key|secret[_-]?key|token|auth[_-]?token)\s*[=:]["\']?([^"\'\s]+)',
        r'(?i)(sk_live|sk_test|pk_live|pk_test|ghp_)[-_\w]+',
        r'(?i)(aws[_-]?access[_-]?key|aws[_-]?secret)',
        r'(?i)xox[a-z-]+-[a-z0-9]+',  # Slack tokens
        r'(?i)hubspot_access[_-]?token',
        r'(?i)microsoft[_-]?access[_-]?token',
        r'(?i)google[_-]?api[_-]?key',
    ],
    "credentials": [
        r'(?i)(username|user|admin|root)\s*[=:]["\']?\w+["\']?',
        r'(?i)password\s*[=:]["\']?\w+',
        r'(?i)passwd\s*[=:]["\']?\w+',
        r'(?i)secret\s*[=:]["\']?\w+',
        r'(?i)credential\s*[=:]["\']?\w+',
        r'(?i)access[_-]?key\s*[=:]["\']?\w+',
        r'(?i)private[_-]?key\s*[=:]["\']?\w+',
        r'(?i)api[_-]?secret\s*[=:]["\']?\w+',
    ],
    "private_keys": [
        r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----',
        r'-----BEGIN EC PRIVATE KEY-----',
        r'-----BEGIN PRIVATE KEY-----',
        r'-----BEGIN PUBLIC KEY-----',
        r'-----BEGIN CERTIFICATE-----',
    ],
    "financial": [
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit cards
        r'\b\d{16,19}\b',  # Account numbers
        r'(?i)(credit[_-]?card|account[_-]?number|cvv)\s*[=:]["\']?\d+',
        r'(?i)(iban)\s*[=:]["\']?[A-Z0-9]+',
    ],
    "dangerous": [
        r'(?i)(git|svn|hg)\s+[^\s]+',
        r'(?i)ssh-rsa\s+[^\s]+',
        r'(?i)private\s*key\s*[=:]',
    ],
}

# ============================================================================
# Security Constants
# ============================================================================

DANGEROUS_PATTERNS: List[str] = [
    r'(?i)(git|svn|hg)\s+[^\s]+',
    r'(?i)ssh-rsa\s+[^\s]+',
    r'(?i)private\s*key\s*[=:]',
]

# ============================================================================
# Data Classification Rules
# ============================================================================

DATA_CLASSIFICATION_RULES: Dict[str, List[str]] = {
    "personal": [
        r'(?i)(email|email_address|e-mail)\s*[=:]["\']?\w+@\w+\.\w+',
        r'(?i)(phone|phone_number|telephone)\s*[=:]["\']?\+?\d+',
        r'(?i)(ssn|social_security)\s*[=:]["\']?\d{3}-?\d{2}-?\d{4}',
        r'(?i)(passport)\s*[=:]["\']?[A-Z0-9]{6,9}',
    ],
    "business": [
        r'(?i)(customer_id|order_id)\s*[=:]["\']?\w+',
        r'(?i)(invoice_id|receipt_id)\s*[=:]["\']?\w+',
        r'(?i)(transaction_id)\s*[=:]["\']?\w+',
    ],
    "security": [
        r'(?i)(password|passwd|pwd)\s*[=:]["\']?\w+',
        r'(?i)(api_key|apikey)\s*[=:]["\']?\w+',
        r'(?i)(secret)\s*[=:]["\']?\w+',
    ],
}

CORS_ORIGINS: List[str] = [
    "https://yourdomain.com",
    "https://app.yourdomain.com",
]

SECURITY_HEADERS: Dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

# ============================================================================
# Rate Limiting Configuration
# ============================================================================

RATE_LIMITS: Dict[str, int] = {
    "default": 60,
    "extract": 30,
    "search": 120,
}

# ============================================================================
# Database Configuration
# ============================================================================

DB_POOL_SIZE: int = 5
DB_MAX_OVERFLOW: int = 10
DB_POOL_TIMEOUT: int = 30
DB_POOL_RECYCLE: int = 3600

# ============================================================================
# Request/Response Limits
# ============================================================================

MAX_REQUEST_SIZE: int = 10485760  # 10 MB
MAX_RESPONSE_SIZE: int = 104857600  # 100 MB
MAX_URL_LENGTH: int = 2048

# ============================================================================
# Timeouts
# ============================================================================

REQUEST_TIMEOUT: float = 30.0
CONNECT_TIMEOUT: float = 10.0
READ_TIMEOUT: float = 30.0
TOTAL_TIMEOUT: float = 60.0

# ============================================================================
# Logging Configuration
# ============================================================================

LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE: Optional[str] = None

# ============================================================================
# Audit Configuration
# ============================================================================

AUDIT_SETTINGS: Dict[str, Any] = {
    "enabled": True,
    "endpoint": "",
    "retention_days": 365,
    "log_level": "INFO",
}

# ============================================================================
# Settings Class
# ============================================================================

class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All sensitive values should be set via environment variables,
    never hardcoded or committed to source control.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Hermes Web Data API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "production")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    CONF_DIR: str = os.getenv("CONF_DIR", "./conf")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))

    # Database
    DB_URL: str = os.getenv("DB_URL", "sqlite:////home/antonio/hermes/api/hermes.db")
    DB_POOL_SIZE: int = DB_POOL_SIZE
    DB_MAX_OVERFLOW: int = DB_MAX_OVERFLOW

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    SECRET_KEY_MIN_LENGTH: int = 32
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY: int = 3600  # 1 hour

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = RATE_LIMITS["default"] > 0
    RATE_LIMIT_WINDOW: int = 60  # seconds
    RATE_LIMIT_MAX: int = RATE_LIMITS["default"]

    # CORS (use ALLOWED_ORIGINS environment variable)

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Get allowed origins from environment or default."""
        origins_str = os.getenv("ALLOWED_ORIGINS", "")
        if origins_str:
            return [o.strip() for o in origins_str.split(",") if o.strip()]
        return ["*"]  # Default to allow all for development

    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    ALLOW_CREDENTIALS: bool = SECURITY_HEADERS.get("X-Frame-Options", "") != "DENY"

    # API Keys (from environment, never hardcode)
    API_KEY: Optional[str] = None
    API_SECRET: Optional[str] = None
    API_KEY_MIN_LENGTH: int = 32
    API_KEY_MAX_LENGTH: int = 128

    # Request/Response Limits
    MAX_REQUEST_SIZE: int = MAX_REQUEST_SIZE
    MAX_RESPONSE_SIZE: int = MAX_RESPONSE_SIZE
    MAX_URL_LENGTH: int = MAX_URL_LENGTH

    # Timeouts
    REQUEST_TIMEOUT: float = REQUEST_TIMEOUT
    CONNECT_TIMEOUT: float = CONNECT_TIMEOUT
    READ_TIMEOUT: float = READ_TIMEOUT
    TOTAL_TIMEOUT: float = TOTAL_TIMEOUT

    # Logging
    LOG_LEVEL: str = AUDIT_SETTINGS["log_level"]
    LOG_FORMAT: str = LOG_FORMAT
    LOG_FILE: Optional[str] = LOG_FILE

    # Audit
    AUDIT_ENABLED: bool = AUDIT_SETTINGS["enabled"]
    AUDIT_ENDPOINT: str = AUDIT_SETTINGS["endpoint"]
    AUDIT_RETENTION_DAYS: int = AUDIT_SETTINGS["retention_days"]

    # Allowed hosts for TrustedHostMiddleware
    @property
    def ALLOWED_HOSTS(self) -> Set[str]:
        """Get allowed hosts from environment for TrustedHostMiddleware."""
        hosts_str = os.getenv("ALLOWED_HOSTS", "")
        if hosts_str:
            return {h.strip().lower() for h in hosts_str.split(",") if h.strip()}
        return {"localhost", "127.0.0.1", "0.0.0.0"}

    # Allowed domains for extraction (use environment)
    @property
    def ALLOWED_DOMAINS(self) -> Set[str]:
        """
        Parse ALLOWED_DOMAINS from environment.

        Format: "example.com,api.example.com,another.example.com"
        Returns empty set if not configured.
        """
        domains_str = os.getenv("ALLOWED_DOMAINS", "")
        if domains_str:
            return set(d.strip().lower() for d in domains_str.split(","))
        return set()

    def __repr__(self) -> str:
        """
        Return a safe string representation.

        Never expose sensitive values in logs or debug output.
        """
        safe_repr = {
            "app_name": self.APP_NAME,
            "app_version": self.APP_VERSION,
            "app_env": self.APP_ENV,
            "host": self.HOST,
            "port": self.PORT,
            "debug": self.DEBUG,
            "rate_limit_enabled": self.RATE_LIMIT_ENABLED,
            "audit_enabled": self.AUDIT_ENABLED,
            "allowed_domains_count": len(self.ALLOWED_DOMAINS),
            "allowed_origins_count": len(self.ALLOWED_ORIGINS),
        }
        return f"Settings({safe_repr!r})"


# ============================================================================
# Utility Functions
# ============================================================================

@lru_cache(maxsize=128)
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to avoid reloading settings on each request.
    """
    return Settings()


def sanitize_error_message(error: str) -> str:
    """
    Sanitize error messages to prevent information leakage.

    Never expose internal details, stack traces, or system paths.
    """
    # Remove file paths
    sanitized = re.sub(r'file://[\w./\-]+', '[FILE_PATH]', error)
    sanitized = re.sub(r'/[\w./\-]+', '[PATH]', sanitized)

    # Remove stack traces
    sanitized = re.sub(r'at [\w.]+:\d+', '[STACK_FRAME]', sanitized)
    sanitized = re.sub(r'#\d+', '[LINE]', sanitized)

    # Remove environment variables
    sanitized = re.sub(r'[\w_]+=[^@]+', '[ENV_VAR]', sanitized)

    # Limit length
    return sanitized[:1000]


def mask_sensitive_value(value: str, show_chars: int = 4) -> str:
    """
    Mask sensitive values for logging and debugging.

    Example: "secret_key_abc123" -> "secret_key_****"
    """
    if len(value) <= show_chars:
        return "*" * len(value)

    return value[:show_chars] + "*" * (len(value) - show_chars)


def validate_url(url: str, max_length: int = MAX_URL_LENGTH) -> bool:
    """
    Validate URL format and length.

    Returns True if URL is valid and within limits.
    """
    if not url:
        return False

    if len(url) > max_length:
        return False

    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        reconstructed = urlunparse(parsed)
        return reconstructed.lower() == url.lower() or parsed.path == url
    except Exception:
        return False


def init_config() -> Settings:
    """Initialize and validate configuration."""
    settings = Settings()
    
    # Validate settings
    if settings.AUDIT_ENABLED and not settings.AUDIT_ENDPOINT:
        raise ValueError("AUDIT_ENDPOINT is required when audit is enabled")
    
    # Validate ALLOWED_DOMAINS if configured
    if settings.ALLOWED_DOMAINS and any("." not in d for d in settings.ALLOWED_DOMAINS):
        raise ValueError("ALLOWED_DOMAINS must contain valid domain names")
    
    return settings


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("Hermes Web Data API - Configuration Module")
    print("=" * 50)
    settings = init_config()
    print(f"Application: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.APP_ENV}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print(f"Allowed domains: {len(settings.ALLOWED_DOMAINS)}")
    print(f"Allowed origins: {len(settings.ALLOWED_ORIGINS)}")
    print(f"Rate limiting: {settings.RATE_LIMIT_ENABLED}")
    print(f"Audit logging: {settings.AUDIT_ENABLED}")
    print("=" * 50)
