import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import { LogOut, Menu } from 'lucide-react';

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuthStore();

  return (
    <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-white px-4 md:px-6">
      <div className="flex items-center gap-3">
        <Button variant="secondary" onClick={onMenuClick} className="md:hidden" aria-label="Abrir menú">
          <Menu className="h-5 w-5" />
        </Button>
        <h2 className="text-base font-semibold text-stone-800 md:text-lg">Panel de Administración</h2>
      </div>
      <div className="flex items-center gap-4">
        <span className="hidden text-sm text-stone-600 md:inline">{user?.email}</span>
        <Button variant="secondary" onClick={logout} className="gap-2 px-2 md:px-4" aria-label="Salir">
          <LogOut className="h-4 w-4" />
          <span className="hidden md:inline">Salir</span>
        </Button>
      </div>
    </header>
  );
}
