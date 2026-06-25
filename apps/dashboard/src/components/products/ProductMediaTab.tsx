import { useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listMedia, uploadMedia, deleteMedia, type ProductMedia } from '@/api/media';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface ProductMediaTabProps {
  productId: string;
}

export function ProductMediaTab({ productId }: ProductMediaTabProps) {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [alt, setAlt] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['product-media', productId],
    queryFn: () => listMedia(productId),
  });

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error('No file selected');
      return uploadMedia(productId, { file, alt });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product-media', productId] });
      setFile(null);
      setAlt('');
      if (fileRef.current) fileRef.current.value = '';
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (mediaId: string) => deleteMedia(productId, mediaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product-media', productId] });
    },
  });

  const media = data?.results || [];

  return (
    <div className="space-y-6">
      <div className="flex items-end gap-4 rounded-lg border border-stone-200 bg-white p-4">
        <div className="flex-1">
          <label className="label">Nueva imagen</label>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>
        <div className="flex-1">
          <label className="label">Texto alternativo</label>
          <Input value={alt} onChange={(e) => setAlt(e.target.value)} placeholder="Descripción de la imagen" />
        </div>
        <Button onClick={() => uploadMutation.mutate()} disabled={!file || uploadMutation.isPending}>
          {uploadMutation.isPending ? 'Subiendo...' : 'Subir'}
        </Button>
      </div>

      {isLoading ? (
        <p>Cargando...</p>
      ) : media.length === 0 ? (
        <p className="text-stone-500">No hay medios para este producto.</p>
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {media.map((item) => (
            <MediaCard key={item.id} item={item} onDelete={() => deleteMutation.mutate(item.id)} isDeleting={deleteMutation.isPending} />
          ))}
        </div>
      )}
    </div>
  );
}

function MediaCard({ item, onDelete, isDeleting }: { item: ProductMedia; onDelete: () => void; isDeleting: boolean }) {
  return (
    <div className="overflow-hidden rounded-lg border border-stone-200 bg-white">
      <img src={item.url} alt={item.alt} className="h-40 w-full object-cover" />
      <div className="p-3">
        <p className="truncate text-xs text-stone-500">{item.alt || 'Sin descripción'}</p>
        <Button variant="danger" onClick={onDelete} disabled={isDeleting} className="mt-2 w-full">
          {isDeleting ? 'Eliminando...' : 'Eliminar'}
        </Button>
      </div>
    </div>
  );
}
