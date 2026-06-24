import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getProduct, updateProduct } from '@/api/products';
import { ProductForm } from '@/components/products/ProductForm';
import type { ProductInput } from '@/lib/schemas';

export const Route = createFileRoute('/products/$id')({
  component: EditProductPage,
});

function EditProductPage() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['product', id],
    queryFn: () => getProduct(id),
  });

  const mutation = useMutation({
    mutationFn: (values: ProductInput) => updateProduct(id, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['product', id] });
      navigate({ to: '/products' });
    },
  });

  if (isLoading) return <p>Cargando...</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-900">Editar producto</h1>
      <ProductForm defaultValues={data} onSubmit={(values) => mutation.mutate(values)} isLoading={mutation.isPending} />
    </div>
  );
}
