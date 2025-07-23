# LawVriksh Referral Platform Backend

A production-ready FastAPI backend for a referral platform with user registration, email automation, social sharing gamification, and leaderboard functionality.

## 🚀 Features

- **User Management**: Registration, authentication, profile management
- **Social Sharing**: Multi-platform share tracking (Facebook, Twitter, LinkedIn, Instagram)
- **Gamification**: Platform-specific points system with first-share-only rewards
- **Leaderboard**: Real-time ranking with caching and pagination
- **Email Automation**: Welcome emails and bulk email campaigns
- **Admin Panel**: User management, analytics, and bulk operations
- **Monitoring**: Prometheus metrics and comprehensive logging
- **Rate Limiting**: Per-IP rate limiting for API protection
- **Caching**: DiskCache for leaderboard performance optimization

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   MySQL 8.0+    │    │   RabbitMQ      │
│   (Gunicorn)    │◄──►│   Database      │    │   Message Queue │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DiskCache     │    │   Prometheus    │    │   Celery        │
│   (Local Cache) │    │   Monitoring    │    │   Background    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- MySQL 8.0+
- RabbitMQ 3.8+
- Docker & Docker Compose (for containerized deployment)

## 🛠️ Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Setup

Run the MySQL schema file in MySQL Workbench:

```sql
-- Execute the lawdata.sql file
source lawdata.sql;
```

Or use the provided Docker Compose:

```bash
docker-compose up -d mysql
```

### 3. Environment Configuration

Create a `.env` file by copying the example:

```bash
cp .env.example .env
```

Then edit the `.env` file with your configuration:

```env
# Database Configuration (Option 1: Individual parameters)
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
DB_HOST=localhost
DB_PORT=3306

# Database Configuration (Option 2: Direct URL - takes precedence)
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/lawvriksh_referral

# Security (IMPORTANT: Generate a secure key for production!)
JWT_SECRET_KEY=your-super-secret-key-here-make-it-long-and-random

# Message Queue
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Email Configuration
EMAIL_FROM=info@lawvriksh.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Application Settings
CACHE_DIR=./cache
```

**Validate your configuration:**
```bash
python validate_config.py
```

### 4. Run the Application

#### Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### Docker Deployment
```bash
docker-compose up -d
```

## 🧪 Testing

### Run Tests
```bash
pip install -r requirements-test.txt
pytest
```

### Run with Coverage
```bash
pytest --cov=app tests/
```

## 📚 API Documentation

### Authentication Endpoints

#### POST /auth/signup
Register a new user.

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

#### POST /auth/login
Authenticate user and get JWT token.

```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

#### GET /auth/me
Get current user information.

### Share Endpoints

#### POST /shares/{platform}
Share on a specific platform (facebook, twitter, linkedin, instagram).

**Points System:**
- Twitter: 1 point
- Instagram: 2 points
- Facebook: 3 points
- LinkedIn: 5 points

*Note: Points awarded only for first share per platform.*

#### GET /shares/history
Get user's share history with pagination.

#### GET /shares/analytics
Get share analytics and platform breakdown.

### Leaderboard Endpoints

#### GET /leaderboard
Get global leaderboard with pagination.

#### GET /leaderboard/around-me
Get leaderboard around current user's rank.

#### GET /leaderboard/top-performers
Get top performers for different time periods.

### Admin Endpoints

#### POST /admin/login
Admin authentication.

#### GET /admin/dashboard
Admin dashboard with platform analytics.

#### GET /admin/users
View all users (admin only).

#### POST /admin/promote
Promote user to admin (admin only).

#### POST /admin/send-bulk-email
Send bulk email to users (admin only).

### User Endpoints

#### GET /users/{user_id}/profile
Get user profile by ID.

#### PUT /users/profile
Update current user's profile.

#### GET /users/view
View all users (admin only).

#### GET /users/export
Export users data as CSV/JSON (admin only).

## 🔧 Configuration

### Platform Points Configuration

Edit `app/services/share_service.py`:

```python
PLATFORM_POINTS = {
    PlatformEnum.twitter: 1,
    PlatformEnum.instagram: 2,
    PlatformEnum.linkedin: 5,
    PlatformEnum.facebook: 3
}
```

### Rate Limiting

Edit `app/main.py`:

```python
RATE_LIMIT = 60  # requests per minute
```

### Cache Configuration

Edit `app/utils/cache.py`:

```python
cache = Cache(settings.CACHE_DIR, size_limit=int(2e9))  # 2GB limit
```

## 📊 Monitoring

### Prometheus Metrics

Access metrics at `/metrics`:

- `api_requests_total`: Total API requests by method, endpoint, and status
- `api_request_duration_seconds`: Request latency
- `user_signup_total`: User signup count
- `share_event_total`: Share event count
- `bulk_email_sent_total`: Bulk email count
- `admin_promotion_total`: Admin promotion count

### Health Check

```bash
curl http://localhost:8000/health
```

## 🐳 Docker Deployment

### Build and Run
```bash
docker-compose up -d
```

### Services
- **Backend**: FastAPI application on port 8000
- **MySQL**: Database on port 3306
- **RabbitMQ**: Message queue on port 5672
- **Prometheus**: Monitoring on port 9090
- **Grafana**: Dashboard on port 3000

### Environment Variables
All environment variables are configured in `docker-compose.yml`.

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting per IP
- CORS configuration
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy

## 📈 Performance Optimizations

- Database indexing on frequently queried columns
- Leaderboard caching with DiskCache
- Connection pooling for database
- Background task processing with Celery
- Efficient SQL queries with proper joins

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check MySQL service is running
   - Verify DATABASE_URL in .env
   - Ensure database exists

2. **Email Sending Fails**
   - Verify SMTP credentials
   - Check firewall settings
   - Use app passwords for Gmail

3. **Cache Issues**
   - Ensure cache directory is writable
   - Check disk space
   - Restart application to clear cache

### Logs

Check application logs for detailed error information:

```bash
tail -f logs/app.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact: info@lawvriksh.com

---

**Built with ❤️ for LawVriksh** 