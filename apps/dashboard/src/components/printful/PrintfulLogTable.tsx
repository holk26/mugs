import { DataTable } from '@/components/ui/DataTable';
import { formatDate } from '@/lib/utils';
import type { PrintfulSyncLog } from '@/api/printful';

interface Props {
  logs: PrintfulSyncLog[];
}

export function PrintfulLogTable({ logs }: Props) {
  const columns = [
    { key: 'started_at', header: 'Inicio', render: (l: PrintfulSyncLog) => formatDate(l.started_at) },
    { key: 'status', header: 'Estado' },
    { key: 'created', header: 'Creados', render: (l: PrintfulSyncLog) => l.products_created },
    { key: 'updated', header: 'Actualizados', render: (l: PrintfulSyncLog) => l.products_updated },
    { key: 'errors', header: 'Errores', render: (l: PrintfulSyncLog) => l.errors.length },
  ];

  return <DataTable columns={columns} data={logs} keyExtractor={(l) => l.id} />;
}
