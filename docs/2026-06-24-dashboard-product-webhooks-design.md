# Dashboard: Product Management + Printful Webhooks

## Overview

Add richer product editing capabilities and Printful webhook visibility to the existing admin dashboard (`dashboar-back.app.moonsbow.com`).

## Goals

- Let admins manage a product's variants, media, tags, and collections from a single page.
- Provide visibility into Printful webhook events received by the backend.

## Non-Goals

- Do not build a full collection CRUD UI (only assign existing collections to a product).
- Do not add manual webhook replay/retry actions.
- Do not create product variants from scratch in the dashboard (only edit existing ones synced from Printful).

## Existing Backend Support

The backend already exposes the required endpoints under `/api/v1/admin/`:

- `GET /admin/products/{id}/` — product detail with `medias`, `variants`, `collections`
- `PATCH /admin/products/{id}/` — update product fields, tags, collections
- `GET/POST/PATCH/DELETE /admin/products/{product_id}/variants/` — variant CRUD
- `GET/POST/PATCH/DELETE /admin/products/{product_id}/media/` — media CRUD
- `GET /admin/printful/webhooks/` — paginated webhook events

No backend changes are required for this design.

## Design

### 1. Product Detail Page (`/products/$id`)

Replace the single-form layout with a tabbed interface.

#### Tabs

1. **General**
   - Existing fields: title, handle, description, status, price, compare_at_price
   - New: tags input (comma-separated string, converted to/from `tags` array)
   - New: collections multi-select (existing `Collection` IDs)

2. **Variants**
   - Table of product variants loaded from `/admin/products/{id}/variants/`
   - Inline editing for: title, sku, price, compare_at_price, stock, active
   - Each row has "Save" and "Cancel" buttons during edit
   - Read-only fields: printful_sync_variant_id, printful_variant_id

3. **Media**
   - Grid of existing media items with preview thumbnail
   - Each item shows: url, alt text input, order input, delete button
   - "Upload new" button opens file picker; uses `POST /admin/products/{id}/media/` with `multipart/form-data`

### 2. Printful Webhooks Page (`/printful/webhooks`)

New route under the Printful section.

- Table listing events from `/admin/printful/webhooks/`
- Columns: event type, processed status, received date
- Row action "View payload" opens a modal showing the JSON payload

### 3. New/Reusable Components

- `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`
- `ProductGeneralTab`
- `ProductVariantsTab`
- `ProductMediaTab`
- `TagsInput`
- `CollectionSelect`
- `WebhookEventPayloadModal`

### 4. State & Data Flow

- TanStack Query fetches product detail with `medias` and `variants` prefetched.
- Each tab manages its own mutations and invalidates relevant query keys.
- Media upload uses `FormData` with `axios.post(..., { headers: { 'Content-Type': 'multipart/form-data' } })`.

### 5. Error Handling

- API errors displayed as toast notifications.
- Inline field errors for variant editing.
- Loading skeletons while tab data is fetched.

### 6. Testing

- Unit tests for `TagsInput` parsing/formatting.
- Unit tests for `ProductVariantsTab` save/cancel flow.
- Unit tests for `ProductMediaTab` upload/delete flow.
- Route test for `/printful/webhooks` rendering events.

## Success Criteria

- Admin can edit tags and collections on the General tab and see changes persisted.
- Admin can update variant price/stock/SKU/active inline and the product page reflects changes.
- Admin can upload and delete product media.
- Admin can view Printful webhook events and inspect payloads.
