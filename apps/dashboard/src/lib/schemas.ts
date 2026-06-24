import { z } from 'zod';

export const signInSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'La contraseña es requerida'),
});

export type SignInInput = z.infer<typeof signInSchema>;

export const productSchema = z.object({
  handle: z.string().min(1, 'El handle es requerido'),
  title: z.string().min(1, 'El título es requerido'),
  description: z.string().optional(),
  status: z.enum(['draft', 'active', 'archived']),
  price: z.coerce.number().min(0),
  compare_at_price: z.coerce.number().min(0).optional().nullable(),
  tags: z.array(z.string()).default([]),
});

export type ProductInput = z.infer<typeof productSchema>;
