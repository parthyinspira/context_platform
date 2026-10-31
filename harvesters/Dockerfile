FROM python:3.12-slim

WORKDIR /app

COPY harvesters/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY harvesters ./harvesters
COPY harvest_validation ./harvest_validation
COPY adapters ./adapters
COPY ontology ./ontology

# No positional CLI arguments baked into the entrypoint: configuration (SOURCE_ID,
# PLAN_ID, DATABASE_URL, ...) comes entirely from the environment, which is how a
# GCP Cloud Run Job and an Azure Container Apps Job both pass per-execution config to
# a task container, so this image runs unmodified under all three targets
# (`docker compose run harvester`, a Cloud Run Job, a Container Apps Job).
ENTRYPOINT ["python", "-m", "harvesters.run"]
