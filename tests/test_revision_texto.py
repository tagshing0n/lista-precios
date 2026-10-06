import unittest
import test_lista_precios
import listaPrecios
from revision_texto import revisar_texto


class TextoTests(unittest.TestCase):
    setUp = test_lista_precios.EstructuraTests.setUp
    limpiar = test_lista_precios.EstructuraTests.limpiar

    def revisar(self):
        self.original = self.cabecera + b'|'.join(self.campos)
        self.entrada.write_bytes(self.original)
        reporte = revisar_texto(self.entrada, listaPrecios.ENCABEZADOS, listaPrecios.COLUMNAS_TEXTO)
        self.assertEqual(self.entrada.read_bytes(), self.original)
        return reporte

    def test_codigos_numericos_y_vacios_son_observaciones(self):
        reporte = self.revisar()
        self.assertEqual(reporte['resumen']['Codigo de Articulo']['solo_digitos'], 1)
        self.assertEqual(reporte['resumen']['Codigo de Articulo']['ceros_iniciales'], 1)
        self.assertEqual(reporte['resumen']['Descripcion 2']['vacios'], 1)
        self.assertEqual(reporte['resumen']['Descripcion Extendida']['solo_punto'], 1)
        self.assertFalse(reporte['incidencias'])

    def test_no_borra_espacios_internos(self):
        self.campos[15] = b' 00  ABC '
        reporte = self.revisar()
        self.assertEqual(reporte['resumen']['Codigo Fabricante']['espacios_externos'], 1)
        self.assertEqual(reporte['resumen']['Codigo Fabricante']['espacios_internos_multiples'], 1)

    def test_acentos_y_codificacion_ambigua_se_preservan(self):
        self.campos[9] = b'CONEXI\xd3N PI\xa5ON'
        reporte = self.revisar()
        incidencia = reporte['incidencias'][0]
        self.assertEqual(bytes.fromhex(incidencia['valor_original_bytes_hex']), self.campos[9])
        self.assertNotEqual(incidencia['vista_cp1252'], incidencia['vista_cp850'])
        self.assertEqual(incidencia['controles_hex'], [])

    def test_controles_y_no_ascii_no_se_confunden_con_vacios(self):
        self.campos[10] = b'\t\x00\x7f\x81\xa0'
        reporte = self.revisar()
        self.assertEqual(reporte['filas'], 1)
        self.assertEqual(reporte['resumen']['Descripcion 2']['vacios'], 0)
        self.assertEqual(reporte['incidencias'][0]['controles_hex'], ['00', '09', '7f'])
        self.assertEqual(reporte['incidencias'][0]['no_ascii_hex'], ['81', 'a0'])

    def test_rechaza_campos_desalineados(self):
        self.campos.append(b'')
        with self.assertRaisesRegex(ValueError, 'Linea 2'):
            self.revisar()

    def test_rechaza_encabezados_incorrectos(self):
        self.cabecera = b'Nombre|Otro\n'
        with self.assertRaisesRegex(ValueError, 'Encabezados'):
            self.revisar()
