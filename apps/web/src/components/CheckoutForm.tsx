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
        <p className="text-stone-600">Your cart is empty.</p>
        <a href="/products" className="btn-secondary mt-6 inline-flex">
          Continue shopping
        </a>
      </div>
    );
  }

  return (
    <div className="section py-12 md:py-20">
      <div className="mx-auto max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight text-stone-900">Checkout</h1>

        {step === 'form' ? (
          <form onSubmit={handleCreateOrder} className="mt-8 space-y-6">
            <div className="rounded-2xl border border-stone-100 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-stone-900">Contact</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-stone-700">Full name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="mt-1 w-full rounded-xl border border-stone-200 bg-stone-50 px-4 py-2.5 text-sm outline-none transition focus:border-orange-700 focus:bg-white focus:ring-1 focus:ring-orange-700"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-stone-700">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="mt-1 w-full rounded-xl border border-stone-200 bg-stone-50 px-4 py-2.5 text-sm outline-none transition focus:border-orange-700 focus:bg-white focus:ring-1 focus:ring-orange-700"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-stone-100 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-stone-900">Order summary</h2>
              <ul className="mt-4 space-y-3 text-sm text-stone-600">
                {items.map((item) => (
                  <li key={item.variantId} className="flex justify-between">
                    <span>
                      {item.quantity}x {item.title} &mdash; {item.variantTitle}
                    </span>
                    <span className="font-medium text-stone-900">
                      ${(item.price * item.quantity).toFixed(2)}
                    </span>
                  </li>
                ))}
              </ul>
              <div className="mt-4 flex justify-between border-t border-stone-100 pt-4 text-base font-semibold text-stone-900">
                <span>Total</span>
                <span>${total().toFixed(2)}</span>
              </div>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

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
              className="inline-flex items-center text-sm font-medium text-stone-600 hover:text-stone-900"
            >
              <ArrowLeft className="mr-1 h-4 w-4" />
              Back to shipping
            </button>

            <div className="rounded-2xl border border-stone-100 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-stone-900">Complete your payment</h2>
              <p className="mt-2 text-sm text-stone-600">
                Order <span className="font-medium text-stone-900">{orderId}</span>
              </p>
              <p className="mt-4 text-sm text-stone-600">
                You will be redirected to Stripe to complete the payment securely.
              </p>

              {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

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
