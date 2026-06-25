import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TagsInput } from './TagsInput';

describe('TagsInput', () => {
  it('renders comma separated tags', () => {
    render(<TagsInput value={['printful', 'mug']} onChange={vi.fn()} />);
    expect(screen.getByDisplayValue('printful, mug')).toBeInTheDocument();
  });

  it('calls onChange with parsed tags', () => {
    const onChange = vi.fn();
    render(<TagsInput value={[]} onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'a, b, c' } });
    expect(onChange).toHaveBeenCalledWith(['a', 'b', 'c']);
  });
});
