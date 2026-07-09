import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface Media {
  id: string;
  url: string;
  alt: string;
}

interface Props {
  medias: Media[];
  title: string;
}

export default function ProductGallery({ medias, title }: Props) {
  const [selected, setSelected] = useState(0);
  const images = medias.length > 0 ? medias : [];

  const next = () => setSelected((i) => (i + 1) % images.length);
  const prev = () => setSelected((i) => (i - 1 + images.length) % images.length);

  if (images.length === 0) {
    return (
      <div className="paper-frame aspect-square">
        <div className="flex h-full items-center justify-center rounded-xl bg-cream text-stone">
          No image
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <div className="paper-frame aspect-square">
          <img
            src={images[selected].url}
            alt={images[selected].alt || title}
            className="h-full w-full rounded-xl object-cover"
          />
        </div>

        {images.length > 1 && (
          <>
            <button
              onClick={prev}
              className="absolute left-3 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-earth/10 bg-cream/90 text-earth shadow-sm backdrop-blur-sm transition hover:bg-cream hover:shadow-md"
              aria-label="Previous image"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={next}
              className="absolute right-3 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-earth/10 bg-cream/90 text-earth shadow-sm backdrop-blur-sm transition hover:bg-cream hover:shadow-md"
              aria-label="Next image"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </>
        )}
      </div>

      {images.length > 1 && (
        <div className="flex gap-3 overflow-x-auto pb-2">
          {images.map((media, index) => (
            <button
              key={media.id}
              onClick={() => setSelected(index)}
              className={`relative flex-shrink-0 overflow-hidden rounded-xl border-2 transition ${
                selected === index
                  ? 'border-clay ring-1 ring-clay/30'
                  : 'border-transparent opacity-80 hover:opacity-100'
              }`}
              aria-label={`View ${media.alt || title} image ${index + 1}`}
            >
              <img
                src={media.url}
                alt={media.alt || title}
                className="h-20 w-20 object-cover md:h-24 md:w-24"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
