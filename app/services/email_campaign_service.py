"""
LawVriksh Email Campaign Service
===============================

This service manages the scheduled email campaigns for LawVriksh Beta Launch.

Campaign Schedule:
1. Mail 1: Welcome (Instant - on signup)
2. Mail 2: Search Engine Complete (July 26, 2025, 2:00 PM IST)
3. Mail 3: Portfolio Builder Complete (July 30, 2025, 10:30 AM IST)
4. Mail 4: Platform Complete & Launch (August 3, 2025, 9:00 AM IST)
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.services.email_service import send_email
from app.core.dependencies import get_db
from datetime import datetime, timezone
import pytz
import logging

logger = logging.getLogger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Email campaign templates
EMAIL_TEMPLATES = {
    "welcome": {
        "subject": "✨ Welcome Aboard, LawVriksh Founding Member!",
        "template": """
Dear {name},

A huge, heartfelt **CONGRATULATIONS** for becoming one of our exclusive LawVriksh Beta Testing Founding Members! 🎉

Welcome aboard! We're absolutely thrilled to have you join our growing community of forward-thinking legal professionals and enthusiasts. By registering with LawVriksh, you've taken the first monumental step towards unlocking a wealth of legal knowledge, connecting with brilliant peers, and staying not just ahead, but **leading** in the ever-evolving legal landscape.

We're incredibly committed to providing you with invaluable resources and unparalleled opportunities to grow, learn, and connect. Your insights as a founding member will be crucial in shaping LawVriksh into the ultimate platform for the legal community.

**🎯 Help Us Build Something Amazing for You!**

As a valued founding member, your feedback is absolutely essential in creating a platform that truly serves your needs. We've prepared a brief survey that will help us understand your challenges, goals, and vision for the future of legal knowledge sharing.

**👉 Please take 5 minutes to share your insights:** https://lawvriksh.com/feedback

Your responses will directly influence how we develop features, prioritize improvements, and ensure LawVriksh becomes the game-changing platform you deserve. Every piece of feedback matters, and we're genuinely excited to hear your perspective!

Get ready for an exciting journey! We'll be in touch very soon with more updates and access details.

Warmly,
The LawVriksh Team

---
🌐 Visit us: https://www.lawvriksh.com
📧 Contact: info@lawvriksh.com
💬 Share your feedback: https://lawvriksh.com/feedback
        """,
        "schedule": "instant"  # Send immediately on signup
    },
    
    "search_engine": {
        "subject": "🚀 Big News! Our Powerful Legal Content Search Engine is officially completed!",
        "template": """
Hello {name},

Get ready to be amazed! We're bursting with excitement to share some incredible news: **our cutting-edge Legal Content Search Engine is officially complete!** 🥳

We've poured our hearts into building a search experience that will transform how you find legal information. Imagine instantly accessing vast legal resources, articles, case studies, and more, all with unparalleled speed and precision. No more endless digging – just the answers you need, right at your fingertips!

This is a massive step forward for LawVriksh, and we can't wait for you to experience its power. We'll be rolling out access to this feature very soon for our founding members.

Stay tuned for more updates – the best is yet to come!

Cheers,
The LawVriksh Team

---
🌐 Visit us: https://www.lawvriksh.com
📧 Contact: info@lawvriksh.com
        """,
        "schedule": datetime(2025, 7, 26, 14, 0, 0, tzinfo=IST)  # July 26, 2025, 2:00 PM IST
    },
    
    "portfolio_builder": {
        "subject": "🌟 Another Milestone Achieved! Your Professional Digital Portfolio Awaits!",
        "template": """
Hi {name},

Hold onto your hats, because we have **more** thrilling news to share! We're absolutely ecstatic to announce that **our innovative Digital Portfolio Builder is now complete!** 🤩

We know how vital it is to present your expertise and achievements in the legal world. That's why we've crafted a seamless, intuitive tool that allows you to build a stunning, professional online portfolio that truly reflects your skills, experience, and unique contributions. Stand out from the crowd and make your mark with ease!

This feature is designed to empower content creators, and we're so excited for you to get your hands on it. Details on how to access and start building your portfolio will be shared with our founding members shortly.

The LawVriksh vision is rapidly coming to life, and you're at the forefront!

Best regards,
The LawVriksh Team

