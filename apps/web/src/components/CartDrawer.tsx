import { X, Plus, Minus, Trash2 } from 'lucide-react';
import { useCart } from '../stores/cart';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  inline?: boolean;
}

export default function CartDrawer({ isOpen, onClose, inline }: Props) {
  const { items, updateQuantity, removeItem, total } = useCart();

  if (!isOpen && !inline) return null;

  const contents = (
    <>
      {!inline && (
        <div className="flex items-center justify-between border-b border-stone-100 px-6 py-5">
          <h2 className="text-lg font-semibold tracking-tight text-stone-900">Your cart</h2>
          <button
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-full text-stone-500 transition hover:bg-stone-100 hover:text-stone-900"
            aria-label="Close cart"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      )}

      <div className={`flex-1 overflow-y-auto px-6 ${inline ? 'py-0' : 'py-6'}`}>
        {items.length === 0 ? (
          <div className={`flex flex-col items-center text-center ${inline ? '' : 'h-full justify-center'}`}>
            <p className="text-stone-500">Your cart is empty.</p>
            <a
              href="/products"
              onClick={onClose}
              className="mt-4 text-sm font-medium text-orange-700 hover:underline"
            >
              Start shopping
            </a>
          </div>
        ) : (
          <ul className="space-y-6">
            {items.map((item) => (
              <li key={item.variantId} className="flex gap-4">
                <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-xl bg-stone-100 text-xs text-stone-400">
                  {item.uploadPreview ? (
                    <img
                      src={item.uploadPreview}
                      alt=""
                      className="h-full w-full rounded-xl object-cover"
                    />
                  ) : (
                    'Mug'
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-stone-900">{item.title}</p>
                  <p className="text-sm text-stone-500">{item.variantTitle}</p>
                  {item.uploadPreview && (
                    <p className="mt-1 text-xs font-medium text-green-700">Drawing attached</p>
                  )}
                </div>
                <div className="flex flex-col items-end gap-3">
                  <p className="text-sm font-medium text-stone-900">
                    ${(item.price * item.quantity).toFixed(2)}
                  </p>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => updateQuantity(item.variantId, Math.max(1, item.quantity - 1))}
                      className="flex h-7 w-7 items-center justify-center rounded-full border border-stone-200 text-stone-600 transition hover:bg-stone-50"
                      aria-label="Decrease quantity"
                    >
                      <Minus className="h-3 w-3" />
                    </button>
                    <span className="w-6 text-center text-sm tabular-nums">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.variantId, item.quantity + 1)}
                      className="flex h-7 w-7 items-center justify-center rounded-full border border-stone-200 text-stone-600 transition hover:bg-stone-50"
                      aria-label="Increase quantity"
                    >
                      <Plus className="h-3 w-3" />
                    </button>
                    <button
                      onClick={() => removeItem(item.variantId)}
                      className="ml-2 text-stone-400 transition hover:text-red-600"
                      aria-label="Remove item"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {items.length > 0 && (
        <div className={`border-stone-100 px-6 py-6 ${inline ? 'border-t' : 'border-t'}`}>
          <div className="mb-5 flex justify-between text-base font-semibold text-stone-900">
            <span>Total</span>
            <span>${total().toFixed(2)}</span>
          </div>
          <a href="/checkout" onClick={onClose} className="btn-primary w-full">
            Checkout
          </a>
        </div>
      )}
    </>
  );

  if (inline) {
    return <div className="flex flex-col">{contents}</div>;
  }

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-stone-900/30 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col bg-white shadow-2xl">
        {contents}
      </div>
    </>
  );
}
