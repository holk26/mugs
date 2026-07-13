import { useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getOrder,
  updateOrderStatus,
  pushOrderToPrintful,
  confirmPrintfulOrder,
  processLineImage,
  generateLineMockup,
  type OrderLine,
} from '@/api/orders';
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
  const [provider, setProvider] = useState<'openai' | 'gemini'>('gemini');
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

  const pushMutation = useMutation({
    mutationFn: () => pushOrderToPrintful(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['order', id] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });

  const confirmMutation = useMutation({
    mutationFn: () => confirmPrintfulOrder(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['order', id] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });

  const processImageMutation = useMutation({
    mutationFn: () => {
      const line = data?.lines?.find((l) => l.id);
      if (!line?.id) throw new Error('No line available for image processing');
      return processLineImage(id, line.id, provider);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['order', id] });
    },
  });

  const mockupMutation = useMutation({
    mutationFn: () => {
      const line = data?.lines?.find((l) => l.id);
      if (!line?.id) throw new Error('No line available for mockup generation');
      return generateLineMockup(id, line.id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['order', id] });
    },
  });

  if (isLoading) return <p>Cargando...</p>;
  if (!data) return <p>No se encontró la orden.</p>;

  const upload = data.raw_upload;
  const processedUpload = data.processed_upload;

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
          {data.discount_code && (
            <div>
              <dt className="text-stone-500">Descuento</dt>
              <dd className="font-medium">{data.discount_code} (-{formatCurrency(Number(data.discount_amount || 0))})</dd>
            </div>
          )}
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
            keyExtractor={(l) => l.id || `${l.product_name}-${l.variant_name}-${l.quantity}`}
          />
        ) : (
          <p className="text-stone-500">Esta orden no tiene productos.</p>
        )}
      </Card>

      {upload && (
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Archivo del cliente</h2>
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="mb-2 text-sm font-medium text-stone-700">Original</p>
              <img
                src={resolveFileUrl(upload.file)}
                alt={upload.name || 'Original'}
                className="h-48 w-full rounded-lg border border-stone-200 object-contain"
              />
              <a
                href={resolveFileUrl(upload.file)}
                download={upload.name || true}
                className="mt-2 inline-flex items-center justify-center rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
              >
                Descargar original
              </a>
            </div>
            {processedUpload && (
              <div>
                <p className="mb-2 text-sm font-medium text-stone-700">Procesada por IA</p>
                <img
                  src={resolveFileUrl(processedUpload.file)}
                  alt={processedUpload.name || 'Procesada'}
                  className="h-48 w-full rounded-lg border border-stone-200 object-contain"
                />
                <a
                  href={resolveFileUrl(processedUpload.file)}
                  download={processedUpload.name || true}
                  className="mt-2 inline-flex items-center justify-center rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
                >
                  Descargar procesada
                </a>
              </div>
            )}
            {data.mockup && (
              <div>
                <p className="mb-2 text-sm font-medium text-stone-700">Vista previa del producto</p>
                <img
                  src={resolveFileUrl(data.mockup.file)}
                  alt={data.mockup.name || 'Mockup'}
                  className="h-48 w-full rounded-lg border border-stone-200 object-contain"
                />
                <a
                  href={resolveFileUrl(data.mockup.file)}
                  download={data.mockup.name || true}
                  className="mt-2 inline-flex items-center justify-center rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
                >
                  Descargar vista previa
                </a>
              </div>
            )}
          </div>
          {!data.printful_order_id && (
            <div className="mt-4 space-y-3">
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                <p className="font-medium">Flujo manual de producción</p>
                <p>
                  1) El pago ya fue recibido. 2) El operador debe generar la imagen limpia con IA.
                  3) Revisar el resultado. 4) Generar la vista previa del producto. 5) Enviar el
                  borrador a Printful. Si la IA falla, se puede reintentar con el mismo u otro
                  proveedor.
                </p>
              </div>
              {data.processed_upload_error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  <p className="font-medium">Error anterior al procesar con IA:</p>
                  <p>{data.processed_upload_error}</p>
                </div>
              )}
              <div className="flex flex-col flex-wrap gap-3 sm:flex-row sm:items-center">
                <div className="flex items-center gap-2">
                  <label htmlFor="provider" className="text-sm font-medium text-stone-700">Proveedor IA:</label>
                  <select
                    id="provider"
                    className="input"
                    value={provider}
                    onChange={(e) => setProvider(e.target.value as 'openai' | 'gemini')}
                  >
                    <option value="openai">OpenAI (DALL·E / gpt-image-2)</option>
                    <option value="gemini">Google Gemini</option>
                  </select>
                </div>
                <Button
                  onClick={() => processImageMutation.mutate()}
                  disabled={processImageMutation.isPending}
                >
                  {processImageMutation.isPending
                    ? 'Procesando con IA...'
                    : data.processed_upload_error
                      ? 'Reintentar generación con IA'
                      : 'Generar imagen limpia con IA'}
                </Button>
                {processedUpload && !data.mockup && (
                  <Button
                    variant="secondary"
                    onClick={() => mockupMutation.mutate()}
                    disabled={mockupMutation.isPending}
                  >
                    {mockupMutation.isPending ? 'Generando vista previa...' : 'Generar vista previa del producto'}
                  </Button>
                )}
                {processImageMutation.isError && (
                  <p className="text-sm text-red-600">
                    Error: {processImageMutation.error?.message}
                  </p>
                )}
                {mockupMutation.isError && (
                  <p className="text-sm text-red-600">
                    Error: {mockupMutation.error?.message}
                  </p>
                )}
              </div>
            </div>
          )}
        </Card>
      )}

      <Card>
        <h2 className="mb-4 text-lg font-semibold">Dirección de envío</h2>
        {data.shipping_address ? (
          <address className="grid gap-1 text-sm not-italic">
            <p className="font-medium">{data.shipping_address.name}</p>
            <p>{data.shipping_address.line1 || data.shipping_address.address1}</p>
            {data.shipping_address.line2 && <p>{data.shipping_address.line2}</p>}
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
        <h2 className="mb-4 text-lg font-semibold">Printful</h2>
        <div className="space-y-3">
          <div className="text-sm">
            <p>
              <span className="text-stone-500">ID en Printful:</span>{' '}
              {data.printful_order_id || 'Sin enviar'}
            </p>
            <p>
              <span className="text-stone-500">Estado:</span>{' '}
              {data.printful_status || '—'}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {!data.printful_order_id && (
              <Button
                onClick={() => pushMutation.mutate()}
                disabled={pushMutation.isPending}
              >
                {pushMutation.isPending ? 'Enviando...' : 'Enviar borrador a Printful'}
              </Button>
            )}
            {data.printful_order_id && data.printful_status !== 'pending' && (
              <Button
                variant="primary"
                onClick={() => confirmMutation.mutate()}
                disabled={confirmMutation.isPending}
              >
                {confirmMutation.isPending ? 'Confirmando...' : 'Confirmar envío a Printful'}
              </Button>
            )}
          </div>
          {(pushMutation.isError || confirmMutation.isError) && (
            <p className="text-sm text-red-600">
              Error: {(pushMutation.error || confirmMutation.error)?.message}
            </p>
          )}
        </div>
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
