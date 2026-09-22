import unittest
import test_lista_precios
import listaPrecios
from limpieza_espacios import limpiar_espacios, recortar_espacios


class RecorteTests(unittest.TestCase):
    def test_solo_bordes_ascii(self):
        self.assertEqual(recortar_espacios(b'  00  ABC  '), (b'00  ABC', 2, 2))
        for original in (b'\xa0ABC\xa0', b'\tABC\t', b'\x00ABC\x00', b'\xd3', b'.'):
            self.assertEqual(recortar_espacios(original), (original, 0, 0))

    def test_vacios_y_solo_espacios_reversibles(self):
        for original in (b'', b' ', b'     ', b' 001.00 '):
            limpio, izquierda, derecha = recortar_espacios(original)
            self.assertEqual(b' ' * izquierda + limpio + b' ' * derecha, original)
            self.assertEqual(recortar_espacios(limpio), (limpio, 0, 0))


class ArchivoTests(unittest.TestCase):
    setUp = test_lista_precios.EstructuraTests.setUp
    limpiar = test_lista_precios.EstructuraTests.limpiar

    def ejecutar(self):
        return limpiar_espacios(self.entrada, self.salida, listaPrecios.ENCABEZADOS)

    def test_conserva_filas_y_reconstruye_encabezado_y_datos(self):
        self.campos[6] = b'  000123 '
        self.campos[7] = b' 1,234.50 '
        self.campos[10] = b'    '
        self.campos[12] = b' A  B \xd3 '
        self.campos[15] = b' 00ABC\xa0 '
        cabecera = self.cabecera.removesuffix(b'\r\n') + b'   \r\n'
        original = cabecera + b'|'.join(self.campos)
        self.entrada.write_bytes(original)
        reporte = self.ejecutar()
        filas = self.salida.read_bytes().split(b'\n')
        self.assertEqual(len(filas), 2)
        for cambio in reporte['cambios']:
            i = cambio['linea'] - 1
            terminador = b'\r' if filas[i].endswith(b'\r') else b''
            campos = filas[i].removesuffix(terminador).split(b'|') if terminador else filas[i].split(b'|')
            for col, izq, der in cambio['recortes']:
                campos[col - 1] = b' ' * izq + campos[col - 1] + b' ' * der
            filas[i] = b'|'.join(campos) + terminador
        self.assertEqual(b'\n'.join(filas), original)
        self.assertEqual(self.entrada.read_bytes(), original)
        self.assertEqual(reporte['encabezados_modificados'], 1)
        self.assertEqual(reporte['filas_datos'], 1)

    def test_saltos_lf_y_crlf(self):
        for salto in (b'\n', b'\r\n'):
            original = self.cabecera.removesuffix(b'\r\n') + salto + b'|'.join(self.campos) + salto
            self.entrada.write_bytes(original)
            self.ejecutar()
            self.assertEqual(self.salida.read_bytes(), original)
            self.salida.unlink()
            self.salida.with_suffix('.auditoria.json').unlink()

    def test_estructura_invalida_no_produce_salida(self):
        self.entrada.write_bytes(self.cabecera + b'UN CAMPO')
        with self.assertRaisesRegex(ValueError, 'estructura incorrecta'):
            self.ejecutar()
        self.assertFalse(self.salida.exists())

    def test_no_sobrescribe_entrada_o_resultados(self):
        original = self.cabecera + b'|'.join(self.campos)
        self.entrada.write_bytes(original)
        with self.assertRaisesRegex(ValueError, 'entrada'):
            limpiar_espacios(self.entrada, self.entrada, listaPrecios.ENCABEZADOS)
        self.salida.write_bytes(b'CONSERVAR')
        with self.assertRaisesRegex(ValueError, 'ya existe'):
            self.ejecutar()
        self.assertEqual(self.salida.read_bytes(), b'CONSERVAR')
        self.assertEqual(self.entrada.read_bytes(), original)
