import { useState, useMemo, useEffect } from 'react';
import { useCart } from '../stores/cart';
import type { Product } from '../lib/api';
import UploadZone from './UploadZone';
import { Check, ShoppingBag } from 'lucide-react';

interface Props {
  product: Product;
}

export default function ProductDetail({ product }: Props) {
  const [variantId, setVariantId] = useState(product.variants[0]?.id || '');
  const [preview, setPreview] = useState<string>('');
  const [fileName, setFileName] = useState<string>('');
  const [added, setAdded] = useState(false);
  const addItem = useCart((s) => s.addItem);

  const selectedVariant = useMemo(
    () => product.variants.find((v) => v.id === variantId) || product.variants[0],
    [variantId, product.variants]
  );
  const displayPrice = selectedVariant?.price || product.price || '0.00';

  useEffect(() => {
    return () => {
      if (preview.startsWith('blob:')) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  const handleFile = (f: File) => {
    setFileName(f.name);
    const blobUrl = URL.createObjectURL(f);
    setPreview(blobUrl);
    const reader = new FileReader();
    reader.onloadend = () => {
      const dataUrl = reader.result as string;
      setPreview(dataUrl);
      URL.revokeObjectURL(blobUrl);
    };
    reader.readAsDataURL(f);
  };

  const handleClear = () => {
    setPreview('');
    setFileName('');
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
      uploadPreview: preview || undefined,
      uploadName: fileName || undefined,
    });
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  };

  return (
    <div className="section py-12 md:py-20">
      <div className="grid gap-10 md:grid-cols-2 lg:gap-16">
        <div className="overflow-hidden rounded-3xl bg-stone-100">
          {product.medias[0] ? (
            <img
              src={product.medias[0].url}
              alt={product.medias[0].alt || product.title}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex aspect-square items-center justify-center text-stone-400">
              No image
            </div>
          )}
        </div>

        <div className="flex flex-col">
          <h1 className="text-3xl font-semibold tracking-tight text-stone-900 md:text-4xl">
            {product.title}
          </h1>
          <p className="mt-3 text-2xl font-medium text-stone-700">
            ${displayPrice}
          </p>
          <p className="mt-6 leading-relaxed text-stone-600">{product.description}</p>

          <div className="mt-8">
            <label className="text-sm font-semibold text-stone-900">Size</label>
            <div className="mt-3 flex flex-wrap gap-2">
              {product.variants.map((v) => (
                <button
                  key={v.id}
                  onClick={() => setVariantId(v.id)}
                  className={`rounded-full border px-5 py-2.5 text-sm font-medium transition ${
                    variantId === v.id
                      ? 'border-orange-700 bg-orange-700 text-white'
                      : 'border-stone-200 bg-white text-stone-700 hover:border-stone-300'
                  }`}
                >
                  {v.title}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-8">
            <label className="text-sm font-semibold text-stone-900">Upload your drawing</label>
            <div className="mt-3">
              <UploadZone onFile={handleFile} preview={preview} onClear={handleClear} />
            </div>
            <p className="mt-3 text-sm text-stone-500">
              We will digitize, clean, and print it on the mug.
            </p>
          </div>

          <button
            onClick={handleAdd}
            disabled={!selectedVariant || added}
            className="btn-primary mt-10 w-full md:w-auto"
          >
            {added ? (
              <>
                <Check className="h-4 w-4" /> Added to cart
              </>
            ) : (
              <>
                <ShoppingBag className="h-4 w-4" /> Add to cart
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
