# Design

## Context
Four of the five compose services (`api`, `ui`, `scheduler`, `embeddings`) do not exist yet in the repo. Each needs a minimal runtime and health endpoint before later stories add real behaviour. The choice of base runtime per service affects every later story that builds inside these containers, so it is a real decision worth recording once here.

## Options considered
- **api / scheduler runtime**: Python 3.12 (matches `CLAUDE.md` conventions, "Python 3.12, type hints") vs Node. -> Python 3.12, consistent with the harvester framework language.
- **api framework**: FastAPI (async, OpenAPI for free, matches future MCP/API work) vs Flask. -> FastAPI, minimal `/health` route only in this story.
- **ui runtime**: Node 20+ per README, using Vite dev-server style container vs a static Nginx placeholder. -> Node 20 skeleton serving a single page with a `/health` route, since `docs/UI_DESIGN.md` calls for React later; starting the real toolchain now avoids a throwaway rebuild.
- **embeddings runtime**: Ollama (serves `nomic-embed-text` per `.env.example`, pulls model into the container at startup) vs a Python sentence-transformers server. -> Ollama, because `.env.example` already names `EMBEDDING_BASE_URL=http://embeddings:11434` and `EMBEDDING_MODEL=nomic-embed-text`, which are Ollama's defaults; this story only adds the container and a `/health`-equivalent check (`ollama list` via compose healthcheck), it does not pre-pull the model to keep startup fast.
- **scheduler runtime**: Python 3.12, FastAPI `/health` only; no cron logic yet (dispatcher behaviour is Epic 4, KAN-4xx).

## Decision and reason
Python 3.12 + FastAPI for `api` and `scheduler`; Node 20 for `ui`; Ollama for `embeddings`. This matches existing conventions in `CLAUDE.md` and `.env.example` so later stories do not need to re-platform any service.

## Consequences
- `embeddings` container will be larger than a bare sentence-transformers image because it bundles the Ollama runtime; acceptable since no model is pre-pulled in this story.
- `ui` ships with a full Node toolchain from the start rather than a static placeholder, slightly increasing this story's scope but avoiding a throwaway rebuild in the UI epic.
