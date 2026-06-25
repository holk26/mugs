import { ProductForm } from './ProductForm';
import type { ProductInput } from '@/lib/schemas';
import type { ProductDetail } from '@/api/products';

interface ProductGeneralTabProps {
  product: ProductDetail;
  onSubmit: (data: ProductInput) => void;
  isLoading?: boolean;
}

export function ProductGeneralTab({ product, onSubmit, isLoading }: ProductGeneralTabProps) {
  return (
    <ProductForm
      defaultValues={{
        ...product,
        tags: Array.isArray(product.tags) ? product.tags : [],
        collections: product.collections || [],
      }}
      onSubmit={onSubmit}
      isLoading={isLoading}
    />
  );
}
