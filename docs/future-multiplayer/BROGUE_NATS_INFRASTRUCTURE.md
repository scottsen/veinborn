# Brogue: NATS Infrastructure Guide

**Date:** 2025-10-22
**Session:** iridescent-shade-1022
**Focus:** NATS setup, Python integration, deployment, tia-proxy routing

---

## 🎯 Overview

This document covers the **complete NATS infrastructure** for Brogue:

1. **NATS Server Setup** - Installation, configuration, clustering
2. **Python Integration** - `nats.py` library, patterns, examples
3. **tia-proxy Routing** - How players connect through nginx
4. **Deployment Architecture** - Local dev, staging, production
5. **Monitoring & Operations** - Health checks, metrics, debugging

---

## 📦 Part 1: NATS Server Setup

### Installation (Development)

**Linux (Ubuntu/Debian):**
```bash
# Download latest NATS server
cd /tmp
wget https://github.com/nats-io/nats-server/releases/download/v2.10.7/nats-server-v2.10.7-linux-amd64.tar.gz
tar -xzf nats-server-v2.10.7-linux-amd64.tar.gz
sudo mv nats-server-v2.10.7-linux-amd64/nats-server /usr/local/bin/

# Verify
nats-server --version
# nats-server: v2.10.7
```

**macOS:**
```bash
brew install nats-server
```

**Docker (Easiest for development):**
```bash
docker run -d \
  --name nats \
  -p 4222:4222 \
  -p 8222:8222 \
  nats:latest -js
```

**Ports:**
- `4222` - Client connections (Python connects here)
- `8222` - HTTP monitoring endpoint
- `6222` - Cluster communication (for multi-server)

---

### Basic Configuration

**Create `/etc/nats/brogue-dev.conf`:**
```conf
# Brogue NATS Server - Development Configuration

# Server identity
server_name: brogue-dev-01

# Listen addresses
listen: 0.0.0.0:4222           # Client connections
http: 0.0.0.0:8222             # Monitoring endpoint

# Enable JetStream (persistence)
jetstream {
    store_dir: /var/lib/nats/jetstream
    max_memory_store: 1GB
    max_file_store: 10GB
}

# Logging
debug: false
trace: false
logtime: true
log_file: /var/log/nats/brogue-dev.log

# Limits
max_connections: 1000
max_payload: 1MB
max_pending: 64MB

# Authentication (development)
authorization {
    # Service accounts (backend services)
    users = [
        {
            user: "brogue-service"
            password: "dev-service-password"
            permissions: {
                publish: ["game.>", "chat.>", "system.>"]
                subscribe: ["game.>", "chat.>", "system.>"]
            }
        },
        # Client connections (players)
        {
            user: "brogue-client"
            password: "dev-client-password"
            permissions: {
                publish: ["game.instance.*.actions", "chat.>"]
                subscribe: ["game.party.*.updates", "chat.>"]
            }
        }
    ]
}
```

**Start server:**
```bash
nats-server -c /etc/nats/brogue-dev.conf
```

**Or as systemd service:**
```ini
# /etc/systemd/system/nats-brogue.service
[Unit]
Description=NATS Server for Brogue
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/nats-server -c /etc/nats/brogue-dev.conf
Restart=always
User=nats
Group=nats

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable nats-brogue
sudo systemctl start nats-brogue
sudo systemctl status nats-brogue
```

---

### Clustering (High Availability)

**For production, run 3+ servers in cluster:**

**Server 1 (`brogue-nats-01.conf`):**
```conf
server_name: brogue-nats-01
listen: 0.0.0.0:4222
http: 0.0.0.0:8222

cluster {
    name: brogue-cluster
    listen: 0.0.0.0:6222
    routes: [
        nats://brogue-nats-02:6222
        nats://brogue-nats-03:6222
    ]
}

jetstream {
    store_dir: /var/lib/nats/jetstream
}
```

**Server 2 & 3:** Same config, just change `server_name` and `routes` list.

**Clients automatically failover:**
```python
# Python client connects to all servers
nc = await nats.connect(servers=[
    "nats://brogue-nats-01:4222",
    "nats://brogue-nats-02:4222",
    "nats://brogue-nats-03:4222"
])

# If one dies, client reconnects to another automatically!
```

