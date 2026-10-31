#!/bin/sh
# Start Ollama, pull the configured embedding model, then stay in the foreground
# serving it. EMBEDDING_MODEL defaults to nomic-embed-text to match
# adapters/embedding/http_local.py's default and .env.example.
set -eu

MODEL="${EMBEDDING_MODEL:-nomic-embed-text}"

ollama serve &
SERVE_PID=$!

# Wait for the server to accept connections before pulling a model.
until ollama list >/dev/null 2>&1; do
    sleep 1
done

ollama pull "$MODEL"

wait "$SERVE_PID"
