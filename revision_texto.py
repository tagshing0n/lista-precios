"""Diagnostico conservador de texto: cuenta y muestra; nunca limpia datos."""
import hashlib


def revisar_texto(ruta, encabezados, columnas):
    categorias = (
        'vacios', 'espacios_externos', 'espacios_internos_multiples',
        'solo_digitos', 'ceros_iniciales', 'solo_punto',
        'controles_ascii', 'bytes_no_ascii',
    )
    resumen = {c: dict.fromkeys(categorias, 0) for c in columnas}
    muestras = {c: {k: [] for k in categorias} for c in columnas}
    posiciones = {c: encabezados.index(c) for c in columnas}
    indice_codigo = encabezados.index('Codigo de Articulo')
    incidencias = []
    filas = 0
    huella = hashlib.sha256()
    with ruta.open('rb') as archivo:
        cabecera = archivo.readline()
        huella.update(cabecera)
        if [c.strip(b' ') for c in cabecera.rstrip(b'\r\n').split(b'|')] != [
            c.encode('ascii') for c in encabezados
        ]:
            raise ValueError('Encabezados incompatibles con la revision de texto.')
        for linea, original in enumerate(archivo, 2):
            huella.update(original)
            campos = original.rstrip(b'\r\n').split(b'|')
            if len(campos) != len(encabezados):
                raise ValueError(f'Linea {linea}: estructura incorrecta; primero revisar los campos.')
            filas += 1
            for columna, posicion in posiciones.items():
                valor = campos[posicion]
                vista = valor.strip(b' ')
                controles = sorted({b for b in valor if b < 32 or b == 127})
                no_ascii = sorted({b for b in valor if b >= 128})
                marcas = {
                    'vacios': not vista,
                    'espacios_externos': valor != vista,
                    'espacios_internos_multiples': b'  ' in vista,
                    'solo_digitos': vista.isdigit(),
                    'ceros_iniciales': vista.isdigit() and len(vista) > 1 and vista.startswith(b'0'),
                    'solo_punto': vista == b'.',
                    'controles_ascii': bool(controles),
                    'bytes_no_ascii': bool(no_ascii),
                }
                for categoria, presente in marcas.items():
                    resumen[columna][categoria] += presente
                    if presente and len(muestras[columna][categoria]) < 5:
                        muestras[columna][categoria].append(linea)
                if controles or no_ascii:
                    incidencias.append({
                        'linea': linea, 'columna': columna,
                        'codigo_articulo_bytes_hex': campos[indice_codigo].hex(),
                        'valor_original_bytes_hex': valor.hex(),
                        'vista_latin1': valor.decode('latin1'),
                        'vista_cp1252': valor.decode('cp1252', errors='backslashreplace'),
                        'vista_cp850': valor.decode('cp850'),
                        'controles_hex': [f'{b:02x}' for b in controles],
                        'no_ascii_hex': [f'{b:02x}' for b in no_ascii],
                    })
    return {
        'sha256_entrada': huella.hexdigest(), 'filas': filas,
        'alcance': 'Observaciones de texto; no clasifica vacios, numeros o simbolos como errores.',
        'codificacion': 'Sin confirmar. Las vistas son comparaciones, no conversiones aprobadas.',
        'muestras': muestras, 'limite_muestras_por_categoria': 5,
        'detalle_incidencias': 'Incluye TODOS los campos con controles ASCII o bytes no ASCII.',
        'resumen': resumen, 'incidencias': incidencias,
    }
