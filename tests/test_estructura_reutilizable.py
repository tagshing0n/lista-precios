import json
import unittest
from unittest.mock import patch
import test_lista_precios
import listaPrecios
from estructura import elegir_correccion, firma_contexto


class EstructuraReutilizableTests(unittest.TestCase):
    setUp = test_lista_precios.EstructuraTests.setUp
    limpiar = test_lista_precios.EstructuraTests.limpiar
    corregir = test_lista_precios.EstructuraTests.corregir

    def test_vacios_consecutivos_sin_identificar_articulo(self):
        campos = self.campos[:11] + [b'    '] + self.campos[11:]
        posicion, regla = elegir_correccion(campos, {})
        self.assertEqual(posicion, 10)
        self.assertEqual(regla, 'distribucion_unica_segun_esquema')
        self.assertEqual([c.strip() for c in campos[:posicion] + campos[posicion+1:]],
                         [c.strip() for c in self.campos])

    def test_no_borra_marca_vacia_si_hay_otra_distribucion(self):
        campos = self.campos[:10] + [b''] + self.campos[10:]
        campos[8] = b''
        campos[11:14] = [b'SEGUNDA', b'TERCERA', b'EXTENDIDA']
        self.assertEqual(elegir_correccion(campos, {})[0], None)

    def test_aprobacion_sobrevive_precio_existencia_y_orden(self):
        campos = self.campos[:10] + [b''] + self.campos[10:]
        campos[11:14] = [b'SEGUNDA', b'TERCERA', b'']
        aprobadas = {firma_contexto(campos): 10}
        campos[5], campos[7] = b'1,234.000', b'9,876.50'
        self.entrada.write_bytes(self.cabecera + b'|'.join(self.campos) + b'\r\n' + b'|'.join(campos))
        with patch.dict(listaPrecios.CORRECCIONES_APROBADAS, aprobadas, clear=True):
            self.corregir()
        fila = self.salida.read_bytes().splitlines()[2].split(b'|')
        self.assertEqual(fila[5], b'1,234.000')
        self.assertEqual(fila[7], b'9,876.50')
        self.assertEqual(fila[10], b'SEGUNDA')
        reporte = json.loads(self.salida.with_suffix('.auditoria.json').read_text())
        self.assertEqual(reporte['correcciones'][0]['linea'], 3)

    def test_descripcion_cambiada_invalida_aprobacion_ambigua(self):
        campos = self.campos[:10] + [b''] + self.campos[10:]
        campos[11:14] = [b'SEGUNDA', b'TERCERA', b'']
        aprobadas = {firma_contexto(campos): 10}
        campos[11] = b'OTRA DESCRIPCION'
        self.assertEqual(elegir_correccion(campos, aprobadas)[0], None)

    def test_no_retira_campo_con_texto_o_nulos(self):
        campos = [b'X'] * 17
        self.assertEqual(elegir_correccion(campos, {})[0], None)
        campos = self.campos[:10] + [b'\x00'] + self.campos[10:]
        campos[11:14] = [b'A', b'B', b'C']
        self.assertEqual(elegir_correccion(campos, {})[0], None)

    def test_rechaza_anclas_desplazadas(self):
        campos = self.campos[:10] + [b''] + self.campos[10:]
        campos[15] = b'NO ES SAT'
        self.assertEqual(elegir_correccion(campos, {})[0], None)

    def test_rechazo_genera_detalle_sin_txt_parcial(self):
        campos = self.campos[:10] + [b''] + self.campos[10:]
        campos[11:14] = [b'SEGUNDA', b'TERCERA', b'']
        original = self.cabecera + b'|'.join(campos)
        self.entrada.write_bytes(original)
        with patch.dict(listaPrecios.CORRECCIONES_APROBADAS, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'sin correccion aprobada'):
                self.corregir()
        self.assertFalse(self.salida.exists())
        reporte = json.loads(self.salida.with_suffix('.incidencias.json').read_text())
        incidencia = reporte['incidencias'][0]
        self.assertEqual(incidencia['linea'], 2)
        self.assertEqual(bytes.fromhex(incidencia['fila_original_hex']), original.split(b'\r\n')[1])
        self.assertEqual(self.entrada.read_bytes(), original)
