from prometheus_client import Counter, Histogram

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
