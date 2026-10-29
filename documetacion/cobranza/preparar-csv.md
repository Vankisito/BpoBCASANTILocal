# Preparar el archivo CSV

El archivo de cobranza debe tener la **estructura exacta** que el sistema espera para cada aseguradora y ramo.

> La referencia más confiable de las columnas es la **plantilla descargable** (ver *descargar-plantilla*), ya que sus encabezados son la única fuente de verdad compartida con la validación.

## Requisitos generales

- **Columna Póliza (número)**: clave de identificación de la póliza.
- Las columnas requeridas dependen de la aseguradora y ramo seleccionados.
- Si falta una columna crítica, el proceso **rechaza el archivo** con un error de estructura.

## Formato de datos

| Dato | Formato esperado |
|---|---|
| Fecha | tipo fecha (dd/mm/aaaa) procesado por el parser |
| Montos | numéricos; la coma se interpreta como separador de miles |
| Conducto | código que debe coincidir con el catálogo |

## Encodificación

- Los archivos de MetLife suelen venir en **Latin-1**.
- El sistema intenta decodificar `utf-8-sig` primero y, si falla, usa `latin-1` (robustez).

## Columnas por ramo

- **Vida**: usa el layout del parser de Vida (MetLife LSP).
- **GMM**: usa el layout del parser GMM (MetLife GCAYE).
- Autos/Qualitas (placeholder) quedan fuera del selector actual de cobranza.

## Notas

- Antes de procesar, el sistema valida la estructura (R-COB-09) de forma **fail-fast**: si falta una columna crítica, no se crea la bitácora.
- Usa siempre la plantilla del mismo ramo que vas a importar.
