# Diseño: Dashboard Admin SPA para Mugs

**Fecha:** 2026-06-24  
**Estado:** Aprobado para implementación  
**Alcance:** Fase 1 — Auth, Productos, Órdenes y Printful Sync  
**Fuera de alcance inmediato:** Agentes de IA (limpieza de fotos y comercial). Se tratarán en specs separados.

---

## 1. Resumen

Crear una SPA (`apps/dashboard`) para administrar la tienda Recuerdo Momentos. El dashboard se conecta al backend Django (`apps/django`) mediante una nueva API de administración bajo `/api/v1/admin/`, usa JWT para autenticación y se despliega como servicio independiente en Dokploy.

La primera fase incluye:
- Login con JWT + rol `is_staff`.
- CRUD de productos, variantes e imágenes.
- Gestión de órdenes (listado, detalle, cambio de estado).
- Sincronización con Printful (disparar sync y ver logs).

Los agentes de IA quedan documentados como requisitos futuros pero no se implementan en esta fase.

---

## 2. Contexto del proyecto

- `apps/web`: Astro 6 + React 19 + Tailwind 4. Storefront público.
- `apps/django`: Django + DRF. Backend API pública (`/api/v1/`) con productos, órdenes, pagos, Printful.
- `apps/dashboard`: **directorio vacío**, reservado para este trabajo.
- `packages/api-client`: cliente Storecraft legacy, **no se usa** en la web actual.

El backend ya tiene autenticación JWT (`/api/v1/auth/signin/`, `/api/v1/auth/refresh/`) pero no distingue admins ni expone operaciones de escritura para productos u órdenes.

---

## 3. Decisiones clave

| Tema | Decisión |
|------|----------|
| Tipo de app | SPA en Vite |
| Stack frontend | React 19 + TypeScript + Tailwind CSS 4 + `@tanstack/react-router` + `@tanstack/react-query` + `zustand` |
| UI components | Componentes propios con Tailwind (no MUI/Ant) |
| Formularios | `react-hook-form` + `zod` |
| Auth | JWT (`simplejwt`) + campo `is_staff` en `User` |
| Almacenamiento de tokens | Access token en memoria (Zustand); refresh token en `localStorage` para MVP |
| API backend | Nuevos endpoints bajo `/api/v1/admin/` usando ViewSets con permisos `IsAuthenticated` + `IsAdminUser` |
| Despliegue | Servicio `dashboard` independiente en `docker-compose.yml`/`docker-compose.dokploy.yml`, servido con nginx |
| Testing | Tests de ViewSets/serializadores en Django + tests de componentes/hooks con Vitest/RTL + smoke E2E con Playwright |

---

## 4. Arquitectura

```
┌─────────────────┐         ┌──────────────────────────┐
│  apps/dashboard │  JWT    │      apps/django         │
│  (Vite + React) │◄───────►│  /api/v1/admin/*         │
│                 │         │  /api/v1/auth/*          │
└─────────────────┘         └──────────────────────────┘
        │                              │
        │      Dokploy (contenedores)  │
        └──────────────────────────────┘
```

### 4.1 Frontend

- **Framework:** Vite 6 + React 19 + TypeScript.
- **Rutas:** `@tanstack/react-router` con `beforeLoad` para guardar auth.
- **Server state:** `@tanstack/react-query` con invalidación manual tras mutaciones.
- **Local state:** `zustand` para auth, UI (toasts, sidebar, modales).
- **Estilos:** Tailwind CSS 4, paleta coherente con `apps/web` pero más densa para tablas.
- **Iconos:** `lucide-react`.

### 4.2 Backend

- Extender `apps/api/urls.py` con prefijo `admin/`.
- Nuevos ViewSets en `apps/api/admin_views.py`.
- Serializadores admin en `apps/api/admin_serializers.py`.
- Permiso personalizado `IsAdminUser` basado en `is_staff`.

### 4.3 Despliegue

