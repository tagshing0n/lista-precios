# Lista de precios

Herramienta Python para inspeccionar y corregir de forma controlada listas de precios delimitadas por `|`.

Proyecto en desarrollo: primero se asegura la estructura y la conservacion de datos; ya incluye validacion numerica sin modificar valores. La conversion y exportacion final estan pendientes.

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
- Corrige campos vacios adicionales de descripciones mediante distribuciones unicas segun el esquema o contextos ya aprobados.
- Si una anomalia resulta ambigua y no coincide con un contexto aprobado, genera un reporte de incidencias y no produce un TXT parcial.
- Conserva los bytes y saltos de linea de las filas no modificadas.
- Registra los cambios y las huellas SHA-256 de entrada y salida.

Las firmas de correccion dependen del codigo y las descripciones, no de precios, existencias ni numeros de fila; no contienen las filas empresariales. El ejemplo es completamente ficticio y tiene estructura valida, por lo que no necesita correcciones.

## Limites conocidos

La inspeccion intenta UTF-8 y, si falla, usa una vista provisional Latin-1. Esto no identifica con certeza la codificacion original.
La correccion opera sobre bytes con encabezados ASCII; no admite actualmente un encabezado con BOM o UTF-16, aunque la inspeccion puede leerlos.
La salida TXT y su auditoria se escriben por separado: un fallo de disco puede dejar solo la primera.
No se eliminan, renombran o reordenan columnas. La validacion numerica comprueba formatos y marca precios cero; no consulta catalogos oficiales ni aplica otras reglas comerciales.

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

## Validacion numerica

    python listaPrecios.py examples/Lista-Precios_demo.txt --validar-numeros --reporte validacion.json

La entrada debe tener 16 campos por fila y encabezados ASCII, sin BOM.
Los identificadores Almacen, Linea, SubLinea y Codigo SAT admiten digitos ASCII.
Existencia y Precio de Lista admiten signo, punto decimal y comas de miles bien agrupadas: 1,234.50.
Se ignoran solo espacios ASCII externos para evaluar, sin modificar el archivo.
Codigo SAT se conserva como texto: 00123456 no se convierte en 123456.
La longitud SAT distinta de 8, negativos y exceso de decimales respecto al formato observado (3 para existencia, 2 para precio) se reportan como avisos, sin aplicar reglas comerciales.
Vacios, NaN, infinito, letras, separadores ambiguos y agrupaciones incorrectas se reportan sin reemplazarlos por cero.
Los calculos de diagnostico usan Decimal; no se exportan valores convertidos.
El reporte conserva todas las incidencias con numero de linea y valor original, y debe mantenerse privado.
Salida del comando: 0 para formatos validos (puede haber avisos), 2 si hay vacios o formatos invalidos, 1 ante un error de archivo o estructura.

### Precios en cero

Un Precio de Lista igual a cero genera el aviso precio_cero_requiere_revision. El reporte incluye linea, codigo de articulo y valor original. Se conserva como formato valido y no se modifica ni elimina el articulo. Existencia en cero no genera este aviso. El comando mantiene salida 0 cuando solo hay avisos; revisar siempre el reporte.

## Revision de texto

    python listaPrecios.py examples/Lista-Precios_demo.txt --revisar-texto --reporte texto.json

Cuenta vacios, espacios externos e internos multiples, codigos formados solo por digitos, ceros iniciales, puntos aislados, controles ASCII y bytes no ASCII. No modifica ningun valor ni considera automaticamente erroneos los textos numericos, vacios o simbolos.
El reporte incluye hasta cinco numeros de linea por categoria y el detalle completo de todos los campos con controles o bytes no ASCII.
Las vistas Latin-1, Windows-1252 y CP850 son comparaciones para revision humana: no identifican por si mismas la codificacion ni autorizan reemplazos. Los bytes originales se guardan en hexadecimal, incluso si una vista no puede decodificar un caracter.
No se eliminan tabuladores, espacios especiales, acentos ni puntos. Las reglas de limpieza se definiran tras revisar los casos.
La revision devuelve 0 si termina (aunque haya observaciones), y 1 por errores de archivo o estructura.
Los reportes contienen informacion del archivo de entrada y permanecen privados.

## Limpieza aprobada de controles

    python listaPrecios.py archivo_estructura.txt --limpiar-controles --salida archivo_controles.txt

Requiere una entrada con estructura valida. Aplica solo a Descripcion 1, 2, 3 y Extendida:
- Sustituye cada tabulador por un espacio ASCII, sin comprimir espacios existentes.
- Deja vacio un campo compuesto exclusivamente por bytes nulos (00).
- Conserva nulos mezclados con texto o espacios y los registra como pendientes.

No modifica codigos, precios, acentos, comillas, puntos, espacios externos ni otros bytes.
Conserva las filas, las columnas y los saltos LF/CRLF, incluido un archivo sin salto final.
Genera un TXT nuevo y una auditoria JSON con linea, columna, regla, codigo de articulo y bytes antes/despues; no sobrescribe archivos.
La auditoria permite reconstruir los campos originales. Ambos archivos son privados y quedan excluidos de Git.
La codificacion sigue sin confirmarse; esta limpieza opera en bytes y no recodifica texto.

## Correccion de estructura reutilizable

Con --corregir, las filas de 16 campos permanecen intactas.
Para filas de 17 campos se evaluan todas las eliminaciones posibles de un campo vacio (solo espacios ASCII), comprobando las posiciones numericas, el codigo no vacio, la unidad de 1 a 8 letras mayusculas y el SAT de 8 digitos.
Solo se retiran campos del bloque de descripciones. Si las alternativas compatibles asignan los mismos valores a las mismas columnas (ignorando solo espacios externos para comparar), se permite una correccion.
Una distribucion anteriormente aprobada se reconoce por el codigo y las cinco partes del bloque de descripciones; permanece valida al cambiar precios, existencias o el orden de las filas.
Una nueva ambiguedad, una descripcion cambiada que invalide la aprobacion o unas anclas incompatibles producen un reporte .incidencias.json con todas las filas pendientes y sus bytes, sin generar un TXT parcial.
Estas comprobaciones son conservadoras y dependen del esquema observado; no verifican catalogos ni reconstruyen textos que contengan pipetas legitimas.
La auditoria indica la regla usada y conserva cada campo retirado. No se descartan valores no vacios.

## Limpieza de espacios externos

    python listaPrecios.py archivo_controles.txt --limpiar-espacios --salida archivo_espacios.txt

Recorta exclusivamente espacios comunes ASCII (byte 20) al inicio y final de todos los campos y encabezados.
Los campos compuestos solo por esos espacios quedan vacios; no desaparecen columnas ni filas.
Conserva espacios internos, codigos con ceros iniciales, comas, puntos, acentos y cualquier byte no ASCII.
No recorta espacios especiales como A0 ni intenta decidir si representan espacios o letras en otra codificacion.
La auditoria compacta registra por linea y columna las cantidades retiradas a izquierda y derecha. Esto permite reconstruir los bytes originales sin repetir los largos rellenos de espacios.
Produce una copia y no sobrescribe entradas ni resultados previos. TXT y auditoria se escriben por separado.
Orden de etapas: corregir estructura, limpiar controles, limpiar espacios y volver a validar.
Las sustituciones de caracteres especiales siguen pendientes de revisar; no hay conversion general de codificacion.
