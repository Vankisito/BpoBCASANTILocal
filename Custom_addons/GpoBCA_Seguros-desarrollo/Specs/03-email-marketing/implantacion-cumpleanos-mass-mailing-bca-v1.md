# Implantación: Cumpleaños Automáticos vía Mass Mailing — BCA · Odoo 19

**Fecha:** 01/09/2026
**Autor:** Santiago Vásquez
**Ambiente probado:** `bca_prod` · Odoo `19.0-20260409`
**Alcance:** 100% operativo vía UX (server action + cron). **Sin módulos nuevos, sin campos nuevos, sin cambios en `mailing.contact` ni en código de módulos.**

---

## 1. Objetivo

Felicitación automática de cumpleaños vía Email Marketing (Mass Mailing), sin registro de cumpleaños en el módulo de Mass Mailing:

- Los contactos de las listas de correo y los contactos de la agenda (`res.partner`) comparten el **mismo correo**.
- El cron busca en `res.partner` el correo de cada contacto de la lista.
- Al encontrarlo, verifica el campo `bca_fecha_nacimiento` del partner (existe en `res.partner`, módulo `BCA_Seguros` — `models/res_partner.py:93`).
- Si coinciden **mes y día** con la fecha de hoy, envía el correo. El año se ignora.

> **NOTA:** NO existe un campo `bca_cumpleanos`. El campo real es `bca_fecha_nacimiento` en `res.partner`.

---

## 2. Piezas implementadas en `bca_prod`

| Pieza | id | Detalle |
|---|---|---|
| Server action `bca_cumple` | 695 | `Execute Python Code`, modelo `mailing.mailing` |
| Scheduled action (cron) `bca_cumple` | 47 | ⚠️ **Pendiente:** cambiar de `1 month` a **diario** (`1 day`) |

---

## 3. Código final (server action)

```python
hoy = datetime.date.today()
listas = env['mailing.list'].search([('name', 'ilike', 'cumple')])

for lista in listas:
    plantilla = env['mailing.mailing'].search([
        ('subject', '=ilike', lista.name),
        ('state', '=', 'draft'),
    ], limit=1, order='id asc')
    if not plantilla:
        continue

    contactos = lista.contact_ids.filtered(lambda c: c.email and not c.opt_out)
    if not contactos:
        continue

    emails = {c.email.strip().lower(): c for c in contactos}
    partners = env['res.partner'].search([
        ('email_normalized', 'in', list(emails)),
        ('bca_fecha_nacimiento', '!=', False),
    ])

    cumple_ids = []
    for p in partners:
        nac = p.bca_fecha_nacimiento
        if nac.month == hoy.month and nac.day == hoy.day:
            contacto = emails.get(p.email_normalized)
            if contacto:
                cumple_ids.append(contacto.id)

    if not cumple_ids:
        continue

    temp_nombre = 'BCA %s (temp)' % lista.name
    lista_temp = env['mailing.list'].search([('name', '=', temp_nombre)], limit=1)
    if not lista_temp:
        lista_temp = env['mailing.list'].create({'name': temp_nombre})
    lista_temp.write({'contact_ids': [(6, 0, cumple_ids)]})

    mailing = plantilla.copy({})
    mailing.write({'contact_list_ids': [(6, 0, [lista_temp.id])]})
    mailing.action_put_in_queue()
```

---

## 4. Decisiones técnicas aprendidas en Odoo 19

| Tema | Hallazgo |
|---|---|
| Identificar la plantilla | Buscar por **`subject`**, nunca por `name`: `name` es **computed no store** = `subject + " (Correo masivo creado el <fecha>)"`. En la UI ves `display_name`/`subject`; el sufijo interno no se muestra. |
| Plantilla en `draft` | Filtro `('state', '=', 'draft')` + `order='id asc'` → se copia la plantilla base (menor id), nunca una copia ya enviada ni una copia cancelada que quedó en draft. Ojo: `mailing.mailing` ordena por `calendar_date DESC` por defecto (`NULL` primero → orden indeterminado entre drafts) → el `order` explícito es obligatorio. |
| Campo M2M de listas en v19 | `contact_list_ids` (renombrado; el viejo `mailing_list_ids` **ya no existe** → arrojaría `Fault`). |
| Programación en v19 | `schedule_date` (renombrado; el viejo `date_send` **ya no existe**). |
| Envío inmediato | `mailing.action_put_in_queue()` = botón **"Envío inmediato"** de la UI; pone `state=in_queue` y dispara el cron nativo `mass_mailing.ir_cron_mass_mailing_queue` vía `_trigger()` → entrega casi inmediata y estadísticas OK. |
| Restricciones server action | `safe_eval`: **no permite `import`** y **prohíbe `STORE_ATTR`** (no `obj.attr = x`). Usar `write({...})` y legacy command `[(6, 0, ids)]`. Globs disponibles: `env`, `model`, `records`, `datetime`, `dateutil`, `time`. |
| `copy()` y la M2M | `copy()` **no reemplaza** la Many2many con el `default` → hay que `mailing.write({'contact_list_ids': [(6,0,[temp])]})` después del copy. Sin esto, en prod enviaría a **TODA la lista**. |
| Convención de nombres | keyword `'cumple'` (`ilike`) selecciona las listas. Por cada lista se usa la plantilla cuyo `subject` coincide con el **nombre de la lista** ("cumple agente" ↔ plantilla "cumple agente"). |
| Lista temporal | `BCA <nombre lista> (temp)` por lista, se recicla en cada corrida (no acumula). Reusa los mismos `mailing.contact` → **respeta `opt_out`**. |
| Buscar por mes/día | Odoo no filtra "mes/día" por dominio (compararía año completo). La coincidencia se resuelve **en Python** (`nac.month == hoy.month and nac.day == hoy.day`). |
| Duplicados de correo en partner | "Enviar si cualquiera coincide": basta un partner con el cumpleaños hoy. |
| Coincidencia de correo | Normalizada: `email_normalized` en `res.partner` / `c.email.strip().lower()` en `mailing.contact`. |

