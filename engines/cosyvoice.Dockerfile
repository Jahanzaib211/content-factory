FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

# CosyVoice 0.5B (Apache-2.0) — local TTS + voice cloning
# https://github.com/FunAudioLLM/CosyVoice
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip git ffmpeg libsox-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip3 install --no-cache-dir \
    torch==2.4.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu124 \
    && pip3 install --no-cache-dir \
    modelscope==1.18.1 \
    hyperpyyaml==1.2.2 \
    hydra-core==1.3.2 \
    librosa==0.10.2 \
    soundfile==0.12.1 \
    fastapi==0.115.0 \
    uvicorn==0.30.6 \
    pydantic==2.9.2

# CosyVoice source (Apache-2.0)
RUN git clone --depth 1 https://github.com/FunAudioLLM/CosyVoice.git /opt/CosyVoice || true

# Model weights are mounted from volume at runtime.
# First-time model download (~2GB for CosyVoice-300M, ~4GB for 0.5B):
#   python3 -c "from modelscope import snapshot_download; snapshot_download('iic/CosyVoice-300M')"

COPY engines/cosyvoice_server.py /app/engines/cosyvoice_server.py
ENV PYTHONPATH=/app
EXPOSE 8004

CMD ["python3", "-m", "engines.cosyvoice_server", "--port", "8004"]
