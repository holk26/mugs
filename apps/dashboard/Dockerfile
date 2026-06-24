# Build stage
FROM node:22-alpine AS builder
WORKDIR /app

# Enable pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY apps/dashboard/package.json ./apps/dashboard/package.json
COPY packages ./packages

RUN pnpm install --frozen-lockfile

COPY apps/dashboard ./apps/dashboard

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN pnpm --filter @mugs/dashboard build

# Serve stage
FROM nginx:alpine
RUN apk add --no-cache gettext
COPY apps/dashboard/nginx.conf /etc/nginx/conf.d/default.conf
COPY apps/dashboard/entrypoint.sh /entrypoint.sh
COPY --from=builder /app/apps/dashboard/dist /usr/share/nginx/html

EXPOSE 80
CMD ["/entrypoint.sh"]
