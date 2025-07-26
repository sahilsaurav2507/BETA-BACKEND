#!/bin/bash

# LawVriksh Production Deployment Script
# This script deploys the LawVriksh backend with integrated email processing

set -e  # Exit on any error

echo "🚀 LawVriksh Production Deployment"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_status "Please copy .env.example to .env and configure your settings"
    exit 1
fi

print_success ".env file found"

# Load environment variables
source .env

# Validate required environment variables
required_vars=("MYSQL_ROOT_PASSWORD" "MYSQL_DATABASE" "MYSQL_USER" "MYSQL_PASSWORD" "SECRET_KEY" "DOMAIN")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set in .env file"
        exit 1
    fi
done

print_success "Environment variables validated"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Docker and Docker Compose are installed"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs/nginx
mkdir -p uploads
mkdir -p cache
mkdir -p nginx/ssl
mkdir -p mysql/init

print_success "Directories created"

# Set proper permissions
print_status "Setting permissions..."
chmod 755 logs uploads cache
chmod 700 nginx/ssl

# Stop existing containers if running
print_status "Stopping existing containers..."
docker-compose down --remove-orphans || true

# Pull latest images
print_status "Pulling latest images..."
docker-compose pull

# Build the application
print_status "Building LawVriksh backend..."
docker-compose build --no-cache backend

# Start the services
print_status "Starting services..."
docker-compose up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check MySQL
if docker-compose exec mysql mysqladmin ping -h localhost --silent; then
    print_success "MySQL is healthy"
else
    print_error "MySQL is not healthy"
    docker-compose logs mysql
    exit 1
fi

# Check Redis
if docker-compose exec redis redis-cli ping | grep -q PONG; then
    print_success "Redis is healthy"
else
    print_error "Redis is not healthy"
    docker-compose logs redis
    exit 1
fi

# Check Backend
if curl -f http://localhost:8000/health &> /dev/null; then
    print_success "Backend is healthy"
else
    print_error "Backend is not healthy"
    docker-compose logs backend
    exit 1
fi

# Check Nginx
if curl -f http://localhost:80 &> /dev/null || curl -f https://localhost:443 &> /dev/null; then
    print_success "Nginx is healthy"
else
    print_warning "Nginx may not be fully configured (SSL certificates needed)"
fi

# Show running containers
print_status "Running containers:"
docker-compose ps

# Show logs
print_status "Recent logs:"
docker-compose logs --tail=20

print_success "Deployment completed successfully!"
echo ""
echo "🎉 LawVriksh is now running with integrated email processing!"
echo ""
echo "📊 Service URLs:"
echo "   • Backend API: http://localhost:8000"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"
echo ""
echo "📧 Email Processing:"
echo "   • Background processor started automatically"
echo "   • Processes emails every 60 seconds"
echo "   • Welcome emails: Immediate processing"
echo "   • Campaign emails: Batch processing on scheduled dates"
echo ""
echo "🔧 Management Commands:"
echo "   • View logs: docker-compose logs -f"
echo "   • Restart services: docker-compose restart"
echo "   • Stop services: docker-compose down"
echo "   • Update: git pull && ./deploy.sh"
echo ""
echo "⚠️  Next Steps:"
echo "   1. Configure SSL certificates for HTTPS"
echo "   2. Set up domain DNS to point to this server"
echo "   3. Configure email SMTP settings in .env"
echo "   4. Test email functionality"
echo "   5. Set up monitoring and backups"
