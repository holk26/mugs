import { createFileRoute } from '@tanstack/react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getOrder, updateOrderStatus } from '@/api/orders';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { OrderStatusBadge } from '@/components/orders/OrderStatusBadge';
import { formatCurrency, formatDate } from '@/lib/utils';

export const Route = createFileRoute('/orders/$id')({
  component: OrderDetailPage,
});

const statuses = ['pending', 'paid', 'processing', 'fulfilled', 'cancelled'];

function OrderDetailPage() {
  const { id } = Route.useParams();
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ['order', id],
    queryFn: () => getOrder(id),
  });

  const mutation = useMutation({
    mutationFn: (status: string) => updateOrderStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['order', id] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });

  if (isLoading) return <p>Cargando...</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-stone-900">Orden {id.slice(0, 8)}</h1>
        <OrderStatusBadge status={data.status} />
      </div>
      <Card>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div><dt className="text-stone-500">Cliente</dt><dd className="font-medium">{data.customer_name || data.customer_email}</dd></div>
          <div><dt className="text-stone-500">Email</dt><dd className="font-medium">{data.customer_email}</dd></div>
          <div><dt className="text-stone-500">Total</dt><dd className="font-medium">{formatCurrency(data.total)}</dd></div>
          <div><dt className="text-stone-500">Fecha</dt><dd className="font-medium">{formatDate(data.created_at)}</dd></div>
        </dl>
      </Card>
      <Card>
        <h2 className="mb-4 text-lg font-semibold">Cambiar estado</h2>
        <div className="flex flex-wrap gap-2">
          {statuses.map((s) => (
            <Button
              key={s}
              variant={data.status === s ? 'primary' : 'secondary'}
              onClick={() => mutation.mutate(s)}
              disabled={mutation.isPending || data.status === s}
            >
              {s}
            </Button>
          ))}
        </div>
      </Card>
    </div>
  );
}