- `docker-compose.yml`: añadir servicio `dashboard` con build multi-stage (`node:22-alpine` → `nginx:alpine`).
- `docker-compose.dokploy.yml`: configuración específica para Dokploy.
- Variable `VITE_API_URL` apunta al backend en producción.
- Dokploy expone el servicio con su propio dominio (ej. `admin.tudominio.com`).

---

## 5. Funcionalidades (Fase 1)

### 5.1 Autenticación

- Pantalla `/login` con email y password.
- `POST /api/v1/auth/signin/`.
- Guardar tokens y redirigir a `/`.
- Si el usuario no es `is_staff`, mostrar 403.
- Refresco automático ante 401.

### 5.2 Home

- Métricas rápidas: órdenes del día, ingresos del día, productos activos, último sync Printful.
- Accesos directos a Productos, Órdenes y Printful.

### 5.3 Productos

- `/products`: tabla paginada con búsqueda, filtros (estado, colección) y ordenamiento.
- `/products/new`: formulario de creación (título, handle, descripción, precio base, estado, colecciones).
- `/products/:id`: edición con pestañas:
  - General
  - Variantes (listado + CRUD)
  - Imágenes (galería + upload)
- Acciones: publicar, archivar, eliminar.

### 5.4 Órdenes

- `/orders`: tabla paginada con filtros (estado, fecha, email).
- `/orders/:id`:
  - Datos del cliente, dirección, estado.
  - Líneas de orden con dibujos subidos.
  - Transacciones de pago.
  - Cambio de estado: pendiente → pagada → en preparación → enviada → entregada/cancelada.

### 5.5 Printful

- `/printful`:
  - Botón "Sincronizar catálogo" que llama `POST /api/v1/admin/printful/sync/`.
  - Tabla de `PrintfulSyncLog` con fecha, estado, mensajes.
  - Tabla de `PrintfulWebhookEvent` recientes.

---

## 6. Endpoints backend

Todos bajo `/api/v1/admin/` requieren `IsAuthenticated` + `IsAdminUser`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST | `/users/` | Listar/crear usuarios admin. |
| GET/PATCH/DELETE | `/users/<id>/` | Ver/editar/eliminar usuario. |
| GET/POST | `/products/` | Listar/crear productos (incluye inactivos). |
| GET/PATCH/DELETE | `/products/<id>/` | CRUD producto. |
| GET/POST | `/products/<id>/variants/` | Variantes de un producto. |
| GET/PATCH/DELETE | `/products/<id>/variants/<variant_id>/` | CRUD variante. |
| GET/POST | `/products/<id>/media/` | Imágenes de un producto. |
| GET/DELETE | `/products/<id>/media/<media_id>/` | Eliminar imagen. |
| GET | `/orders/` | Listar órdenes con filtros. |
| GET/PATCH | `/orders/<id>/` | Ver/actualizar orden. |
| GET | `/orders/<id>/lines/` | Líneas de orden. |
| POST | `/printful/sync/` | Ejecutar sync de catálogo (tarea síncrona o queue). |
| GET | `/printful/logs/` | Logs de sincronización. |
| GET | `/printful/webhooks/` | Eventos de webhook recibidos. |

### 6.1 Cambios en modelos

- Añadir `is_staff = models.BooleanField(default=False)` a `apps/users/models.py`.
- Actualizar migraciones.

### 6.2 Cambios en settings

- Añadir origen del dashboard a `CORS_ALLOWED_ORIGINS`.
- Asegurar `DEFAULT_AUTHENTICATION_CLASSES` incluya `JWTAuthentication`.

---

## 7. Estructura de archivos del frontend

