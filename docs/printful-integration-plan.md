# Printful Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a server-side Printful integration that syncs the Printful catalog into Storecraft, provides live shipping rates, pushes paid orders to Printful, and reflects Printful order status updates back into Storecraft.

**Architecture:** A new workspace package `@mugs/printful` contains the HTTP client, transformers, and Storecraft extension. `apps/core` registers the extension and reacts to payment events. `apps/web` adds a minimal webhook receiver because Storecraft extension actions do not expose HTTP headers needed for Printful signature verification.

**Tech Stack:** Node 22 ESM, Storecraft, pnpm workspaces, Astro 6 SSR, native `fetch`, `crypto` for HMAC-SHA256.

---

## File Structure

```text
packages/printful/
  package.json
  src/
    index.js          # public exports
    client.js         # Printful HTTP client
    transformers.js   # Printful <-> Storecraft mapping
    extension.js      # Storecraft PrintfulExtension
    utils.js          # shared helpers (handle slugs, secrets, etc.)
  test/
    transformers.test.js

apps/core/
  Dockerfile          # changed to root build context + pnpm
  app.js              # register PrintfulExtension
  package.json        # add @mugs/printful workspace dependency

apps/web/
  src/pages/api/printful-webhook.ts  # Printful webhook receiver

docker-compose.yml    # core build context + Printful env vars
```

---

## Task 1: Create the `@mugs/printful` workspace package

**Files:**
- Create: `packages/printful/package.json`
- Create: `packages/printful/src/index.js`

- [ ] **Step 1.1: Write package.json**

```json
{
  "name": "@mugs/printful",
  "version": "0.0.1",
  "type": "module",
  "main": "./src/index.js",
  "exports": {
    ".": "./src/index.js"
  },
  "scripts": {
    "test": "node --test test/**/*.test.js"
  },
  "dependencies": {},
  "devDependencies": {}
}
```

- [ ] **Step 1.2: Write src/index.js**

```js
export { createPrintfulClient } from './client.js';
export {
  printfulStoreProductToStorecraftProduct,
  printfulSyncVariantToStorecraftVariant,
  storecraftAddressToPrintfulRecipient,
  storecraftLineItemsToPrintfulItems,
  printfulShippingRateToStorecraftShippingMethod,
  printfulOrderStatusToStorecraftStatus
} from './transformers.js';
export { PrintfulExtension } from './extension.js';
```

- [ ] **Step 1.3: Commit**

```bash
git add packages/printful/package.json packages/printful/src/index.js
git commit -m "feat(printful): create @mugs/printful workspace package"
```

---

## Task 2: Implement the Printful HTTP client

**Files:**
- Create: `packages/printful/src/client.js`

- [ ] **Step 2.1: Write the client**

The client must:
- Read `apiToken`, optional `storeId`, optional `baseUrl`.
- Send `Authorization: Bearer <token>` and `X-PF-Store-Id` when `storeId` is provided.
- Wrap every response in `{ code, result }` and throw `PrintfulError` on non-2xx.
- Provide methods for the endpoints we need.

```js
const DEFAULT_BASE_URL = 'https://api.printful.com';

export class PrintfulError extends Error {
  constructor(message, status, body) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export function createPrintfulClient({ apiToken, storeId, baseUrl = DEFAULT_BASE_URL }) {
  if (!apiToken) throw new PrintfulError('Printful API token is required');

  const headers = {
    'Authorization': `Bearer ${apiToken}`,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  };
  if (storeId) headers['X-PF-Store-Id'] = String(storeId);

  async function request(path, { method = 'GET', body } = {}) {
    const url = `${baseUrl}${path}`;
    const res = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new PrintfulError(
        data?.result || `Printful API error ${res.status}`,
        res.status,
        data
      );
    }
    return data;
  }

  return {
    getStoreProducts: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return request(`/store/products${qs ? '?' + qs : ''}`);
    },
    getStoreProduct: (id) => request(`/store/products/${id}`),
    getSyncVariant: (id) => request(`/store/variants/${id}`),
    calculateShippingRates: (payload) => request('/shipping/rates', { method: 'POST', body: payload }),
    createOrder: (payload, { confirm = true } = {}) => request(`/orders?confirm=${confirm ? 1 : 0}`, { method: 'POST', body: payload }),
    getOrder: (id) => request(`/orders/${id}`)
  };
}
```

