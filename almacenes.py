"""Identidad visual de los almacenes; no modifica los datos del TXT."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Presentacion:
    nombre: str
    titulo: str
    encabezados: str
    edicion: str


ALMACENES = {
    'adelar': Presentacion('ADELAR', '12264B', '193C63', 'A62436'),
    'egarama-mexico': Presentacion('EGARAMA MÉXICO', '008000', '008000', 'A62436'),
    'egarama-queretaro': Presentacion('EGARAMA QUERÉTARO', 'ED2100', 'ED2100', '12264B'),
}


def obtener_presentacion(almacen):
    try:
        return ALMACENES[almacen]
    except KeyError as error:
        raise ValueError(f'Almacen desconocido: {almacen}') from error


def seleccionar_almacen():
    claves = tuple(ALMACENES)
    print('\nSelecciona el almacen para la lista de precios:')
    for numero, clave in enumerate(claves, 1):
        print(f'  {numero}. {ALMACENES[clave].nombre}')
    print('  0. Salir')
    while True:
        opcion = input('Opcion: ').strip()
        if opcion == '0':
            return None
        if opcion in ('1', '2', '3'):
            return claves[int(opcion) - 1]
        print('Opcion invalida. Escribe 1, 2, 3 o 0 para salir.')
