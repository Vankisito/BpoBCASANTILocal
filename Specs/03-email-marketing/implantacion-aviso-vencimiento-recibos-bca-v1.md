# Implantación: Aviso de Vencimiento de Recibos vía Plantilla de Correo — BCA · Odoo 19

**Fecha:** 02/09/2026 (rev. chatter no-envío)
**Ambiente destino:** `bca_prod`
**Alcance:** 100% operativo vía UX (plantilla de correo + server action + cron). **Sin módulos nuevos, sin campos nuevos.** Los no-envíos se registran en el chatter de cada recibo.

---

## 1. Objetivo

Enviar un correo de aviso al **contratante** cuando un recibo de póliza `bca.recibo` esté **a punto de vencer**.

- Se usa **plantilla de correo** de Odoo (`mail.template`), **NO** Mass Mailing.
- El disparador es el campo **`fecha_desde` (Cobertura Desde)** del recibo: se avisa **15 días antes**.
- Complementa el aviso de vencimiento de pólizas (`implantacion-aviso-vencimiento-polizas-bca-v1.md`): aquí se avisa del **cobro** del siguiente período de cobertura.

---

## 2. Decisiones de diseño (configuración acordada)

| Concepto | Valor |
|---|---|
| Condición | Recibo **`pendiente`** (no pagado, no cancelado) |
| Campo disparador | **`fecha_desde`** (Cobertura Desde) |
| Anticipación | **15 días** antes (`fecha_desde = hoy + 15`) |
| Frecuencia | **Una sola vez** (día exacto de coincidencia; sin duplicados ni recordatorio diario) |
| Póliza | Solo estado **`activa`** (`poliza_id.estado = 'activa'`) |
| Destinatario | **Contratante** de la póliza del recibo (`poliza_id.contratante_id.email`) |
| Plantilla | Identificada por **ID** (`PLANTILLA_ID = 42`, nombre `Aviso vencimiento recibo`) |
| No-envío en chatter | Cada recibo en ventana que NO envía queda registrado en su chatter (`message_post`) con la causa |

**Idempotencia sin campos nuevos:** al disparar por igualdad exacta de fechas (`fecha_desde == hoy + 15`),
el cron no reenvía el mismo recibo en días distintos. Alcance exacto: si el cron se re-ejecuta el **mismo
día**, reenvía (el recibo sigue en la ventana); en `bca_prod` solo el cron diario lo dispara (sin re-run
manual por permisos), así que 1 ejecución diaria = 1 correo. Si el cron no corre un día, ese recibo no se
avisa (diseño acordado).

---

## 3. Piezas implementadas (pendiente de crear en `bca_prod`)

| Pieza | Detalle |
|---|---|
| Plantilla `mail.template` | ID **42**, sobre `bca.recibo`, `Para = {{ object.poliza_id.contratante_id.email }}` |
| Server action `bca_aviso_vencimiento_recibo` | `Execute Python Code` con código §4 |
| Scheduled action (cron) | Diario (`1 day`), hora deseada |

---

## 4. Código (server action)

```python
AVISO_DIAS = 15
PLANTILLA_ID = 42
MSG_SIN_EMAIL = 'Aviso de vencimiento no enviado: el contratante no tiene email registrado.'
MSG_SIN_PLANTILLA = 'Aviso de vencimiento no enviado: plantilla de correo no encontrada.'

hoy = datetime.date.today()
dia_aviso = hoy + datetime.timedelta(days=AVISO_DIAS)

plantilla = env['mail.template'].browse(PLANTILLA_ID)

# Todos los recibos pendientes en ventana (con o sin email): los sin-email
# se capturan para postear en su chatter en vez de silenciarlos.
recibos = env['bca.recibo'].search([
    ('estado', '=', 'pendiente'),
    ('fecha_desde', '=', dia_aviso),
    ('poliza_id.estado', '=', 'activa'),
])

for rec in recibos:
    if not plantilla:
        rec.message_post(body=MSG_SIN_PLANTILLA)
        continue
    if not rec.poliza_id.contratante_id.email:
        rec.message_post(body=MSG_SIN_EMAIL)
        continue
    plantilla.send_mail(rec.id, force_send=False)
```

