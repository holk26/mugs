const API_BASE = import.meta.env.DJANGO_API_URL || 'http://localhost:8080';

export interface Product {
  id: string;
  handle: string;
  title: string;
  description: string;
  price: string;
  compare_at_price?: string;
  status: string;
  medias: { id: string; url: string; alt: string }[];
  variants: Variant[];
}

export interface Variant {
  id: string;
  title: string;
  sku: string;
  price: string;
  options: Record<string, string>;
}

export interface CartItem {
  variantId: string;
  productHandle: string;
  title: string;
  variantTitle: string;
  price: number;
  quantity: number;
  uploadUrl?: string;
  uploadFile?: File;
}

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function listProducts(): Promise<{ results: Product[] }> {
  return fetchJson('/api/v1/products/?expand=medias,variants');
}

export async function getProduct(handle: string): Promise<Product> {
  return fetchJson(`/api/v1/products/${handle}/?expand=medias,variants`);
}

export async function createOrder(items: CartItem[], customer: { email: string; name: string }) {
  const lines = items.map((item) => ({
    variant: item.variantId,
    title: `${item.title} — ${item.variantTitle}`,
    quantity: item.quantity,
    price: item.price.toFixed(2),
  }));

  return fetchJson('/api/v1/orders/', {
    method: 'POST',
    body: JSON.stringify({
      customer_email: customer.email,
      customer_name: customer.name,
      shipping_address: {},
      lines,
    }),
  });
}

export async function uploadDrawing(orderId: string, lineId: string, file: File) {
  const form = new FormData();
  form.append('file', file);
  return fetch(`${API_BASE}/api/v1/orders/${orderId}/lines/${lineId}/upload/`, {
    method: 'POST',
    body: form,
  });
}

export async function createPaymentIntent(orderId: string) {
  return fetchJson('/api/v1/payments/stripe/intent/', {
    method: 'POST',
    body: JSON.stringify({ order_id: orderId }),
  });
}
