# LawVriksh Production Deployment Guide

## 🚀 Complete Step-by-Step VPS Deployment

This guide covers deploying the LawVriksh backend with integrated email processing on a VPS server using Docker, Docker Compose, and Nginx.

---

## **📋 Prerequisites**

### **VPS Requirements**
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: Minimum 20GB SSD
- **CPU**: 2 cores minimum
- **Network**: Public IP address

### **Domain Requirements**
- Domain name pointing to your VPS IP
- Access to DNS management
- Email address for SSL certificates

---

## **🔧 Step 1: VPS Initial Setup**

### **1.1 Connect to VPS**
```bash
ssh root@your-server-ip
```

### **1.2 Create Non-Root User**
```bash
# Create user
adduser lawvriksh
usermod -aG sudo lawvriksh

# Switch to new user
su - lawvriksh
```

### **1.3 Update System**
```bash
sudo apt update && sudo apt upgrade -y
```

### **1.4 Install Required Packages**
```bash
# Install basic tools
sudo apt install -y curl wget git unzip software-properties-common

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again to apply Docker group
exit
ssh lawvriksh@your-server-ip
```

### **1.5 Verify Installation**
```bash
docker --version
docker-compose --version
```

---

## **🔧 Step 2: Firewall Configuration**

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Check status
sudo ufw status
```

---

## **📁 Step 3: Deploy Application**

### **3.1 Clone Repository**
```bash
# Clone your repository
git clone https://github.com/yourusername/lawvriksh-backend.git
cd lawvriksh-backend/deployment
```

### **3.2 Configure Environment**
```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

### **3.3 Configure .env File**
```bash
# Database Configuration
MYSQL_ROOT_PASSWORD=your_super_secure_root_password_here
MYSQL_DATABASE=lawvriksh_db
MYSQL_USER=lawvriksh_user
MYSQL_PASSWORD=your_secure_db_password_here

# Application Security
SECRET_KEY=your_super_secret_jwt_key_minimum_32_characters_long
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip

# Frontend Configuration
FRONTEND_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email Configuration (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_USE_TLS=true
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=LawVriksh Platform

# Domain Configuration
DOMAIN=yourdomain.com
SSL_EMAIL=admin@yourdomain.com
```

### **3.4 Make Scripts Executable**
```bash
chmod +x deploy.sh ssl-setup.sh ssl-renew.sh
```

### **3.5 Deploy Application**
```bash
./deploy.sh
```

---

## **🔒 Step 4: SSL Certificate Setup**

### **4.1 Point Domain to Server**
Before setting up SSL, ensure your domain DNS is pointing to your server:
- **A Record**: `yourdomain.com` → `your-server-ip`
- **A Record**: `www.yourdomain.com` → `your-server-ip`

### **4.2 Setup SSL Certificates**
```bash
./ssl-setup.sh
```

This script will:
- Install Certbot
- Obtain Let's Encrypt SSL certificates
- Configure automatic renewal
- Update Nginx configuration

---

## **📧 Step 5: Email Configuration**

### **5.1 Gmail SMTP Setup**
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use the generated password in `SMTP_PASSWORD`

### **5.2 Custom SMTP Setup**
```bash
# For custom email server
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=your_email_password
SMTP_USE_TLS=true
```

### **5.3 Test Email Functionality**
```bash
# Check email processor logs
docker-compose logs -f backend | grep email

# Test email sending
curl -X POST "https://yourdomain.com/api/test-email" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

---

## **📊 Step 6: Monitoring and Maintenance**

### **6.1 View Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f nginx
docker-compose logs -f mysql

# Email processing logs
docker-compose logs -f backend | grep "background_email_processor"
```

### **6.2 Service Management**
```bash
# Restart services
docker-compose restart

# Stop services
docker-compose down

# Update application
git pull
docker-compose build --no-cache backend
docker-compose up -d
```

### **6.3 Database Backup**
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD lawvriksh_db > backup_$DATE.sql
gzip backup_$DATE.sql
EOF

chmod +x backup.sh

# Run backup
./backup.sh

# Schedule daily backups
(crontab -l; echo "0 2 * * * cd $(pwd) && ./backup.sh") | crontab -
```

---

## **🔍 Step 7: Verification**

### **7.1 Check Service Health**
```bash
# Backend health
curl https://yourdomain.com/health

# API documentation
curl https://yourdomain.com/docs

# Email queue status
curl https://yourdomain.com/api/email-queue/stats
```

### **7.2 Test Email Processing**
```bash
# Register a test user to trigger welcome email
curl -X POST "https://yourdomain.com/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@yourdomain.com",
    "password": "testpassword123"
  }'

# Check if welcome email was queued and processed
docker-compose logs backend | grep "welcome email"
```

---

## **⚡ Step 8: Performance Optimization**

### **8.1 Nginx Optimization**
The provided nginx.conf includes:
- Gzip compression
- Security headers
- Rate limiting
- SSL optimization
- Caching headers

### **8.2 Database Optimization**
```bash
# Add to docker-compose.yml mysql service
command: --default-authentication-plugin=mysql_native_password --innodb-buffer-pool-size=512M --max-connections=200
```

### **8.3 Application Scaling**
```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Update nginx upstream in nginx.conf
upstream lawvriksh_backend {
    server backend:8000;
    server backend:8000;
    server backend:8000;
    keepalive 32;
}
```

---

## **🚨 Troubleshooting**

### **Common Issues**

#### **Email Not Sending**
```bash
# Check email processor status
docker-compose logs backend | grep "background_email_processor"

# Check SMTP configuration
docker-compose exec backend python -c "
from app.core.config import settings
print(f'SMTP: {settings.SMTP_SERVER}:{settings.SMTP_PORT}')
print(f'User: {settings.SMTP_USERNAME}')
"
```

#### **SSL Issues**
```bash
# Check certificate files
ls -la nginx/ssl/

# Test SSL
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Renew certificates manually
sudo certbot renew --force-renewal
./ssl-renew.sh
```

#### **Database Connection Issues**
```bash
# Check MySQL logs
docker-compose logs mysql

# Test connection
docker-compose exec mysql mysql -u root -p$MYSQL_ROOT_PASSWORD -e "SHOW DATABASES;"
```

---

## **🎉 Deployment Complete!**

Your LawVriksh backend is now deployed with:

✅ **Integrated Email Processing**: Automatic background processing every 60 seconds
✅ **SSL Security**: HTTPS with automatic certificate renewal
✅ **Production Ready**: Optimized Nginx, security headers, rate limiting
✅ **Monitoring**: Comprehensive logging and health checks
✅ **Scalable**: Docker-based architecture ready for scaling

### **Access Points**
- **API**: `https://yourdomain.com/api/`
- **Documentation**: `https://yourdomain.com/docs`
- **Health Check**: `https://yourdomain.com/health`

### **Email Processing**
- **Welcome emails**: Sent within 60 seconds of registration
- **Campaign emails**: Batch processed on scheduled dates
- **Background processor**: Runs automatically with the application

Your production deployment is complete and ready for users! 🚀
