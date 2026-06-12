/**
 * @typedef {import('../types.js').StorecraftClient} StorecraftClient
 * @typedef {import('../types.js').Collection} Collection
 * @typedef {import('../types.js').Product} Product
 * @typedef {import('../types.js').ListQuery} ListQuery
 * @typedef {import('../types.js').ListResponse} ListResponse
 */

/**
 * Listar colecciones.
 * @param {StorecraftClient} client
 * @param {ListQuery} [query]
 * @returns {Promise<ListResponse<Collection>>}
 */
export async function getCollections(client, query = {}) {
  const params = buildSearchParams(query);
  return client.request(`/collections${params}`);
}

/**
 * Obtener una colección por id o handle.
 * @param {StorecraftClient} client
 * @param {string} idOrHandle
 * @returns {Promise<Collection>}
 */
export async function getCollection(client, idOrHandle) {
  return client.request(`/collections/${encodeURIComponent(idOrHandle)}`);
}

/**
 * Listar productos de una colección.
 * @param {StorecraftClient} client
 * @param {string} idOrHandle
 * @param {ListQuery} [query]
 * @returns {Promise<ListResponse<Product>>}
 */
export async function getCollectionProducts(client, idOrHandle, query = {}) {
  const params = buildSearchParams(query);
  return client.request(`/collections/${encodeURIComponent(idOrHandle)}/products${params}`);
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
