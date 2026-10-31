from fastapi import FastAPI

app = FastAPI(title="context-platform-scheduler")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
