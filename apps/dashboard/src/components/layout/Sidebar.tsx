import { Link } from '@tanstack/react-router';
import { Button } from '@/components/ui/Button';
import { Package, ShoppingCart, RefreshCw, Home, Radio, TicketPercent, X } from 'lucide-react';

const nav = [
  { to: '/', label: 'Inicio', icon: Home },
  { to: '/products', label: 'Productos', icon: Package },
  { to: '/orders', label: 'Órdenes', icon: ShoppingCart },
  { to: '/discounts', label: 'Cupones', icon: TicketPercent },
  { to: '/printful', label: 'Printful', icon: RefreshCw },
  { to: '/printful/webhooks', label: 'Webhooks', icon: Radio },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-64 flex-col border-r border-stone-200 bg-white md:flex">
        <div className="flex h-16 items-center border-b border-stone-200 px-6">
          <span className="text-lg font-bold text-primary-700">Recuerdo Momentos</span>
        </div>
        <nav className="flex-1 space-y-1 p-4">
          {nav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium"
              activeProps={{ className: 'bg-primary-50 text-primary-700' }}
              inactiveProps={{ className: 'text-stone-600 hover:bg-stone-50 hover:text-primary-700' }}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Mobile drawer */}
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Menú de navegación"
        className={`fixed inset-y-0 left-0 z-50 flex w-[80%] max-w-xs flex-col border-r border-stone-200 bg-white shadow-xl transition-transform duration-200 ease-in-out md:hidden ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center justify-between border-b border-stone-200 px-4">
          <span className="text-lg font-bold text-primary-700">Recuerdo Momentos</span>
          <Button
            type="button"
            variant="secondary"
            size="icon"
            onClick={onClose}
            aria-label="Cerrar menú"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        <nav className="flex-1 space-y-1 p-4">
          {nav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              onClick={onClose}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium"
              activeProps={{ className: 'bg-primary-50 text-primary-700' }}
              inactiveProps={{ className: 'text-stone-600 hover:bg-stone-50 hover:text-primary-700' }}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
    </>
  );
}
