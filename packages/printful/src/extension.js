import { createPrintfulClient, PrintfulError } from './client.js';
import {
  printfulStoreProductToStorecraftProduct,
  printfulSyncVariantToStorecraftVariant,
  storecraftAddressToPrintfulRecipient,
  storecraftLineItemsToPrintfulItems,
  printfulShippingRateToStorecraftShippingMethod,
  printfulOrderStatusToStorecraftStatus
} from './transformers.js';
import { pfProductHandle } from './utils.js';

export class PrintfulExtension {
  info = {
    name: 'Printful',
    description: 'Sync Printful catalog and push orders for fulfillment'
  };

  actions = [
    { handle: 'sync-catalog', name: 'Sync Printful catalog' },
    { handle: 'shipping-rates', name: 'Get live shipping rates' },
    { handle: 'select-shipping-rate', name: 'Reserve a shipping method for checkout' },
    { handle: 'push-order', name: 'Push a Storecraft order to Printful' },
    { handle: 'sync-order-status', name: 'Sync a single order status from Printful' }
  ];

  #client = null;
  #app = null;
  #secret = null;
  #syncTimer = null;
  #isSyncing = false;

  onInit(app) {
    this.#app = app;
    const apiToken = process.env.PRINTFUL_API_TOKEN;
    const storeId = process.env.PRINTFUL_STORE_ID;
    this.#secret = process.env.PRINTFUL_INTERNAL_SECRET;

    if (!apiToken) {
      console.warn('PrintfulExtension: PRINTFUL_API_TOKEN missing, extension disabled');
      return;
    }
    if (!this.#secret) {
      console.warn('PrintfulExtension: PRINTFUL_INTERNAL_SECRET missing, protected actions will fail');
    }

    this.#client = createPrintfulClient({ apiToken, storeId });

    app.pubsub.on('orders/payments/captured', async (event) => {
      try {
        await this.#pushOrder(event.payload.current);
      } catch (err) {
        console.error('PrintfulExtension: failed to push order', err);
      }
    });

    const intervalMinutes = Number(process.env.PRINTFUL_SYNC_INTERVAL_MINUTES ?? 60);
    if (intervalMinutes > 0) {
      const ms = intervalMinutes * 60 * 1000;
      this.#syncTimer = setInterval(() => this.#syncCatalogSafe(), ms);
    }
  }

  invokeAction(action_handle) {
    switch (action_handle) {
      case 'sync-catalog': return (payload) => this.#requireSecret(payload, () => this.#syncCatalog(payload));
      case 'shipping-rates': return (payload) => this.#getShippingRates(payload);
      case 'select-shipping-rate': return (payload) => this.#selectShippingRate(payload);
      case 'push-order': return (payload) => this.#requireSecret(payload, () => this.#pushOrderById(payload));
      case 'sync-order-status': return (payload) => this.#requireSecret(payload, () => this.#syncOrderStatus(payload));
    }
  }