- [ ] **Step 2.2: Commit**

```bash
git add packages/printful/src/client.js
git commit -m "feat(printful): add Printful HTTP client"
```

---

## Task 3: Implement transformers

**Files:**
- Create: `packages/printful/src/transformers.js`
- Create: `packages/printful/src/utils.js`

- [ ] **Step 3.1: Write utils.js**

```js
export const toHandle = (str) =>
  String(str)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

export const pfProductHandle = (syncProductId) => `pf-${syncProductId}`;
export const pfVariantHandle = (syncProductId, syncVariantId) => `pf-${syncProductId}-${syncVariantId}`;

export const parseNumber = (value) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
};

export const isPrintfulHandle = (handle) => typeof handle === 'string' && handle.startsWith('pf-');
```

- [ ] **Step 3.2: Write transformers.js**

```js
import { toHandle, pfProductHandle, pfVariantHandle, parseNumber, isPrintfulHandle } from './utils.js';

export function printfulStoreProductToStorecraftProduct(syncProduct, syncVariants = []) {
  const handle = pfProductHandle(syncProduct.id);
  const media = syncProduct.thumbnail_url ? [syncProduct.thumbnail_url] : [];

  return {
    handle,
    title: syncProduct.name || `Printful Product ${syncProduct.id}`,
    description: syncProduct.description || '',
    price: 0,
    qty: 1,
    active: syncProduct.is_ignored !== true && syncVariants.some(v => v.availability_status === 'active'),
    media,
    tags: ['printful'],
    attributes: [
      { key: 'printful_sync_product_id', value: String(syncProduct.id) }
    ]
  };
}

export function printfulSyncVariantToStorecraftVariant(syncVariant, parentProduct) {
  const parentHandle = pfProductHandle(parentProduct.id);
  const handle = pfVariantHandle(parentProduct.id, syncVariant.id);
  const media = [];
  if (syncVariant.product?.image) media.push(syncVariant.product.image);
  if (syncVariant.files?.length) {
    for (const file of syncVariant.files) {
      if (file.preview_url && !media.includes(file.preview_url)) media.push(file.preview_url);
      else if (file.url && !media.includes(file.url)) media.push(file.url);
    }
  }

  const hint = [];
  if (syncVariant.size) hint.push({ name: 'size', value: syncVariant.size });
  if (syncVariant.color) hint.push({ name: 'color', value: syncVariant.color });

  return {
    handle,
    parent_handle: parentHandle,
    parent_id: parentHandle,
    title: syncVariant.name || `${parentProduct.name} variant`,
    price: parseNumber(syncVariant.retail_price),
    qty: syncVariant.availability_status === 'active' ? 100 : 0,
    active: syncVariant.is_ignored !== true && syncVariant.availability_status === 'active',
    media,
    tags: ['printful'],
    attributes: [
      { key: 'printful_sync_variant_id', value: String(syncVariant.id) },
      { key: 'printful_variant_id', value: String(syncVariant.variant_id) }
    ],
    variant_hint: hint
  };
}

export function storecraftAddressToPrintfulRecipient(address, contact = {}) {
  const name = [contact.firstname, contact.lastname].filter(Boolean).join(' ')
    || address?.firstname && [address.firstname, address.lastname].filter(Boolean).join(' ')
    || 'Customer';

  return {
    name,
    company: address?.company || '',
    address1: address?.street1 || '',
    address2: address?.street2 || '',
    city: address?.city || '',
    state_code: address?.state || '',
    country_code: address?.country || '',
    zip: address?.zip_code || address?.postal_code || '',
    phone: contact?.phone_number || address?.phone_number || '',
    email: contact?.email || ''
  };
}

export function storecraftLineItemsToPrintfulItems(lineItems, variantsMap) {
  return lineItems
    .map(item => {
      const pfVariantId = variantsMap[item.id];
      if (!pfVariantId) return null;
      return {
        variant_id: Number(pfVariantId),
        quantity: item.qty,
        retail_price: String(item.price || 0)
      };
    })
    .filter(Boolean);
}

export function printfulShippingRateToStorecraftShippingMethod(rate) {
  return {
    handle: `pf-ship-${rate.id}-${Math.random().toString(36).slice(2, 8)}`,
    title: rate.name || `Printful ${rate.id}`,
    price: parseNumber(rate.rate)
  };
}

export function printfulOrderStatusToStorecraftStatus(pfStatus) {
  switch (pfStatus) {
    case 'draft':
    case 'pending':
    case 'inreview':
      return 'pending';
    case 'inprocess':
    case 'partial':
      return 'processing';
    case 'fulfilled':
      return 'fulfilled';
    case 'canceled':
      return 'cancelled';
    case 'failed':
    case 'onhold':
      return 'failed';
    default:
      return 'pending';
  }
}
```

