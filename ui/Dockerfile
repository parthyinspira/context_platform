FROM node:20-slim

WORKDIR /app

COPY package.json .
COPY server.js .

HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=5 \
    CMD node -e "fetch('http://localhost:3000/health').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"

CMD ["node", "server.js"]
