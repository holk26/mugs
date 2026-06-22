import type { Product } from '../lib/api';

interface Props {
  product: Product;
}

export default function ProductCard({ product }: Props) {
  const image = product.medias[0]?.url;

  return (
    <a
      href={`/products/${product.handle}`}
      className="group block overflow-hidden rounded-xl border border-neutral-200 bg-white transition hover:shadow-md"
    >
      <div className="aspect-square bg-neutral-100">
        {image ? (
          <img
            src={image}
            alt={product.medias[0]?.alt || product.title}
            className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-neutral-400">No image</div>
        )}
      </div>
      <div className="p-4">
        <h3 className="font-medium text-neutral-900">{product.title}</h3>
        <p className="mt-1 text-sm text-neutral-500">From ${product.price}</p>
      </div>
    </a>
  );
}