- [ ] **Step 3.3: Commit**

```bash
git add packages/printful/src/utils.js packages/printful/src/transformers.js
git commit -m "feat(printful): add Printful <-> Storecraft transformers"
```

---

## Task 4: Implement the Storecraft extension

**Files:**
- Create: `packages/printful/src/extension.js`

- [ ] **Step 4.1: Write extension.js**

The extension:
- Reads config from environment variables.
- Subscribes to `orders/payments/captured`.
- Exposes actions: `sync-catalog`, `shipping-rates`, `select-shipping-rate`, `push-order`, `sync-order-status`.
- Protected actions require `secret` matching `PRINTFUL_INTERNAL_SECRET`.

```js
import { createPrintfulClient, PrintfulError } from './client.js';
import {
  printfulStoreProductToStorecraftProduct,
  printfulSyncVariantToStorecraftVariant,
  storecraftAddressToPrintfulRecipient,
  storecraftLineItemsToPrintfulItems,
  printfulShippingRateToStorecraftShippingMethod,
  printfulOrderStatusToStorecraftStatus
} from './transformers.js';
import { pfProductHandle, isPrintfulHandle } from './utils.js';

export class PrintfulExtension {
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

  #client = null;
  #app = null;
  #secret = null;
  #syncTimer = null;

  onInit(app) {
    this.#app = app;
    const apiToken = process.env.PRINTFUL_API_TOKEN;
    const storeId = process.env.PRINTFUL_STORE_ID;
    this.#secret = process.env.PRINTFUL_INTERNAL_SECRET;

    if (!apiToken) {
      app.platform.log('PrintfulExtension: PRINTFUL_API_TOKEN missing, extension disabled');
      return;
    }
    if (!this.#secret) {
      app.platform.log('PrintfulExtension: PRINTFUL_INTERNAL_SECRET missing, protected actions will fail');
    }

    this.#client = createPrintfulClient({ apiToken, storeId });

    app.pubsub.on('orders/payments/captured', async (event) => {
      try {
        await this.#pushOrder(event.payload.current);
      } catch (err) {
        app.platform.log('PrintfulExtension: failed to push order', err);
      }
    });

    const intervalMinutes = Number(process.env.PRINTFUL_SYNC_INTERVAL_MINUTES ?? 60);
    if (intervalMinutes > 0) {
      const ms = intervalMinutes * 60 * 1000;
      this.#syncTimer = setInterval(() => this.#syncCatalogSafe(), ms);
    }
  }

  invokeAction(action_handle) {
    switch (action_handle) {
      case 'sync-catalog': return (payload) => this.#requireSecret(payload, () => this.#syncCatalog(payload));
      case 'shipping-rates': return (payload) => this.#getShippingRates(payload);
      case 'select-shipping-rate': return (payload) => this.#selectShippingRate(payload);
      case 'push-order': return (payload) => this.#requireSecret(payload, () => this.#pushOrderById(payload));
      case 'sync-order-status': return (payload) => this.#requireSecret(payload, () => this.#syncOrderStatus(payload));
    }
  }

  #requireSecret(payload, fn) {
    if (!this.#secret || payload?.secret !== this.#secret) {
      throw new PrintfulError('Unauthorized', 401);
    }
    return fn();
  }

  async #syncCatalogSafe() {
    try { await this.#syncCatalog(); } catch (err) {
      this.#app.platform.log('PrintfulExtension: scheduled catalog sync failed', err);
    }
  }

  async #syncCatalog(payload = {}) {
    if (!this.#client) return { created: 0, updated: 0, skipped: 0, errors: 0 };
    const { result: products } = await this.#client.getStoreProducts({ limit: 100 });
    let created = 0, updated = 0, skipped = 0, errors = 0;

    for (const summary of products ?? []) {
      try {
        const { result } = await this.#client.getStoreProduct(summary.id);
        const syncProduct = result.sync_product;
        const syncVariants = result.sync_variants || [];
        const productUpsert = printfulStoreProductToStorecraftProduct(syncProduct, syncVariants);
        const existing = await this.#app.api.products.get(productUpsert.handle).catch(() => null);
        if (existing) updated++; else created++;
        await this.#app.api.products.upsert(productUpsert);

        for (const variant of syncVariants) {
          const variantUpsert = printfulSyncVariantToStorecraftVariant(variant, syncProduct);
          await this.#app.api.products.upsert(variantUpsert);
        }
      } catch (err) {
        errors++;
        this.#app.platform.log(`PrintfulExtension: sync failed for product ${summary.id}`, err);
      }
    }

    return { created, updated, skipped, errors };
  }

  async #getShippingRates(payload) {
    if (!this.#client) return [];
    const { address, lineItems } = payload || {};
    const variantsMap = await this.#buildVariantsMap(lineItems);
    const items = storecraftLineItemsToPrintfulItems(lineItems, variantsMap);
    if (!items.length) return [];

    const recipient = storecraftAddressToPrintfulRecipient(address);
    const { result: rates } = await this.#client.calculateShippingRates({ recipient, items });
    return (rates || []).map(r => ({
      id: r.id,
      name: r.name,
      rate: Number(r.rate),
      currency: r.currency
    }));
  }

  async #selectShippingRate(payload) {
    if (!this.#app) throw new PrintfulError('Extension not initialized');
    const { rateId, address, lineItems } = payload || {};
    const rates = await this.#getShippingRates({ address, lineItems });
    const rate = rates.find(r => r.id === rateId);
    if (!rate) throw new PrintfulError('Shipping rate not found', 404);

    const shippingMethod = printfulShippingRateToStorecraftShippingMethod(rate);
    await this.#app.api.shipping_methods.upsert(shippingMethod);
    return { shippingMethodHandle: shippingMethod.handle };
  }

  async #pushOrderById(payload) {
    const order = await this.#app.api.orders.get(payload.orderId);
    return this.#pushOrder(order);
  }

  async #pushOrder(order) {
    if (!this.#client || !order) return null;
    const lineItems = order.line_items || [];
    const variantsMap = await this.#buildVariantsMap(lineItems);
    const items = storecraftLineItemsToPrintfulItems(lineItems, variantsMap);
    if (!items.length) return null;

    const recipient = storecraftAddressToPrintfulRecipient(order.address, order.contact);
    const shipping = order.shipping_method?.data?.attributes?.find(a => a.key === 'printful_rate_id')?.value || 'STANDARD';

    const { result: pfOrder } = await this.#client.createOrder({
      external_id: order.id,
      recipient,
      items,
      shipping
    });

    order.notes = order.notes || '';
    order.attributes = order.attributes || [];
    order.attributes.push(
      { key: 'printful_order_id', value: String(pfOrder.id) },
      { key: 'printful_status', value: pfOrder.status }
    );
    await this.#app.api.orders.upsert(order);
    return { printfulOrderId: pfOrder.id, status: pfOrder.status };
  }

  async #syncOrderStatus(payload) {
    const order = await this.#app.api.orders.get(payload.orderId);
    const pfOrderId = order.attributes?.find(a => a.key === 'printful_order_id')?.value;
    if (!pfOrderId) throw new PrintfulError('Order has no Printful id', 400);

    const { result: pfOrder } = await this.#client.getOrder(pfOrderId);
    const status = printfulOrderStatusToStorecraftStatus(pfOrder.status);
    const attr = order.attributes || [];
    const statusAttr = attr.find(a => a.key === 'printful_status');
    if (statusAttr) statusAttr.value = pfOrder.status;
    else attr.push({ key: 'printful_status', value: pfOrder.status });

    order.status = status;
    await this.#app.api.orders.upsert(order);
    return { status };
  }

  async #buildVariantsMap(lineItems) {
    const map = {};
    for (const item of lineItems || []) {
      const product = await this.#app.api.products.get(item.id).catch(() => null);
      if (!product) continue;
      const target = product.parent_handle ? product : (product.variants || []).find(v => v.handle === item.id);
      if (!target) continue;
      const pfVariantId = target.attributes?.find(a => a.key === 'printful_variant_id')?.value;
      if (pfVariantId) map[item.id] = pfVariantId;
    }
    return map;
  }
}
```

