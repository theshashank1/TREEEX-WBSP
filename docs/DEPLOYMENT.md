# 🚀 Production Deployment Guide

This guide covers how to deploy TREEEX-WBSP to a production environment (e.g., AWS EC2, DigitalOcean Droplet, or Container Service).

## 🏗️ Deployment Strategy

We recommend using **Docker** for ease of deployment and isolation, but you can also deploy directly on a VM using **systemd**.

### Requirements

- A Linux server (Ubuntu 22.04 LTS recommended)
- 2 CPU Cores / 4GB RAM (minimum)
- PostgreSQL 14+ (Managed service recommended, e.g., RDS, Supabase)
- Redis 6+ (Managed service recommended)
- Domain name with SSL (HTTPS is required for WhatsApp Webhooks)

---

## 🐳 Docker Deployment (Recommended)

### 1. Build the Image

```bash
docker build -t treeex-wbsp:latest .
```

### 2. Docker Compose

Create a `docker-compose.yml` file for production usage.

```yaml
services:
  api:
    image: treeex-wbsp:latest
    command: uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 4
    env_file: .env.production
    ports:
      - "8000:8000"
    restart: always

  worker-outbound:
    image: treeex-wbsp:latest
    command: python -m server.workers.outbound
    env_file: .env.production
    restart: always

  worker-webhook:
    image: treeex-wbsp:latest
    command: python -m server.workers.webhook
    env_file: .env.production
    restart: always
```

### 3. Environment Configuration

Create `.env.production` based on [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md).

> ⚠️ **Important:**
> - Set `ENV=production`
> - Set `DEBUG=false`
> - Use a strong `SECRET_KEY`

### 4. Start Services

```bash
docker-compose up -d
```

---

## 🖥️ Manual Deployment (Systemd)

If you prefer running directly on the host (Bare Metal / VM).

### 1. Service: API

Create `/etc/systemd/system/treeex-api.service`:

```ini
[Unit]
Description=TREEEX API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/TREEEX-WBSP
EnvironmentFile=/home/ubuntu/TREEEX-WBSP/server/.env
ExecStart=/home/ubuntu/TREEEX-WBSP/.venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. Service: Workers

Create `/etc/systemd/system/treeex-worker-outbound.service`:

```ini
[Unit]
Description=TREEEX Outbound Worker
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/TREEEX-WBSP
EnvironmentFile=/home/ubuntu/TREEEX-WBSP/server/.env
ExecStart=/home/ubuntu/TREEEX-WBSP/.venv/bin/python -m server.workers.outbound
Restart=always

[Install]
WantedBy=multi-user.target
```

(Repeat for `treeex-worker-webhook.service` changing the command).

### 3. Enable & Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now treeex-api treeex-worker-outbound treeex-worker-webhook
```

---

## 🔒 SSL & Reverse Proxy (Nginx)

Never expose Uvicorn directly to the internet. Use Nginx as a reverse proxy.

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Monitoring

- **Health Checks**: Monitor `/health` endpoint.
- **Logs**:
  - Docker: `docker logs -f <container_id>`
  - Systemd: `journalctl -u treeex-api -f`
