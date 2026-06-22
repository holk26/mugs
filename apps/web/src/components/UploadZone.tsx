import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload } from 'lucide-react';

interface Props {
  onFile: (file: File) => void;
  preview?: string;
}

export default function UploadZone({ onFile, preview }: Props) {
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

  return (
    <div
      {...getRootProps()}
      className={`cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition ${
        isDragActive ? 'border-orange-700 bg-orange-50' : 'border-neutral-300 hover:border-neutral-400'
      }`}
    >
      <input {...getInputProps()} />
      {preview ? (
        <img src={preview} alt="Preview" className="mx-auto h-32 object-contain" />
      ) : (
        <>
          <Upload className="mx-auto h-8 w-8 text-neutral-400" />
          <p className="mt-2 text-sm font-medium text-neutral-700">
            {isDragActive ? 'Drop the drawing here' : 'Drag & drop a drawing, or click to select'}
          </p>
          <p className="mt-1 text-xs text-neutral-500">PNG, JPG, WEBP or PDF up to 10MB</p>
        </>
      )}
    </div>
  );
}
