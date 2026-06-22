import type { Product } from '../lib/api';

interface Props {
  product: Product;
}

export default function ProductCard({ product }: Props) {
  const image = product.medias[0]?.url;

  return (
    <a
      href={`/products/${product.handle}`}
      className="group block"
    >
      <div className="card aspect-square overflow-hidden">
        {image ? (
          <img
            src={image}
            alt={product.medias[0]?.alt || product.title}
            className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full items-center justify-center bg-stone-100 text-stone-400">
            No image
          </div>
        )}
      </div>
      <div className="mt-4">
        <h3 className="text-base font-medium text-stone-900">{product.title}</h3>
        <p className="mt-1 text-sm text-stone-500">From ${product.price}</p>
      </div>
    </a>
  );
}
