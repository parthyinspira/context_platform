FROM ollama/ollama:0.3.12

HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=10 \
    CMD ollama list || exit 1
