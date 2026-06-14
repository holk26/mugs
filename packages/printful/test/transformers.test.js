import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  printfulStoreProductToStorecraftProduct,
  printfulSyncVariantToStorecraftVariant,
  storecraftAddressToPrintfulRecipient,
  printfulOrderStatusToStorecraftStatus
} from '../src/transformers.js';

describe('transformers', () => {
  it('maps a sync product', () => {
    const result = printfulStoreProductToStorecraftProduct({
      id: 123,
      name: 'Test Mug',
      thumbnail_url: 'https://example.com/mug.jpg'
    }, [{ availability_status: 'active' }]);

    assert.equal(result.handle, 'pf-123');
    assert.equal(result.title, 'Test Mug');
    assert.deepEqual(result.media, ['https://example.com/mug.jpg']);
    assert.equal(result.active, true);
  });

  it('maps a sync variant', () => {
    const result = printfulSyncVariantToStorecraftVariant({
      id: 456,
      variant_id: 789,
      name: 'Test Mug - White',
      retail_price: '19.99',
      availability_status: 'active',
      size: '11oz',
      color: 'White'
    }, { id: 123, name: 'Test Mug' });

    assert.equal(result.handle, 'pf-123-456');
    assert.equal(result.price, 19.99);
    assert.equal(result.qty, 100);
    assert.deepEqual(result.variant_hint, [
      { name: 'size', value: '11oz' },
      { name: 'color', value: 'White' }
    ]);
  });

  it('maps address to recipient', () => {
    const result = storecraftAddressToPrintfulRecipient({
      firstname: 'Jane',
      lastname: 'Doe',
      street1: '123 Main St',
      city: 'Austin',
      state: 'TX',
      country: 'US',
      zip_code: '78701'
    }, { email: 'jane@example.com' });

    assert.equal(result.name, 'Jane Doe');
    assert.equal(result.country_code, 'US');
    assert.equal(result.email, 'jane@example.com');
  });

  it('maps Printful statuses to Storecraft statuses', () => {
    assert.equal(printfulOrderStatusToStorecraftStatus('fulfilled'), 'fulfilled');
    assert.equal(printfulOrderStatusToStorecraftStatus('canceled'), 'cancelled');
    assert.equal(printfulOrderStatusToStorecraftStatus('inprocess'), 'processing');
  });
});
