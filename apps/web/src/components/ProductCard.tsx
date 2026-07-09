import type { Product } from '../lib/api';

interface Props {
  product: Product;
}

export default function ProductCard({ product }: Props) {
  const image = product.medias[0]?.url;

  return (
    <a href={`/products/${product.handle}`} className="group block">
      <div className="card aspect-square overflow-hidden">
        {image ? (
          <img
            src={image}
            alt={product.medias[0]?.alt || product.title}
            className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full items-center justify-center bg-cream text-stone">
            No image
          </div>
        )}
      </div>
      <div className="mt-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-earth transition group-hover:text-clay">
            {product.title}
          </h3>
          <p className="mt-1 font-mono text-sm text-stone">
            From ${product.price}
          </p>
        </div>
        <span className="rounded-full bg-sand px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-earth">
          New
        </span>
      </div>
    </a>
  );
}
