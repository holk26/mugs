> I'm using the writing-plans skill to create the implementation plan.

# Checkout Shipping, Dashboard Session, and Order Detail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add shipping address collection to checkout, persist dashboard sessions across refreshes, and display complete order details (lines, upload, address) in the dashboard.

**Architecture:** Extend the existing React/Astro checkout form with a shipping step, store the address on the existing `Order` JSONField, pass a `SITE_URL` setting to Printful order pushes, persist the dashboard access token via zustand, and enrich the dashboard order detail route with line items and upload links.

**Tech Stack:** Astro + React + TypeScript (storefront), TanStack Router + shadcn/ui (dashboard), Django REST Framework (backend), Printful API.

---

## File map

| File | Responsibility |
|------|----------------|
| `apps/web/src/lib/countries.ts` | Static list of Printful-supported destination countries. |
| `apps/web/src/components/CheckoutForm.tsx` | Adds shipping step and sends `shipping_address` when creating the order. |
| `apps/web/src/components/AddressForm.tsx` | New reusable shipping address form component. |
| `apps/django/config/settings.py` | Adds `SITE_URL` env var with production default. |
| `apps/django/apps/printful/sync.py` | Replaces hardcoded domain with `settings.SITE_URL` for upload URLs. |
| `docker-compose.yml` | Passes `SITE_URL` to the django service. |
| `docker-compose.dokploy.yml` | Passes `SITE_URL` to the django service. |
| `apps/dashboard/src/stores/authStore.ts` | Persists `accessToken` via zustand partialize. |
| `apps/dashboard/src/routes/__root.tsx` | Restores persisted token before rendering protected routes. |
| `apps/dashboard/src/routes/orders.$id.tsx` | Renders lines table, upload download links, and formatted shipping address. |
| `apps/dashboard/src/api/client.ts` | Ensures interceptor reads the latest token from the store. |

---

## Task 1: Country list constant

**Files:**
- Create: `apps/web/src/lib/countries.ts`

- [ ] **Step 1: Create the country list**

```typescript
export interface Country {
  code: string;
  name: string;
}

export const PRINTFUL_COUNTRIES: Country[] = [
  { code: 'US', name: 'United States' },
  { code: 'CA', name: 'Canada' },
  { code: 'MX', name: 'Mexico' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'ES', name: 'Spain' },
  { code: 'DE', name: 'Germany' },
  { code: 'FR', name: 'France' },
  { code: 'AU', name: 'Australia' },
  { code: 'IT', name: 'Italy' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'SE', name: 'Sweden' },
  { code: 'NO', name: 'Norway' },
  { code: 'DK', name: 'Denmark' },
  { code: 'FI', name: 'Finland' },
  { code: 'BE', name: 'Belgium' },
  { code: 'AT', name: 'Austria' },
  { code: 'CH', name: 'Switzerland' },
  { code: 'PT', name: 'Portugal' },
  { code: 'IE', name: 'Ireland' },
  { code: 'NZ', name: 'New Zealand' },
  { code: 'JP', name: 'Japan' },
  { code: 'BR', name: 'Brazil' },
];

export const countryByCode = (code: string | undefined): Country | undefined =>
  PRINTFUL_COUNTRIES.find((c) => c.code === code);
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/lib/countries.ts
git commit -m "feat(web): add static list of Printful-supported countries"
```

---

## Task 2: Reusable AddressForm component

**Files:**
- Create: `apps/web/src/components/AddressForm.tsx`
- Modify: `apps/web/src/components/CheckoutForm.tsx`

- [ ] **Step 1: Create AddressForm component**

