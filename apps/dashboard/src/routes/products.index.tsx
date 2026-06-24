import { createFileRoute, Link } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { listProducts } from '@/api/products';
import { DataTable } from '@/components/ui/DataTable';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Plus } from 'lucide-react';
import type { Product } from '@/api/products';

export const Route = createFileRoute('/products/')({
  component: ProductsPage,
});

const statusMap = {
  draft: { label: 'Borrador', variant: 'default' as const },
  active: { label: 'Activo', variant: 'success' as const },
  archived: { label: 'Archivado', variant: 'warning' as const },
};

function ProductsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['products'],
    queryFn: () => listProducts(),
  });

  const columns = [
    { key: 'title', header: 'Producto' },
    { key: 'handle', header: 'Handle' },
    { key: 'price', header: 'Precio', render: (p: Product) => `$${p.price}` },
    { key: 'status', header: 'Estado', render: (p: Product) => <Badge variant={statusMap[p.status].variant}>{statusMap[p.status].label}</Badge> },
    { key: 'actions', header: '', render: (p: Product) => <Link to={`/products/$id`} params={{ id: p.id }} className="text-primary-700 hover:underline">Editar</Link> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-stone-900">Productos</h1>
        <Link to="/products/new">
          <Button className="gap-2"><Plus className="h-4 w-4" /> Nuevo producto</Button>
        </Link>
      </div>
      <DataTable columns={columns} data={data?.results || []} keyExtractor={(p) => p.id} isLoading={isLoading} />
    </div>
  );
}
