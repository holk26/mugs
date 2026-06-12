/**
 * @typedef {import('../types.js').StorecraftClient} StorecraftClient
 * @typedef {import('../types.js').Product} Product
 * @typedef {import('../types.js').ListQuery} ListQuery
 * @typedef {import('../types.js').ListResponse} ListResponse
 */

/**
 * Listar productos.
 * @param {StorecraftClient} client
 * @param {ListQuery} [query]
 * @returns {Promise<ListResponse<Product>>}
 */
export async function getProducts(client, query = {}) {
  const params = buildSearchParams(query);
  return client.request(`/products${params}`);
}

/**
 * Obtener un producto por id o handle.
 * @param {StorecraftClient} client
 * @param {string} idOrHandle
 * @returns {Promise<Product>}
 */
export async function getProduct(client, idOrHandle) {
  return client.request(`/products/${encodeURIComponent(idOrHandle)}`);
}

/**
 * @param {ListQuery} query
 */
function buildSearchParams(query) {
  const params = new URLSearchParams();
  if (query.limit) params.set('limit', String(query.limit));
  if (query.offset) params.set('offset', String(query.offset));
  if (query.sortBy) params.set('sortBy', query.sortBy);
  if (query.order) params.set('order', query.order);
  if (query.expand) params.set('expand', JSON.stringify(query.expand));
  if (query.vql) params.set('vql', query.vql);
  const qs = params.toString();
  return qs ? '?' + qs : '';
}
