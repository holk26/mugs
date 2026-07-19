import type { APIRoute } from 'astro';
import { createHmac, timingSafeEqual } from 'crypto';

export const POST: APIRoute = async ({ request }) => {
  const signature = request.headers.get('X-PF-WEBHOOK-SIGNATURE') || '';
  const body = await request.text();
  const secret = process.env.PRINTFUL_WEBHOOK_SECRET || '';

  // Fail closed: without a configured secret there is no way to authenticate
  // the sender, so the webhook must not be processed at all.
  if (!secret) {
    return new Response(JSON.stringify({ detail: 'Webhook secret not configured.' }), { status: 500 });
  }

  const expected = createHmac('sha256', secret).update(body).digest('hex');
  const signatureBuffer = Buffer.from(signature);
  const expectedBuffer = Buffer.from(expected);
  const valid =
    signatureBuffer.length === expectedBuffer.length &&
    timingSafeEqual(signatureBuffer, expectedBuffer);
  if (!valid) {
    return new Response(JSON.stringify({ detail: 'Invalid signature.' }), { status: 400 });
  }

  const baseUrl = import.meta.env.PUBLIC_DJANGO_API_URL || process.env.PUBLIC_DJANGO_API_URL;

  if (!baseUrl) {
    return new Response(JSON.stringify({ detail: 'Backend URL not configured.' }), { status: 500 });
  }

  try {
    const response = await fetch(`${baseUrl}/api/v1/printful/webhook/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-PF-WEBHOOK-SIGNATURE': signature,
      },
      body,
    });
    return new Response(await response.text(), { status: response.status });
  } catch (err) {
    return new Response(JSON.stringify({ detail: 'Backend unreachable.' }), { status: 502 });
  }
};
