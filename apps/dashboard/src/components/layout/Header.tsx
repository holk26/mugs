import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import { LogOut } from 'lucide-react';

export function Header() {
  const { user, logout } = useAuthStore();

  return (
    <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-white px-6">
      <h2 className="text-lg font-semibold text-stone-800">Panel de Administración</h2>
      <div className="flex items-center gap-4">
        <span className="text-sm text-stone-600">{user?.email}</span>
        <Button variant="secondary" onClick={logout} className="gap-2">
          <LogOut className="h-4 w-4" />
          Salir
        </Button>
      </div>
    </header>
  );
}
