import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X } from 'lucide-react';

interface Props {
  onFile: (file: File) => void;
  preview?: string;
  onClear?: () => void;
}

export default function UploadZone({ onFile, preview, onClear }: Props) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles[0]) onFile(acceptedFiles[0]);
    },
    [onFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.webp'], 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  if (preview) {
    return (
      <div className="relative overflow-hidden rounded-2xl border border-earth/10 bg-cream p-2">
        <img src={preview} alt="Preview" className="h-64 w-full rounded-xl object-contain" />
        {onClear && (
          <button
            onClick={onClear}
            className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-white text-earth shadow-sm transition hover:text-clay"
            aria-label="Remove file"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition ${
        isDragActive
          ? 'border-clay bg-clay/5'
          : 'border-earth/20 bg-cream hover:border-clay'
      }`}
    >
      <input {...getInputProps()} />
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-sand shadow-sm">
        <Upload className="h-5 w-5 text-earth" />
      </div>
      <p className="mt-4 text-sm font-semibold text-earth">
        {isDragActive ? 'Drop the drawing here' : 'Click or drag drawing here'}
      </p>
      <p className="mt-1 text-xs text-stone">PNG, JPG, WEBP or PDF up to 10MB</p>
    </div>
  );
}
