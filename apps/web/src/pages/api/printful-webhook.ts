import type { APIRoute } from 'astro';
import { createHmac } from 'crypto';

export const POST: APIRoute = async ({ request }) => {
  const signature = request.headers.get('X-PF-WEBHOOK-SIGNATURE') || '';
  const body = await request.text();
  const secret = process.env.PRINTFUL_WEBHOOK_SECRET || '';

  if (secret) {
    const expected = createHmac('sha256', secret).update(body).digest('hex');
    if (signature !== expected) {
      return new Response(JSON.stringify({ detail: 'Invalid signature.' }), { status: 400 });
    }
  }

  const baseUrl =
    import.meta.env.DJANGO_API_URL ||
    import.meta.env.CORE_API_URL ||
    process.env.DJANGO_API_URL ||
    process.env.CORE_API_URL;

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
