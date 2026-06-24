FROM node:18-bookworm-slim

# Install Chromium and FFmpeg for Remotion rendering
# Replace /etc/apt/sources.list.d/debian.sources with a minimal DEB822 file pointing
# at ftp.us.debian.org (faster US mirror) and NO security component. The
# bookworm-security suite isn't published on ftp.us.debian.org, which makes
# 'apt-get update' fail with exit code 100. Build-time apt doesn't need security
# updates. Single-quoted heredoc disables all shell expansion.
RUN cat > /etc/apt/sources.list.d/debian.sources <<'DEBIAN_EOF'
Types: deb
URIs: http://ftp.us.debian.org/debian
Suites: bookworm bookworm-updates
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
DEBIAN_EOF
RUN apt-get update && \
    apt-get install -y --no-install-recommends chromium ffmpeg && \
    rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV REMOTION_BUNDLE_PATH=/app/remotion
ENV OUTPUT_DIR=/output

WORKDIR /app

# Copy render service source
COPY render-service/package.json ./
RUN npm install

COPY render-service/tsconfig.json ./
COPY render-service/src/ ./src/

# Copy remotion source for bundling
COPY remotion/package.json /app/remotion/package.json
COPY remotion/tsconfig.json /app/remotion/tsconfig.json
COPY remotion/src/ /app/remotion/src/
COPY remotion/public/ /app/remotion/public/

# Install remotion deps
RUN cd /app/remotion && npm install

# Build TypeScript
RUN npm run build

EXPOSE 3100
CMD ["node", "dist/server.js"]
