import { createFileRoute } from '@tanstack/react-router';
import { Card } from '@/components/ui/Card';

export const Route = createFileRoute('/')({
  component: HomePage,
});

function HomePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-900">Resumen</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <p className="text-sm text-stone-500">Órdenes hoy</p>
          <p className="text-3xl font-bold text-stone-900">—</p>
        </Card>
        <Card>
          <p className="text-sm text-stone-500">Productos activos</p>
          <p className="text-3xl font-bold text-stone-900">—</p>
        </Card>
        <Card>
          <p className="text-sm text-stone-500">Último sync Printful</p>
          <p className="text-3xl font-bold text-stone-900">—</p>
        </Card>
      </div>
    </div>
  );
}
