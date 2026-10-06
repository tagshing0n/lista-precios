# Lista de precios

## Presentacion comercial independiente

    python presentacion_comercial.py ruta/Lista_Precios_observaciones_reducida.xlsx --salida Lista_Comercial.xlsx

Este modulo genera un libro nuevo para vendedores y clientes sin modificar la limpieza ni el archivo de trabajo. Exporta exclusivamente, en este orden: Nombre de Linea, Codigo de Articulo, Precio de Lista, Marca, Descripcion 1, Descripcion 2, Descripcion 3, Descripcion Extendida, Unidad de Medida, Codigo SAT y Existencia. Mantiene todas las filas y su orden.

Existencia se transforma en celda vacia si es cero y D si es distinta de cero, incluidos negativos segun la regla aprobada. Una existencia vacia o no numerica detiene la exportacion; no se confunde con agotado. El libro se construye desde cero: no copia Incidencias, auditorias, columnas ocultas, comentarios, vinculos o cantidades internas. Las columnas futuras quedan excluidas salvo autorizacion explicita en COLUMNAS. Los precios cero se conservan como cero.

El diseño inicial incluye titulo, leyenda de disponibilidad, filtros, encabezados fijos, texto ajustado y precios con dos decimales. La configuracion de impresion es horizontal A3, una pagina de ancho. No sobrescribe resultados. El estilo puede ajustarse en este modulo sin cambiar las reglas de limpieza.

Herramienta Python para inspeccionar y corregir de forma controlada listas de precios delimitadas por `|`.

Proyecto en desarrollo: primero se asegura la estructura y la conservacion de datos; ya incluye validacion numerica sin modificar valores. Incluye exportacion Excel con los casos pendientes en una hoja de incidencias.

## Requisitos

Python 3.10 o posterior. La limpieza utiliza la biblioteca estandar. Para exportar Excel y ejecutar todas las pruebas instala: python -m pip install -r requirements.txt.

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
- Conserva los valores originales en los TXT; la exportacion Excel convierte numeros validos y mantiene los codigos como texto.
- Corrige campos vacios adicionales de descripciones mediante distribuciones unicas segun el esquema o contextos ya aprobados.
- Si una anomalia resulta ambigua y no coincide con un contexto aprobado, genera un reporte de incidencias y no produce un TXT parcial.
- Conserva los bytes y saltos de linea de las filas no modificadas.
- Registra los cambios y las huellas SHA-256 de entrada y salida.

Las firmas de correccion dependen del codigo y las descripciones, no de precios, existencias ni numeros de fila; no contienen las filas empresariales. El ejemplo es completamente ficticio y tiene estructura valida, por lo que no necesita correcciones.

## Limites conocidos

La inspeccion intenta UTF-8 y, si falla, usa una vista provisional Latin-1. Esto no identifica con certeza la codificacion original.
La correccion opera sobre bytes con encabezados ASCII; no admite actualmente un encabezado con BOM o UTF-16, aunque la inspeccion puede leerlos.
La salida TXT y su auditoria se escriben por separado: un fallo de disco puede dejar solo la primera.
Los TXT conservan las 16 columnas. Se generan dos Excel: completo y reducido, ambos con Existencia al final. La validacion numerica comprueba formatos y marca precios cero; no consulta catalogos oficiales ni aplica otras reglas comerciales.

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
Este diagnostico no modifica tabuladores, espacios especiales, acentos ni puntos. Las etapas de limpieza aplican solo las reglas aprobadas descritas abajo.
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
Hay 16 sustituciones contextuales aprobadas; otros casos siguen pendientes. No hay conversion general de codificacion.

## Correcciones contextuales aprobadas

    python listaPrecios.py archivo_espacios.txt --corregir-caracteres --salida archivo_caracteres.txt

Aplica exclusivamente en Descripcion 1, 2, 3 y Extendida estas palabras exactas (vista Windows-1252):
- PI¥ON -> PIÑON
- CONEXIàN -> CONEXIÓN
- CONEXIàNES -> CONEXIONES
- TUBERÖA -> TUBERÍA
- CIGUE¥AL -> CIGÜEÑAL
- CIGšE¥AL -> CIGÜEÑAL
- TEFLàN -> TEFLÓN
- CAMIàN -> CAMIÓN
- A¥OS -> AÑOS
- BRASILE¥O -> BRASILEÑO
- DISE¥O -> DISEÑO
- MU¥ON -> MUÑÓN
- ANTIEMPA¥ANTE -> ANTIEMPAÑANTE
- U¥A -> UÑA
- ARA¥A -> ARAÑA
- MALIBé -> MALIBÚ

No reemplaza partes dentro de palabras mas largas o codigos. Los limites de palabra excluyen letras, numeros, guion bajo y bytes no ASCII adyacentes.
No modifica Codigo de Articulo, Codigo Fabricante, Marca ni otras columnas.
Conserva todos los bytes fuera de las coincidencias. No reinterpreta ni recodifica el archivo completo.
Produce copia y auditoria con bytes originales/nuevos y cantidades por regla; no sobrescribe archivos.
Los bytes de estas 16 reglas estan fijados al formato observado y aprobado. Nuevas codificaciones o palabras distintas requieren revision.

## Ejecucion completa

    python -m pip install -r requirements.txt
    python listaPrecios.py ruta/Lista-Precios.txt --generar-excel

El nombre incluye fecha y hora si no indicas --salida. Cada ejecucion conserva una carpeta de auditoria compartida con copia exacta del origen, intermedios y reportes. No sobrescribe resultados existentes. Si falla la segunda exportacion, el registro indica el fallo y conserva el primer libro ya generado.

    python listaPrecios.py ruta/Lista-Precios.txt --generar-excel --salida Lista_Precios.xlsx

