FROM node:24.21.0-bookworm-slim AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/index.html frontend/vite.config.ts frontend/tsconfig.json frontend/tsconfig.node.json ./
COPY frontend/src ./src
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.28.0-alpine
COPY docker/frontend/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/dist /usr/share/nginx/html
USER 101:101
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/"]
