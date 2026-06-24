FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

# Wan 2.1 (Apache-2.0) video generation
# https://github.com/Wan-Video/Wan2.1
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip git ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install torch + dependencies (CUDA 12.4)
RUN pip3 install --no-cache-dir \
    torch==2.4.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu124 \
    && pip3 install --no-cache-dir \
    diffusers==0.30.0 \
    transformers==4.44.2 \
    accelerate==0.34.0 \
    safetensors==0.4.5 \
    fastapi==0.115.0 \
    uvicorn==0.30.6 \
    pydantic==2.9.2

# Wan 2.1 source (Apache-2.0)
RUN git clone --depth 1 https://github.com/Wan-Video/Wan2.1.git /opt/Wan2.1 || true

# Model weights are mounted from volume at runtime.
# First-time model download (~24GB for 14B, ~6GB for 1.3B):
#   python3 -c "from huggingface_hub import snapshot_download; snapshot_download('Wan-AI/Wan2.1-T2V-1.3B')"

COPY engines/wan_server.py /app/engines/wan_server.py
ENV PYTHONPATH=/app
EXPOSE 8003

CMD ["python3", "-m", "engines.wan_server", "--port", "8003"]
