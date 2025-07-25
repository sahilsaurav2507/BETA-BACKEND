# LawVriksh Email Queue System

## Overview

The LawVriksh Email Queue System is a pure Python, database-driven email scheduling solution that replaces Redis/Celery with a reliable, predictable email delivery system. It implements sequential 5-minute email processing to ensure consistent timing regardless of registration volume.

## Key Features

- **Sequential 5-Minute Processing**: Emails are sent exactly 5 minutes apart
- **Database-Driven**: No external dependencies like Redis or RabbitMQ
- **Reliable Delivery**: Built-in retry mechanism with error handling
- **Campaign Support**: Handles scheduled campaign emails (July 26, July 30, August 3)
- **Monitoring**: Comprehensive monitoring and admin interface
- **Scalable**: Handles high registration volumes with predictable timing

## Architecture

### Core Components

1. **Database Schema** (`email_queue` table)
2. **Email Queue Service** (`app/services/email_queue_service.py`)
3. **Email Processor Daemon** (`email_processor.py`)
4. **Monitoring Tools** (`email_queue_monitor.py`, API endpoints)
5. **Modified Registration** (Updated `auth.py` endpoints)

### Email Flow

```
User Registration → Database Queue → Email Processor → Email Sent
                                  ↓
                            5-minute delay
                                  ↓
                            Next Email Processed
```

## Installation & Setup

### 1. Database Migration

Execute the email queue migration:

```bash
# From MySQL terminal
mysql -u your_user -p your_database < BETA-SQL/add_email_queue.sql
```

Or apply the updated schema:

```bash
# Use the modified lawdata.sql which includes email_queue table
mysql -u your_user -p your_database < BETA-SQL/lawdata.sql
```

### 2. Start Email Processor

Run the email processor daemon:

```bash
# Start as daemon (recommended for production)
python email_processor.py --daemon --interval 30 --batch-size 5

# Run single batch (for testing)
python email_processor.py --batch-size 10

# Dry run (don't actually send emails)
python email_processor.py --dry-run --daemon
```

### 3. Monitor Queue

Use the monitoring script:

```bash
# Check queue status
python email_queue_monitor.py status

# View pending emails
python email_queue_monitor.py pending --limit 20

# View failed emails
python email_queue_monitor.py failed

# Check campaign status
python email_queue_monitor.py campaigns

# Retry failed email
python email_queue_monitor.py retry 123
```

## Usage Examples

### Adding Emails to Queue

```python
from app.models.email_queue import EmailType
from app.schemas.email_queue import EmailQueueCreate
from app.services.email_queue_service import add_email_to_queue

# Add welcome email
email_data = EmailQueueCreate(
    user_email="user@example.com",
    user_name="John Doe",
    email_type=EmailType.WELCOME
)
email_entry = add_email_to_queue(db, email_data)
```

### Campaign Email Management

```python
# Add campaign emails for new user
campaign_emails = add_campaign_emails_for_user(db, "user@example.com", "John Doe")

# Add campaign for all existing users
added_count = add_campaign_emails_for_all_users(db, EmailType.SEARCH_ENGINE)
```

### Queue Monitoring

```python
# Get queue statistics
stats = get_queue_stats(db)
print(f"Pending: {stats.pending_count}, Sent: {stats.sent_count}")

# Get failed emails
failed_emails = get_failed_emails(db, limit=50)

# Retry failed email
success = retry_failed_email(db, email_id)
```

## API Endpoints

### Admin Endpoints (Require admin authentication)

- `GET /email-queue/stats` - Queue statistics
- `GET /email-queue/pending` - Pending emails
- `GET /email-queue/failed` - Failed emails
- `POST /email-queue/retry/{email_id}` - Retry failed email
- `GET /email-queue/campaigns/status` - Campaign status
- `POST /email-queue/campaigns/add/{email_type}` - Add campaign for all users
- `GET /email-queue/health` - Health check

## Database Schema

### email_queue Table

```sql
CREATE TABLE email_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    email_type ENUM('welcome', 'search_engine', 'portfolio_builder', 'platform_complete'),
    subject VARCHAR(500),
    body TEXT,
    scheduled_time TIMESTAMP NOT NULL,
    status ENUM('pending', 'processing', 'sent', 'failed', 'cancelled') DEFAULT 'pending',
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes for performance
    INDEX idx_email_queue_status (status),
    INDEX idx_email_queue_scheduled_time (scheduled_time),
    INDEX idx_email_queue_status_scheduled (status, scheduled_time)
);
```

## Configuration

### Email Processor Options

- `--daemon`: Run continuously
- `--interval N`: Check interval in seconds (default: 30)
- `--batch-size N`: Emails per batch (default: 5)
- `--dry-run`: Don't send emails, just log
- `--verbose`: Enable debug logging

### Environment Variables

Uses existing email configuration from `app/core/config.py`:

- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
- `EMAIL_FROM`
- Database connection settings

## Monitoring & Maintenance

### Health Checks

1. **Queue Status**: Monitor pending/failed email counts
2. **Processing Time**: Check average processing time
3. **Error Rates**: Monitor failed email percentage
4. **Daemon Status**: Ensure email processor is running

### Common Operations

```bash
# Check if processor is running
ps aux | grep email_processor

# View recent logs
tail -f email_processor.log

# Check queue status
python email_queue_monitor.py status

# Restart processor
pkill -f email_processor.py
python email_processor.py --daemon &
```

### Troubleshooting

1. **Emails not sending**: Check email processor daemon status
2. **High failure rate**: Check SMTP configuration and network
3. **Queue backup**: Increase batch size or check for errors
4. **Database issues**: Check connection and table permissions

## Testing

Run comprehensive tests:

```bash
python test_email_queue.py
```

Tests cover:
- Basic queue operations
- Sequential 5-minute scheduling
- Campaign email functionality
- Error handling and retries
- Queue statistics
- Schedule time calculation

## Migration from Celery

The system automatically replaces Celery functionality:

1. **Registration endpoints** now use `add_email_to_queue()` instead of Celery tasks
2. **Email processor** replaces Celery workers
3. **Database queue** replaces Redis/RabbitMQ
4. **Monitoring tools** replace Celery monitoring

## Performance

- **Throughput**: Processes 12 emails per hour (5-minute intervals)
- **Reliability**: Database-backed with automatic retries
- **Scalability**: Handles unlimited registration volume
- **Predictability**: Consistent 5-minute timing regardless of load

## Security

- Admin-only access to monitoring endpoints
- Input validation on all queue operations
- SQL injection protection via SQLAlchemy ORM
- Error message sanitization in logs