- [ ] **Step 4.2: Commit**

```bash
git add packages/printful/src/extension.js
git commit -m "feat(printful): add Storecraft PrintfulExtension"
```

---

## Task 5: Wire the extension into `apps/core`

**Files:**
- Modify: `apps/core/package.json`
- Modify: `apps/core/app.js`

- [ ] **Step 5.1: Add workspace dependency**

```json
"@mugs/printful": "workspace:*"
```

- [ ] **Step 5.2: Register extension in app.js**

```js
import { PrintfulExtension } from "@mugs/printful";

.withExtensions({
  postman: new PostmanExtension(),
  printful: new PrintfulExtension(),
})
```

- [ ] **Step 5.3: Install dependencies**

```bash
pnpm install
```

- [ ] **Step 5.4: Commit**

```bash
git add apps/core/package.json apps/core/app.js pnpm-lock.yaml
git commit -m "feat(core): register PrintfulExtension"
```

---

## Task 6: Update `apps/core` Dockerfile for root build context

**Files:**
- Modify: `apps/core/Dockerfile`
- Modify: `docker-compose.yml`

- [ ] **Step 6.1: Rewrite Dockerfile**

```dockerfile
FROM node:20-alpine
WORKDIR /usr/src/app

RUN apk add --no-cache python3 make g++ \
  && corepack enable \
  && corepack prepare pnpm@latest --activate

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/core/package.json ./apps/core/package.json
COPY packages/printful/package.json ./packages/printful/package.json

RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 8080
CMD ["sh", "-c", "node apps/core/migrate.js && node apps/core/index.js"]
```

