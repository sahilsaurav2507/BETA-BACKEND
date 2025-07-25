@echo off
echo Starting Celery Beat Scheduler for LawVriksh Campaigns...
cd /d "C:\Users\Asus\Desktop\TESTING\BETA-BACKEND"
celery -A celery_beat_config beat --loglevel=info
pause
