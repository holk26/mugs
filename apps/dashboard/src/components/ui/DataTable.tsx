interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  isLoading?: boolean;
}

export function DataTable<T>({ columns, data, keyExtractor, isLoading }: DataTableProps<T>) {
  return (
    <div className="overflow-hidden rounded-xl border border-stone-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-stone-200">
        <thead className="bg-stone-50">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-stone-500">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-stone-200">
          {isLoading ? (
            <tr><td colSpan={columns.length} className="px-6 py-8 text-center text-stone-500">Cargando...</td></tr>
          ) : data.length === 0 ? (
            <tr><td colSpan={columns.length} className="px-6 py-8 text-center text-stone-500">No hay datos</td></tr>
          ) : (
            data.map((row) => (
              <tr key={keyExtractor(row)} className="hover:bg-stone-50">
                {columns.map((col) => (
                  <td key={col.key} className="whitespace-nowrap px-6 py-4 text-sm text-stone-900">
                    {col.render ? col.render(row) : (row as Record<string, unknown>)[col.key] as React.ReactNode}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
