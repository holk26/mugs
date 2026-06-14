import { pfProductHandle, pfVariantHandle, parseNumber } from './utils.js';

export function printfulStoreProductToStorecraftProduct(syncProduct, syncVariants = []) {
  const handle = pfProductHandle(syncProduct.id);
  const media = syncProduct.thumbnail_url ? [syncProduct.thumbnail_url] : [];

  return {
    handle,
    title: syncProduct.name || `Printful Product ${syncProduct.id}`,
    description: syncProduct.description || '',
    price: 0,
    qty: 1,
    active: syncProduct.is_ignored !== true && syncVariants.some(v => v.availability_status === 'active'),
    media,
    tags: ['printful'],
    attributes: [
      { key: 'printful_sync_product_id', value: String(syncProduct.id) }
    ]
  };
}

export function printfulSyncVariantToStorecraftVariant(syncVariant, parentProduct) {
  const parentHandle = pfProductHandle(parentProduct.id);
  const handle = pfVariantHandle(parentProduct.id, syncVariant.id);
  const media = [];

  if (syncVariant.product?.image) {
    media.push(syncVariant.product.image);
  }

  if (syncVariant.files?.length) {
    for (const file of syncVariant.files) {
      const url = file.preview_url || file.url;
      if (url && !media.includes(url)) {
        media.push(url);
      }
    }
  }

  const hint = [];
  if (syncVariant.size) {
    hint.push({ name: 'size', value: syncVariant.size });
  }
  if (syncVariant.color) {
    hint.push({ name: 'color', value: syncVariant.color });
  }

  return {
    handle,
    parent_handle: parentHandle,
    parent_id: parentHandle,
    title: syncVariant.name || `${parentProduct.name} variant`,
    price: parseNumber(syncVariant.retail_price),
    qty: syncVariant.availability_status === 'active' ? 100 : 0,
    active: syncVariant.is_ignored !== true && syncVariant.availability_status === 'active',
    media,
    tags: ['printful'],
    attributes: [
      { key: 'printful_sync_variant_id', value: String(syncVariant.id) },
      { key: 'printful_variant_id', value: String(syncVariant.variant_id) }
    ],
    variant_hint: hint
  };
}

export function storecraftAddressToPrintfulRecipient(address, contact = {}) {
  const fromContact = [contact.firstname, contact.lastname].filter(Boolean).join(' ');
  const fromAddress = [address?.firstname, address?.lastname].filter(Boolean).join(' ');
  const name = fromContact || fromAddress || 'Customer';

  return {
    name,
    company: address?.company || '',
    address1: address?.street1 || '',
    address2: address?.street2 || '',
    city: address?.city || '',
    state_code: address?.state || '',
    country_code: address?.country || '',
    zip: address?.zip_code || address?.postal_code || '',
    phone: contact?.phone_number || address?.phone_number || '',
    email: contact?.email || ''
  };
}

export function storecraftLineItemsToPrintfulItems(lineItems, variantsMap) {
  return lineItems
    .map(item => {
      const pfVariantId = variantsMap[item.id];
      if (!pfVariantId) return null;

      return {
        variant_id: Number(pfVariantId),
        quantity: item.qty,
        retail_price: String(item.price || 0)
      };
    })
    .filter(Boolean);
}

export function printfulShippingRateToStorecraftShippingMethod(rate) {
  return {
    handle: `pf-ship-${rate.id}-${Math.random().toString(36).slice(2, 8)}`,
    title: rate.name || `Printful ${rate.id}`,
    price: parseNumber(rate.rate)
  };
}

export function printfulOrderStatusToStorecraftStatus(pfStatus) {
  switch (pfStatus) {
    case 'draft':
    case 'pending':
    case 'inreview':
      return 'pending';
    case 'inprocess':
    case 'partial':
      return 'processing';
    case 'fulfilled':
      return 'fulfilled';
    case 'canceled':
      return 'cancelled';
    case 'failed':
    case 'onhold':
      return 'failed';
    default:
      return 'pending';
  }
}