---
🌐 Visit us: https://www.lawvriksh.com
📧 Contact: info@lawvriksh.com
        """,
        "schedule": datetime(2025, 7, 30, 10, 30, 0, tzinfo=IST)  # July 30, 2025, 10:30 AM IST
    },
    
    "platform_complete": {
        "subject": "🎉 LawVriksh is Complete! Get Ready for Launch & Your Exclusive Benefits!",
        "template": """
Dear {name},

The moment we've all been working towards is finally here! We are absolutely overjoyed to announce that **the entire LawVriksh platform is now complete!** 🥳

Every piece of the puzzle, from the powerful content search engine to the dynamic digital portfolio builder, and all the incredible community features in between, is polished and ready.

This is a monumental achievement, and it's all thanks to the anticipation and support of amazing founding members like you! We're now moving full steam ahead towards our official launch.

As promised, as a founding beta member, you will receive **exclusive benefits and early access** that others won't. We're putting the final touches on everything to ensure a seamless and impactful experience for you from day one.

Get ready to revolutionize your legal journey with LawVriksh! We'll be sending out the grand launch details and your special access information very, very soon.

Thank you for being an integral part of this incredible journey!

Warmest regards,
The LawVriksh Team

---
🌐 Visit us: https://www.lawvriksh.com
📧 Contact: info@lawvriksh.com
🚀 Beta Access: Coming Soon!
        """,
        "schedule": datetime(2025, 8, 3, 9, 0, 0, tzinfo=IST)  # August 3, 2025, 9:00 AM IST
    }
}

def send_welcome_email_campaign(user_email: str, user_name: str):
    """
    Send the instant welcome email when user signs up.
    Also send any past-due scheduled emails instantly.

    Args:
        user_email: User's email address
        user_name: User's name
    """
    try:
        # Send welcome email immediately
        template = EMAIL_TEMPLATES["welcome"]
        subject = template["subject"]
        body = template["template"].format(name=user_name)
        send_email(user_email, subject, body)
        logger.info(f"Welcome email sent to {user_email} ({user_name})")

        # Check for past-due scheduled emails and send them instantly
        current_time = datetime.now(IST)
        past_due_campaigns = []

        for campaign_type, template in EMAIL_TEMPLATES.items():
            if campaign_type == "welcome":
                continue  # Skip welcome email (already sent)

            schedule_time = template["schedule"]
            if schedule_time != "instant" and current_time >= schedule_time:
                past_due_campaigns.append(campaign_type)

        # Send past-due campaigns instantly
        for campaign_type in past_due_campaigns:
            try:
                send_scheduled_campaign_email(campaign_type, user_email, user_name)
                logger.info(f"Past-due campaign '{campaign_type}' sent instantly to {user_email}")
            except Exception as e:
                logger.error(f"Failed to send past-due campaign '{campaign_type}' to {user_email}: {e}")

        if past_due_campaigns:
            logger.info(f"Sent {len(past_due_campaigns)} past-due campaigns to {user_email}: {past_due_campaigns}")

        return True

    except Exception as e:
        logger.error(f"Failed to send welcome email campaign to {user_email}: {e}")
        return False

def send_scheduled_campaign_email(campaign_type: str, user_email: str, user_name: str):
    """
    Send a scheduled campaign email.
    
    Args:
        campaign_type: Type of campaign (search_engine, portfolio_builder, platform_complete)
        user_email: User's email address
        user_name: User's name
    """
    try:
        if campaign_type not in EMAIL_TEMPLATES:
            logger.error(f"Unknown campaign type: {campaign_type}")
            return False
        
        template = EMAIL_TEMPLATES[campaign_type]
        subject = template["subject"]
        body = template["template"].format(name=user_name)
        
        # Send email
        send_email(user_email, subject, body)
        
        logger.info(f"Campaign email '{campaign_type}' sent to {user_email} ({user_name})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send campaign email '{campaign_type}' to {user_email}: {e}")
        return False

def send_bulk_campaign_email(campaign_type: str, db: Session):
    """
    Send campaign email to all active users, but only if the campaign is not in the past.

    Args:
        campaign_type: Type of campaign to send
        db: Database session
    """
    try:
        # Check if campaign is in the past
        if is_campaign_in_past(campaign_type):
            logger.warning(f"Campaign '{campaign_type}' is in the past. Skipping bulk send.")
            return 0, 0

        # Get all active non-admin users
        users = db.query(User).filter(
            User.is_active == True,
            User.is_admin == False
        ).all()

        logger.info(f"Sending '{campaign_type}' campaign to {len(users)} users")

        success_count = 0
        failed_count = 0

        for user in users:
            if send_scheduled_campaign_email(campaign_type, user.email, user.name):
                success_count += 1
            else:
                failed_count += 1

        logger.info(f"Campaign '{campaign_type}' completed: {success_count} sent, {failed_count} failed")
        return success_count, failed_count

    except Exception as e:
        logger.error(f"Failed to send bulk campaign '{campaign_type}': {e}")
        return 0, 0

def get_campaign_schedule():
    """
    Get the complete campaign schedule.
    
    Returns:
        dict: Campaign schedule information
    """
    schedule = {}
    
    for campaign_type, template in EMAIL_TEMPLATES.items():
        schedule[campaign_type] = {
            "subject": template["subject"],
            "schedule": template["schedule"],
            "status": "pending" if template["schedule"] != "instant" else "instant"
        }
    
    return schedule

def is_campaign_due(campaign_type: str) -> bool:
    """
    Check if a campaign is due to be sent.
    
    Args:
        campaign_type: Type of campaign to check
        
    Returns:
        bool: True if campaign is due
    """
    if campaign_type not in EMAIL_TEMPLATES:
        return False
    
    template = EMAIL_TEMPLATES[campaign_type]
    schedule_time = template["schedule"]
    
    if schedule_time == "instant":
        return False  # Instant emails are sent immediately, not scheduled
    
    # Check if current time is past the scheduled time
    current_time = datetime.now(IST)
    return current_time >= schedule_time

def is_campaign_in_past(campaign_type: str) -> bool:
    """
    Check if a campaign's scheduled time is in the past.

    Args:
        campaign_type: Type of campaign to check

    Returns:
        bool: True if campaign is in the past
    """
    if campaign_type not in EMAIL_TEMPLATES:
        return False

    template = EMAIL_TEMPLATES[campaign_type]
    schedule_time = template["schedule"]

    if schedule_time == "instant":
        return False  # Instant emails are never in the past

    # Check if scheduled time is in the past
    current_time = datetime.now(IST)
    return current_time > schedule_time

def get_future_campaigns_for_new_user() -> list:
    """
    Get list of campaigns that should be sent to new users (only future campaigns).

    Returns:
        list: List of campaign types that are in the future
    """
    future_campaigns = []

    for campaign_type in EMAIL_TEMPLATES.keys():
        if campaign_type == "welcome":
            continue  # Welcome is handled separately

        if not is_campaign_in_past(campaign_type):
            future_campaigns.append(campaign_type)

    return future_campaigns

def send_future_campaigns_to_new_user(user_email: str, user_name: str):
    """
    Send only future scheduled campaigns to a new user.
    This is called when a user registers after some campaigns have already passed.

    Args:
        user_email: User's email address
        user_name: User's name
    """
    try:
        future_campaigns = get_future_campaigns_for_new_user()

        if not future_campaigns:
            logger.info(f"No future campaigns to send to new user {user_email}")
            return True

        logger.info(f"Sending {len(future_campaigns)} future campaigns to new user {user_email}")

        success_count = 0
        for campaign_type in future_campaigns:
            if send_scheduled_campaign_email(campaign_type, user_email, user_name):
                success_count += 1
                logger.info(f"Future campaign '{campaign_type}' sent to {user_email}")
            else:
                logger.error(f"Failed to send future campaign '{campaign_type}' to {user_email}")

        logger.info(f"Sent {success_count}/{len(future_campaigns)} future campaigns to {user_email}")
        return success_count == len(future_campaigns)

    except Exception as e:
        logger.error(f"Failed to send future campaigns to {user_email}: {e}")
        return False

def get_due_campaigns():
    """
    Get list of campaigns that are due to be sent (not in the past, but due now).

    Returns:
        list: List of campaign types that are due
    """
    due_campaigns = []

    for campaign_type in EMAIL_TEMPLATES.keys():
        if campaign_type != "welcome" and is_campaign_due(campaign_type) and not is_campaign_in_past(campaign_type):
            due_campaigns.append(campaign_type)

    return due_campaigns
