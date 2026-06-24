import { createFileRoute } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { listPrintfulLogs } from '@/api/printful';
import { PrintfulSyncPanel } from '@/components/printful/PrintfulSyncPanel';
import { PrintfulLogTable } from '@/components/printful/PrintfulLogTable';

export const Route = createFileRoute('/printful/')({
  component: PrintfulPage,
});

function PrintfulPage() {
  const { data } = useQuery({
    queryKey: ['printful-logs'],
    queryFn: listPrintfulLogs,
    refetchInterval: 5000,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-900">Printful</h1>
      <PrintfulSyncPanel />
      <div>
        <h2 className="mb-4 text-lg font-semibold">Historial de sincronización</h2>
        <PrintfulLogTable logs={data?.results || []} />
      </div>
    </div>
  );
}
