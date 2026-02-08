# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Runtime Environment
FROM python:3.9-slim

# Replace Debian sources with Aliyun mirrors for China connectivity
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# Install system dependencies (Nginx, Supervisor, curl for healthcheck)
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Setup Directories
WORKDIR /app

# Copy Backend Dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy Backend Code
COPY backend ./backend

# Copy Built Frontend from Stage 1
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy Configs
COPY docker/nginx.conf /etc/nginx/sites-available/default
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create directory for config and logs
RUN mkdir -p /app/data /app/logs
# Create a dummy config if not mounted, but code expects it at /app/config.json
# We will assume config.json is mounted or copied. 
# Copying example config as default
COPY config.example.json /app/config.json

# Expose Ports
EXPOSE 80

# Environment Variables
ENV PYTHONUNBUFFERED=1

# Start Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
