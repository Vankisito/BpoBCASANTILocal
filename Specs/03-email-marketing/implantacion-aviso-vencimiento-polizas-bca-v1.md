# Implantación: Aviso de Vencimiento de Pólizas vía Plantilla de Correo — BCA · Odoo 19

**Fecha:** 01/09/2026
**Autor:** Santiago Vásquez
**Ambiente destino:** `bca_prod` · Odoo `19.0-20260409`
**Alcance:** 100% operativo vía UX (plantilla de correo + server action + cron). **Sin módulos nuevos, sin campos nuevos.**

---

## 1. Objetivo

Enviar un correo al **contratante** de cada póliza `bca.poliza` que esté **a punto de vencer** (campo `fecha_fin`).

- Se usa **plantilla de correo** de Odoo (`mail.template`), **NO** Mass Mailing.
- Diferente del módulo de cumpleaños (`03-email-marketing/implantacion-cumpleanos-mass-mailing-bca-v1.md`): aquí el destinatario viene del propio registro (`contratante_id.email`), sin puentes ni listas.

---

## 2. Decisiones de diseño (confirgación acordada)

| Concepto | Valor |
|---|---|
| Anticipación | **15 días** antes de `fecha_fin` |
| Frecuencia | **Una sola vez** (dispara únicamente el día exacto en que `fecha_fin = hoy + 15`) |
| Estados incluidos | Solo **`activa`** (excluye `borrador`, `vencida`/expirada, `cancelada`) |
| Plantilla | Identificada por **nombre exacto** (`NOMBRE_PLANTILLA`) |
| Contratante | Mismo `res.partner` vinculado por `contratante_id`; se requiere `email` |

**Idempotencia sin campos nuevos:** al disparar un día exacto (igualdad `fecha_fin == hoy + 15`),
el cron nunca reenvía la misma póliza. Si la póliza se renueva (nuevo `fecha_fin`), se avisará de nuevo el siguiente año.

**Limitación conocida:** si el cron no corre un día (servidor caído), la póliza de ese día queda sin aviso (diseño "una sola vez" acordado).

---

## 3. Piezas implementadas (pendiente de crear en `bca_prod`)

| Pieza | Detalle |
|---|---|
| Plantilla `mail.template` | Sobre `bca.poliza`, `Para = {{ object.contratante_id.email }}` |
| Server action `bca_aviso_vencimiento` | `Execute Python Code` con código §4 |
| Scheduled action (cron) | Diario (`1 day`), hora deseada (ej. 07:00) |

---

## 4. Código (server action)

```python
AVISO_DIAS = 15
NOMBRE_PLANTILLA = 'Aviso vencimiento poliza'

hoy = datetime.date.today()
dia_aviso = hoy + datetime.timedelta(days=AVISO_DIAS)

plantilla = env['mail.template'].search([
    ('name', '=ilike', NOMBRE_PLANTILLA),
], limit=1)
if not plantilla:
    raise ValueError('No se encontró la plantilla "%s"' % NOMBRE_PLANTILLA)

polizas = env['bca.poliza'].search([
    ('estado', '=', 'activa'),
    ('fecha_fin', '=', dia_aviso),
    ('contratante_id.email', '!=', False),
])

for poliza in polizas:
    plantilla.send_mail(poliza.id, force_send=False)
```

**Restricciones server action respetadas (Odoo 19 `safe_eval`):** sin `import`, sin `STORE_ATTR`
(solo asignaciones locales `STORE_FAST`), `datetime`/`timedelta` vía módulo inyectado. Envío por
`send_mail(force_send=False)` → cola de `mail.mail`, entregada por el cron nativo
`Mail: Email Queue Manager`.

---

## 5. Configuración UX (paso a paso)

1. **Plantilla** (`Correos → Plantillas`):
   - `Aplicar a`: `bca.poliza` (Póliza BCA).
   - `Destinatarios (Para)`: `{{ object.contratante_id.email }}`.
   - `Asunto`: ej. `Su póliza {{ object.name }} vence el {{ object.fecha_fin }}`.
   - Cuerpo con placeholders `{{ object.name }}`, `{{ object.contratante_id.name }}`, `{{ object.fecha_fin }}`.
   - `Enviar desde` y servidor de correo correctos.
2. **Server action** `bca_aviso_vencimiento`: Ajustes → Técnico → Acciones → Acciones del servidor → tipo `Execute Python Code`, pegar §4.
3. **Cron** vinculado a la acción → interval_number `1`, interval_type **`days`**, hora deseada.

---

## 6. Casos de prueba

| # | Caso | Esperado |
|---|---|---|
| 1 | Póliza activa con `fecha_fin = hoy + 15` | ✓ envía correo al contratante |
| 2 | Póliza activa con `fecha_fin = hoy + 14` o `+16` | ✗ no envía |
| 3 | Póliza `borrador`/`expirada`/`cancelada` en ventana | ✗ no envía |
| 4 | Contratante sin `email` | ✗ se excluye |
| 5 | Re-ejecución mismo día | ✗ no duplica (disparo por igualdad exacta) |
| 6 | Plantilla no encontrada | ⚠️ error visible en log (min `ValueError`) |

---

## 7. Relación con la infraestructura SMTP

Mismo contexto que el módulo de cumpleaños: la entrega depende de los **servidores de correo saliente**.
- Revisar que el dominio del `Enviar desde` tenga servidor con `from_filter` (o que el primer server activo tenga credenciales válidas).
- Histórico: server id 16 `notificaciones@grupobca.com.mx` (`smtp.gmail.com:465`) devolvió
  `535 Bad Credentials` en 2026-09-01; validar `Test Connection` antes de la primera corrida real.
- (Entregabilidad) SPF/DKIM/DMARC → mejor entrega.

---

## 8. Pendientes

- [ ] Crear la plantilla de correo en `bca_prod` (nombre exacto `NOMBRE_PLANTILLA`).
- [ ] Crear server action `bca_aviso_vencimiento` con §4.
- [ ] Crear cron diario y definir hora.
- [ ] `Test Connection` del servidor SMTP y corrección de credenciales.