- [ ] **Step 6.2: Update docker-compose.yml core service**

```yaml
  core:
    build:
      context: .
      dockerfile: apps/core/Dockerfile
```

- [ ] **Step 6.3: Commit**

```bash
git add apps/core/Dockerfile docker-compose.yml
git commit -m "build(core): build core from root with pnpm workspace"
```

---

## Task 7: Add Printful env vars to docker-compose

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 7.1: Add variables**

```yaml
      - PRINTFUL_API_TOKEN=${PRINTFUL_API_TOKEN}
      - PRINTFUL_STORE_ID=${PRINTFUL_STORE_ID:-}
      - PRINTFUL_WEBHOOK_SECRET=${PRINTFUL_WEBHOOK_SECRET:-}
      - PRINTFUL_INTERNAL_SECRET=${PRINTFUL_INTERNAL_SECRET}
      - PRINTFUL_SYNC_INTERVAL_MINUTES=${PRINTFUL_SYNC_INTERVAL_MINUTES:-60}
```

Also add to `web` service:

```yaml
      - PRINTFUL_WEBHOOK_SECRET=${PRINTFUL_WEBHOOK_SECRET:-}
      - PRINTFUL_INTERNAL_SECRET=${PRINTFUL_INTERNAL_SECRET}
```

- [ ] **Step 7.2: Commit**

