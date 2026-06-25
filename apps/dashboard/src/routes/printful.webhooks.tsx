import { createFileRoute } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { listPrintfulWebhookEvents } from '@/api/printful-webhooks';
import { PrintfulWebhookTable } from '@/components/printful/PrintfulWebhookTable';

export const Route = createFileRoute('/printful/webhooks')({
  component: PrintfulWebhooksPage,
});

function PrintfulWebhooksPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['printful-webhooks'],
    queryFn: listPrintfulWebhookEvents,
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-900">Webhooks de Printful</h1>
      <PrintfulWebhookTable events={data?.results || []} isLoading={isLoading} />
    </div>
  );
}
