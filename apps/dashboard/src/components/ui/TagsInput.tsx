import { useState, useEffect } from 'react';
import { Input } from './Input';

interface TagsInputProps {
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
}

export function TagsInput({ value, onChange, placeholder }: TagsInputProps) {
  const [inputValue, setInputValue] = useState(value.join(', '));

  useEffect(() => {
    setInputValue(value.join(', '));
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    const tags = e.target.value
      .split(',')
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0);
    onChange(tags);
  };

  return (
    <Input
      value={inputValue}
      onChange={handleChange}
      placeholder={placeholder || 'tag1, tag2, tag3'}
    />
  );
}
