import { createFileRoute } from '@tanstack/react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getProduct, updateProduct, type ProductDetail } from '@/api/products';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { ProductGeneralTab } from '@/components/products/ProductGeneralTab';
import { ProductVariantsTab } from '@/components/products/ProductVariantsTab';
import { ProductMediaTab } from '@/components/products/ProductMediaTab';
import type { ProductInput } from '@/lib/schemas';

export const Route = createFileRoute('/products/$id')({
  component: EditProductPage,
});

function EditProductPage() {
  const { id } = Route.useParams();
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
    },
  });

  if (isLoading) return <p>Cargando...</p>;

  const product = data as ProductDetail;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-900">Editar producto</h1>
      <Tabs defaultValue="general">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="variants">Variantes</TabsTrigger>
          <TabsTrigger value="media">Medios</TabsTrigger>
        </TabsList>
        <TabsContent value="general">
          <ProductGeneralTab product={product} onSubmit={(values) => mutation.mutate(values)} isLoading={mutation.isPending} />
        </TabsContent>
        <TabsContent value="variants">
          <ProductVariantsTab productId={id} />
        </TabsContent>
        <TabsContent value="media">
          <ProductMediaTab productId={id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
