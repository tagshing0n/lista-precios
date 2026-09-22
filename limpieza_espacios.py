"""Retira solo espacios ASCII externos, con auditoria compacta reversible."""
import hashlib
import json


def recortar_espacios(campo):
    sin_izquierda = campo.lstrip(b' ')
    limpio = sin_izquierda.rstrip(b' ')
    return limpio, len(campo) - len(sin_izquierda), len(sin_izquierda) - len(limpio)


def limpiar_espacios(ruta, destino, encabezados):
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
    resultado = []
    cambios = []
    campos_datos = 0
    campos_encabezado = 0
    espacios = 0
    for numero, original in enumerate(lineas, 1):
        terminador = b'\r' if original.endswith(b'\r') else b''
        cuerpo = original[:-1] if terminador else original
        campos = cuerpo.split(b'|')
        if len(campos) != len(encabezados):
            raise ValueError(f'Linea {numero}: estructura incorrecta; no se genero salida.')
        recortes = []
        for i, campo in enumerate(campos):
            nuevo, izquierda, derecha = recortar_espacios(campo)
            if izquierda or derecha:
                recortes.append([i + 1, izquierda, derecha])
                campos[i] = nuevo
                espacios += izquierda + derecha
        if recortes:
            cambios.append({'linea': numero, 'recortes': recortes})
            if numero == 1:
                campos_encabezado += len(recortes)
            else:
                campos_datos += len(recortes)
        resultado.append(b'|'.join(campos) + terminador)
    salida = b'\n'.join(resultado) + (b'\n' if salto_final else b'')
    registro = {
        'sha256_entrada': hashlib.sha256(entrada).hexdigest(),
        'sha256_salida': hashlib.sha256(salida).hexdigest(),
        'filas_datos': len(lineas) - 1,
        'campos_datos_modificados': campos_datos,
        'encabezados_modificados': campos_encabezado,
        'espacios_ascii_retirados': espacios,
        'regla': 'Solo byte 20 al inicio y final. Sin cambiar espacios internos ni otros bytes.',
        'formato_recortes': '[columna_1_based, espacios_izquierda, espacios_derecha]',
        'reconstruccion': 'Anteponer y agregar esas cantidades de bytes 20 al campo de salida.',
        'cambios': cambios,
    }
    with destino.open('xb') as archivo:
        archivo.write(salida)
    with auditoria.open('x', encoding='utf-8') as archivo:
        json.dump(registro, archivo, ensure_ascii=True, separators=(',', ':'))
    return registro
