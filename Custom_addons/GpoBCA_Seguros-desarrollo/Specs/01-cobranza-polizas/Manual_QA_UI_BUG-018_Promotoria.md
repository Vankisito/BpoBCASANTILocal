# Manual de QA UI — BUG-018 y Gobernanza de Promotorías

**Módulo:** `BCA_Seguros` — Gestión de Pólizas y Cobranza
**Versión objetivo:** `19.0.1.10.0`
**Plataforma:** Odoo 19 Community
**Dirigido a:** QA Junior / Testing funcional
**Tipo:** Pruebas manuales desde la interfaz de Odoo
**Fecha:** 2026-08-10

---

## 1. Objetivo

Verificar desde la interfaz de usuario que:

1. La lista de pólizas se puede **agrupar por Promotoría** sin mostrar un error RPC.
2. La Promotoría se muestra correctamente en agentes y pólizas.
3. La jerarquía **Holding → Promotoría → Agente** se respeta.
4. Un usuario no puede cambiar directamente la Promotoría de un agente ya creado.
5. Un Director Comercial o Director puede realizar un cambio mediante el flujo autorizado.
6. El cambio de Promotoría queda registrado en un historial inmutable.
7. La cartera vigente cambia de Promotoría cuando corresponde.
8. Los recibos pagados y su PCA histórica no cambian después de una transferencia.
9. Los permisos de los distintos roles continúan funcionando.

> **Regla principal:** ninguna prueba debe terminar en una pantalla roja, `RPC_ERROR`, traceback, error de servidor o mensaje técnico inesperado.

---

## 2. Cómo usar este manual

- Ejecuta las pruebas en orden.
- Marca cada resultado como:

  ```text
  [ ] OK     [ ] Falla     [ ] No aplica
  ```

- Adjunta una captura de pantalla cuando la prueba sea relevante.
- Si una prueba falla, no intentes “arreglarla” cambiando datos sin documentarlo.
- Anota el usuario utilizado, la fecha y el identificador de la prueba.
- Utiliza únicamente datos ficticios.

### 2.1 Convención para datos de prueba

Usa el prefijo `QA-018` en nombres y folios:

| Tipo de dato | Ejemplo |
|---|---|
| Holding | `QA-018 Holding` |
| Promotoría A | `QA-018 Promotoría A` |
| Promotoría B | `QA-018 Promotoría B` |
| Agente A | `QA-018 Agente A` |
| Agente B | `QA-018 Agente B` |
| Cliente | `QA-018 Cliente 01` |
| Póliza | `QA-018-POL-001` |
| Motivo | `Transferencia QA BUG-018` |

No uses información real de clientes, RFC reales, teléfonos reales ni datos financieros reales.

---

## 3. Entorno requerido

Completa esta información antes de comenzar:

| Dato | Valor |
|---|---|
| URL | ______________________________ |
| Base de datos | ______________________________ |
| Versión Odoo | `19.0 Community` |
| Versión del módulo | `19.0.1.10.0` |
| QA responsable | ______________________________ |
| Fecha de ejecución | ______________________________ |
| Navegador | ______________________________ |

### 3.1 Verificación inicial

- [ ] Inicio sesión correctamente.
- [ ] Veo la aplicación **BCA Seguros**.
- [ ] En **Ajustes → Aplicaciones**, `BCA Seguros` aparece instalada.
- [ ] La versión instalada es `19.0.1.10.0`.
- [ ] No aparece ningún error al abrir el tablero.
- [ ] La pantalla no muestra un error RPC al cargar los menús.

Si la versión no coincide, detén la prueba y repórtalo como incidencia de ambiente.

---

## 4. Roles que se deben probar

Solicita al responsable del ambiente usuarios de prueba para los roles disponibles.

| Rol | Uso en este manual |
|---|---|
| **Agente BCA** | Verificar que solo vea sus registros y no pueda administrar la red. |
| **Operador BCA** | Verificar operación general y lectura de históricos. |
| **Líder BCA** | Verificar reportes y acceso ampliado de lectura. |
| **Director Comercial BCA** | Verificar el cambio autorizado de Promotoría. |
| **Director BCA** | Verificar acceso total y cambio autorizado de Promotoría. |

