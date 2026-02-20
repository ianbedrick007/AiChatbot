@echo off
REM Run Docker container with environment variables from .env file

echo Starting FastAPI application with environment variables...
docker run -p 8080:8080 --env-file .env fastwebapp

pause
