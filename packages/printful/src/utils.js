export function toHandle(str) {
  return String(str)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

export function pfProductHandle(syncProductId) {
  return `pf-${syncProductId}`;
}

export function pfVariantHandle(syncProductId, syncVariantId) {
  return `pf-${syncProductId}-${syncVariantId}`;
}

export function parseNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

export function isPrintfulHandle(handle) {
  return typeof handle === 'string' && handle.startsWith('pf-');
}
