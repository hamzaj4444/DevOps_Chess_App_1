# DevOps Chess App ♟️

A full-stack DevOps showcase involving a FastAPI backend, a Chess Bot powered by a Neural Network (PyTorch) train from scratch to play Chess just Like me, and a complete monitoring/logging stack (Prometheus, Loki, Grafana).

## Features

- **Chess.com Stats**: View user statistics from Chess.com.
- **AI Chess Bot**: Play against a bot trained on professional master games.
- **Interactive UI**: Clean, glassmorphism-inspired UI for playing chess.
- **Full Observability**: Real-time metrics and log aggregation.
- **DevOps Ready**: Dockerized, CI/CD with GitHub Actions, and Kubernetes ready.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.12 (for local development)

### Running the Stack

To start the entire application stack:

```bash
docker-compose up -d --build
```

Access the components:

- **Chess App & UI**: [http://localhost/game/](http://localhost/game/)
- **API Docs (Swagger)**: [http://localhost/docs](http://localhost/docs)
- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **Grafana**: [http://localhost:3000](http://localhost:3000) (Default: `admin`/`admin`)
- **Loki**: [http://localhost:3100](http://localhost:3100)

## API Documentation

### Chess Module (`/chess`)

- `GET /chess/health`: Health status and active games count.
- `POST /chess/move`: Stateless move prediction (send FEN, get bot move).
- `POST /chess/game/new`: Start a new game session.
- `GET /chess/game/{id}`: Get current game state.
- `POST /chess/game/{id}/move`: Make a move and receive bot response.
- `DELETE /chess/game/{id}`: Terminate a session.

### Monitoring Metrics

The app exposes Prometheus metrics at `/metrics`:
- `chess_games_total`: Cumulative games started.
- `chess_moves_total`: Moves made by player/bot.
- `chess_bot_move_duration_seconds`: Performance histogram of bot thinking.
- `chess_games_active`: Current concurrent games.
- `chess_game_outcomes_total`: Win/Loss/Draw statistics.

## Project Structure

- `app/`: FastAPI backend and integrated logic.
  - `chess/`: The chess bot module (logic, model, routes).
  - `static/`: Frontend assets.
- `kubernetes/`: K8s deployment and service manifests.
- `prometheus/`, `loki/`, `nginx/`: Configuration for infra services.
- `tests/`: Comprehensive test suite.

## CI/CD

The project uses GitHub Actions for:
1. **Testing**: `pytest` with 100% logic coverage.
2. **Build**: Docker image creation with PyTorch CPU-only optimization.
3. **Security**: Trivy vulnerability scanning for OS and Python dependencies.
