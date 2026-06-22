import { useState } from 'react';
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { useCart } from '../stores/cart';
import { createOrder, createPaymentIntent, uploadDrawing } from '../lib/api';

const stripePromise = loadStripe(import.meta.env.PUBLIC_STRIPE_PUBLISHABLE_KEY);

function PaymentForm({ orderId, clientSecret }: { orderId: string; clientSecret: string }) {
  const stripe = useStripe();
  const elements = useElements();
  const [error, setError] = useState<string>('');
  const [processing, setProcessing] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
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
      <PaymentElement />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={!stripe || processing}
        className="w-full rounded-lg bg-orange-700 py-3 font-medium text-white hover:bg-orange-800 disabled:bg-neutral-300"
      >
        {processing ? 'Processing...' : 'Pay now'}
      </button>
    </form>
  );
}

export default function CheckoutForm() {
  const { items, total, clearCart } = useCart();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [step, setStep] = useState<'form' | 'payment'>('form');
  const [clientSecret, setClientSecret] = useState('');
  const [orderId, setOrderId] = useState('');

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || items.length === 0) return;

    const order = await createOrder(items, { email, name });
    setOrderId(order.id);

    for (const item of items) {
      const line = order.lines.find((l: any) => l.variant === item.variantId);
      if (line && item.uploadFile) {
        await uploadDrawing(order.id, line.id, item.uploadFile);
      }
    }

    const intent = await createPaymentIntent(order.id);
    setClientSecret(intent.client_secret);
    setStep('payment');
    clearCart();
  };

  if (items.length === 0 && step === 'form') {
    return (
      <div className="text-center">
        <p className="text-neutral-600">Your cart is empty.</p>
        <a href="/products" className="mt-4 inline-block text-orange-700 hover:underline">
          Continue shopping
        </a>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-12">
      <h1 className="text-2xl font-semibold text-neutral-900">Checkout</h1>

      {step === 'form' ? (
        <form onSubmit={handleCreateOrder} className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-700">Full name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-neutral-300 px-4 py-2 focus:border-orange-700 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-neutral-300 px-4 py-2 focus:border-orange-700 focus:outline-none"
            />
          </div>

          <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-4">
            <p className="text-sm font-medium text-neutral-700">Order summary</p>
            <ul className="mt-2 space-y-1 text-sm text-neutral-600">
              {items.map((item) => (
                <li key={item.variantId} className="flex justify-between">
                  <span>{item.quantity}x {item.title} &mdash; {item.variantTitle}</span>
                  <span>${(item.price * item.quantity).toFixed(2)}</span>
                </li>
              ))}
            </ul>
            <div className="mt-3 flex justify-between border-t border-neutral-200 pt-3 font-semibold">
              <span>Total</span>
              <span>${total().toFixed(2)}</span>
            </div>
          </div>

          <button
            type="submit"
            className="w-full rounded-lg bg-orange-700 py-3 font-medium text-white hover:bg-orange-800"
          >
            Continue to payment
          </button>
        </form>
      ) : (
        <div className="mt-6">
          {clientSecret && (
            <Elements stripe={stripePromise} options={{ clientSecret }}>
              <PaymentForm orderId={orderId} clientSecret={clientSecret} />
            </Elements>
          )}
        </div>
      )}
    </div>
  );
}
