import { defineMiddleware } from 'astro:middleware';

// Security headers for the storefront (the Node standalone server sets none).
// CSP is deliberately permissive with images/media (MinIO, data URLs for the
// upload previews) but blocks framing and mixed content.
export const onRequest = defineMiddleware(async (_context, next) => {
  const response = await next();
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
  return response;
});
