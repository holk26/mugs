import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createDiscount, type DiscountCodeInput } from '@/api/discounts';
import { DiscountForm } from '@/components/discounts/DiscountForm';

export const Route = createFileRoute('/discounts/new')({
  component: NewDiscountPage,
});

function NewDiscountPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: createDiscount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discounts'] });
      navigate({ to: '/discounts' });
    },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-stone-900">Nuevo cupón</h1>
      <DiscountForm onSubmit={(data: DiscountCodeInput) => mutation.mutate(data)} isLoading={mutation.isPending} />
    </div>
  );
}
