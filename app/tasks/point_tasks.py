from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.RABBITMQ_URL,
    backend=settings.RABBITMQ_URL
)

@celery_app.task
def update_user_points_task(user_id: int, platform: str):
    from app.services.share_service import calculate_and_update_points
    return calculate_and_update_points(user_id, platform) 