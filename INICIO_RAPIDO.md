# Uso con doble clic en Windows

1. Instala Python 3.11 o posterior y activa **Add Python to PATH**.
2. Abre **Instalar_dependencias.cmd**. Requiere Internet para descargar las
   dependencias. Crea un entorno `.venv` local, sin cambiar el Python del sistema.
3. Copia a `datos` estos archivos:
   - `Lista-Precios.txt` actualizado.
   - `logo_empresa.jpeg`.
   - `Lista-Precios.revisiones.json`, si tienes las aceptaciones anteriores.
4. Abre **Generar_listas.cmd**. Espera el mensaje de finalizacion; puede tardar
   varios minutos. La ventana permanece abierta para consultar el resultado.
5. Abre la nueva carpeta con fecha y hora dentro de `outputs`.

Se generan `Lista_Precios.xlsx` (respaldo completo),
`Lista_Precios_reducida.xlsx` (uso interno, con incidencias) y
`Lista_Precios_Final.xlsx` (para distribuir). La auditoria y `ejecucion.json`
permiten comprobar el resultado. Un fallo conserva sus archivos para diagnostico;
no distribuyas una ejecucion cuyo estado no sea `completado`.

Para actualizar, reemplaza solamente el TXT en `datos` y ejecuta de nuevo
**Generar_listas.cmd**. Cada ejecucion usa una carpeta nueva y no sobrescribe las
listas anteriores. La fecha de edicion es la fecha de generacion del equipo.

No necesitas Excel ni Codex para generar los libros. Instala **Open Sans Light**
en el equipo donde los visualizaras para conservar la tipografia.

Al trasladar el proyecto, copia el codigo y tus archivos privados de `datos`,
pero no copies `.venv`: ejecuta el instalador en el nuevo equipo. El TXT, el logo,
las decisiones privadas y los resultados no se suben al repositorio.
