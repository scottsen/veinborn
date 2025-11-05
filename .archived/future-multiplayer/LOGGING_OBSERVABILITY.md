# Brogue Logging & Observability

**Document Type:** Operational Guide
**Audience:** SRE, DevOps, Backend Developers
**Status:** Active
**Last Updated:** 2025-10-23

---

## Overview

Distributed systems require comprehensive observability. This document defines logging, metrics, and monitoring for operational excellence.

**The Three Pillars:**
1. **Logs** - What happened (events, errors)
2. **Metrics** - How much/how fast (counters, gauges, histograms)
3. **Traces** - Where did requests go (request flow across services)

---

## 1. Structured Logging

### Setup (structlog)

```python
# brogue/logging/setup.py
import structlog
import logging
import sys

def setup_logging(
    level: str = "INFO",
    json_logs: bool = True,
    service_name: str = "brogue"
):
    """Configure structured logging"""

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper())
    )

    processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        # Production: JSON output
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Development: Pretty console output
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set global context
    structlog.contextvars.bind_contextvars(
        service=service_name,
        environment="production"
    )
```

### Context-Aware Logger

```python
# brogue/logging/logger.py
import structlog
from contextvars import ContextVar
import uuid

# Context variables for tracing
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
player_id_ctx: ContextVar[str] = ContextVar("player_id", default="")
party_id_ctx: ContextVar[str] = ContextVar("party_id", default="")

def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get logger with automatic context"""
    logger = structlog.get_logger(name)

    # Bind context variables
    ctx = {}
    if request_id := request_id_ctx.get():
        ctx["request_id"] = request_id
    if player_id := player_id_ctx.get():
        ctx["player_id"] = player_id
    if party_id := party_id_ctx.get():
        ctx["party_id"] = party_id

    return logger.bind(**ctx) if ctx else logger

class LogContext:
    """Context manager for scoped logging context"""

    def __init__(
        self,
        request_id: str = None,
        player_id: str = None,
        party_id: str = None
    ):
        self.request_id = request_id or str(uuid.uuid4())
        self.player_id = player_id
        self.party_id = party_id
        self.tokens = []

    def __enter__(self):
        self.tokens.append(request_id_ctx.set(self.request_id))
        if self.player_id:
            self.tokens.append(player_id_ctx.set(self.player_id))
        if self.party_id:
            self.tokens.append(party_id_ctx.set(self.party_id))
        return self

    def __exit__(self, *args):
        for token in self.tokens:
            if token:
                token.var.reset(token)
```

### Usage Examples

```python
from brogue.logging.logger import get_logger, LogContext

logger = get_logger(__name__)

# Simple logging
logger.info("server_started", port=8765)

# With context
with LogContext(player_id="alice", party_id="dragon_slayers"):
    logger.info("processing_action", action_type="move")
    # All logs in this scope include player_id and party_id

# Output (JSON):
# {
#   "event": "processing_action",
#   "action_type": "move",
#   "player_id": "alice",
#   "party_id": "dragon_slayers",
#   "request_id": "550e8400-...",
#   "timestamp": "2025-10-23T14:30:00Z",
#   "level": "info",
#   "service": "brogue-game-instance"
# }
```

### What to Log

#### Request Lifecycle
```python
logger.info("request_received", method="POST", path="/api/action")
logger.info("request_completed", duration_ms=42, status=200)
```

#### Performance
```python
from contextlib import contextmanager
import time

@contextmanager
def log_duration(operation: str, **context):
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"{operation}_completed",
            duration_ms=round(duration_ms, 2),
            **context
        )

# Usage:
with log_duration("game_tick", tick=1234):
    process_tick()
```

#### Critical Events
```python
logger.warning(
    "critical_event",
    event_type="legacy_ore_collected",
    player_id="alice",
    ore_quality=98
)
```

#### Errors
```python
try:
    await dangerous_operation()
except Exception as e:
    logger.error(
        "operation_failed",
        operation="save_dungeon",
        error=str(e),
        exc_info=True  # Include stack trace
    )
```