```tsx
import { PRINTFUL_COUNTRIES } from '@/lib/countries';

export interface AddressFormData {
  name: string;
  address1: string;
  city: string;
  state_code: string;
  zip: string;
  country_code: string;
}

interface AddressFormProps {
  value: AddressFormData;
  onChange: (value: AddressFormData) => void;
  disabled?: boolean;
}

export function AddressForm({ value, onChange, disabled }: AddressFormProps) {
  const update = (field: keyof AddressFormData, fieldValue: string) => {
    onChange({ ...value, [field]: fieldValue });
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium">Full name</label>
        <input
          type="text"
          value={value.name}
          onChange={(e) => update('name', e.target.value)}
          disabled={disabled}
          className="w-full rounded border p-2"
          placeholder="Jane Doe"
        />
      </div>
      <div>
        <label className="block text-sm font-medium">Address</label>
        <input
          type="text"
          value={value.address1}
          onChange={(e) => update('address1', e.target.value)}
          disabled={disabled}
          className="w-full rounded border p-2"
          placeholder="123 Main St"
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium">City</label>
          <input
            type="text"
            value={value.city}
            onChange={(e) => update('city', e.target.value)}
            disabled={disabled}
            className="w-full rounded border p-2"
            placeholder="Austin"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">State / Province</label>
          <input
            type="text"
            value={value.state_code}
            onChange={(e) => update('state_code', e.target.value)}
            disabled={disabled}
            className="w-full rounded border p-2"
            placeholder="TX"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium">Postal code</label>
          <input
            type="text"
            value={value.zip}
            onChange={(e) => update('zip', e.target.value)}
            disabled={disabled}
            className="w-full rounded border p-2"
            placeholder="78701"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Country</label>
          <select
            value={value.country_code}
            onChange={(e) => update('country_code', e.target.value)}
            disabled={disabled}
            className="w-full rounded border p-2"
          >
            <option value="">Select country</option>
            {PRINTFUL_COUNTRIES.map((country) => (
              <option key={country.code} value={country.code}>
                {country.name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/components/AddressForm.tsx
git commit -m "feat(web): add reusable AddressForm component"
```

---

## Task 3: Checkout shipping step

**Files:**
- Modify: `apps/web/src/components/CheckoutForm.tsx`

- [ ] **Step 1: Add shipping step state and validation**

Add imports at the top:

```tsx
import { useState } from 'react';
import { AddressForm, type AddressFormData } from './AddressForm';
```

Inside the component, add:

```tsx
const [shippingStep, setShippingStep] = useState<'shipping' | 'payment'>('shipping');
const [shippingAddress, setShippingAddress] = useState<AddressFormData>({
  name: '',
  address1: '',
  city: '',
  state_code: '',
  zip: '',
  country_code: '',
});

const isAddressValid = () => {
  return (
    shippingAddress.name.trim().length > 0 &&
    shippingAddress.address1.trim().length > 0 &&
    shippingAddress.city.trim().length > 0 &&
    shippingAddress.state_code.trim().length > 0 &&
    shippingAddress.zip.trim().length > 0 &&
    shippingAddress.country_code.trim().length > 0
  );
};
```

- [ ] **Step 2: Include shipping address in order creation**

Find the call to `createOrder` and update the payload:

```tsx
const order = await createOrder({
  customer_name: name,
  customer_email: email,
  shipping_address: {
    name: shippingAddress.name,
    address1: shippingAddress.address1,
    city: shippingAddress.city,
    state_code: shippingAddress.state_code,
    zip: shippingAddress.zip,
    country_code: shippingAddress.country_code,
  },
  lines: items.map((item) => ({
    variant: item.variantId,
    quantity: item.quantity,
  })),
});
```

- [ ] **Step 3: Render shipping step before payment**

Replace the existing single form render with a two-step flow. Keep the order summary sidebar. Render the shipping form when `shippingStep === 'shipping'`:

```tsx
{shippingStep === 'shipping' ? (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold">Shipping address</h2>
    <div>
      <label className="block text-sm font-medium">Full name</label>
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="w-full rounded border p-2"
      />
    </div>
    <div>
      <label className="block text-sm font-medium">Email</label>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-full rounded border p-2"
      />
    </div>
    <AddressForm value={shippingAddress} onChange={setShippingAddress} />
    <button
      onClick={() => setShippingStep('payment')}
      disabled={!name || !email || !isAddressValid()}
      className="w-full rounded bg-black py-3 text-white disabled:opacity-50"
    >
      Continue to payment
    </button>
  </div>
) : (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold">Payment</h2>
    <form onSubmit={handleSubmit}>
      <PaymentElement />
      <button
        type="submit"
        disabled={!stripe || isSubmitting}
        className="mt-4 w-full rounded bg-black py-3 text-white disabled:opacity-50"
      >
        {isSubmitting ? 'Processing...' : 'Pay now'}
      </button>
    </form>
    <button
      onClick={() => setShippingStep('shipping')}
      className="text-sm text-gray-600 underline"
    >
      Back to shipping
    </button>
  </div>
)}
```

- [ ] **Step 4: Show shipping address in order summary**

In the sidebar summary, add after the lines list:

