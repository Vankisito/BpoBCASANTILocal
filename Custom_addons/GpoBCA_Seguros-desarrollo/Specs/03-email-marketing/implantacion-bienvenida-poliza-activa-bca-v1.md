# Implantación: Bienvenida al Contratante al Activar Póliza — BCA · Odoo 19

**Fecha:** 02/09/2026
**Autor:** Santiago Vásquez
**Ambiente destino:** `bca_prod` · Odoo `19.0-20260409`
**Alcance:** 100% operativo vía UX (plantilla de correo + regla de automatización con acción "Execute Python Code"). **Sin módulos nuevos, sin campos nuevos, sin tocar `BCA_Seguros`.**

---

## 1. Objetivo

Enviar un correo de **bienvenida** al **contratante** de una póliza `bca.poliza` **en el instante** en que la póliza pasa al estado **`activa`** (Borrador → Activa, `action_confirmar()`).

- Se usa **plantilla de correo** de Odoo (`mail.template`), **NO** Mass Mailing.
- Diferente de los avisos por fecha (`implantacion-aviso-vencimiento-polizas-bca-v1.md`, `-recibos-`): aquí el disparador es un **evento transaccional inmediato** (cambio de `estado`), no una condición de calendario. Por eso se usa **regla de automatización** (`base.automation`), no un cron.
- El destinatario viene del propio registro (`contratante_id.email`), sin puentes ni listas.

---

## 2. Decisiones de diseño (configuración acordada)

| Concepto | Valor |
|---|---|
| Disparador | Cambio de `estado` de la póliza a **`activa`** (Borrador → Activa) |
| Mecanismo | **Regla de automatización** (`base.automation`) + acción tipo **"Execute Python Code"** con envío por `mail.template.send_mail` (§4) |
| Trigger | **Al actualizar** (`on_write` / `on_create_or_write`) sobre el campo `estado` (`trigger_field_ids` = `estado`) |
| Condición (dominio) | `[('estado', '=', 'activa')]` |
| Estados excluidos | `borrador`, `vencida`/expirada, `cancelada` |
| Destinatario | Contratante (`contratante_id.email`); se requiere `email` |
| Plantilla | Referenciada por **ID** (`PLANTILLA_ID = 41` en `bca_prod`), no por nombre (evita colisiones) |
| Idempotencia | Sin campos nuevos: el trigger solo se dispara al **cambiar** `estado` a `activa`; reescribir una póliza ya activa (sin tocar `estado`) **no** reenvía. Sin duplicados |

**Idempotencia sin campos nuevos:** al monitorizar el campo `estado` con dominio `estado = activa`,
la regla se dispara únicamente en la transición a `activa`. No se requiere flag ni fecha de envío.

**Nota:** si a futuro se quisiera "reenviar manualmente" la bienvenida, se haría con el botón de
correo nativo del chatter de la póliza (ya activa), sin implicar a la automatización.

---

## 3. Piezas implementadas (pendiente de crear en `bca_prod`)

| Pieza | Detalle |
|---|---|
| Plantilla `mail.template` | Sobre `bca.poliza`, `Para = {{ object.contratante_id.email }}` |
| Regla de automatización | `base.automation`, trigger campo `estado`, dominio `estado = activa`, acción "Execute Python Code" (código §4) |
| Server action (acción de la regla) | `bca_bienvenida_poliza_activa`, estado `code`, modelo `bca.poliza`, código §4 — recibe `records` solo con la póliza disparada |

---

## 4. Código (acción "Execute Python Code" de la regla de §5)

> Esta acción es la que ejecuta la regla de automatización de §5. No es una alternativa: es el
> mecanismo de envío acordado. Recibe en `records` **solo** la póliza que disparó la transición a
> `activa` → no barre la cartera, no reenvía a pólizas ya activas.

```python
PLANTILLA_ID = 41   # bca_prod: 'BCA Bienvenida póliza activa' (verificar id real)

plantilla = env['mail.template'].browse(PLANTILLA_ID)
if not plantilla:
    raise ValueError('Plantilla de bienvenida no encontrada (id %s)' % PLANTILLA_ID)

for poliza in records:
    if not poliza.contratante_id.email:
        continue            # sin email → no envía, no rompe
    plantilla.send_mail(poliza.id, force_send=False)
```

**Restricciones server action respetadas (Odoo 19 `safe_eval`):** sin `import`, sin atributos
(solo asignaciones locales `STORE_FAST`), `continue` permitido. Envío por `send_mail(force_send=False)`
→ cola de `mail.mail`, entregada por el cron nativo `Mail: Email Queue Manager`.

**Idempotencia sin campos nuevos:** base.automation dispara solo en el cambio de `estado` a `activa`
(monitoreo del campo derivado del dominio, ver §5.2); su mecanismo interno `__action_done` bloquea
re-procesos. Cero duplicados.

---

