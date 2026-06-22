const API_BASE =
  import.meta.env.DJANGO_API_URL ||
  import.meta.env.CORE_API_URL ||
  'http://localhost:8080';

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
  uploadPreview?: string;
  uploadName?: string;
}

export interface OrderLine {
  id: string;
  variant: string;
  title: string;
  quantity: number;
  price: string;
  customer_upload?: string;
}

export interface Order {
  id: string;
  status: string;
  customer_email: string;
  customer_name: string;
  total: string;
  currency: string;
  lines: OrderLine[];
}

export interface PaymentIntent {
  client_secret: string;
  publishable_key: string;
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

export async function createOrder(
  items: CartItem[],
  customer: { email: string; name: string }
): Promise<Order> {
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

export async function uploadDrawing(
  orderId: string,
  lineId: string,
  file: File
): Promise<{ id: string; customer_upload: string }> {
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(
    `${API_BASE}/api/v1/orders/${orderId}/lines/${lineId}/upload/`,
    {
      method: 'POST',
      body: form,
    }
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function createPaymentIntent(orderId: string): Promise<PaymentIntent> {
  return fetchJson('/api/v1/payments/stripe/intent/', {
    method: 'POST',
    body: JSON.stringify({ order_id: orderId }),
  });
}

export function dataUrlToFile(dataUrl: string, filename: string): File {
  const arr = dataUrl.split(',');
  const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/png';
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new File([u8arr], filename, { type: mime });
}
