import { useState } from 'react';
import { DataTable } from '@/components/ui/DataTable';
import { Button } from '@/components/ui/Button';
import { WebhookPayloadModal } from './WebhookPayloadModal';
import type { PrintfulWebhookEvent } from '@/api/printful-webhooks';

interface PrintfulWebhookTableProps {
  events: PrintfulWebhookEvent[];
  isLoading?: boolean;
}

export function PrintfulWebhookTable({ events, isLoading }: PrintfulWebhookTableProps) {
  const [selected, setSelected] = useState<PrintfulWebhookEvent | null>(null);

  return (
    <>
      <DataTable
        data={events}
        keyExtractor={(row) => row.id}
        isLoading={isLoading}
        columns={[
          { key: 'event_type', header: 'Evento' },
          {
            key: 'processed',
            header: 'Procesado',
            render: (row) => (row.processed ? 'Sí' : 'No'),
          },
          {
            key: 'created_at',
            header: 'Recibido',
            render: (row) => new Date(row.created_at).toLocaleString(),
          },
          {
            key: 'actions',
            header: 'Acciones',
            render: (row) => (
              <Button variant="secondary" onClick={() => setSelected(row)}>
                Ver payload
              </Button>
            ),
          },
        ]}
      />
      {selected && <WebhookPayloadModal payload={selected.payload} onClose={() => setSelected(null)} />}
    </>
  );
}
