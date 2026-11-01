FROM python:3.12-slim

WORKDIR /app

COPY context_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY context_service/app ./app

HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
