FROM python:3.12-slim

WORKDIR /app

COPY scripts/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/migrate.py ./migrate.py
COPY migrations ./migrations

ENTRYPOINT ["python", "migrate.py"]
CMD ["up"]