---

## 5. Configuración UX (paso a paso)

1. **Lista:** Email Marketing → Listas → crear `cumple <grupo>` (ej. `cumple agente`).
2. **Plantilla:** Crear un Correo (mailing) cuyo **subject = nombre exacto de la lista** (`cumple agente`). Dejar su estado en **`draft`** (funciona como plantilla). `email_from` y servidor de correo correctos.
3. **Destinatarios:** Agregar contactos a la lista (se usa su `email`). Los `res.partner` correspondientes deben tener `bca_fecha_nacimiento` y el **mismo correo**.
4. **Server action:** Ajustes → Técnico → Acciones → Acciones del servidor → nueva → tipo `Execute Python Code`, modelo `mailing.mailing`, pegar el código de §3.
5. **Cron:** Acción programada vinculada a la server action → interval_number `1`, interval_type **`days`**, hora deseada (ej. 08:00).

---

## 6. Pruebas validadas en `bca_prod` (01/09/2026)

| # | Caso | Resultado |
|---|---|---|
| 1 | Cumpleaños hoy (mes/día = hoy) | ✓ mail recibido (Gmail, pestaña **Promociones**) |
| 2 | Cumpleaños otro día | ✓ no envía (no entra a `cumple_ids`) |
| 3 | Contacto sin fecha de nacimiento | ✓ se excluye |
| 4 | Contacto sin `res.partner` con ese correo | ✓ se excluye |
| 5 | Datos de la prueba | lista `cumple prueba`, partner id 20814, `bca_fecha_nacimiento = 2026-09-01` |
| 6 | Flujo completo | mailings id 3 y 4 → `state=done`; cron nativo `Process queue` los procesó; `mail.mail` creado hacia `santivanki2004@gmail.com` |

---

## 7. Infraestructura SMTP (observado)

- Primer envío: `mail.mail` id 294 → `state=exception`, `failure_reason = 535 5.7.8 Username and Password not accepted (gsmtp)`.
- Causa: `email_from` = `santiagovasquez@habitatdigital.net`; no hay servidor con `from_filter` para ese dominio, por lo que Odoo tomó el primer server activo (sequence 1) = **server id 16 `notificaciones@grupobca.com.mx`** (`smtp.gmail.com:465`, SSL). Sus credenciales SMTP de Gmail resultaron inválidas/revocadas (requieren contraseña de aplicación con 2FA en la cuenta).
- Consistente con historial: digest y mails de seguridad desde abril 2026 también quedaron en `exception`.
- El correo **sí llegó** al buzón destino (Gmail, Promociones). El registro `exception` es un artefacto del reintento tras corregir credenciales.
- **Pendiente:** `Test Connection` en el server 16 + regenerar contraseña de aplicación Gmail de `notificaciones@grupobca.com.mx`, o crear servidor con `from_filter` para el dominio emisor.

---

## 8. Pendientes

- [ ] Cron `bca_cumple` (id 47) → **diario** (hoy es mensual).
- [ ] Validar `Test Connection` del server SMTP 16 y corregir credenciales.
- [ ] Probar con más listas `cumple*` y plantillas en paralelo (una lista sin plantilla no rompe el resto).
- [ ] (Entregabilidad) SPF + DKIM + DMARC para `habitatdigital.net` / `grupobca.com.mx` → mejorar de Promociones a Bandeja principal.

> **Decisión (10/09/2026):** sin guarda de duplicados intra-día (hallazgo 2 de revisión). Aceptado: ningún usuario tiene permisos para ejecutar manualmente el cron; el cron diario dispara una sola vez por día.
