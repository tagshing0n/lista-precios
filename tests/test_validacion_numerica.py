import unittest
from decimal import Decimal
import test_lista_precios
from validacion_numerica import clasificar, validar_numeros
import listaPrecios


class FormatosTests(unittest.TestCase):
    def test_miles_y_decimal_exacto(self):
        for valor, esperado in [(b' 1,918.000 ', '1918.000'), (b'4,653.10', '4653.10'), (b'0.10', '0.10')]:
            with self.subTest(valor=valor):
                estado, numero, _ = clasificar('Existencia', valor)
                self.assertEqual(estado, 'valido')
                self.assertEqual(numero, Decimal(esperado))

    def test_ambiguos_y_no_numeros(self):
        for valor in (b'1,23', b'1.234,50', b'12,34.50', b'1,,000', b'NaN', b'Infinity', b'1e3', b'1 000', b'\xa010'):
            with self.subTest(valor=valor):
                self.assertEqual(clasificar('Precio de Lista', valor)[0], 'invalido')

    def test_vacio_distinto_de_cero(self):
        self.assertEqual(clasificar('Existencia', b'  ')[0], 'vacio')
        self.assertEqual(clasificar('Existencia', b'0.000')[0], 'valido')

    def test_identificadores(self):
        for valor in (b'1.0', b'-1', b'1,000', b'ABC'):
            self.assertEqual(clasificar('Linea', valor)[0], 'invalido')
        self.assertEqual(clasificar('Codigo SAT', b'00123456'), ('valido', Decimal('123456'), []))

    def test_avisos_no_alteran_valor(self):
        estado, numero, avisos = clasificar('Precio de Lista', b'-1.234')
        self.assertEqual(estado, 'valido')
        self.assertEqual(numero, Decimal('-1.234'))
        self.assertEqual(len(avisos), 2)
        self.assertTrue(clasificar('Codigo SAT', b'123')[2])


class ArchivoTests(unittest.TestCase):
    setUp = test_lista_precios.EstructuraTests.setUp
    limpiar = test_lista_precios.EstructuraTests.limpiar

    def validar(self):
        return validar_numeros(self.entrada, listaPrecios.ENCABEZADOS, listaPrecios.COLUMNAS_NUMERICAS)

    def test_conservacion_y_ceros_sat(self):
        original = self.cabecera + b'|'.join(self.campos)
        self.entrada.write_bytes(original)
        reporte = self.validar()
        self.assertEqual(reporte['filas'], 1)
        self.assertEqual(reporte['resumen']['Codigo SAT']['ceros_iniciales'], 1)
        self.assertFalse(reporte['incidencias'])
        self.assertEqual(self.entrada.read_bytes(), original)

    def test_registra_valor_y_linea(self):
        self.campos[5] = b' 1,23 '
        self.campos[7] = b' '
        self.entrada.write_bytes(self.cabecera + b'|'.join(self.campos))
        reporte = self.validar()
        self.assertEqual(len(reporte['incidencias']), 2)
        self.assertEqual(reporte['incidencias'][0]['linea'], 2)
        self.assertEqual(reporte['incidencias'][0]['valor_original'], ' 1,23 ')
        self.assertEqual(reporte['resumen']['Precio de Lista']['vacios'], 1)

    def test_rechaza_estructura(self):
        self.entrada.write_bytes(self.cabecera + b'|'.join(self.campos + [b'']))
        with self.assertRaisesRegex(ValueError, 'Linea 2'):
            self.validar()