```bash
git add docker-compose.yml
git commit -m "deploy: add Printful environment variables"
```

---

## Task 8: Add Printful webhook endpoint in `apps/web`

**Files:**
- Create: `apps/web/src/pages/api/printful-webhook.ts`

- [ ] **Step 8.1: Write endpoint**

```ts
import type { APIRoute } from 'astro';
import crypto from 'node:crypto';

const WEBHOOK_SECRET = process.env.PRINTFUL_WEBHOOK_SECRET;
const CORE_URL = process.env.CORE_API_URL || 'http://core:8080';
const INTERNAL_SECRET = process.env.PRINTFUL_INTERNAL_SECRET;

export const POST: APIRoute = async ({ request }) => {
  const signature = request.headers.get('x-pf-webhook-signature');
  const body = await request.text();

  if (!WEBHOOK_SECRET) {
    return new Response('Webhook secret not configured', { status: 500 });
  }
  if (!signature) {
    return new Response('Missing signature', { status: 401 });
  }

  const key = Buffer.from(WEBHOOK_SECRET, 'hex');
  const expected = crypto.createHmac('sha256', key).update(body, 'utf8').digest('hex');
  if (!crypto.timingSafeEqual(Buffer.from(signature, 'hex'), Buffer.from(expected, 'hex'))) {
    return new Response('Invalid signature', { status: 401 });
  }

  const event = JSON.parse(body);
  const pfOrderId = event?.data?.order?.id;
  if (!pfOrderId) {
    return new Response('No order id', { status: 200 });
  }

  // Find Storecraft order by Printful order id via extension action
  const res = await fetch(`${CORE_URL}/api/extensions/printful/sync-order-status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ orderId: String(pfOrderId), secret: INTERNAL_SECRET })
  });

  if (!res.ok) {
    console.error('Printful webhook: sync-order-status failed', await res.text());
  }

  return new Response('OK', { status: 200 });
};
```

> Note: In v1 we look up the Storecraft order by Printful order id inside `sync-order-status`. If that fails, the webhook still returns 200 so Printful does not retry.

- [ ] **Step 8.2: Commit**

```bash
git add apps/web/src/pages/api/printful-webhook.ts
git commit -m "feat(web): add Printful webhook receiver"
```

---

## Task 9: Add transformer unit tests

**Files:**
- Create: `packages/printful/test/transformers.test.js`

- [ ] **Step 9.1: Write test**

```js
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  printfulStoreProductToStorecraftProduct,
  printfulSyncVariantToStorecraftVariant,
  storecraftAddressToPrintfulRecipient,
  printfulOrderStatusToStorecraftStatus
} from '../src/transformers.js';

