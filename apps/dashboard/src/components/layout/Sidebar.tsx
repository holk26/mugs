import { Link } from '@tanstack/react-router';
import { Package, ShoppingCart, RefreshCw, Home } from 'lucide-react';

const nav = [
  { to: '/', label: 'Inicio', icon: Home },
  { to: '/products', label: 'Productos', icon: Package },
  { to: '/orders', label: 'Órdenes', icon: ShoppingCart },
  { to: '/printful', label: 'Printful', icon: RefreshCw },
];

export function Sidebar() {
  return (
    <aside className="flex w-64 flex-col border-r border-stone-200 bg-white">
      <div className="flex h-16 items-center border-b border-stone-200 px-6">
        <span className="text-lg font-bold text-primary-700">Recuerdo Momentos</span>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {nav.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-stone-600 hover:bg-stone-50 hover:text-primary-700"
            activeProps={{ className: 'bg-primary-50 text-primary-700' }}
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
