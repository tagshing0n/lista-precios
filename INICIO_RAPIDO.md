# Uso con doble clic en Windows

1. Instala Python 3.11 o posterior y activa **Add Python to PATH**.
2. Abre **Instalar_dependencias.cmd**. Requiere Internet para descargar las
   dependencias. Crea un entorno `.venv` local, sin cambiar el Python del sistema.
3. Copia a `datos` estos archivos:
   - `Lista-Precios.txt` actualizado.
   - `logo_empresa.jpeg`.
   - `Lista-Precios.revisiones.json`, si tienes las aceptaciones anteriores.
4. Abre **Generar_listas.cmd** y selecciona **1. ADELAR**, **2. EGARAMA MÉXICO**
   o **3. EGARAMA QUERÉTARO**. La opcion **0** permite salir sin generar archivos.
   Espera el mensaje de finalizacion; puede tardar
   varios minutos. La ventana permanece abierta para consultar el resultado.
5. Abre la nueva carpeta con fecha y hora dentro de `outputs`.

Se generan `Lista_Precios_{ALMACEN}_{AAAA-MM-DD}.xlsx` (respaldo completo),
`Lista_Precios_reducida_{ALMACEN}_{AAAA-MM-DD}.xlsx` (uso interno, con incidencias) y
`Lista_Precios_Final_{ALMACEN}_{AAAA-MM-DD}.xlsx` (para distribuir).
Por ejemplo: `Lista_Precios_Final_ADELAR_2026-10-14.xlsx`.
Los otros almacenes se identifican como `EGARAMA_MÉXICO` y `EGARAMA_QUERÉTARO`.
La fecha corresponde al dia de generacion del equipo. La auditoria y `ejecucion.json`
permiten comprobar el resultado. Un fallo conserva sus archivos para diagnostico;
no distribuyas una ejecucion cuyo estado no sea `completado`.

Para actualizar, reemplaza solamente el TXT en `datos` y ejecuta de nuevo
**Generar_listas.cmd**. Cada ejecucion usa una carpeta nueva y no sobrescribe las
listas anteriores. La fecha de edicion es la fecha de generacion del equipo.

La seleccion cambia el nombre y los colores de la lista comercial; no filtra
articulos por almacen ni modifica la limpieza. Coloca previamente el TXT del
almacen correspondiente en `datos/Lista-Precios.txt`. Se conserva el logo de
`datos/logo_empresa.jpeg`. El almacen elegido queda registrado en `ejecucion.json`.

ADELAR mantiene sus colores actuales. EGARAMA MÉXICO usa verde `#008000` en
titulo y encabezados. EGARAMA QUERÉTARO usa rojo `#ED2100` y la franja de edicion
azul `#12264B`. Las tres versiones muestran solamente la leyenda:
"Disponibilidad: D = disponible | Celda vacia = agotado. Los precios de lista no incluyen IVA".

Para ejecuciones automatizadas se puede omitir el menu con
`python generar_listas.py --almacen adelar` (tambien `egarama-mexico` o
`egarama-queretaro`).

No necesitas Excel ni Codex para generar los libros. Instala **Open Sans Light**
en el equipo donde los visualizaras para conservar la tipografia.

Al trasladar el proyecto, copia el codigo y tus archivos privados de `datos`,
pero no copies `.venv`: ejecuta el instalador en el nuevo equipo. El TXT, el logo,
las decisiones privadas y los resultados no se suben al repositorio.
