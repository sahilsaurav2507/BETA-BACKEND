#!/bin/bash

# Production Deployment Script for LawVriksh Referral Platform
# ============================================================
# This script automates the complete production deployment process
# with scientific worker configuration and optimized database pooling.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="lawvriksh-api"
APP_DIR="/opt/lawvriksh"
USER="www-data"
GROUP="www-data"
PYTHON_VERSION="3.11"
VENV_DIR="$APP_DIR/venv"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
    
    # Check Python version
    if ! command -v python$PYTHON_VERSION &> /dev/null; then
        log_error "Python $PYTHON_VERSION is not installed"
        exit 1
    fi
    
    # Check required packages
    local packages=("nginx" "mysql-server" "redis-server" "supervisor")
    for package in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            log_warning "$package is not installed. Installing..."
            apt-get update && apt-get install -y $package
        fi
    done
    
    log_success "System requirements check completed"
}

setup_user() {
    log_info "Setting up application user..."
    
    # Create user if it doesn't exist
    if ! id "$USER" &>/dev/null; then
        useradd --system --shell /bin/bash --home-dir $APP_DIR --create-home $USER
        log_success "Created user: $USER"
    else
        log_info "User $USER already exists"
    fi
    
    # Create application directory
    mkdir -p $APP_DIR
    chown -R $USER:$GROUP $APP_DIR
    
    # Create log directory
    mkdir -p /var/log/lawvriksh
    chown -R $USER:$GROUP /var/log/lawvriksh
    
    log_success "User setup completed"
}

setup_python_environment() {
    log_info "Setting up Python environment..."
    
    # Create virtual environment
    sudo -u $USER python$PYTHON_VERSION -m venv $VENV_DIR
    
    # Upgrade pip
    sudo -u $USER $VENV_DIR/bin/pip install --upgrade pip
    
    # Install production dependencies
    if [ -f "requirements.txt" ]; then
        sudo -u $USER $VENV_DIR/bin/pip install -r requirements.txt
        log_success "Installed Python dependencies"
    else
        log_warning "requirements.txt not found. Installing basic dependencies..."
        sudo -u $USER $VENV_DIR/bin/pip install fastapi uvicorn gunicorn sqlalchemy pymysql redis psutil
    fi
    
    log_success "Python environment setup completed"
}

deploy_application() {
    log_info "Deploying application code..."
    
    # Copy application files
    cp -r . $APP_DIR/app/
    chown -R $USER:$GROUP $APP_DIR/app/
    
    # Generate production configuration
    log_info "Generating production configuration..."
    cd $APP_DIR/app
    sudo -u $USER $VENV_DIR/bin/python production/start_production.py deploy
    
    # Set proper permissions
    chmod 600 .env.production
    chown $USER:$GROUP .env.production
    
    log_success "Application deployment completed"
}

setup_database() {
    log_info "Setting up database..."
    
    # Check if MySQL is running
    if ! systemctl is-active --quiet mysql; then
        systemctl start mysql
        systemctl enable mysql
    fi
    
    # Create database and user (if they don't exist)
    mysql -e "CREATE DATABASE IF NOT EXISTS lawvriksh_referral;" 2>/dev/null || true
    mysql -e "CREATE USER IF NOT EXISTS 'lawuser'@'%' IDENTIFIED BY 'lawpass123';" 2>/dev/null || true
    mysql -e "GRANT ALL PRIVILEGES ON lawvriksh_referral.* TO 'lawuser'@'%';" 2>/dev/null || true
    mysql -e "FLUSH PRIVILEGES;" 2>/dev/null || true
    
    # Run database migrations
    if [ -f "$APP_DIR/app/lawdata.sql" ]; then
        log_info "Running database migrations..."
        mysql lawvriksh_referral < $APP_DIR/app/lawdata.sql
        log_success "Database migrations completed"
    fi
    
    # Optimize MySQL for production
    log_info "Optimizing MySQL configuration..."
    cat > /etc/mysql/mysql.conf.d/lawvriksh.cnf << EOF
[mysqld]
# Connection settings
max_connections = 200
connect_timeout = 10
wait_timeout = 28800
interactive_timeout = 28800

# Buffer settings
innodb_buffer_pool_size = 256M
innodb_log_file_size = 64M
innodb_log_buffer_size = 16M
innodb_flush_log_at_trx_commit = 2

# Query cache
query_cache_type = 1
query_cache_size = 64M
query_cache_limit = 2M

# Performance
innodb_flush_method = O_DIRECT
innodb_file_per_table = 1
EOF
    
    systemctl restart mysql
    log_success "Database setup completed"
}

