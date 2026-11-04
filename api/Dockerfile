FROM python:3.12-slim

WORKDIR /app

# git CLI: the discover/plan/test-connection routes call into GitHarvester,
# which shells out to `git` (blobless partial clone for discovery).
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/app ./app
COPY adapters ./adapters
COPY harvesters ./harvesters
COPY harvest_validation ./harvest_validation
COPY agents ./agents

HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
