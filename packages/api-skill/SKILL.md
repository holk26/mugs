---
name: storecraft-api
description: Use when working with the Storecraft backend API in the mugs monorepo, connecting Astro to store-core, or adding new API-consuming features.
---

# Storecraft API (mugs project)

## Overview

This skill documents the REST API exposed by the `apps/core` Storecraft backend in the `mugs` monorepo. The frontend (`apps/web`, Astro) consumes this API through `@mugs/api-client`.

## Base URL

- **Development:** `http://localhost:8080/api`
- **Production:** set via `CORE_API_URL` in `apps/web/.env`

## Authentication

The API supports three security schemes (defined in OpenAPI):

| Method | How to use |
|--------|------------|
| **Bearer JWT** | `Authorization: Bearer <access_token>` obtained from `/auth/signin` |
| **API Key** | `X-API-KEY: <key>` configured in store-core env |
| **Basic Auth** | username + password (for dashboard/admin flows) |

Public reads (e.g. listing products) may work without authentication depending on store-core config; writes always require auth.

## Core endpoints

| Resource | Endpoints |
|----------|-----------|
| **Products** | `GET /products`, `POST /products`, `GET /products/{id_or_handle}`, `DELETE /products/{id_or_handle}`, `GET /products/count_query`, `GET /products/used_tags` |
| **Collections** | `GET /collections`, `POST /collections`, `GET /collections/{id_or_handle}`, `GET /collections/{id_or_handle}/products` |
| **Orders** | `GET /orders`, `POST /orders`, `GET /orders/{id_or_handle}`, `GET /orders/me` |
| **Customers** | `GET /customers`, `POST /customers`, `GET /customers/{id_or_handle}`, `GET /customers/{id_or_email}/orders` |
| **Auth** | `POST /auth/signin`, `POST /auth/signup`, `POST /auth/refresh`, `GET /auth/confirm-email`, `GET /auth/forgot-password-request` |
| **Checkout** | `POST /checkout/create?gateway={gateway}`, `POST /checkout/pricing`, `POST /checkout/{order_id}/complete` |
| **Payments** | `GET /payments/gateways`, `GET /payments/status/{order_id}`, `POST /payments/{action_handle}/{order_id}` |
| **Storage** | `GET /storage/{file_key}`, `PUT /storage/{file_key}`, `DELETE /storage/{file_key}` |
| **Search** | `GET /search`, `GET /similarity-search` |
| **AI / Chat** | `POST /ai/agents/{agent_handle}/run`, `GET /chats`, `POST /chats` |

## Query parameters for lists

Most list endpoints accept:

- `limit` / `offset` — pagination
- `sortBy` — field to sort by
- `order` — `asc` or `desc`
- `expand` — JSON array of relations to expand, e.g. `expand=["medias","variants"]`
- `vql` — Virtual Query Language string for filtering

## Usage from Astro

Use `@mugs/api-client` and read the API URL from env:

```astro
---
import { createClient, getProducts } from '@mugs/api-client';

const baseUrl = import.meta.env.CORE_API_URL || 'http://localhost:8080';
const client = createClient(baseUrl);
const { data: products } = await getProducts(client, { limit: 10 });
---
```

Keep `CORE_API_URL` server-only (no `PUBLIC_` prefix) so the value is never sent to the browser.

## Usage with authentication

```ts
const client = createClient('http://localhost:8080', {
  accessToken: 'jwt-from-signin',
});

// or
const client = createClient('http://localhost:8080', {
  apiKey: 'your-api-key',
});
```

## Common mistakes

- **404 / `{ detail: 'Not Found' }`** — store-core is not running or the path is wrong. Base path is `/api`, not `/api/v1`.
- **500 / `{ messages: [...] }`** — check store-core logs; often a missing DB migration or native SQLite binding issue.
- **Auth errors** — make sure `SC_AUTH_SECRET_ACCESS_TOKEN` and friends are set in `apps/core/.env`.
- **CORS in browser** — prefer server-side calls from Astro; for client-side islands use API routes or a proxy.

## Reference file

The full OpenAPI spec lives at `packages/api-skill/openapi.json` and is served by store-core at `/api/openapi.json`.