El comando genera dos libros: Lista_Precios.xlsx con las 16 columnas (Nombre de SubLinea despues de SubLinea), y Lista_Precios_reducida.xlsx con 14 columnas, sin Nombre de SubLinea ni Codigo Fabricante. Ambos mantienen Existencia al final. Las pipetas son delimitadores del TXT, no columnas. Intermedios y auditorias conservan las 16 columnas originales.

Ambos libros ordenan las filas por Linea numerica ascendente, luego SubLinea numerica ascendente y finalmente Codigo de Articulo alfabeticamente, sin distinguir mayusculas. Los codigos se comparan como texto: 10 precede a 2. Los empates conservan el orden original. Los identificadores con ceros iniciales se ordenan por su valor numerico sin cambiar el texto guardado. Valores no numericos de Linea/SubLinea se conservan despues de los numeros y los vacios al final. El orden textual es Unicode normalizado; signos y letras acentuadas pueden diferir de la intercalacion regional de Excel.

En Incidencias, Linea TXT conserva la referencia al origen y Fila Excel apunta a la nueva posicion ordenada. Ambos libros mantienen el diagnostico completo, incluso de las columnas omitidas en el reducido.
Codigo de Articulo, Codigo Fabricante y Codigo SAT son texto. Precios y existencias validos son numeros; invalidos o valores fuera de precision segura permanecen como texto con aviso. Identificadores con ceros iniciales siguen como texto. Textos que comienzan por = nunca se convierten en formulas.
Se detiene si Excel no puede representar algun valor sin truncar o eliminar caracteres.

### Incidencias

Las aceptaciones individuales se leen de un archivo privado junto al origen: Lista-Precios.revisiones.json. Vinculan cada decision al almacen, linea, sublinea y codigo de articulo mediante una huella. Los precios cero y nombres de linea vacios confirmados se conservan, pero no aparecen como pendientes; los ceros aceptados tampoco se resaltan. Casos nuevos u otras advertencias siguen requiriendo revision. Sin este archivo se muestran todas las observaciones habituales. No equivale a autorizar precios cero o nombres vacios de forma general.

Cada ejecucion copia las aceptaciones utilizadas a su auditoria y cuenta las aplicadas en proceso.json. El diagnostico numerico conserva sus observaciones tecnicas originales; la aceptacion se aplica al generar el Excel. El archivo de decisiones debe conservarse junto al TXT al actualizarlo y queda fuera de Git.

Los casos aceptados siguen visibles en la hoja Incidencias con estado Aceptado y motivo confirmado en origen. La hoja distingue el total de observaciones, aceptadas y pendientes; el filtro Revision permite consultarlas por separado. Una advertencia adicional no aceptada del mismo precio mantiene el caso Pendiente.

Los grados se normalizan a ° solo en descripciones: numeros con unidad C/F, o precedidos por CODO, JIC, ANGULO, ASIENTO o TERMOST/TERMOSTATO. Solo se sustituye el simbolo; cantidades, signos y separadores se conservan. Casos sin contexto claro siguen pendientes.

Los contextos validados de acentos (lista explicita de palabras), diametros Ø con medida en mm y grados no se muestran como sospechosos en el Excel CP1252. El diagnostico JSON conserva todos los campos no ASCII con requiere_revision; un campo que mezcla texto valido y dudoso permanece pendiente. Esta clasificacion no elimina ni modifica el texto. Otras codificaciones mantienen todas las observaciones.

Incluye precios cero, valores invalidos, nombres de linea vacios y comparaciones de caracteres no ASCII (no son automaticamente errores).
La lectura Windows-1252 es provisional y se indica en el libro. Solo aplica las 16 sustituciones aprobadas; no corrige otros simbolos.
El selector Pendiente/Revisado corresponde a esa copia; las decisiones manuales no se importan en futuras ejecuciones.
Si hay ambiguedad estructural no genera Excel; la carpeta de auditoria conserva las incidencias y el estado fallido.
Salidas, originales y reportes estan excluidos de Git.
# Primera versión final para distribución

El Excel completo conserva todas las filas y las cantidades originales. El reducido
excluye las líneas 85 y 104 y los precios exactamente 0, 0.50 y 1.00; otros precios
(por ejemplo 0.51 o 1.01) se conservan. Existencia se muestra como `D` para cualquier
cantidad distinta de cero (también negativa) y vacío para cero. Un valor inválido
impide generar la salida reducida: nunca se interpreta como agotado ni se descarta
silenciosamente.

Las incidencias se mantienen en el reducido como información interna. Para una fila
excluida, `Fila Excel` queda vacía; `Linea TXT` y el código siguen identificando el
registro. La carpeta de auditoría incluye `exclusiones_reducido.json` y el manifiesto
registra las cantidades del completo y del reducido por separado.

Para distribuir a clientes y vendedores, generar un libro comercial nuevo:

```powershell
python presentacion_comercial.py "Lista_Precios_reducida.xlsx" --salida "Lista_Precios_Final_v1.xlsx" --logo "logo_empresa.jpeg" --edicion "Primera edición | 05/10/2026"
```

El logo es un archivo local autorizado por la empresa; no se incluye en el repositorio.
La salida comercial contiene solo las 11 columnas autorizadas, incluida Descripcion 1,
sin Almacen, Linea, SubLinea, cantidades internas ni Incidencias. Reconoce la
disponibilidad del nuevo reducido mediante su marcador de formato y sigue admitiendo
archivos anteriores con cantidades numéricas. Cuando hay columna Linea, aplica también
los filtros aprobados antes de presentar los artículos. Conserva el orden de entrada.
Cada salida requiere un nombre nuevo para no sobrescribir versiones previas.
