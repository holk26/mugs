import { createRootRoute, Outlet, redirect } from '@tanstack/react-router';
import { useAuthStore } from '@/stores/authStore';
import { refreshToken } from '@/api/auth';

export const Route = createRootRoute({
  component: RootComponent,
  beforeLoad: async ({ location }) => {
    const publicRoutes = ['/login'];
    const isPublic = publicRoutes.includes(location.pathname);
    const store = useAuthStore.getState();

    if (!store.accessToken) {
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { access } = await refreshToken(refresh);
          store.setAccessToken(access);
        } catch {
          store.logout();
          if (!isPublic) throw redirect({ to: '/login' });
        }
      } else if (!isPublic) {
        throw redirect({ to: '/login' });
      }
    }

    if (store.user && !store.user.is_staff && !isPublic) {
      throw redirect({ to: '/login' });
    }
  },
});

function RootComponent() {
  return <Outlet />;
}