### 4.1 Datos de usuarios

| Rol | Usuario | Confirmado |
|---|---|:---:|
| Agente BCA | __________________ | [ ] |
| Operador BCA | __________________ | [ ] |
| Líder BCA | __________________ | [ ] |
| Director Comercial BCA | __________________ | [ ] |
| Director BCA | __________________ | [ ] |

> Si no es posible disponer de todos los usuarios, ejecuta las pruebas funcionales con un Director y realiza como mínimo las pruebas de seguridad con un Agente y un Director Comercial.

---

## 5. Preparación de datos de prueba

Estas acciones deben realizarlas un usuario autorizado, preferentemente Director.

### QA-001 — Crear o confirmar el Holding

**Objetivo:** contar con el nivel raíz de la jerarquía.

**Pasos:**

1. Ve a **BCA Seguros → Configuración → Promotorías**.
2. Busca `QA-018 Holding`.
3. Si ya existe un Holding de pruebas, reutilízalo.
4. Si no existe y el rol lo permite, crea un contacto BCA con:
   - Nombre: `QA-018 Holding`.
   - Tipo BCA: **Holding**.
   - Sin “Pertenece a”.
5. Guarda.

**Resultado esperado:**

- [ ] El Holding se guarda correctamente.
- [ ] No solicita una Promotoría superior.
- [ ] No aparece ningún error.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-002 — Crear dos Promotorías válidas

**Objetivo:** preparar dos destinos diferentes para probar una transferencia.

**Pasos:**

1. Ve a **BCA Seguros → Configuración → Promotorías**.
2. Crea `QA-018 Promotoría A`.
3. En **Tipo BCA**, selecciona **Promotoría**.
4. En **Pertenece a**, selecciona `QA-018 Holding`.
5. Guarda.
6. Repite para `QA-018 Promotoría B`.

**Resultado esperado:**

- [ ] Ambas Promotorías se guardan.
- [ ] Ambas muestran al Holding como entidad superior.
- [ ] La Promotoría no puede guardarse sin Holding.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-003 — Crear agentes de prueba

**Objetivo:** crear agentes asignados a distintas Promotorías.

**Pasos:**

1. Ve a **BCA Seguros → Configuración → Agentes**.
2. Crea `QA-018 Agente A`.
3. Selecciona **Tipo BCA: Agente**.
4. Selecciona `QA-018 Promotoría A` en **Pertenece a**.
5. Guarda.
6. Crea `QA-018 Agente B` y asígnalo a `QA-018 Promotoría B`.
7. Abre cada agente.

**Resultado esperado:**

- [ ] El agente se guarda con su Promotoría.
- [ ] El campo **Promotoría** se muestra automáticamente.
- [ ] El campo calculado de Promotoría es de solo lectura.
- [ ] La lista de Agentes muestra correctamente la Promotoría si se activa la columna opcional.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

---

## 6. Pruebas negativas de jerarquía

Estas pruebas confirman que no se aceptan registros organizacionales incompletos.

### QA-004 — Agente sin Promotoría

**Pasos:**

1. Ve a **BCA Seguros → Configuración → Agentes → Nuevo**.
2. Selecciona **Tipo BCA: Agente**.
3. No selecciones una Promotoría.
4. Intenta guardar.

**Resultado esperado:**

- [ ] El sistema impide guardar.
- [ ] Muestra un mensaje entendible indicando que el Agente debe pertenecer a una Promotoría.
- [ ] No aparece traceback ni error RPC.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-005 — Promotoría sin Holding

**Pasos:**

1. Ve a **BCA Seguros → Configuración → Promotorías → Nuevo**.
2. Selecciona **Tipo BCA: Promotoría**.
3. No selecciones un Holding en **Pertenece a**.
4. Intenta guardar.

**Resultado esperado:**

- [ ] El sistema impide guardar.
- [ ] Muestra un mensaje indicando que la Promotoría debe pertenecer a un Holding.
- [ ] No se crea un registro incompleto.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-006 — Tipo de padre incorrecto

**Pasos:**

1. Intenta crear una Promotoría usando como padre una entidad que no sea Holding.
2. Intenta crear un Agente usando como padre una entidad que no sea Promotoría.

**Resultado esperado:**

