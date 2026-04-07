#!/bin/bash
# ============================================================================
# Hermes Web Data API - Installation Script
# ============================================================================
# This script installs and configures the Hermes Web Data API
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        MIN_VERSION="3.10"
        
        if [[ $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")') < "$MIN_VERSION" ]]; then
            log_error "Python 3.10 or higher is required. Found: $PYTHON_VERSION"
            return 1
        fi
        
        log_info "Python $PYTHON_VERSION detected"
        return 0
    else
        log_error "Python 3 is not installed"
        return 1
    fi
}

check_pip() {
    if command -v pip3 &> /dev/null; then
        log_info "pip3 detected"
        return 0
    else
        log_error "pip3 is not installed"
        return 1
    fi
}

create_venv() {
    log_info "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        log_warn "Virtual environment 'venv' already exists"
        read -p "Remove existing venv? (y/n): " -n 1 -s
        echo
        
        if [[ "$REPLY" =~ ^[Yy]$ ]]; then
            rm -rf venv
        else
            log_warn "Skipping virtual environment creation"
            return 0
        fi
    fi
    
    python3 -m venv venv
    log_success "Virtual environment created"
}

activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        log_info "Activating virtual environment..."
        source venv/bin/activate
        
        if command -v pip &> /dev/null; then
            log_info "Pip is ready"
        else
            log_error "Pip not found in virtual environment"
            return 1
        fi
    else
        log_error "Virtual environment not found"
        return 1
    fi
}

install_dependencies() {
    log_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        log_info "Installing from requirements.txt..."
        
        if command -v pip &> /dev/null; then
            pip install --upgrade pip setuptools wheel
            pip install -r requirements.txt --no-cache-dir
            
            if [ $? -eq 0 ]; then
                log_success "Dependencies installed successfully"
            else
                log_error "Failed to install dependencies"
                return 1
            fi
        else
            log_error "pip not found"
            return 1
        fi
    else
        log_error "requirements.txt not found"
        return 1
    fi
}

configure_environment() {
    log_info "Setting up environment..."
    
    if [ -f ".env" ]; then
        log_warn ".env file already exists"
        read -p "Overwrite existing .env? (y/n): " -n 1 -s
        echo
        
        if [[ "$REPLY" =~ ^[Yy]$ ]]; then
            rm -f .env
        else
            log_info "Keeping existing .env"
            return 0
        fi
    fi
    
    # Copy .env.example if it exists
    if [ -f ".env.example" ]; then
        cp .env.example .env
        
        log_info "Created .env from .env.example"
        log_info "Edit .env to configure your settings"
        
        # Generate SECRET_KEY if not set
        if [ ! -f ".env" ] || [ "$(grep -c "SECRET_KEY" .env)" -eq 0 ]; then
            log_info "Generating SECRET_KEY..."
            SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
            sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
            log_success "SECRET_KEY generated"
        fi
    else
        log_warn ".env.example not found, skipping environment setup"
    fi
}

verify_installation() {
    log_info "Verifying installation..."
    
    checks=0
    passed=0
    
    # Check Python
    if command -v python3 &> /dev/null; then
        ((checks++))
        if python3 --version &> /dev/null; then
            ((passed++))
        fi
    fi
    
    # Check pip
    if command -v pip &> /dev/null; then
        ((checks++))
        if pip --version &> /dev/null; then
            ((passed++))
        fi
    fi
    
    # Check virtual environment
    if [ -d "venv" ]; then
        ((checks++))
        if [ -f "venv/bin/python" ]; then
            ((passed++))
        fi
    fi
    
    # Check requirements
    if [ -f "requirements.txt" ]; then
        ((checks++))
        if [ -f "venv/lib/python*/site-packages/fastapi" ]; then
            ((passed++))
        fi
    fi
    
    log_info "Verification complete: $passed/$checks checks passed"
    
    if [ $passed -eq $checks ]; then
        log_success "Installation verified successfully"
        return 0
    else
        log_error "Verification failed"
        return 1
    fi
}

print_summary() {
    echo ""
    echo "======================================================================"
    echo "HERMES WEB DATA API - Installation Complete"
    echo "======================================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Edit .env file to configure settings"
    echo "  2. Configure database connection (DB_URL in .env)"
    echo "  3. Run tests: python test_api.py"
    echo "  4. Start server: python startup.py"
    echo ""
    echo "Documentation:"
    echo "  - README.md for detailed instructions"
    echo "  - .env.example for configuration reference"
    echo ""
    echo "======================================================================"
}

# ============================================================================
# Main Script
# ============================================================================

main() {
    echo ""
    echo "======================================================================"
    echo "HERMES WEB DATA API - Installation"
    echo "======================================================================"
    echo ""
    
    # Check Python
    if ! check_python; then
        echo ""
        log_error "Python installation failed"
        exit 1
    fi
    
    # Check pip
    if ! check_pip; then
        echo ""
        log_error "pip installation failed"
        exit 1
    fi
    
    # Create virtual environment
    create_venv
    
    # Activate virtual environment
    activate_venv
    
    # Install dependencies
    install_dependencies
    
    # Configure environment
    configure_environment
    
    # Verify installation
    if verify_installation; then
        print_summary
    else
        log_error "Installation failed"
        exit 1
    fi
}

# Run main function
main "$@"