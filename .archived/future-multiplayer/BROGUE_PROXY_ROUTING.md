# Brogue: tia-proxy Routing Design

**Date:** 2025-10-22
**Session:** iridescent-shade-1022
**Focus:** nginx-based routing, load balancing, SSL for Brogue servers

---

## 🎯 Overview

**tia-proxy** is the nginx-based reverse proxy that:
- Provides stable DNS entry point (`brogue.tia.dev`)
- Terminates SSL/TLS
- Load balances across ConnectionService instances
- Routes WebSocket connections
- Provides health checks

---

## 🏗️ Architecture

```
Players
  ↓
  wss://brogue.tia.dev:443 (SSL)
  ↓
┌─────────────────────────────────────┐
│         tia-proxy (nginx)           │
│  - SSL termination                  │
│  - WebSocket upgrade                │
│  - Load balancing                   │
│  - Health checks                    │
└─────────────────────────────────────┘
  ↓
  ws://localhost:8765, :8766, :8767 (no SSL)
  ↓
┌──────────────────────────────────────┐
│   ConnectionService Instances        │
│  - Handle WebSocket connections      │
│  - Route to NATS                     │
│  - Manage player sessions            │
└──────────────────────────────────────┘
```

**Why proxy?**
- ✅ **Single entry point** - Players always connect to same URL
- ✅ **SSL offloading** - ConnectionService doesn't need SSL certs
- ✅ **Load balancing** - Distribute connections across instances
- ✅ **Zero-downtime deploys** - Rolling updates behind proxy
- ✅ **Health checks** - Route around failed instances
- ✅ **Rate limiting** - Prevent abuse
- ✅ **Logging** - Centralized access logs

---

## 📋 tia-proxy Directory Structure

```
/etc/tia-proxy/
├── nginx.conf                    # Main nginx config
├── conf.d/
│   └── brogue.conf              # Brogue-specific config
├── sites-available/
│   ├── brogue-dev.conf          # Development
│   ├── brogue-staging.conf      # Staging
│   └── brogue-prod.conf         # Production
├── sites-enabled/               # Symlinks to active sites
│   └── brogue-prod.conf -> ../sites-available/brogue-prod.conf
├── ssl/
│   ├── brogue.tia.dev/
│   │   ├── fullchain.pem
│   │   └── privkey.pem
│   └── dhparam.pem
└── logs/
    ├── brogue-access.log
    └── brogue-error.log
```

---

## ⚙️ Configuration Files

### Main nginx.conf

```nginx
# /etc/tia-proxy/nginx.conf

user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
}

http {
    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # MIME types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript;

    # WebSocket settings
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }

    # Include site configs
    include /etc/tia-proxy/sites-enabled/*.conf;
}
```

---

### Brogue Production Config

```nginx
# /etc/tia-proxy/sites-available/brogue-prod.conf

# Upstream ConnectionService instances
upstream brogue_websocket {
    # Load balancing method
    least_conn;  # Send to instance with fewest active connections

    # ConnectionService instances
    server 127.0.0.1:8765 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8766 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8767 max_fails=3 fail_timeout=30s;

    # Health check
    # If server fails 3 health checks, mark down for 30s
}

# HTTP → HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name brogue.tia.dev;

    # ACME challenge for Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect everything else to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name brogue.tia.dev;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/brogue.tia.dev/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/brogue.tia.dev/privkey.pem;

    # SSL settings (modern, secure)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # HSTS (force HTTPS)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # SSL session cache
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Diffie-Hellman parameter
    ssl_dhparam /etc/tia-proxy/ssl/dhparam.pem;

    # Logging
    access_log /etc/tia-proxy/logs/brogue-access.log;
    error_log /etc/tia-proxy/logs/brogue-error.log;

    # WebSocket connection
    location / {
        # Proxy to upstream
        proxy_pass http://brogue_websocket;

        # WebSocket upgrade headers
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        # Pass client information
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts (long for WebSocket)
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;

        # Buffering (disable for WebSocket)
        proxy_buffering off;
    }

    # Health check endpoint
    location /health {
        access_log off;
        add_header Content-Type text/plain;
        return 200 "healthy\n";
    }

    # Metrics endpoint (restrict access)
    location /metrics {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://brogue_websocket;
    }
}
```

---

### Brogue Development Config

