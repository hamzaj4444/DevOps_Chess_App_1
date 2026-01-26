from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency",
    ["endpoint"]
)

LOGIN_FAILURES = Counter(
    "login_failures_total",
    "Total failed login attempts"
)

CHESS_API_ERRORS = Counter(
    "chess_api_errors_total",
    "Total Chess.com API errors"
)

# Chess game metrics
CHESS_GAMES_TOTAL = Counter(
    "chess_games_total",
    "Total chess games started"
)

CHESS_MOVES_TOTAL = Counter(
    "chess_moves_total",
    "Total chess moves made",
    ["color"]  # player or bot
)

CHESS_BOT_MOVE_DURATION = Histogram(
    "chess_bot_move_duration_seconds",
    "Time taken for bot to calculate a move",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

CHESS_GAMES_ACTIVE = Gauge(
    "chess_games_active",
    "Number of currently active chess games"
)

CHESS_GAME_OUTCOMES = Counter(
    "chess_game_outcomes_total",
    "Chess game outcomes",
    ["result"]  # white_wins, black_wins, stalemate, draw, etc.
)
