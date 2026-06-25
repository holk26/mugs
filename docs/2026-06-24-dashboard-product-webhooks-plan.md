# Dashboard Product Management + Printful Webhooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add product variant, media, tags and collection editing to the dashboard, plus a page to inspect Printful webhook events.

**Architecture:** Keep the existing TanStack Router + React Query + Zustand stack. Extend the dashboard API layer with typed functions for the already-existing backend endpoints. Build small, focused tab components under the product detail route and a new webhooks route under `/printful`.

**Tech Stack:** React, TypeScript, TanStack Router, TanStack Query, React Hook Form, Zod, Axios, Tailwind CSS, Vitest, React Testing Library.

---

## Files to Create/Modify

### New files
- `apps/dashboard/src/api/variants.ts`
- `apps/dashboard/src/api/media.ts`
- `apps/dashboard/src/api/collections.ts`
- `apps/dashboard/src/api/printful-webhooks.ts`
- `apps/dashboard/src/components/ui/Tabs.tsx`
- `apps/dashboard/src/components/ui/TagsInput.tsx`
- `apps/dashboard/src/components/ui/CollectionSelect.tsx`
- `apps/dashboard/src/components/products/ProductGeneralTab.tsx`
- `apps/dashboard/src/components/products/ProductVariantsTab.tsx`
- `apps/dashboard/src/components/products/ProductMediaTab.tsx`
- `apps/dashboard/src/components/printful/PrintfulWebhookTable.tsx`
- `apps/dashboard/src/components/printful/WebhookPayloadModal.tsx`
- `apps/dashboard/src/routes/printful.webhooks.tsx`

### Modified files
- `apps/dashboard/src/lib/schemas.ts`
- `apps/dashboard/src/api/products.ts`
- `apps/dashboard/src/routes/products.$id.tsx`
- `apps/dashboard/src/components/layout/Sidebar.tsx`
- `apps/dashboard/src/components/products/ProductForm.tsx`
- `apps/dashboard/src/components/printful/PrintfulLogTable.tsx` (move shared formatting if needed)

---

### Task 1: Extend product schema and types

**Files:**
- Modify: `apps/dashboard/src/lib/schemas.ts`

- [ ] **Step 1: Update schema to include tags string and collections**

```typescript
import { z } from 'zod';

export const signInSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'La contraseña es requerida'),
});

export type SignInInput = z.infer<typeof signInSchema>;

export const productSchema = z.object({
  handle: z.string().min(1, 'El handle es requerido'),
  title: z.string().min(1, 'El título es requerido'),
  description: z.string().optional(),
  status: z.enum(['draft', 'active', 'archived']),
  price: z.coerce.number().min(0),
  compare_at_price: z.coerce.number().min(0).optional().nullable(),
  tags: z.array(z.string()).default([]),
  collections: z.array(z.string()).default([]),
});

export type ProductInput = z.infer<typeof productSchema>;
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd apps/dashboard && pnpm tsc --noEmit`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add apps/dashboard/src/lib/schemas.ts
git commit -m "feat(dashboard): extend product schema with tags and collections"
```

---

### Task 1B: Add admin collections endpoint and media file upload (backend)

**Files:**
- Modify: `apps/django/apps/api/admin_serializers.py`
- Modify: `apps/django/apps/api/admin_views.py`
- Modify: `apps/django/apps/api/urls.py`
- Modify: `apps/django/config/settings.py`
- Modify: `apps/django/apps/products/models.py`

- [ ] **Step 1: Add file upload support to ProductMedia model**

Modify `apps/django/apps/products/models.py` to add an optional upload field:

```python
import uuid
from django.db import models


def product_media_upload_path(instance, filename):
    return f'products/{instance.product.id}/media/{filename}'


class ProductMedia(models.Model):
    MEDIA_TYPES = [('image', 'Image'), ('video', 'Video')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name='medias', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=MEDIA_TYPES, default='image')
    file = models.ImageField(upload_to=product_media_upload_path, blank=True, null=True)
    url = models.URLField(blank=True)
    alt = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'product media'

    def __str__(self):
        return self.alt or self.url or str(self.file)

    def save(self, *args, **kwargs):
        if self.file and not self.url:
            self.url = self.file.url
        super().save(*args, **kwargs)
```

- [ ] **Step 2: Create and run migration**

Run:
```bash
cd apps/django
python manage.py makemigrations products
python manage.py migrate
```

Expected: migration `products/0002_productmedia_file.py` created and applied.

- [ ] **Step 3: Configure media storage in settings**

Modify `apps/django/config/settings.py` to ensure these settings exist:

```python
import os

MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))
```

- [ ] **Step 4: Update media serializer to accept file uploads**

Modify `apps/django/apps/api/admin_serializers.py`:

```python
class AdminProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ['id', 'type', 'file', 'url', 'alt', 'order']
        extra_kwargs = {
            'url': {'required': False, 'allow_blank': True},
        }
