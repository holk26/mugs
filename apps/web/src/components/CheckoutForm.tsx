import { useState, type FormEvent } from 'react';
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { useCart } from '../stores/cart';
import {
  createOrder,
  createPaymentIntent,
  uploadDrawing,
  dataUrlToFile,
  type OrderLine,
} from '../lib/api';
import { Lock } from 'lucide-react';

const stripePromise = loadStripe(import.meta.env.PUBLIC_STRIPE_PUBLISHABLE_KEY || '');

function PaymentForm({ orderId }: { orderId: string }) {
  const stripe = useStripe();
  const elements = useElements();
  const [error, setError] = useState<string>('');
  const [processing, setProcessing] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!stripe || !elements) return;

    setProcessing(true);
    const { error: submitError } = await elements.submit();
    if (submitError) {
      setError(submitError.message || 'Payment error');
      setProcessing(false);
      return;
    }

    const { error: confirmError } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${window.location.origin}/thanks?order=${orderId}`,
      },
    });

    if (confirmError) {
      setError(confirmError.message || 'Payment failed');
    }
    setProcessing(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
        <PaymentElement />
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={!stripe || processing}
        className="btn-primary w-full"
      >
        <Lock className="h-4 w-4" />
        {processing ? 'Processing...' : 'Pay now'}
      </button>
    </form>
  );
}

export default function CheckoutForm() {
  const { items, total } = useCart();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [step, setStep] = useState<'form' | 'payment'>('form');
  const [clientSecret, setClientSecret] = useState('');
  const [orderId, setOrderId] = useState('');
  const [error, setError] = useState('');

  const handleCreateOrder = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!email || items.length === 0) return;

    setError('');
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

      const intent = await createPaymentIntent(order.id);
      setClientSecret(intent.client_secret);
      setStep('payment');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Checkout failed');
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

            <button type="submit" className="btn-primary w-full">
              Continue to payment
            </button>
          </form>
        ) : (
          <div className="mt-8">
            <p className="text-sm text-stone-500">
              Order <span className="font-medium text-stone-900">{orderId}</span>. Complete payment below.
            </p>
            {clientSecret && (
              <div className="mt-4">
                <Elements stripe={stripePromise} options={{ clientSecret }}>
                  <PaymentForm orderId={orderId} />
                </Elements>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
