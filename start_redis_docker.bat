@echo off
echo Starting Redis with Docker for LawVriksh...
docker run -d --name lawvriksh-redis -p 6379:6379 redis:alpine redis-server --requirepass Sahil@123
echo Redis started on:
echo - Host: localhost:6379
echo - Password: Sahil@123
echo - Management: Use redis-cli or Redis Desktop Manager
pause
