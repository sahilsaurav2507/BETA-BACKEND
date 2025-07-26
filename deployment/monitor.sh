#!/bin/bash

# LawVriksh Monitoring Script
# Monitors system health and email processing

set -e

echo "📊 LawVriksh System Monitor"
echo "==========================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if services are running
check_service_health() {
    local service=$1
    local url=$2
    
    if curl -f "$url" &> /dev/null; then
        print_success "$service is healthy"
        return 0
    else
        print_error "$service is not responding"
        return 1
    fi
}

# Check Docker containers
print_status "Checking Docker containers..."
if docker-compose ps | grep -q "Up"; then
    print_success "Docker containers are running"
    docker-compose ps
else
    print_error "Some Docker containers are not running"
    docker-compose ps
fi

echo ""

# Check service health
print_status "Checking service health..."

# Backend health
check_service_health "Backend API" "http://localhost:8000/health"

# Nginx health
if curl -f "http://localhost:80" &> /dev/null || curl -f "https://localhost:443" &> /dev/null; then
    print_success "Nginx is healthy"
else
    print_error "Nginx is not responding"
fi

# MySQL health
if docker-compose exec mysql mysqladmin ping -h localhost --silent; then
    print_success "MySQL is healthy"
else
    print_error "MySQL is not healthy"
fi

# Redis health
if docker-compose exec redis redis-cli ping | grep -q PONG; then
    print_success "Redis is healthy"
else
    print_error "Redis is not healthy"
fi

echo ""

# Check email processing
print_status "Checking email processing..."

# Get email queue stats
EMAIL_STATS=$(curl -s "http://localhost:8000/api/email-queue/stats" 2>/dev/null || echo "Failed to get stats")

if [[ "$EMAIL_STATS" != "Failed to get stats" ]]; then
    print_success "Email queue API is responding"
    echo "Email Queue Stats:"
    echo "$EMAIL_STATS" | python3 -m json.tool 2>/dev/null || echo "$EMAIL_STATS"
else
    print_error "Email queue API is not responding"
fi

# Check background processor logs
print_status "Recent email processor activity:"
docker-compose logs --tail=10 backend | grep -i "background_email_processor\|email.*sent\|email.*processed" || echo "No recent email activity"

echo ""

# System resources
print_status "System resources..."

# Disk usage
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    print_warning "Disk usage is high: ${DISK_USAGE}%"
else
    print_success "Disk usage: ${DISK_USAGE}%"
fi

# Memory usage
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$MEMORY_USAGE" -gt 80 ]; then
    print_warning "Memory usage is high: ${MEMORY_USAGE}%"
else
    print_success "Memory usage: ${MEMORY_USAGE}%"
fi

# Docker container resource usage
print_status "Container resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -5

echo ""

# SSL certificate check
if [ -f "nginx/ssl/fullchain.pem" ]; then
    print_status "Checking SSL certificate..."
    CERT_EXPIRY=$(openssl x509 -enddate -noout -in nginx/ssl/fullchain.pem | cut -d= -f2)
    CERT_EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s)
    CURRENT_EPOCH=$(date +%s)
    DAYS_UNTIL_EXPIRY=$(( (CERT_EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
    
    if [ "$DAYS_UNTIL_EXPIRY" -lt 30 ]; then
        print_warning "SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
    else
        print_success "SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
    fi
fi

echo ""

# Recent errors
print_status "Recent errors in logs:"
ERROR_COUNT=$(docker-compose logs --since="1h" 2>/dev/null | grep -i "error\|exception\|failed" | wc -l)

if [ "$ERROR_COUNT" -gt 0 ]; then
    print_warning "Found $ERROR_COUNT errors in the last hour"
    echo "Recent errors:"
    docker-compose logs --since="1h" 2>/dev/null | grep -i "error\|exception\|failed" | tail -5
else
    print_success "No errors found in the last hour"
fi

echo ""

# Summary
print_status "System Summary:"
echo "   • Services: $(docker-compose ps | grep -c "Up") running"
echo "   • Disk usage: ${DISK_USAGE}%"
echo "   • Memory usage: ${MEMORY_USAGE}%"
echo "   • Recent errors: $ERROR_COUNT"

if [ -f "nginx/ssl/fullchain.pem" ]; then
    echo "   • SSL expires: $DAYS_UNTIL_EXPIRY days"
fi

echo ""
echo "🔧 Management commands:"
echo "   • View logs: docker-compose logs -f"
echo "   • Restart: docker-compose restart"
echo "   • Update: git pull && ./deploy.sh"
echo "   • Backup: ./backup.sh"