---

### Monitoring Endpoint

**Check server health:**
```bash
curl http://localhost:8222/varz
```

**Returns:**
```json
{
  "server_id": "brogue-dev-01",
  "version": "2.10.7",
  "connections": 42,
  "in_msgs": 1523421,
  "out_msgs": 1523421,
  "in_bytes": 152342100,
  "out_bytes": 152342100,
  "mem": 15728640,
  "cpu": 0.5
}
```

**Other endpoints:**
- `/connz` - Active connections
- `/subsz` - Active subscriptions
- `/routez` - Cluster routes
- `/jsz` - JetStream stats

---

## 🐍 Part 2: Python Integration

### Installation

```bash
pip install nats-py
```

**Or in `requirements.txt`:**
```txt
nats-py>=2.6.0
asyncpg>=0.29.0        # PostgreSQL
websockets>=12.0       # Client connections
textual>=0.45.0        # TUI
pydantic>=2.0          # Message validation
```

---

### Basic Connection

```python
import asyncio
from nats.aio.client import Client as NATS

async def main():
    # Connect to NATS server
    nc = await NATS().connect(
        servers=["nats://localhost:4222"],
        user="brogue-service",
        password="dev-service-password"
    )

    print(f"Connected to NATS at {nc.connected_url}")

    # Close when done
    await nc.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Connection with Reconnection Handling

```python
async def disconnected_cb():
    print("❌ Disconnected from NATS!")

async def reconnected_cb():
    print("✅ Reconnected to NATS!")

async def error_cb(e):
    print(f"⚠️  NATS error: {e}")

async def closed_cb():
    print("🔌 Connection closed")

nc = await NATS().connect(
    servers=[
        "nats://brogue-nats-01:4222",
        "nats://brogue-nats-02:4222",
        "nats://brogue-nats-03:4222"
    ],
    user="brogue-service",
    password="dev-service-password",

    # Reconnection settings
    max_reconnect_attempts=10,
    reconnect_time_wait=2,  # seconds between attempts

    # Callbacks
    disconnected_cb=disconnected_cb,
    reconnected_cb=reconnected_cb,
    error_cb=error_cb,
    closed_cb=closed_cb
)
```

---

### Publish/Subscribe Pattern

**Publisher:**
```python
import json

async def publish_game_update(nc, party_id: str, state: dict):
    """Publish game state update to all party members"""
    subject = f"game.party.{party_id}.updates"
    message = json.dumps(state).encode()

    await nc.publish(subject, message)
    print(f"Published to {subject}")
```

**Subscriber:**
```python
async def handle_update(msg):
    """Handle incoming game state update"""
    state = json.loads(msg.data.decode())
    print(f"Received update on {msg.subject}: {state}")

async def subscribe_to_party(nc, party_id: str):
    """Subscribe to party updates"""
    subject = f"game.party.{party_id}.updates"

    # Subscribe with callback
    await nc.subscribe(subject, cb=handle_update)
    print(f"Subscribed to {subject}")
```

**Wildcard subscriptions:**
```python
# Subscribe to ALL party updates
await nc.subscribe("game.party.*.updates", cb=handle_update)

# Subscribe to ALL game events
await nc.subscribe("game.>", cb=handle_all_game_events)

# Subscribe to specific instance, all event types
await nc.subscribe("game.instance.42.*", cb=handle_instance_events)
```

---

### Request/Reply Pattern (RPC)

**Service (responder):**
```python
async def handle_get_state(msg):
    """Respond to state request"""
    request = json.loads(msg.data.decode())
    instance_id = request["instance_id"]

    # Get current state
    state = game_instances[instance_id].get_state()

    # Send response
    await msg.respond(json.dumps(state).encode())

# Subscribe to state requests
await nc.subscribe("game.instance.*.get_state", cb=handle_get_state)
```

**Client (requester):**
```python
async def request_game_state(nc, instance_id: str):
    """Request current game state (RPC-style)"""
    subject = f"game.instance.{instance_id}.get_state"
    request = json.dumps({"instance_id": instance_id})

    # Send request, wait for response (with timeout)
    try:
        response = await nc.request(
            subject,
            request.encode(),
            timeout=2.0  # 2 second timeout
        )

        state = json.loads(response.data.decode())
        return state

    except asyncio.TimeoutError:
        print(f"Request timeout for {subject}")
        return None
