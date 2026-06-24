import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { syncPrintful, listPrintfulLogs } from '@/api/printful';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

export function PrintfulSyncPanel() {
  const queryClient = useQueryClient();
  const { data: logs } = useQuery({
    queryKey: ['printful-logs'],
    queryFn: listPrintfulLogs,
    refetchInterval: 5000,
  });

  const mutation = useMutation({
    mutationFn: syncPrintful,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['printful-logs'] });
    },
  });

  const latest = logs?.results[0];

  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Sincronización Printful</h2>
          {latest && (
            <p className="text-sm text-stone-500">
              Último: {latest.status} · Creados: {latest.products_created} · Actualizados: {latest.products_updated}
            </p>
          )}
        </div>
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="gap-2">
          <RefreshCw className={cn('h-4 w-4', mutation.isPending && 'animate-spin')} />
          {mutation.isPending ? 'Sincronizando...' : 'Sincronizar ahora'}
        </Button>
      </div>
      {mutation.isSuccess && <p className="text-sm text-green-700">Tarea encolada: {mutation.data.task_id}</p>}
    </Card>
  );
}
