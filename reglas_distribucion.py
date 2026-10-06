"""Reglas comerciales aprobadas; no alteran la fuente ni el Excel completo."""
from decimal import Decimal, InvalidOperation
import re

MARCADOR_REDUCIDO = 'listaPrecios:reducida:disponibilidad:v1'
LINEAS_EXCLUIDAS = frozenset((Decimal(85), Decimal(104)))
PRECIOS_EXCLUIDOS = frozenset((Decimal('0'), Decimal('0.5'), Decimal('1')))
NUMERO = re.compile(r'[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?')

def numero(valor, campo):
    texto = str(valor).strip()
    if isinstance(valor, bool) or not NUMERO.fullmatch(texto):
        raise ValueError(f'{campo}: valor no numerico; revisar antes de distribuir.')
    try:
        return Decimal(texto.replace(',', ''))
    except InvalidOperation as error:
        raise ValueError(f'{campo}: numero invalido.') from error

def motivos_exclusion(linea, precio):
    linea, precio = numero(linea, 'Linea'), numero(precio, 'Precio de Lista')
    motivos = []
    if linea in LINEAS_EXCLUIDAS: motivos.append(f'Linea {int(linea)}')
    if precio in PRECIOS_EXCLUIDOS: motivos.append(f'Precio {precio:.2f}')
    return motivos

def disponibilidad(valor):
    return '' if numero(valor, 'Existencia') == 0 else 'D'
