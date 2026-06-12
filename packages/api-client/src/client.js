/**
 * Cliente HTTP básico para la API de Storecraft.
 * @param {string} baseUrl - URL base del backend, ej. http://localhost:8080
 * @param {object} [options]
 * @param {string} [options.apiKey] - API key para header X-API-KEY
 * @param {string} [options.accessToken] - Bearer token de acceso
 */
export function createClient(baseUrl, options = {}) {
  const normalized = baseUrl.replace(/\/$/, '');

  /**
   * @param {string} path
   * @param {RequestInit} [init]
   */
  async function request(path, init = {}) {
    const url = `${normalized}/api${path.startsWith('/') ? path : '/' + path}`;
    const headers = new Headers(init.headers || {});

    if (options.apiKey) {
      headers.set('X-API-KEY', options.apiKey);
    }
    if (options.accessToken) {
      headers.set('Authorization', `Bearer ${options.accessToken}`);
    }
    if (init.body && typeof init.body === 'object' && !(init.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(url, {
      ...init,
      headers,
      body: init.body && typeof init.body === 'object' && !(init.body instanceof FormData)
        ? JSON.stringify(init.body)
        : init.body,
    });

    const text = await response.text();
    const data = text ? JSON.parse(text) : null;

    if (!response.ok) {
      const error = new Error(data?.message || `HTTP ${response.status}`);
      // @ts-ignore
      error.status = response.status;
      // @ts-ignore
      error.body = data;
      throw error;
    }

    return data;
  }

  return { request };
}