```

- [ ] **Step 5: Add admin collection serializer and viewset**

Modify `apps/django/apps/api/admin_serializers.py` to add:

```python
class AdminCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'handle', 'title', 'description', 'created_at', 'updated_at']
```

Modify `apps/django/apps/api/admin_views.py` to add:

```python
class AdminCollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all().order_by('-created_at')
    serializer_class = AdminCollectionSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'handle']
    ordering_fields = ['created_at', 'title']
    lookup_field = 'id'
```

- [ ] **Step 6: Register admin collection URL**

Modify `apps/django/apps/api/urls.py` to register the new viewset in `admin_router`:

```python
admin_router.register(r'collections', AdminCollectionViewSet, basename='admin-collection')
```

Import `AdminCollectionViewSet` from `admin_views`.

- [ ] **Step 7: Serve media files in development**

If not already present, add to `apps/django/config/urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # existing patterns
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 8: Run Django backend tests**

Run: `cd apps/django && python manage.py test apps.api`
Expected: tests pass

- [ ] **Step 9: Commit**

```bash
git add apps/django/apps/products/models.py apps/django/apps/products/migrations/ apps/django/apps/api/admin_serializers.py apps/django/apps/api/admin_views.py apps/django/apps/api/urls.py apps/django/config/settings.py apps/django/config/urls.py
git commit -m "feat(api): support media file uploads and admin collections endpoint"
```

---

### Task 1C: Configure Dokploy to serve uploaded media files

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add media volume to Django service**

Modify `docker-compose.yml` under the `django` service:

```yaml
    volumes:
      - ./media:/app/media
```

And expose `MEDIA_ROOT` env var:

```yaml
    environment:
      - MEDIA_ROOT=/app/media
```

- [ ] **Step 2: Add media URL to Traefik labels**

Add a new router for `/media/` in the `django` service labels:

```yaml
      - "traefik.http.routers.mugs-media.rule=Host(`backshop.app.moonsbow.com`) && PathPrefix(`/media/`)"
      - "traefik.http.routers.mugs-media.entrypoints=websecure"
      - "traefik.http.routers.mugs-media.tls=true"
      - "traefik.http.routers.mugs-media.tls.certresolver=letsencrypt"
      - "traefik.http.services.mugs-media.loadbalancer.server.port=8080"
```

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "dokploy: configure media volume and traefik route for uploads"
```

---

### Task 2: Add API functions for variants, media, collections and webhooks

**Files:**
- Modify: `apps/django/apps/api/admin_views.py`
- Modify: `apps/django/apps/api/admin_serializers.py`
- Modify: `apps/django/apps/api/urls.py`

- [ ] **Step 1: Add admin collection serializer**

Modify `apps/django/apps/api/admin_serializers.py` to add:

```python
class AdminCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'handle', 'title', 'description', 'created_at', 'updated_at']
```

- [ ] **Step 2: Add admin collection viewset**

Modify `apps/django/apps/api/admin_views.py` to add:

```python
class AdminCollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all().order_by('-created_at')
    serializer_class = AdminCollectionSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'handle']
    ordering_fields = ['created_at', 'title']
    lookup_field = 'id'
```

- [ ] **Step 3: Register admin collection URL**

Modify `apps/django/apps/api/urls.py` to register the new viewset in `admin_router`:

```python
admin_router.register(r'collections', AdminCollectionViewSet, basename='admin-collection')
```

Import `AdminCollectionViewSet` from `admin_views`.

- [ ] **Step 4: Run Django backend tests**

Run: `cd apps/django && python manage.py test apps.api`
Expected: tests pass

- [ ] **Step 5: Commit**

```bash
git add apps/django/apps/api/admin_serializers.py apps/django/apps/api/admin_views.py apps/django/apps/api/urls.py
git commit -m "feat(api): add admin collections endpoint"
```

---

### Task 2: Add API functions for variants, media, collections and webhooks

**Files:**
- Create: `apps/dashboard/src/api/variants.ts`
- Create: `apps/dashboard/src/api/media.ts`
- Create: `apps/dashboard/src/api/collections.ts`
- Create: `apps/dashboard/src/api/printful-webhooks.ts`
- Modify: `apps/dashboard/src/api/products.ts`

- [ ] **Step 1: Create variants API**

Create `apps/dashboard/src/api/variants.ts`:

```typescript
import apiClient from './client';
import type { PaginatedResponse } from './products';

export interface ProductVariant {
  id: string;
  title: string;
  sku: string;
  price: number;
  compare_at_price: number | null;
  stock: number;
  options: Record<string, unknown>;
  active: boolean;
  printful_sync_variant_id: number;
  printful_variant_id: number;
  created_at: string;
  updated_at: string;
}

export interface VariantInput {
  title: string;
  sku: string;
  price: number;
  compare_at_price?: number | null;
  stock: number;
  active: boolean;
}

