# Dockerfile de producción para la tienda Astro (SSR con @astrojs/node)
FROM node:22-slim

WORKDIR /app

RUN npm install -g pnpm

# Evitar prompts interactivos de pnpm en builds sin TTY
ENV CI=true

# Copiar manifiestos del workspace para aprovechar la caché de dependencias
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/api-client/package.json packages/api-client/package.json

RUN pnpm install --frozen-lockfile

# Copiar todo el código fuente
COPY . .

# URL base de la API (build-time y runtime)
ARG DJANGO_API_URL=http://django:8080
ENV DJANGO_API_URL=${DJANGO_API_URL}
ENV HOST=0.0.0.0
ENV PORT=4321

# Compilar la aplicación
RUN pnpm --filter @mugs/web build

EXPOSE 4321

# Servidor SSR standalone de Astro
CMD ["node", "apps/web/dist/server/entry.mjs"]
