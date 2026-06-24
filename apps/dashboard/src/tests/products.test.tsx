/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider, createMemoryHistory, createRouter } from '@tanstack/react-router';
import { routeTree } from '../routeTree.gen';
import { useAuthStore } from '@/stores/authStore';

vi.mock('@/api/products', () => ({
  listProducts: vi.fn().mockResolvedValue({ count: 1, next: null, previous: null, results: [{ id: '1', title: 'Mug', handle: 'mug', price: 10, status: 'active', created_at: '' }] }),
}));

const queryClient = new QueryClient();

function createTestRouter() {
  return createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: ['/products'] }),
    context: { queryClient },
  });
}

describe('ProductsPage', () => {
  beforeEach(() => {
    useAuthStore.setState({
      accessToken: 'token',
      user: { id: '1', email: 'test@test.com', first_name: '', last_name: '', is_staff: true },
    });
  });

  it('renders product title', async () => {
    const router = createTestRouter();
    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    );
    expect(await screen.findByText('Mug')).toBeInTheDocument();
  });
});

import { ProductForm } from '@/components/products/ProductForm';

describe('ProductForm', () => {
  it('shows validation errors', async () => {
    const onSubmit = vi.fn();
    render(<ProductForm onSubmit={onSubmit} />);
    fireEvent.click(screen.getByText('Guardar'));
    await waitFor(() => {
      expect(screen.getByText('El título es requerido')).toBeInTheDocument();
    });
  });
});
