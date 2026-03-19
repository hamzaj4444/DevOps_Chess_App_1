# DevOps Chess App

> A full-stack, AI-powered chess application built with FastAPI, PyTorch, and a complete DevOps pipeline — containerised with Docker, orchestrated on Kubernetes, and monitored with Prometheus, Loki, and Grafana.

[![CI/CD](https://img.shields.io/github/actions/workflow/status/hamzaj4444/DevOps_Chess_App_1/ci.yml?label=CI%2FCD&style=flat-square)](https://github.com/hamzaj4444/DevOps_Chess_App_1/actions)
[![Docker Image](https://img.shields.io/badge/Docker_Hub-hamzaj4444%2Fdevops--chess--app-blue?style=flat-square&logo=docker)](https://hub.docker.com/r/hamzaj4444/devops-chess-app)
[![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.35-blue?style=flat-square&logo=kubernetes)](https://kubernetes.io/)

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Backend API](#backend-api)
  - [Endpoints](#endpoints)
  - [Authentication](#authentication)
  - [Custom Prometheus Metrics](#custom-prometheus-metrics)
- [AI Chess Engine](#ai-chess-engine)
- [Frontend](#frontend)
- [Docker & Containerisation](#docker--containerisation)
  - [Multi-Stage Dockerfile](#multi-stage-dockerfile)
  - [Docker Compose Stack](#docker-compose-stack)
- [Observability Stack](#observability-stack)
  - [Prometheus](#prometheus)
  - [Loki + Promtail](#loki--promtail)
  - [Grafana Dashboards](#grafana-dashboards)
- [CI/CD Pipeline](#cicd-pipeline)
- [Kubernetes Deployment](#kubernetes-deployment)
  - [Cluster Setup](#cluster-setup)
  - [Manifest Inventory](#manifest-inventory)
  - [Grafana Auto-Provisioning](#grafana-auto-provisioning)
  - [Accessing Services](#accessing-services)
- [Environment Variables & Secrets](#environment-variables--secrets)
- [Running Locally](#running-locally)
- [Running on Kubernetes](#running-on-kubernetes)
- [Testing](#testing)
- [Known Limitations & Future Work](#known-limitations--future-work)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Host / Browser                          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                    Nginx (Reverse Proxy)                        │
│         nginx:alpine  |  ClusterIP :80  |  K8s: nginx-service  │
└─────────────┬──────────────────────────────────────────────────┘
              │ upstream: chess-service:8000
              ▼
┌─────────────────────────────────────────────────────────────────┐
│               FastAPI Backend  (chess-service:8000)             │
│  - REST API (auth, stats, chess engine, metrics)                │
│  - PyTorch AI chess bot                                         │
│  - Static frontend at /game/                                    │
│  - Prometheus metrics at /metrics                               │
└────┬───────────────────────────────────┬───────────────────────┘
     │ scrape /metrics                   │ log output
     ▼                                   ▼
┌──────────────┐              ┌──────────────────────────┐
│  Prometheus  │              │ Promtail (DaemonSet)      │
│  :9090       │              │ reads /var/run/docker.sock│
└──────┬───────┘              └────────────┬─────────────┘
       │ PromQL                            │ push logs
       ▼                                   ▼
┌──────────────────────────────────────────────────┐
│                   Grafana  :3000                  │
│  datasources: Prometheus + Loki (auto-provisioned)│
│  dashboards: chess-dashboard.json (auto-provisioned)│
└──────────────────────────────────────────────────┘
                        ▲
              ┌─────────┘
              │ log queries
     ┌────────────────┐
     │   Loki :3100   │
     └────────────────┘
```

---

## Project Structure

```
DevOps_chess_app/
├── app/
│   ├── main.py              # FastAPI app factory, middleware, root routes
│   ├── auth.py              # JWT token creation + dependency injection
│   ├── users.py             # In-memory user store with bcrypt hashes
│   ├── metrics.py           # All prometheus_client instruments
│   ├── stats.py             # Chess.com public API client
│   ├── logger.py            # Centralised Python logger
│   ├── chess/
│   │   └── routes.py        # Chess game session lifecycle + AI move endpoints
│   └── static/chess/
│       ├── index.html       # Single-page Glassmorphism UI
│       ├── index.css        # Glassmorphism stylesheet
│       └── app.js           # chess.js integration + async fetch to backend
├── kubernetes/
│   ├── chess-deployment.yaml         # Deployment + Service + Secret
│   ├── nginx-configmap.yaml          # Nginx virtual host config (ConfigMap)
│   ├── nginx-deployment.yaml         # Nginx Deployment
│   ├── nginx-service.yaml            # ClusterIP Service
│   ├── prometheus.yaml               # Deployment + Service + ConfigMap + PVC
│   ├── loki.yaml                     # Deployment + Service + ConfigMap + PVC
│   ├── promtail.yaml                 # DaemonSet + ConfigMap
│   ├── grafana.yaml                  # Deployment + Service + PVC
│   ├── grafana-provisioning-cm.yaml  # Dashboard provider config
│   ├── grafana-datasources-cm.yaml   # Auto-provisioned Prometheus + Loki
│   └── grafana-dashboard-cm.yaml     # chess-dashboard.json as ConfigMap
├── loki/
│   ├── loki-config.yaml         # Loki storage, schema, retention config
│   ├── promtail-config.yaml     # Promtail scrape + relabel config
│   └── chess-dashboard.json     # Grafana dashboard definition
├── prometheus/
│   └── prometheus.yml           # Prometheus scrape jobs
├── nginx/
│   └── nginx.conf               # Nginx upstream + location config
├── tests/
│   └── test_chess.py            # pytest integration test suite
├── Dockerfile                   # Multi-stage production image
├── docker-compose.yml           # Full local stack (6 services)
├── requirements.txt             # Python dependencies
├── install_k8s.sh               # kubectl + minikube installer script
└── .github/
    └── workflows/
        └── ci.yml               # GitHub Actions 4-stage CI/CD pipeline
```

---

## Backend API

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET`  | `/health` | ❌ | Liveness probe — returns `{"status": "ok"}` |
| `POST` | `/login` | ❌ | Accepts `username` + `password` query params, returns a signed JWT |
| `GET`  | `/stats` | ✅ JWT | Proxies the Chess.com public API for player statistics |
| `GET`  | `/metrics` | ❌ | Prometheus text-format exposition |
| `POST` | `/chess/game/new` | ❌ | Creates a new stateful game session, returns `game_id` |
| `POST` | `/chess/game/{game_id}` | ❌ | Submits player move (UCI string), returns AI's response move |
| `GET`  | `/chess/move` | ❌ | Stateless — accepts `fen` query param, returns single best move |
| `GET`  | `/game/` | ❌ | Serves the static HTML frontend (mounted via `StaticFiles`) |

### Authentication

JWT tokens are generated and verified using `PyJWT`. Passwords are stored as bcrypt hashes via `passlib[bcrypt]`.

**Login flow:**
```
POST /login?username=admin&password=admin123
→ 200 OK {"access_token": "<JWT>"}

GET /stats
Authorization: Bearer <JWT>
→ 200 OK {rapid: {...}, blitz: {...}, bullet: {...}}
```

The JWT secret is read from the `JWT_SECRET` environment variable at runtime (falls back to a dev placeholder if unset). Token expiry is currently set to 30 minutes.

> ⚠️ **Security Note**: The current user store is an in-memory Python dict in `app/users.py`. This is appropriate for a single-user development environment but should be replaced with a proper database in production.

### Custom Prometheus Metrics

All instruments are defined in `app/metrics.py` and exposed at `GET /metrics`:

| Instrument | Name | Type | Labels |
|---|---|---|---|
| HTTP request count | `http_requests_total` | `Counter` | `method`, `endpoint`, `status` |
| HTTP latency | `http_request_latency_seconds` | `Histogram` | `endpoint` |
| Failed logins | `login_failures_total` | `Counter` | — |
| Chess.com API errors | `chess_api_errors_total` | `Counter` | — |
| Games started | `chess_games_total` | `Counter` | — |
| Moves made | `chess_moves_total` | `Counter` | `color` (player/bot) |
| Bot computation time | `chess_bot_move_duration_seconds` | `Histogram` | — (buckets: 0.1s–10s) |
| Active sessions | `chess_games_active` | `Gauge` | — |
| Game results | `chess_game_outcomes_total` | `Counter` | `result` |

Metrics are collected via a FastAPI HTTP middleware in `main.py`:

```python
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    return response
```

---

## AI Chess Engine

The chess bot is a custom **PyTorch neural network** (CPU-only) integrated via the `app/chess/` module.

**Dependencies:**
```
torch            # CPU-only wheel via --extra-index-url https://download.pytorch.org/whl/cpu
python-chess     # FEN parsing, legal move generation, board manipulation
numpy            # Tensor input construction
```

**Session lifecycle:**
```
POST /chess/game/new
  → Initialises board, stores in in-memory dict with UUID key
  → Returns: {"game_id": "<uuid>", "fen": "<starting_fen>"}

POST /chess/game/{game_id}
  body: {"move": "e2e4"}        # UCI format
  → Validates move legality (python-chess)
  → Applies player move to board
  → Runs PyTorch model inference → selects bot move
  → Records duration in chess_bot_move_duration_seconds histogram
  → Returns: {"player_move": "e2e4", "bot_move": "e7e5", "fen": "<new_fen>", "status": "ongoing"}
```

**Stateless mode** (`GET /chess/move?fen=<fen>`) accepts a raw FEN string and returns a single best move without creating or modifying any session state — useful for frontend single-move queries.

---

## Frontend

A vanilla JavaScript single-page application served at `/game/` from FastAPI's `StaticFiles` mount.

**Design:** Glassmorphism — frosted glass panels, `backdrop-filter: blur()`, semi-transparent `rgba` backgrounds, and neon accent colors.

**Board logic:** Powered by `chess.js`, which runs entirely in the browser to:
- Render the board and pieces
- Validate legal moves on drag-and-drop
- Detect check, checkmate, and stalemate before submitting to the API

**API integration:** Player moves are submitted asynchronously:
```javascript
const res = await fetch(`/chess/game/${gameId}`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ move: moveUCI })
});
const data = await res.json();
// Apply bot_move to board, update FEN display
```

---

## Docker & Containerisation

### Multi-Stage Dockerfile

A two-stage build minimises final image size and eliminates build-time tools from the runtime:

```dockerfile
# Stage 1: Builder — install all Python deps including PyTorch (~1.5GB)
FROM python:3.12-slim-bookworm AS builder
WORKDIR /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime — lean, secure, non-root
FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
    && useradd -m appuser
WORKDIR /app
COPY --from=builder /install /usr/local   # copy compiled wheels only
COPY app app
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key decisions:**
- `python:3.12-slim-bookworm` (not `-alpine`) — avoids musl libc incompatibility with PyTorch wheels
- `--prefix=/install` trick allows copying only the final installed packages without pip/setuptools
- `apt-get upgrade -y` in runtime stage applies OS-level security patches
- Process runs as non-root `appuser` for container isolation

### Docker Compose Stack

```yaml
# All 6 services on a shared bridge network `backend`
services:
  app:        # FastAPI, memory limit: 2G, reserve: 1G
  nginx:      # Reverse proxy → app:8000, port 80
  prometheus: # Scrape → app:8000/metrics, port 9090
  loki:       # Log aggregation, port 3100
  promtail:   # Log collector, mounts /var/run/docker.sock
  grafana:    # Dashboards, port 3000, persisted volume
```

**Build and run:**
```bash
docker compose up --build -d
docker compose ps
docker compose logs -f app
```

---

## Observability Stack

### Prometheus

`prometheus/prometheus.yml` defines a single scrape job:
```yaml
scrape_configs:
  - job_name: chess-app
    static_configs:
      - targets: ['chess-app:8000']   # Docker Compose DNS
    # In Kubernetes:      ['chess-service:8000']
    scrape_interval: 15s
```

Access the Prometheus expression browser at `http://localhost:9090`.

**Useful PromQL queries:**
```promql
# Request rate per endpoint
rate(http_requests_total[5m])

# P95 bot response time
histogram_quantile(0.95, rate(chess_bot_move_duration_seconds_bucket[5m]))

# Active games gauge
chess_games_active

# Game outcome breakdown
sum by (result) (chess_game_outcomes_total)
```

### Loki + Promtail

Promtail reads container logs via the Docker socket (`unix:///var/run/docker.sock`) using the `docker_sd_configs` discovery mechanism.

**Relabeling pipeline (Kubernetes-aware):**
```yaml
relabel_configs:
  # In K8s, containers are named: /k8s_chess-app_chess-app-785c45b79b-zczct_default_...
  # This regex extracts just "chess-app"
  - source_labels: ["__meta_docker_container_name"]
    regex: "/k8s_([^_]+)_.*"
    target_label: "container"
  - source_labels: ["__meta_docker_container_log_stream"]
    target_label: "stream"
```

Logs are pushed to `http://loki-service:3100/loki/api/v1/push` (Kubernetes DNS).

**Loki LogQL queries:**
```logql
# All chess app logs
{container="chess-app"}

# Only chess-related log lines
{container="chess-app"} |= "chess"

# Error logs only
{container="chess-app"} |= "ERROR"
```

### Grafana Dashboards

The `loki/chess-dashboard.json` file defines a pre-built dashboard with 5 panels:

| Panel | Visualization | Query |
|---|---|---|
| Games Started Rate | Time series | `rate(chess_games_total[5m]) * 60` |
| Active Games | Gauge | `chess_games_active` |
| Bot Move Latency (P95) | Time series | `histogram_quantile(0.95, rate(chess_bot_move_duration_seconds_bucket[5m]))` |
| Game Outcomes | Pie chart | `sum by (result) (chess_game_outcomes_total)` |
| Chess App Logs | Logs panel | `{container="chess-app"} \|= "chess"` |

Default Grafana login: `admin` / `admin`

---

## CI/CD Pipeline

The `.github/workflows/ci.yml` defines a 4-stage sequential pipeline triggered on push/PR to `main`:

```
┌─────────┐     ┌────────────────┐     ┌─────────────────┐     ┌────────┐
│  test   │ ──► │ build-and-push │ ──► │  security-scan  │ ──► │ deploy │
│ pytest  │     │ Docker Buildx  │     │ Aqua Trivy      │     │ Render │
└─────────┘     │ Push to Hub    │     │ CRITICAL+HIGH   │     │ Hook   │
                └────────────────┘     └─────────────────┘     └────────┘
```

**Stage 1 — `test`** (push + PR):
```yaml
- uses: actions/setup-python@v5
  with: {python-version: "3.12", cache: "pip"}
- run: pip install -r requirements.txt
- run: pytest -v
  env: {PYTHONPATH: ${{ github.workspace }}}
```

**Stage 2 — `build-and-push`** (push to `main` only):
```yaml
- uses: docker/setup-buildx-action@v3
- uses: docker/login-action@v3
- uses: docker/build-push-action@v5
  with:
    push: true
    tags: |
      hamzaj4444/devops-chess-app:latest
      hamzaj4444/devops-chess-app:${{ github.sha }}
    cache-from: type=gha        # GitHub Actions layer cache
    cache-to: type=gha,mode=max
```

**Stage 3 — `security-scan`** (after build):
```yaml
- uses: aquasecurity/trivy-action@master
  with:
    image-ref: hamzaj4444/devops-chess-app:latest
    format: table
    exit-code: "1"              # Fails pipeline on CRITICAL/HIGH CVEs
    ignore-unfixed: true
    severity: CRITICAL,HIGH
# Also outputs SARIF report uploaded as a GitHub artifact
```

**Stage 4 — `deploy`** (after clean security scan):
```yaml
- run: curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}" --fail
```

**Required GitHub Secrets:**

| Secret | Description |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub username for image tagging |
| `DOCKER_PASSWORD` | Docker Hub access token |
| `RENDER_DEPLOY_HOOK_URL` | Render.com service webhook deploy URL |

---

## Kubernetes Deployment

### Cluster Setup

Install prerequisites using the included script:
```bash
chmod +x install_k8s.sh && ./install_k8s.sh
```

This installs `kubectl` and `minikube`. Then start the cluster:
```bash
# Start Minikube using Docker driver
minikube start --driver=docker

# Verify cluster is healthy
kubectl cluster-info
kubectl get nodes
```

### Building the App Image Inside Minikube

Minikube uses an isolated Docker daemon separate from the host. You **must** build within that context, otherwise Kubernetes cannot find the image:

```bash
# Point Docker CLI to Minikube's daemon
eval $(minikube docker-env)

# Build the image into Minikube's registry
docker build -t hamzaj4444/devops-chess-app:latest .
```

The `chess-deployment.yaml` uses `imagePullPolicy: IfNotPresent` to prevent K8s from trying to pull the image from Docker Hub when it's already available locally.

### Manifest Inventory

| File | K8s Resources | Notes |
|---|---|---|
| `chess-deployment.yaml` | `Deployment`, `Service`, `Secret` | `imagePullPolicy: IfNotPresent`, memory limit 2G |
| `nginx-configmap.yaml` | `ConfigMap` | Nginx `upstream chess-service:8000` |
| `nginx-deployment.yaml` | `Deployment` | nginx:alpine |
| `nginx-service.yaml` | `Service` (ClusterIP) | Entry point for Minikube tunnel |
| `prometheus.yaml` | `Deployment`, `Service`, `ConfigMap`, `PVC` | `args: --config.file=...` |
| `loki.yaml` | `Deployment`, `Service`, `ConfigMap`, `PVC` | `args: -config.file=...` |
| `promtail.yaml` | `DaemonSet`, `ConfigMap` | Mounts `/var/run/docker.sock` from host |
| `grafana.yaml` | `Deployment`, `Service`, `PVC` | Mounts 3 provisioning ConfigMaps |
| `grafana-provisioning-cm.yaml` | `ConfigMap` | Dashboard file provider at `/etc/grafana/provisioning/dashboards` |
| `grafana-datasources-cm.yaml` | `ConfigMap` | Auto-provisions Prometheus (`uid: prometheus`) + Loki (`uid: loki`) |
| `grafana-dashboard-cm.yaml` | `ConfigMap` | Injects `chess-dashboard.json` at `/etc/grafana/dashboards` |

> **Important:** In manifests, monitoring tools (`loki`, `prometheus`, `promtail`) use `args:` not `command:`. Using `command:` overrides the container's `ENTRYPOINT` entirely, causing the runtime to try to execute a config flag string as a binary path — which crashes the pod.

### Grafana Auto-Provisioning

Three ConfigMaps are mounted into the Grafana Deployment to make datasources and dashboards **fully declarative and reproducible**:

```yaml
# In grafana.yaml pod spec
volumeMounts:
  - name: grafana-provisioning
    mountPath: /etc/grafana/provisioning/dashboards
  - name: grafana-datasources
    mountPath: /etc/grafana/provisioning/datasources
  - name: grafana-dashboard
    mountPath: /etc/grafana/dashboards

volumes:
  - name: grafana-provisioning
    configMap: {name: grafana-provisioning}
  - name: grafana-datasources
    configMap: {name: grafana-datasources}
  - name: grafana-dashboard
    configMap: {name: grafana-dashboard}
```

The `grafana-datasources-cm.yaml` explicitly sets `uid:` values to match the `uid` fields in `chess-dashboard.json` so that panel datasource references resolve correctly without manual configuration.

### Accessing Services

Since Minikube on Linux uses Docker as its driver, ClusterIP services are not reachable directly from the host. Use:

```bash
# Chess application
minikube service nginx-service --url
# → http://127.0.0.1:<PORT>
# Navigate to http://127.0.0.1:<PORT>/game/

# Grafana
minikube service grafana-service --url
# → http://127.0.0.1:<PORT>  (login: admin / admin)

# Prometheus
minikube service prometheus-service --url
# → http://127.0.0.1:<PORT>
```

⚠️ Keep the terminal open — the tunnel is active only while the command is running.

**Check all pod status:**
```bash
kubectl get pods
kubectl describe pod <pod-name>   # for troubleshooting
kubectl logs deployment/chess-app --tail=50
kubectl logs deployment/grafana --tail=50
```

---

## Environment Variables & Secrets

| Variable | Where | Default | Description |
|---|---|---|---|
| `JWT_SECRET` | `.env` / K8s Secret | `your-secret-key-change-me` | HMAC signing key for JWT tokens |
| `GRAFANA_PASSWORD` | `.env` | `admin` | Grafana admin password |
| `DOCKERHUB_USERNAME` | GitHub Secret | — | Docker Hub username |
| `DOCKER_PASSWORD` | GitHub Secret | — | Docker Hub access token |
| `RENDER_DEPLOY_HOOK_URL` | GitHub Secret | — | Render.com deploy webhook |

The Kubernetes `Secret` for the chess app is defined in `chess-secret.yaml` and mounted as environment variables into the `chess-app` Deployment.

---

## Running Locally

**Option A — Docker Compose (recommended for development):**
```bash
cp .env.example .env        # set JWT_SECRET
docker compose up --build -d
# App:       http://localhost/game/
# Grafana:   http://localhost:3000
# Prometheus:http://localhost:9090
```

**Option B — Bare Python (no Docker):**
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Note: monitoring stack will not be available
```

---

## Running on Kubernetes

```bash
# 1. Start Minikube
minikube start --driver=docker

# 2. Build image inside Minikube
eval $(minikube docker-env)
docker build -t hamzaj4444/devops-chess-app:latest .

# 3. Apply all manifests
kubectl apply -f kubernetes/

# 4. Wait for pods to be ready
kubectl wait --for=condition=ready pod --all --timeout=120s

# 5. Open browser tunnel
minikube service nginx-service --url
```

**Useful management commands:**
```bash
# Restart a deployment
kubectl rollout restart deployment chess-app

# Scale the backend
kubectl scale deployment chess-app --replicas=3

# Watch pod events
kubectl get events --sort-by='.lastTimestamp'

# Delete and recreate a PVC (e.g., Grafana reset)
kubectl delete deployment grafana
kubectl delete pvc grafana-pvc
kubectl apply -f kubernetes/grafana.yaml

# Stop Minikube
minikube stop
```

---

## Testing

Tests are written with `pytest` and `httpx`:

```bash
# Run all tests
PYTHONPATH=. pytest -v

# Run a specific test file
PYTHONPATH=. pytest tests/test_chess.py -v

# With coverage
PYTHONPATH=. pytest --cov=app tests/
```

The test suite covers:
- `/health` endpoint response shape
- `/login` with valid and invalid credentials
- Full game lifecycle: `POST /chess/game/new` → `POST /chess/game/{id}` → final state
- Invalid FEN string handling in the stateless `/chess/move` endpoint
- HTTP response status codes for authenticated vs unauthenticated requests

---

## Known Limitations & Future Work

| Area | Current State | Planned Improvement |
|---|---|---|
| **User store** | In-memory `users.py` dict | Replace with PostgreSQL + SQLAlchemy ORM |
| **Chess.com stats** | Hardcoded username `dextre4` | Accept username from JWT claims or query param |
| **Ingress / TLS** | No HTTPS | Add cert-manager + NGINX Ingress Controller with Let's Encrypt |
| **Public exposure** | Minikube-only | Cloudflare Tunnel (`cloudflared`) for zero-config public access |
| **Helm packaging** | Raw YAML manifests | Package as Helm chart with values.yaml overrides |
| **Autoscaling** | Fixed 1 replica | Add HPA targeting `chess_bot_move_duration_seconds` |
| **Game history** | In-memory session map | Persist to database for leaderboards and replays |
| **Alerting** | Grafana dashboards only | Add Prometheus alerting rules + Alertmanager → Slack/email |
| **Multi-arch image** | linux/amd64 only | Add `linux/arm64` via Buildx matrix for Apple Silicon / RPi |
