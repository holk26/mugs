import { useState } from 'react';
import { ShoppingBag, Menu, X } from 'lucide-react';
import { useCart } from '../stores/cart';
import CartDrawer from './CartDrawer';

export default function Header() {
  const [isOpen, setIsOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const count = useCart((s) => s.items.reduce((sum, i) => sum + i.quantity, 0));

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-neutral-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <a href="/" className="text-xl font-semibold tracking-tight text-neutral-900">
            Recuerdo Momentos
          </a>

          <nav className="hidden items-center gap-8 md:flex">
            <a href="/products" className="text-sm font-medium text-neutral-600 hover:text-neutral-900">
              Shop
            </a>
            <a href="/cart" className="text-sm font-medium text-neutral-600 hover:text-neutral-900">
              Cart
            </a>
          </nav>

          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsOpen(true)}
              className="relative rounded-full p-2 hover:bg-neutral-100"
              aria-label="Open cart"
            >
              <ShoppingBag className="h-5 w-5 text-neutral-700" />
              {count > 0 && (
                <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-orange-700 text-[10px] font-bold text-white">
                  {count}
                </span>
              )}
            </button>
            <button
              className="md:hidden"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {mobileOpen && (
          <div className="border-t border-neutral-200 px-4 py-4 md:hidden">
            <a href="/products" className="block py-2 text-neutral-700">Shop</a>
            <a href="/cart" className="block py-2 text-neutral-700">Cart</a>
          </div>
        )}
      </header>

      <CartDrawer isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
}
