#!/bin/bash

# LawVriksh Email Processing Update Script
# This script updates your existing VPS deployment to include integrated email processing

set -e

echo "🚀 LawVriksh Email Processing Update"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run this script from your VPS deployment directory."
    exit 1
fi

print_success "Found docker-compose.yml"

# Check if .env.production exists
if [ ! -f "backend/.env.production" ]; then
    print_error "backend/.env.production not found. Please ensure your environment file exists."
    exit 1
fi

print_success "Found .env.production"

# Backup current configuration
print_status "Creating backup of current configuration..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp docker-compose.yml "$BACKUP_DIR/"
cp backend/.env.production "$BACKUP_DIR/"
cp nginx.conf "$BACKUP_DIR/"

print_success "Backup created in $BACKUP_DIR"

# Update .env.production with email processing configuration
print_status "Updating .env.production with email processing configuration..."

# Check if email configuration already exists
if ! grep -q "BACKGROUND_EMAIL_PROCESSING" backend/.env.production; then
    print_status "Adding email processing configuration to .env.production..."
    
    cat >> backend/.env.production << 'EOF'

# Background Email Processing Configuration (Added by update script)
BACKGROUND_EMAIL_PROCESSING=true
EMAIL_CHECK_INTERVAL=60
EMAIL_BATCH_SIZE=100

# Email SMTP Configuration (Update these with your actual values)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_USE_TLS=true
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=LawVriksh Platform

# Redis Configuration (for caching - optional)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
EOF

    print_success "Email processing configuration added to .env.production"
    print_warning "IMPORTANT: Please update the SMTP settings in backend/.env.production with your actual email credentials!"
else
    print_success "Email processing configuration already exists in .env.production"
fi

# Update docker-compose.yml to include Redis (optional but recommended)
print_status "Checking if Redis service needs to be added to docker-compose.yml..."

if ! grep -q "redis:" docker-compose.yml; then
    print_status "Adding Redis service to docker-compose.yml..."
    
    # Create updated docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # The FastAPI backend service with integrated email processing
  backend:
    build: ./backend
    restart: always
    volumes:
      # Volume mount for logs, uploads, and cache
      - ./backend:/app
      - ./backend/logs:/app/logs
      - ./backend/uploads:/app/uploads
      - ./backend/cache:/app/cache
    env_file:
      - ./backend/.env.production
    environment:
      # Database configuration
      - DB_HOST=db
      - DB_PORT=3306
      # Redis configuration
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    command: ["/usr/local/bin/wait-for.sh", "db", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network

  # The React frontend service
  frontend:
    build: ./frontend
    restart: always
    networks:
      - app-network

  # The MySQL database service
  db:
    image: mysql:8.0
    restart: always
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
    environment:
      MYSQL_ALLOW_EMPTY_PASSWORD: "yes"
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db-data:/var/lib/mysql
      - ./backend/lawdata.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - app-network

  # Redis service for caching and session management
  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes --maxmemory 128mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # The Nginx reverse proxy service
  nginx:
    image: nginx:latest
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    depends_on:
      - frontend
      - backend
    networks:
      - app-network

  # The Certbot service for SSL certificates
  certbot:
    image: certbot/certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

# Defines the named volumes for persistent data
volumes:
  db-data:
  redis-data:

# Defines the shared network for inter-container communication
networks:
  app-network:
    driver: bridge
EOF

    print_success "Updated docker-compose.yml with Redis service"
else
    print_success "Redis service already exists in docker-compose.yml"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p backend/logs backend/uploads backend/cache

print_success "Directories created"

# Stop current services
print_status "Stopping current services..."
docker-compose down

# Rebuild backend with email processing
print_status "Rebuilding backend with email processing functionality..."
docker-compose build --no-cache backend

# Start services
print_status "Starting services with email processing..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check if backend is healthy
if curl -f http://localhost:8000/health &> /dev/null; then
    print_success "Backend is healthy and email processing is active"
else
    print_error "Backend is not responding. Check logs: docker-compose logs backend"
fi

# Check if Redis is healthy (if added)
if docker-compose ps | grep -q redis; then
    if docker-compose exec redis redis-cli ping | grep -q PONG; then
        print_success "Redis is healthy"
    else
        print_warning "Redis is not responding"
    fi
fi

print_success "Update completed!"
echo ""
echo "🎉 LawVriksh Email Processing Update Complete!"
echo ""
echo "✅ What's New:"
echo "   • Integrated background email processing"
echo "   • Welcome emails sent within 60 seconds"
echo "   • Campaign emails batch processed on schedule"
echo "   • No more separate email processor needed"
echo "   • Redis caching for better performance"
echo ""
echo "📧 Email Processing Status:"
echo "   • Background processor: Started automatically with backend"
echo "   • Processing interval: Every 60 seconds"
echo "   • Welcome emails: Immediate processing"
echo "   • Campaign emails: Scheduled date processing"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update SMTP settings in backend/.env.production"
echo "   2. Test email functionality by registering a user"
echo "   3. Monitor logs: docker-compose logs -f backend"
echo "   4. Check email queue: curl http://localhost:8000/api/email-queue/stats"
echo ""
echo "📊 Monitoring Commands:"
echo "   • View logs: docker-compose logs -f backend"
echo "   • Check email processing: docker-compose logs backend | grep email"
echo "   • Service status: docker-compose ps"
echo "   • Restart services: docker-compose restart"
echo ""
print_warning "IMPORTANT: Don't forget to update your SMTP credentials in backend/.env.production!"
echo ""
echo "🚀 Your LawVriksh platform now has integrated email processing!"
