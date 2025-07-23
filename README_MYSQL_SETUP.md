# MySQL Database Setup for Lawvriksh Backend

This guide will help you set up MySQL database for the Lawvriksh referral platform.

## Prerequisites

1. **MySQL Server 8.0+** installed and running
2. **Python 3.11+** with virtual environment activated
3. **PyMySQL** library (will be installed automatically)

## Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
# Run the automated setup script
python setup_mysql_db.py
```

This script will:
- Check MySQL client availability
- Test connection to MySQL server
- Execute the `lawdata.sql` file
- Verify the setup

### Option 2: Manual Setup

1. **Start MySQL Server**
   ```bash
   # Windows (if MySQL is installed as service)
   net start mysql
   
   # macOS (using Homebrew)
   brew services start mysql
   
   # Linux (systemd)
   sudo systemctl start mysql
   ```

2. **Execute SQL File**
   ```bash
   mysql -u root -p < lawdata.sql
   ```

3. **Verify Setup**
   ```bash
   python test_db_connection.py
   ```

## Database Configuration

The application is configured to use:

- **Database**: `lawvriksh_referral`
- **User**: `lawuser`
- **Password**: `lawpass123`
- **Host**: `localhost`
- **Port**: `3306`

### Connection String
```
mysql+pymysql://lawuser:lawpass123@localhost:3306/lawvriksh_referral
```

## What Gets Created

### Database Structure
- **Database**: `lawvriksh_referral`
- **Tables**: `users`, `share_events`
- **User**: `lawuser@%` with full privileges

### Sample Data
- **5 Users** including 1 admin user
- **10 Share Events** across different platforms
- **Admin Login**: `admin@lawvriksh.com` / `password123`

### Advanced Features
- **Stored Procedures**: User stats management, leaderboard, ranking
- **Triggers**: Automatic point calculation on share events
- **Views**: User statistics, platform analytics
- **Indexes**: Optimized for performance

## Testing the Setup

### 1. Test Database Connection
```bash
python test_db_connection.py
```

### 2. Check Database Schema
```bash
python check_db_schema.py
```

### 3. Start the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access API Documentation
Open: http://localhost:8000/docs

## Troubleshooting

### Common Issues

1. **MySQL Server Not Running**
   ```
   Error: Can't connect to MySQL server
   Solution: Start MySQL server
   ```

2. **Access Denied**
   ```
   Error: Access denied for user 'lawuser'
   Solution: Check credentials or run setup script as root
   ```

3. **Database Doesn't Exist**
   ```
   Error: Unknown database 'lawvriksh_referral'
   Solution: Run the lawdata.sql file
   ```

4. **Port Already in Use**
   ```
   Error: Port 3306 already in use
   Solution: Check if MySQL is already running or change port
   ```

### Reset Database
If you need to reset the database:

```bash
# Connect to MySQL as root
mysql -u root -p

# Drop and recreate
DROP DATABASE IF EXISTS lawvriksh_referral;
DROP USER IF EXISTS 'lawuser'@'%';

# Then run setup again
python setup_mysql_db.py
```

## Production Considerations

For production deployment:

1. **Change Default Passwords**
   - Update `lawuser` password
   - Update admin user password

2. **Secure MySQL Installation**
   ```bash
   mysql_secure_installation
   ```

3. **Configure Firewall**
   - Restrict MySQL port access
   - Use SSL connections

4. **Backup Strategy**
   - Set up regular database backups
   - Test restore procedures

5. **Performance Tuning**
   - Configure MySQL for your server specs
   - Monitor query performance
   - Optimize indexes as needed

## Environment Variables

Update your `.env` file:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://lawuser:lawpass123@localhost:3306/lawvriksh_referral
DB_USER=lawuser
DB_PASSWORD=lawpass123
DB_NAME=lawvriksh_referral
DB_HOST=localhost
DB_PORT=3306
```

## Support

If you encounter issues:

1. Check MySQL error logs
2. Run the test scripts for diagnostics
3. Verify network connectivity
4. Check MySQL user permissions

For additional help, refer to the MySQL documentation or contact the development team.
