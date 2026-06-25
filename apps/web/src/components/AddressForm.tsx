import { PRINTFUL_COUNTRIES } from '@/lib/countries';

export interface AddressFormData {
  address1: string;
  city: string;
  state_code: string;
  zip: string;
  country_code: string;
}

interface AddressFormProps {
  value: AddressFormData;
  onChange: (value: AddressFormData) => void;
  disabled?: boolean;
}

const inputClasses =
  'mt-1 w-full rounded-xl border border-stone-200 bg-stone-50 px-4 py-2.5 text-sm outline-none transition focus:border-orange-700 focus:bg-white focus:ring-1 focus:ring-orange-700';

export function AddressForm({ value, onChange, disabled }: AddressFormProps) {
  const update = (field: keyof AddressFormData, fieldValue: string) => {
    onChange({ ...value, [field]: fieldValue });
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-stone-700">Address</label>
        <input
          type="text"
          value={value.address1}
          onChange={(e) => update('address1', e.target.value)}
          disabled={disabled}
          required
          autoComplete="address-line1"
          className={inputClasses}
          placeholder="123 Main St"
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-stone-700">City</label>
          <input
            type="text"
            value={value.city}
            onChange={(e) => update('city', e.target.value)}
            disabled={disabled}
            required
            autoComplete="address-level2"
            className={inputClasses}
            placeholder="Austin"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-stone-700">State / Province</label>
          <input
            type="text"
            value={value.state_code}
            onChange={(e) => update('state_code', e.target.value)}
            disabled={disabled}
            required
            autoComplete="address-level1"
            className={inputClasses}
            placeholder="TX"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-stone-700">Postal code</label>
          <input
            type="text"
            value={value.zip}
            onChange={(e) => update('zip', e.target.value)}
            disabled={disabled}
            required
            autoComplete="postal-code"
            className={inputClasses}
            placeholder="78701"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-stone-700">Country</label>
          <select
            value={value.country_code}
            onChange={(e) => update('country_code', e.target.value)}
            disabled={disabled}
            required
            autoComplete="country"
            className={inputClasses}
          >
            <option value="">Select country</option>
            {PRINTFUL_COUNTRIES.map((country) => (
              <option key={country.code} value={country.code}>
                {country.name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
