import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProductVariantsTab } from './ProductVariantsTab';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

describe('ProductVariantsTab', () => {
  it('renders loading state', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ProductVariantsTab productId="test-product" />
      </QueryClientProvider>
    );
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
  });
});
