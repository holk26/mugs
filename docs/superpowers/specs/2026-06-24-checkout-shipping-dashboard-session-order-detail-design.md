# Checkout Shipping, Dashboard Session Persistence, and Order Detail

## Context

The mugs store now has a working product catalog, cart, and Stripe payment flow. However, end-to-end order fulfillment is still blocked because the checkout does not collect a shipping address, which Printful requires to create a production order. Additionally, the dashboard experience is incomplete: sessions are lost on page refresh, and the order detail view lacks the line items, uploaded drawing, and shipping address needed to operate the business.

## Goals

1. Collect a valid shipping address during checkout and store it on the order.
2. Persist the dashboard access token so admins stay logged in across page refreshes.
3. Show a complete order detail view in the dashboard, including line items, customer upload, and shipping address.

## Scope

### In scope

- Shipping address form in `CheckoutForm.tsx`.
- Country select limited to Printful-supported destination countries.
- Passing `shipping_address` to the order creation API.
- Updating `push_order` to use `settings.SITE_URL` for upload URLs instead of a hardcoded domain.
- Persisting `accessToken` in the dashboard auth store and restoring it on app load.
- Rendering order lines, upload preview/download, and formatted shipping address in `orders.$id.tsx`.

### Out of scope

- Real-time shipping rate calculation at checkout.
- Address validation against third-party APIs.
- Editing orders from the dashboard.
- Customer accounts or order history for shoppers.

## Design

### A. Checkout shipping address

#### Frontend

`CheckoutForm.tsx` gains a second step before payment:

- Step 1: Contact + Shipping
  - Full name (text)
  - Email (email)
  - Address line 1 (text)
  - City (text)
  - State / Province (text)
  - Postal code (text)
  - Country (select, see Country List below)
- Step 2: Payment (existing Stripe Payment Element)

Validation happens before advancing to payment. The order creation payload sent to `POST /api/v1/orders/` includes:

```json
{
  "customer_name": "Jane Doe",
  "customer_email": "jane@example.com",
  "shipping_address": {
    "name": "Jane Doe",
    "address1": "123 Main St",
    "city": "Austin",
    "state_code": "TX",
    "zip": "78701",
    "country_code": "US"
  },
  "lines": [...]
}
```

The order summary sidebar shows the formatted shipping address.

#### Backend

`OrderSerializer.create()` already stores `shipping_address`. No model changes are needed.

`apps/printful/sync.py`:

- Replace the hardcoded `https://mugs.app.moonsbow.com` prefix for `customer_upload` URLs with `settings.SITE_URL`.
- Default to `https://mugs.app.moonsbow.com` if `SITE_URL` is not configured to avoid breaking existing behavior.

`config/settings.py`:

- Add `SITE_URL = os.environ.get("SITE_URL", "https://mugs.app.moonsbow.com")`.

`docker-compose.yml` and `docker-compose.dokploy.yml`:

- Pass `SITE_URL` to the `django` service environment.

#### Country list

Use a curated static list of countries where Printful delivers. The list is stored in a shared constant file so it can be reused. Example entries:

- `US` — United States
- `CA` — Canada
- `MX` — Mexico
- `GB` — United Kingdom
- `ES` — Spain
- `AU` — Australia
- `DE` — Germany
- `FR` — France

The list can be extended later. The backend does not validate against this list; it only stores whatever the frontend sends. This keeps iteration easy.

### B. Dashboard session persistence

#### Frontend

`apps/dashboard/src/stores/authStore.ts`:

- Include `accessToken` in the `partialize` function so it is persisted alongside `user`.
- Keep `refreshToken` persisted via localStorage as it is today.

`apps/dashboard/src/routes/__root.tsx`:

- On mount, if a persisted `accessToken` exists and the user object is present, skip the immediate refresh and trust the token.
- Keep the existing `refreshToken` call as a fallback when no valid access token is available or when the token is about to expire.
- This eliminates the visible "Cargando..." state caused by the refresh race when navigating directly to a route.

#### Backend

No backend changes required.

### C. Order detail view

#### Frontend

`apps/dashboard/src/routes/orders.$id.tsx`:

- Display order metadata: status, customer name/email, total, currency, created/updated dates, Printful order ID/status.
- Render `lines` in a table with columns:
  - Product (title)
  - Variant
  - Quantity
  - Price
  - Customer upload (thumbnail + download link if present)
- Render `shipping_address` as a formatted address block.
- Add a "Download drawing" link per line that points to `/media/<path>`.

#### Backend

`OrderSerializer` already returns `lines` and `shipping_address`. `customer_upload` is a `FileField`, so DRF returns the relative URL by default. Ensure the media route in Traefik serves `/media/drawings/...`.

## Data flow

### Checkout with shipping

```
User adds mug to cart → /checkout
  ↓
Fills contact + shipping address
  ↓
POST /api/v1/orders/ with shipping_address
  ↓
Backend creates Order + OrderLines
  ↓
POST /api/v1/payments/create-intent/ → Stripe PaymentIntent
  ↓
User pays with Stripe
  ↓
Stripe webhook payment_intent.succeeded
  ↓
Backend sets order.status = 'paid'
  ↓
post_save signal calls push_order(order)
  ↓
Printful order created with recipient from shipping_address and upload URL from SITE_URL
```

## Error handling

- Invalid shipping address blocks advance to payment.
- If Printful order creation fails after payment, the order remains `paid` and the failure is logged. A future iteration can add a retry UI.
- If the dashboard persisted token is rejected, the app falls back to refresh; if refresh fails, the user is redirected to `/login`.

## Testing

- Verify checkout creates an order with a populated `shipping_address`.
- Verify Printful order push uses `SITE_URL` for upload URLs.
- Verify dashboard order detail shows lines, upload link, and shipping address.
- Verify refreshing the dashboard while logged in does not log the user out.

## Iteration notes

- The country list is intentionally a static constant. If Printful support changes, update the constant.
- Shipping rates are not calculated yet; `shipping: 'STANDARD'` is used in the Printful order.
- Order detail download links rely on the existing `/media/` Traefik route.
