import { createFileRoute } from '@tanstack/react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getOrder, updateOrderStatus, type OrderLine } from '@/api/orders';
import apiClient from '@/api/client';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { DataTable } from '@/components/ui/DataTable';
import { OrderStatusBadge } from '@/components/orders/OrderStatusBadge';
import { formatCurrency, formatDate } from '@/lib/utils';

export const Route = createFileRoute('/orders/$id')({
  component: OrderDetailPage,
});

const statuses = ['pending', 'paid', 'processing', 'fulfilled', 'cancelled'];

function resolveFileUrl(file: string): string {
  if (/^https?:\/\//i.test(file)) return file;
  const base = apiClient.defaults.baseURL || window.location.origin;
  return new URL(file, base).href;
}

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
  if (!data) return <p>No se encontró la orden.</p>;

  const upload = data.processed_upload || data.raw_upload;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-stone-900">Orden {id.slice(0, 8)}</h1>
        <OrderStatusBadge status={data.status} />
      </div>

      <Card>
        <dl className="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-stone-500">Cliente</dt>
            <dd className="font-medium">{data.customer_name || data.customer_email}</dd>
          </div>
          <div>
            <dt className="text-stone-500">Email</dt>
            <dd className="font-medium">{data.customer_email}</dd>
          </div>
          <div>
            <dt className="text-stone-500">Total</dt>
            <dd className="font-medium">{formatCurrency(Number(data.total))}</dd>
          </div>
          <div>
            <dt className="text-stone-500">Fecha</dt>
            <dd className="font-medium">{formatDate(data.created_at)}</dd>
          </div>
        </dl>
      </Card>

      <Card>
        <h2 className="mb-4 text-lg font-semibold">Productos</h2>
        {data.lines && data.lines.length > 0 ? (
          <DataTable
            columns={[
              { key: 'product', header: 'Producto', render: (l: OrderLine) => l.product_name },
              { key: 'variant', header: 'Variante', render: (l) => l.variant_name || '-' },
              { key: 'quantity', header: 'Cantidad', render: (l) => l.quantity },
              { key: 'unit_price', header: 'Precio unitario', render: (l) => formatCurrency(Number(l.unit_price)) },
              { key: 'total_price', header: 'Total', render: (l) => formatCurrency(Number(l.total_price)) },
            ]}
            data={data.lines}
            keyExtractor={(l) => `${l.product_name}-${l.variant_name}-${l.quantity}`}
          />
        ) : (
          <p className="text-stone-500">Esta orden no tiene productos.</p>
        )}
      </Card>

      {upload && (
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Archivo del cliente</h2>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-stone-600">{upload.name || 'Archivo subido'}</p>
            <a
              href={resolveFileUrl(upload.file)}
              download={upload.name || true}
              className="btn-primary"
            >
              {data.processed_upload ? 'Descargar diseño procesado' : 'Descargar archivo subido'}
            </a>
          </div>
        </Card>
      )}

      <Card>
        <h2 className="mb-4 text-lg font-semibold">Dirección de envío</h2>
        {data.shipping_address ? (
          <address className="grid gap-1 text-sm not-italic">
            <p className="font-medium">{data.shipping_address.name}</p>
            <p>{data.shipping_address.address1}</p>
            {data.shipping_address.address2 && <p>{data.shipping_address.address2}</p>}
            <p>
              {[
                data.shipping_address.city,
                data.shipping_address.state,
                data.shipping_address.postal_code,
              ]
                .filter(Boolean)
                .join(', ')}
            </p>
            <p>{data.shipping_address.country}</p>
          </address>
        ) : (
          <p className="text-stone-500">No se ha registrado dirección de envío.</p>
        )}
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