export async function listVariants(productId: string): Promise<PaginatedResponse<ProductVariant>> {
  const response = await apiClient.get<PaginatedResponse<ProductVariant>>(`/api/v1/admin/products/${productId}/variants/`);
  return response.data;
}

export async function updateVariant(productId: string, variantId: string, data: VariantInput) {
  const response = await apiClient.patch(`/api/v1/admin/products/${productId}/variants/${variantId}/`, data);
  return response.data;
}
```

- [ ] **Step 2: Create media API**

Create `apps/dashboard/src/api/media.ts`:

```typescript
import apiClient from './client';
import type { PaginatedResponse } from './products';

export interface ProductMedia {
  id: string;
  type: 'image' | 'video';
  url: string;
  alt: string;
  order: number;
}

export interface MediaInput {
  file: File;
  alt?: string;
  order?: number;
}

export async function listMedia(productId: string): Promise<PaginatedResponse<ProductMedia>> {
  const response = await apiClient.get<PaginatedResponse<ProductMedia>>(`/api/v1/admin/products/${productId}/media/`);
  return response.data;
}

export async function uploadMedia(productId: string, data: MediaInput) {
  const formData = new FormData();
  formData.append('file', data.file);
  if (data.alt) formData.append('alt', data.alt);
  if (data.order !== undefined) formData.append('order', String(data.order));
  const response = await apiClient.post(`/api/v1/admin/products/${productId}/media/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function updateMedia(productId: string, mediaId: string, data: { alt?: string; order?: number }) {
  const response = await apiClient.patch(`/api/v1/admin/products/${productId}/media/${mediaId}/`, data);
  return response.data;
}

export async function deleteMedia(productId: string, mediaId: string) {
  await apiClient.delete(`/api/v1/admin/products/${productId}/media/${mediaId}/`);
}
```

- [ ] **Step 3: Create collections API**

Create `apps/dashboard/src/api/collections.ts`:

```typescript
import apiClient from './client';
import type { PaginatedResponse } from './products';

export interface Collection {
  id: string;
  handle: string;
  title: string;
}

export async function listCollections(): Promise<PaginatedResponse<Collection>> {
  const response = await apiClient.get<PaginatedResponse<Collection>>('/api/v1/admin/collections/');
  return response.data;
}

// Requires backend AdminCollectionViewSet (see Task 1B below).
```

- [ ] **Step 4: Create Printful webhooks API**

Create `apps/dashboard/src/api/printful-webhooks.ts`:

```typescript
import apiClient from './client';
import type { PaginatedResponse } from './products';

export interface PrintfulWebhookEvent {
  id: string;
  event_type: string;
  payload: Record<string, unknown>;
  processed: boolean;
  created_at: string;
}

export async function listPrintfulWebhookEvents(): Promise<PaginatedResponse<PrintfulWebhookEvent>> {
  const response = await apiClient.get<PaginatedResponse<PrintfulWebhookEvent>>('/api/v1/admin/printful/webhooks/');
  return response.data;
}
```

- [ ] **Step 5: Update products API to include full product type**

Modify `apps/dashboard/src/api/products.ts`:

```typescript
import apiClient from './client';
import type { ProductInput } from '@/lib/schemas';

export interface Product {
  id: string;
  handle: string;
  title: string;
  price: number;
  status: 'draft' | 'active' | 'archived';
  created_at: string;
}

export interface ProductDetail extends Product {
  description: string;
  compare_at_price: number | null;
  tags: string[];
  collections: string[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function listProducts(params?: Record<string, unknown>): Promise<PaginatedResponse<Product>> {
  const response = await apiClient.get<PaginatedResponse<Product>>('/api/v1/admin/products/', { params });
  return response.data;
}

export async function getProduct(id: string): Promise<ProductDetail> {
  const response = await apiClient.get<ProductDetail>(`/api/v1/admin/products/${id}/`);
  return response.data;
}

export async function createProduct(data: ProductInput) {
  const response = await apiClient.post('/api/v1/admin/products/', data);
  return response.data;
}

export async function updateProduct(id: string, data: ProductInput) {
  const response = await apiClient.patch(`/api/v1/admin/products/${id}/`, data);
  return response.data;
}

export async function deleteProduct(id: string) {
  await apiClient.delete(`/api/v1/admin/products/${id}/`);
}
```

- [ ] **Step 6: Verify TypeScript compiles**

Run: `cd apps/dashboard && pnpm tsc --noEmit`
Expected: no errors

- [ ] **Step 7: Commit**

```bash
git add apps/dashboard/src/api/variants.ts apps/dashboard/src/api/media.ts apps/dashboard/src/api/collections.ts apps/dashboard/src/api/printful-webhooks.ts apps/dashboard/src/api/products.ts
git commit -m "feat(dashboard): add API functions for variants, media, collections and webhooks"
```

---

### Task 3: Build reusable UI components (Tabs, TagsInput, CollectionSelect)

**Files:**
- Create: `apps/dashboard/src/components/ui/Tabs.tsx`
- Create: `apps/dashboard/src/components/ui/TagsInput.tsx`
- Create: `apps/dashboard/src/components/ui/CollectionSelect.tsx`

- [ ] **Step 1: Create Tabs component**

Create `apps/dashboard/src/components/ui/Tabs.tsx`:

```typescript
import { createContext, useContext, useState, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface TabsContextValue {
  value: string;
  setValue: (value: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabs() {
  const context = useContext(TabsContext);
  if (!context) throw new Error('Tabs components must be used inside <Tabs>');
  return context;
}

interface TabsProps {
  defaultValue: string;
  children: ReactNode;
  className?: string;
}

export function Tabs({ defaultValue, children, className }: TabsProps) {
  const [value, setValue] = useState(defaultValue);
  return (
    <TabsContext.Provider value={{ value, setValue }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('flex border-b border-stone-200', className)}>{children}</div>;
}

interface TabsTriggerProps {
  value: string;
  children: ReactNode;
}

export function TabsTrigger({ value, children }: TabsTriggerProps) {
  const { value: selected, setValue } = useTabs();
  const isActive = selected === value;
  return (
    <button
      type="button"
      onClick={() => setValue(value)}
      className={cn(
        'px-4 py-2 text-sm font-medium',
        isActive ? 'border-b-2 border-primary-600 text-primary-700' : 'text-stone-500 hover:text-stone-700'
      )}
    >
      {children}
    </button>
  );
}

interface TabsContentProps {
  value: string;
  children: ReactNode;
}

export function TabsContent({ value, children }: TabsContentProps) {
  const { value: selected } = useTabs();
  if (selected !== value) return null;
  return <div className="py-4">{children}</div>;
}
```

- [ ] **Step 2: Create TagsInput component**

Create `apps/dashboard/src/components/ui/TagsInput.tsx`:

```typescript
import { useState } from 'react';
import { Input } from './Input';

interface TagsInputProps {
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
}

export function TagsInput({ value, onChange, placeholder }: TagsInputProps) {
  const [inputValue, setInputValue] = useState(value.join(', '));

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    const tags = e.target.value
      .split(',')
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0);
    onChange(tags);
  };

  return (
    <Input
      value={inputValue}
      onChange={handleChange}
      placeholder={placeholder || 'tag1, tag2, tag3'}
    />
  );
}
```

- [ ] **Step 3: Create CollectionSelect component**

Create `apps/dashboard/src/components/ui/CollectionSelect.tsx`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { listCollections } from '@/api/collections';

interface CollectionSelectProps {
  value: string[];
  onChange: (value: string[]) => void;
}

export function CollectionSelect({ value, onChange }: CollectionSelectProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['collections'],
    queryFn: listCollections,
  });

  if (isLoading) return <p className="text-sm text-stone-500">Cargando colecciones...</p>;

  return (
    <select
      multiple
      value={value}
      onChange={(e) => {
        const options = Array.from(e.target.selectedOptions).map((opt) => opt.value);
        onChange(options);
      }}
      className="input min-h-[120px]"
    >
      {data?.results.map((collection) => (
        <option key={collection.id} value={collection.id}>
          {collection.title}
        </option>
      ))}
    </select>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/dashboard/src/components/ui/Tabs.tsx apps/dashboard/src/components/ui/TagsInput.tsx apps/dashboard/src/components/ui/CollectionSelect.tsx
git commit -m "feat(dashboard): add Tabs, TagsInput and CollectionSelect components"
```

---

### Task 4: Build ProductGeneralTab

**Files:**
- Create: `apps/dashboard/src/components/products/ProductGeneralTab.tsx`
- Modify: `apps/dashboard/src/components/products/ProductForm.tsx`

- [ ] **Step 1: Add tags and collections fields to ProductForm**

Modify `apps/dashboard/src/components/products/ProductForm.tsx`:

```typescript
import { useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { TagsInput } from '@/components/ui/TagsInput';
import { CollectionSelect } from '@/components/ui/CollectionSelect';
import { productSchema, type ProductInput } from '@/lib/schemas';

interface ProductFormProps {
  defaultValues?: Partial<ProductInput>;
  onSubmit: (data: ProductInput) => void;
  isLoading?: boolean;
}

export function ProductForm({ defaultValues, onSubmit, isLoading }: ProductFormProps) {
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<ProductInput>({
    resolver: zodResolver(productSchema) as Resolver<ProductInput>,
    defaultValues: {
      status: 'draft',
      tags: [],
      collections: [],
      ...defaultValues,
    },
  });

  const tags = watch('tags') || [];
  const collections = watch('collections') || [];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-2xl space-y-6">
      <div>
        <label className="label">Título</label>
        <Input {...register('title')} />
        {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>}
      </div>
      <div>
        <label className="label">Handle</label>
        <Input {...register('handle')} />
        {errors.handle && <p className="mt-1 text-sm text-red-600">{errors.handle.message}</p>}
      </div>
      <div>
        <label className="label">Descripción</label>
        <textarea {...register('description')} className="input min-h-[120px]" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Precio</label>
          <Input {...register('price')} type="number" step="0.01" />
        </div>
        <div>
          <label className="label">Precio comparación</label>
          <Input {...register('compare_at_price')} type="number" step="0.01" />
        </div>
      </div>
      <div>
        <label className="label">Estado</label>
        <select {...register('status')} className="input">
          <option value="draft">Borrador</option>
          <option value="active">Activo</option>
          <option value="archived">Archivado</option>
        </select>
      </div>
      <div>
        <label className="label">Tags</label>
        <TagsInput value={tags} onChange={(v) => setValue('tags', v)} />
      </div>
      <div>
        <label className="label">Colecciones</label>
        <CollectionSelect value={collections} onChange={(v) => setValue('collections', v)} />
      </div>
      <div className="flex gap-4">
        <Button type="submit" disabled={isLoading}>{isLoading ? 'Guardando...' : 'Guardar'}</Button>
      </div>
    </form>
  );
}
```

- [ ] **Step 2: Create ProductGeneralTab wrapper**

Create `apps/dashboard/src/components/products/ProductGeneralTab.tsx`:

```typescript
import { ProductForm } from './ProductForm';
import type { ProductInput } from '@/lib/schemas';
import type { ProductDetail } from '@/api/products';

interface ProductGeneralTabProps {
  product: ProductDetail;
  onSubmit: (data: ProductInput) => void;
  isLoading?: boolean;
}

export function ProductGeneralTab({ product, onSubmit, isLoading }: ProductGeneralTabProps) {
  return (
    <ProductForm
      defaultValues={{
        ...product,
        tags: Array.isArray(product.tags) ? product.tags : [],
        collections: product.collections || [],
      }}
      onSubmit={onSubmit}
      isLoading={isLoading}
    />
  );
}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd apps/dashboard && pnpm tsc --noEmit`
Expected: no errors

- [ ] **Step 4: Commit**

```bash
git add apps/dashboard/src/components/products/ProductForm.tsx apps/dashboard/src/components/products/ProductGeneralTab.tsx
git commit -m "feat(dashboard): add tags, collections and general product tab"
```

---

### Task 5: Build ProductVariantsTab

**Files:**
- Create: `apps/dashboard/src/components/products/ProductVariantsTab.tsx`

- [ ] **Step 1: Create inline editable variants table**

Create `apps/dashboard/src/components/products/ProductVariantsTab.tsx`:

```typescript
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listVariants, updateVariant, type ProductVariant, type VariantInput } from '@/api/variants';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { DataTable } from '@/components/ui/DataTable';

interface ProductVariantsTabProps {
  productId: string;
}

export function ProductVariantsTab({ productId }: ProductVariantsTabProps) {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ['product-variants', productId],
    queryFn: () => listVariants(productId),
  });

  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<VariantInput | null>(null);

  const mutation = useMutation({
    mutationFn: ({ variantId, data }: { variantId: string; data: VariantInput }) =>
      updateVariant(productId, variantId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product-variants', productId] });
      setEditingId(null);
      setDraft(null);
    },
  });

  const startEdit = (variant: ProductVariant) => {
    setEditingId(variant.id);
    setDraft({
      title: variant.title,
      sku: variant.sku,
      price: Number(variant.price),
      compare_at_price: variant.compare_at_price ? Number(variant.compare_at_price) : null,
      stock: variant.stock,
      active: variant.active,
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setDraft(null);
  };

  const saveEdit = (variantId: string) => {
    if (!draft) return;
    mutation.mutate({ variantId, data: draft });
  };

  const variants = data?.results || [];

  return (
    <div className="space-y-4">
      <DataTable
        data={variants}
        keyExtractor={(row) => row.id}
        isLoading={isLoading}
        columns={[
          {
            key: 'title',
            header: 'Título',
            render: (row) =>
              editingId === row.id ? (
                <Input
                  value={draft?.title || ''}
                  onChange={(e) => setDraft((d) => (d ? { ...d, title: e.target.value } : d))}
                />
              ) : (
                row.title
              ),
          },
          {
            key: 'sku',
            header: 'SKU',
            render: (row) =>
              editingId === row.id ? (
                <Input
                  value={draft?.sku || ''}
                  onChange={(e) => setDraft((d) => (d ? { ...d, sku: e.target.value } : d))}
                />
              ) : (
                row.sku
              ),
          },
          {
            key: 'price',
            header: 'Precio',
            render: (row) =>
              editingId === row.id ? (
                <Input
                  type="number"
                  step="0.01"
                  value={draft?.price ?? ''}
                  onChange={(e) => setDraft((d) => (d ? { ...d, price: Number(e.target.value) } : d))}
                />
              ) : (
                `$${row.price}`
              ),
          },
          {
            key: 'stock',
            header: 'Stock',
            render: (row) =>
              editingId === row.id ? (
                <Input
                  type="number"
                  value={draft?.stock ?? ''}
                  onChange={(e) => setDraft((d) => (d ? { ...d, stock: Number(e.target.value) } : d))}
                />
              ) : (
                row.stock
              ),
          },
          {
            key: 'active',
            header: 'Activo',
            render: (row) =>
              editingId === row.id ? (
                <input
                  type="checkbox"
                  checked={draft?.active || false}
                  onChange={(e) => setDraft((d) => (d ? { ...d, active: e.target.checked } : d))}
                />
              ) : (
                row.active ? 'Sí' : 'No'
              ),
          },
          {
            key: 'actions',
            header: 'Acciones',
            render: (row) =>
              editingId === row.id ? (
                <div className="flex gap-2">
                  <Button onClick={() => saveEdit(row.id)} disabled={mutation.isPending}>
                    {mutation.isPending ? 'Guardando...' : 'Guardar'}
                  </Button>
                  <Button variant="secondary" onClick={cancelEdit}>
                    Cancelar
                  </Button>
                </div>
              ) : (
                <Button variant="secondary" onClick={() => startEdit(row)}>
                  Editar
                </Button>
              ),
          },
        ]}
      />
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd apps/dashboard && pnpm tsc --noEmit`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add apps/dashboard/src/components/products/ProductVariantsTab.tsx
git commit -m "feat(dashboard): add inline variant editing tab"
```

---

### Task 6: Build ProductMediaTab

**Files:**
- Create: `apps/dashboard/src/components/products/ProductMediaTab.tsx`

- [ ] **Step 1: Create media grid and upload**

Create `apps/dashboard/src/components/products/ProductMediaTab.tsx`:

```typescript
import { useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listMedia, uploadMedia, deleteMedia, type ProductMedia } from '@/api/media';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface ProductMediaTabProps {
  productId: string;
}

export function ProductMediaTab({ productId }: ProductMediaTabProps) {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [alt, setAlt] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['product-media', productId],
    queryFn: () => listMedia(productId),
  });

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error('No file selected');
      return uploadMedia(productId, { file, alt });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product-media', productId] });
      setFile(null);
      setAlt('');
      if (fileRef.current) fileRef.current.value = '';
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (mediaId: string) => deleteMedia(productId, mediaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product-media', productId] });
    },
  });

  const media = data?.results || [];

  return (
    <div className="space-y-6">
      <div className="flex items-end gap-4 rounded-lg border border-stone-200 bg-white p-4">
        <div className="flex-1">
          <label className="label">Nueva imagen</label>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>
        <div className="flex-1">
          <label className="label">Texto alternativo</label>
          <Input value={alt} onChange={(e) => setAlt(e.target.value)} placeholder="Descripción de la imagen" />
        </div>
        <Button onClick={() => uploadMutation.mutate()} disabled={!file || uploadMutation.isPending}>
          {uploadMutation.isPending ? 'Subiendo...' : 'Subir'}
        </Button>
      </div>

      {isLoading ? (
        <p>Cargando...</p>
      ) : media.length === 0 ? (
        <p className="text-stone-500">No hay medios para este producto.</p>
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {media.map((item) => (
            <MediaCard key={item.id} item={item} onDelete={() => deleteMutation.mutate(item.id)} isDeleting={deleteMutation.isPending} />
          ))}
        </div>
      )}
    </div>
  );
}

function MediaCard({ item, onDelete, isDeleting }: { item: ProductMedia; onDelete: () => void; isDeleting: boolean }) {
  return (
    <div className="overflow-hidden rounded-lg border border-stone-200 bg-white">
      <img src={item.url} alt={item.alt} className="h-40 w-full object-cover" />
      <div className="p-3">
        <p className="truncate text-xs text-stone-500">{item.alt || 'Sin descripción'}</p>
        <Button variant="danger" onClick={onDelete} disabled={isDeleting} className="mt-2 w-full">
          {isDeleting ? 'Eliminando...' : 'Eliminar'}
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd apps/dashboard && pnpm tsc --noEmit`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add apps/dashboard/src/components/products/ProductMediaTab.tsx
git commit -m "feat(dashboard): add product media upload and delete tab"
```

---

### Task 7: Update product detail page with tabs

**Files:**
- Modify: `apps/dashboard/src/routes/products.$id.tsx`

- [ ] **Step 1: Replace single form with tabbed layout**

Modify `apps/dashboard/src/routes/products.$id.tsx`:

```typescript
import { createFileRoute } from '@tanstack/react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getProduct, updateProduct, type ProductDetail } from '@/api/products';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { ProductGeneralTab } from '@/components/products/ProductGeneralTab';
import { ProductVariantsTab } from '@/components/products/ProductVariantsTab';
import { ProductMediaTab } from '@/components/products/ProductMediaTab';
import type { ProductInput } from '@/lib/schemas';

export const Route = createFileRoute('/products/$id')({
  component: EditProductPage,
});

function EditProductPage() {
  const { id } = Route.useParams();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['product', id],
    queryFn: () => getProduct(id),
  });

  const mutation = useMutation({
    mutationFn: (values: ProductInput) => updateProduct(id, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['product', id] });
    },
  });

  if (isLoading) return <p>Cargando...</p>;

  const product = data as ProductDetail;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-900">Editar producto</h1>
      <Tabs defaultValue="general">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="variants">Variantes</TabsTrigger>
          <TabsTrigger value="media">Medios</TabsTrigger>
        </TabsList>
        <TabsContent value="general">
          <ProductGeneralTab product={product} onSubmit={(values) => mutation.mutate(values)} isLoading={mutation.isPending} />
        </TabsContent>
        <TabsContent value="variants">
          <ProductVariantsTab productId={id} />
        </TabsContent>
        <TabsContent value="media">
          <ProductMediaTab productId={id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd apps/dashboard && pnpm tsc --noEmit`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add apps/dashboard/src/routes/products.$id.tsx
git commit -m "feat(dashboard): add tabs to product detail page"
```

---

### Task 8: Build Printful webhooks page

**Files:**
- Create: `apps/dashboard/src/components/printful/PrintfulWebhookTable.tsx`
- Create: `apps/dashboard/src/components/printful/WebhookPayloadModal.tsx`
- Create: `apps/dashboard/src/routes/printful.webhooks.tsx`
- Modify: `apps/dashboard/src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Create webhook payload modal**

Create `apps/dashboard/src/components/printful/WebhookPayloadModal.tsx`:

```typescript
import { Button } from '@/components/ui/Button';

interface WebhookPayloadModalProps {
  payload: Record<string, unknown>;
  onClose: () => void;
}

export function WebhookPayloadModal({ payload, onClose }: WebhookPayloadModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[80vh] w-full max-w-2xl overflow-auto rounded-xl bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Payload del webhook</h3>
          <Button variant="secondary" onClick={onClose}>Cerrar</Button>
        </div>
        <pre className="overflow-auto rounded-lg bg-stone-100 p-4 text-xs">
          {JSON.stringify(payload, null, 2)}
        </pre>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create webhook events table**

Create `apps/dashboard/src/components/printful/PrintfulWebhookTable.tsx`:

```typescript
import { useState } from 'react';
import { DataTable } from '@/components/ui/DataTable';
import { Button } from '@/components/ui/Button';
import { WebhookPayloadModal } from './WebhookPayloadModal';
import type { PrintfulWebhookEvent } from '@/api/printful-webhooks';

interface PrintfulWebhookTableProps {
  events: PrintfulWebhookEvent[];
  isLoading?: boolean;
}

export function PrintfulWebhookTable({ events, isLoading }: PrintfulWebhookTableProps) {
  const [selected, setSelected] = useState<PrintfulWebhookEvent | null>(null);

  return (
    <>
      <DataTable
        data={events}
        keyExtractor={(row) => row.id}
        isLoading={isLoading}
        columns={[
          { key: 'event_type', header: 'Evento' },
          {
            key: 'processed',
            header: 'Procesado',
            render: (row) => (row.processed ? 'Sí' : 'No'),
          },
          {
            key: 'created_at',
            header: 'Recibido',
            render: (row) => new Date(row.created_at).toLocaleString(),
          },
          {
            key: 'actions',
            header: 'Acciones',
            render: (row) => (
              <Button variant="secondary" onClick={() => setSelected(row)}>
                Ver payload
              </Button>
            ),
          },
        ]}
      />
      {selected && <WebhookPayloadModal payload={selected.payload} onClose={() => setSelected(null)} />}
    </>
  );
}
```

- [ ] **Step 3: Create webhooks route**

Create `apps/dashboard/src/routes/printful.webhooks.tsx`:

```typescript
import { createFileRoute } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { listPrintfulWebhookEvents } from '@/api/printful-webhooks';
import { PrintfulWebhookTable } from '@/components/printful/PrintfulWebhookTable';

export const Route = createFileRoute('/printful/webhooks')({
  component: PrintfulWebhooksPage,
});

function PrintfulWebhooksPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['printful-webhooks'],
    queryFn: listPrintfulWebhookEvents,
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-900">Webhooks de Printful</h1>
      <PrintfulWebhookTable events={data?.results || []} isLoading={isLoading} />
    </div>
  );
}
```

- [ ] **Step 4: Update sidebar with webhooks link**

Modify `apps/dashboard/src/components/layout/Sidebar.tsx` to group Printful navigation. Replace the nav array with nested structure or add a second link:

```typescript
import { Link } from '@tanstack/react-router';
import { Package, ShoppingCart, RefreshCw, Home, Radio } from 'lucide-react';

const nav = [
  { to: '/', label: 'Inicio', icon: Home },
  { to: '/products', label: 'Productos', icon: Package },
  { to: '/orders', label: 'Órdenes', icon: ShoppingCart },
  { to: '/printful', label: 'Printful Sync', icon: RefreshCw },
  { to: '/printful/webhooks', label: 'Printful Webhooks', icon: Radio },
];

export function Sidebar() {
  return (
    <aside className="flex w-64 flex-col border-r border-stone-200 bg-white">
      <div className="flex h-16 items-center border-b border-stone-200 px-6">
        <span className="text-lg font-bold text-primary-700">Recuerdo Momentos</span>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {nav.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-stone-600 hover:bg-stone-50 hover:text-primary-700"
            activeProps={{ className: 'bg-primary-50 text-primary-700' }}
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
```

- [ ] **Step 5: Regenerate TanStack route tree**

Run: `cd apps/dashboard && pnpm route:generate`
Expected: `src/routeTree.gen.ts` is updated to include the new `/printful/webhooks` route.

- [ ] **Step 6: Verify TypeScript compiles**

Run: `cd apps/dashboard && pnpm tsc --noEmit`
Expected: no errors

- [ ] **Step 7: Commit**

```bash
git add apps/dashboard/src/components/printful/WebhookPayloadModal.tsx apps/dashboard/src/components/printful/PrintfulWebhookTable.tsx apps/dashboard/src/routes/printful.webhooks.tsx apps/dashboard/src/components/layout/Sidebar.tsx apps/dashboard/src/routeTree.gen.ts
git commit -m "feat(dashboard): add Printful webhook events page"
```

---

### Task 9: Add tests

**Files:**
- Create: `apps/dashboard/src/components/ui/TagsInput.test.tsx`
- Create: `apps/dashboard/src/components/products/ProductVariantsTab.test.tsx`
- Create: `apps/dashboard/src/components/printful/PrintfulWebhookTable.test.tsx`

- [ ] **Step 1: Test TagsInput**

Create `apps/dashboard/src/components/ui/TagsInput.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TagsInput } from './TagsInput';

describe('TagsInput', () => {
  it('renders comma separated tags', () => {
    render(<TagsInput value={['printful', 'mug']} onChange={vi.fn()} />);
    expect(screen.getByDisplayValue('printful, mug')).toBeInTheDocument();
  });

  it('calls onChange with parsed tags', () => {
    const onChange = vi.fn();
    render(<TagsInput value={[]} onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'a, b, c' } });
    expect(onChange).toHaveBeenCalledWith(['a', 'b', 'c']);
  });
});
```

- [ ] **Step 2: Test ProductVariantsTab rendering**

Create `apps/dashboard/src/components/products/ProductVariantsTab.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProductVariantsTab } from './ProductVariantsTab';

const queryClient = new QueryClient();

describe('ProductVariantsTab', () => {
  it('renders loading state', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ProductVariantsTab productId="test-product" />
      </QueryClientProvider>
    );
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Test PrintfulWebhookTable**

Create `apps/dashboard/src/components/printful/PrintfulWebhookTable.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PrintfulWebhookTable } from './PrintfulWebhookTable';

const events = [
  {
    id: '1',
    event_type: 'product_updated',
    payload: { id: 123 },
    processed: false,
    created_at: '2026-06-24T00:00:00Z',
  },
];

describe('PrintfulWebhookTable', () => {
  it('renders event and opens modal', () => {
    render(<PrintfulWebhookTable events={events} />);
    expect(screen.getByText('product_updated')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Ver payload'));
    expect(screen.getByText('"id": 123')).toBeInTheDocument();
  });
});
```

- [ ] **Step 4: Run tests**

Run: `cd apps/dashboard && pnpm test`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/src/components/ui/TagsInput.test.tsx apps/dashboard/src/components/products/ProductVariantsTab.test.tsx apps/dashboard/src/components/printful/PrintfulWebhookTable.test.tsx
git commit -m "test(dashboard): add tests for tags, variants and webhooks"
```

---

### Task 10: Final integration and deployment

- [ ] **Step 1: Run full dashboard build**

Run: `cd apps/dashboard && pnpm build`
Expected: build succeeds

- [ ] **Step 2: Push to origin**

```bash
git push origin master
```

- [ ] **Step 3: Verify deployment**

Wait for Dokploy deployment to complete, then verify:
- `/products/$id` shows tabs General / Variantes / Medios
- Variants can be edited inline
- Media can be uploaded and deleted
- `/printful/webhooks` shows webhook events

---

## Self-Review Checklist

1. **Spec coverage:**
   - Product tabs (General/Variants/Media): Tasks 4, 5, 6, 7 ✓
   - Tags and collections editing: Task 4 ✓
   - Printful webhook page: Task 8 ✓
   - Tests: Task 9 ✓

2. **Placeholder scan:**
   - No TBD/TODO/fill-in-details found.
   - Each task includes concrete file paths and code.

3. **Type consistency:**
   - `ProductDetail` extends `Product` in `products.ts`.
   - `ProductInput` includes `tags: string` and `collections: string[]`.
   - API functions return typed `PaginatedResponse<T>`.
