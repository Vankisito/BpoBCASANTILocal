# Manual operativo: Alta de Promotorias y usuarios BCA

## Objetivo

Definir procedimiento para:

- Crear Holding y Promotoria.
- Crear usuario interno para persona promotora.
- Asignar rol BCA.
- Ligar usuario con Promotoria.
- Validar permisos y cartera visible.

## Conceptos

### Holding

Entidad raiz de red BCA. Una Promotoria debe pertenecer a un Holding.

### Promotoria

Entidad comercial que agrupa agentes. Puede ser:

- Empresa: persona moral.
- Persona: persona fisica.

### Usuario

Credencial de acceso a Odoo. El usuario tiene un contacto relacionado. La Promotoria se resuelve mediante:

- Usuario ligado directamente a la Promotoria.
- Contacto del usuario cuyo campo `Empresa / Pertenece a` es la Promotoria.

## Requisitos

La persona que realiza el alta debe ser:

- Director Comercial BCA; o
- Director BCA.

Debe contar con:

- Nombre legal de Holding.
- Datos fiscales de Promotoria.
- Nombre y correo de cada usuario.
- Tipo de Promotoria: empresa o persona fisica.
- Agentes que pertenecen a la Promotoria.

## Orden obligatorio

```text
1. Crear Holding.
2. Crear Promotoria bajo Holding.
3. Crear contacto del usuario promotor.
4. Crear usuario interno.
5. Asignar Rol BCA Seguros = Promotor BCA.
6. Ligar contacto del usuario a la Promotoria.
7. Crear o afiliar agentes.
8. Validar usuarios promotores, menus y cartera.
```

## Paso 1: crear Holding

Ruta:

```text
Contactos -> Nuevo
```

En pestaña `BCA Seguros`:

- `Tipo BCA`: `Holding`.
- `Nombre`: nombre del grupo o holding.
- `Pertenece a`: vacío.
- Capturar RFC y domicilio fiscal si corresponde.

Guardar.

Ejemplo:

```text
Nombre: Grupo BCA
Tipo BCA: Holding
```

## Paso 2A: crear Promotoria empresa

Ruta:

```text
Contactos -> Nuevo
```

Datos generales:

- Activar `Es una empresa`.
- `Nombre`: razón social de la Promotoria.
- Correo corporativo, teléfono y domicilio.

Pestaña `BCA Seguros`:

- `Tipo BCA`: `Promotoria`.
- `Pertenece a`: Holding creado.
- Capturar RFC y domicilio fiscal propios de la Promotoria.

Guardar.

Ejemplo:

```text
Nombre: La Promotoria Nueva, S.A. de C.V.
Tipo BCA: Promotoria
Pertenece a: Grupo BCA
Es una empresa: si
```

## Paso 2B: crear Promotoria persona fisica

Ruta:

```text
Contactos -> Nuevo
```

Datos generales:

- Desactivar `Es una empresa`.
- `Nombre`: nombre completo de la persona.
- Correo y teléfono personales.

Pestaña `BCA Seguros`:

- `Tipo BCA`: `Promotoria`.
- `Pertenece a`: Holding creado.
- Capturar RFC y domicilio fiscal propios.

Guardar.

Ejemplo:

```text
Nombre: Alex Perez
Tipo BCA: Promotoria
Pertenece a: Grupo BCA
Es una empresa: no
```

## Paso 3: preparar contacto persona para empresa

Este paso aplica solo cuando la Promotoria es empresa. Crear contacto persona:

```text
Contactos -> Nuevo
```

Capturar:

- `Nombre`: nombre de la persona promotora.
- Correo personal.
- `Empresa / Pertenece a`: Promotoria empresa.
- No seleccionar `Tipo BCA` para este contacto persona.

Guardar.

Para una Promotoria persona fisica, se usara directamente el contacto que ya
tiene `Tipo BCA = Promotoria`; no crear otro contacto.

## Paso 4: crear usuario interno usando contacto existente

Al crear un usuario, el formulario muestra para Directores el campo:

```text
Contacto existente
```

Seleccionar un contacto existente evita que Odoo cree un segundo contacto.
Odoo guarda la relacion mediante `res.users.partner_id`.

Ruta:

```text
Ajustes -> Usuarios y companias -> Usuarios -> Nuevo
```

Datos:

- `Nombre`: nombre de la persona.
- `Login`: correo de inicio de sesion.
- Tipo de usuario: `Usuario` o usuario interno.
- No seleccionar `Portal`.
- No seleccionar `Administrador`.
- En `Contacto existente`, seleccionar:
  - El partner Promotoria, si es persona fisica.
  - El contacto persona creado en Paso 3, si es empresa.

Guardar.

## Paso 5: asignar rol BCA

En la pestaña `Permisos de acceso`, seleccionar:

```text
BCA Seguros -> Rol BCA Seguros -> Promotor BCA
```

