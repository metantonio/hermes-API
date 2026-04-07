#!/usr/bin/env python3
"""
Hermes Web Data API - Main Entry Point
======================================
Production-ready API server for web data extraction.
"""

import os
import sys
import signal
import logging
from typing import Optional, List
from datetime import datetime, timezone

# Add API directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
from main import app
from config import get_settings, init_config
from security_filter import create_security_filter, SecurityFilter
from models import (
    create_database_engine,
    create_tables,
    get_session_maker,
    init_db,
)


# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    include_request: bool = False
) -> None:
    """
    Setup application logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs
        include_request: Include request details in logs
    """
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logging.getLogger().addHandler(file_handler)
    
    # Configure API logger
    api_logger = logging.getLogger("hermes.api")
    api_logger.setLevel(level)
    
    # Add request logging middleware (already in main.py)
    if include_request:
        from main import app
        @app.middleware("http")
        async def log_requests(request, call_next):
            """Log all requests"""
            start_time = datetime.now(timezone.utc)
            
            logger = logging.getLogger("hermes.api")
            logger.info(
                f"Request: {request.method} {request.url.path}",
                extra={
                    "request_id": str(request.headers.get("x-request-id", "unknown")),
                    "client_ip": request.client.host,
                    "user_agent": request.headers.get("user-agent", "")[:100],
                }
            )
            
            response = await call_next(request)
            duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            logger.info(
                f"Response: {response.status_code} ({duration:.0f}ms)",
                extra={
                    "request_id": str(request.headers.get("x-request-id", "unknown")),
                    "response_size": len(response.body) if hasattr(response, "body") else 0,
                }
            )
            
            return response


# ============================================================================
# Application Startup
# ============================================================================

def create_app(
    debug: bool = False,
    host: str = "0.0.0.0",
    port: int = 8000,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    db_url: Optional[str] = None,
    create_db: bool = False,
    health_check: bool = True
) -> tuple:
    """
    Create and configure the FastAPI application.
    
    Args:
        debug: Enable debug mode
        host: Server host
        port: Server port
        log_level: Log level
        log_file: Optional log file path
        db_url: Database connection URL
        create_db: Create database tables on startup
        health_check: Enable health check endpoint
    
    Returns:
        Tuple of (FastAPI app, settings)
    """
    print("=" * 60)
    print("HERMES WEB DATA API - Starting")
    print("=" * 60)
    
    # 1. Initialize configuration
    print("\n[1/6] Initializing configuration...")
    try:
        settings = get_settings()
        settings.validate()
        print(f"  ✓ Configuration loaded from environment")
        print(f"    App: {settings.APP_NAME} v{settings.APP_VERSION}")
        print(f"    Environment: {settings.APP_ENV}")
        print(f"    Host: {host}:{port}")
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        sys.exit(1)
    
    # 2. Setup logging
    print("\n[2/6] Setting up logging...")
    setup_logging(
        level=log_level,
        log_file=log_file,
        include_request=True
    )
    print(f"  ✓ Logging configured (level: {log_level})")
    
    # 3. Create security filter
    print("\n[3/6] Initializing security filter...")
    security_filter = create_security_filter(
        strict_mode=True,
        log_level=log_level
    )
    print(f"  ✓ Security filter initialized")
    
    # 4. Initialize database
    print("\n[4/6] Initializing database...")
    if db_url:
        engine = create_database_engine(
            url=db_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
        )
        if create_db:
            create_tables(engine)
        print(f"  ✓ Database initialized ({db_url})")
    else:
        print("  ⚠ No database URL provided (using in-memory)")
    
    # 5. Create FastAPI app
    print("\n[5/6] Creating FastAPI application...")
    
    # Configure CORS
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Configure security headers
    from fastapi import Request
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        """Add security headers to all responses"""
        response = await call_next(request)
        
        # Add security headers
        security_headers_dict = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        
        for header, value in security_headers_dict.items():
            response.headers.set(header, value)
        
        return response
    
    print(f"  ✓ FastAPI app created")
    print(f"  ✓ CORS configured")
    print(f"  ✓ Security headers added")
    
    # 6. Register routes
    print("\n[6/6] Registering routes...")
    
    # Health check
    if health_check:
        @app.get("/health", tags=["System"])
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": settings.APP_VERSION,
            }
    
    # API routes (already defined in main.py)
    print(f"  ✓ Routes registered")
    
    print("\n" + "=" * 60)
    print("HERMES WEB DATA API - Ready to Accept Requests")
    print("=" * 60)
    print(f"  URL: http://{host}:{port}")
    print(f"  Docs: http://{host}:{port}/docs")
    print(f"  Redoc: http://{host}:{port}/redoc")
    print("=" * 60)
    
    return app, settings


# ============================================================================
# Server Runner
# ============================================================================

def run_server(
    debug: bool = False,
    host: str = "0.0.0.0",
    port: int = 8000,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    db_url: Optional[str] = None,
    create_db: bool = False,
    reload: bool = True
) -> None:
    """
    Run the FastAPI server.
    
    Args:
        debug: Enable debug mode
        host: Server host
        port: Server port
        log_level: Log level
        log_file: Optional log file path
        db_url: Database connection URL
        create_db: Create database tables on startup
        reload: Enable auto-reload for development
    """
    import uvicorn
    
    # Create app
    app, settings = create_app(
        debug=debug,
        host=host,
        port=port,
        log_level=log_level,
        log_file=log_file,
        db_url=db_url,
        create_db=create_db,
    )
    
    # Configure uvicorn server
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if debug else "info",
        access_log=True,
        workers=4 if not debug else 1,
    )
    
    server = uvicorn.Server(config)
    
    # Handle signals for graceful shutdown
    def handle_signal(sig, frame):
        """Handle shutdown signals"""
        print(f"\n{'=' * 60}")
        print(f"Received shutdown signal: {sig}")
        print(f"Shutting down Hermes Web Data API...")
        print(f"{'=' * 60}")
        server.should_exit = True
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Run server
    print(f"\nStarting server on {host}:{port}...\n")
    server.run()


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Hermes Web Data API - Production-ready web data extraction"
    )
    
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "0.0.0.0"),
        help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Server port (default: 8000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level (default: INFO)"
    )
    parser.add_argument(
        "--log-file",
        help="Optional log file path"
    )
    parser.add_argument(
        "--db-url",
        help="Database connection URL"
    )
    parser.add_argument(
        "--create-db",
        action="store_true",
        help="Create database tables on startup"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload (production)"
    )
    
    args = parser.parse_args()
    
    # Run server
    run_server(
        debug=args.debug,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        log_file=args.log_file,
        db_url=args.db_url,
        create_db=args.create_db,
        reload=not args.no_reload,
    )


if __name__ == "__main__":
    main()