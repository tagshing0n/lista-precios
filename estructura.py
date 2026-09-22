"""Seleccion conservadora de correcciones para filas de 17 campos."""
import hashlib
import re
from validacion_numerica import clasificar


def firma_contexto(campos):
    """Excluye precios, existencias y numero de fila; no expone datos en el codigo."""
    return hashlib.sha256(b'|'.join(c.strip(b' ') for c in [campos[6], *campos[9:14]])).hexdigest()


def compatible(campos):
    if len(campos) != 16 or not campos[6].strip(b' '):
        return False
    for posicion, nombre in ((0, 'Almacen'), (1, 'Linea'), (3, 'SubLinea'),
                             (5, 'Existencia'), (7, 'Precio de Lista')):
        if clasificar(nombre, campos[posicion])[0] != 'valido':
            return False
    # Anclas conservadoras del formato observado; no validan catalogos oficiales.
    return bool(re.fullmatch(rb'[A-Z]{1,8}', campos[13].strip(b' '))) and bool(
        re.fullmatch(rb'[0-9]{8}', campos[14].strip(b' ')))


def elegir_correccion(campos, aprobadas):
    if len(campos) != 17:
        return None, 'cantidad_de_campos_no_admitida'
    alternativas = {}
    posiciones_descripcion = []
    for i, campo in enumerate(campos):
        if campo.strip(b' '):
            continue
        candidato = campos[:i] + campos[i + 1:]
        if not compatible(candidato):
            continue
        distribucion = tuple(v.strip(b' ') for v in candidato)
        alternativas.setdefault(distribucion, []).append(i)
        if 9 <= i <= 13:
            posiciones_descripcion.append(i)
    if not posiciones_descripcion:
        return None, 'sin_campo_vacio_de_descripcion_con_anclas_validas'
    aprobada = aprobadas.get(firma_contexto(campos))
    if aprobada in posiciones_descripcion:
        return aprobada, 'distribucion_previamente_aprobada'
    if len(alternativas) == 1:
        # Solo varia que campo vacio redundante se retira; el resto se conserva.
        return posiciones_descripcion[0], 'distribucion_unica_segun_esquema'
    return None, 'distribuciones_ambiguas_requieren_revision'
