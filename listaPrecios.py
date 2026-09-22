'''Inspeccion y correccion controlada de la estructura de la lista de precios.'''
from pathlib import Path
from collections import Counter
import argparse
import unicodedata
import json
from validacion_numerica import validar_numeros
from revision_texto import revisar_texto
from limpieza_controles import limpiar_controles
from limpieza_espacios import limpiar_espacios
from correccion_caracteres import corregir_caracteres
from estructura import elegir_correccion, firma_contexto

ENCABEZADOS = (
    'Almacen', 'Linea', 'Nombre de Linea', 'SubLinea',
    'Nombre de SubLinea', 'Existencia', 'Codigo de Articulo',
    'Precio de Lista', 'Marca', 'Descripcion 1', 'Descripcion 2',
    'Descripcion 3', 'Descripcion Extendida', 'Unidad de Medida',
    'Codigo SAT', 'Codigo Fabricante',
)
COLUMNAS_NUMERICAS = (
    'Almacen', 'Linea', 'SubLinea', 'Existencia', 'Precio de Lista', 'Codigo SAT',
)
# Son categorias esperadas; este paso NO convierte ningun valor.
COLUMNAS_TEXTO = tuple(c for c in ENCABEZADOS if c not in COLUMNAS_NUMERICAS)


def inspeccionar(ruta, encoding=None):
    contenido = ruta.read_bytes()
    if not contenido:
        raise ValueError('El archivo esta vacio.')
    if encoding:
        texto = contenido.decode(encoding, errors='strict')
        decision = 'Codificacion indicada: ' + encoding
    elif contenido.startswith((b'\xff\xfe', b'\xfe\xff')):
        texto = contenido.decode('utf-16', errors='strict')
        decision = 'UTF-16 identificado por BOM.'
    else:
        try:
            texto = contenido.decode('utf-8-sig', errors='strict')
            decision = 'Compatible con UTF-8; esto no prueba su origen.'
        except UnicodeDecodeError:
            texto = contenido.decode('latin1', errors='strict')
            decision = ('Vista provisional Latin-1: conserva cada byte, '
                        'pero NO confirma la codificacion del sistema.')
    # Separar solo saltos de linea reales; no controles Unicode como U+0085.
    lineas = texto.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    if lineas[-1] == '':
        lineas.pop()  # El terminador final no es un registro adicional.
    originales = lineas[0].split('|')
    print(decision)
    print('Encabezados encontrados:', len(originales))
    for posicion, original in enumerate(originales, 1):
        esperado = ENCABEZADOS[posicion - 1] if posicion <= len(ENCABEZADOS) else None
        estado = 'EXACTO' if original == esperado else (
            'SOLO ESPACIOS EXTERNOS' if original.strip(' ') == esperado else 'REVISAR'
        )
        print(f'{posicion:02d} | {ascii(original)} | {estado}')
        especiales = [
            'U+{:04X} {}'.format(ord(c), unicodedata.name(c, 'SIN NOMBRE'))
            for c in dict.fromkeys(original) if not 32 <= ord(c) <= 126
        ]
        if especiales:
            print('   Caracteres especiales:', ', '.join(especiales))
    estructura = Counter()
    ejemplos = []
    vacias = 0
    for numero, linea in enumerate(lineas[1:], 2):
        cantidad = len(linea.split('|'))
        estructura[cantidad] += 1
        vacias += not linea.strip()
        if cantidad != len(ENCABEZADOS) and len(ejemplos) < 20:
            ejemplos.append((numero, cantidad))
    print('Filas posteriores al encabezado:', len(lineas) - 1)
    print('Filas vacias (incluidas en el conteo):', vacias)
    print('Cantidad de campos -> filas:', dict(sorted(estructura.items())))
    print('Primeras filas con cantidad distinta de 16:', ejemplos)
    print('Validacion numerica pendiente:', ', '.join(COLUMNAS_NUMERICAS))
    print('No se modifico el archivo ni se eliminaron filas o campos.')


CORRECCIONES_APROBADAS = {'172f918f6fe6cd2e1ce03e04dc5903259bc5dafd59c63de19ad082042886c18a': 10, '9b84902256c5bc53b5ccc23491b6638e8ed54f8f9efd4636e9348d511fde89f7': 11, '80298221c7aeaf267186236ff7399e0e388949f85245438196b35699ef724e07': 10}


