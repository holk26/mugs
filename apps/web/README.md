# Mugs Web

Tienda frontend construida con **Astro**.

## Desarrollo

```bash
# Desde la raíz del monorepo
pnpm install
pnpm --filter @mugs/web dev --host
```

La tienda se conecta al backend mediante `@mugs/api-client`. La URL de la API se lee de `CORE_API_URL` (por defecto `http://localhost:8080`).

## Build de producción

```bash
pnpm --filter @mugs/web build
pnpm --filter @mugs/web preview
```

## Docker

```bash
# Desde la raíz del monorepo
docker compose up --build
```

## Estructura

- `src/pages/index.astro` – página de inicio con listado de productos
- `src/layouts/Layout.astro` – layout base
