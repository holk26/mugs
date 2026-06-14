import type { APIRoute } from 'astro';
import crypto from 'node:crypto';

const WEBHOOK_SECRET = process.env.PRINTFUL_WEBHOOK_SECRET;
const CORE_URL = process.env.CORE_API_URL || 'http://core:8080';
const INTERNAL_SECRET = process.env.PRINTFUL_INTERNAL_SECRET;

export const POST: APIRoute = async ({ request }) => {
  const signature = request.headers.get('x-pf-webhook-signature');
  const body = await request.text();

  if (!WEBHOOK_SECRET) {
    console.error('Printful webhook: PRINTFUL_WEBHOOK_SECRET not configured');
    return new Response('Webhook secret not configured', { status: 500 });
  }

  if (!signature) {
    return new Response('Missing signature', { status: 401 });
  }

  let key;
  try {
    key = Buffer.from(WEBHOOK_SECRET, 'hex');
  } catch {
    return new Response('Invalid webhook secret', { status: 500 });
  }

  const expected = crypto.createHmac('sha256', key).update(body, 'utf8').digest('hex');

  try {
    if (!crypto.timingSafeEqual(Buffer.from(signature, 'hex'), Buffer.from(expected, 'hex'))) {
      return new Response('Invalid signature', { status: 401 });
    }
  } catch {
    return new Response('Invalid signature', { status: 401 });
  }

  let event;
  try {
    event = JSON.parse(body);
  } catch {
    return new Response('Invalid JSON', { status: 400 });
  }

  const pfOrderId = event?.data?.order?.id;
  if (!pfOrderId) {
    return new Response('No Printful order id', { status: 200 });
  }

  try {
    const res = await fetch(`${CORE_URL}/api/extensions/printful/sync-order-status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ printfulOrderId: String(pfOrderId), secret: INTERNAL_SECRET })
    });

    if (!res.ok) {
      const text = await res.text();
      console.error('Printful webhook: sync-order-status failed', text);
    }
  } catch (err) {
    console.error('Printful webhook: failed to forward to core', err);
  }

  return new Response('OK', { status: 200 });
};
