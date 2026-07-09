import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { listPrintfulStoreProducts, importPrintfulProduct } from '@/api/printful';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Download, Search, Loader2 } from 'lucide-react';

export function PrintfulImportPanel() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['printful-store-products', debouncedSearch],
    queryFn: () => listPrintfulStoreProducts({ search: debouncedSearch }),
  });

  const importMutation = useMutation({
    mutationFn: importPrintfulProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setDebouncedSearch(search);
  };

  const products = data?.items || [];

  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Importar desde Printful</h2>
          <p className="text-sm text-stone-500">
            Selecciona un producto de tu tienda Printful para agregarlo al catálogo.
          </p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <Input
          placeholder="Buscar producto..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1"
        />
        <Button type="submit" variant="secondary" className="gap-2">
          <Search className="h-4 w-4" />
          Buscar
        </Button>
      </form>

      {error && (
        <p className="text-sm text-red-600">
          Error cargando productos: {error.message}
        </p>
      )}

      {isLoading ? (
        <div className="flex items-center gap-2 text-sm text-stone-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Cargando productos...
        </div>
      ) : (
        <ul className="divide-y divide-stone-200">
          {products.map((product) => {
            const isImporting = importMutation.isPending && importMutation.variables === product.id;

            return (
              <li key={product.id} className="flex items-center gap-4 py-3">
                {product.thumbnail_url ? (
                  <img
                    src={product.thumbnail_url}
                    alt={product.name}
                    className="h-12 w-12 rounded-lg border border-stone-200 object-contain"
                  />
                ) : (
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg border border-stone-200 bg-stone-100 text-xs text-stone-400">
                    N/A
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{product.name}</p>
                  <p className="text-xs text-stone-500">ID: {product.id}</p>
                </div>
                <Button
                  onClick={() => importMutation.mutate(product.id)}
                  disabled={importMutation.isPending}
                  className="gap-2"
                >
                  {isImporting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Importando...
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4" />
                      Importar
                    </>
                  )}
                </Button>
              </li>
            );
          })}
          {products.length === 0 && !error && (
            <li className="py-4 text-sm text-stone-500">No se encontraron productos.</li>
          )}
        </ul>
      )}

      {importMutation.isError && (
        <p className="text-sm text-red-600">
          Error: {importMutation.error?.message}
        </p>
      )}

      {importMutation.isSuccess && (
        <p className="text-sm text-green-700">
          "{importMutation.data.title}" importado correctamente.
        </p>
      )}
    </Card>
  );
}
