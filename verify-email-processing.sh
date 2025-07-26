#!/bin/bash

# LawVriksh Email Processing Verification Script
# This script verifies that the integrated email processing is working correctly

set -e

echo "🔍 LawVriksh Email Processing Verification"
echo "=========================================="

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

# Check if services are running
print_status "Checking service status..."
if docker-compose ps | grep -q "Up"; then
    print_success "Docker services are running"
    docker-compose ps
else
    print_error "Some services are not running"
    docker-compose ps
    exit 1
fi

echo ""

# Check backend health
print_status "Checking backend health..."
if curl -f http://localhost:8000/health &> /dev/null; then
    print_success "Backend is healthy"
else
    print_error "Backend is not responding"
    exit 1
fi

# Check if background email processor is running
print_status "Checking background email processor..."
EMAIL_PROCESSOR_LOGS=$(docker-compose logs backend | grep -i "background_email_processor\|email.*processor" | tail -5)

if [ -n "$EMAIL_PROCESSOR_LOGS" ]; then
    print_success "Background email processor is active"
    echo "Recent processor logs:"
    echo "$EMAIL_PROCESSOR_LOGS"
else
    print_warning "No background email processor logs found yet (may still be starting)"
fi

echo ""

# Check email queue API
print_status "Checking email queue API..."
EMAIL_QUEUE_RESPONSE=$(curl -s http://localhost:8000/api/email-queue/stats 2>/dev/null || echo "API_ERROR")

if [ "$EMAIL_QUEUE_RESPONSE" != "API_ERROR" ]; then
    print_success "Email queue API is responding"
    echo "Email queue stats:"
    echo "$EMAIL_QUEUE_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(json.dumps(data, indent=2))
except:
    print(sys.stdin.read())
" 2>/dev/null || echo "$EMAIL_QUEUE_RESPONSE"
else
    print_error "Email queue API is not responding"
fi

echo ""

# Check SMTP configuration
print_status "Checking SMTP configuration..."
SMTP_CONFIG=$(docker-compose exec -T backend python3 -c "
try:
    from app.core.config import settings
    print(f'SMTP Server: {getattr(settings, \"SMTP_SERVER\", \"Not configured\")}')
    print(f'SMTP Port: {getattr(settings, \"SMTP_PORT\", \"Not configured\")}')
    print(f'SMTP Username: {getattr(settings, \"SMTP_USERNAME\", \"Not configured\")}')
    print(f'From Email: {getattr(settings, \"FROM_EMAIL\", \"Not configured\")}')
    print(f'Background Processing: {getattr(settings, \"BACKGROUND_EMAIL_PROCESSING\", \"Not configured\")}')
except Exception as e:
    print(f'Error checking SMTP config: {e}')
" 2>/dev/null)

if [ -n "$SMTP_CONFIG" ]; then
    print_success "SMTP configuration found"
    echo "$SMTP_CONFIG"
else
    print_warning "Could not retrieve SMTP configuration"
fi

echo ""

# Check recent email activity
print_status "Checking recent email activity..."
RECENT_EMAIL_LOGS=$(docker-compose logs --since="1h" backend | grep -i "email.*sent\|email.*processed\|welcome.*email\|campaign.*email" | tail -10)

if [ -n "$RECENT_EMAIL_LOGS" ]; then
    print_success "Recent email activity found"
    echo "Recent email logs:"
    echo "$RECENT_EMAIL_LOGS"
else
    print_warning "No recent email activity (this is normal if no users have registered recently)"
fi

echo ""

# Check Redis connection (if Redis is configured)
if docker-compose ps | grep -q redis; then
    print_status "Checking Redis connection..."
    if docker-compose exec redis redis-cli ping | grep -q PONG; then
        print_success "Redis is connected and responding"
    else
        print_warning "Redis is not responding"
    fi
fi

echo ""

# System resource check
print_status "Checking system resources..."
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

echo "Memory usage: ${MEMORY_USAGE}%"
echo "Disk usage: ${DISK_USAGE}%"

if [ "$MEMORY_USAGE" -gt 80 ]; then
    print_warning "High memory usage: ${MEMORY_USAGE}%"
fi

if [ "$DISK_USAGE" -gt 80 ]; then
    print_warning "High disk usage: ${DISK_USAGE}%"
fi

echo ""

# Summary
print_status "Verification Summary"
echo "===================="

# Count checks
TOTAL_CHECKS=0
PASSED_CHECKS=0

# Backend health
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if curl -f http://localhost:8000/health &> /dev/null; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo "✅ Backend Health: PASS"
else
    echo "❌ Backend Health: FAIL"
fi

# Email queue API
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if [ "$EMAIL_QUEUE_RESPONSE" != "API_ERROR" ]; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo "✅ Email Queue API: PASS"
else
    echo "❌ Email Queue API: FAIL"
fi

# SMTP configuration
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if echo "$SMTP_CONFIG" | grep -q "SMTP Server:" && ! echo "$SMTP_CONFIG" | grep -q "Not configured"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo "✅ SMTP Configuration: PASS"
else
    echo "❌ SMTP Configuration: FAIL"
fi

# Background processor
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if [ -n "$EMAIL_PROCESSOR_LOGS" ]; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo "✅ Background Processor: PASS"
else
    echo "⚠️  Background Processor: UNKNOWN (may still be starting)"
fi

echo ""
echo "📊 Overall Score: $PASSED_CHECKS/$TOTAL_CHECKS checks passed"

if [ "$PASSED_CHECKS" -eq "$TOTAL_CHECKS" ]; then
    print_success "All checks passed! Email processing is working correctly."
elif [ "$PASSED_CHECKS" -gt $((TOTAL_CHECKS / 2)) ]; then
    print_warning "Most checks passed. Some issues may need attention."
else
    print_error "Multiple issues detected. Please review the configuration."
fi

echo ""
echo "🔧 Useful Commands:"
echo "   • View email logs: docker-compose logs -f backend | grep email"
echo "   • Check queue status: curl http://localhost:8000/api/email-queue/stats"
echo "   • Restart services: docker-compose restart"
echo "   • View all logs: docker-compose logs -f"
echo ""
echo "📧 To test email processing:"
echo "   1. Register a new user on your frontend"
echo "   2. Check logs for welcome email processing"
echo "   3. Verify email delivery"
