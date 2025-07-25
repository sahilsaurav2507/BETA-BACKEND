@echo off
echo Starting Celery Worker for LawVriksh Email System...
cd /d "C:\Users\Asus\Desktop\TESTING\BETA-BACKEND"
celery -A app.tasks.email_tasks worker --loglevel=info --pool=solo
pause
