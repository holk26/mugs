import { useQuery } from '@tanstack/react-query';
import { listCollections } from '@/api/collections';

interface CollectionSelectProps {
  value: string[];
  onChange: (value: string[]) => void;
}

export function CollectionSelect({ value, onChange }: CollectionSelectProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['collections'],
    queryFn: listCollections,
  });

  if (isLoading) return <p className="text-sm text-stone-500">Cargando colecciones...</p>;

  return (
    <select
      multiple
      value={value}
      onChange={(e) => {
        const options = Array.from(e.target.selectedOptions).map((opt) => opt.value);
        onChange(options);
      }}
      className="input min-h-[120px]"
    >
      {data?.results.map((collection) => (
        <option key={collection.id} value={collection.id}>
          {collection.title}
        </option>
      ))}
    </select>
  );
}
