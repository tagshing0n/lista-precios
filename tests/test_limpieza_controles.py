import json
import unittest
import test_lista_precios
import listaPrecios
from limpieza_controles import limpiar_controles, transformar_campo


class ReglasTests(unittest.TestCase):
    def test_tab_no_une_palabras_ni_comprime_espacios(self):
        self.assertEqual(transformar_campo(b'A\t B\t\tC\t')[0], b'A  B  C ')
        self.assertEqual(transformar_campo(b' \xd3.\t"')[0], b' \xd3. "')

    def test_solo_nulos(self):
        self.assertEqual(transformar_campo(b'\x00' * 36), (b'', 'campo_solo_nulos_a_vacio'))
        self.assertEqual(transformar_campo(b''), (b'', None))

    def test_nulos_mezclados_se_conservan(self):
        for original in (b'A\x00B', b' \x00 ', b'\xa0\x00'):
            self.assertEqual(transformar_campo(original), (original, None))

    def test_idempotencia(self):
        for original in (b'A\tB', b'\x00' * 36, b'A  B', b'0', b'.'):
            limpio, _ = transformar_campo(original)
            self.assertEqual(transformar_campo(limpio), (limpio, None))


class LimpiezaTests(unittest.TestCase):
    setUp = test_lista_precios.EstructuraTests.setUp
    limpiar = test_lista_precios.EstructuraTests.limpiar

    def ejecutar(self):
        return limpiar_controles(self.entrada, self.salida, listaPrecios.ENCABEZADOS)

    def test_solo_descripciones_y_auditoria_reversible(self):
        self.campos[6] = b'00\t123'
        self.campos[10] = b'\x00' * 36
        self.campos[12] = b' \xd3.\t ABC  '
        original = self.cabecera + b'|'.join(self.campos) + b'\r\n'
        self.entrada.write_bytes(original)
        registro = self.ejecutar()
        filas = self.salida.read_bytes().split(b'\r\n')
        despues = filas[1].split(b'|')
        self.assertEqual(despues[6], self.campos[6])
        self.assertEqual(despues[10], b'')
        self.assertEqual(despues[12], b' \xd3.  ABC  ')
        for cambio in registro['cambios']:
            indice = listaPrecios.ENCABEZADOS.index(cambio['columna'])
            self.assertEqual(despues[indice], bytes.fromhex(cambio['nuevo_hex']))
            despues[indice] = bytes.fromhex(cambio['original_hex'])
        self.assertEqual(self.cabecera + b'|'.join(despues) + b'\r\n', original)
        self.assertEqual(self.entrada.read_bytes(), original)
        self.assertEqual(registro['campos_modificados'], 2)
        self.assertEqual(registro['nulos_retirados'], 36)
        self.assertEqual(json.loads(self.salida.with_suffix('.auditoria.json').read_text()), registro)

    def test_sin_salto_final_y_nulos_pendientes(self):
        self.campos[10] = b'A\x00B'
        original = self.cabecera + b'|'.join(self.campos)
        self.entrada.write_bytes(original)
        reporte = self.ejecutar()
        self.assertEqual(self.salida.read_bytes(), original)
        self.assertEqual(len(reporte['pendientes']), 1)

    def test_estructura_invalida_no_escribe(self):
        self.entrada.write_bytes(self.cabecera + b'|'.join(self.campos + [b'']))
        with self.assertRaisesRegex(ValueError, 'estructura incorrecta'):
            self.ejecutar()
        self.assertFalse(self.salida.exists())
        self.assertFalse(self.salida.with_suffix('.auditoria.json').exists())

    def test_protege_entrada_y_salida(self):
        original = self.cabecera + b'|'.join(self.campos)
        self.entrada.write_bytes(original)
        with self.assertRaisesRegex(ValueError, 'entrada'):
            limpiar_controles(self.entrada, self.entrada, listaPrecios.ENCABEZADOS)
        self.salida.write_bytes(b'CONSERVAR')
        with self.assertRaisesRegex(ValueError, 'ya existe'):
            self.ejecutar()
        self.assertEqual(self.salida.read_bytes(), b'CONSERVAR')
        self.assertEqual(self.entrada.read_bytes(), original)
