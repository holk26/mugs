import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LoginPage } from '@/routes/login';

vi.mock('@/api/auth', () => ({
  signIn: vi.fn().mockResolvedValue({
    access: 'a',
    refresh: 'r',
    user: { id: '1', email: 'a@b.com', first_name: '', last_name: '', is_staff: true },
  }),
}));

const queryClient = new QueryClient();

describe('LoginPage', () => {
  it('submits email and password', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <LoginPage />
      </QueryClientProvider>
    );
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'pass' } });
    fireEvent.click(screen.getByText('Entrar'));
    await waitFor(() => {
      expect(screen.queryByText('Credenciales inválidas')).not.toBeInTheDocument();
    });
  });
});
