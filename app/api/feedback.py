import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import csv
import json
import io

from app.core.dependencies import get_db
from app.core.security import get_current_admin, verify_access_token
from app.models.feedback import Feedback
from app.models.user import User
from app.schemas.feedback import (
    FeedbackCreate, FeedbackResponse, FeedbackListResponse, 
    FeedbackStatsResponse, FeedbackSubmitResponse, FeedbackFilters,
    ExportFormat, HURDLE_LABELS, MOTIVATION_LABELS, TIME_CONSUMING_LABELS, FEAR_LABELS
)

router = APIRouter(prefix="/feedback", tags=["feedback"])
logger = logging.getLogger(__name__)

@router.post("/submit", response_model=FeedbackSubmitResponse)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Submit feedback survey response.
    Can be submitted anonymously or by authenticated users.
    """
    try:
        # Get user ID if authenticated (optional)
        user_id = None
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                payload = verify_access_token(token)
                if payload:
                    user_id = payload.get("user_id")
        except:
            # Anonymous submission is allowed
            pass
        
        # Get client IP address
        client_ip = request.client.host
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Get user agent
        user_agent = request.headers.get("user-agent", "")
        
        # Note: 24-hour submission restriction has been removed to allow multiple submissions
        
        # Create feedback record
        feedback = Feedback(
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            email=feedback_data.email,
            name=feedback_data.name,
            biggest_hurdle=feedback_data.biggest_hurdle,
            biggest_hurdle_other=feedback_data.biggest_hurdle_other,
            primary_motivation=feedback_data.primary_motivation,
            time_consuming_part=feedback_data.time_consuming_part,
            professional_fear=feedback_data.professional_fear,
            monetization_considerations=feedback_data.monetization_considerations,
            professional_legacy=feedback_data.professional_legacy,
            platform_impact=feedback_data.platform_impact
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        logger.info(f"Feedback submitted successfully. ID: {feedback.id}, User ID: {user_id}, IP: {client_ip}")
        
        return FeedbackSubmitResponse(
            success=True,
            message="Feedback submitted successfully. Thank you for your valuable insights!",
            feedback_id=feedback.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback. Please try again later."
        )

@router.get("", response_model=FeedbackListResponse)
async def get_feedback_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    biggest_hurdle: Optional[str] = Query(None),
    primary_motivation: Optional[str] = Query(None),
    professional_fear: Optional[str] = Query(None),
    time_consuming_part: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get paginated list of feedback responses (admin only).
    """
    try:
        # Build query
        query = db.query(Feedback).join(User, Feedback.user_id == User.id, isouter=True)
        
        # Apply filters
        if search:
            search_filter = or_(
                Feedback.monetization_considerations.ilike(f"%{search}%"),
                Feedback.professional_legacy.ilike(f"%{search}%"),
                Feedback.platform_impact.ilike(f"%{search}%"),
                Feedback.biggest_hurdle_other.ilike(f"%{search}%"),
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if biggest_hurdle:
            query = query.filter(Feedback.biggest_hurdle == biggest_hurdle)
        
        if primary_motivation:
            query = query.filter(Feedback.primary_motivation == primary_motivation)
        
        if professional_fear:
            query = query.filter(Feedback.professional_fear == professional_fear)
        
        if time_consuming_part:
            query = query.filter(Feedback.time_consuming_part == time_consuming_part)
        
        if start_date:
            query = query.filter(Feedback.submitted_at >= start_date)
        
        if end_date:
            query = query.filter(Feedback.submitted_at <= end_date)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        feedback_list = query.order_by(Feedback.submitted_at.desc()).offset(offset).limit(page_size).all()
        
        # Convert to response format
        feedback_responses = []
        for feedback in feedback_list:
            response = FeedbackResponse(
                id=feedback.id,
                user_id=feedback.user_id,
                ip_address=feedback.ip_address,
                email=feedback.email,
                name=feedback.name,
                biggest_hurdle=feedback.biggest_hurdle,
                biggest_hurdle_other=feedback.biggest_hurdle_other,
                primary_motivation=feedback.primary_motivation,
                time_consuming_part=feedback.time_consuming_part,
                professional_fear=feedback.professional_fear,
                monetization_considerations=feedback.monetization_considerations,
                professional_legacy=feedback.professional_legacy,
                platform_impact=feedback.platform_impact,
                submitted_at=feedback.submitted_at,
                updated_at=feedback.updated_at,
                user_name=feedback.user.name if feedback.user else None,
                user_email=feedback.user.email if feedback.user else None
            )
            feedback_responses.append(response)
        
        return FeedbackListResponse(
            feedback=feedback_responses,
            pagination={
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching feedback list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback data"
        )

@router.get("/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get feedback statistics and analytics (admin only).
    """
    try:
        # Get total responses
        total_responses = db.query(func.count(Feedback.id)).scalar()
        
        # Get breakdown by categories
        hurdle_stats = db.query(
            Feedback.biggest_hurdle,
            func.count(Feedback.id)
        ).group_by(Feedback.biggest_hurdle).all()
        
        motivation_stats = db.query(
            Feedback.primary_motivation,
            func.count(Feedback.id)
        ).group_by(Feedback.primary_motivation).all()
        
        time_stats = db.query(
            Feedback.time_consuming_part,
            func.count(Feedback.id)
        ).group_by(Feedback.time_consuming_part).all()
        
        fear_stats = db.query(
            Feedback.professional_fear,
            func.count(Feedback.id)
        ).group_by(Feedback.professional_fear).all()
        
        # Get recent activity
        now = datetime.now(timezone.utc)
        last_7_days = db.query(func.count(Feedback.id)).filter(
            Feedback.submitted_at >= now - timedelta(days=7)
        ).scalar()
        
        last_30_days = db.query(func.count(Feedback.id)).filter(
            Feedback.submitted_at >= now - timedelta(days=30)
        ).scalar()
        
        # Get date range
        date_range = db.query(
            func.min(Feedback.submitted_at),
            func.max(Feedback.submitted_at)
        ).first()
        
        return FeedbackStatsResponse(
            total_responses=total_responses or 0,
            responses_by_hurdle={str(hurdle): count for hurdle, count in hurdle_stats},
            responses_by_motivation={str(motivation): count for motivation, count in motivation_stats},
            responses_by_time_consuming_part={str(part): count for part, count in time_stats},
            responses_by_fear={str(fear): count for fear, count in fear_stats},
            recent_responses=last_7_days or 0,
            responses_last_7_days=last_7_days or 0,
            responses_last_30_days=last_30_days or 0,
            first_response=date_range[0] if date_range[0] else None,
            latest_response=date_range[1] if date_range[1] else None
        )
        
    except Exception as e:
        logger.error(f"Error fetching feedback stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback statistics"
        )

@router.get("/export")
async def export_feedback(
    format: ExportFormat = Query(ExportFormat.CSV),
    search: Optional[str] = Query(None),
    biggest_hurdle: Optional[str] = Query(None),
    primary_motivation: Optional[str] = Query(None),
    professional_fear: Optional[str] = Query(None),
    time_consuming_part: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Export feedback data in CSV or JSON format (admin only).
    """
    try:
        # Build query (same as get_feedback_list)
        query = db.query(Feedback).join(User, Feedback.user_id == User.id, isouter=True)

        # Apply filters
        if search:
            search_filter = or_(
                Feedback.monetization_considerations.ilike(f"%{search}%"),
                Feedback.professional_legacy.ilike(f"%{search}%"),
                Feedback.platform_impact.ilike(f"%{search}%"),
                Feedback.biggest_hurdle_other.ilike(f"%{search}%"),
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        if biggest_hurdle:
            query = query.filter(Feedback.biggest_hurdle == biggest_hurdle)

        if primary_motivation:
            query = query.filter(Feedback.primary_motivation == primary_motivation)

        if professional_fear:
            query = query.filter(Feedback.professional_fear == professional_fear)

        if time_consuming_part:
            query = query.filter(Feedback.time_consuming_part == time_consuming_part)

        if start_date:
            query = query.filter(Feedback.submitted_at >= start_date)

        if end_date:
            query = query.filter(Feedback.submitted_at <= end_date)

        # Get all feedback data
        feedback_list = query.order_by(Feedback.submitted_at.desc()).all()

        if format == ExportFormat.CSV:
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Write headers
            headers = [
                'ID', 'User ID', 'Email', 'Name', 'User Name', 'User Email', 'IP Address',
                'Biggest Hurdle', 'Biggest Hurdle (Text)', 'Biggest Hurdle Other',
                'Primary Motivation', 'Primary Motivation (Text)',
                'Time Consuming Part', 'Time Consuming Part (Text)',
                'Professional Fear', 'Professional Fear (Text)',
                'Monetization Considerations', 'Professional Legacy', 'Platform Impact',
                'Submitted At', 'Updated At'
            ]
            writer.writerow(headers)

            # Write data
            for feedback in feedback_list:
                row = [
                    feedback.id,
                    feedback.user_id or '',
                    feedback.email or '',
                    feedback.name or '',
                    feedback.user.name if feedback.user else '',
                    feedback.user.email if feedback.user else '',
                    feedback.ip_address or '',
                    feedback.biggest_hurdle.value,
                    HURDLE_LABELS.get(feedback.biggest_hurdle.value, ''),
                    feedback.biggest_hurdle_other or '',
                    feedback.primary_motivation.value if feedback.primary_motivation else '',
                    MOTIVATION_LABELS.get(feedback.primary_motivation.value, '') if feedback.primary_motivation else '',
                    feedback.time_consuming_part.value if feedback.time_consuming_part else '',
                    TIME_CONSUMING_LABELS.get(feedback.time_consuming_part.value, '') if feedback.time_consuming_part else '',
                    feedback.professional_fear.value,
                    FEAR_LABELS.get(feedback.professional_fear.value, ''),
                    feedback.monetization_considerations or '',
                    feedback.professional_legacy or '',
                    feedback.platform_impact,
                    feedback.submitted_at.isoformat(),
                    feedback.updated_at.isoformat()
                ]
                writer.writerow(row)

            output.seek(0)

            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
            )

        else:  # JSON format
            export_data = []
            for feedback in feedback_list:
                data = {
                    'id': feedback.id,
                    'user_id': feedback.user_id,
                    'email': feedback.email,
                    'name': feedback.name,
                    'user_name': feedback.user.name if feedback.user else None,
                    'user_email': feedback.user.email if feedback.user else None,
                    'ip_address': feedback.ip_address,
                    'biggest_hurdle': {
                        'value': feedback.biggest_hurdle.value,
                        'label': HURDLE_LABELS.get(feedback.biggest_hurdle.value, '')
                    },
                    'biggest_hurdle_other': feedback.biggest_hurdle_other,
                    'primary_motivation': {
                        'value': feedback.primary_motivation.value if feedback.primary_motivation else None,
                        'label': MOTIVATION_LABELS.get(feedback.primary_motivation.value, '') if feedback.primary_motivation else None
                    } if feedback.primary_motivation else None,
                    'time_consuming_part': {
                        'value': feedback.time_consuming_part.value if feedback.time_consuming_part else None,
                        'label': TIME_CONSUMING_LABELS.get(feedback.time_consuming_part.value, '') if feedback.time_consuming_part else None
                    } if feedback.time_consuming_part else None,
                    'professional_fear': {
                        'value': feedback.professional_fear.value,
                        'label': FEAR_LABELS.get(feedback.professional_fear.value, '')
                    },
                    'monetization_considerations': feedback.monetization_considerations,
                    'professional_legacy': feedback.professional_legacy,
                    'platform_impact': feedback.platform_impact,
                    'submitted_at': feedback.submitted_at.isoformat(),
                    'updated_at': feedback.updated_at.isoformat()
                }
                export_data.append(data)

            json_data = json.dumps(export_data, indent=2)

            return StreamingResponse(
                io.BytesIO(json_data.encode('utf-8')),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
            )

    except Exception as e:
        logger.error(f"Error exporting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export feedback data"
        )
