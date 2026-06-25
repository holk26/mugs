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
import { AddressForm, type AddressFormData } from './AddressForm';
import { countryByCode } from '@/lib/countries';

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
  const [shippingStep, setShippingStep] = useState<'shipping' | 'payment'>('shipping');
  const [shippingAddress, setShippingAddress] = useState<AddressFormData>({
    address1: '',
    city: '',
    state_code: '',
    zip: '',
    country_code: '',
  });
  const [clientSecret, setClientSecret] = useState('');
  const [orderId, setOrderId] = useState('');
  const [error, setError] = useState('');

  const isAddressValid = () => {
    return (
      shippingAddress.address1.trim().length > 0 &&
      shippingAddress.city.trim().length > 0 &&
      shippingAddress.state_code.trim().length > 0 &&
      shippingAddress.zip.trim().length > 0 &&
      shippingAddress.country_code.trim().length > 0
    );
  };

  const handleCreateOrder = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!email || items.length === 0 || !isAddressValid()) return;

    setError('');
    try {
      const order = await createOrder({
        customer_name: name,
        customer_email: email,
        shipping_address: {
          name,
          address1: shippingAddress.address1,
          city: shippingAddress.city,
          state_code: shippingAddress.state_code,
          zip: shippingAddress.zip,
          country_code: shippingAddress.country_code,
        },
        lines: items.map((item) => ({
          variant: item.variantId,
          quantity: item.quantity,
        })),
      });
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
      setShippingStep('payment');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Checkout failed');
    }
  };

  if (items.length === 0 && shippingStep === 'shipping') {
    return (
      <div className="section py-20 text-center">
        <p className="text-stone-600">Your cart is empty.</p>
        <a href="/products" className="btn-secondary mt-6 inline-flex">
          Continue shopping
        </a>
      </div>
    );
  }

  const selectedCountry = countryByCode(shippingAddress.country_code);

  return (
    <div className="section py-12 md:py-20">
      <div className="mx-auto max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight text-stone-900">Checkout</h1>

        {shippingStep === 'shipping' ? (
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
              <h2 className="text-lg font-semibold text-stone-900">Shipping address</h2>
              <div className="mt-4">
                <AddressForm
                  value={shippingAddress}
                  onChange={setShippingAddress}
                />
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

              {isAddressValid() && (
                <div className="mt-4 border-t border-stone-100 pt-4">
                  <h3 className="text-sm font-medium text-stone-700">Shipping to</h3>
                  <address className="mt-1 not-italic text-sm text-stone-600">
                    {name}
                    <br />
                    {shippingAddress.address1}
                    <br />
                    {shippingAddress.city}, {shippingAddress.state_code} {shippingAddress.zip}
                    <br />
                    {selectedCountry?.name || shippingAddress.country_code}
                  </address>
                </div>
              )}
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <button
              type="submit"
              disabled={!email || !name || !isAddressValid()}
              className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50"
            >
              Continue to payment
            </button>
          </form>
        ) : (
          <div className="mt-8 space-y-6">
            <div className="rounded-2xl border border-stone-100 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-stone-900">Payment</h2>
              <p className="mt-2 text-sm text-stone-500">
                Order <span className="font-medium text-stone-900">{orderId}</span>. Complete payment below.
              </p>
            </div>
            {clientSecret && (
              <Elements stripe={stripePromise} options={{ clientSecret }}>
                <PaymentForm orderId={orderId} />
              </Elements>
            )}
            <button
              type="button"
              onClick={() => setShippingStep('shipping')}
              className="btn-secondary w-full"
            >
              Back to shipping
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
