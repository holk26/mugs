import { Link } from '@tanstack/react-router';

export default function Footer() {
  return (
    <footer className="border-t border-orange-100 bg-gradient-to-b from-white to-orange-50/60">
      <div className="section py-12">
        <div className="grid gap-8 md:grid-cols-3">
          <div>
            <p className="bg-gradient-to-r from-orange-600 to-amber-500 bg-clip-text text-lg font-bold tracking-tight text-transparent">
              Recuerdo Momentos
            </p>
            <p className="mt-2 text-sm leading-relaxed text-stone-500">
              Custom mugs made from children's drawings. A keepsake for every little artist.
            </p>
          </div>
          <div>
            <p className="text-sm font-semibold text-stone-900">Shop</p>
            <ul className="mt-3 space-y-2 text-sm text-stone-500">
              <li><Link to="/products" className="hover:text-stone-900">All mugs</Link></li>
              <li><Link to="/cart" className="hover:text-stone-900">Cart</Link></li>
            </ul>
          </div>
          <div>
            <p className="text-sm font-semibold text-stone-900">Stay in touch</p>
            <p className="mt-2 text-sm text-stone-500">Join for updates and new designs.</p>
            <div className="mt-3 flex gap-2">
              <input
                type="email"
                placeholder="your@email.com"
                className="flex-1 rounded-full border border-orange-200 bg-white px-4 py-2 text-sm outline-none focus:border-orange-600"
              />
              <button className="btn-primary px-4 py-2">Join</button>
            </div>
          </div>
        </div>
        <div className="mt-12 border-t border-stone-200 pt-6 text-sm text-stone-400">
          © {new Date().getFullYear()} Recuerdo Momentos. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
