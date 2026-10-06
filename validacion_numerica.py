"""Validacion de formatos numericos sin modificar los datos de entrada."""
import hashlib
import re
from decimal import Decimal

ENTERO = re.compile(rb'[0-9]+')
DECIMAL = re.compile(rb'[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?')
IDENTIFICADORES = {'Almacen', 'Linea', 'SubLinea', 'Codigo SAT'}
PRECISIONES = {'Existencia': 3, 'Precio de Lista': 2}


def clasificar(columna, original):
    """Usa una vista sin espacios ASCII externos; conserva el original."""
    valor = original.strip(b' ')
    if not valor:
        return 'vacio', None, []
    patron = ENTERO if columna in IDENTIFICADORES else DECIMAL
    if not patron.fullmatch(valor):
        return 'invalido', None, []
    numero = Decimal(valor.replace(b',', b'').decode('ascii'))
    avisos = []
    if columna == 'Precio de Lista' and numero == 0:
        avisos.append('precio_cero_requiere_revision')
    if numero < 0:
        avisos.append('negativo_requiere_revision')
    if columna == 'Codigo SAT' and len(valor) != 8:
        avisos.append('longitud_sat_distinta_de_8')
    decimales = len(valor.split(b'.')[1]) if b'.' in valor else 0
    if columna in PRECISIONES and decimales > PRECISIONES[columna]:
        avisos.append('mas_decimales_que_el_formato_observado')
    return 'valido', numero, avisos


def validar_numeros(ruta, encabezados, columnas):
    resumen = {
        c: dict(validos=0, vacios=0, invalidos=0, con_miles=0, ceros=0,
                ceros_iniciales=0, negativos=0, avisos=0)
        for c in columnas
    }
    posiciones = {c: encabezados.index(c) for c in columnas}
    incidencias = []
    huella = hashlib.sha256()
    filas = 0
    with ruta.open('rb') as archivo:
        cabecera = archivo.readline()
        huella.update(cabecera)
        if [c.strip(b' ') for c in cabecera.rstrip(b'\r\n').split(b'|')] != [
            c.encode('ascii') for c in encabezados
        ]:
            raise ValueError('Encabezados incompatibles con la validacion numerica.')
        for linea, original in enumerate(archivo, 2):
            huella.update(original)
            campos = original.rstrip(b'\r\n').split(b'|')
            if len(campos) != len(encabezados):
                raise ValueError(f'Linea {linea}: estructura incorrecta; primero revisar los campos.')
            filas += 1
            for columna, posicion in posiciones.items():
                campo = campos[posicion]
                estado, numero, avisos = clasificar(columna, campo)
                cuenta = resumen[columna]
                cuenta[{'valido': 'validos', 'vacio': 'vacios', 'invalido': 'invalidos'}[estado]] += 1
                if estado == 'valido':
                    valor = campo.strip(b' ')
                    cuenta['con_miles'] += b',' in valor
                    cuenta['ceros'] += numero == 0
                    cuenta['negativos'] += numero < 0
                    cuenta['ceros_iniciales'] += bool(re.match(rb'^0[0-9]', valor))
                cuenta['avisos'] += bool(avisos)
                if estado != 'valido' or avisos:
                    incidencias.append({
                        'linea': linea, 'columna': columna, 'estado': estado,
                        'codigo_articulo': campos[encabezados.index('Codigo de Articulo')].strip(b' ').decode('latin1'),
                        'valor_original': campo.decode('latin1'),
                        'bytes_originales_hex': campo.hex(), 'avisos': avisos,
                    })
    return {
        'sha256_entrada': huella.hexdigest(), 'filas': filas,
        'alcance': 'Formato numerico y aviso de precio cero; no verifica catalogos ni otras reglas comerciales.',
        'convencion': 'Punto decimal; coma de miles agrupada en bloques de tres.',
        'resumen': resumen, 'incidencias': incidencias,
    }