**Restricciones server action respetadas (Odoo 19 `safe_eval`):** sin `import`, sin `STORE_ATTR`
(solo asignaciones locales `STORE_FAST`), `datetime`/`timedelta` vía módulo inyectado.

**No-envío en chatter:** `bca.recibo` hereda `mail.thread` → dispone de `message_post`. Ante las dos
causas evaluadas (plantilla ausente, contratante sin email) se publica una nota en el chatter del
recibo con la causa y `continue` (no detiene el resto). Si la plantilla falta, **no se hace `raise`**:
cada recibo en ventana queda con su nota. (Sobre `mail.thread` vs `mail.activity.mixin`, ver §5.)

**Envío:** por `send_mail(force_send=False)` → cola de `mail.mail`, entregada por el cron nativo
`Mail: Email Queue Manager`.

---

## 5. Configuración UX (paso a paso)

1. **Plantilla** (`Correos → Plantillas`):
   - `Aplicar a`: `bca.recibo` (Recibo de Póliza BCA).
   - `Destinatarios (Para)`: `{{ object.poliza_id.contratante_id.email }}`.
   - `Asunto`: ej. `Aviso: su recibo {{ object.name }} de la póliza {{ object.poliza_id.name }} cobra el {{ object.fecha_desde }}`.
   - Cuerpo con placeholders `{{ object.name }}`, `{{ object.poliza_id.name }}`,
     `{{ object.poliza_id.contratante_id.name }}`, `{{ object.fecha_desde }}`, `{{ object.fecha_hasta }}`,
     `{{ object.prima_total }}`.
   - `Enviar desde` y servidor de correo correctos.
2. **Server action** `bca_aviso_vencimiento_recibo`: Ajustes → Técnico → Acciones → Acciones del
   servidor → tipo `Execute Python Code`, pegar §4.
3. **Cron** vinculado a la acción → interval_number `1`, interval_type **`days`**, hora deseada.

**Nota sobre `bca.recibo`:** el modelo hereda `mail.thread` (chatter/correos) pero **no**
`mail.activity.mixin`. No afecta al envío por plantilla; solo limita funciones de actividades si se
quisieran usar sobre el recibo.

---

## 6. Casos de prueba

| # | Caso | Esperado |
|---|---|---|
| 1 | Recibo `pendiente` con `fecha_desde = hoy + 15`, póliza `activa`, contratante con `email` | ✓ envía correo al contratante |
| 2 | Recibo `pendiente` con `fecha_desde = hoy + 14` o `+16` | ✗ no envía, no postea (fuera de ventana) |
| 3 | Recibo `pagado` o `cancelado` en ventana | ✗ no envía, no postea (estado excluido por dominio) |
| 4 | Póliza en `borrador`/`expirada`/`cancelada` | ✗ no envía, no postea (estado excluido por dominio) |
| 5 | Contratante sin `email` | ✗ no envía ✓ postea `MSG_SIN_EMAIL` en el chatter del recibo |
| 6 | Re-ejecución mismo día | ⚠ **duplica** si se re-ejecuta (recibo sigue en ventana); en `bca_prod` solo el cron diario lo dispara, 1×/día |
| 7 | Plantilla no encontrada | ✗ no envía, **no rompe**: por cada recibo en ventana postea `MSG_SIN_PLANTILLA` en su chatter |

---

## 7. Relación con la infraestructura SMTP

Misma base que los avisos previos: la entrega depende de los **servidores de correo saliente**.
- Revisar que el dominio del `Enviar desde` tenga servidor con `from_filter`.
- Histórico: server id 16 `notificaciones@grupobca.com.mx` (`smtp.gmail.com:465`) devolvió
  `535 Bad Credentials` en 2026-09-01; validar `Test Connection` antes de la primera corrida real.
- (Entregabilidad) SPF/DKIM/DMARC → mejor entrega.

---

## 8. Pendientes

- [ ] Crear la plantilla de correo en `bca_prod` (ID 42, nombre `Aviso vencimiento recibo`).
- [ ] Crear server action `bca_aviso_vencimiento_recibo` con §4 (rev. chatter no-envío).
- [ ] Crear cron diario y definir hora.
- [ ] `Test Connection` del servidor SMTP y corrección de credenciales.
