"""Decisiones privadas por articulo; no aprueba automaticamente casos nuevos."""
import hashlib
import json


def identidad(fila):
    valores = [str(fila[i]).strip(' ') for i in (0,1,3,6)]
    return hashlib.sha256(json.dumps(valores,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()


def cargar_revisiones(ruta):
    archivo = ruta.with_suffix('.revisiones.json')
    if not archivo.exists():
        return {}, None
    contenido = json.loads(archivo.read_text(encoding='utf-8'))
    if contenido.get('version') != 1:
        raise ValueError('Version no reconocida del archivo de revisiones.')
    reglas = contenido.get('aceptaciones', {})
    if not isinstance(reglas, dict) or any(k not in {'precio_cero','nombre_linea_vacio'} or
            not isinstance(v,list) or any(not isinstance(x,str) or len(x)!=64 for x in v)
            for k,v in reglas.items()):
        raise ValueError('Archivo de revisiones invalido.')
    return {k:set(v) for k,v in reglas.items()}, archivo


def aceptada(tipo, fila, revisiones):
    return identidad(fila) in revisiones.get(tipo,set())
