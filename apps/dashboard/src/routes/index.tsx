import { createFileRoute } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { getDashboardStats } from '@/api/stats';
import { formatDate } from '@/lib/utils';

export const Route = createFileRoute('/')({
  component: HomePage,
});

function HomePage() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
  });

  const stats = data || { orders_today: 0, active_products: 0, last_sync_at: null };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-900">Resumen</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <p className="text-sm text-stone-500">Órdenes hoy</p>
          <p className="text-3xl font-bold text-stone-900">
            {isLoading ? '—' : stats.orders_today}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-stone-500">Productos activos</p>
          <p className="text-3xl font-bold text-stone-900">
            {isLoading ? '—' : stats.active_products}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-stone-500">Último sync Printful</p>
          <p className="text-3xl font-bold text-stone-900">
            {isLoading || !stats.last_sync_at ? '—' : formatDate(stats.last_sync_at)}
          </p>
        </Card>
      </div>
    </div>
  );
}
