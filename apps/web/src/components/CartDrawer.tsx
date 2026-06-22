import { X, Plus, Minus, Trash2 } from 'lucide-react';
import { useCart } from '../stores/cart';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function CartDrawer({ isOpen, onClose }: Props) {
  const { items, updateQuantity, removeItem, total } = useCart();

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-black/40"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-neutral-200 px-6 py-4">
          <h2 className="text-lg font-semibold">Your cart</h2>
          <button onClick={onClose} aria-label="Close cart">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {items.length === 0 ? (
            <p className="text-neutral-500">Your cart is empty.</p>
          ) : (
            <ul className="space-y-6">
              {items.map((item) => (
                <li key={item.variantId} className="flex gap-4">
                  <div className="flex-1">
                    <p className="font-medium">{item.title}</p>
                    <p className="text-sm text-neutral-500">{item.variantTitle}</p>
                    {item.uploadPreview && (
                      <p className="text-xs text-green-700">Drawing attached</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <p>${(item.price * item.quantity).toFixed(2)}</p>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => updateQuantity(item.variantId, Math.max(1, item.quantity - 1))}
                        className="rounded border p-1 hover:bg-neutral-100"
                      >
                        <Minus className="h-3 w-3" />
                      </button>
                      <span className="w-4 text-center text-sm">{item.quantity}</span>
                      <button
                        onClick={() => updateQuantity(item.variantId, item.quantity + 1)}
                        className="rounded border p-1 hover:bg-neutral-100"
                      >
                        <Plus className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => removeItem(item.variantId)}
                        className="ml-2 text-neutral-400 hover:text-red-600"
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
          <div className="border-t border-neutral-200 px-6 py-4">
            <div className="mb-4 flex justify-between text-lg font-semibold">
              <span>Total</span>
              <span>${total().toFixed(2)}</span>
            </div>
            <a
              href="/checkout"
              onClick={onClose}
              className="block w-full rounded-lg bg-orange-700 py-3 text-center font-medium text-white hover:bg-orange-800"
            >
              Checkout
            </a>
          </div>
        )}
      </div>
    </>
  );
}