---

## 2. Metrics (Prometheus)

### Setup

```python
# brogue/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# ===== Counters (monotonically increasing) =====
player_actions_total = Counter(
    'brogue_player_actions_total',
    'Total player actions processed',
    ['action_type', 'success']
)

critical_events_total = Counter(
    'brogue_critical_events_total',
    'Critical game events',
    ['event_type']
)

# ===== Histograms (latency distributions) =====
action_duration = Histogram(
    'brogue_action_duration_seconds',
    'Time to process player action',
    ['action_type'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

game_tick_duration = Histogram(
    'brogue_game_tick_duration_seconds',
    'Game tick processing time',
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5]
)

# ===== Gauges (current state) =====
active_players = Gauge(
    'brogue_active_players',
    'Number of currently connected players'
)

active_parties = Gauge(
    'brogue_active_parties',
    'Number of active game parties'
)

nats_connected = Gauge(
    'brogue_nats_connected',
    'NATS connection status (1=connected, 0=disconnected)'
)

# Start metrics endpoint
def start_metrics_server(port: int = 9090):
    """Start Prometheus metrics HTTP server"""
    start_http_server(port)
    logger.info("metrics_server_started", port=port)
```

### Usage in Code

```python
from brogue.monitoring.metrics import (
    player_actions_total,
    action_duration,
    active_players
)

# Increment counter
player_actions_total.labels(action_type="move", success="true").inc()

# Record duration
with action_duration.labels(action_type="move").time():
    await process_move_action(action)

# Set gauge
active_players.set(len(connected_players))
```

### Grafana Dashboard Queries

```promql
# Actions per second
rate(brogue_player_actions_total[1m])

# Average action latency
rate(brogue_action_duration_seconds_sum[5m]) / rate(brogue_action_duration_seconds_count[5m])

# 95th percentile tick duration
histogram_quantile(0.95, rate(brogue_game_tick_duration_seconds_bucket[5m]))

# Error rate
rate(brogue_player_actions_total{success="false"}[5m]) / rate(brogue_player_actions_total[5m])

# Active players (current)
brogue_active_players
```

---

## 3. Distributed Tracing

### Request ID Propagation

```python
# Client sends action
action = MoveAction(player_id="alice", direction="north")
# action.message_id = "550e8400-..."

# ConnectionService receives
with LogContext(request_id=action.message_id):
    logger.info("websocket_message_received")
    await route_to_nats(action)

# GameInstance processes
with LogContext(request_id=action.message_id):
    logger.info("action_received", action_type="move")
    await process(action)

# All logs have same request_id → full trace!
```

### Trace Query

```bash
# Find all logs for a request
cat logs/*.log | jq 'select(.request_id == "550e8400-...")' | jq -s 'sort_by(.timestamp)'
```

---

## 4. Log Aggregation

### ELK Stack (Production)

```yaml
# docker-compose.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

```conf
# logstash.conf
input {
  file {
    path => "/var/log/brogue/*.log"
    codec => "json"
  }
}

filter {
  # Already JSON, no parsing needed!
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "brogue-logs-%{+YYYY.MM.dd}"
  }
}
```

### Query Examples (Kibana)

```
# All errors for a player
player_id:"alice" AND level:"error"

# Slow operations
duration_ms:>100

# Critical events
event:"critical_event" AND event_type:"legacy_ore_collected"

