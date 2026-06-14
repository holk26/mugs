# Printful Integration Design

## Status

Approved for implementation.

## Context

`mugs` is a pnpm monorepo with two deployed services:

- `apps/core` — Storecraft backend (`backshop.app.moonsbow.com`).
- `apps/web` — Astro 6 SSR frontend (`mugs.app.moonsbow.com`).

Storecraft already manages products, orders, customers, checkout, payments and shipping methods. The goal is to make **Printful** the product catalog source and the fulfillment backend:

1. Printful provides the catalog (products, variants, mockups).
2. The Astro storefront displays those products and accepts orders through Storecraft.
3. When a payment is captured, Storecraft forwards the order to Printful for production and shipping.
4. Real Printful shipping rates are shown during checkout.
5. Order status updates from Printful are reflected back in Storecraft.

## Goals

- Sync the whole Printful catalog into Storecraft products automatically and periodically.
- Create a Printful order when Storecraft emits `orders/payments/captured`.
- Fetch live Printful shipping rates before checkout and use the selected rate.
- Receive Printful webhooks (or poll as fallback) to update Storecraft order status.
- Keep Printful API credentials server-side only.
- Reuse the existing `@mugs/api-client` and Storecraft extension model.

## Non-goals

- Replacing Storecraft as the commerce engine (cart, checkout, payments, customers).
- Building a generic Printful SDK for public npm.
- Supporting multi-store Printful accounts in the first iteration.

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                              mugs                                   │
│  ┌──────────────┐         ┌──────────────┐         ┌─────────────┐ │
│  │   apps/web   │────────▶│  apps/core   │────────▶│   Printful  │ │
│  │   (Astro)    │  HTTP   │  (Storecraft)│  HTTPS  │    API      │ │
│  └──────────────┘         └──────┬───────┘         └─────────────┘ │
│                                  │                                   │
│                          ┌───────▼────────┐                        │
│                          │ @mugs/printful │                        │
│                          │  - client      │                        │
│                          │  - transformers│                        │
│                          │  - extension   │                        │
│                          └────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

- **`@mugs/printful`** — new workspace package. It owns everything related to Printful:
  - `client` — thin, fetch-based HTTP client for the Printful API.
  - `transformers` — map Printful entities to/from Storecraft types.
  - `extension` — `PrintfulExtension`, a Storecraft extension that wires events and actions.
- **`apps/core`** — registers `PrintfulExtension` via `withExtensions()` and supplies configuration through environment variables.
- **`apps/web`** — keeps using `@mugs/api-client` to read products and create checkouts. It adds a small public webhook endpoint only because Storecraft extension actions do not expose HTTP headers, and Printful webhook signatures must be verified against the raw request body and headers.

## Components

### 1. `@mugs/printful` package

#### `printful-client.js`

- Accepts `{ apiToken, storeId?, baseUrl }`.
- Adds `Authorization: Bearer <token>` and optional `X-PF-Store-Id`.
- Wraps `fetch`, parses JSON, throws typed errors.
- Exposes methods needed for the flows:
  - `getStoreProducts()`
  - `getStoreProduct(id)`
  - `getVariant(id)`
  - `getShippingRates(payload)`
  - `createOrder(payload)`
  - `getOrder(id)`
  - `getOrderStatus(id)` (helper for polling fallback)

#### `transformers.js`

Pure functions, no side effects:

- `printfulStoreProductToStorecraftProduct(syncProduct, syncVariants)` → `ProductTypeUpsert`.
- `printfulSyncVariantToStorecraftVariant(variant, parentHandle)` → `VariantType`.
- `storecraftLineItemsToPrintfulItems(lineItems, variantMap)` → Printful order items.
- `storecraftAddressToPrintfulRecipient(address, contact)` → Printful recipient object.
- `printfulShippingRateToStorecraftShippingMethod(rate)` → `ShippingMethodType`.
- `printfulOrderToStorecraftStatusUpdate(pfOrder)` → `{ status, note, tracking? }`.

Key mapping decisions:

| Printful | Storecraft |
|----------|------------|
| `sync_product.id` | `handle` prefix (`pf-<id>`) and external id in `tags`/`attributes` |
| `sync_product.name` | `title` |
| `sync_product.description` | `description` |
| `sync_variants[].name` | variant `title` |
| `sync_variants[].retail_price` | variant `price` |
| `sync_variants[].currency` | ignored in v1; all prices treated as USD unless config says otherwise |
| `files[].preview_url` / mockups | `media[]` |
| `sync_variants[].id` | stored in `variant_hint` / attributes to rebuild Printful items |

#### `printful-extension.js`

A Storecraft extension class with:

