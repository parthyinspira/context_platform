FROM ollama/ollama:0.3.12

ENV EMBEDDING_MODEL=nomic-embed-text

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=10 \
    CMD ollama list | grep -q "$EMBEDDING_MODEL" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