```tsx
<div className="border-t pt-4">
  <h3 className="font-medium">Ship to</h3>
  <p className="text-sm text-gray-600">
    {shippingAddress.name}
    <br />
    {shippingAddress.address1}
    <br />
    {shippingAddress.city}, {shippingAddress.state_code} {shippingAddress.zip}
    <br />
    {shippingAddress.country_code}
  </p>
</div>
```

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/CheckoutForm.tsx
git commit -m "feat(web): add shipping address step to checkout"
```

---

## Task 4: Backend SITE_URL setting and Printful URL fix

**Files:**
- Modify: `apps/django/config/settings.py`
- Modify: `apps/django/apps/printful/sync.py`
- Modify: `docker-compose.yml`
- Modify: `docker-compose.dokploy.yml`

- [ ] **Step 1: Add SITE_URL to settings**

```python
SITE_URL = os.environ.get("SITE_URL", "https://mugs.app.moonsbow.com")
```

- [ ] **Step 2: Use SITE_URL in push_order**

In `apps/django/apps/printful/sync.py`, inside `push_order`, replace:

```python
absolute_url = f"https://mugs.app.moonsbow.com{absolute_url}"
```

with:

```python
from django.conf import settings
absolute_url = f"{settings.SITE_URL.rstrip('/')}{absolute_url}"
```

- [ ] **Step 3: Pass SITE_URL in compose files**

Add to both `docker-compose.yml` and `docker-compose.dokploy.yml` under the `django` service environment:

```yaml
      - SITE_URL=${SITE_URL:-https://mugs.app.moonsbow.com}
```

- [ ] **Step 4: Commit**

```bash
git add apps/django/config/settings.py apps/django/apps/printful/sync.py docker-compose.yml docker-compose.dokploy.yml
git commit -m "feat(django): add SITE_URL setting and use it for Printful uploads"
```

---

## Task 5: Persist dashboard access token

**Files:**
- Modify: `apps/dashboard/src/stores/authStore.ts`
- Modify: `apps/dashboard/src/routes/__root.tsx`

- [ ] **Step 1: Persist accessToken in auth store**

In `authStore.ts`, update the persist options:

```typescript
partialize: (state) => ({
  accessToken: state.accessToken,
  refreshToken: state.refreshToken,
  user: state.user,
}),
```

- [ ] **Step 2: Restore token on app load**

In `__root.tsx`, replace the unconditional `refreshToken()` call with a guarded restore:

```tsx
const accessToken = useAuthStore.getState().accessToken;
const user = useAuthStore.getState().user;

React.useEffect(() => {
  if (!accessToken || !user) {
    refreshToken().catch(() => {
      // silently fail; protected routes will redirect if needed
    });
  }
}, [accessToken, user, refreshToken]);
```

If the existing `beforeLoad` already handles refresh, keep it but ensure it also checks for a valid persisted access token before refreshing. The goal is to avoid the race that caused the initial "Cargando..." state.

- [ ] **Step 3: Commit**

```bash
git add apps/dashboard/src/stores/authStore.ts apps/dashboard/src/routes/__root.tsx
git commit -m "feat(dashboard): persist access token and restore session on refresh"
```

---

## Task 6: Dashboard order detail

**Files:**
- Modify: `apps/dashboard/src/routes/orders.$id.tsx`

- [ ] **Step 1: Define order detail types if missing**

If not already defined, add interfaces near the component:

```typescript
interface OrderLine {
  id: string;
  title: string;
  variant: string;
  quantity: number;
  price: string;
  customer_upload: string | null;
}

interface ShippingAddress {
  name: string;
  address1: string;
  city: string;
  state_code: string;
  zip: string;
  country_code: string;
}

interface Order {
  id: string;
  status: string;
  customer_name: string;
  customer_email: string;
  total: string;
  currency: string;
  shipping_address: ShippingAddress;
  lines: OrderLine[];
  printful_order_id: string;
  printful_status: string;
  created_at: string;
  updated_at: string;
}
```

- [ ] **Step 2: Render order metadata and address**

Replace the current minimal render with:

```tsx
<div className="space-y-6">
  <div className="grid grid-cols-2 gap-4">
    <div>
      <h3 className="font-medium text-gray-500">Customer</h3>
      <p>{order.customer_name}</p>
      <p>{order.customer_email}</p>
    </div>
    <div>
      <h3 className="font-medium text-gray-500">Status</h3>
      <p className="capitalize">{order.status}</p>
    </div>
  </div>

  <div>
    <h3 className="font-medium text-gray-500">Shipping address</h3>
    {order.shipping_address?.address1 ? (
      <address className="not-italic">
        {order.shipping_address.name}
        <br />
        {order.shipping_address.address1}
        <br />
        {order.shipping_address.city}, {order.shipping_address.state_code} {order.shipping_address.zip}
        <br />
        {order.shipping_address.country_code}
      </address>
    ) : (
      <p className="text-gray-500">No shipping address provided.</p>
    )}
  </div>

  <div>
    <h3 className="font-medium text-gray-500">Items</h3>
    <table className="w-full text-left">
      <thead>
        <tr className="border-b">
          <th className="py-2">Product</th>
          <th>Variant</th>
          <th>Qty</th>
          <th>Price</th>
          <th>Drawing</th>
        </tr>
      </thead>
      <tbody>
        {order.lines.map((line) => (
          <tr key={line.id} className="border-b">
            <td className="py-2">{line.title}</td>
            <td>{line.variant}</td>
            <td>{line.quantity}</td>
            <td>${line.price}</td>
            <td>
              {line.customer_upload ? (
                <a
                  href={line.customer_upload}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-600 underline"
                >
                  Download
                </a>
              ) : (
                '—'
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>

  <div className="grid grid-cols-2 gap-4">
    <div>
      <h3 className="font-medium text-gray-500">Printful</h3>
      <p>Order ID: {order.printful_order_id || '—'}</p>
      <p>Status: {order.printful_status || '—'}</p>
    </div>
    <div>
      <h3 className="font-medium text-gray-500">Total</h3>
      <p className="text-xl font-semibold">
        {order.total} {order.currency}
      </p>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Commit**

```bash
git add apps/dashboard/src/routes/orders.$id.tsx
git commit -m "feat(dashboard): show order lines, upload link, and shipping address"
```

---

## Task 7: Verify media route serves drawings

**Files:**
- Modify: `docker-compose.yml` (if needed)

- [ ] **Step 1: Confirm media route exists**

Ensure the existing Traefik labels for `/media/` are present in `docker-compose.yml`. They were added in previous work; if missing, add:

```yaml
      - "traefik.http.routers.mugs-media.rule=Host(`backshop.app.moonsbow.com`) && PathPrefix(`/media/`)"
      - "traefik.http.routers.mugs-media.entrypoints=websecure"
      - "traefik.http.routers.mugs-media.tls=true"
      - "traefik.http.routers.mugs-media.tls.certresolver=letsencrypt"
      - "traefik.http.routers.mugs-media.service=mugs-media-service"
      - "traefik.http.services.mugs-media-loadbalancer.server.port=8080"
```

Also ensure the volume mount exists:

```yaml
    volumes:
      - ./media:/app/media
```

- [ ] **Step 2: Commit if changes were made**

```bash
git add docker-compose.yml
git commit -m "fix(dokploy): ensure /media/ route serves uploaded drawings" || echo "No changes to commit"
```

---

## Task 8: End-to-end verification

- [ ] **Step 1: Build and test locally (optional)**

Run the storefront build:

```bash
cd /home/holk/Documents/proyectos/mugs/mugs
pnpm --filter @mugs/web build
```

Expected: build succeeds.

- [ ] **Step 2: Run Python tests for backend**

```bash
cd apps/django
python manage.py test apps.api.payment_tests apps.orders -v 2
```

Expected: existing tests pass.

- [ ] **Step 3: Merge and deploy**

```bash
git push origin master
```

Dokploy will redeploy automatically.

- [ ] **Step 4: Run browser verification**

Use the existing verification script in `.worktrees/webwright_verify/final_runs/run_verify/final_script.py` plus an additional checkout flow test:

1. Add mug to cart.
2. Go to checkout.
3. Fill contact + shipping address.
4. Continue to payment.
5. Confirm Stripe Payment Element appears and no console errors about missing key.
6. Log into dashboard, refresh the page, confirm still logged in.
7. Open the newly created order and confirm shipping address, line items, and drawing download link are visible.

---

## Spec coverage check

| Spec requirement | Implementing task |
|------------------|-------------------|
| Shipping address form in checkout | Task 2, Task 3 |
| Country select limited to Printful countries | Task 1, Task 2 |
| `shipping_address` sent to order API | Task 3 |
| `SITE_URL` setting for upload URLs | Task 4 |
| Persist dashboard access token | Task 5 |
| Restore session on refresh | Task 5 |
| Order detail shows lines, upload, address | Task 6 |
| Media route serves drawings | Task 7 |

No placeholders or unresolved items remain.