# Errors in last hour
level:"error" AND @timestamp:[now-1h TO now]
```

---

## 5. Alerting

### Alert Definitions

```yaml
# prometheus/alerts.yml
groups:
  - name: brogue_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          rate(brogue_player_actions_total{success="false"}[5m])
          / rate(brogue_player_actions_total[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate (>5%)"

      # Slow game ticks
      - alert: SlowGameTicks
        expr: |
          histogram_quantile(0.95,
            rate(brogue_game_tick_duration_seconds_bucket[5m])
          ) > 0.15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Game ticks slow (p95 > 150ms)"

      # NATS disconnected
      - alert: NATSDisconnected
        expr: brogue_nats_connected == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "NATS connection lost!"

      # No players (possible crash)
      - alert: NoActivePlayers
        expr: brogue_active_players == 0
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "No active players for 10 minutes"
```

---

## 6. Operational Runbooks

### High Error Rate

**Alert:** HighErrorRate
**Severity:** Warning

**Investigation:**
1. Check logs: `cat logs/brogue.log | jq 'select(.level == "error")' | tail -20`
2. Identify error types: `... | jq -r '.error_type' | sort | uniq -c`
3. Check metrics: Grafana → Actions panel → Filter by `success=false`

**Common Causes:**
- Invalid client messages → Check MessageRegistry validation
- Database errors → Check `db_url` connectivity
- NATS errors → Check NATS cluster health

### Slow Game Ticks

**Alert:** SlowGameTicks
**Severity:** Warning

**Investigation:**
1. Check tick duration logs: `... | jq 'select(.event == "game_tick_completed")'`
2. Identify slow systems: Check system-specific duration metrics
3. Profile code: Add timing around suspect systems

**Common Causes:**
- Too many entities (monsters, loot) → Optimize culling
- Database query in tick loop → Move to background job
- Expensive calculations → Cache or precompute

### NATS Disconnected

**Alert:** NATSDisconnected
**Severity:** Critical

**Immediate Action:**
1. Check NATS cluster: `nats-server -sl show`
2. Check network: `ping nats-server-host`
3. Restart service: `systemctl restart brogue-game-instance`

**Prevention:**
- Use NATS cluster (3+ nodes) for HA
- Configure auto-reconnect in client

---

## 7. Performance Monitoring

### Key Metrics Dashboard

```
┌─────────────────────────────────────────────┐
│  Brogue Performance Dashboard               │
├─────────────────────────────────────────────┤
│  Active Players: 127                        │
│  Active Parties: 32                         │
│  Actions/sec: 245                           │
│  Error Rate: 0.3%                           │
├─────────────────────────────────────────────┤
│  Game Tick Duration (p50/p95/p99):          │
│    42ms / 87ms / 132ms                      │
│                                             │
│  Action Processing (p50/p95/p99):           │
│    8ms / 24ms / 45ms                        │
├─────────────────────────────────────────────┤
│  NATS: Connected (3/3 nodes)                │
│  Database: Healthy (12ms query latency)     │
│  Memory: 2.4GB / 4GB                        │
│  CPU: 45%                                   │
└─────────────────────────────────────────────┘
```

---

## 8. Development Logging

### Log Sampling (High Frequency)

```python
import random

class LogSampler:
    def __init__(self, sample_rate: float = 0.1):
        self.sample_rate = sample_rate

    def should_log(self) -> bool:
        return random.random() < self.sample_rate

# Log only 10% of ticks
tick_sampler = LogSampler(sample_rate=0.1)

async def game_tick():
    if tick_sampler.should_log():
        logger.debug("game_tick", tick=self.tick)

    # Always log slow ticks
    if duration > 100:
        logger.warning("slow_tick", tick=self.tick, duration_ms=duration)
```

### Hot-Reload Logging Config

```python
# Change log level without restart
import signal

def reload_logging_config(signum, frame):
    """Reload logging on SIGHUP"""
    new_level = os.getenv("BROGUE_LOG_LEVEL", "INFO")
    logging.root.setLevel(getattr(logging, new_level))
    logger.info("log_level_changed", new_level=new_level)

signal.signal(signal.SIGHUP, reload_logging_config)

# Usage:
# kill -HUP <process_id>
```

---

## References

- [structlog Documentation](https://www.structlog.org/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [ELK Stack](https://www.elastic.co/elastic-stack)

---

**Next Steps:**
1. Set up structlog in `main.py`
2. Add metrics to key code paths
3. Create Grafana dashboard
4. Configure alerts
5. Test log aggregation (ELK or Loki)