No asignar simultaneamente:

- Agente BCA.
- Operador BCA.
- Lider BCA.
- Director Comercial BCA.
- Director BCA.

El rol `Promotor BCA` es independiente y no hereda permisos operativos globales.

## Paso 6: validar vinculo con Promotoria

No se debe cambiar `Contacto relacionado` despues de guardar: el campo es de
solo lectura en la vista estandar de Odoo 19. Si se eligio correctamente
`Contacto existente`, la liga ya quedo creada.

Resultado para empresa:

```text
La Promotoria Nueva
└── Contacto persona del promotor
    └── Usuario Promotor
```

Resultado para persona fisica:

```text
Promotoria Alex Perez
└── Usuario Promotor
```

No crear un segundo contacto con el mismo nombre y correo.

### Validar vinculo

Abrir la Promotoria:

```text
Contactos -> Promotoria -> pestaña BCA Seguros
```

En `Clasificacion`, revisar:

```text
Usuarios promotores
```

Debe aparecer el usuario promotor. La lista incluye:

- Usuarios ligados directamente a la Promotoria.
- Usuarios cuyos contactos hijos pertenecen a la Promotoria.

Este campo es de consulta. La liga se modifica desde el contacto del usuario, mediante `Empresa / Pertenece a`.

## Paso 7: crear o afiliar agentes

Para cada agente:

```text
Contactos -> Nuevo
```

En pestaña `BCA Seguros`:

- `Tipo BCA`: `Agente`.
- `Pertenece a`: Promotoria.
- Capturar datos fiscales y de aseguradora.

Un agente debe pertenecer a una Promotoria. El sistema deriva la Promotoria de la póliza desde el agente.

## Permisos por rol

### Promotor BCA

Acceso segmentado a su Promotoria:

- Pólizas: lectura.
- Recibos: lectura.
- Beneficiarios: lectura.
- Agentes afiliados: lectura.
- Tablero BCA: lectura de indicadores de su cartera.
- Menus: Tablero, Pólizas y Recibos.

Sin acceso a:

- Crear, editar o eliminar pólizas.
- Crear, editar o eliminar recibos.
- Importar cobranza.
- Cargar portafolios.
- Bitácoras.
- Configuración.
- Cambios de Promotoria.
- Datos de otras Promotorias.

### Agente BCA

- Pólizas propias: lectura.
- Recibos propios: lectura.
- Beneficiarios propios: lectura.
- Reportes propios permitidos por reglas.

### Operador BCA

- Operación global de pólizas y agentes.
- Carga de portafolios.
- Importación de cobranza.
- Consulta de bitácoras.
- Sin permisos de Director.

### Lider BCA

- Hereda permisos de Operador.
- Consulta reportes por agente y Promotoria.
- No es Director.

### Director Comercial BCA

- Hereda permisos de Lider y Operador.
- Gestiona configuración comercial.
- Gestiona Promotorias y cambios de afiliación.
- Consulta reportes consolidados.

### Director BCA

- Hereda permisos de Director Comercial.
- Acceso completo de administración BCA.
- Puede eliminar registros en los modelos autorizados.

### Reclutador BCA

Selector:

```text
Recursos humanos -> Reclutamiento -> Reclutador BCA
```

- Acceso de entrevistador.
- Puede gestionar sus candidatos.
- Ve únicamente candidatos asignados según reglas de reclutamiento.

### Capital Humano BCA

Selector:

```text
Recursos humanos -> Reclutamiento -> Capital Humano BCA
```

- Acceso de encargado de Reclutamiento.
- Gestiona el embudo de candidatos.
- Consulta todos los candidatos permitidos por reglas nativas.

## Validacion del alta

### Promotoria

- Tipo BCA correcto.
- Holding correcto.
- RFC y domicilio propios.
- Empresa/persona configurada correctamente.

### Usuario

- Usuario interno.
- Login correcto.
- Contacto relacionado correcto.
- Rol BCA correcto.
- Sin roles operativos adicionales no autorizados.

### Vinculo

- Contacto del usuario tiene `Empresa / Pertenece a` correcta.
- Usuario aparece en `Usuarios promotores` de la Promotoria.
- El agente aparece afiliado a la Promotoria.

### Seguridad

- Promotor ve solo su Promotoria.
- No ve pólizas de otras Promotorias.
- No puede editar ni crear información operativa.
- Tablero muestra solo cifras permitidas.

## Errores que deben evitarse

- Crear Promotoria sin Holding.
- Crear agente sin Promotoria.
- Asignar `Operador BCA` a un Promotor.
- Usar usuario Portal para un Promotor.
- Crear dos contactos para la misma persona sin necesidad.
- Ligar el usuario a la empresa equivocada.
- Cambiar directamente el `parent_id` de un agente ya activo.
- Confundir `Usuarios promotores` con un campo de asignación manual: es una vista de comprobación.