  #requireSecret(payload, fn) {
    if (!this.#secret || payload?.secret !== this.#secret) {
      throw new PrintfulError('Unauthorized', 401);
    }
    return fn();
  }

  async #syncCatalogSafe() {
    if (this.#isSyncing) return;
    this.#isSyncing = true;
    try {
      await this.#syncCatalog();
    } catch (err) {
      console.error('PrintfulExtension: scheduled catalog sync failed', err);
    } finally {
      this.#isSyncing = false;
    }
  }

  async #syncCatalog(payload = {}) {
    if (!this.#client) return { created: 0, updated: 0, skipped: 0, errors: 0 };

    let offset = 0;
    const limit = 100;
    let total = Infinity;
    let created = 0, updated = 0, skipped = 0, errors = 0;

    while (offset < total) {
      const { result: products, paging } = await this.#client.getStoreProducts({ limit, offset });
      total = paging?.total ?? (products?.length ?? 0);

      for (const summary of products ?? []) {
        try {
          const { result } = await this.#client.getStoreProduct(summary.id);
          const syncProduct = result.sync_product;
          const syncVariants = result.sync_variants || [];
          const productUpsert = printfulStoreProductToStorecraftProduct(syncProduct, syncVariants);

          const existing = await this.#app.api.products.get(productUpsert.handle).catch(() => null);
          if (existing) updated++; else created++;
          await this.#app.api.products.upsert(productUpsert);

          for (const variant of syncVariants) {
            const variantUpsert = printfulSyncVariantToStorecraftVariant(variant, syncProduct);
            await this.#app.api.products.upsert(variantUpsert);
          }
        } catch (err) {
          errors++;
          console.error(`PrintfulExtension: sync failed for product ${summary.id}`, err);
        }
      }

      offset += limit;
    }

    console.log(`PrintfulExtension: catalog sync complete created=${created} updated=${updated} errors=${errors}`);
    return { created, updated, skipped, errors };
  }

  async #getShippingRates(payload) {
    if (!this.#client) return [];
    const { address, lineItems } = payload || {};
    const variantsMap = await this.#buildVariantsMap(lineItems);
    const items = storecraftLineItemsToPrintfulItems(lineItems, variantsMap);
    if (!items.length) return [];

    const recipient = storecraftAddressToPrintfulRecipient(address);
    const { result: rates } = await this.#client.calculateShippingRates({ recipient, items });

    return (rates || []).map(r => ({
      id: r.id,
      name: r.name,
      rate: Number(r.rate),
      currency: r.currency
    }));
  }

  async #selectShippingRate(payload) {
    if (!this.#app) throw new PrintfulError('Extension not initialized');
    const { rateId, address, lineItems } = payload || {};
    const rates = await this.#getShippingRates({ address, lineItems });
    const rate = rates.find(r => r.id === rateId);
    if (!rate) throw new PrintfulError('Shipping rate not found', 404);

    const shippingMethod = printfulShippingRateToStorecraftShippingMethod(rate);
    shippingMethod.attributes = [
      { key: 'printful_rate_id', value: rate.id }
    ];
    await this.#app.api.shipping_methods.upsert(shippingMethod);
    return { shippingMethodHandle: shippingMethod.handle };
  }

  async #pushOrderById(payload) {
    const order = await this.#app.api.orders.get(payload.orderId);
    return this.#pushOrder(order);
  }

  async #pushOrder(order) {
    if (!this.#client || !order) return null;

    const lineItems = order.line_items || [];
    const variantsMap = await this.#buildVariantsMap(lineItems);
    const items = storecraftLineItemsToPrintfulItems(lineItems, variantsMap);
    if (!items.length) return null;

    const recipient = storecraftAddressToPrintfulRecipient(order.address, order.contact);
    const rateId = order.shipping_method?.attributes?.find(a => a.key === 'printful_rate_id')?.value;
    const shipping = rateId || 'STANDARD';

    const { result: pfOrder } = await this.#client.createOrder({
      external_id: order.id,
      recipient,
      items,
      shipping
    });

    order.attributes = order.attributes || [];
    order.attributes.push(
      { key: 'printful_order_id', value: String(pfOrder.id) },
      { key: 'printful_status', value: pfOrder.status }
    );
    order.tags = [...new Set([...(order.tags || []), 'printful'])];

    await this.#app.api.orders.upsert(order);
    console.log(`PrintfulExtension: pushed order ${order.id} as Printful order ${pfOrder.id}`);
    return { printfulOrderId: pfOrder.id, status: pfOrder.status };
  }

  async #syncOrderStatus(payload) {
    if (!this.#client) throw new PrintfulError('Printful client not initialized');

    let order;
    if (payload.orderId) {
      order = await this.#app.api.orders.get(payload.orderId);
    } else if (payload.printfulOrderId) {
      const { data: orders } = await this.#app.api.orders.list({
        limit: 100,
        tags: ['printful'],
        sortBy: 'created_at',
        order: 'desc'
      });
      order = (orders || []).find(o =>
        o.attributes?.some(a => a.key === 'printful_order_id' && String(a.value) === String(payload.printfulOrderId))
      );
    }

    if (!order) throw new PrintfulError('Order not found', 404);

    const pfOrderId = order.attributes?.find(a => a.key === 'printful_order_id')?.value;
    if (!pfOrderId) throw new PrintfulError('Order has no Printful id', 400);

    const { result: pfOrder } = await this.#client.getOrder(pfOrderId);
    const status = printfulOrderStatusToStorecraftStatus(pfOrder.status);

    const attr = order.attributes || [];
    const statusAttr = attr.find(a => a.key === 'printful_status');
    if (statusAttr) statusAttr.value = pfOrder.status;
    else attr.push({ key: 'printful_status', value: pfOrder.status });

    order.status = status;
    await this.#app.api.orders.upsert(order);
    console.log(`PrintfulExtension: synced order ${order.id} status to ${status}`);
    return { status };
  }

  async #buildVariantsMap(lineItems) {
    const map = {};
    for (const item of lineItems || []) {
      const product = await this.#app.api.products.get(item.id).catch(() => null);
      if (!product) continue;

      const target = product.parent_handle ? product : (product.variants || []).find(v => v.handle === item.id);
      if (!target) continue;

      const pfVariantId = target.attributes?.find(a => a.key === 'printful_variant_id')?.value;
      if (pfVariantId) map[item.id] = pfVariantId;
    }
    return map;
  }
}
