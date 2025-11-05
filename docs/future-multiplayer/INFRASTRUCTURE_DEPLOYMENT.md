# Brogue Infrastructure & Deployment Guide

**Last Updated**: 2025-10-23
**Audience**: DevOps, SRE, Backend Developers
**Phase Coverage**: MVP (Phase 1) + Multiplayer (Phase 2)
**Container Technology**: Podman (rootless, daemonless, Kubernetes-compatible)

---

## Executive Summary

**Current State**: MVP (single-player) needs minimal infrastructure
**Future State**: Multiplayer needs containers, orchestration, monitoring

**Key Decision**: **Use Podman from day 1** (even for MVP) to get security, pod architecture, and seamless Kubernetes migration.

**Why Podman over Docker**:
- ✅ **Rootless by default** - Better security for internet-facing game servers
- ✅ **Pod concept** - Natural grouping of related containers (like Kubernetes)
- ✅ **Daemonless** - No root daemon to attack, lower resource overhead
- ✅ **Drop-in Docker replacement** - Same commands, same Dockerfiles
- ✅ **Native systemd integration** - Cleaner production deployment
- ✅ **Seamless K8s migration** - `podman generate kube` creates K8s manifests

**Quick Start**:
- MVP: Local Python → Podman dev environment (Week 1)
- Phase 2: Podman pods → systemd services (Week 12+)
- Phase 3: Export pods to Kubernetes (Week 18+)

---

## Table of Contents

