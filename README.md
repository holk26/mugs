# Recuerdo Momentos — Mugs Store

Custom mugs from kids' drawings. Astro frontend + Django backend + Printful fulfillment.

## Estructura

```
mugs/
├── apps/
│   ├── django/         # Django 6.0.6 backend (API, payments, orders, Printful sync)
│   └── web/            # Astro 6 SSR frontend (React islands, Tailwind, Stripe)
├── packages/
│   ├── api-client/     # JS API client for the Django backend
│   └── printful/       # Printful integration (legacy Storecraft extension)
├── docker-compose.yml  # Orquestación: db (Postgres), django, web
└── pnpm-workspace.yaml
```

## Variables de entorno clave

### Backend (apps/django/.env)

- `DATABASE_URL` — PostgreSQL connection string
- `STRIPE_SECRET_KEY` — Stripe secret key
- `STRIPE_PUBLISHABLE_KEY` — Stripe publishable key
- `STRIPE_WEBHOOK_SECRET` — Stripe webhook signing secret
- `RESEND_API_KEY` — Resend API key for order emails
- `PRINTFUL_API_TOKEN` — Printful API token
- `PRINTFUL_WEBHOOK_SECRET` — Printful webhook signing secret

### Frontend (apps/web/.env)

- `DJANGO_API_URL` — Backend API base URL (default: `http://localhost:8080`)
- `PUBLIC_STRIPE_PUBLISHABLE_KEY` — Stripe publishable key (public)

## Desarrollo local

```bash
# Backend
cd apps/django
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8080

# Frontend (desde raíz)
pnpm --filter @mugs/web dev --host
```

## Docker Compose

```bash
docker compose up --build
```

- Django API: http://localhost:8080
- Astro storefront: http://localhost:4321

## Funcionalidades

- Catálogo de productos sincronizado con Printful
- Subida de dibujos por el cliente por línea de pedido
- Pago con Stripe (PaymentIntent + PaymentElement)
- Emails de confirmación y actualización con Resend
- Printful fulfillment con push de orden y webhook de estado
- Carrito persistente con Zustand + localStorage