setup_redis() {
    log_info "Setting up Redis..."
    
    # Configure Redis for production
    cat > /etc/redis/redis.conf << EOF
bind 127.0.0.1
port 6379
timeout 300
keepalive 60
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF
    
    systemctl restart redis-server
    systemctl enable redis-server
    
    log_success "Redis setup completed"
}

setup_systemd_service() {
    log_info "Setting up systemd service..."
    
    # Copy systemd service file
    cp $APP_DIR/app/lawvriksh-api.service /etc/systemd/system/
    
    # Update service file with correct paths
    sed -i "s|/app|$APP_DIR/app|g" /etc/systemd/system/lawvriksh-api.service
    sed -i "s|User=www-data|User=$USER|g" /etc/systemd/system/lawvriksh-api.service
    sed -i "s|Group=www-data|Group=$GROUP|g" /etc/systemd/system/lawvriksh-api.service
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable $APP_NAME
    
    log_success "Systemd service setup completed"
}

setup_nginx() {
    log_info "Setting up Nginx reverse proxy..."
    
    # Create Nginx configuration
    cat > /etc/nginx/sites-available/lawvriksh << EOF
upstream lawvriksh_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://lawvriksh_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://lawvriksh_backend;
        access_log off;
    }
    
    # Static files (if any)
    location /static/ {
        alias $APP_DIR/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/lawvriksh /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test and reload Nginx
    nginx -t
    systemctl restart nginx
    systemctl enable nginx
    
    log_success "Nginx setup completed"
}

start_services() {
    log_info "Starting services..."
    
    # Start the application
    systemctl start $APP_NAME
    
    # Wait for service to start
    sleep 5
    
    # Check service status
    if systemctl is-active --quiet $APP_NAME; then
        log_success "Application service started successfully"
    else
        log_error "Failed to start application service"
        systemctl status $APP_NAME
        exit 1
    fi
    
    # Perform health check
    log_info "Performing health check..."
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_warning "Health check failed - service may still be starting"
    fi
}

show_deployment_info() {
    log_success "🎉 Production deployment completed successfully!"
    echo
    log_info "📋 Deployment Summary:"
    echo "  • Application: $APP_NAME"
    echo "  • Directory: $APP_DIR"
    echo "  • User: $USER"
    echo "  • Python: $PYTHON_VERSION"
    echo "  • Workers: $(grep GUNICORN_WORKERS $APP_DIR/app/.env.production | cut -d'=' -f2)"
    echo
    log_info "🔧 Service Management:"
    echo "  • Start:   systemctl start $APP_NAME"
    echo "  • Stop:    systemctl stop $APP_NAME"
    echo "  • Restart: systemctl restart $APP_NAME"
    echo "  • Status:  systemctl status $APP_NAME"
    echo "  • Logs:    journalctl -u $APP_NAME -f"
    echo
    log_info "🌐 Access Points:"
    echo "  • Application: http://$(hostname -I | awk '{print $1}')"
    echo "  • Health Check: http://$(hostname -I | awk '{print $1}')/health"
    echo "  • API Docs: http://$(hostname -I | awk '{print $1}')/docs"
    echo
    log_info "📊 Monitoring:"
    echo "  • System: htop, iotop"
    echo "  • Logs: tail -f /var/log/lawvriksh/app.log"
    echo "  • Database: mysql -u lawuser -p lawvriksh_referral"
}

# Main deployment process
main() {
    log_info "🚀 Starting LawVriksh production deployment..."
    
    check_requirements
    setup_user
    setup_python_environment
    deploy_application
    setup_database
    setup_redis
    setup_systemd_service
    setup_nginx
    start_services
    show_deployment_info
}

# Run main function
main "$@"
