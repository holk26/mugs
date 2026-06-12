/**
 * @typedef {object} StorecraftClient
 * @property {(path: string, init?: RequestInit) => Promise<any>} request
 */

/**
 * @typedef {object} ListQuery
 * @property {number} [limit]
 * @property {number} [offset]
 * @property {string} [sortBy]
 * @property {'asc' | 'desc'} [order]
 * @property {string[]} [expand]
 * @property {string} [vql]
 */

/**
 * @template T
 * @typedef {object} ListResponse
 * @property {T[]} data
 * @property {number} total
 * @property {number} [limit]
 * @property {number} [offset]
 */

/**
 * @typedef {object} Product
 * @property {string} id
 * @property {string} handle
 * @property {string} title
 * @property {string} [description]
 * @property {number} [price]
 * @property {string} [compare_at_price]
 * @property {string} [status]
 * @property {string[]} [tags]
 * @property {object} [variants]
 * @property {object} [medias]
 */

/**
 * @typedef {object} Collection
 * @property {string} id
 * @property {string} handle
 * @property {string} title
 * @property {string} [description]
 * @property {string} [status]
 */

/**
 * @typedef {object} AuthUser
 * @property {string} id
 * @property {string} email
 * @property {string} [firstname]
 * @property {string} [lastname]
 */

export {};
