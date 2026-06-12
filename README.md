# Mugs Store

Monorepo con la tienda frontend en **Astro** y el backend/API en **Storecraft**.

## Estructura

```text
mugs/
├── apps/
│   ├── core/          # API Storecraft (Node.js + SQLite)
│   └── web/           # Tienda Astro (SSR / estático)
├── packages/
│   └── api-client/    # Cliente tipado para la API de Storecraft
├── docker-compose.yml # Orquestación de core + web
└── pnpm-workspace.yaml
```

## Requisitos

- Node.js >= 22
- pnpm >= 11
- Docker + Docker Compose (opcional)

## Configuración

1. Copia el ejemplo de entorno en `apps/core`:

```bash
cp apps/core/.env.example apps/core/.env
```

2. Completa `apps/core/.env` con las variables de Storecraft (tokens de auth, etc.).

## Desarrollo local

```bash
# Instalar dependencias del workspace
pnpm install

# Levantar el backend (puerto 8080)
cd apps/core
npm run migrate
npm start

# En otra terminal, levantar Astro (puerto 4321)
pnpm --filter @mugs/web dev --host
```

- Dashboard de Storecraft: http://localhost:8080/dashboard
- Referencia de la API: http://localhost:8080/api
- Tienda Astro: http://localhost:4321

## Docker Compose

```bash
docker compose up --build
```

- Core: http://localhost:8080
- Web: http://localhost:4321

> Recuerda crear `apps/core/.env` antes de levantar los contenedores.

## Build de producción (Astro)

```bash
pnpm --filter @mugs/web build
pnpm --filter @mugs/web preview
```

## Comandos útiles

| Comando | Descripción |
| --- | --- |
| `pnpm install` | Instala dependencias del monorepo |
| `cd apps/core && npm run migrate` | Ejecuta migraciones de SQLite |
| `cd apps/core && npm start` | Inicia el backend |
| `pnpm --filter @mugs/web dev --host` | Inicia Astro en desarrollo |
| `pnpm --filter @mugs/web build` | Compila la tienda |
| `docker compose up --build` | Levanta todo con Docker |
