"""Reconoce contextos aprobados sin aceptar caracteres sueltos globalmente."""
import re

LIMITES = r'A-Za-z0-9_\x80-\uffff'
PALABRAS_VALIDAS = {
    'CONEXIÓN', 'CIGÜEÑAL', 'ESTÁNDAR', 'DIÉSEL', 'PIÑON', 'TUBERÍA',
    'TEFLÓN', 'CAMIÓN', 'AÑOS', 'BRASILEÑO', 'DISEÑO', 'MUÑÓN',
    'ANTIEMPAÑANTE', 'UÑA', 'ARAÑA', 'MALIBÚ',
}
PALABRA = re.compile('(?<!['+LIMITES+'])('+'|'.join(sorted(PALABRAS_VALIDAS))+')(?!['+LIMITES+'])', re.IGNORECASE)
SIMBOLOS = r'[ø§º¦°]'
CONTEXTOS = (
    re.compile(r'(?<![A-Za-z0-9_])[+-]?\d+(?:[.,]\d+)?(?P<grado>'+SIMBOLOS+r')(?=[CF](?:[^A-Za-z]|$))'),
    re.compile(r'\b(?:CODO|JIC|ANGULO|ASIENTO)(?:\s+(?:DE|HEMBRA))?\s*\d+(?P<grado>'+SIMBOLOS+r')'),
    re.compile(r'\bTERMOST(?:ATO)?\s+\d+(?:-\d+)?(?P<grado>'+SIMBOLOS+r')'),
)
DIAMETRO = re.compile(r'Ø\d+(?:[.,]\d+)?\s*mm(?=\b|BALATA)', re.IGNORECASE)


def posiciones_grados(texto):
    return {m.start('grado') for patron in CONTEXTOS for m in patron.finditer(texto)}


def corregir_grados(valor):
    # La decodificacion debe ser exacta para que las posiciones sean posiciones de bytes.
    try:
        texto = valor.decode('cp1252')
    except UnicodeDecodeError:
        return valor, 0
    posiciones = posiciones_grados(texto)
    salida = bytearray(valor)
    cantidad = 0
    for i in posiciones:
        if salida[i] != 0xb0:
            salida[i] = 0xb0
            cantidad += 1
    return bytes(salida), cantidad


def tiene_pendientes(valor, columna):
    if any(b < 32 or b == 127 for b in valor):
        return True
    if columna not in {'Descripcion 1','Descripcion 2','Descripcion 3','Descripcion Extendida'}:
        return any(b >= 128 for b in valor)
    try:
        texto = valor.decode('cp1252')
    except UnicodeDecodeError:
        return True
    reconocidas = set()
    for patron in (PALABRA, DIAMETRO):
        for match in patron.finditer(texto):
            reconocidas.update(range(match.start(), match.end()))
    reconocidas.update(i for i in posiciones_grados(texto) if texto[i] == '°')
    return any(ord(c) >= 128 and i not in reconocidas for i,c in enumerate(texto))