```js
info = {
  name: 'Printful',
  description: 'Sync Printful catalog and push orders for fulfillment'
};

actions = [
  { handle: 'sync-catalog', name: 'Sync Printful catalog' },
  { handle: 'shipping-rates', name: 'Get live shipping rates' },
  { handle: 'select-shipping-rate', name: 'Reserve a shipping method for checkout' },
  { handle: 'push-order', name: 'Push a Storecraft order to Printful' },
  { handle: 'sync-order-status', name: 'Sync a single order status from Printful' }
];
```

`onInit(app)`:

1. Reads configuration from environment variables (see Configuration).
2. Initializes the Printful client.
3. Subscribes to `orders/payments/captured` to push orders.
4. Optionally starts a `setInterval` background sync for the catalog if `PRINTFUL_SYNC_INTERVAL_MINUTES` is set.
5. Logs a clear warning if credentials are missing; the extension stays disabled but does not crash the app.

`invokeAction(action)`:

| Action | Input | Output | Auth |
|--------|-------|--------|------|
| `sync-catalog` | `{ force?: boolean, secret: string }` | `{ created, updated, skipped, errors }` | `PRINTFUL_INTERNAL_SECRET` |
| `shipping-rates` | `{ address, lineItems }` | `[{ id, name, rate, currency }]` | public |
| `select-shipping-rate` | `{ rateId, address, lineItems }` | `{ shippingMethodHandle }` | public |
| `push-order` | `{ orderId, secret: string }` | `{ printfulOrderId, status }` | `PRINTFUL_INTERNAL_SECRET` |
| `sync-order-status` | `{ orderId, secret: string }` | `{ status }` | `PRINTFUL_INTERNAL_SECRET` |

> Note: Storecraft extension action routes (`POST /api/extensions/:handle/:action`) do not enforce admin auth by default. Protected actions compare `secret` in the request body against the `PRINTFUL_INTERNAL_SECRET` environment variable. `shipping-rates` and `select-shipping-rate` are public because they are called directly from the storefront.

### 2. `apps/core` wiring

```js
import { App } from "@storecraft/core";
import { PrintfulExtension } from "@mugs/printful";

export const app = new App({ ... })
  .withExtensions({
    postman: new PostmanExtension(),
    printful: new PrintfulExtension(),
  })
  .init();
```

Environment variables passed through `docker-compose.yml`:

```yaml
- PRINTFUL_API_TOKEN=${PRINTFUL_API_TOKEN}
- PRINTFUL_STORE_ID=${PRINTFUL_STORE_ID:-}
- PRINTFUL_WEBHOOK_SECRET=${PRINTFUL_WEBHOOK_SECRET:-}
- PRINTFUL_INTERNAL_SECRET=${PRINTFUL_INTERNAL_SECRET}
- PRINTFUL_SYNC_INTERVAL_MINUTES=${PRINTFUL_SYNC_INTERVAL_MINUTES:-60}
```

### 3. `apps/web` Printful webhook endpoint

Because Storecraft extension actions receive only the parsed request body, we cannot verify the `x-pf-webhook-signature` header inside the extension. We add one minimal Astro API route:

```
src/pages/api/printful-webhook.ts
```

Responsibilities:

1. Read the raw request body and `x-pf-webhook-signature` header.
2. Verify the HMAC-SHA256 signature using `PRINTFUL_WEBHOOK_SECRET` (hex key decoded to bytes).
3. On success, call `POST /api/extensions/printful/sync-order-status` with `{ orderId }` derived from the webhook payload.
4. Return `200 OK` quickly so Printful does not retry.

If Printful webhooks are not configured, the extension falls back to polling order status during periodic catalog syncs.

## Data Flows

### Catalog sync

```text
1. trigger: interval OR POST /api/extensions/printful/sync-catalog
2. GET /store/products (Printful)
3. for each product: GET /store/products/{id}
4. map to Storecraft ProductTypeUpsert + VariantType[]
5. app.api.products.upsert(parent product)
6. app.api.products.upsert(each variant)
7. log counts; failures recorded individually so one bad product does not abort the sync
```

- Existing Storecraft products not created by Printful are left untouched.
- A product is considered "managed by Printful" if it has a `printful` tag or a `pf-<id>` handle prefix.
- `active` is set to Printful's availability; if Printful marks a variant out of stock, `qty` becomes 0.

### Live shipping rates

```text
1. Customer fills cart and address in Astro.
2. Astro POST /api/extensions/printful/shipping-rates
   { address, lineItems: [{ productHandle, variantHint, qty }] }
3. Extension maps line items to Printful variant IDs.
4. POST /shipping/rates (Printful)
5. Return [{ id, name, rate, currency }]
6. Customer selects a rate.
7. Astro POST /api/extensions/printful/select-shipping-rate
   { rateId, address, lineItems }
8. Extension creates a unique Storecraft ShippingMethodType with the live price:
   { handle: "pf-ship-<rateId>-<shortUid>", title: name, price: rate }
   The unique suffix prevents collisions between concurrent customers.
9. Astro creates checkout with the returned shipping_method handle.
```

