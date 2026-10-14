"""Ejecuta todas las etapas aprobadas y exporta un Excel nuevo."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
from limpieza_controles import limpiar_controles
from limpieza_espacios import limpiar_espacios
from correccion_caracteres import corregir_caracteres
from validacion_numerica import validar_numeros
from revision_texto import revisar_texto
from exportacion_excel import exportar_excel
from revisiones_aceptadas import cargar_revisiones


def generar_excel(ruta, destino, encabezados, numericas, textos, corregir, encoding='cp1252',
                  *, destino_reducido=None):
    ruta, destino = Path(ruta), Path(destino)
    revisiones, archivo_revisiones = cargar_revisiones(ruta)
    if destino.suffix.lower() != '.xlsx':
        raise ValueError('La salida debe terminar en .xlsx.')
    if destino.exists() or ruta.resolve() == destino.resolve():
        raise ValueError('El destino existe o coincide con la entrada.')
    reducido = (Path(destino_reducido) if destino_reducido is not None
                else destino.with_name(destino.stem + '_reducida.xlsx'))
    if reducido.suffix.lower() != '.xlsx' or reducido.resolve() == destino.resolve():
        raise ValueError('El destino reducido debe ser un .xlsx distinto del completo.')
    if reducido.exists() or ruta.resolve() == reducido.resolve():
        raise ValueError('El destino reducido existe o coincide con la entrada.')
    carpeta = destino.with_name(destino.stem + '_auditoria')
    if carpeta.exists():
        raise ValueError('La carpeta de auditoria ya existe; elige otro destino.')
    original = ruta.read_bytes()
    carpeta.mkdir()
    manifiesto = {'fuente': ruta.name, 'sha256_original': hashlib.sha256(original).hexdigest(),
                  'estado': 'en_proceso', 'lectura_provisional': encoding}
    try:
        if archivo_revisiones:
            copia_revisiones = carpeta/'revisiones_aceptadas.json'
            copia_revisiones.write_text(json.dumps({'version':1,'aceptaciones':{k:sorted(v) for k,v in revisiones.items()}},indent=2),encoding='utf-8')
        copia = carpeta / '00_original.txt'
        copia.write_bytes(original)
        estructura = carpeta / '01_estructura.txt'
        controles = carpeta / '02_controles.txt'
        espacios = carpeta / '03_espacios.txt'
        caracteres = carpeta / '04_caracteres.txt'
        corregir(copia, estructura)
        limpiar_controles(estructura, controles, encabezados)
        limpiar_espacios(controles, espacios, encabezados)
        corregir_caracteres(espacios, caracteres, encabezados)
        numeros = validar_numeros(caracteres, encabezados, numericas)
        texto = revisar_texto(caracteres, encabezados, textos)
        for nombre,reporte in [('validacion_numerica.json',numeros),('revision_texto.json',texto)]:
            (carpeta / nombre).write_text(json.dumps(reporte,ensure_ascii=True,indent=2),encoding='utf-8')
        if ruta.read_bytes() != original:
            raise ValueError('La entrada cambio durante el proceso; vuelve a ejecutar.')
        resumen = exportar_excel(caracteres, destino, encabezados, numeros, texto, encoding, ruta.name, revisiones=revisiones)
        manifiesto.update(resumen)
        manifiesto['estado'] = 'generado_con_incidencias' if resumen['incidencias'] else 'generado'
        manifiesto['sha256_excel'] = hashlib.sha256(destino.read_bytes()).hexdigest()
        manifiesto['excel'] = destino.name
        resumen_reducido = exportar_excel(caracteres, reducido, encabezados, numeros, texto, encoding, ruta.name,
                       reducida=True, revisiones=revisiones)
        manifiesto['filas_reducido'] = resumen_reducido['filas']
        manifiesto['excluidas_reducido'] = len(resumen_reducido['exclusiones'])
        (carpeta/'exclusiones_reducido.json').write_text(json.dumps(resumen_reducido['exclusiones'],ensure_ascii=True,indent=2),encoding='utf-8')
        manifiesto['excel_reducido'] = reducido.name
        manifiesto['sha256_excel_reducido'] = hashlib.sha256(reducido.read_bytes()).hexdigest()
        manifiesto['orden'] = ['Linea ascendente numerica', 'SubLinea ascendente numerica',
                              'Codigo de Articulo ascendente sin distinguir mayusculas']
        return manifiesto
    except Exception as error:
        manifiesto['estado'] = 'fallido'
        manifiesto['error'] = str(error)
        raise
    finally:
        (carpeta / 'proceso.json').write_text(json.dumps(manifiesto,ensure_ascii=True,indent=2),encoding='utf-8')


def destino_por_defecto(ruta):
    return Path(ruta).with_name('Lista_Precios_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.xlsx')
