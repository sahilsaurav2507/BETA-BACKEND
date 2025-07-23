"""
Email Campaign Management API
============================

This API provides endpoints for managing LawVriksh email campaigns.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.security import get_current_admin
from app.services.email_campaign_service import (
    get_campaign_schedule,
    send_bulk_campaign_email,
    get_due_campaigns,
    is_campaign_due,
    is_campaign_in_past,
    get_future_campaigns_for_new_user,
    send_scheduled_campaign_email
)
from app.tasks.email_tasks import (
    send_bulk_campaign_task,
    send_campaign_email_task,
    process_due_campaigns_task
)
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

class CampaignSendRequest(BaseModel):
    campaign_type: str
    user_email: str = None
    user_name: str = None

class CampaignScheduleResponse(BaseModel):
    campaigns: Dict[str, Any]
    current_time: str
    due_campaigns: List[str]

class CampaignSendResponse(BaseModel):
    success: bool
    message: str
    task_id: str = None
    details: Dict[str, Any] = None

@router.get("/schedule", response_model=CampaignScheduleResponse)
def get_campaign_schedule_info(admin=Depends(get_current_admin)):
    """
    Get the complete campaign schedule information with past/future status.

    Returns:
        CampaignScheduleResponse: Campaign schedule and status
    """
    try:
        schedule = get_campaign_schedule()
        due_campaigns = get_due_campaigns()
        future_campaigns = get_future_campaigns_for_new_user()

        # Add past/future status to each campaign
        for campaign_type, details in schedule.items():
            if campaign_type == "welcome":
                details["status"] = "instant"
                details["is_past"] = False
                details["is_future"] = True
            else:
                details["is_past"] = is_campaign_in_past(campaign_type)
                details["is_future"] = not details["is_past"]
                details["status"] = "past" if details["is_past"] else "future"

        return CampaignScheduleResponse(
            campaigns=schedule,
            current_time=datetime.now().isoformat(),
            due_campaigns=due_campaigns
        )

    except Exception as e:
        logger.error(f"Failed to get campaign schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaign schedule"
        )

@router.post("/send", response_model=CampaignSendResponse)
def send_campaign(
    request: CampaignSendRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """
    Send a campaign email to a specific user or all users.
    
    Args:
        request: Campaign send request
        db: Database session
        admin: Admin user (required)
        
    Returns:
        CampaignSendResponse: Send operation result
    """
    try:
        campaign_type = request.campaign_type
        
        # Validate campaign type
        valid_campaigns = ["welcome", "search_engine", "portfolio_builder", "platform_complete"]
        if campaign_type not in valid_campaigns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid campaign type. Valid types: {valid_campaigns}"
            )
        
        # Send to specific user
        if request.user_email and request.user_name:
            task = send_campaign_email_task.delay(campaign_type, request.user_email, request.user_name)
            
            return CampaignSendResponse(
                success=True,
                message=f"Campaign '{campaign_type}' queued for {request.user_email}",
                task_id=task.id,
                details={
                    "campaign_type": campaign_type,
                    "recipient": request.user_email,
                    "send_type": "individual"
                }
            )
        
        # Send to all users
        else:
            task = send_bulk_campaign_task.delay(campaign_type)
            
            return CampaignSendResponse(
                success=True,
                message=f"Bulk campaign '{campaign_type}' queued for all users",
                task_id=task.id,
                details={
                    "campaign_type": campaign_type,
                    "send_type": "bulk"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send campaign"
        )

@router.post("/send-due", response_model=CampaignSendResponse)
def send_due_campaigns(admin=Depends(get_current_admin)):
    """
    Send all campaigns that are currently due.
    
    Args:
        admin: Admin user (required)
        
    Returns:
        CampaignSendResponse: Send operation result
    """
    try:
        task = process_due_campaigns_task.delay()
        
        return CampaignSendResponse(
            success=True,
            message="Due campaigns processing queued",
            task_id=task.id,
            details={
                "send_type": "due_campaigns",
                "note": "All due campaigns will be processed automatically"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to process due campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process due campaigns"
        )

@router.get("/status/{campaign_type}")
def get_campaign_status(campaign_type: str, admin=Depends(get_current_admin)):
    """
    Get the status of a specific campaign.
    
    Args:
        campaign_type: Type of campaign to check
        admin: Admin user (required)
        
    Returns:
        dict: Campaign status information
    """
    try:
        valid_campaigns = ["welcome", "search_engine", "portfolio_builder", "platform_complete"]
        if campaign_type not in valid_campaigns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid campaign type. Valid types: {valid_campaigns}"
            )
        
        schedule = get_campaign_schedule()
        is_due = is_campaign_due(campaign_type)
        
        campaign_info = schedule.get(campaign_type, {})
        
        return {
            "campaign_type": campaign_type,
            "subject": campaign_info.get("subject"),
            "schedule": str(campaign_info.get("schedule")),
            "status": campaign_info.get("status"),
            "is_due": is_due,
            "current_time": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign status"
        )

@router.post("/test-sahil")
def test_sahil_campaign(
    campaign_type: str = "welcome",
    admin=Depends(get_current_admin)
):
    """
    Send a test campaign email to Sahil Saurav.
    
    Args:
        campaign_type: Type of campaign to send (default: welcome)
        admin: Admin user (required)
        
    Returns:
        dict: Test send result
    """
    try:
        sahil_email = "sahilsaurav2507@gmail.com"
        sahil_name = "Sahil Saurav"
        
        valid_campaigns = ["welcome", "search_engine", "portfolio_builder", "platform_complete"]
        if campaign_type not in valid_campaigns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid campaign type. Valid types: {valid_campaigns}"
            )
        
        # Send campaign email to Sahil
        task = send_campaign_email_task.delay(campaign_type, sahil_email, sahil_name)
        
        return {
            "success": True,
            "message": f"Test campaign '{campaign_type}' sent to Sahil Saurav",
            "task_id": task.id,
            "recipient": sahil_email,
            "campaign_type": campaign_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test campaign to Sahil: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test campaign"
        )

@router.get("/new-user-campaigns")
def get_new_user_campaigns(admin=Depends(get_current_admin)):
    """
    Get campaigns that would be sent to a new user registering now.

    Args:
        admin: Admin user (required)

    Returns:
        dict: New user campaign information
    """
    try:
        future_campaigns = get_future_campaigns_for_new_user()

        campaign_details = []
        for campaign_type in future_campaigns:
            from app.services.email_campaign_service import EMAIL_TEMPLATES
            template = EMAIL_TEMPLATES[campaign_type]
            campaign_details.append({
                "campaign_type": campaign_type,
                "subject": template["subject"],
                "schedule": str(template["schedule"]),
                "is_future": True
            })

        # Check past campaigns
        past_campaigns = []
        from app.services.email_campaign_service import EMAIL_TEMPLATES
        for campaign_type, template in EMAIL_TEMPLATES.items():
            if campaign_type != "welcome" and is_campaign_in_past(campaign_type):
                past_campaigns.append({
                    "campaign_type": campaign_type,
                    "subject": template["subject"],
                    "schedule": str(template["schedule"]),
                    "is_past": True
                })

        return {
            "instant_email": {
                "campaign_type": "welcome",
                "subject": EMAIL_TEMPLATES["welcome"]["subject"],
                "will_be_sent": True,
                "note": "Always sent immediately on registration"
            },
            "future_campaigns": {
                "count": len(future_campaigns),
                "campaigns": campaign_details,
                "note": "These will be sent automatically on scheduled dates"
            },
            "past_campaigns": {
                "count": len(past_campaigns),
                "campaigns": past_campaigns,
                "note": "These will NOT be sent to new users (backdated)"
            },
            "current_time": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get new user campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get new user campaigns"
        )

@router.get("/preview/{campaign_type}")
def preview_campaign(campaign_type: str, admin=Depends(get_current_admin)):
    """
    Preview a campaign email template.

    Args:
        campaign_type: Type of campaign to preview
        admin: Admin user (required)

    Returns:
        dict: Campaign preview
    """
    try:
        from app.services.email_campaign_service import EMAIL_TEMPLATES

        if campaign_type not in EMAIL_TEMPLATES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid campaign type. Valid types: {list(EMAIL_TEMPLATES.keys())}"
            )

        template = EMAIL_TEMPLATES[campaign_type]

        # Preview with sample data
        sample_body = template["template"].format(name="[User Name]")

        is_past = is_campaign_in_past(campaign_type) if campaign_type != "welcome" else False

        return {
            "campaign_type": campaign_type,
            "subject": template["subject"],
            "body": sample_body,
            "schedule": str(template["schedule"]),
            "is_past": is_past,
            "is_future": not is_past,
            "will_be_sent_to_new_users": not is_past,
            "preview_note": "This is a preview with placeholder [User Name]"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview campaign"
        )
