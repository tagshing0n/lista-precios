"""Limpieza aprobada de controles en columnas de descripcion."""
import hashlib
import json

DESCRIPCIONES = ('Descripcion 1', 'Descripcion 2', 'Descripcion 3', 'Descripcion Extendida')


def transformar_campo(original):
    if original and not original.strip(b'\x00'):
        return b'', 'campo_solo_nulos_a_vacio'
    if b'\t' in original:
        return original.replace(b'\t', b' '), 'tabulador_a_espacio'
    return original, None


def limpiar_controles(ruta, destino, encabezados):
    """Trabaja sobre bytes para no cambiar la codificacion ni otros caracteres."""
    auditoria = destino.with_suffix('.auditoria.json')
    if ruta.resolve() in (destino.resolve(), auditoria.resolve()):
        raise ValueError('La salida no puede reemplazar la entrada.')
    if destino.resolve() == auditoria.resolve():
        raise ValueError('La salida y la auditoria deben ser archivos diferentes.')
    if destino.exists() or auditoria.exists():
        raise ValueError('La salida o su auditoria ya existe; elige otro destino.')
    entrada = ruta.read_bytes()
    # Se separa solo por LF; se conserva cada CRLF y la ausencia de salto final.
    lineas = entrada.split(b'\n')
    if not entrada:
        raise ValueError('El archivo esta vacio.')
    tiene_salto_final = lineas[-1] == b''
    if tiene_salto_final:
        lineas.pop()
    if [c.strip(b' ') for c in lineas[0].removesuffix(b'\r').split(b'|')] != [
        c.encode('ascii') for c in encabezados
    ]:
        raise ValueError('El encabezado no coincide con el esquema aprobado.')
    posiciones = {c: encabezados.index(c) for c in DESCRIPCIONES}
    cambios = []
    pendientes = []
    salida_lineas = [lineas[0]]
    for numero, original in enumerate(lineas[1:], 2):
        terminador = b'\r' if original.endswith(b'\r') else b''
        cuerpo = original[:-1] if terminador else original
        campos = cuerpo.split(b'|')
        if len(campos) != len(encabezados):
            raise ValueError(f'Linea {numero}: estructura incorrecta; no se genero salida.')
        for columna, posicion in posiciones.items():
            anterior = campos[posicion]
            nuevo, regla = transformar_campo(anterior)
            if regla:
                cambios.append({
                    'linea': numero, 'columna': columna, 'regla': regla,
                    'codigo_articulo': campos[encabezados.index('Codigo de Articulo')].strip(b' ').decode('latin1'),
                    'original_hex': anterior.hex(), 'nuevo_hex': nuevo.hex(),
                    'tabuladores_sustituidos': anterior.count(b'\t'),
                    'nulos_retirados': anterior.count(b'\x00') if regla == 'campo_solo_nulos_a_vacio' else 0,
                })
                campos[posicion] = nuevo
            if b'\x00' in nuevo:
                pendientes.append({'linea': numero, 'columna': columna,
                                   'motivo': 'nulos_mezclados_con_otros_bytes_conservados'})
        salida_lineas.append(b'|'.join(campos) + terminador)
    salida = b'\n'.join(salida_lineas) + (b'\n' if tiene_salto_final else b'')
    registro = {
        'sha256_entrada': hashlib.sha256(entrada).hexdigest(),
        'sha256_salida': hashlib.sha256(salida).hexdigest(),
        'filas_datos': len(lineas) - 1,
        'campos_modificados': len(cambios),
        'tabuladores_sustituidos': sum(c['tabuladores_sustituidos'] for c in cambios),
        'nulos_retirados': sum(c['nulos_retirados'] for c in cambios),
        'alcance': 'Solo las cuatro columnas de descripcion. No recorta ni comprime espacios.',
        'cambios': cambios, 'pendientes': pendientes,
    }
    with destino.open('xb') as archivo:
        archivo.write(salida)
    with auditoria.open('x', encoding='utf-8') as archivo:
        json.dump(registro, archivo, ensure_ascii=True, indent=2)
    return registro
