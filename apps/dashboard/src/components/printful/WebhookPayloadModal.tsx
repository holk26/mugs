import { Button } from '@/components/ui/Button';

interface WebhookPayloadModalProps {
  payload: Record<string, unknown>;
  onClose: () => void;
}

export function WebhookPayloadModal({ payload, onClose }: WebhookPayloadModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[80vh] w-full max-w-2xl overflow-auto rounded-xl bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Payload del webhook</h3>
          <Button variant="secondary" onClick={onClose}>Cerrar</Button>
        </div>
        <pre className="overflow-auto rounded-lg bg-stone-100 p-4 text-xs">
          {JSON.stringify(payload, null, 2)}
        </pre>
      </div>
    </div>
  );
}
