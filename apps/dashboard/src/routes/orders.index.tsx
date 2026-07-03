import { createFileRoute, Link } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { listOrders } from '@/api/orders';
import { DataTable } from '@/components/ui/DataTable';
import { OrderStatusBadge } from '@/components/orders/OrderStatusBadge';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Order } from '@/api/orders';

export const Route = createFileRoute('/orders/')({
  component: OrdersPage,
});

function OrdersPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: () => listOrders(),
  });

  const columns = [
    { key: 'id', header: 'Orden', render: (o: Order) => <span className="font-mono text-xs">{o.id.slice(0, 8)}</span> },
    { key: 'customer', header: 'Cliente', render: (o: Order) => `${o.customer_name || o.customer_email}` },
    { key: 'total', header: 'Total', render: (o: Order) => formatCurrency(Number(o.total)) },
    { key: 'status', header: 'Estado', render: (o: Order) => <OrderStatusBadge status={o.status} /> },
    { key: 'created_at', header: 'Fecha', render: (o: Order) => formatDate(o.created_at) },
    { key: 'actions', header: '', render: (o: Order) => <Link to={`/orders/$id`} params={{ id: o.id }} className="text-primary-700 hover:underline">Ver</Link> },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-900">Órdenes</h1>
      <DataTable columns={columns} data={data?.results || []} keyExtractor={(o) => o.id} isLoading={isLoading} />
    </div>
  );
}
