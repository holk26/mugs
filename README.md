# Recuerdo Momentos — Mugs Store

Custom mugs from kids' drawings. Astro frontend + Django backend + Printful fulfillment.

## Estructura

```
mugs/
├── apps/
│   ├── django/         # Django 6 backend (API REST, pagos Stripe, pedidos, sync Printful, Celery)
│   ├── web/            # Astro 6 SSR storefront (islas React, Tailwind 4, Zustand)
│   └── dashboard/      # Admin SPA (React 19 + Vite + TanStack Router/Query, servida con nginx)
├── docker-compose.yml  # Stack de producción (Dokploy/Traefik)
└── pnpm-workspace.yaml
```

## Stack de producción

`docker-compose.yml` levanta 8 servicios sobre la red externa `dokploy-network` (Traefik termina TLS con Let's Encrypt):

| Servicio    | Descripción                          | Dominio                          |
|-------------|--------------------------------------|----------------------------------|
| `web`       | Storefront Astro SSR                 | mugs.app.moonsbow.com            |
| `django`    | API + admin de Django (gunicorn)     | backshop.app.moonsbow.com        |
| `dashboard` | Panel de administración (nginx)      | dashboar-back.app.moonsbow.com   |
| `celery`    | Worker Celery (imágenes IA, Printful)| —                                |
| `db`        | PostgreSQL 16                        | —                                |
| `redis`     | Broker Celery (con AOF)              | —                                |
| `minio`     | Object storage S3 (media + dibujos)  | minio.app.moonsbow.com           |
| `minio-init`| Crea los buckets público y privado   | —                                |

Hay dos buckets: `mugs-media` (público, media de productos) y `mugs-drawings`
(privado, dibujos originales de clientes, servido con URLs firmadas).

## Variables de entorno

- **Producción (compose):** ver `.env.example` en la raíz. Las requeridas son
  `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `AWS_ACCESS_KEY_ID`,
  `AWS_SECRET_ACCESS_KEY`, `PRINTFUL_API_TOKEN`, `STRIPE_SECRET_KEY`,
  `STRIPE_WEBHOOK_SECRET` y `PRINTFUL_WEBHOOK_SECRET`; compose falla si falta
  alguna. `AWS_S3_ENDPOINT_URL` debe ser la URL **pública** de MinIO para que
  las URLs firmadas del bucket privado funcionen en el navegador.
- **Backend (desarrollo):** `apps/django/.env.example`.
- **Storefront (desarrollo):** `apps/web/.env.example`.
- **Dashboard (desarrollo):** `apps/dashboard/.env.example`.

## Desarrollo local

```bash
# Backend
cd apps/django
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8080

# Storefront (desde raíz)
pnpm --filter @mugs/web dev --host

# Dashboard (desde raíz)
pnpm --filter @mugs/dashboard dev
```

## Tests

```bash
# Backend (90 tests)
cd apps/django && python -m pytest

# Dashboard
pnpm --filter @mugs/dashboard test
```

## Despliegue

```bash
docker compose up --build -d
```

Diseñado para Dokploy: la red `dokploy-network` debe existir y Traefik se
encarga del TLS. El entrypoint de Django corre `migrate`, `collectstatic` y
`ensure_admin` (crea el admin inicial si `ADMIN_EMAIL`/`ADMIN_PASSWORD` están
definidas) en cada arranque.

## Funcionalidades

- Catálogo de productos sincronizado con Printful
- Subida de dibujos por el cliente por línea de pedido (validación real de imagen)
- Pago con Stripe Checkout (con verificación de propiedad del pedido e idempotencia de webhooks)
- Cupones de descuento con rate limiting
- Emails de confirmación y actualización con Resend
- Printful fulfillment con push asíncrono (Celery) y webhook de estado firmado
- Procesamiento de imágenes con IA (OpenAI/Gemini) y generación de mockups
- Carrito persistente con Zustand + localStorage