```
apps/dashboard/
├── Dockerfile
├── nginx.conf
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── .env.example
└── src/
    ├── main.tsx
    ├── routeTree.gen.ts
    ├── api/
    │   ├── client.ts          # axios + interceptores
    │   ├── auth.ts            # login, refresh, logout
    │   ├── products.ts        # queries/mutations productos
    │   ├── orders.ts          # queries/mutations órdenes
    │   └── printful.ts        # sync + logs
    ├── components/
    │   ├── ui/                # Button, Input, Table, Modal, Toast...
    │   ├── layout/            # AppLayout, Sidebar, Header
    │   ├── products/          # ProductForm, VariantList, MediaGallery
    │   ├── orders/            # OrderDetail, OrderStatusBadge
    │   └── printful/          # PrintfulSyncPanel, PrintfulLogTable
    ├── routes/
    │   ├── __root.tsx
    │   ├── login.tsx
    │   ├── index.tsx
    │   ├── products.index.tsx
    │   ├── products.new.tsx
    │   ├── products.$id.tsx
    │   ├── orders.index.tsx
    │   ├── orders.$id.tsx
    │   └── printful.index.tsx
    ├── stores/
    │   ├── authStore.ts
    │   └── uiStore.ts
    ├── lib/
    │   ├── utils.ts
    │   └── schemas.ts         # zod schemas
    └── styles/
        └── global.css
```

---

## 8. Flujo de autenticación

1. Usuario envía `POST /api/v1/auth/signin/`.
2. Backend responde `{ access, refresh, user }`.
3. Frontend guarda `access` en `authStore` (memoria) y `refresh` en `localStorage`.
4. Interceptor de axios añade `Authorization: Bearer <access>`.
5. Ante `401`, se intenta refresh con `POST /api/v1/auth/refresh/`.
6. Si refresh falla, se limpian tokens y se redirige a `/login`.
7. `__root.tsx` verifica sesión en `beforeLoad`.

---

## 9. Manejo de errores

- **Errores de red:** retry automático (3 intentos) con TanStack Query.
- **Errores de API (4xx/5xx):** toasts con mensaje del backend.
- **Validación de formularios:** `zod` en frontend; errores de campo mostrados junto a inputs.
- **Auth:** 403 muestra página de acceso denegado.
- **Errores de renderizado:** `ErrorBoundary` de TanStack Router con fallback amigable.

---

## 10. Testing

### Backend
- Tests de permisos: usuarios no autenticados/no-admin rechazados.
- Tests de CRUD para cada ViewSet admin.
- Tests de serializadores con datos inválidos.

### Frontend
- Vitest + React Testing Library.
- Tests de componentes: `LoginForm`, `ProductForm`, `DataTable`.
- Tests de hooks: `useAuth`, `useProducts`.
- Al menos un test E2E con Playwright: login → navegar a productos → crear producto.

---

## 11. Requisitos futuros (fuera de esta fase)

- **Agente de limpieza de fotos con IA:** endpoint y worker en Django que procese los dibujos subidos automáticamente.
- **Agente comercial:** chatbot integrado al flujo de venta y al dashboard para responder a clientes.
- **Clientes:** CRUD completo de usuarios/clientes.
- **Pagos:** listado de transacciones y reembolsos manuales.
- **Configuración:** settings de tienda, pasarelas de pago, email.

---

## 12. Criterios de aceptación

- [ ] El dashboard compila y corre en `pnpm dev` en puerto separado.
- [ ] Un usuario admin puede iniciar sesión, ver productos, crear/editar/eliminar productos.
- [ ] Un usuario admin puede listar órdenes y cambiar su estado.
- [ ] Un usuario admin puede disparar sync de Printful y ver logs.
- [ ] Los endpoints admin rechazan a usuarios no autenticados o no `is_staff`.
- [ ] Los tests de backend pasan.
- [ ] El build del dashboard funciona en Docker y se despliega en Dokploy.

---

## 13. Notas de implementación

- Reutilizar estilos base de `apps/web` cuando sea posible, pero mantener la densidad de datos del admin.
- No modificar la API pública existente de `apps/web`; solo añadir endpoints admin.
- Mantener `packages/api-client` como legacy; el dashboard usa su propio cliente en `src/api/`.
