> Complemento al plan principal tras revisar `arquitectura.md`.

# Complemento de plan: visión de arquitectura y fases

Revisé `arquitectura.md`. El documento describe un ecosistema más amplio que el estado actual. El plan principal cubre los tres arreglos inmediatos (A, B, C), pero la arquitectura espera también:

1. **Pipeline de procesamiento con IA** para limpiar, quitar fondo y vectorizar el dibujo subido.
2. **Máquina de estados** de la orden: `Pendiente` → `Procesando IA` → `En Curación` → `Aprobado` → `Enviado a Producción`.
3. **Flujo de curación visual** en el dashboard: comparar "Antes y Después" y aprobar/rechazar/reemplazar el diseño.
4. **Envío a Printful solo tras aprobación**, usando la imagen procesada por IA, no el original.
5. **Multi-tenencia** por `store_id`, con `X-Store-ID` en las peticiones Astro → Django.
6. **Workers Celery** separados: Worker AI y Worker General.

## Propuesta de fases

### Fase 1 — Quick wins (ya en el plan principal)
- A. Dirección de envío en checkout.
- B. Persistir sesión del dashboard.
- C. Detalle de orden con ítems, dibujo y dirección.
- Además: corregir `SITE_URL` para URLs de upload.

### Fase 2 — Pipeline IA + curación (siguiente iteración grande)
- Crear cola Celery y worker AI.
- Al crear la orden, encolar tarea de procesamiento de imagen.
- Nuevos estados de orden: `processing_ai`, `in_curation`, `approved`, `sent_to_production`.
- Pantalla de curación en dashboard: comparar imagen original vs imagen IA, botones Aprobar / Rechazar / Reemplazar.
- Al aprobar, cambiar estado a `approved` y encolar envío a Printful con la imagen IA.
- Actualizar `push_order` para usar la imagen aprobada (`processed_upload`) en lugar del original.

### Fase 3 — Multi-tenencia
- Agregar `store_id` a productos, órdenes, webhooks, etc.
- Astro envía `X-Store-ID` en cada petición a la API.
- Dashboard filtra todo por tienda seleccionada.
- API keys de Printful dinámicas por tienda.

## Complemento inmediato al plan principal

Para no bloquear la Fase 1, se pueden agregar al plan actual dos tareas pequeñas que preparan el terreno para la Fase 2 sin implementarla toda:

### Tarea extra 1: Estado `processing_ai` y campo `processed_upload`

**Archivos:**
- Modify: `apps/django/apps/orders/models.py`
- Modify: `apps/django/apps/api/order_serializers.py`

- [ ] **Step 1: Extender estados de orden**

```python
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing_ai', 'Processing AI'),
    ('in_curation', 'In Curation'),
    ('approved', 'Approved'),
    ('sent_to_production', 'Sent to Production'),
    ('paid', 'Paid'),
    ('fulfilled', 'Fulfilled'),
    ('failed', 'Failed'),
    ('cancelled', 'Cancelled'),
]
```

- [ ] **Step 2: Agregar campo `processed_upload` a OrderLine**

```python
processed_upload = models.FileField(
    upload_to='drawings/processed/%Y/%m/%d/',
    blank=True,
    null=True,
    help_text='AI-processed drawing ready for production'
)
```

- [ ] **Step 3: Incluir en serializers**

```python
class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine
        fields = ['id', 'variant', 'title', 'quantity', 'price', 'customer_upload', 'processed_upload']
        read_only_fields = ['title', 'price']
```

- [ ] **Step 4: Crear y aplicar migración**

```bash
cd apps/django
python manage.py makemigrations orders
python manage.py migrate
```

- [ ] **Step 5: Commit**

```bash
git add apps/django/apps/orders/models.py apps/django/apps/api/order_serializers.py apps/django/apps/orders/migrations/
git commit -m "feat(orders): add processing_ai status and processed_upload field"
```

### Tarea extra 2: Cambiar `push_order` para usar imagen aprobada (fallback al original)

**Archivos:**
- Modify: `apps/django/apps/printful/sync.py`

- [ ] **Step 1: Usar `processed_upload` cuando exista**

```python
upload_file = line.processed_upload or line.customer_upload
if upload_file:
    absolute_url = upload_file.url
    if absolute_url.startswith('/'):
        from django.conf import settings
        absolute_url = f"{settings.SITE_URL.rstrip('/')}{absolute_url}"
    item['files'].append({
        'url': absolute_url,
        'type': 'default',
    })
```

- [ ] **Step 2: Commit**

```bash
git add apps/django/apps/printful/sync.py
git commit -m "feat(printful): prefer processed_upload over customer_upload in order push"
```

## Decisión de alcance

El plan principal + estas dos tareas extra dejan el sistema listo para:
- Recibir pagos con dirección de envío.
- Mostrar órdenes en el dashboard.
- Persistir sesión del admin.
- Enviar a Printful usando el dibujo original (hasta que exista el pipeline IA).

La Fase 2 (IA + curación) es un proyecto aparte que debería tener su propio spec y plan.
