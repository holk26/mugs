# Dockerfile de producción para la tienda SPA (Vite + React + TanStack Router)
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

# URL base de la API y Stripe key (build-time)
ARG VITE_API_URL=http://django:8080
ARG VITE_PUBLIC_STRIPE_PUBLISHABLE_KEY
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_PUBLIC_STRIPE_PUBLISHABLE_KEY=${VITE_PUBLIC_STRIPE_PUBLISHABLE_KEY}
ENV HOST=0.0.0.0
ENV PORT=4321

# Compilar la aplicación
RUN pnpm --filter @mugs/web build

EXPOSE 4321

# Servidor SPA
CMD ["pnpm", "--filter", "@mugs/web", "preview", "--host", "0.0.0.0", "--port", "4321"]
