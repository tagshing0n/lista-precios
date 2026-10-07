"""Genera los tres libros en una carpeta nueva por ejecucion."""
from pathlib import Path
from datetime import datetime
import argparse
import json
import traceback


def ejecutar(base, ahora=None):
    base = Path(base).resolve()
    datos = base / 'datos'
    fuente = datos / 'Lista-Precios.txt'
    logo = datos / 'logo_empresa.jpeg'
    faltantes = [str(p) for p in (fuente, logo) if not p.is_file()]
    if faltantes:
        raise ValueError('Faltan archivos:\n' + '\n'.join(faltantes))
    from PIL import Image
    with Image.open(logo) as imagen:
        imagen.verify()
    import listaPrecios
    from proceso_completo import generar_excel
    from presentacion_comercial import generar_comercial
    ahora = ahora or datetime.now()
    carpeta = base / 'outputs' / ahora.strftime('%Y%m%d_%H%M%S_%f')
    carpeta.mkdir(parents=True, exist_ok=False)
    estado = {'estado': 'en_proceso'}
    try:
        completo = carpeta / 'Lista_Precios.xlsx'
        print('Limpiando TXT y generando completo y reducido...', flush=True)
        resumen = generar_excel(fuente, completo, listaPrecios.ENCABEZADOS,
                                listaPrecios.COLUMNAS_NUMERICAS, listaPrecios.COLUMNAS_TEXTO,
                                listaPrecios.corregir_estructura)
        print('Generando lista comercial con logo...', flush=True)
        comercial = generar_comercial(carpeta / 'Lista_Precios_reducida.xlsx',
                                      carpeta / 'Lista_Precios_Final.xlsx', logo,
                                      'Edicion | ' + ahora.strftime('%d/%m/%Y'))
        estado.update(estado='completado', completo=resumen['filas'],
                      reducido=resumen['filas_reducido'], comercial=comercial)
        print(f'Listas terminadas: {carpeta}', flush=True)
        return carpeta
    except Exception:
        estado['estado'] = 'fallido'
        (carpeta / 'error.log').write_text(traceback.format_exc(), encoding='utf-8')
        print(f'Proceso incompleto. Detalle en: {carpeta / "error.log"}', flush=True)
        raise
    finally:
        (carpeta / 'ejecucion.json').write_text(json.dumps(estado, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--carpeta', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    try:
        ejecutar(args.carpeta)
    except Exception as error:
        print(f'No se completaron las listas: {error}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
