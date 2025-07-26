#!/bin/bash

# SSL Certificate Renewal Script for LawVriksh
# This script is called by cron when certificates are renewed

set -e

echo "🔄 Renewing SSL certificates for LawVriksh"
echo "========================================="

# Load environment variables
if [ -f ".env" ]; then
    source .env
fi

# Copy renewed certificates
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "./nginx/ssl/"
    cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "./nginx/ssl/"
    
    # Set permissions
    chown $(whoami):$(whoami) ./nginx/ssl/*.pem
    chmod 600 ./nginx/ssl/*.pem
    
    # Reload nginx
    docker-compose exec nginx nginx -s reload
    
    echo "✅ SSL certificates renewed and nginx reloaded"
else
    echo "❌ Certificate files not found"
    exit 1
fi
