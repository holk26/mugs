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
| Almacenamiento de tokens | **Objetivo:** cookies `HttpOnly`/`Secure`/`SameSite=Strict` gestionadas por Django. **MVP pragmático:** access token en memoria (Zustand), refresh en `localStorage` solo si no se implementan cookies en la primera iteración, acompañado de CSP estricto en nginx. |
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
- **Estilos:** Tailwind CSS 4 con el plugin oficial `@tailwindcss/vite`. Temas y tokens definidos con `@theme` y variables CSS en `src/styles/global.css`, sin `tailwind.config.js`.
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
  - Botón "Sincronizar catálogo" que llama `POST /api/v1/admin/printful/sync/`. El backend encola la tarea (Celery/Django Q) y responde `202 Accepted` con el ID de la tarea.
  - Polling controlado desde el frontend hacia `GET /api/v1/admin/printful/logs/` (cada 3-5 s) para mostrar progreso en tiempo real.
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
| POST | `/printful/sync/` | Encolar tarea de sync de catálogo. Responde `202 Accepted` + `task_id`. |
| GET | `/printful/logs/` | Logs de sincronización (usado para polling de progreso). |
| GET | `/printful/webhooks/` | Eventos de webhook recibidos. |

### 6.1 Cambios en modelos

- Añadir `is_staff = models.BooleanField(default=False)` a `apps/users/models.py`.
- Actualizar migraciones.

### 6.2 Paginación, filtros y búsqueda

Todos los ViewSets de listado deben incluir:

```python
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

class AdminPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class AdminProductViewSet(viewsets.ModelViewSet):
    pagination_class = AdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'collections']
    search_fields = ['title', 'handle', 'description']
    ordering_fields = ['created_at', 'title', 'price']
```

El frontend enviará parámetros `page`, `page_size`, `search`, `ordering` y filtros correspondientes.

### 6.3 Cambios en settings

- Añadir origen del dashboard a `CORS_ALLOWED_ORIGINS`.
- Asegurar `DEFAULT_AUTHENTICATION_CLASSES` incluya `JWTAuthentication`.
- Configurar cola de tareas (Celery con Redis/RabbitMQ o Django Q) para el sync de Printful.
- Configurar cookies JWT `HttpOnly`/`Secure`/`SameSite=Strict` cuando se elija ese modo de auth.

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

### 8.1 Login

1. Usuario envía `POST /api/v1/auth/signin/`.
2. Backend responde `{ access, refresh, user }` (o setea cookies `HttpOnly`).
3. Frontend guarda `access` en `authStore` (memoria) y `refresh` en `localStorage` (si no hay cookies).
4. Interceptor de axios añade `Authorization: Bearer <access>`.
5. Ante `401`, se intenta refresh con `POST /api/v1/auth/refresh/`.
6. Si refresh falla, se limpian tokens y se redirige a `/login`.

### 8.2 Rehidratación tras F5 (anti "efecto F5")

El guardián de rutas (`__root.tsx` `beforeLoad`) no debe confiar solo en el estado de Zustand:

1. Verificar si existe `access` en memoria.
2. Si no existe, revisar `refresh` en `localStorage` (o cookie httpOnly).
3. Si hay refresh token, pausar la navegación y llamar silenciosamente a `/api/v1/auth/refresh/`.
4. Si el refresh es exitoso, guardar el nuevo `access` en Zustand y continuar.
5. Si falla, redirigir a `/login`.

Esto garantiza que la sesión sobreviva a recargas de página.

---

## 9. Manejo de errores y seguridad

- **Errores de red:** retry automático (3 intentos) con TanStack Query.
- **Errores de API (4xx/5xx):** toasts con mensaje del backend.
- **Validación de formularios:** `zod` en frontend; errores de campo mostrados junto a inputs.
- **Auth:** 403 muestra página de acceso denegado.
- **Errores de renderizado:** `ErrorBoundary` de TanStack Router con fallback amigable.
- **Seguridad de tokens:** si se usa `localStorage` para el refresh token en el MVP, el `nginx.conf` del dashboard debe incluir una **Content Security Policy (CSP)** estricta para mitigar riesgos XSS. La configuración ideal es usar cookies `HttpOnly`/`Secure`/`SameSite=Strict` gestionadas por Django.

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
- Configurar Tailwind CSS 4 con `@tailwindcss/vite` en `vite.config.ts` y temas mediante `@theme` en `src/styles/global.css`.
- Implementar cola de tareas desde el inicio para el sync de Printful; nunca ejecutar sync síncrono dentro del request/response.