Temporary shipping methods are cleaned up after checkout completion or by the periodic sync job.

### Order push

```text
1. Storecraft emits orders/payments/captured.
2. Extension checks that all line items belong to Printful-managed products.
3. If yes, build Printful order payload:
   - recipient from order.address + order.contact
   - items from lineItems (variant id, qty, retail_price snapshot)
   - shipping method from the rate id stored in order.notes or shipping_method metadata
4. POST /orders (Printful)
5. Store Printful order id in order.notes / attributes:
   { printful_order_id: "<id>", printful_status: "pending" }
6. app.api.orders.upsert(order) to persist metadata.
```

If the push fails, the error is logged and stored in order metadata; a manual retry can be triggered via `push-order` action.

### Status updates

**Webhook path:**

```text
Printful --▶ POST mugs.app.moonsbow.com/api/printful-webhook
Astro verifies signature
Astro --▶ POST backshop.app.moonsbow.com/api/extensions/printful/sync-order-status
Extension finds Storecraft order by printful_order_id
Extension GET /orders/{id} (Printful)
Extension updates order.status / notes / tracking info
```

**Polling fallback:**

During each catalog sync, the extension also iterates over recent Storecraft orders that have a `printful_order_id` but are not in a terminal status, and calls `sync-order-status` for each.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PRINTFUL_API_TOKEN` | yes | — | Printful private API token |
| `PRINTFUL_STORE_ID` | no | — | Required only for account-level tokens |
| `PRINTFUL_WEBHOOK_SECRET` | no | — | Secret for verifying Printful v2 webhooks |
| `PRINTFUL_INTERNAL_SECRET` | yes | — | Shared secret for internal/admin extension actions |
| `PRINTFUL_SYNC_INTERVAL_MINUTES` | no | `60` | Interval for background catalog sync (`0` disables) |
| `PRINTFUL_BASE_URL` | no | `https://api.printful.com` | Useful for mocking/tests |

## Error Handling

- Missing credentials: extension logs warning and skips all operations; app still boots.
- Printful API errors: wrapped in typed error with status, message and context; logged; per-item failures do not abort a full sync.
- Order push failure: stored in order metadata (`printful_push_error`); admin can retry via action.
- Webhook signature failure: Astro returns `401` and ignores payload.
- Duplicate catalog sync: actions are idempotent (upsert by handle); concurrent runs are not guarded in v1.

## Security

- `PRINTFUL_API_TOKEN` and `PRINTFUL_WEBHOOK_SECRET` are never sent to the browser.
- `sync-catalog`, `push-order` and `sync-order-status` require the `PRINTFUL_INTERNAL_SECRET` shared secret.
- Webhook signature uses HMAC-SHA256 with constant-time comparison.
- Storefront only calls public actions (`shipping-rates`, `select-shipping-rate`) and never the Printful API directly.

## Testing Strategy

- Unit tests in `@mugs/printful` for transformers using sample Printful payloads.
- Integration tests with a mocked Printful HTTP server (`undici` mock or `msw`) for the client and extension actions.
- Manual end-to-end test:
  1. Run sync-catalog and verify products appear in Storecraft.
  2. Add product to cart, fetch shipping rates, complete checkout with Stripe test card.
  3. Verify Printful order created.
  4. Trigger webhook or poll until status updates in Storecraft.

## Deployment

1. Add Printful env vars to Dokploy `Mugs` compose environment.
2. Deploy updated `apps/core` image (now depends on `@mugs/printful`).
3. Deploy updated `apps/web` image with the new webhook route.
4. Run initial `sync-catalog` manually via the Storecraft admin or a one-off curl.
5. Configure Printful webhook URL to `https://mugs.app.moonsbow.com/api/printful-webhook` and copy the secret into Dokploy.

## Open Questions / Future Work

- The provided `printful.json` OpenAPI spec was not present in the repo at design time; endpoint paths and field names will be validated against that spec during implementation.
- Currency handling: v1 assumes USD. Multi-currency support can be added later by reading `general_store_currency` from Storecraft config.
- Webhook vs polling: polling is the fallback; webhooks give faster updates once configured.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use a Storecraft extension instead of a separate service | Reuses auth, REST routing, pubsub and product/order APIs. Fewer moving parts. |
| Package as `@mugs/printful` | Keeps Printful logic isolated and testable; can be consumed by core and, if needed, by web later. |
| Temporary shipping methods for live rates | Storecraft checkout requires a `shipping_method` resource. Creating one on the fly is the least intrusive way to inject a live price without modifying Storecraft core. |
| Webhook endpoint in Astro, not core | Storecraft extension actions do not expose HTTP headers, which are required to verify Printful signatures. Astro SSR can read headers and forward safely to core. |
| Polling fallback | Guarantees status updates even if webhooks are not configured or fail. |
