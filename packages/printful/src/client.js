const DEFAULT_BASE_URL = 'https://api.printful.com';

export class PrintfulError extends Error {
  constructor(message, status, body) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export function createPrintfulClient({ apiToken, storeId, baseUrl = DEFAULT_BASE_URL }) {
  if (!apiToken) {
    throw new PrintfulError('Printful API token is required');
  }

  const headers = {
    'Authorization': `Bearer ${apiToken}`,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  };

  if (storeId) {
    headers['X-PF-Store-Id'] = String(storeId);
  }

  async function request(path, { method = 'GET', body } = {}) {
    const url = `${baseUrl}${path}`;
    const res = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new PrintfulError(
        data?.result || `Printful API error ${res.status}`,
        res.status,
        data
      );
    }

    return data;
  }

  return {
    getStoreProducts: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return request(`/store/products${qs ? '?' + qs : ''}`);
    },

    getStoreProduct: (id) => request(`/store/products/${id}`),

    getSyncVariant: (id) => request(`/store/variants/${id}`),

    calculateShippingRates: (payload) =>
      request('/shipping/rates', { method: 'POST', body: payload }),

    createOrder: (payload, { confirm = true } = {}) =>
      request(`/orders?confirm=${confirm ? 1 : 0}`, { method: 'POST', body: payload }),

    getOrder: (id) => request(`/orders/${id}`)
  };
}
