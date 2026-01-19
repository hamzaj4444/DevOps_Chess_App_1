# -------- Builder stage --------
FROM python:3.12-slim AS builder

WORKDIR /install

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# -------- Runtime stage --------
FROM python:3.12-slim

# Create non-root user
RUN useradd -m appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY app app

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
