#!/bin/bash

# SSL Certificate Setup Script for LawVriksh
# Sets up Let's Encrypt SSL certificates using Certbot

set -e

echo "🔒 SSL Certificate Setup for LawVriksh"
echo "====================================="

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

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    exit 1
fi

# Load environment variables
source .env

# Validate required variables
if [ -z "$DOMAIN" ] || [ -z "$SSL_EMAIL" ]; then
    print_error "DOMAIN and SSL_EMAIL must be set in .env file"
    exit 1
fi

print_status "Setting up SSL for domain: $DOMAIN"
print_status "Contact email: $SSL_EMAIL"

# Install Certbot if not already installed
if ! command -v certbot &> /dev/null; then
    print_status "Installing Certbot..."
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y certbot python3-certbot-nginx
    else
        print_error "Unsupported package manager. Please install Certbot manually."
        exit 1
    fi
    
    print_success "Certbot installed"
else
    print_success "Certbot is already installed"
fi

# Stop Nginx temporarily to allow Certbot to bind to port 80
print_status "Stopping Nginx temporarily..."
docker-compose stop nginx

# Obtain SSL certificate
print_status "Obtaining SSL certificate..."
sudo certbot certonly \
    --standalone \
    --email "$SSL_EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

if [ $? -eq 0 ]; then
    print_success "SSL certificate obtained successfully"
else
    print_error "Failed to obtain SSL certificate"
    docker-compose start nginx
    exit 1
fi

# Copy certificates to nginx directory
print_status "Copying certificates to nginx directory..."
sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "./nginx/ssl/"
sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "./nginx/ssl/"

# Set proper permissions
sudo chown $(whoami):$(whoami) ./nginx/ssl/*.pem
chmod 600 ./nginx/ssl/*.pem

print_success "Certificates copied and permissions set"

# Update nginx configuration with correct domain
print_status "Updating nginx configuration..."
sed -i "s/yourdomain.com/$DOMAIN/g" ./nginx/nginx.conf

# Start Nginx with SSL
print_status "Starting Nginx with SSL..."
docker-compose start nginx

# Test SSL configuration
sleep 5
if curl -f "https://$DOMAIN/health" &> /dev/null; then
    print_success "SSL is working correctly!"
else
    print_warning "SSL may not be working. Check nginx logs: docker-compose logs nginx"
fi

# Set up automatic renewal
print_status "Setting up automatic certificate renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --deploy-hook 'cd $(pwd) && ./ssl-renew.sh'") | crontab -

print_success "SSL setup completed!"
echo ""
echo "🔒 SSL Certificate Information:"
echo "   • Domain: $DOMAIN"
echo "   • Certificate location: /etc/letsencrypt/live/$DOMAIN/"
echo "   • Nginx SSL files: ./nginx/ssl/"
echo "   • Auto-renewal: Configured (runs daily at 12:00)"
echo ""
echo "🌐 Your site should now be accessible at:"
echo "   • https://$DOMAIN"
echo "   • https://www.$DOMAIN"
echo ""
echo "⚠️  Note: Make sure your domain DNS is pointing to this server's IP address"
