"""Sustituciones contextuales aprobadas, sin recodificar el archivo."""
import hashlib
import json
import re
from limpieza_controles import DESCRIPCIONES

# Bytes originales observados -> palabra aprobada representada en Windows-1252.
REGLAS = (
    ('pinon', b'PI\xa5ON', b'PI\xd1ON'),
    ('conexion', b'CONEXI\xe0N', b'CONEXI\xd3N'),
    ('conexiones', b'CONEXI\xe0NES', b'CONEXIONES'),
    ('tuberia', b'TUBER\xd6A', b'TUBER\xcdA'),
)
LIMITES = rb'A-Za-z0-9_\x80-\xff'
PATRONES = tuple(
    (nombre, re.compile(rb'(?<![' + LIMITES + rb'])' + re.escape(origen)
                        + rb'(?![' + LIMITES + rb'])'), destino)
    for nombre, origen, destino in REGLAS
)


def transformar_palabras(original):
    nuevo = original
    aplicadas = {}
    for nombre, patron, destino in PATRONES:
        nuevo, cantidad = patron.subn(destino, nuevo)
        if cantidad:
            aplicadas[nombre] = cantidad
    return nuevo, aplicadas


def corregir_caracteres(ruta, destino, encabezados):
    auditoria = destino.with_suffix('.auditoria.json')
    if ruta.resolve() in (destino.resolve(), auditoria.resolve()):
        raise ValueError('La salida no puede reemplazar la entrada.')
    if destino.resolve() == auditoria.resolve():
        raise ValueError('La salida y la auditoria deben ser diferentes.')
    if destino.exists() or auditoria.exists():
        raise ValueError('La salida o su auditoria ya existe; elige otro destino.')
    entrada = ruta.read_bytes()
    if not entrada:
        raise ValueError('El archivo esta vacio.')
    lineas = entrada.split(b'\n')
    salto_final = lineas[-1] == b''
    if salto_final:
        lineas.pop()
    if [c.strip(b' ') for c in lineas[0].removesuffix(b'\r').split(b'|')] != [
        c.encode('ascii') for c in encabezados
    ]:
        raise ValueError('El encabezado no coincide con el esquema aprobado.')
    posiciones = {c: encabezados.index(c) for c in DESCRIPCIONES}
    resultado = [lineas[0]]
    cambios = []
    totales = {nombre: 0 for nombre, _, _ in REGLAS}
    for numero, original in enumerate(lineas[1:], 2):
        terminador = b'\r' if original.endswith(b'\r') else b''
        cuerpo = original[:-1] if terminador else original
        campos = cuerpo.split(b'|')
        if len(campos) != len(encabezados):
            raise ValueError(f'Linea {numero}: estructura incorrecta; no se genero salida.')
        for columna, posicion in posiciones.items():
            anterior = campos[posicion]
            nuevo, aplicadas = transformar_palabras(anterior)
            if not aplicadas:
                continue
            cambios.append({
                'linea': numero, 'columna': columna,
                'codigo_articulo_bytes_hex': campos[encabezados.index('Codigo de Articulo')].hex(),
                'original_hex': anterior.hex(), 'nuevo_hex': nuevo.hex(),
                'sustituciones': aplicadas,
            })
            for regla, cantidad in aplicadas.items():
                totales[regla] += cantidad
            campos[posicion] = nuevo
        resultado.append(b'|'.join(campos) + terminador)
    salida = b'\n'.join(resultado) + (b'\n' if salto_final else b'')
    registro = {
        'sha256_entrada': hashlib.sha256(entrada).hexdigest(),
        'sha256_salida': hashlib.sha256(salida).hexdigest(),
        'filas_datos': len(lineas) - 1,
        'campos_modificados': len(cambios),
        'sustituciones_por_regla': totales,
        'reglas': {nombre: {'origen_hex': origen.hex(), 'destino_hex': nuevo.hex()}
                   for nombre, origen, nuevo in REGLAS},
        'alcance': 'Solo palabras completas aprobadas en las cuatro descripciones.',
        'codificacion': 'No se recodifica el archivo; solo bytes exactos aprobados.',
        'cambios': cambios,
    }
    with destino.open('xb') as archivo:
        archivo.write(salida)
    with auditoria.open('x', encoding='utf-8') as archivo:
        json.dump(registro, archivo, ensure_ascii=True, indent=2)
    return registro
