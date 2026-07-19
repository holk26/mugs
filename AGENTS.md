# Mugs — Recuerdo Momentos

Tienda de mugs personalizados con dibujos de niños. Monorepo pnpm:

- `apps/django` — API Django 6 + DRF (pedidos, Stripe, Printful, Celery)
- `apps/web` — Storefront Astro 6 SSR (`@mugs/web`)
- `apps/dashboard` — Admin SPA React 19 + Vite (`@mugs/dashboard`)

## Comandos

```bash
# Tests backend (obligatorio que pasen antes de commit)
cd apps/django && python -m pytest

# Tests y builds frontend
pnpm --filter @mugs/dashboard test
pnpm --filter @mugs/web build
pnpm --filter @mugs/dashboard build
```

## Despliegue (Dokploy)

El despliegue es automático: cada push a `master` dispara un deploy vía webhook
de GitHub en Dokploy.

- **Proyecto:** `Diego` (projectId `XRd4XCjv6DiGkghHEqk95`), environment `production`
- **Servicio compose:** `Mugs` — appName `diego-mugs-fjvxly-im4pvb`, composeId `iZfg5xridS83hqKLK2q02`
- **Compose file:** `./docker-compose.yml` (rama `master`, repo `holk26/mugs`)
- **Dominios:** `mugs.app.moonsbow.com` (web), `backshop.app.moonsbow.com` (django), `dashboar-back.app.moonsbow.com` (dashboard)

### Configuración de MCPs necesaria

Para operar el despliegue y las integraciones sin exponer secretos en el repo,
configura los MCPs en el entorno del agente (no en archivos del proyecto):

- **Dokploy MCP**: requiere un token de API de Dokploy con acceso a la organización.
  Proyecto `Diego` (`XRd4XCjv6DiGkghHEqk95`), environment `production` (`Qj9Wstik9VTgOTMsMJEuO`),
  compose `Mugs` (`iZfg5xridS83hqKLK2q02`), appName `diego-mugs-fjvxly-im4pvb`.
- **Printful MCP**: requiere el token de la cuenta de Printful vinculada a la tienda
  Homero's Store (`storeId: 18364589`).

### Regla: validar el deploy tras cada push a master

Después de subir cambios a `master`, el agente DEBE verificar que el despliegue
quedó bien usando el MCP de Dokploy, en este orden:

1. **Estado del deployment** — `compose-one` (composeId `iZfg5xridS83hqKLK2q02`):
   el deployment más reciente debe tener `status: "done"` y `composeStatus: "done"`.
   Si es `error`, leer los logs de los servicios (`compose-loadServices` para
   obtener los `containerId` y luego `compose-readLogs`), diagnosticar, corregir
   y redeployar (`compose-redeploy`) hasta que quede verde. No dar la tarea por
   terminada con un deploy en error.
2. **Healthchecks HTTP** (con FetchURL o similar):
   - `https://backshop.app.moonsbow.com/api/v1/health/` → `{"status": "ok"}`
   - `https://mugs.app.moonsbow.com/` → 200 con el HTML de la home
   - `https://dashboar-back.app.moonsbow.com/` → 200
3. **Smoke funcional según el cambio** — si el cambio toca un flujo concreto
   (checkout, login admin, webhooks), verificar ese flujo en producción.

### Variables de entorno requeridas en Dokploy

`docker-compose.yml` falla rápido si falta alguna de estas (sintaxis `${VAR:?}`),
así que deben estar definidas con valores reales en el env del servicio en Dokploy:

- `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (deben coincidir con el root de MinIO existente)
- `PRINTFUL_API_TOKEN`, `PRINTFUL_WEBHOOK_SECRET`
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`

`POSTGRES_PASSWORD` debe coincidir con la contraseña con la que se inicializó el
volumen de Postgres existente (cambiarla en el env NO cambia la contraseña real
de una base ya creada). Lista completa y defaults en `.env.example` (raíz).

## Convenciones

- Commits en español, formato `tipo(alcance): descripción` (ej. `fix(api): ...`).
- No commitear `.env` ni secretos; `.env.example` documenta las variables.
- El código legacy de Storecraft (`apps/core`, `packages/*` JS) fue eliminado;
  la integración Printful vigente vive en `apps/django/apps/printful/`.
