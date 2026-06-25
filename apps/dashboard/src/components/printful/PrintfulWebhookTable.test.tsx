import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PrintfulWebhookTable } from './PrintfulWebhookTable';

const events = [
  {
    id: '1',
    event_type: 'product_updated',
    payload: { id: 123 },
    processed: false,
    created_at: '2026-06-24T00:00:00Z',
  },
];

describe('PrintfulWebhookTable', () => {
  it('renders event and opens modal', () => {
    render(<PrintfulWebhookTable events={events} />);
    expect(screen.getByText('product_updated')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Ver payload'));
    expect(screen.getByText((content) => content.includes('"id": 123'))).toBeInTheDocument();
  });
});
