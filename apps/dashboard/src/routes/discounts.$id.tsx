import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getDiscount, updateDiscount, deleteDiscount, type DiscountCodeInput } from '@/api/discounts';
import { DiscountForm } from '@/components/discounts/DiscountForm';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export const Route = createFileRoute('/discounts/$id')({
  component: EditDiscountPage,
});

function EditDiscountPage() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['discount', id],
    queryFn: () => getDiscount(id),
  });

  const updateMutation = useMutation({
    mutationFn: (values: DiscountCodeInput) => updateDiscount(id, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discounts'] });
      queryClient.invalidateQueries({ queryKey: ['discount', id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteDiscount(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discounts'] });
      navigate({ to: '/discounts' });
    },
  });

  if (isLoading) return <p>Cargando...</p>;
  if (!data) return <p>No se encontró el cupón.</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-stone-900">Editar cupón</h1>
        <Button variant="danger" onClick={() => deleteMutation.mutate()} disabled={deleteMutation.isPending}>
          {deleteMutation.isPending ? 'Eliminando...' : 'Eliminar'}
        </Button>
      </div>

      <Card className="p-6">
        <DiscountForm
          initial={data}
          onSubmit={(values: DiscountCodeInput) => updateMutation.mutate(values)}
          isLoading={updateMutation.isPending}
        />
      </Card>
    </div>
  );
}
