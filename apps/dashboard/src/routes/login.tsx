import { createFileRoute, redirect } from '@tanstack/react-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { signIn } from '@/api/auth';
import { useAuthStore } from '@/stores/authStore';
import { signInSchema, type SignInInput } from '@/lib/schemas';

export const Route = createFileRoute('/login')({
  component: LoginPage,
  beforeLoad: () => {
    if (useAuthStore.getState().accessToken) {
      throw redirect({ to: '/' });
    }
  },
});

export function LoginPage() {
  const { register, handleSubmit, formState: { errors } } = useForm<SignInInput>({
    resolver: zodResolver(signInSchema),
  });
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = Route.useNavigate();

  const mutation = useMutation({
    mutationFn: signIn,
    onSuccess: (data) => {
      setAuth(data.access, data.refresh, data.user);
      navigate({ to: '/' });
    },
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-stone-100 p-4">
      <div className="w-full max-w-sm card">
        <h1 className="mb-6 text-2xl font-bold text-stone-900">Admin Recuerdo Momentos</h1>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
          <div>
            <label htmlFor="email" className="label">Email</label>
            <input {...register('email')} id="email" type="email" className="input" />
            {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>}
          </div>
          <div>
            <label htmlFor="password" className="label">Contraseña</label>
            <input {...register('password')} id="password" type="password" className="input" />
            {errors.password && <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>}
          </div>
          {mutation.isError && <p className="text-sm text-red-600">Credenciales inválidas</p>}
          <button type="submit" disabled={mutation.isPending} className="btn-primary w-full">
            {mutation.isPending ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  );
}