1. [MVP Infrastructure (Phase 1)](#mvp-infrastructure-phase-1)
2. [Development Environment](#development-environment)
3. [Docker Strategy](#docker-strategy)
4. [Multiplayer Infrastructure (Phase 2)](#multiplayer-infrastructure-phase-2)
5. [Production Deployment](#production-deployment)
6. [Monitoring & Observability](#monitoring--observability)
7. [Cost Analysis](#cost-analysis)

---

## MVP Infrastructure (Phase 1)

### Current Needs (Weeks 1-6)

**MVP is single-player, runs locally**:
- No server needed
- No database needed (JSON files)
- No networking needed
- Terminal UI only

**But**: Containerize with Podman from day 1 for Phase 2 readiness

### Why Podman for MVP?

❌ **Don't containerize**: "MVP doesn't need it, save time"
✅ **Do containerize with Podman**: "Better security, pods from day 1, seamless K8s migration"

**Benefits**:
- Consistent dev environment (no "works on my machine")
- **Rootless containers** (better security)
- **Pod architecture** (practice for multiplayer)
- Phase 2 transition is trivial
- Easy testing (spin up, test, tear down)
- Developer onboarding is `podman pod start brogue-dev`
- **Systemd integration** for production

**Cost**: 2-3 hours upfront, saves 2-3 days later + better security

---

## Development Environment

### Option 1: Local Python (MVP Quick Start)

**Fastest way to start coding**:

```bash
# Setup
cd /home/scottsen/src/tia/projects/brogue
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python3 run_textual.py
```

**Pros**: Fast, simple, no Docker knowledge needed
**Cons**: Environment drift, Phase 2 migration harder
**Recommended for**: Week 1 if you want to start coding immediately

---

### Option 2: Podman Dev Environment (Recommended)

**Container-based from day 1 with Podman**:

```bash
# Build
podman build -t brogue:dev -f docker/Dockerfile.dev .

# Run (rootless by default!)
podman run -it --rm \
  -v $(pwd):/app \
  -v $(pwd)/data:/app/data \
  brogue:dev python3 run_textual.py
```

**Pros**: Consistent environment, rootless security, Phase 2 ready, reproducible, pod-native
**Cons**: Podman learning curve (but identical to Docker), slightly slower iteration
**Recommended for**: Week 1-2 (Podman is Docker-compatible)

**Docker compatibility**: `alias docker=podman` - all Docker commands work!

---

### Option 3: Podman Pods (Best for MVP)

**Full dev environment with hot-reload using Podman pods**:

```bash
# Create and start development pod
./scripts/dev-pod-start.sh

# Develop (changes auto-reload)
# Edit src/, see changes instantly

# Stop
podman pod stop brogue-dev

# Restart
podman pod start brogue-dev

# Remove
podman pod rm -f brogue-dev
```

**Example `dev-pod-start.sh`**:
```bash
#!/bin/bash
# Create pod for all dev services
podman pod create --name brogue-dev -p 8080:8080

# Start services in pod
podman run -d --pod brogue-dev --name brogue-game \
  -v $(pwd)/src:/app/src:z \
  -v $(pwd)/data:/app/data:z \
  brogue:dev
```

**Pros**: One command setup, hot-reload, **pod architecture** (like K8s), rootless security, Phase 2 ready
**Cons**: Podman pod learning curve (simpler than Docker Compose!)
**Recommended for**: Week 2+ once MVP basics working

**Note**: Podman pods are superior to docker-compose for Brogue because they map directly to Kubernetes pods

---

## Podman Strategy

### MVP Containerfile (Phase 1)

**Location**: `docker/Dockerfile.dev` (Podman uses same Dockerfile format!)

```dockerfile
# Brogue MVP Containerfile (Dockerfile)
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
COPY run_textual.py .

# Volume for data persistence
VOLUME ["/app/data"]

# Default command
CMD ["python3", "run_textual.py"]
```

**Build** (rootless by default):
```bash
podman build -t brogue-mvp:latest -f docker/Dockerfile.dev .
```

**Run** (rootless, no daemon needed):
```bash
podman run -it --rm \
  -v $(pwd)/data:/app/data:z \
  brogue-mvp:latest
```

**Note**: The `:z` flag tells Podman to relabel the volume for SELinux compatibility (safe, automatic)

---

### Podman Pod for MVP

**Location**: `scripts/dev-pod.sh`

```bash
#!/bin/bash
# Development pod setup script

# Create pod for MVP development
podman pod create --name brogue-mvp-pod -p 8080:8080

# Build image (if not exists)
podman build -t brogue-mvp:latest -f docker/Dockerfile.dev .

# Run game service with hot-reload
podman run -d \
  --pod brogue-mvp-pod \
  --name brogue-game \
  -v $(pwd)/src:/app/src:z \
  -v $(pwd)/run_textual.py:/app/run_textual.py:z \
  -v $(pwd)/data:/app/data:z \
  brogue-mvp:latest \
  python3 run_textual.py

echo "✅ MVP pod created: brogue-mvp-pod"
echo "📍 Attach to game: podman attach brogue-game"
```

**Usage**:
```bash
# Start development pod
./scripts/dev-pod.sh

# View logs
podman pod logs brogue-mvp-pod

# Run tests in same pod
podman run --rm --pod brogue-mvp-pod \
  -v $(pwd)/src:/app/src:z \
  -v $(pwd)/tests:/app/tests:z \
  brogue-mvp:latest pytest tests/

# Shell access
podman run -it --rm --pod brogue-mvp-pod \
  brogue-mvp:latest bash

# Stop pod
podman pod stop brogue-mvp-pod

# Remove pod
podman pod rm -f brogue-mvp-pod
```

**Why pods over docker-compose?**
- ✅ **Kubernetes-compatible** - Same pod concept
- ✅ **Simpler** - No YAML file needed for simple cases
- ✅ **Faster** - Shared network namespace
- ✅ **Export to K8s** - `podman generate kube` creates K8s manifests

---

### Multi-Stage Dockerfile (Production-Ready)

**Location**: `docker/Dockerfile`

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY src/ ./src/
COPY run_textual.py .

# Create non-root user
RUN useradd -m -u 1000 brogue && chown -R brogue:brogue /app
USER brogue

# Volume for data
VOLUME ["/app/data"]

# Healthcheck (for Phase 2)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "import sys; sys.exit(0)"

CMD ["python3", "run_textual.py"]
```

**Benefits**:
- Smaller image (multi-stage build)
- Security (non-root user)
- Health checks for orchestration
- Production-ready from day 1

---

## Multiplayer Infrastructure (Phase 2)

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              Podman Pods (Dev)                  │
├─────────────────────────────────────────────────┤
│  nginx-pod (tia-proxy)                          │
│    ↓                                            │
│  connection-pod (WebSocket gateway)             │
│    ↓                                            │
│  nats-pod (message bus)                         │
│    ↓                                            │
│  game-instance-pod-N (game logic)               │
│    ↓                                            │
│  postgres-pod (persistence)                     │
│                                                 │
│  prometheus-pod (metrics)                       │
│  grafana-pod (dashboards)                       │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│         Production (systemd + Podman)           │
├─────────────────────────────────────────────────┤
│  nginx-pod (SSL termination)                    │
│    ↓                                            │
│  connection-pod-1, connection-pod-2 (replicas)  │
│    ↓                                            │
│  nats-pod-1, nats-pod-2, nats-pod-3 (cluster)   │
│    ↓                                            │
│  game-instance-pod-N (scaled via systemd)       │
│    ↓                                            │
│  postgres-pod (PostgreSQL or managed RDS)       │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│         Kubernetes (Future - Week 18+)          │
├─────────────────────────────────────────────────┤
│  (Export pods with: podman generate kube)       │
│                                                 │
│  Ingress (SSL termination)                      │
│    ↓                                            │
│  ConnectionService (Deployment, replicas: 2)    │
│    ↓                                            │
│  NATS StatefulSet (cluster, replicas: 3)        │
│    ↓                                            │
│  GameInstance (Deployment, replicas: N)         │
│    ↓                                            │
│  PostgreSQL (StatefulSet or managed RDS)        │
└─────────────────────────────────────────────────┘
```

**Key Insight**: Podman pods → systemd → Kubernetes with zero architecture changes!

---

### Podman Pods for Multiplayer

**Location**: `scripts/multiplayer-pods.sh`

```bash
#!/bin/bash
# Multiplayer pod setup script

# Create network (optional, pods can discover via podman network)
podman network create brogue-net

# Pod 1: NATS Message Bus
podman pod create --name nats-pod --network brogue-net -p 4222:4222 -p 8222:8222
podman run -d --pod nats-pod --name nats \
  -v nats-data:/data \
  nats:latest -js -m 8222

# Pod 2: PostgreSQL Database
podman pod create --name postgres-pod --network brogue-net -p 5432:5432
podman run -d --pod postgres-pod --name postgres \
  -e POSTGRES_USER=brogue \
  -e POSTGRES_PASSWORD=dev \
  -e POSTGRES_DB=brogue \
  -v postgres-data:/var/lib/postgresql/data \
  -v ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro,z \
  --health-cmd "pg_isready -U brogue" \
  --health-interval 10s \
  postgres:15-alpine

# Pod 3-4: Connection Services (2 instances for load balancing)
for i in 1 2; do
  podman pod create --name connection-pod-$i --network brogue-net -p 876$i:8765
  podman run -d --pod connection-pod-$i --name connection-$i \
    -e NATS_URL=nats://nats-pod:4222 \
    -e POSTGRES_URL=postgresql://brogue:dev@postgres-pod:5432/brogue \
    -e LOG_LEVEL=INFO \
    brogue-connection:latest
done

# Pod 5-7: Game Instances (3 instances for testing)
for i in 1 2 3; do
  podman pod create --name game-instance-pod-$i --network brogue-net
  podman run -d --pod game-instance-pod-$i --name game-instance-$i \
    -e NATS_URL=nats://nats-pod:4222 \
    -e POSTGRES_URL=postgresql://brogue:dev@postgres-pod:5432/brogue \
    -e INSTANCE_ID=game-$i \
    -e LOG_LEVEL=DEBUG \
    brogue-game:latest
done

# Pod 8: Prometheus
podman pod create --name prometheus-pod --network brogue-net -p 9090:9090
podman run -d --pod prometheus-pod --name prometheus \
  -v ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro,z \
  -v prometheus-data:/prometheus \
  prom/prometheus:latest

# Pod 9: Grafana
podman pod create --name grafana-pod --network brogue-net -p 3000:3000
podman run -d --pod grafana-pod --name grafana \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -v grafana-data:/var/lib/grafana \
  -v ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro,z \
  grafana/grafana:latest

# Pod 10: nginx (reverse proxy)
podman pod create --name nginx-pod --network brogue-net -p 80:80 -p 443:443
podman run -d --pod nginx-pod --name nginx \
  -v ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro,z \
  -v ./nginx/ssl:/etc/nginx/ssl:ro,z \
  nginx:alpine

echo "✅ Multiplayer pods created!"
echo "📊 Prometheus: http://localhost:9090"
echo "📈 Grafana: http://localhost:3000"
echo "🎮 Game: wss://localhost (via nginx)"
```

**Usage**:
```bash
# Start full multiplayer stack
./scripts/multiplayer-pods.sh

# List all pods
podman pod ls

# Check pod status
podman pod ps -a

# View logs for specific pod
podman pod logs nats-pod
podman pod logs game-instance-pod-1

# Scale game instances (add more pods)
for i in 4 5; do
  podman pod create --name game-instance-pod-$i --network brogue-net
  podman run -d --pod game-instance-pod-$i --name game-instance-$i \
    -e NATS_URL=nats://nats-pod:4222 \
    -e INSTANCE_ID=game-$i \
    brogue-game:latest
done

# Stop all pods
podman pod stop nats-pod postgres-pod connection-pod-{1,2} \
  game-instance-pod-{1,2,3} prometheus-pod grafana-pod nginx-pod

# Remove all pods
podman pod rm -f nats-pod postgres-pod connection-pod-{1,2} \
  game-instance-pod-{1,2,3} prometheus-pod grafana-pod nginx-pod
```

**Export to Kubernetes**:
```bash
# Generate Kubernetes YAML for each pod
podman generate kube nats-pod > k8s/nats.yaml
podman generate kube postgres-pod > k8s/postgres.yaml
podman generate kube connection-pod-1 > k8s/connection.yaml
podman generate kube game-instance-pod-1 > k8s/game-instance.yaml
podman generate kube prometheus-pod > k8s/prometheus.yaml
podman generate kube grafana-pod > k8s/grafana.yaml
podman generate kube nginx-pod > k8s/nginx.yaml

# Deploy to Kubernetes (when ready)
kubectl apply -f k8s/
```

**Why Podman pods over Docker Compose?**
1. **Pod architecture** - Maps directly to Kubernetes pods
2. **Kubernetes export** - `podman generate kube` creates production-ready manifests
3. **Rootless** - Better security (no root daemon)
4. **Systemd integration** - Each pod becomes a systemd unit
5. **Zero migration** - Dev pods → systemd → Kubernetes with no changes

---

### Service Dockerfiles

#### Connection Service Dockerfile

**Location**: `docker/Dockerfile.connection`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.multiplayer.txt .
RUN pip install --no-cache-dir -r requirements.multiplayer.txt

# Copy service code
COPY src/services/connection/ ./src/services/connection/
COPY src/brogue/ ./src/brogue/

# Non-root user
RUN useradd -m -u 1000 brogue && chown -R brogue:brogue /app
USER brogue

EXPOSE 8080

CMD ["python3", "-m", "src.services.connection.main"]
```

#### Game Instance Dockerfile

**Location**: `docker/Dockerfile.game`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.multiplayer.txt .
RUN pip install --no-cache-dir -r requirements.multiplayer.txt

# Copy game code
COPY src/core/ ./src/core/
COPY src/services/game/ ./src/services/game/
COPY data/ ./data/

# Non-root user
RUN useradd -m -u 1000 brogue && chown -R brogue:brogue /app
USER brogue

CMD ["python3", "-m", "src.services.game.main"]
```

---

## Kubernetes Deployment (Production)

### Namespace

**Location**: `k8s/namespace.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: brogue
  labels:
    app: brogue
    env: production
```

---

### NATS StatefulSet

**Location**: `k8s/nats-statefulset.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nats
  namespace: brogue
spec:
  selector:
    app: nats
  ports:
    - name: client
      port: 4222
      targetPort: 4222
    - name: monitoring
      port: 8222
      targetPort: 8222
  clusterIP: None  # Headless service for StatefulSet

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: nats
  namespace: brogue
spec:
  serviceName: nats
  replicas: 3
  selector:
    matchLabels:
      app: nats
  template:
    metadata:
      labels:
        app: nats
    spec:
      containers:
      - name: nats
        image: nats:latest
        args:
          - "-js"
          - "-m"
          - "8222"
          - "--cluster"
          - "nats://0.0.0.0:6222"
          - "--routes"
          - "nats://nats-0.nats:6222,nats://nats-1.nats:6222,nats://nats-2.nats:6222"
        ports:
          - containerPort: 4222
            name: client
          - containerPort: 8222
            name: monitoring
          - containerPort: 6222
            name: cluster
        volumeMounts:
          - name: nats-data
            mountPath: /data
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
  volumeClaimTemplates:
    - metadata:
        name: nats-data
      spec:
        accessModes: [ "ReadWriteOnce" ]
        resources:
          requests:
            storage: 1Gi
```

---

### Connection Service Deployment

**Location**: `k8s/connection-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: connection-service
  namespace: brogue
spec:
  replicas: 2
  selector:
    matchLabels:
      app: connection-service
  template:
    metadata:
      labels:
        app: connection-service
    spec:
      containers:
      - name: connection-service
        image: brogue-connection:v1.0.0
        env:
          - name: NATS_URL
            value: "nats://nats:4222"
          - name: POSTGRES_URL
            valueFrom:
              secretKeyRef:
                name: db-credentials
                key: connection-string
        ports:
          - containerPort: 8080
            name: websocket
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: connection-service
  namespace: brogue
spec:
  selector:
    app: connection-service
  ports:
    - port: 8080
      targetPort: 8080
  type: ClusterIP
```

---

### Game Instance Deployment

**Location**: `k8s/game-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: game-instance
  namespace: brogue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: game-instance
  template:
    metadata:
      labels:
        app: game-instance
    spec:
      containers:
      - name: game-instance
        image: brogue-game:v1.0.0
        env:
          - name: NATS_URL
            value: "nats://nats:4222"
          - name: POSTGRES_URL
            valueFrom:
              secretKeyRef:
                name: db-credentials
                key: connection-string
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
        livenessProbe:
          exec:
            command:
              - python3
              - -c
              - "import sys; sys.exit(0)"
          initialDelaySeconds: 15
          periodSeconds: 60
```

---

### Ingress (SSL Termination)

**Location**: `k8s/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: brogue-ingress
  namespace: brogue
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/websocket-services: "connection-service"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - brogue.example.com
      secretName: brogue-tls
  rules:
    - host: brogue.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: connection-service
                port:
                  number: 8080
```

---

## Production Deployment

### Deployment Workflow (Podman + systemd)

```bash
# 1. Build images
podman build -t brogue-connection:v1.0.0 -f docker/Dockerfile.connection .
podman build -t brogue-game:v1.0.0 -f docker/Dockerfile.game .

# 2. Push to registry (optional, or export/import)
podman tag brogue-connection:v1.0.0 registry.example.com/brogue-connection:v1.0.0
podman push registry.example.com/brogue-connection:v1.0.0

podman tag brogue-game:v1.0.0 registry.example.com/brogue-game:v1.0.0
podman push registry.example.com/brogue-game:v1.0.0

# 3. Create pods on production server
./scripts/multiplayer-pods.sh

# 4. Generate systemd units for each pod
podman generate systemd --new --name nats-pod --files
podman generate systemd --new --name postgres-pod --files
podman generate systemd --new --name connection-pod-1 --files
podman generate systemd --new --name connection-pod-2 --files
podman generate systemd --new --name game-instance-pod-1 --files
podman generate systemd --new --name game-instance-pod-2 --files
podman generate systemd --new --name game-instance-pod-3 --files
podman generate systemd --new --name prometheus-pod --files
podman generate systemd --new --name grafana-pod --files
podman generate systemd --new --name nginx-pod --files

# 5. Move systemd units to system directory
sudo mv *.service /etc/systemd/system/

# 6. Reload systemd and enable pods
sudo systemctl daemon-reload
sudo systemctl enable --now pod-nats-pod
sudo systemctl enable --now pod-postgres-pod
sudo systemctl enable --now pod-connection-pod-1
sudo systemctl enable --now pod-connection-pod-2
sudo systemctl enable --now pod-game-instance-pod-{1,2,3}
sudo systemctl enable --now pod-prometheus-pod
sudo systemctl enable --now pod-grafana-pod
sudo systemctl enable --now pod-nginx-pod

# 7. Verify deployment
systemctl status pod-nats-pod
systemctl status pod-game-instance-pod-1
journalctl -u pod-game-instance-pod-1 -f
```

**Benefits of Podman + systemd**:
- ✅ Pods start automatically on boot
- ✅ systemd manages restarts
- ✅ Integrated logging (journald)
- ✅ Resource limits (cgroups)
- ✅ No manual process management

---

### Zero-Downtime Deployment (Podman + systemd)

```bash
# Option 1: Blue-Green Deployment with Podman
# Create new pods with updated image
./scripts/multiplayer-pods-v2.sh  # Uses v1.1.0 images, new pod names

# Test new pods
curl http://localhost:8767/health  # connection-pod-3 (new)

# Update nginx to route to new pods
# Edit nginx.conf upstream to include new pods

# Reload nginx (zero downtime)
systemctl reload pod-nginx-pod

# Stop old pods
systemctl stop pod-connection-pod-1 pod-connection-pod-2

# Option 2: Rolling Update (manual)
# Update one pod at a time
systemctl stop pod-game-instance-pod-1
podman pod rm -f game-instance-pod-1
# Recreate with new image
podman pod create --name game-instance-pod-1 --network brogue-net
podman run -d --pod game-instance-pod-1 --name game-instance-1 brogue-game:v1.1.0
# Generate new systemd unit
podman generate systemd --new --name game-instance-pod-1 --files
sudo mv pod-game-instance-pod-1.service /etc/systemd/system/
sudo systemctl daemon-reload
systemctl start pod-game-instance-pod-1

# Repeat for pod-2, pod-3, etc.

# Option 3: Migrate to Kubernetes for native rolling updates
podman generate kube game-instance-pod-1 > k8s/game-instance.yaml
kubectl apply -f k8s/game-instance.yaml
kubectl set image deployment/game-instance game-instance=brogue-game:v1.1.0
kubectl rollout status deployment/game-instance
```

---

## Monitoring & Observability

### Prometheus Metrics

**Expose from each service**:
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
players_connected = Gauge('brogue_players_connected', 'Number of connected players')
actions_processed = Counter('brogue_actions_total', 'Total actions processed')
action_latency = Histogram('brogue_action_latency_seconds', 'Action processing latency')

# Start metrics server
start_http_server(9090)
```

**Scrape with Prometheus**:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'brogue-connection'
    static_configs:
      - targets: ['connection-service:9090']

  - job_name: 'brogue-game'
    static_configs:
      - targets: ['game-instance:9090']
```

---

### Grafana Dashboard

**Key Metrics to Track**:
- Players connected (real-time)
- Actions per second
- Action latency (p50, p95, p99)
- Game instances running
- NATS message throughput
- Database query times
- Error rates

---

## Cost Analysis

### MVP (Phase 1) - $0/month

**Local Development**:
- Free (runs on dev machine)
- Optional: Docker Desktop (free for personal use)

---

### Multiplayer Dev/Test (Phase 2) - $5-10/month

**Small VPS (DigitalOcean/Linode)**:
- 2 vCPU, 4GB RAM: $12/month
- Runs full Docker Compose stack
- 4-10 concurrent players
- Good for testing

---

### Multiplayer Production - $40-200/month

**Kubernetes on Managed Service**:

| Load | Setup | Cost/Month |
|------|-------|------------|
| 10 players | 1 node (2 vCPU, 4GB) | $40 |
| 50 players | 2 nodes (4 vCPU, 8GB) | $80 |
| 200 players | 4 nodes (8 vCPU, 16GB) | $160 |

**Managed Services**:
- Managed Kubernetes (GKE/EKS/AKS): +$70/month (control plane)
- Managed PostgreSQL (RDS): +$20-50/month
- Load Balancer: +$10/month

**Total Estimate**:
- Small (10 players): $50-70/month
- Medium (50 players): $100-150/month
- Large (200 players): $200-300/month

---

## Implementation Timeline

### MVP (Phase 1) - Weeks 1-6

**Week 1**:
- [ ] Create Dockerfile.dev
- [ ] Test local Docker build
- [ ] Document Docker workflow

**Week 2**:
- [ ] Create docker-compose.dev.yml
- [ ] Test hot-reload
- [ ] Update README with Docker instructions

**Weeks 3-6**:
- [ ] Use Docker for development
- [ ] Create multi-stage Dockerfile (production-ready)

---

### Multiplayer (Phase 2) - Weeks 7-18

**Weeks 7-8**:
- [ ] Create service Dockerfiles
- [ ] Create docker-compose.multiplayer.yml
- [ ] Test full stack locally

**Weeks 9-10**:
- [ ] Write Kubernetes manifests
- [ ] Test on local Kubernetes (minikube/kind)
- [ ] Document deployment process

**Weeks 11-12**:
- [ ] Deploy to staging (small VPS)
- [ ] Load testing
- [ ] Monitoring setup

**Weeks 13-18**:
- [ ] Production deployment
- [ ] Scaling tests
- [ ] Incident response playbook

---

## Quick Reference

### Essential Podman Commands

```bash
# MVP Development
./scripts/dev-pod.sh
podman pod stop brogue-mvp-pod
podman pod start brogue-mvp-pod
podman pod logs brogue-mvp-pod

# Multiplayer Development
./scripts/multiplayer-pods.sh
podman pod ls
podman pod ps -a
podman pod logs game-instance-pod-1
podman pod stop --all
podman pod start --all

# Production (Podman + systemd)
systemctl status pod-game-instance-pod-1
systemctl restart pod-game-instance-pod-1
journalctl -u pod-game-instance-pod-1 -f

# Scale game instances (create more pods)
for i in 4 5 6; do
  podman pod create --name game-instance-pod-$i --network brogue-net
  podman run -d --pod game-instance-pod-$i brogue-game:latest
  podman generate systemd --new --name game-instance-pod-$i --files
  sudo mv pod-game-instance-pod-$i.service /etc/systemd/system/
  sudo systemctl daemon-reload
  systemctl enable --now pod-game-instance-pod-$i
done

# Export to Kubernetes
podman generate kube <pod-name> > k8s/<pod-name>.yaml
kubectl apply -f k8s/

# Kubernetes Production (future)
kubectl get pods -n brogue
kubectl logs -f -n brogue deployment/game-instance
kubectl scale deployment/game-instance --replicas=10 -n brogue
```

### Pod Management Cheat Sheet

```bash
# List all pods
podman pod ls

# View pod details
podman pod inspect <pod-name>

# View pod logs
podman pod logs <pod-name>
podman pod logs -f <pod-name>  # Follow logs

# Start/stop pods
podman pod start <pod-name>
podman pod stop <pod-name>
podman pod restart <pod-name>

# Remove pods
podman pod rm <pod-name>
podman pod rm -f <pod-name>  # Force remove

# List containers in pod
podman ps -a --pod --filter pod=<pod-name>

# Execute command in pod container
podman exec -it <container-name> bash

# View resource usage
podman pod stats <pod-name>

# Generate Kubernetes YAML
podman generate kube <pod-name>

# Generate systemd unit
podman generate systemd --new --name <pod-name> --files
```

### Docker → Podman Migration

```bash
# Most Docker commands work with Podman!
# Just replace 'docker' with 'podman'

# Create alias for seamless migration
alias docker=podman
alias docker-compose=podman-compose

# Docker commands that work with Podman:
podman run ...        # Same as docker run
podman build ...      # Same as docker build
podman ps             # Same as docker ps
podman images         # Same as docker images
podman exec ...       # Same as docker exec
podman logs ...       # Same as docker logs

# Podman-specific (not in Docker):
podman pod create ...
podman pod start ...
podman generate kube ...
podman generate systemd ...
```

---

### Directory Structure

```
brogue/
├── docker/
│   ├── Dockerfile.dev              # MVP development
│   ├── Dockerfile                  # Production multi-stage
│   ├── Dockerfile.connection       # Connection service
│   ├── Dockerfile.game             # Game instance
│   ├── docker-compose.dev.yml      # MVP dev stack
│   ├── docker-compose.multiplayer.yml  # Full multiplayer stack
│   └── nginx/
│       └── nginx.conf              # Reverse proxy config
├── k8s/
│   ├── namespace.yaml
│   ├── nats-statefulset.yaml
│   ├── postgres-statefulset.yaml
│   ├── connection-deployment.yaml
│   ├── game-deployment.yaml
│   └── ingress.yaml
└── scripts/
    ├── build-images.sh
    ├── deploy-dev.sh
    └── deploy-prod.sh
```

---

## Next Steps

1. **This Week** (MVP Week 1):
   - [ ] Install Podman (`sudo apt-get install podman`)
   - [ ] Create `docker/Dockerfile.dev` (works with Podman!)
   - [ ] Test Podman build locally
   - [ ] Create `scripts/dev-pod.sh` for MVP development
   - [ ] Optional: `alias docker=podman` for seamless transition

2. **Week 2**:
   - [ ] Create pod-based development environment
   - [ ] Test hot-reload with pod volumes
   - [ ] Practice `podman pod` commands
   - [ ] Verify SELinux compatibility (`:z` flags)

3. **Before Phase 2** (Week 6):
   - [ ] Create production Containerfiles (Dockerfiles)
   - [ ] Test systemd integration (`podman generate systemd`)
   - [ ] Review Kubernetes migration path
   - [ ] Plan infrastructure costs

4. **Phase 2** (Week 7-12):
   - [ ] Create `scripts/multiplayer-pods.sh`
   - [ ] Generate systemd units for all pods
   - [ ] Deploy to production with systemd
   - [ ] Monitor with Prometheus/Grafana

5. **Phase 3** (Week 18+):
   - [ ] Export pods to Kubernetes YAML (`podman generate kube`)
   - [ ] Test K8s deployment locally (minikube)
   - [ ] Deploy to production Kubernetes cluster
   - [ ] Celebrate seamless migration! 🎉

---

**Status**: Ready for MVP implementation with Podman from day 1

**Key Insight**: Pods aren't overhead—they're the foundation for security, scalability, and seamless Kubernetes migration.

**Decision**: Podman over Docker for:
- 🔒 **Rootless security** - No root daemon to exploit
- 🎯 **Pod architecture** - Practice Kubernetes patterns from day 1
- 🔄 **Zero refactoring** - Dev → systemd → K8s with same pods
- 🚀 **Native systemd** - Production deployment is `systemctl enable`
- 📦 **K8s migration** - `podman generate kube` creates manifests

🐳 **Start with Podman pods, migrate to Kubernetes with zero pain.**
