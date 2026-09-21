'''Inspeccion y correccion controlada de la estructura de la lista de precios.'''
from pathlib import Path
from collections import Counter
import argparse
import unicodedata

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


CORRECCIONES_APROBADAS = {'dac4d9850eb9746b5d5d9c0a16567244d3d870b5ba2244f2fc27f2501f72ef2d': 10, 'f7bf7356dad76e78e55b35e29a0588469cba716a3a4bfc29e5e35d4ce37fdbb8': 11, '55f95fa1b2e4338f68d9c854a9f533599137011e75ff857eff8dc4a5fcf002f1': 10}


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
        posicion = CORRECCIONES_APROBADAS.get(huella)
        if len(campos) != 17 or posicion is None or campos[posicion].strip(b' '):
            pendientes.append(numero)
            continue
        eliminado = campos[posicion]
        nuevos = campos[:posicion] + campos[posicion + 1:]
        if len(nuevos) != 16:
            raise ValueError('La correccion no produce 16 campos.')
        resultado.append(b'|'.join(nuevos) + terminador)
        cambios.append({
            'linea': numero,
            'codigo_articulo': campos[6].strip(b' ').decode('ascii'),
            'campo_eliminado_1_based': posicion + 1,
            'bytes_eliminados_hex': eliminado.hex(),
            'sha256_fila_original': huella,
        })
    if pendientes:
        raise ValueError('Filas sin correccion aprobada; no se genero salida: ' + str(pendientes[:20]))
    salida = b''.join(resultado)
    if len(resultado) != len(lineas):
        raise ValueError('Cambio inesperado en el numero de filas.')
    reporte = destino.with_suffix('.auditoria.json')
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
        'politica': 'Solo filas exactas previamente aprobadas. Sin conversion de tipos.',
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
    parser.add_argument('--corregir', action='store_true', help='Aplicar solo las correcciones aprobadas.')
    parser.add_argument('--salida', type=Path, help='Destino del TXT corregido.')
    args = parser.parse_args()
    try:
        if args.corregir:
            destino = args.salida or args.archivo.with_name('Lista-Precios_estructura.txt')
            corregir_estructura(args.archivo, destino)
        else:
            inspeccionar(args.archivo, args.encoding)
    except (OSError, UnicodeError, ValueError, LookupError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
