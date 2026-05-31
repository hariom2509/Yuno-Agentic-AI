Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Yuno AI Agent Orchestration Platform  " -ForegroundColor Cyan
Write-Host "        Unified Docker Automation        " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Clean up old container if running
Write-Host "`n[1/3] Cleaning up old container..." -ForegroundColor Yellow
$oldContainer = docker ps -a -q --filter "name=yuno_app"
if ($oldContainer) {
    Write-Host "Stopping and removing existing 'yuno_app' container..." -ForegroundColor Gray
    docker stop yuno_app | Out-Null
    docker rm yuno_app | Out-Null
} else {
    Write-Host "No existing container found." -ForegroundColor Gray
}

# 2. Build the unified Docker image
Write-Host "`n[2/3] Building unified Docker image (yuno-platform:latest)..." -ForegroundColor Yellow
docker build -t yuno-platform .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed! Aborting."
    exit $LASTEXITCODE
}

# 3. Start the newly built container
Write-Host "`n[3/3] Starting Yuno AI Platform container on port 8000..." -ForegroundColor Yellow
docker run -d -p 8000:8000 --name yuno_app --env-file ./backend/.env yuno-platform:latest
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker run failed! Check your environment variables and port usage."
    exit $LASTEXITCODE
}

# Success!
Write-Host "`n=========================================" -ForegroundColor Green
Write-Host "   Success! Yuno AI Platform is Active   " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Visual Builder & Observability Dashboard are available at:" -ForegroundColor White
Write-Host "👉 http://localhost:8000 👈" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