```

---

### Queue Groups (Load Balancing)

**Multiple workers processing same queue:**

```python
# Worker 1
async def worker_1_handler(msg):
    print(f"Worker 1 processing: {msg.data.decode()}")
    # Process job...
    await asyncio.sleep(1)

await nc.subscribe("jobs.save_dungeon", queue="save_workers", cb=worker_1_handler)

# Worker 2
async def worker_2_handler(msg):
    print(f"Worker 2 processing: {msg.data.decode()}")
    # Process job...
    await asyncio.sleep(1)

await nc.subscribe("jobs.save_dungeon", queue="save_workers", cb=worker_2_handler)

# Publisher sends 10 jobs
for i in range(10):
    await nc.publish("jobs.save_dungeon", f"Job {i}".encode())

# NATS distributes jobs across workers (random or round-robin)
```

**Output:**
```
Worker 1 processing: Job 0
Worker 2 processing: Job 1
Worker 1 processing: Job 2
Worker 2 processing: Job 3
...
```

**Use cases:**
- Multiple game instance processes
- Parallel persistence workers
- Distributed AI computation

---

### JetStream (Persistent Messaging)

**Enable JetStream:**
```python
from nats.js import JetStreamContext

nc = await NATS().connect("nats://localhost:4222")
js = nc.jetstream()
```

**Create stream:**
```python
# Stream stores all messages matching subjects
await js.add_stream(
    name="GAME_EVENTS",
    subjects=["game.>"],
    retention="limits",  # Delete old messages when limits hit
    max_msgs=1000000,    # Max 1M messages
    max_bytes=1073741824,  # 1GB
    max_age=86400          # Keep for 24 hours
)
```

**Publish to JetStream (persistent):**
```python
async def save_critical_event(js, event: dict):
    """Publish critical event with persistence"""
    ack = await js.publish(
        "game.loot.legendary.collected",
        json.dumps(event).encode()
    )

    print(f"Event persisted at sequence {ack.seq}")
```

**Consume from JetStream:**
```python
# Create durable consumer (remembers position)
consumer = await js.subscribe(
    "game.loot.legendary.collected",
    durable="loot_persister"  # Durable name
)

async for msg in consumer.messages:
    event = json.loads(msg.data.decode())

    # Process event
    await save_to_database(event)

    # Acknowledge (removes from stream for this consumer)
    await msg.ack()

    # If you crash before ack, message will be redelivered!
```

**JetStream guarantees:**
- ✅ Message persisted to disk/memory
- ✅ At-least-once delivery
- ✅ Consumer tracks position
- ✅ Can replay history
- ✅ Survives server restart

---

### Graceful Shutdown

```python
import signal

async def main():
    nc = await NATS().connect("nats://localhost:4222")

    # Setup subscriptions...

    # Wait for shutdown signal
    stop_event = asyncio.Event()

    def signal_handler(sig, frame):
        print("Shutting down gracefully...")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await stop_event.wait()

    # Drain (finish processing current messages, then close)
    await nc.drain()
    print("Shutdown complete")

asyncio.run(main())
```

---

## 🔌 Part 3: tia-proxy Integration

### Problem: Players Need Stable URL

**Without proxy:**
```
Player → ws://192.168.1.100:8765  # Direct to server, no SSL, IP changes
```

**With tia-proxy:**
```
Player → wss://brogue.tia.dev  # Stable DNS, SSL, load balanced
```

---

### tia-proxy Architecture

```
┌─────────────────────────────────────────────┐
│            Players (Clients)                │
│  ws://brogue.tia.dev (SSL on port 443)     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│          tia-proxy (nginx)                  │
│  - SSL termination                          │
│  - Load balancing                           │
│  - WebSocket proxying                       │
└─────────────────────────────────────────────┘
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
┌────────────────┐    ┌────────────────┐
│ ConnectionSvc  │    │ ConnectionSvc  │
│   (port 8765)  │    │   (port 8766)  │
└────────────────┘    └────────────────┘
```

---

### nginx Configuration for Brogue

**Create `/etc/tia-proxy/sites-available/brogue.conf`:**

```nginx
# Upstream servers (ConnectionService instances)
upstream brogue_websocket {
    # IP hash ensures same player goes to same instance (sticky sessions)
    ip_hash;

    server 127.0.0.1:8765 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8766 max_fails=3 fail_timeout=30s;
    # Add more instances as needed
}

