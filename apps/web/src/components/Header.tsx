import { useState } from 'react';
import { ShoppingBag, Menu, X } from 'lucide-react';
import { useCart } from '../stores/cart';
import CartDrawer from './CartDrawer';

export default function Header() {
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const count = useCart((s) => s.items.reduce((sum, i) => sum + i.quantity, 0));

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-orange-100/80 bg-white/85 backdrop-blur-md">
        <div className="section flex h-16 items-center justify-between">
          <a href="/" className="bg-gradient-to-r from-orange-600 to-amber-500 bg-clip-text text-lg font-bold tracking-tight text-transparent">
            Recuerdo Momentos
          </a>

          <nav className="hidden items-center gap-8 md:flex">
            <a href="/products" className="text-sm font-medium text-stone-600 hover:text-stone-900">
              Shop
            </a>
            <a href="/cart" className="text-sm font-medium text-stone-600 hover:text-stone-900">
              Cart
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsCartOpen(true)}
              className="relative flex h-10 w-10 items-center justify-center rounded-full transition hover:bg-orange-50"
              aria-label="Open cart"
            >
              <ShoppingBag className="h-5 w-5 text-stone-700" strokeWidth={1.5} />
              {count > 0 && (
                <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-orange-700 px-1 text-[10px] font-semibold text-white">
                  {count}
                </span>
              )}
            </button>
            <button
              className="flex h-10 w-10 items-center justify-center rounded-full transition hover:bg-orange-50 md:hidden"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {mobileOpen && (
          <div className="border-t border-orange-100 bg-white px-4 py-4 md:hidden">
            <a href="/products" className="block py-3 text-base font-medium text-stone-700">
              Shop
            </a>
            <a href="/cart" className="block py-3 text-base font-medium text-stone-700">
              Cart
            </a>
          </div>
        )}
      </header>

      <CartDrawer isOpen={isCartOpen} onClose={() => setIsCartOpen(false)} />
    </>
  );
}
