import { useState, type FormEvent } from 'react';
import { useCart } from '../stores/cart';
import {
  createOrder,
  createCheckoutSession,
  uploadDrawing,
  dataUrlToFile,
  type OrderLine,
} from '../lib/api';
import { ArrowLeft, ExternalLink } from 'lucide-react';

export default function CheckoutForm() {
  const { items, total } = useCart();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [step, setStep] = useState<'form' | 'payment'>('form');
  const [orderId, setOrderId] = useState('');
  const [checkoutUrl, setCheckoutUrl] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleCreateOrder = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!email || items.length === 0) return;

    setError('');
    setLoading(true);
    try {
      const order = await createOrder(items, { email, name });
      setOrderId(order.id);

      for (const item of items) {
        const line = order.lines.find((l: OrderLine) => l.variant === item.variantId);
        if (line && item.uploadPreview && item.uploadName) {
          const file = dataUrlToFile(item.uploadPreview, item.uploadName);
          await uploadDrawing(order.id, line.id, file);
        }
      }

      const session = await createCheckoutSession(order.id);
      setCheckoutUrl(session.url);
      setStep('payment');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Checkout failed');
    } finally {
      setLoading(false);
    }
  };

  const handlePay = () => {
    if (checkoutUrl) {
      window.location.href = checkoutUrl;
    }
  };

  if (items.length === 0 && step === 'form') {
    return (
      <div className="section py-20 text-center">
        <p className="text-stone">Your cart is empty.</p>
        <a href="/products" className="btn-secondary mt-6 inline-flex">
          Continue shopping
        </a>
      </div>
    );
  }

  return (
    <div className="section py-12 md:py-20">
      <div className="mx-auto max-w-2xl">
        <h1 className="font-serif text-4xl tracking-tight text-earth md:text-5xl">Checkout</h1>

        {step === 'form' ? (
          <form onSubmit={handleCreateOrder} className="mt-8 space-y-6">
            <div className="rounded-2xl border border-earth/5 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-earth">Contact</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-earth">Full name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="mt-1 w-full rounded-xl border border-earth/10 bg-cream px-4 py-2.5 text-sm outline-none transition focus:border-clay focus:bg-white focus:ring-1 focus:ring-clay"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-earth">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="mt-1 w-full rounded-xl border border-earth/10 bg-cream px-4 py-2.5 text-sm outline-none transition focus:border-clay focus:bg-white focus:ring-1 focus:ring-clay"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-earth/5 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-earth">Order summary</h2>
              <ul className="mt-4 space-y-3 text-sm text-stone">
                {items.map((item) => (
                  <li key={item.variantId} className="flex justify-between">
                    <span>
                      {item.quantity}x {item.title} &mdash; {item.variantTitle}
                    </span>
                    <span className="font-mono font-bold text-earth">
                      ${(item.price * item.quantity).toFixed(2)}
                    </span>
                  </li>
                ))}
              </ul>
              <div className="mt-4 flex justify-between border-t border-earth/5 pt-4 text-base font-bold text-earth">
                <span>Total</span>
                <span className="font-mono">${total().toFixed(2)}</span>
              </div>
            </div>

            {error && <p className="text-sm text-terracotta">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full disabled:opacity-60"
            >
              {loading ? 'Processing...' : 'Continue to payment'}
            </button>
          </form>
        ) : (
          <div className="mt-8 space-y-6">
            <button
              onClick={() => setStep('form')}
              className="inline-flex items-center text-sm font-semibold text-stone hover:text-earth"
            >
              <ArrowLeft className="mr-1 h-4 w-4" />
              Back to shipping
            </button>

            <div className="rounded-2xl border border-earth/5 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-earth">Complete your payment</h2>
              <p className="mt-2 text-sm text-stone">
                Order <span className="font-mono font-bold text-earth">{orderId}</span>
              </p>
              <p className="mt-4 text-sm text-stone">
                You will be redirected to Stripe to complete the payment securely.
              </p>

              {error && <p className="mt-4 text-sm text-terracotta">{error}</p>}

              <button
                onClick={handlePay}
                disabled={!checkoutUrl || loading}
                className="btn-primary mt-6 flex w-full items-center justify-center gap-2 disabled:opacity-60"
              >
                <ExternalLink className="h-4 w-4" />
                Pay with Stripe
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