- [ ] El dominio de selección no muestra padres inválidos o el servidor rechaza el guardado.
- [ ] No se permite una jerarquía inválida.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

---

## 7. BUG-018 — Agrupar pólizas por Promotoría

### QA-007 — Crear pólizas para dos Promotorías

**Objetivo:** disponer de registros visibles en grupos diferentes.

**Precondiciones:**

- Existen `QA-018 Agente A` y `QA-018 Agente B`.
- Existe una Aseguradora de prueba, por ejemplo MetLife.
- Existe un Producto de Seguro.
- Existe un Contratante de prueba.

**Pasos:**

1. Ve a **BCA Seguros → Pólizas → Pólizas → Nuevo**.
2. Crea una póliza con:
   - Número: `QA-018-POL-001`.
   - Aseguradora: una aseguradora disponible.
   - Producto: un producto válido.
   - Contratante: un contacto ficticio.
   - Agente: `QA-018 Agente A`.
   - Fechas válidas.
   - Periodicidad: Anual o Mensual.
   - Prima anual: un valor de prueba.
3. Guarda.
4. Crea una segunda póliza con número `QA-018-POL-002` y agente `QA-018 Agente B`.
5. Regresa a la lista de pólizas.

**Resultado esperado:**

- [ ] Ambas pólizas se guardan.
- [ ] La Promotoría se llena automáticamente según el agente.
- [ ] El campo Promotoría no es editable directamente desde la póliza.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-008 — Agrupación principal por Promotoría

**Objetivo:** reproducir el escenario original del BUG-018.

**Pasos:**

1. Ve a **BCA Seguros → Pólizas → Pólizas**.
2. Abre el menú de búsqueda/filtros.
3. Entra en **Agrupar por**.
4. Selecciona **Promotoría**.
5. Espera a que la lista termine de cargar.

**Resultado esperado obligatorio:**

- [ ] La lista se divide en grupos por Promotoría.
- [ ] `QA-018 Promotoría A` aparece con la póliza del Agente A.
- [ ] `QA-018 Promotoría B` aparece con la póliza del Agente B.
- [ ] No aparece `RPC_ERROR`.
- [ ] No aparece `ValueError: Cannot convert ... because it is not stored`.
- [ ] No aparece una pantalla roja.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

**Captura requerida:** la lista agrupada mostrando al menos dos grupos.

### QA-009 — Agrupaciones relacionadas

En la misma lista, prueba por separado:

- [ ] Agrupar por Aseguradora.
- [ ] Agrupar por Ramo.
- [ ] Agrupar por Agente.
- [ ] Agrupar por Promotoría.
- [ ] Agrupar por Estado.

**Resultado esperado:** todas las agrupaciones cargan sin errores y los registros pertenecen al grupo correcto.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-010 — Filtro y columna Promotoría

**Pasos:**

1. En la lista de pólizas, abre la configuración de columnas.
2. Activa la columna **Promotoría** si está oculta.
3. Filtra por una Promotoría específica.
4. Limpia el filtro.

**Resultado esperado:**

- [ ] La columna muestra el valor correcto.
- [ ] El filtro devuelve las pólizas de la Promotoría seleccionada.
- [ ] No se muestran pólizas de otra Promotoría.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

---

## 8. Gobernanza del cambio de Promotoría

### QA-011 — El agente no puede cambiar su Promotoría directamente

**Usuario recomendado:** Agente o usuario Operador.

**Pasos:**

1. Abre **BCA Seguros → Configuración → Agentes**.
2. Abre un agente ya guardado.
3. En la pestaña **BCA Seguros**, localiza **Pertenece a**.
4. Intenta editar la Promotoría directamente.
5. Intenta guardar si la interfaz permite iniciar la edición.

**Resultado esperado:**

- [ ] El campo está bloqueado en registros existentes.
- [ ] El usuario no puede modificar la Promotoría directamente.
- [ ] Si intenta hacerlo mediante una acción disponible, el servidor lo rechaza con un mensaje funcional.
- [ ] No se modifica el agente.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-012 — El Agente no ve el botón de cambio

**Usuario recomendado:** Agente BCA.

**Pasos:**