```nginx
# /etc/tia-proxy/sites-available/brogue-dev.conf

upstream brogue_websocket_dev {
    server 127.0.0.1:8765;  # Single instance for dev
}

server {
    listen 8080;  # Non-standard port for dev
    server_name localhost;

    # No SSL for local dev
    location / {
        proxy_pass http://brogue_websocket_dev;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Shorter timeouts for dev
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        return 200 "dev healthy\n";
    }
}
```

---

## 🔐 SSL Certificate Setup

### Let's Encrypt (Certbot)

**Install certbot:**
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

**Get certificate:**
```bash
sudo certbot --nginx -d brogue.tia.dev
```

**Auto-renewal (certbot sets up cron):**
```bash
# Test renewal
sudo certbot renew --dry-run

# Cron job (automatically created)
# /etc/cron.d/certbot
0 */12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
```

**Manual renewal:**
```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## 📊 Load Balancing Strategies

### 1. Least Connections (Recommended)

```nginx
upstream brogue_websocket {
    least_conn;  # Route to instance with fewest active connections
    server 127.0.0.1:8765;
    server 127.0.0.1:8766;
}
```

**Best for:** Long-lived WebSocket connections
**Why:** Evenly distributes load as players connect/disconnect

---

### 2. IP Hash (Sticky Sessions)

```nginx
upstream brogue_websocket {
    ip_hash;  # Same IP → same server
    server 127.0.0.1:8765;
    server 127.0.0.1:8766;
}
```

**Best for:** Session affinity needed
**Why:** Ensures player reconnects to same instance (useful if session state is local)

---

### 3. Round Robin (Default)

```nginx
upstream brogue_websocket {
    # No directive = round robin
    server 127.0.0.1:8765;
    server 127.0.0.1:8766;
}
```

**Best for:** Stateless connections
**Why:** Simple, predictable distribution

---

### 4. Weighted Distribution

```nginx
upstream brogue_websocket {
    server 127.0.0.1:8765 weight=3;  # Gets 3x more traffic
    server 127.0.0.1:8766 weight=1;
}
```

**Best for:** Different instance capabilities
**Why:** More powerful servers handle more load

---

## 🏥 Health Checks

### Active Health Checks (nginx Plus only)

**For open-source nginx, use passive health checks:**

```nginx
upstream brogue_websocket {
    server 127.0.0.1:8765 max_fails=3 fail_timeout=30s;
    # If 3 requests fail, mark down for 30s
}
```

---

### External Health Monitoring

**Use a monitoring service to check `/health`:**

```bash
# Cron job to check health
*/1 * * * * curl -f http://localhost:8765/health || systemctl restart brogue-connection-8765
```

**Or use systemd watchdog:**

```ini
# /etc/systemd/system/brogue-connection@.service
[Service]
WatchdogSec=30s
# Service must call sd_notify(0, "WATCHDOG=1") every 30s
```

---

## 🔒 Security

### Rate Limiting

```nginx
# Limit to 10 connections per IP
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;
limit_conn conn_limit 10;

# Limit to 100 requests per minute
limit_req_zone $binary_remote_addr zone=req_limit:10m rate=100r/m;
limit_req zone=req_limit burst=20;

server {
    # Apply limits
    limit_conn conn_limit 10;
    limit_req zone=req_limit burst=20 nodelay;
    ...
}
```

---

### IP Whitelisting (Admin endpoints)

```nginx
location /admin {
    allow 192.168.1.0/24;  # Internal network
    allow 10.0.0.0/8;      # VPN
    deny all;

    proxy_pass http://brogue_websocket;
}
```

---

### DDoS Protection

```nginx
# Connection limits
limit_conn_zone $binary_remote_addr zone=ddos:10m;
limit_conn ddos 10;

# Request rate limits
limit_req_zone $binary_remote_addr zone=ddos_req:10m rate=10r/s;
limit_req zone=ddos_req burst=20;

# Timeout limits
client_body_timeout 5s;
client_header_timeout 5s;
```

---

## 📈 Monitoring

### Access Logs

```nginx
# Custom log format with timing
log_format brogue '$remote_addr - $remote_user [$time_local] '
                  '"$request" $status $body_bytes_sent '
                  '"$http_referer" "$http_user_agent" '
                  'rt=$request_time uct="$upstream_connect_time" '
                  'uht="$upstream_header_time" urt="$upstream_response_time"';

