import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request }) => {
  const signature = request.headers.get('X-PF-WEBHOOK-SIGNATURE') || '';
  const body = await request.text();

  const djangoUrl = `${import.meta.env.DJANGO_API_URL}/api/v1/printful/webhook/`;
  const response = await fetch(djangoUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-PF-WEBHOOK-SIGNATURE': signature,
    },
    body,
  });

  return new Response(await response.text(), { status: response.status });
};
