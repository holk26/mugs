/**
 * @typedef {import('../types.js').StorecraftClient} StorecraftClient
 * @typedef {import('../types.js').AuthUser} AuthUser
 */

/**
 * Iniciar sesión con email y contraseña.
 * @param {StorecraftClient} client
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{ accessToken: string, refreshToken: string, user: AuthUser }>}
 */
export async function signIn(client, email, password) {
  return client.request('/auth/signin', {
    method: 'POST',
    body: { email, password },
  });
}

/**
 * Registrar un nuevo usuario.
 * @param {StorecraftClient} client
 * @param {object} data
 * @param {string} data.email
 * @param {string} data.password
 * @param {string} [data.firstname]
 * @param {string} [data.lastname]
 * @returns {Promise<AuthUser>}
 */
export async function signUp(client, data) {
  return client.request('/auth/signup', {
    method: 'POST',
    body: data,
  });
}