1. Inicia sesión como Agente BCA.
2. Abre un agente/contacto propio si tiene acceso.
3. Revisa la pestaña **BCA Seguros**.

**Resultado esperado:**

- [ ] No aparece el botón **Cambiar Promotoría**.
- [ ] No aparece el menú de Configuración.
- [ ] El usuario no puede administrar Promotorías ni Agentes.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-013 — Director Comercial ve el flujo autorizado

**Usuario recomendado:** Director Comercial BCA.

**Pasos:**

1. Inicia sesión como Director Comercial.
2. Ve a **BCA Seguros → Configuración → Agentes**.
3. Abre `QA-018 Agente A`.
4. En la pestaña **BCA Seguros**, pulsa **Cambiar Promotoría**.

**Resultado esperado:**

- [ ] Se abre la ventana **Cambiar Promotoría**.
- [ ] El Agente aparece precargado.
- [ ] Se muestra la Promotoría actual.
- [ ] Se puede elegir una Promotoría nueva.
- [ ] Se muestran los contadores de impacto:
  - Pólizas afectadas.
  - Recibos pendientes.
  - Recibos pagados.
- [ ] Se muestra la nota de que los recibos pagados conservan su histórico y PCA.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-014 — Validación de cambio sin motivo

**Pasos:**

1. Abre el wizard **Cambiar Promotoría**.
2. Selecciona la Promotoría nueva.
3. Deja vacío el campo **Motivo**.
4. Pulsa **Confirmar Cambio**.

**Resultado esperado:**

- [ ] El sistema no confirma el cambio.
- [ ] Solicita capturar un motivo.
- [ ] El agente conserva su Promotoría original.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-015 — Transferir Agente de Promotoría A a B

**Usuario recomendado:** Director Comercial BCA.

**Pasos:**

1. Abre el wizard para `QA-018 Agente A`.
2. Selecciona `QA-018 Promotoría B`.
3. Captura el motivo: `Transferencia QA BUG-018`.
4. Verifica los contadores mostrados.
5. Pulsa **Confirmar Cambio**.
6. Cierra y vuelve a abrir el agente.

**Resultado esperado:**

- [ ] El wizard se cierra sin error.
- [ ] El agente ahora pertenece a `QA-018 Promotoría B`.
- [ ] El campo calculado **Promotoría** muestra `QA-018 Promotoría B`.
- [ ] La lista de agentes refleja la nueva Promotoría.
- [ ] Las pólizas vigentes del agente se muestran ahora bajo la nueva Promotoría.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

---

## 9. Historial del cambio

### QA-016 — Consultar el historial

**Pasos:**

1. Ve a **BCA Seguros → Configuración → Cambios de Promotoría**.
2. Busca el registro creado en QA-015.
3. Abre el registro.

**Resultado esperado:**

- [ ] Existe un registro para el cambio.
- [ ] El Agente es correcto.
- [ ] La Promotoría anterior es `QA-018 Promotoría A`.
- [ ] La Promotoría nueva es `QA-018 Promotoría B`.
- [ ] La fecha del cambio es correcta.
- [ ] El motivo es `Transferencia QA BUG-018`.
- [ ] El usuario autorizador es el Director Comercial que ejecutó la acción.
- [ ] Los campos se muestran en modo lectura.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-017 — Historial no editable

**Usuario recomendado:** Director Comercial o Director.

**Pasos:**

1. Abre el registro histórico creado en QA-016.
2. Intenta cambiar la Promotoría nueva, el motivo o la fecha.
3. Intenta eliminar el registro, si aparece la opción.

**Resultado esperado:**

- [ ] Los campos son solo lectura.
- [ ] No se puede editar el histórico.
- [ ] No se puede eliminar el histórico.
- [ ] La información original permanece intacta.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

---

## 10. Regresión de cartera, recibos y PCA

Esta sección es obligatoria porque la Promotoría actual y la Promotoría histórica son conceptos distintos.

### 10.1 Diferencia entre los dos valores

| Pantalla/campo | Qué representa |
|---|---|
| Promotoría en la póliza | Promotoría vigente de la cartera actual. |
| Promotoría en un recibo pendiente | Promotoría vigente de la póliza/agente. |
| Promotoría en un recibo pagado | Fotografía de la Promotoría al momento del pago. |
| PCA de recibo pagado | Valor congelado al registrar el pago. |