def corregir_estructura(ruta, destino):
    import hashlib
    import json
    contenido = ruta.read_bytes()
    lineas = contenido.splitlines(keepends=True)
    if not lineas:
        raise ValueError('El archivo esta vacio.')
    cabecera = lineas[0].rstrip(b'\r\n').split(b'|')
    if [c.strip(b' ') for c in cabecera] != [c.encode('ascii') for c in ENCABEZADOS]:
        raise ValueError('El encabezado no coincide con el esquema aprobado.')
    resultado = [lineas[0]]
    cambios = []
    pendientes = []
    for numero, original in enumerate(lineas[1:], 2):
        cuerpo = original.rstrip(b'\r\n')
        terminador = original[len(cuerpo):]
        campos = cuerpo.split(b'|')
        if len(campos) == 16:
            resultado.append(original)
            continue
        huella = hashlib.sha256(cuerpo).hexdigest()
        posicion, regla = elegir_correccion(campos, CORRECCIONES_APROBADAS)
        if posicion is None:
            pendientes.append({'linea': numero, 'cantidad_campos': len(campos),
                               'motivo': regla, 'fila_original_hex': cuerpo.hex()})
            continue
        eliminado = campos[posicion]
        nuevos = campos[:posicion] + campos[posicion + 1:]
        if len(nuevos) != 16:
            raise ValueError('La correccion no produce 16 campos.')
        resultado.append(b'|'.join(nuevos) + terminador)
        cambios.append({
            'linea': numero,
            'codigo_articulo': campos[6].strip(b' ').decode('latin1'),
            'campo_eliminado_1_based': posicion + 1,
            'regla': regla,
            'bytes_eliminados_hex': eliminado.hex(),
            'sha256_fila_original': huella,
        })
    if pendientes:
        incidencias = destino.with_suffix('.incidencias.json')
        if incidencias.resolve() == ruta.resolve():
            raise ValueError('El reporte no puede reemplazar la entrada.')
        with incidencias.open('x', encoding='utf-8') as archivo:
            json.dump({'sha256_entrada': hashlib.sha256(contenido).hexdigest(),
                       'incidencias': pendientes}, archivo, ensure_ascii=True, indent=2)
        raise ValueError('Filas sin correccion aprobada; no se genero TXT. Reporte: ' + str(incidencias))
    salida = b''.join(resultado)
    if len(resultado) != len(lineas):
        raise ValueError('Cambio inesperado en el numero de filas.')
    reporte = destino.with_suffix('.auditoria.json')
    if destino.resolve() == reporte.resolve():
        raise ValueError('La salida y la auditoria deben ser diferentes.')
    if destino.resolve() == ruta.resolve() or reporte.resolve() == ruta.resolve():
        raise ValueError('La salida no puede reemplazar el archivo original.')
    if destino.exists() or reporte.exists():
        raise ValueError('La salida o su auditoria ya existe; elige otro destino.')
    registro = {
        'entrada': str(ruta.resolve()),
        'salida': str(destino.resolve()),
        'sha256_entrada': hashlib.sha256(contenido).hexdigest(),
        'sha256_salida': hashlib.sha256(salida).hexdigest(),
        'filas_datos': len(lineas) - 1,
        'correcciones': cambios,
        'politica': 'Distribucion unica segun esquema o contexto previamente aprobado. Sin conversion de tipos.',
    }
    with destino.open('xb') as archivo:
        archivo.write(salida)
    with reporte.open('x', encoding='utf-8') as archivo:
        json.dump(registro, archivo, ensure_ascii=True, indent=2)
    print('Filas conservadas:', len(lineas) - 1)
    print('Campos vacios retirados:', len(cambios))
    print('Salida:', destino)
    print('Auditoria:', reporte)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archivo', nargs='?', type=Path,
                        default=Path(__file__).with_name('Lista-Precios.txt'))
    parser.add_argument('--encoding', help='Codificacion confirmada, por ejemplo cp1252.')
    modos = parser.add_mutually_exclusive_group()
    modos.add_argument('--corregir-caracteres', action='store_true', help='Aplicar las cuatro sustituciones aprobadas.')
    modos.add_argument('--limpiar-espacios', action='store_true', help='Recortar solo espacios ASCII externos.')
    modos.add_argument('--limpiar-controles', action='store_true', help='Aplicar reglas aprobadas a descripciones.')
    modos.add_argument('--revisar-texto', action='store_true', help='Revisar texto sin modificarlo.')
    modos.add_argument('--validar-numeros', action='store_true', help='Validar sin modificar los valores.')
    parser.add_argument('--reporte', type=Path, help='Nuevo archivo JSON para la validacion.')
    modos.add_argument('--corregir', action='store_true', help='Aplicar solo las correcciones aprobadas.')
    parser.add_argument('--salida', type=Path, help='Destino del TXT corregido.')
    args = parser.parse_args()
    if args.reporte and not (args.validar_numeros or args.revisar_texto):
        parser.error('--reporte requiere --validar-numeros o --revisar-texto')
    if args.salida and not (args.corregir or args.limpiar_controles or args.limpiar_espacios or args.corregir_caracteres):
        parser.error('--salida requiere un modo de correccion o limpieza')
    try:
        if args.validar_numeros or args.revisar_texto:
            if args.validar_numeros:
                reporte = validar_numeros(args.archivo, ENCABEZADOS, COLUMNAS_NUMERICAS)
            else:
                reporte = revisar_texto(args.archivo, ENCABEZADOS, COLUMNAS_TEXTO)
            if args.reporte:
                if args.reporte.resolve() == args.archivo.resolve():
                    raise ValueError('El reporte no puede reemplazar la entrada.')
                with args.reporte.open('x', encoding='utf-8') as salida:
                    json.dump(reporte, salida, ensure_ascii=True, indent=2)
            print(json.dumps(reporte['resumen'], ensure_ascii=True, indent=2))
            print('Filas validadas:', reporte['filas'])
            print('Incidencias:', len(reporte['incidencias']))
            print('Archivo original sin modificar.')
            if args.validar_numeros and any(c['vacios'] or c['invalidos'] for c in reporte['resumen'].values()):
                parser.exit(2, 'Hay valores vacios o invalidos; revisar el reporte.\n')
        elif args.corregir_caracteres:
            destino = args.salida or args.archivo.with_name('Lista-Precios_caracteres.txt')
            registro = corregir_caracteres(args.archivo, destino, ENCABEZADOS)
            print('Filas conservadas:', registro['filas_datos'])
            print('Campos modificados:', registro['campos_modificados'])
            print('Sustituciones:', registro['sustituciones_por_regla'])
            print('Salida:', destino)
            print('Auditoria:', destino.with_suffix('.auditoria.json'))
        elif args.limpiar_espacios:
            destino = args.salida or args.archivo.with_name('Lista-Precios_espacios.txt')
            registro = limpiar_espacios(args.archivo, destino, ENCABEZADOS)
            print('Filas conservadas:', registro['filas_datos'])
            print('Campos de datos recortados:', registro['campos_datos_modificados'])
            print('Encabezados recortados:', registro['encabezados_modificados'])
            print('Espacios ASCII retirados:', registro['espacios_ascii_retirados'])
            print('Salida:', destino)
            print('Auditoria:', destino.with_suffix('.auditoria.json'))
        elif args.limpiar_controles:
            destino = args.salida or args.archivo.with_name('Lista-Precios_controles.txt')
            registro = limpiar_controles(args.archivo, destino, ENCABEZADOS)
            print('Filas conservadas:', registro['filas_datos'])
            print('Campos modificados:', registro['campos_modificados'])
            print('Tabuladores sustituidos:', registro['tabuladores_sustituidos'])
            print('Nulos retirados:', registro['nulos_retirados'])
            print('Casos pendientes:', len(registro['pendientes']))
            print('Salida:', destino)
            print('Auditoria:', destino.with_suffix('.auditoria.json'))
        elif args.corregir:
            destino = args.salida or args.archivo.with_name('Lista-Precios_estructura.txt')
            corregir_estructura(args.archivo, destino)
        else:
            inspeccionar(args.archivo, args.encoding)
    except (OSError, UnicodeError, ValueError, LookupError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
