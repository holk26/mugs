import { Badge } from '@/components/ui/Badge';

const statusConfig: Record<string, { label: string; variant: 'default' | 'success' | 'warning' | 'danger' }> = {
  pending: { label: 'Pendiente', variant: 'warning' },
  paid: { label: 'Pagada', variant: 'success' },
  processing: { label: 'En preparación', variant: 'default' },
  fulfilled: { label: 'Enviada', variant: 'success' },
  cancelled: { label: 'Cancelada', variant: 'danger' },
  failed: { label: 'Fallida', variant: 'danger' },
};

export function OrderStatusBadge({ status }: { status: string }) {
  const config = statusConfig[status] || { label: status, variant: 'default' };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
