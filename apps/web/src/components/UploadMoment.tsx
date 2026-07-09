import { useState } from 'react';
import UploadZone from './UploadZone';

export default function UploadMoment() {
  const [preview, setPreview] = useState<string>('');

  const handleFile = (file: File) => {
    const blobUrl = URL.createObjectURL(file);
    setPreview(blobUrl);
    const reader = new FileReader();
    reader.onloadend = () => {
      const dataUrl = reader.result as string;
      setPreview(dataUrl);
      URL.revokeObjectURL(blobUrl);
    };
    reader.readAsDataURL(file);
  };

  const handleClear = () => {
    setPreview('');
  };

  return (
    <div className="mx-auto max-w-xl rounded-2xl bg-white/10 p-2 ring-1 ring-white/10">
      <div className="rounded-xl bg-white p-4 md:p-6">
        <UploadZone onFile={handleFile} preview={preview} onClear={handleClear} />
        {preview && (
          <div className="mt-4 flex items-center justify-center gap-4">
            <a href="/products" className="btn-primary w-full text-center">
              Pick a mug
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
