import time
from fastapi import FastAPI, Depends, HTTPException, Request
from prometheus_client import generate_latest
from app.users import get_user, verify_password
from app.auth import create_access_token, get_current_user
from app.stats import fetch_stats
from app.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    LOGIN_FAILURES,
    CHESS_API_ERRORS
)
from app.logger import logger
from app.chess.routes import router as chess_router
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Include chess router
app.include_router(chess_router)

# Serve static files for chess game
app.mount("/game", StaticFiles(directory="app/static/chess", html=True), name="chess-game")

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        endpoint=request.url.path
    ).observe(duration)

    return response

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/login")
def login(username: str, password: str):
    user = get_user(username)

    if not user or not verify_password(password, user["hashed_password"]):
        LOGIN_FAILURES.inc()
        logger.warning(f"Login failed for user={username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    logger.info(f"Login successful for user={username}")
    return {"access_token": create_access_token({"sub": username})}

@app.get("/stats")
def stats(user: str = Depends(get_current_user)):
    try:
        return fetch_stats()
    except Exception as e:
        CHESS_API_ERRORS.inc()
        logger.error(f"Chess API error user={user} error={str(e)}")
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch Chess.com stats"
        )


@app.get("/metrics")
def metrics():
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type="text/plain")
