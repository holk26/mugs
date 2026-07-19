import { X, Plus, Minus, Trash2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useCart } from '../stores/cart';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  inline?: boolean;
}

export default function CartDrawer({ isOpen, onClose, inline }: Props) {
  const { items, updateQuantity, removeItem, total } = useCart();
  const dialogRef = useRef<HTMLDivElement>(null);
  const [storageWarning, setStorageWarning] = useState(false);

  // Close with Escape and move focus into the dialog when it opens.
  useEffect(() => {
    if (inline || !isOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    dialogRef.current?.focus();
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, inline, onClose]);

  // Surface localStorage quota failures (large drawing previews) to the user.
  useEffect(() => {
    const handleStorageError = () => setStorageWarning(true);
    window.addEventListener('recuerdo:cart-storage-error', handleStorageError);
    return () => window.removeEventListener('recuerdo:cart-storage-error', handleStorageError);
  }, []);

  if (!isOpen && !inline) return null;

  const contents = (
    <>
      {!inline && (
        <div className="flex items-center justify-between border-b border-earth/5 px-6 py-5">
          <h2 className="font-serif text-xl tracking-tight text-earth">Your cart</h2>
          <button
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-full text-stone transition hover:bg-earth/5 hover:text-earth"
            aria-label="Close cart"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      )}

      {storageWarning && (
        <div role="alert" className="mx-6 mt-4 rounded-xl bg-clay/10 px-4 py-3 text-xs font-medium text-earth">
          Your browser storage is full, so your cart and drawing won't be kept if you
          reload this page. Complete your order in this session.
        </div>
      )}

      <div className={`flex-1 overflow-y-auto px-6 ${inline ? 'py-0' : 'py-6'}`}>
        {items.length === 0 ? (
          <div className={`flex flex-col items-center text-center ${inline ? '' : 'h-full justify-center'}`}>
            <p className="text-stone">Your cart is empty.</p>
            <a
              href="/products"
              onClick={onClose}
              className="mt-4 text-sm font-semibold text-earth underline underline-offset-4 hover:text-clay"
            >
              Start shopping
            </a>
          </div>
        ) : (
          <ul className="space-y-6">
            {items.map((item) => (
              <li key={item.variantId} className="flex gap-4">
                <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-xl bg-cream text-xs text-stone">
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
                  <p className="truncate font-semibold text-earth">{item.title}</p>
                  <p className="text-sm text-stone">{item.variantTitle}</p>
                  {item.uploadPreview && (
                    <p className="mt-1 text-xs font-bold text-clay">Drawing attached</p>
                  )}
                </div>
                <div className="flex flex-col items-end gap-3">
                  <p className="font-mono text-sm font-bold text-earth">
                    ${(item.price * item.quantity).toFixed(2)}
                  </p>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => updateQuantity(item.variantId, Math.max(1, item.quantity - 1))}
                      className="flex h-7 w-7 items-center justify-center rounded-full border border-earth/10 text-stone transition hover:bg-earth/5"
                      aria-label="Decrease quantity"
                    >
                      <Minus className="h-3 w-3" />
                    </button>
                    <span className="w-6 text-center text-sm tabular-nums">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.variantId, item.quantity + 1)}
                      className="flex h-7 w-7 items-center justify-center rounded-full border border-earth/10 text-stone transition hover:bg-earth/5"
                      aria-label="Increase quantity"
                    >
                      <Plus className="h-3 w-3" />
                    </button>
                    <button
                      onClick={() => removeItem(item.variantId)}
                      className="ml-2 text-stone transition hover:text-clay"
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
        <div className={`border-t border-earth/5 px-6 py-6`}>
          <div className="mb-5 flex justify-between text-base font-bold text-earth">
            <span>Total</span>
            <span className="font-mono">${total().toFixed(2)}</span>
          </div>
          <a href="/checkout" onClick={onClose} className="btn-primary w-full text-center">
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
        className="fixed inset-0 z-50 bg-earth/20 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Shopping cart"
        tabIndex={-1}
        className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col bg-cream shadow-2xl outline-none"
      >
        {contents}
      </div>
    </>
  );
}
