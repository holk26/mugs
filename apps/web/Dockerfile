# Dockerfile de desarrollo para la tienda Astro
FROM node:22-slim

WORKDIR /app

RUN npm install -g pnpm

# Copiar manifiestos del workspace para aprovechar la caché de dependencias
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/api-client/package.json packages/api-client/package.json

RUN pnpm install --frozen-lockfile

COPY . .

ENV CORE_API_URL=http://core:8080
EXPOSE 4321

CMD ["pnpm", "--filter", "@mugs/web", "dev", "--host"]