## 5. Configuración UX (paso a paso)

### 5.1 Plantilla de correo (`Correos → Plantillas` → Nuevo)

- **Aplicar a:** `bca.poliza` (Póliza BCA).
- **Destinatarios (Para):** `{{ object.contratante_id.email }}`
- **Asunto:** `¡Bienvenido a BCA! Su póliza {{ object.name }} ya está activa`
- **Cuerpo** (QWeb, forma sugerida):

```
Estimado/a {{ object.contratante_id.name }}:

¡Bienvenido a Grupo BCA! Le confirmamos que su póliza se encuentra ACTIVA.

Datos de su póliza:
  - Número de póliza:      {{ object.name }}
  - Aseguradora:           {{ object.aseguradora_id.name }}
  - Producto:              {{ object.producto_id.name }}
  - Plan:                  {{ object.plan }}
  - Periodicidad:          {{ object.periodicidad }}
  - Fecha de inicio:       {{ object.fecha_inicio }}
  - Fecha de fin:          {{ object.fecha_fin }}
  - Prima anual:           {{ object.prima_anual }}

Para cualquier duda sobre su cobertura o cobros, puede contactar a su agente:
  {{ object.agente_id.name }}
  {{ object.agente_id.email or '' }}

Atentamente,
Grupo BCA
```

- **Enviar desde** y servidor de correo correctos (ver §7).

### 5.2 Regla de automatización (`Ajustes → Técnico → Automatización → Reglas de automatización` → Nuevo)

1. **Nombre:** `BCA: Bienvenida al activar póliza`
2. **Modelo:** `bca.poliza` (Póliza BCA).
3. **Trigger** → **Al actualizar** (o `Al crear o actualizar` si se desea cubrir creaciones directas en activa):
   - En **"Monitorizar el campo"** seleccionar **`estado`**.
4. **Condición (dominio):** `[('estado', '=', 'activa')]`
5. **Acciones a realizar** → **Añadir una acción**:
   - **Tipo:** **"Execute Python Code"** (código §4).
   - **Modelo:** `bca.poliza` (debe coincidir con el de la regla).
   - **Código:** el de §4 con `PLANTILLA_ID = 41`.
6. Guardar y **activar** la regla.

### 5.3 Nota sobre la acción

La acción "Execute Python Code" de §4 se crea dentro de la regla (paso 5.2). Si se prefiere crearla
aparte desde `Ajustes → Técnico → Acciones → Acciones del servidor` (tipo `Execute Python Code`,
modelo `bca.poliza`, código §4), luego se enlaza a la regla. En cualquier caso debe tener el mismo
modelo que la regla (la validación `_check_action_server_model` lo exige).

---

## 6. Casos de prueba

| # | Caso | Esperado |
|---|---|---|
| 1 | Póliza `borrador` → `activa`, contratante con `email` | ✓ envía correo al contratante al instante |
| 2 | Póliza creada y dejada en `borrador` | ✗ no envía |
| 3 | Póliza `activa` → `cancelada` o `vencida` | ✗ no envía |
| 4 | Contratante sin `email` | ✗ no envía (destinatario vacío) |
| 5 | Re-edición de póliza ya `activa` sin cambiar `estado` | ✗ no reenvía (trigger solo al cambio de `estado`) |
| 6 | Cambio de `estado` a valor distinto de `activa` | ✗ no envía |
| 7 | Nueva póliza creada directamente en `activa` | ✓ envía (trigger `on_create_or_write` cubre creación y actualización) |
| 8 | Plantilla no encontrada (id 41 inexistente/borrada) | ⚠️ `raise ValueError`; error visible en log del server action |

---

## 7. Relación con la infraestructura SMTP

Misma base que los avisos previos: la entrega depende de los **servidores de correo saliente**.

- Revisar que el dominio del `Enviar desde` tenga servidor con `from_filter` (o que el primer server activo tenga credenciales válidas).
- Histórico: server id 16 `notificaciones@grupobca.com.mx` (`smtp.gmail.com:465`) devolvió
  `535 Bad Credentials` en 2026-09-01; validar `Test Connection` antes de la primera corrida real.
- (Entregabilidad) SPF/DKIM/DMARC → mejor entrega.

---

## 8. Pendientes

- [ ] Verificar que el id 41 de `bca_prod` sea la plantilla 'BCA Bienvenida póliza activa' sobre `bca.poliza`.
- [ ] Crear la plantilla de correo en `bca_prod` (nombre `BCA Bienvenida póliza activa`).
- [ ] Crear la regla de automatización en `bca_prod` (trigger `Al crear y actualizar`, dominio `estado = activa`, acción "Execute Python Code" con §4).
- [ ] `Test Connection` del servidor SMTP y corrección de credenciales.
- [ ] Probar caso 1 de §6 end-to-end (confirmar una póliza y verificar el correo en el buzón del contratante).
