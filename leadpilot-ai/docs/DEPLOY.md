# LeadPilot AI — Production Cloud Deployment Guide

This guide describes how to deploy the LeadPilot AI stack to a single Linux VM (Ubuntu 22.04 / 24.04 on Hetzner, DigitalOcean, or AWS EC2) with automatic HTTPS using **Caddy** and **Docker Compose**.

---

## 1. Virtual Machine Hardware Requirements
- **CPU:** 2 vCPUs minimum (4 recommended for pgvector search under load).
- **RAM:** 4 GB minimum (8 GB recommended for simultaneous Next.js build & n8n workflows).
- **Disk:** 40 GB NVMe SSD.
- **OS:** Ubuntu 22.04 LTS or 24.04 LTS.

---

## 2. Server Provisioning & Docker Setup

```bash
# 1. Update and install Docker
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. Clone the repository
git clone https://github.com/your-org/leadpilot-ai.git
cd leadpilot-ai

# 3. Configure production environment
cp .env.example .env
nano .env
```

Set strong production values in `.env`:
- `AI_SERVICE_API_KEY`: Generate a 32+ character random hex string (`openssl rand -hex 32`).
- `N8N_ENCRYPTION_KEY`: Generate another random string.
- Set `GEMINI_MODE=real` (with active `GEMINI_API_KEY`), `SLACK_MODE=real`, `HUBSPOT_MODE=real`.

---

## 3. Reverse Proxy with Caddy (Automatic SSL)

Create `/etc/caddy/Caddyfile`:

```caddyfile
# Dashboard & Embeddable Widget
hub.brightsmile.example.com {
    reverse_proxy localhost:3000
}

# AI Service API & Webhooks
api.brightsmile.example.com {
    reverse_proxy localhost:8000
}

# n8n Workflow Automation Engine
n8n.brightsmile.example.com {
    reverse_proxy localhost:5678
}
```

Reload Caddy:
```bash
sudo systemctl reload caddy
```
*Caddy automatically provisions free Let's Encrypt SSL certificates.*

---

## 4. Starting the Stack with Production Overrides

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## 5. Automated Database Backups

Create `/opt/backup_leadpilot.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/leadpilot"
mkdir -p "$BACKUP_DIR"
docker exec -t leadpilot-postgres pg_dump -U leadpilot leadpilot | gzip > "$BACKUP_DIR/db_$(date +%F_%T).sql.gz"
# Retain last 14 days
find "$BACKUP_DIR" -type f -mtime +14 -delete
```
Add to crontab (`crontab -e`):
```cron
0 2 * * * /opt/backup_leadpilot.sh
```

---

## 6. Managed Cloud Alternatives

For teams that prefer serverless or managed infrastructure:
- **Database & Vectors:** [Supabase](https://supabase.com/) provides managed PostgreSQL 16 with pgvector and automatic daily backups.
- **App Hosting:** Deploy `ai-service` and `web` to [Render](https://render.com/) or [Railway](https://railway.app/).
- **n8n:** Use [n8n Cloud](https://n8n.io/cloud/) to avoid managing workers.
