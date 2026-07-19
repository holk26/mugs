import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { CartItem } from '../lib/api';

const safeLocalStorage = {
  getItem: (name: string) => {
    try {
      return localStorage.getItem(name);
    } catch {
      return null;
    }
  },
  setItem: (name: string, value: string) => {
    try {
      localStorage.setItem(name, value);
    } catch {
      // Quota exceeded (large drawing previews) or storage unavailable: warn
      // the user instead of silently losing the cart/drawing.
      console.warn('Cart could not be persisted to localStorage (quota exceeded?)');
      window.dispatchEvent(new CustomEvent('recuerdo:cart-storage-error'));
    }
  },
  removeItem: (name: string) => {
    try {
      localStorage.removeItem(name);
    } catch {
      // ignore
    }
  },
};

interface CartState {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (variantId: string) => void;
  updateQuantity: (variantId: string, quantity: number) => void;
  updateUpload: (variantId: string, uploadPreview: string, uploadName: string) => void;
  clearCart: () => void;
  total: () => number;
}

export const useCart = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      addItem: (item) => {
        const existing = get().items.find((i) => i.variantId === item.variantId);
        if (existing) {
          set({
            items: get().items.map((i) =>
              i.variantId === item.variantId
                ? { ...i, quantity: i.quantity + item.quantity }
                : i
            ),
          });
        } else {
          set({ items: [...get().items, item] });
        }
      },
      removeItem: (variantId) =>
        set({ items: get().items.filter((i) => i.variantId !== variantId) }),
      updateQuantity: (variantId, quantity) =>
        set({
          items: get().items.map((i) =>
            i.variantId === variantId
              ? { ...i, quantity: Math.max(1, Math.min(99, quantity)) }
              : i
          ),
        }),
      updateUpload: (variantId, uploadPreview, uploadName) =>
        set({
          items: get().items.map((i) =>
            i.variantId === variantId ? { ...i, uploadPreview, uploadName } : i
          ),
        }),
      clearCart: () => set({ items: [] }),
      total: () =>
        get().items.reduce((sum, item) => sum + item.price * item.quantity, 0),
    }),
    {
      name: 'recuerdo-cart',
      storage: createJSONStorage(() => safeLocalStorage),
      partialize: (state) => ({
        items: state.items,
      }),
    }
  )
);
