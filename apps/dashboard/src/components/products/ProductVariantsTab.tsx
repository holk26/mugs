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