# HTTP server (redirect to HTTPS)
server {
    listen 80;
    server_name brogue.tia.dev;

    return 301 https://$server_name$request_uri;
}

# HTTPS server (WebSocket)
server {
    listen 443 ssl http2;
    server_name brogue.tia.dev;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/brogue.tia.dev/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/brogue.tia.dev/privkey.pem;

    # SSL settings (modern, secure)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # WebSocket proxying
    location / {
        proxy_pass http://brogue_websocket;

        # WebSocket upgrade headers
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Pass client info to backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/tia-proxy/sites-available/brogue.conf /etc/tia-proxy/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

### SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d brogue.tia.dev

# Auto-renewal (certbot sets up cron job automatically)
sudo certbot renew --dry-run
```

---

### Client Connection (Through Proxy)

```python
# Python client
import websockets

async def connect_to_brogue():
    # Connect through tia-proxy (SSL enabled)
    ws = await websockets.connect("wss://brogue.tia.dev")

    # Send authentication
    await ws.send(json.dumps({
        "type": "auth",
        "username": "alice",
        "password": "secret"
    }))

    # Receive state updates
    async for message in ws:
        state = json.loads(message)
        render_game(state)
```

---

### Load Balancing Strategies

**1. IP Hash (Sticky Sessions):**
```nginx
upstream brogue_websocket {
    ip_hash;  # Same IP → same server
    server 127.0.0.1:8765;
    server 127.0.0.1:8766;
}
```
**Use when:** Player session tied to specific server

**2. Least Connections:**
```nginx
upstream brogue_websocket {
    least_conn;  # Route to server with fewest connections
    server 127.0.0.1:8765;
    server 127.0.0.1:8766;
}
```
**Use when:** Even distribution of load

**3. Round Robin (default):**
```nginx
upstream brogue_websocket {
    # No directive = round robin
    server 127.0.0.1:8765;
    server 127.0.0.1:8766;
}
```
**Use when:** Stateless connections

---

## 🏗️ Part 4: Deployment Architecture

### Local Development

```
┌─────────────────────────────────────────────┐
│         Developer Laptop                    │
│                                             │
│  NATS:           localhost:4222             │
│  PostgreSQL:     localhost:5432             │
│  ConnectionSvc:  localhost:8765             │
│  GameInstance:   Process in same terminal   │
│  Client:         Textual TUI                │
└─────────────────────────────────────────────┘
```

**Start all services:**
```bash
# Terminal 1: NATS
nats-server -js

# Terminal 2: PostgreSQL
docker run -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:15

# Terminal 3: Connection Service
cd brogue/services/connection
python connection_service.py

# Terminal 4: Game Instance
cd brogue/services/game
python game_instance.py --party=test

# Terminal 5: Client
cd brogue/client
python brogue_client.py --server ws://localhost:8765
```

**Or use Docker Compose:**
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  nats:
    image: nats:latest
    command: ["-js"]
    ports:
      - "4222:4222"
      - "8222:8222"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: dev
      POSTGRES_DB: brogue
    ports:
      - "5432:5432"

  connection:
    build: ./services/connection
    environment:
      NATS_URL: nats://nats:4222
      DB_URL: postgresql://postgres:dev@postgres/brogue
    ports:
      - "8765:8765"
    depends_on:
      - nats
      - postgres
```

```bash
docker-compose -f docker-compose.dev.yml up
```

---

### Production Deployment

```
┌────────────────────────────────────────────────────┐
│                  brogue.tia.dev                    │
│                  (tia-proxy / nginx)               │
│                  SSL termination                   │
└────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴────────────────┐
        ↓                                ↓
┌──────────────────┐            ┌──────────────────┐
│ ConnectionSvc 1  │            │ ConnectionSvc 2  │
│  (systemd)       │            │  (systemd)       │
└──────────────────┘            └──────────────────┘
        ↓                                ↓
    ┌───────────────────────────────────────┐
    │         NATS Cluster (3 nodes)        │
    │  nats-01, nats-02, nats-03           │
    └───────────────────────────────────────┘
        ↓                                ↓
┌──────────────────┐            ┌──────────────────┐
│ GameInstance 1   │            │ GameInstance 2   │
│  (process pool)  │            │  (process pool)  │
└──────────────────┘            └──────────────────┘
        ↓                                ↓
    ┌───────────────────────────────────────┐
    │     PostgreSQL (managed RDS)          │
    │     + Read replicas                   │
    └───────────────────────────────────────┘
```

**Systemd service:**
```ini
# /etc/systemd/system/brogue-connection.service
[Unit]
Description=Brogue Connection Service
After=network.target nats-brogue.service

[Service]
Type=simple
User=brogue
WorkingDirectory=/opt/brogue/services/connection
ExecStart=/opt/brogue/venv/bin/python connection_service.py
Restart=always
Environment="NATS_URL=nats://localhost:4222"
Environment="DB_URL=postgresql://brogue:***@postgres.internal/brogue"

[Install]
WantedBy=multi-user.target
```

---

## 📊 Part 5: Monitoring & Operations

### NATS Monitoring

**Install NATS CLI:**
```bash
go install github.com/nats-io/natscli/nats@latest
```

**Check server status:**
```bash
nats server list
nats server info
```

**Monitor streams:**
```bash
nats stream list
nats stream info GAME_EVENTS
```

**Monitor consumers:**
```bash
nats consumer list GAME_EVENTS
```

**Watch messages (debug):**
```bash
# Subscribe and print all game events
nats sub "game.>"

# Specific subject
nats sub "game.party.dragon_slayers.updates"
```

---

### Health Checks

**NATS health:**
```bash
curl http://localhost:8222/healthz
# OK if healthy
```

**Service health (implement in services):**
```python
# In ConnectionService
from aiohttp import web

async def health_check(request):
    # Check NATS connection
    if nc.is_connected:
        return web.Response(text="healthy", status=200)
    else:
        return web.Response(text="unhealthy", status=503)

app = web.Application()
app.router.add_get("/health", health_check)
```

---

### Debugging

**Enable NATS trace logging:**
```conf
# nats.conf
trace: true
debug: true
```

**Python logging:**
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("nats")
logger.setLevel(logging.DEBUG)
```

**Monitor subjects:**
```bash
# See all active subjects
curl http://localhost:8222/subsz
```

---

## 🎯 Quick Reference

### NATS URLs
- **Development:** `nats://localhost:4222`
- **Production:** `nats://brogue-nats-01:4222,nats://brogue-nats-02:4222,nats://brogue-nats-03:4222`

### Subject Naming Convention
```
game.instance.{instance_id}.actions       # Player actions to instance
game.instance.{instance_id}.get_state     # Request state (RPC)
game.party.{party_id}.updates             # State updates to party
game.party.{party_id}.chat                # Party chat
chat.global                                # Global chat
chat.whisper.{from}.{to}                  # Private messages
loot.legendary.collected                   # Critical events (JetStream)
jobs.save_dungeon                          # Work queue
```

### Python Quick Start
```python
from nats.aio.client import Client as NATS

# Connect
nc = await NATS().connect("nats://localhost:4222")

# Publish
await nc.publish("game.party.42.updates", b"data")

# Subscribe
await nc.subscribe("game.party.42.updates", cb=handler)

# Request/Reply
resp = await nc.request("game.instance.42.get_state", b"", timeout=2.0)

# JetStream
js = nc.jetstream()
await js.publish("loot.legendary", b"data")

# Close
await nc.drain()
```

---

## 🚀 Next Steps

1. ✅ Read this doc
2. 🔨 Setup local NATS server
3. 🔨 Test Python connection
4. 🔨 Build first pub/sub example
5. 🔨 Integrate with ConnectionService
6. 🔨 Setup tia-proxy routing
7. 📝 Deploy to staging

**Key insight:** NATS is the nervous system connecting all Brogue services. Master it, and the distributed architecture becomes elegant.
