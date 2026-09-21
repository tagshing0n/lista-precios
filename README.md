# Lista de precios

Herramienta Python para inspeccionar y corregir de forma controlada listas de precios delimitadas por `|`.

Proyecto en desarrollo: primero se asegura la estructura y la conservacion de datos; la conversion numerica y la exportacion final estan pendientes.

## Requisitos

Python 3.10 o posterior. Solo utiliza la biblioteca estandar; no requiere instalar paquetes.

## Uso

Desde esta carpeta:

```sh
python listaPrecios.py examples/Lista-Precios_demo.txt
python listaPrecios.py examples/Lista-Precios_demo.txt --corregir --salida demo_estructura.txt
python -m unittest discover -s tests -v
```

El segundo comando genera una copia y una auditoria JSON. No sobrescribe salidas existentes.

Para trabajar con datos privados, indica la ruta del archivo original fuera del repositorio.
Sin argumentos busca `Lista-Precios.txt` junto al programa.

## Comportamiento actual

- Comprueba 16 encabezados y cuenta los campos de cada fila.
- Inspecciona caracteres especiales y espacios externos en los encabezados.
- Mantiene como texto los valores originales; no convierte precios, cantidades ni codigos.
- Corrige exclusivamente tres firmas de filas previamente revisadas y aprobadas.
- Si cambia una de esas filas o aparece otra anomalia, se detiene sin generar salida.
- Conserva los bytes y saltos de linea de las filas no modificadas.
- Registra los cambios y las huellas SHA-256 de entrada y salida.

Las firmas de correccion no contienen las filas empresariales. El ejemplo es completamente ficticio y tiene estructura valida, por lo que no necesita correcciones.

## Limites conocidos

La inspeccion intenta UTF-8 y, si falla, usa una vista provisional Latin-1. Esto no identifica con certeza la codificacion original.
La correccion opera sobre bytes con encabezados ASCII; no admite actualmente un encabezado con BOM o UTF-16, aunque la inspeccion puede leerlos.
La salida TXT y su auditoria se escriben por separado: un fallo de disco puede dejar solo la primera.
Todavia no se validan valores numericos ni se eliminan, renombran o reordenan columnas.

## Datos privados

No incluir listas reales, precios, codigos de clientes ni resultados empresariales en Git.
El archivo `.gitignore` excluye TXT (salvo ejemplos), JSON, hojas de calculo, carpetas de datos y temporales.
Revisar siempre `git diff --cached` antes de un commit: las reglas no protegen datos pegados dentro del codigo o la documentacion.

## Trabajo diario

1. Crear una rama: `git switch -c mejora/nombre-del-cambio`.
2. Hacer un cambio pequeno y ejecutar las pruebas.
3. Revisar `git status` y `git diff`.
4. Preparar solo los archivos deseados: `git add ruta-del-archivo`.
5. Revisar `git diff --cached`.
6. Guardar: `git commit -m "Describe el cambio"`.
7. Subir la rama: `git push -u origin mejora/nombre-del-cambio`.
8. Abrir un pull request hacia `main`, revisar y fusionar.

Para ver el historial: `git log --oneline`.
Para deshacer un commit ya compartido, usar `git revert HASH`: crea otro commit que revierte sus cambios.
Un commit protege solo los archivos versionados. Los datos excluidos necesitan su propio respaldo.
