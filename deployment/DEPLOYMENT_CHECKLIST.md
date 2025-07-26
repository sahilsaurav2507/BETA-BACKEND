# LawVriksh Production Deployment Checklist

## 📋 Pre-Deployment Checklist

### **VPS Setup**
- [ ] VPS provisioned (2GB+ RAM, 20GB+ SSD, Ubuntu 20.04+)
- [ ] SSH access configured
- [ ] Non-root user created with sudo privileges
- [ ] Firewall configured (ports 22, 80, 443)
- [ ] Docker and Docker Compose installed
- [ ] Domain name purchased and DNS configured

### **Domain & DNS**
- [ ] A record: `yourdomain.com` → `server-ip`
- [ ] A record: `www.yourdomain.com` → `server-ip`
- [ ] DNS propagation verified (use `dig yourdomain.com`)

### **Email Configuration**
- [ ] SMTP server details obtained
- [ ] Email credentials configured
- [ ] App-specific password generated (if using Gmail)
- [ ] Test email account available for testing

---

## 🚀 Deployment Steps

### **Step 1: Server Preparation**
```bash
# Connect to server
ssh lawvriksh@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y curl wget git unzip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again
exit && ssh lawvriksh@your-server-ip
```

### **Step 2: Application Deployment**
```bash
# Clone repository
git clone https://github.com/yourusername/lawvriksh-backend.git
cd lawvriksh-backend/deployment

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# Make scripts executable
chmod +x *.sh

# Deploy application
./deploy.sh
```

### **Step 3: SSL Setup**
```bash
# Setup SSL certificates
./ssl-setup.sh
```

### **Step 4: Verification**
```bash
# Check services
./monitor.sh

# Test API
curl https://yourdomain.com/health
curl https://yourdomain.com/docs

# Test email functionality
# Register a test user and check logs
```

---

## ✅ Post-Deployment Verification

### **Service Health Checks**
- [ ] Backend API responding: `https://yourdomain.com/health`
- [ ] API documentation accessible: `https://yourdomain.com/docs`
- [ ] SSL certificate valid and auto-renewal configured
- [ ] All Docker containers running: `docker-compose ps`
- [ ] Database connection working
- [ ] Redis cache working

### **Email Processing Verification**
- [ ] Background email processor started automatically
- [ ] SMTP configuration working
- [ ] Welcome email template loading correctly
- [ ] Campaign email templates loading correctly
- [ ] Email queue processing every 60 seconds
- [ ] Test user registration triggers welcome email
- [ ] Email logs showing successful processing

### **Security Verification**
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] Security headers present
- [ ] Rate limiting working
- [ ] Firewall configured correctly
- [ ] Non-root user running containers
- [ ] Sensitive files protected

### **Performance Verification**
- [ ] API response times acceptable (<500ms)
- [ ] Database queries optimized
- [ ] Nginx compression working
- [ ] Static files cached properly
- [ ] Memory usage reasonable (<80%)
- [ ] Disk usage reasonable (<80%)

---

## 🔧 Maintenance Setup

### **Monitoring**
- [ ] Log rotation configured
- [ ] Monitoring script scheduled: `./monitor.sh`
- [ ] Health check endpoints working
- [ ] Error alerting configured (optional)

### **Backups**
- [ ] Backup script tested: `./backup.sh`
- [ ] Daily backup cron job configured
- [ ] Backup retention policy set (30 days default)
- [ ] Backup restoration tested

### **Updates**
- [ ] Update procedure documented
- [ ] Git repository access configured
- [ ] Deployment script tested
- [ ] Rollback procedure documented

---

## 📧 Email System Verification

### **Welcome Email Flow**
1. [ ] User registers → Welcome email queued immediately
2. [ ] Background processor picks up email within 60 seconds
3. [ ] Email sent successfully via SMTP
4. [ ] Email status updated to 'sent'
5. [ ] User receives welcome email

### **Campaign Email Flow**
1. [ ] Campaign emails scheduled for future dates
2. [ ] Multiple users with same campaign date
3. [ ] On scheduled date, all emails processed together
4. [ ] Sequential sending without delays
5. [ ] All users receive campaign emails

### **Email Processing Logs**
```bash
# Check background processor logs
docker-compose logs backend | grep "background_email_processor"

# Check email sending logs
docker-compose logs backend | grep "email.*sent"

# Check email queue status
curl https://yourdomain.com/api/email-queue/stats
```

---

## 🚨 Troubleshooting Guide

### **Common Issues**

#### **Services Not Starting**
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check memory
free -h

# Restart services
docker-compose restart
```

#### **SSL Issues**
```bash
# Check certificate files
ls -la nginx/ssl/

# Test SSL
openssl s_client -connect yourdomain.com:443

# Renew certificates
sudo certbot renew --force-renewal
./ssl-renew.sh
```

#### **Email Not Sending**
```bash
# Check SMTP configuration
docker-compose exec backend python -c "
from app.core.config import settings
print(f'SMTP: {settings.SMTP_SERVER}:{settings.SMTP_PORT}')
"

# Check email processor
docker-compose logs backend | grep email

# Test SMTP connection
telnet smtp.gmail.com 587
```

#### **Database Issues**
```bash
# Check MySQL logs
docker-compose logs mysql

# Test connection
docker-compose exec mysql mysql -u root -p

# Check database size
docker-compose exec mysql mysql -u root -p -e "
SELECT table_schema AS 'Database',
ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
GROUP BY table_schema;
"
```

---

## 📊 Success Metrics

### **Performance Targets**
- [ ] API response time: <500ms average
- [ ] Welcome email delivery: <2 minutes
- [ ] Campaign email processing: 100% on scheduled date
- [ ] System uptime: >99.9%
- [ ] SSL certificate: Valid and auto-renewing

### **Email Processing Targets**
- [ ] Welcome emails: 100% delivery rate
- [ ] Campaign emails: 100% delivery rate
- [ ] Processing time: <60 seconds per batch
- [ ] Queue processing: Every 60 seconds
- [ ] Error rate: <1%

---

## 🎉 Deployment Complete!

Once all items are checked, your LawVriksh backend is successfully deployed with:

✅ **Production-ready infrastructure**
✅ **Integrated email processing**
✅ **SSL security**
✅ **Monitoring and backups**
✅ **Scalable architecture**

Your users will now receive:
- **Welcome emails within 60 seconds** of registration
- **Campaign emails on scheduled dates**
- **Professional, reliable email delivery**

**Congratulations! Your LawVriksh platform is live! 🚀**
