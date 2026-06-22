/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly DJANGO_API_URL?: string;
  readonly CORE_API_URL?: string;
  readonly PUBLIC_STRIPE_PUBLISHABLE_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
