import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createProduct } from '@/api/products';
import { ProductForm } from '@/components/products/ProductForm';

export const Route = createFileRoute('/products/new')({
  component: NewProductPage,
});

function NewProductPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      navigate({ to: '/products' });
    },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-900">Nuevo producto</h1>
      <ProductForm onSubmit={(data) => mutation.mutate(data)} isLoading={mutation.isPending} />
    </div>
  );
}