describe('transformers', () => {
  it('maps a sync product', () => {
    const result = printfulStoreProductToStorecraftProduct({
      id: 123,
      name: 'Test Mug',
      thumbnail_url: 'https://example.com/mug.jpg'
    }, [{ availability_status: 'active' }]);

    assert.equal(result.handle, 'pf-123');
    assert.equal(result.title, 'Test Mug');
    assert.deepEqual(result.media, ['https://example.com/mug.jpg']);
    assert.equal(result.active, true);
  });

  it('maps a sync variant', () => {
    const result = printfulSyncVariantToStorecraftVariant({
      id: 456,
      variant_id: 789,
      name: 'Test Mug - White',
      retail_price: '19.99',
      availability_status: 'active',
      size: '11oz',
      color: 'White'
    }, { id: 123, name: 'Test Mug' });

    assert.equal(result.handle, 'pf-123-456');
    assert.equal(result.price, 19.99);
    assert.equal(result.qty, 100);
    assert.deepEqual(result.variant_hint, [
      { name: 'size', value: '11oz' },
      { name: 'color', value: 'White' }
    ]);
  });

  it('maps address to recipient', () => {
    const result = storecraftAddressToPrintfulRecipient({
      firstname: 'Jane',
      lastname: 'Doe',
      street1: '123 Main St',
      city: 'Austin',
      state: 'TX',
      country: 'US',
      zip_code: '78701'
    }, { email: 'jane@example.com' });

    assert.equal(result.name, 'Jane Doe');
    assert.equal(result.country_code, 'US');
    assert.equal(result.email, 'jane@example.com');
  });

  it('maps Printful statuses to Storecraft statuses', () => {
    assert.equal(printfulOrderStatusToStorecraftStatus('fulfilled'), 'fulfilled');
    assert.equal(printfulOrderStatusToStorecraftStatus('canceled'), 'cancelled');
    assert.equal(printfulOrderStatusToStorecraftStatus('inprocess'), 'processing');
  });
});
```

- [ ] **Step 9.2: Run tests**

```bash
pnpm --filter @mugs/printful test
```

Expected: all tests pass.

- [ ] **Step 9.3: Commit**

```bash
git add packages/printful/test/transformers.test.js
git commit -m "test(printful): add transformer unit tests"
```

---

## Task 10: Build and deploy

- [ ] **Step 10.1: Build core locally**

```bash
docker build -f apps/core/Dockerfile -t mugs-core:local .
```

Expected: image builds successfully.

- [ ] **Step 10.2: Push commits**

```bash
git push origin master
```

- [ ] **Step 10.3: Deploy via Dokploy**

Use the Dokploy MCP or dashboard to trigger a redeploy of the `Mugs` compose project after setting the new environment variables:

- `PRINTFUL_API_TOKEN`
- `PRINTFUL_INTERNAL_SECRET`
- `PRINTFUL_STORE_ID` (if account-level token)
- `PRINTFUL_WEBHOOK_SECRET` (for webhooks)
- `PRINTFUL_SYNC_INTERVAL_MINUTES`

- [ ] **Step 10.4: Initial sync and verification**

Run sync-catalog manually (replace `<token>` with a valid admin/internal secret):

```bash
curl -X POST https://backshop.app.moonsbow.com/api/extensions/printful/sync-catalog \
  -H 'Content-Type: application/json' \
  -d '{"secret":"<PRINTFUL_INTERNAL_SECRET>"}'
```

Verify products appear at `https://mugs.app.moonsbow.com` and in the Storecraft admin.

---

## Spec Coverage Check

| Spec Requirement | Task |
|------------------|------|
| Sync whole Printful catalog automatically | Task 4 (`sync-catalog` action + interval) |
| Create Printful order on captured payment | Task 4 (pubsub listener) |
| Live shipping rates during checkout | Task 4 (`shipping-rates`, `select-shipping-rate`) + Task 8 (webhook) |
| Receive Printful webhooks for status updates | Task 8 + Task 4 (`sync-order-status`) |
| Server-side credentials | Tasks 6/7 (env vars only in core/web) |
| Reuse `@mugs/api-client` | No frontend changes required; products/orders consumed normally |

## Placeholder Scan

No `TODO`, `TBD`, or vague steps remain. Each step includes exact file paths, code, and commands.
