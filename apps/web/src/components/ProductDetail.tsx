import { useState, useMemo } from 'react';
import { useCart } from '../stores/cart';
import type { Product } from '../lib/api';
import UploadZone from './UploadZone';

interface Props {
  product: Product;
}

export default function ProductDetail({ product }: Props) {
  const [variantId, setVariantId] = useState(product.variants[0]?.id || '');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>('');
  const addItem = useCart((s) => s.addItem);

  const selectedVariant = useMemo(
    () => product.variants.find((v) => v.id === variantId) || product.variants[0],
    [variantId, product.variants]
  );

  const handleFile = (f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const handleAdd = () => {
    if (!selectedVariant) return;
    addItem({
      variantId: selectedVariant.id,
      productHandle: product.handle,
      title: product.title,
      variantTitle: selectedVariant.title,
      price: parseFloat(selectedVariant.price),
      quantity: 1,
      uploadFile: file || undefined,
      uploadUrl: preview || undefined,
    });
  };

  return (
    <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 md:grid-cols-2">
      <div className="rounded-xl bg-neutral-100">
        {product.medias[0] ? (
          <img
            src={product.medias[0].url}
            alt={product.medias[0].alt || product.title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-96 items-center justify-center text-neutral-400">No image</div>
        )}
      </div>

      <div className="flex flex-col">
        <h1 className="text-3xl font-semibold text-neutral-900">{product.title}</h1>
        <p className="mt-2 text-2xl font-medium text-neutral-700">${selectedVariant?.price}</p>
        <p className="mt-4 leading-relaxed text-neutral-600">{product.description}</p>

        <div className="mt-6">
          <label className="text-sm font-medium text-neutral-700">Size</label>
          <div className="mt-2 flex flex-wrap gap-2">
            {product.variants.map((v) => (
              <button
                key={v.id}
                onClick={() => setVariantId(v.id)}
                className={`rounded-lg border px-4 py-2 text-sm font-medium transition ${
                  variantId === v.id
                    ? 'border-orange-700 bg-orange-700 text-white'
                    : 'border-neutral-300 text-neutral-700 hover:border-neutral-400'
                }`}
              >
                {v.title}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6">
          <label className="text-sm font-medium text-neutral-700">Upload your drawing</label>
          <div className="mt-2">
            <UploadZone onFile={handleFile} preview={preview} />
          </div>
          <p className="mt-2 text-xs text-neutral-500">
            We will digitize and clean it before printing.
          </p>
        </div>

        <button
          onClick={handleAdd}
          className="mt-8 w-full rounded-lg bg-orange-700 py-3 text-center font-medium text-white hover:bg-orange-800 disabled:bg-neutral-300"
          disabled={!selectedVariant}
        >
          Add to cart
        </button>
      </div>
    </div>
  );
}
