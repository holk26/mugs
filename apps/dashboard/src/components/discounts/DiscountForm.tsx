import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { TagsInput } from '@/components/ui/TagsInput';
import type { DiscountCode, DiscountCodeInput, DiscountType, AppliesTo } from '@/api/discounts';

interface DiscountFormProps {
  initial?: DiscountCode;
  onSubmit: (data: DiscountCodeInput) => void;
  isLoading?: boolean;
}

const emptyState: DiscountCodeInput = {
  code: '',
  description: '',
  discount_type: 'percentage',
  value: '',
  currency: 'USD',
  min_order_amount: null,
  max_discount_amount: null,
  usage_limit_total: null,
  usage_limit_per_user: null,
  starts_at: null,
  expires_at: null,
  applies_to: 'all',
  product_ids: [],
  collection_ids: [],
  is_active: true,
};

function toDatetimeLocal(iso: string | null): string {
  if (!iso) return '';
  const date = new Date(iso);
  if (isNaN(date.getTime())) return '';
  const offset = date.getTimezoneOffset() * 60000;
  const local = new Date(date.getTime() - offset);
  return local.toISOString().slice(0, 16);
}

function fromDatetimeLocal(value: string): string | null {
  if (!value) return null;
  return new Date(value).toISOString();
}

export function DiscountForm({ initial, onSubmit, isLoading }: DiscountFormProps) {
  const [form, setForm] = useState<DiscountCodeInput>({
    ...emptyState,
    ...(initial
      ? {
          ...initial,
          value: String(initial.value),
          min_order_amount: initial.min_order_amount == null ? null : String(initial.min_order_amount),
          max_discount_amount: initial.max_discount_amount == null ? null : String(initial.max_discount_amount),
          usage_limit_total: initial.usage_limit_total,
          usage_limit_per_user: initial.usage_limit_per_user,
          starts_at: initial.starts_at ? toDatetimeLocal(initial.starts_at) : null,
          expires_at: initial.expires_at ? toDatetimeLocal(initial.expires_at) : null,
          product_ids: initial.product_ids || [],
          collection_ids: initial.collection_ids || [],
        }
      : {}),
  });

  const update = <K extends keyof DiscountCodeInput>(key: K, value: DiscountCodeInput[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...form,
      starts_at: fromDatetimeLocal(form.starts_at || ''),
      expires_at: fromDatetimeLocal(form.expires_at || ''),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Código</label>
          <Input value={form.code} onChange={(e) => update('code', e.target.value.toUpperCase())} required />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Descripción</label>
          <Input value={form.description} onChange={(e) => update('description', e.target.value)} />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Tipo</label>
          <select
            className="input w-full"
            value={form.discount_type}
            onChange={(e) => update('discount_type', e.target.value as DiscountType)}
          >
            <option value="percentage">Porcentaje</option>
            <option value="fixed_amount">Monto fijo</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Valor</label>
          <Input
            type="number"
            step="0.01"
            min="0"
            value={form.value}
            onChange={(e) => update('value', e.target.value)}
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Moneda</label>
          <Input value={form.currency} onChange={(e) => update('currency', e.target.value)} required />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Monto mínimo de orden</label>
          <Input
            type="number"
            step="0.01"
            min="0"
            value={form.min_order_amount ?? ''}
            onChange={(e) => update('min_order_amount', e.target.value === '' ? null : e.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Descuento máximo</label>
          <Input
            type="number"
            step="0.01"
            min="0"
            value={form.max_discount_amount ?? ''}
            onChange={(e) => update('max_discount_amount', e.target.value === '' ? null : e.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Límite total de usos</label>
          <Input
            type="number"
            min="0"
            value={form.usage_limit_total ?? ''}
            onChange={(e) => update('usage_limit_total', e.target.value === '' ? null : Number(e.target.value))}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Límite por usuario</label>
          <Input
            type="number"
            min="0"
            value={form.usage_limit_per_user ?? ''}
            onChange={(e) => update('usage_limit_per_user', e.target.value === '' ? null : Number(e.target.value))}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Inicia</label>
          <Input
            type="datetime-local"
            value={form.starts_at ?? ''}
            onChange={(e) => update('starts_at', e.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Expira</label>
          <Input
            type="datetime-local"
            value={form.expires_at ?? ''}
            onChange={(e) => update('expires_at', e.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-stone-700">Aplica a</label>
          <select
            className="input w-full"
            value={form.applies_to}
            onChange={(e) => update('applies_to', e.target.value as AppliesTo)}
          >
            <option value="all">Todos los productos</option>
            <option value="products">Productos específicos</option>
            <option value="collections">Colecciones específicas</option>
          </select>
        </div>
        <div className="flex items-center gap-2 md:col-span-2">
          <input
            id="is_active"
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => update('is_active', e.target.checked)}
          />
          <label htmlFor="is_active" className="text-sm font-medium text-stone-700">Activo</label>
        </div>
        {form.applies_to === 'products' && (
          <div className="md:col-span-2">
            <label className="mb-1 block text-sm font-medium text-stone-700">IDs de productos</label>
            <TagsInput
              value={form.product_ids}
              onChange={(v) => update('product_ids', v)}
              placeholder="id1, id2, id3"
            />
          </div>
        )}
        {form.applies_to === 'collections' && (
          <div className="md:col-span-2">
            <label className="mb-1 block text-sm font-medium text-stone-700">IDs de colecciones</label>
            <TagsInput
              value={form.collection_ids}
              onChange={(v) => update('collection_ids', v)}
              placeholder="id1, id2, id3"
            />
          </div>
        )}
      </div>
      <Button type="submit" disabled={isLoading}>{isLoading ? 'Guardando...' : 'Guardar cupón'}</Button>
    </form>
  );
}
