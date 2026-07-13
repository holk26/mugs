import { useState, type FormEvent } from 'react';
import { useCart } from '../stores/cart';
import {
  createOrder,
  createCheckoutSession,
  uploadDrawing,
  applyDiscount,
  removeDiscount,
  dataUrlToFile,
  type OrderLine,
  type DiscountResult,
} from '../lib/api';
import { AddressForm, type AddressFormData } from './AddressForm';
import { ArrowLeft, ExternalLink, Tag, X } from 'lucide-react';

function formatMoney(amount: number | string): string {
  return `$${Number(amount).toFixed(2)}`;
}

const emptyAddress: AddressFormData = {
  address1: '',
  city: '',
  state_code: '',
  zip: '',
  country_code: '',
};

export default function CheckoutForm() {
  const { items, total } = useCart();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [address, setAddress] = useState<AddressFormData>(emptyAddress);
  const [step, setStep] = useState<'form' | 'payment'>('form');
  const [orderId, setOrderId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [couponCode, setCouponCode] = useState('');
  const [couponLoading, setCouponLoading] = useState(false);
  const [discount, setDiscount] = useState<DiscountResult | null>(null);

  const addressComplete =
    address.address1.trim() &&
    address.city.trim() &&
    address.state_code.trim() &&
    address.zip.trim() &&
    address.country_code.trim();

  const handleCreateOrder = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!email || items.length === 0 || !addressComplete) return;

    setError('');
    setLoading(true);
    try {
      const order = await createOrder(items, { email, name }, {
        name: name || email,
        line1: address.address1,
        city: address.city,
        state: address.state_code,
        postal_code: address.zip,
        country: address.country_code,
      });
      setOrderId(order.id);

      for (const item of items) {
        const line = order.lines.find((l: OrderLine) => l.variant === item.variantId);
        if (line && item.uploadPreview && item.uploadName) {
          const file = dataUrlToFile(item.uploadPreview, item.uploadName);
          await uploadDrawing(order.id, line.id, file);
        }
      }

      setStep('payment');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Checkout failed');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyCoupon = async (e: FormEvent) => {
    e.preventDefault();
    if (!couponCode.trim() || !orderId) return;

    setCouponLoading(true);
    setError('');
    try {
      const result = await applyDiscount(orderId, couponCode.trim(), email);
      setDiscount(result);
      setCouponCode('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid coupon');
      setDiscount(null);
    } finally {
      setCouponLoading(false);
    }
  };

  const handleRemoveCoupon = async () => {
    if (!orderId) return;
    setCouponLoading(true);
    setError('');
    try {
      await removeDiscount(orderId, email);
      setDiscount(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not remove coupon');
    } finally {
      setCouponLoading(false);
    }
  };

  const handlePay = async () => {
    if (!orderId) return;

    setLoading(true);
    setError('');
    try {
      const session = await createCheckoutSession(orderId);
      window.location.href = session.url;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  const subtotal = total();
  const discountAmount = discount ? Number(discount.discount_amount) : 0;
  const finalTotal = discount ? Number(discount.order_total) : subtotal;

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
              <h2 className="text-lg font-semibold text-stone-900">Shipping address</h2>
              <div className="mt-4">
                <AddressForm value={address} onChange={setAddress} disabled={loading} />
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
              disabled={loading || !addressComplete}
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

              <div className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between text-stone-600">
                  <span>Subtotal</span>
                  <span>{formatMoney(subtotal)}</span>
                </div>
                {discount && (
                  <div className="flex justify-between text-green-700">
                    <span className="flex items-center gap-1">
                      <Tag className="h-3.5 w-3.5" />
                      Discount ({discount.discount_code})
                    </span>
                    <span>-{formatMoney(discountAmount)}</span>
                  </div>
                )}
                <div className="flex justify-between border-t border-stone-100 pt-2 text-base font-semibold text-stone-900">
                  <span>Total</span>
                  <span>{formatMoney(finalTotal)}</span>
                </div>
              </div>

              {!discount ? (
                <form onSubmit={handleApplyCoupon} className="mt-6">
                  <label className="block text-sm font-medium text-stone-700">Discount code</label>
                  <div className="mt-2 flex gap-2">
                    <input
                      type="text"
                      value={couponCode}
                      onChange={(e) => setCouponCode(e.target.value)}
                      placeholder="Enter code"
                      className="flex-1 rounded-xl border border-stone-200 bg-stone-50 px-4 py-2.5 text-sm uppercase outline-none transition focus:border-orange-700 focus:bg-white focus:ring-1 focus:ring-orange-700"
                    />
                    <button
                      type="submit"
                      disabled={couponLoading || !couponCode.trim()}
                      className="btn-secondary disabled:opacity-60"
                    >
                      {couponLoading ? '...' : 'Apply'}
                    </button>
                  </div>
                </form>
              ) : (
                <div className="mt-6 flex items-center justify-between rounded-xl bg-green-50 px-4 py-3 text-sm text-green-800">
                  <span className="flex items-center gap-2">
                    <Tag className="h-4 w-4" />
                    Coupon <strong>{discount.discount_code}</strong> applied
                  </span>
                  <button
                    onClick={handleRemoveCoupon}
                    disabled={couponLoading}
                    className="inline-flex items-center gap-1 text-red-600 hover:text-red-700 disabled:opacity-60"
                  >
                    <X className="h-4 w-4" />
                    Remove
                  </button>
                </div>
              )}

              {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

              <button
                onClick={handlePay}
                disabled={loading || couponLoading}
                className="btn-primary mt-6 flex w-full items-center justify-center gap-2 disabled:opacity-60"
              >
                <ExternalLink className="h-4 w-4" />
                Pay {formatMoney(finalTotal)} with Stripe
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
