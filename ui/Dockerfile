FROM node:20-slim AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

FROM node:20-slim

WORKDIR /app

COPY package.json .
COPY server.js .
COPY --from=build /app/dist ./dist

HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=5 \
    CMD node -e "fetch('http://localhost:' + (process.env.PORT || 3000) + '/health').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"

CMD ["node", "server.js"]