access_log /etc/tia-proxy/logs/brogue-access.log brogue;
```

**Parse logs for metrics:**
```bash
# Most connected IPs
cat brogue-access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head

# Average response time
cat brogue-access.log | grep -oP 'urt="\K[^"]+' | awk '{s+=$1; c++} END {print s/c}'
```

---

### nginx Metrics (Prometheus Exporter)

**Install nginx-prometheus-exporter:**
```bash
docker run -d \
  --name nginx-exporter \
  -p 9113:9113 \
  nginx/nginx-prometheus-exporter:0.11.0 \
  -nginx.scrape-uri=http://localhost:8080/stub_status
```

**Enable stub_status in nginx:**
```nginx
server {
    listen 8080;
    location /stub_status {
        stub_status;
        allow 127.0.0.1;
        deny all;
    }
}
```

---

## 🚀 Deployment Workflow

### Zero-Downtime Deploy

**1. Start new instance on different port:**
```bash
# New version
./brogue_connection_service --port 8768
```

**2. Add to upstream (gradually):**
```nginx
upstream brogue_websocket {
    server 127.0.0.1:8765 weight=2;  # Old version
    server 127.0.0.1:8768 weight=1;  # New version (testing)
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

**3. Monitor metrics, shift traffic:**
```nginx
upstream brogue_websocket {
    server 127.0.0.1:8765 weight=1;  # Old
    server 127.0.0.1:8768 weight=2;  # New (most traffic)
}
```

**4. Remove old version:**
```nginx
upstream brogue_websocket {
    server 127.0.0.1:8768;  # New only
}
```

**5. Stop old instance:**
```bash
systemctl stop brogue-connection-8765
```

---

## 🔧 Operations

### Reload Config (No Downtime)

```bash
# Test config first
sudo nginx -t

# Reload (graceful)
sudo systemctl reload nginx
```

---

### Emergency Maintenance Mode

```nginx
# Add to server block
if (-f /etc/tia-proxy/maintenance.flag) {
    return 503 "Brogue is undergoing maintenance. Back soon!";
}
```

```bash
# Enable maintenance mode
sudo touch /etc/tia-proxy/maintenance.flag
sudo systemctl reload nginx

# Disable
sudo rm /etc/tia-proxy/maintenance.flag
sudo systemctl reload nginx
```

---

### Debugging

**Test WebSocket connection:**
```bash
# wscat (npm install -g wscat)
wscat -c wss://brogue.tia.dev

# Or Python
python3 -c "
import asyncio, websockets
async def test():
    async with websockets.connect('wss://brogue.tia.dev') as ws:
        await ws.send('ping')
        print(await ws.recv())
asyncio.run(test())
"
```

**Check upstream status:**
```bash
curl http://localhost:8080/stub_status
```

**Monitor real-time logs:**
```bash
tail -f /etc/tia-proxy/logs/brogue-access.log
tail -f /etc/tia-proxy/logs/brogue-error.log
```

---

## 📋 Quick Reference

### Enable Site
```bash
sudo ln -s /etc/tia-proxy/sites-available/brogue-prod.conf \
            /etc/tia-proxy/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Disable Site
```bash
sudo rm /etc/tia-proxy/sites-enabled/brogue-prod.conf
sudo systemctl reload nginx
```

### Check Config
```bash
sudo nginx -t
```

### Reload (Graceful)
```bash
sudo systemctl reload nginx
```

### Restart (Hard)
```bash
sudo systemctl restart nginx
```

### View Logs
```bash
tail -f /etc/tia-proxy/logs/brogue-access.log
tail -f /etc/tia-proxy/logs/brogue-error.log
```

---

## 🎯 Summary

**tia-proxy provides:**
- ✅ Stable entry point (`brogue.tia.dev`)
- ✅ SSL/TLS termination
- ✅ Load balancing across ConnectionService instances
- ✅ Health checks and automatic failover
- ✅ Zero-downtime deploys
- ✅ Rate limiting and DDoS protection
- ✅ Centralized logging

**Next steps:**
1. Setup nginx with Brogue config
2. Get SSL cert from Let's Encrypt
3. Deploy ConnectionService instances
4. Test WebSocket connection through proxy
5. Monitor and tune load balancing

**Key insight:** The proxy is the front door to Brogue. Keep it simple, secure, and reliable.
