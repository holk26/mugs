import { createFileRoute, Link } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { listDiscounts, type DiscountCode } from '@/api/discounts';
import { DataTable } from '@/components/ui/DataTable';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Plus } from 'lucide-react';

export const Route = createFileRoute('/discounts/')({
  component: DiscountsPage,
});

const typeMap = {
  percentage: { label: 'Porcentaje', variant: 'default' as const },
  fixed_amount: { label: 'Monto fijo', variant: 'warning' as const },
};

function DiscountsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['discounts'],
    queryFn: () => listDiscounts(),
  });

  const columns = [
    { key: 'code', header: 'Código' },
    { key: 'description', header: 'Descripción' },
    { key: 'type', header: 'Tipo', render: (d: DiscountCode) => (
      <Badge variant={typeMap[d.discount_type].variant}>{typeMap[d.discount_type].label}</Badge>
    )},
    { key: 'value', header: 'Valor', render: (d: DiscountCode) => (
      d.discount_type === 'percentage' ? `${d.value}%` : `$${d.value}`
    )},
    { key: 'usage', header: 'Usos', render: (d: DiscountCode) => `${d.usage_count}${d.usage_limit_total ? ` / ${d.usage_limit_total}` : ''}` },
    { key: 'status', header: 'Estado', render: (d: DiscountCode) => (
      <Badge variant={d.is_active ? 'success' : 'default'}>{d.is_active ? 'Activo' : 'Inactivo'}</Badge>
    )},
    { key: 'actions', header: '', render: (d: DiscountCode) => (
      <Link to={`/discounts/$id`} params={{ id: d.id }} className="text-primary-700 hover:underline">Editar</Link>
    )},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-stone-900">Cupones de descuento</h1>
        <Link to="/discounts/new">
          <Button className="gap-2"><Plus className="h-4 w-4" /> Nuevo cupón</Button>
        </Link>
      </div>
      <DataTable columns={columns} data={data?.results || []} keyExtractor={(d) => d.id} isLoading={isLoading} />
    </div>
  );
}
