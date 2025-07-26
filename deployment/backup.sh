#!/bin/bash

# LawVriksh Backup Script
# Creates backups of database and application data

set -e

echo "💾 LawVriksh Backup Script"
echo "========================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment variables
if [ -f ".env" ]; then
    source .env
else
    print_error ".env file not found!"
    exit 1
fi

# Create backup directory
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$DATE"

mkdir -p "$BACKUP_PATH"

print_status "Creating backup in $BACKUP_PATH"

# Backup database
print_status "Backing up MySQL database..."
docker-compose exec -T mysql mysqldump \
    -u root \
    -p"$MYSQL_ROOT_PASSWORD" \
    --single-transaction \
    --routines \
    --triggers \
    "$MYSQL_DATABASE" > "$BACKUP_PATH/database.sql"

if [ $? -eq 0 ]; then
    print_success "Database backup completed"
    gzip "$BACKUP_PATH/database.sql"
else
    print_error "Database backup failed"
    exit 1
fi

# Backup uploaded files
if [ -d "uploads" ]; then
    print_status "Backing up uploaded files..."
    tar -czf "$BACKUP_PATH/uploads.tar.gz" uploads/
    print_success "Uploads backup completed"
fi

# Backup logs
if [ -d "logs" ]; then
    print_status "Backing up logs..."
    tar -czf "$BACKUP_PATH/logs.tar.gz" logs/
    print_success "Logs backup completed"
fi

# Backup configuration
print_status "Backing up configuration..."
cp .env "$BACKUP_PATH/"
cp docker-compose.yml "$BACKUP_PATH/"
cp -r nginx/ "$BACKUP_PATH/"

print_success "Configuration backup completed"

# Create backup info file
cat > "$BACKUP_PATH/backup_info.txt" << EOF
LawVriksh Backup Information
===========================
Date: $(date)
Server: $(hostname)
Database: $MYSQL_DATABASE
Backup Size: $(du -sh "$BACKUP_PATH" | cut -f1)

Files Included:
- database.sql.gz (MySQL dump)
- uploads.tar.gz (User uploads)
- logs.tar.gz (Application logs)
- .env (Environment configuration)
- docker-compose.yml (Docker configuration)
- nginx/ (Nginx configuration)

Restore Instructions:
1. Extract files to deployment directory
2. Restore database: gunzip -c database.sql.gz | docker-compose exec -T mysql mysql -u root -p[password] [database]
3. Extract uploads: tar -xzf uploads.tar.gz
4. Restart services: docker-compose restart
EOF

# Calculate total backup size
BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
print_success "Backup completed successfully!"
print_status "Backup location: $BACKUP_PATH"
print_status "Backup size: $BACKUP_SIZE"

# Clean up old backups (keep last 30 days)
if [ -n "$BACKUP_RETENTION_DAYS" ]; then
    RETENTION_DAYS=$BACKUP_RETENTION_DAYS
else
    RETENTION_DAYS=30
fi

print_status "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true

print_success "Backup process completed!"
echo ""
echo "📁 Backup Details:"
echo "   Location: $BACKUP_PATH"
echo "   Size: $BACKUP_SIZE"
echo "   Retention: $RETENTION_DAYS days"
echo ""
echo "🔄 To restore this backup:"
echo "   1. cd $BACKUP_PATH"
echo "   2. Follow instructions in backup_info.txt"
