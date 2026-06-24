# Multi-stage build for smaller final image
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
# Replace /etc/apt/sources.list.d/debian.sources with a minimal DEB822 file pointing
# at ftp.us.debian.org (faster US mirror) and NO security component. The
# trixie-security suite isn't published on ftp.us.debian.org, which makes
# 'apt-get update' fail with exit code 100. Build-time apt doesn't need security
# updates. Single-quoted heredoc disables all shell expansion.
RUN cat > /etc/apt/sources.list.d/debian.sources <<'DEBIAN_EOF'
Types: deb
URIs: http://ftp.us.debian.org/debian
Suites: trixie trixie-updates
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
DEBIAN_EOF
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
# Copy and install Python dependencies
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg, OpenCV dependencies, and Node.js (for yt-dlp JS challenges)
# Replace /etc/apt/sources.list.d/debian.sources with a minimal DEB822 file pointing
# at ftp.us.debian.org (faster US mirror) and NO security component. The
# trixie-security suite isn't published on ftp.us.debian.org, which makes
# 'apt-get update' fail with exit code 100. Build-time apt doesn't need security
# updates. Single-quoted heredoc disables all shell expansion.
RUN cat > /etc/apt/sources.list.d/debian.sources <<'DEBIAN_EOF'
Types: deb
URIs: http://ftp.us.debian.org/debian
Suites: trixie trixie-updates
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
DEBIAN_EOF
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Always upgrade yt-dlp to latest (YouTube bot-detection changes frequently)
RUN pip install --upgrade --no-cache-dir yt-dlp

# Copy application code
COPY . .

# Create a non-root user (Moved up)
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Create directories including Ultralytics cache config
RUN mkdir -p /app/uploads /app/output /tmp/Ultralytics
# Fix permissions: /app for code/uploads, /tmp/Ultralytics for AI cache
RUN chown -R appuser:appuser /app /tmp/Ultralytics

# Switch to non-root user
USER appuser

# Pre-download YOLO model on build (now running as appuser)
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
