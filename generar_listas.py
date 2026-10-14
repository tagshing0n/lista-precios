"""Genera los tres libros en una carpeta nueva por ejecucion."""
from pathlib import Path
from datetime import datetime
import argparse
import json
import traceback
from almacenes import ALMACENES, obtener_presentacion, seleccionar_almacen


def ejecutar(base, ahora=None, almacen='adelar'):
    presentacion = obtener_presentacion(almacen)
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
    sufijo = presentacion.nombre.replace(' ', '_') + '_' + ahora.strftime('%Y-%m-%d')
    carpeta = base / 'outputs' / ahora.strftime('%Y%m%d_%H%M%S_%f')
    carpeta.mkdir(parents=True, exist_ok=False)
    estado = {'estado': 'en_proceso', 'almacen': almacen,
              'nombre_almacen': presentacion.nombre}
    try:
        completo = carpeta / f'Lista_Precios_{sufijo}.xlsx'
        reducido = carpeta / f'Lista_Precios_reducida_{sufijo}.xlsx'
        final = carpeta / f'Lista_Precios_Final_{sufijo}.xlsx'
        estado['archivos'] = {'completo': completo.name, 'reducido': reducido.name,
                              'comercial': final.name}
        print('Limpiando TXT y generando completo y reducido...', flush=True)
        resumen = generar_excel(fuente, completo, listaPrecios.ENCABEZADOS,
                                listaPrecios.COLUMNAS_NUMERICAS, listaPrecios.COLUMNAS_TEXTO,
                                listaPrecios.corregir_estructura, destino_reducido=reducido)
        print('Generando lista comercial con logo...', flush=True)
        comercial = generar_comercial(reducido, final, logo,
                                      'Edicion | ' + ahora.strftime('%d/%m/%Y'),
                                      almacen=almacen)
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
    parser.add_argument('--almacen', choices=ALMACENES,
                        help='Omite el menu y utiliza el almacen indicado.')
    args = parser.parse_args()
    try:
        almacen = args.almacen or seleccionar_almacen()
        if almacen is None:
            print('Generacion cancelada.')
            return 0
        print(f'Almacen: {ALMACENES[almacen].nombre}', flush=True)
        ejecutar(args.carpeta, almacen=almacen)
    except (EOFError, KeyboardInterrupt):
        print('\nGeneracion cancelada.')
        return 1
    except Exception as error:
        print(f'No se completaron las listas: {error}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
