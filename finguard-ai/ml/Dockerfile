# FinGuard AI — one-shot training image.
# Produces model artifacts into /app/artifacts (mount a volume there).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY data ./data

# If /app/artifacts already has a model, skip retraining; otherwise train on
# synthetic data (or real data if data/paysim.csv is mounted).
CMD ["sh", "-c", "if [ -f artifacts/model.joblib ]; then echo 'Model already present, skipping training.'; elif [ -f data/paysim.csv ]; then python -m src.train --data data/paysim.csv; else python -m src.train; fi"]
