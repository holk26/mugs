# Dockerfile de producción para la tienda Astro (SSR con @astrojs/node)
FROM node:22-slim

WORKDIR /app

RUN npm install -g pnpm@11.9.0

# Evitar prompts interactivos de pnpm en builds sin TTY
ENV CI=true

# Copiar manifiestos del workspace para aprovechar la caché de dependencias
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY apps/web/package.json apps/web/package.json

RUN pnpm install --frozen-lockfile

# Copiar todo el código fuente
COPY . .

# URL base de la API (must be public for browser requests)
ARG PUBLIC_DJANGO_API_URL=https://backshop.app.moonsbow.com
ENV PUBLIC_DJANGO_API_URL=${PUBLIC_DJANGO_API_URL}
ENV HOST=0.0.0.0
ENV PORT=4321

# Compilar la aplicación
RUN pnpm --filter @mugs/web build

EXPOSE 4321

# Servidor SSR standalone de Astro
CMD ["node", "apps/web/dist/server/entry.mjs"]
