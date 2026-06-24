import { useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { productSchema, type ProductInput } from '@/lib/schemas';

interface ProductFormProps {
  defaultValues?: Partial<ProductInput>;
  onSubmit: (data: ProductInput) => void;
  isLoading?: boolean;
}

export function ProductForm({ defaultValues, onSubmit, isLoading }: ProductFormProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<ProductInput>({
    resolver: zodResolver(productSchema) as Resolver<ProductInput>,
    defaultValues: {
      status: 'draft',
      ...defaultValues,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-2xl space-y-6">
      <div>
        <label className="label">Título</label>
        <Input {...register('title')} />
        {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>}
      </div>
      <div>
        <label className="label">Handle</label>
        <Input {...register('handle')} />
        {errors.handle && <p className="mt-1 text-sm text-red-600">{errors.handle.message}</p>}
      </div>
      <div>
        <label className="label">Descripción</label>
        <textarea {...register('description')} className="input min-h-[120px]" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Precio</label>
          <Input {...register('price')} type="number" step="0.01" />
        </div>
        <div>
          <label className="label">Precio comparación</label>
          <Input {...register('compare_at_price')} type="number" step="0.01" />
        </div>
      </div>
      <div>
        <label className="label">Estado</label>
        <select {...register('status')} className="input">
          <option value="draft">Borrador</option>
          <option value="active">Activo</option>
          <option value="archived">Archivado</option>
        </select>
      </div>
      <div className="flex gap-4">
        <Button type="submit" disabled={isLoading}>{isLoading ? 'Guardando...' : 'Guardar'}</Button>
      </div>
    </form>
  );
}