### QA-018 — Verificar pólizas después de la transferencia

**Pasos:**

1. Ve a **BCA Seguros → Pólizas → Pólizas**.
2. Busca `QA-018-POL-001`, que originalmente pertenecía al Agente A.
3. Activa la columna **Promotoría**.
4. Agrupa nuevamente por Promotoría.

**Resultado esperado:**

- [ ] La póliza aparece bajo `QA-018 Promotoría B` después de la transferencia del agente.
- [ ] La póliza conserva el mismo agente.
- [ ] La póliza no cambia de contratante, aseguradora, producto o prima.
- [ ] La agrupación continúa funcionando sin error RPC.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-019 — Verificar recibos pagados e históricos

**Precondición:** debe existir al menos un recibo pagado antes de la transferencia. Si no existe, registra el caso como “No aplica” y deja constancia.

**Pasos:**

1. Ve a **BCA Seguros → Cobranza → Recibos**.
2. Busca el recibo pagado relacionado con la póliza de prueba.
3. Activa las columnas opcionales:
   - `Agente (al pagar)`.
   - `Promotoría (al pagar)`.
   - `PCA`.
   - `Factor aplicado`.
4. Abre el recibo y anota los valores antes de transferir, si el caso se prepara desde cero.
5. Después de la transferencia, vuelve a revisar el recibo.

**Resultado esperado:**

- [ ] La Promotoría histórica sigue siendo la que correspondía al momento del pago.
- [ ] El Agente histórico no cambia.
- [ ] La PCA no cambia.
- [ ] El factor aplicado no cambia.
- [ ] El recibo conserva su estado Pagado.

Resultado: `[ ] OK  [ ] Falla  [ ] No aplica`  Observaciones: ______________________________

### QA-020 — Reporte PCA por Promotoría

**Pasos:**

1. Ve a **BCA Seguros → Reportes → PCA por Promotoría**.
2. Busca el registro correspondiente al recibo pagado de prueba.
3. Revisa Promotoría, PCA y cantidad de recibos.
4. Compara contra la información del recibo pagado.

**Resultado esperado:**

- [ ] El reporte carga sin error.
- [ ] La Promotoría corresponde a la fotografía histórica del pago.
- [ ] El importe PCA coincide con el recibo.
- [ ] El cambio actual de Promotoría no mueve artificialmente la PCA histórica al nuevo grupo.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

---

## 11. Pruebas de permisos

### QA-021 — Acceso de Agente

**Usuario:** Agente BCA.

- [ ] Puede abrir **Pólizas**.
- [ ] Solo ve sus propias pólizas.
- [ ] Puede abrir sus recibos autorizados.
- [ ] No ve **Configuración**.
- [ ] No ve **Cambios de Promotoría**.
- [ ] No puede cambiar la Promotoría de un agente.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-022 — Acceso de Operador

**Usuario:** Operador BCA.

- [ ] Puede operar pólizas y cobranza según sus permisos.
- [ ] Puede consultar el historial de cambios si el menú o acción está disponible.
- [ ] No puede crear un cambio de Promotoría desde el flujo autorizado.
- [ ] No puede editar ni eliminar un histórico.
- [ ] No ve Configuración administrativa de la red.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-023 — Acceso de Líder

**Usuario:** Líder BCA.

- [ ] Puede consultar reportes.
- [ ] Puede leer históricos si están disponibles.
- [ ] No puede ejecutar el cambio de Promotoría.
- [ ] No puede editar ni eliminar el histórico.

Resultado: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

### QA-024 — Acceso de Director Comercial y Director

Para ambos roles:

- [ ] Ven Configuración.
- [ ] Ven Agentes y Promotorías.
- [ ] Ven el botón **Cambiar Promotoría**.
- [ ] Pueden abrir el wizard.
- [ ] Pueden ejecutar una transferencia válida.
- [ ] Pueden consultar el historial.
- [ ] No pueden editar ni eliminar un registro histórico existente.

Resultado Director Comercial: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

Resultado Director: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

---

## 12. Pruebas de regresión rápida

Ejecuta estas comprobaciones después de terminar las pruebas principales.

