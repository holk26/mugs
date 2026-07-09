import { useState, useMemo, useEffect } from 'react';
import { useCart } from '../stores/cart';
import type { Product } from '../lib/api';
import UploadZone from './UploadZone';
import ProductGallery from './ProductGallery';
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
        <div className="reveal">
          <ProductGallery medias={product.medias} title={product.title} />
        </div>

        <div className="reveal reveal-delay-1 flex flex-col">
          <p className="eyebrow">Personalized mug</p>
          <h1 className="mt-3 font-serif text-4xl tracking-tight text-earth md:text-5xl">
            {product.title}
          </h1>
          <p className="mt-4 font-mono text-2xl font-bold text-earth">
            ${selectedVariant?.price}
          </p>
          <p className="mt-6 leading-relaxed text-stone">{product.description}</p>

          <div className="mt-8">
            <label className="text-sm font-semibold text-earth">Size</label>
            <div className="mt-3 flex flex-wrap gap-2">
              {product.variants.map((v) => (
                <button
                  key={v.id}
                  onClick={() => setVariantId(v.id)}
                  className={`rounded-full border px-5 py-2.5 text-sm font-medium transition ${
                    variantId === v.id
                      ? 'border-earth bg-earth text-cream'
                      : 'border-earth/10 bg-white text-stone hover:border-clay'
                  }`}
                >
                  {v.title}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-8">
            <label className="text-sm font-semibold text-earth">Upload your drawing</label>
            <div className="mt-3">
              <UploadZone onFile={handleFile} preview={preview} onClear={handleClear} />
            </div>
            <p className="mt-3 text-sm text-stone">
              We will digitize, clean, and print it on the mug.
            </p>
          </div>

          <button
            onClick={handleAdd}
            disabled={!selectedVariant || added}
            className="btn-primary mt-10 w-full md:w-max"
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
