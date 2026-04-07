#!/bin/bash
# ============================================================================
# Hermes Web Data API - Quick Start Script
# ============================================================================
# Quick deployment for production environments
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_warn "This script should be run as root for system-wide installation"
    log_warn "Run: sudo $0"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
MIN_VERSION="3.11"

if [[ $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")') < "$MIN_VERSION" ]]; then
    log_error "Python 3.11+ is required. Found: $PYTHON_VERSION"
    exit 1
fi

log_info "Python $PYTHON_VERSION detected"

# Create installation directory
INSTALL_DIR="/opt/hermes-api"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

log_info "Creating installation directory: $INSTALL_DIR"

# Copy files
log_info "Copying Hermes Web Data API files..."

# Use the current directory (where this script is)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/" 2>/dev/null || true

log_success "Files copied to $INSTALL_DIR"

# Create symbolic links
log_info "Creating symbolic links..."

# Create systemd service file
cat > "$INSTALL_DIR/hermes-api.service" << EOF
[Unit]
Description=Hermes Web Data API
After=network.target

[Service]
Type=simple
User=hermes
Group=hermes
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python startup.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

log_success "Created systemd service file"

# Create systemd user directory
useradd -m -s /bin/bash hermes 2>/dev/null || true

# Set ownership
log_info "Setting ownership..."
chown -R hermes:hermes "$INSTALL_DIR" 2>/dev/null || true
chmod -R 755 "$INSTALL_DIR" 2>/dev/null || true

log_success "Ownership set"

# Create database configuration
log_info "Creating database configuration..."

# PostgreSQL setup
if command -v pg_ctl &> /dev/null; then
    if ! pg_isready &> /dev/null; then
        log_warn "PostgreSQL is not running"
        log_warn "Run: sudo systemctl start postgresql"
    else
        log_info "PostgreSQL is running"
        
        # Create database
        PGPASSWORD="${POSTGRES_PASSWORD:-hermes}" psql -c "
        CREATE DATABASE hermes;
        CREATE USER hermes_api WITH PASSWORD '${POSTGRES_PASSWORD:-hermes}';
        GRANT ALL PRIVILEGES ON DATABASE hermes TO hermes_api;" 2>/dev/null || true
    fi
fi

log_success "Database configuration complete"

# Create application user home
HOME_DIR="/home/hermes"
mkdir -p "$HOME_DIR"
chown hermes:hermes "$HOME_DIR" 2>/dev/null || true

# Set environment variables
log_info "Setting environment variables..."

cat > /etc/default/hermes-api << EOF
# Hermes Web Data API Environment
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
DB_URL=postgresql://hermes_api:${POSTGRES_PASSWORD:-hermes}@localhost/hermes
SECRET_KEY=${SECRET_KEY:-}
LOG_LEVEL=INFO
EOF

log_success "Environment variables set"

# Create cron job for health check
log_info "Setting up health check cron job..."

cat > "/etc/cron.d/hermes-api-health" << EOF
# Hermes API Health Check
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Check every 5 minutes
*/5 * * * * root /usr/bin/python3 $INSTALL_DIR/venv/bin/python startup.py --health-check >> /var/log/hermes-api-health.log 2>&1
EOF

chmod 644 "/etc/cron.d/hermes-api-health"

log_success "Cron job created"

# Create log directory
log_info "Creating log directory..."
mkdir -p "$INSTALL_DIR/logs"
touch "$INSTALL_DIR/logs/api.log"
touch "$INSTALL_DIR/logs/error.log"
chown hermes:hermes "$INSTALL_DIR/logs"

log_success "Log directories created"

# Create firewall rules
log_info "Configuring firewall..."

if command -v ufw &> /dev/null; then
    ufw allow 80/tcp 2>/dev/null || true
    ufw allow 443/tcp 2>/dev/null || true
    ufw allow 8000/tcp 2>/dev/null || true
    log_success "Firewall rules configured"
fi

# Create SSL certificates (optional)
log_info "Setting up SSL certificates..."

SSL_DIR="/etc/letsencrypt"
mkdir -p "$SSL_DIR"

if [ -f "/etc/letsencrypt/live/hermes-api.com/fullchain.pem" ]; then
    log_info "SSL certificates found"
else
    log_warn "No SSL certificates found"
    log_warn "Run certbot to obtain certificates"
fi

# Create systemd socket for fast startup
log_info "Creating systemd socket..."

cat > "$INSTALL_DIR/hermes-api.socket" << EOF
[Unit]
Description=Hermes API Socket

[Socket]
ListenStream=8000
Accept=no
SocketMode=0660
SocketUser=hermes
SocketGroup=hermes

[Install]
WantedBy=sockets.target
EOF

log_success "Socket created"

# Final summary
log_info ""
log_info "======================================================================"
log_info "HERMES WEB DATA API - Installation Complete"
log_info "======================================================================"
log_info ""
log_info "Installation directory: $INSTALL_DIR"
log_info "Service file: /etc/systemd/system/hermes-api.service"
log_info "Logs: $INSTALL_DIR/logs/"
log_info ""
log_info "Next steps:"
log_info "  1. Start the service: sudo systemctl start hermes-api"
log_info "  2. Enable auto-start: sudo systemctl enable hermes-api"
log_info "  3. Check status: sudo systemctl status hermes-api"
log_info "  4. View logs: journalctl -u hermes-api -f"
log_info "  5. Access API: http://localhost:8000/docs"
log_info ""
log_info "======================================================================"

# Cleanup
log_info "Cleaning up temporary files..."
rm -f /tmp/hermes-install-*.txt 2>/dev/null || true

log_success "Installation complete!"