- [ ] El tablero BCA abre sin error.
- [ ] La lista de pólizas abre sin error.
- [ ] La lista de recibos abre sin error.
- [ ] El formulario de Agente abre sin error.
- [ ] El formulario de Promotoría abre sin error.
- [ ] El reporte PCA por Agente abre sin error.
- [ ] El reporte PCA por Promotoría abre sin error.
- [ ] El reporte Consolidado BCA abre sin error.
- [ ] La importación de portafolio no muestra error técnico al abrirse.
- [ ] La cobranza diaria no muestra error técnico al abrirse.
- [ ] Los filtros existentes de pólizas siguen funcionando.
- [ ] Los filtros existentes de contactos siguen funcionando.
- [ ] La PCA de recibos pagados no cambia durante estas pruebas.

Resultado global: `[ ] OK  [ ] Falla`  Observaciones: ______________________________

---

## 13. Qué se considera un fallo bloqueante

Clasifica como **Bloqueante** cualquiera de estos casos:

- Pantalla roja o traceback.
- `RPC_ERROR` al agrupar por Promotoría.
- El sistema permite crear un Agente sin Promotoría.
- El sistema permite crear una Promotoría sin Holding.
- Un Agente puede cambiar directamente su Promotoría sin autorización.
- Un usuario Agente puede modificar la red.
- Una transferencia cambia la Promotoría histórica de un recibo pagado.
- Una transferencia cambia la PCA o el factor de un recibo pagado.
- El módulo deja de actualizarse por error de migración.

---

## 14. Plantilla para reportar incidencias

Copia este bloque por cada fallo:

```text
### Incidencia QA-018-___

- ID de prueba:
- Fecha y hora:
- Ambiente / URL:
- Base de datos:
- Versión del módulo:
- Navegador:
- Usuario / rol:
- Datos utilizados:
- Resultado esperado:
- Resultado obtenido:
- Pasos para reproducir:
  1.
  2.
  3.
- ¿Apareció RPC_ERROR o traceback?: Sí / No
- Texto exacto del mensaje:
- Captura de pantalla:
- Video o grabación, si aplica:
- Frecuencia: Siempre / Intermitente / Una vez
- Severidad propuesta: Bloqueante / Alta / Media / Baja
- Observaciones adicionales:
```

### 14.1 Reglas para una buena evidencia

- Captura la pantalla completa cuando aparezca un error.
- Incluye el menú y el registro donde ocurrió.
- No tapes el mensaje de error.
- Si es un problema de datos, anota el folio exacto.
- Si es un problema de permisos, indica el rol y el usuario.
- No adjuntes contraseñas ni datos personales reales.

---

## 15. Criterios de aceptación

La entrega se considera aprobada cuando:

- [ ] QA-001 a QA-006 pasan.
- [ ] QA-008 pasa sin RPC_ERROR.
- [ ] QA-009 y QA-010 pasan.
- [ ] QA-011 y QA-012 confirman el bloqueo a usuarios no autorizados.
- [ ] QA-013 a QA-017 pasan para Director Comercial o Director.
- [ ] QA-018 confirma la actualización de cartera vigente.
- [ ] QA-019 y QA-020 pasan, o se marcan como No aplica con justificación.
- [ ] QA-021 a QA-024 pasan.
- [ ] La regresión rápida no presenta fallos.
- [ ] No existen incidencias Bloqueantes o Altas abiertas.

### Firma de ejecución

| Rol | Nombre | Fecha | Firma |
|---|---|---|---|
| QA ejecutor |  |  |  |
| QA revisor |  |  |  |
| Responsable funcional |  |  |  |

**Resultado global:** `[ ] Aprobado  [ ] Aprobado con incidencias  [ ] Rechazado`

---

## 16. Nota para el equipo QA

La Promotoría que aparece en una póliza representa la **cartera vigente**. La Promotoría que aparece en un recibo pagado representa la **fotografía histórica al momento del pago**. Es correcto que ambos valores sean distintos después de una transferencia de agente.

No reportes esa diferencia como bug si:

1. La póliza muestra la Promotoría nueva.
2. El recibo pagado conserva la Promotoría original.
3. La PCA y el factor aplicado permanecen sin cambios.
