# ==========================================
# STAGE 1: Compile the Vite React Frontend
# ==========================================
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

# Copy frontend packages first to utilize Docker layer caching
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy the rest of the frontend files and compile production bundle
COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Build the Unified FastAPI Runtime
# ==========================================
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for caching
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend codebase
COPY backend/ ./backend/

# Copy the compiled React assets from Stage 1 into backend's static files directory
COPY --from=frontend-builder /app/frontend/build ./backend/app/static

# Set working directory to backend
WORKDIR /app/backend

# Expose the default execution port
EXPOSE 8000

# Start unified server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
