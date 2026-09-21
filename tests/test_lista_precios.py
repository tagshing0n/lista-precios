import contextlib
import hashlib
import io
import json
from pathlib import Path
import uuid
import unittest
from unittest.mock import patch

import listaPrecios as programa


class EstructuraTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(__file__).resolve().parents[1] / 'work' / uuid.uuid4().hex
        self.tmp.mkdir(parents=True)
        self.addCleanup(self.limpiar)
        self.entrada = self.tmp / 'entrada.txt'
        self.salida = self.tmp / 'salida.txt'
        self.cabecera = '|'.join(programa.ENCABEZADOS).encode('ascii') + b'\r\n'
        self.campos = [
            b'1', b'2', b'LINEA DEMO', b'201', b'SUBLINEA DEMO',
            b'3.000', b'000123', b'10.50', b'MARCA DEMO',
            b'ARTICULO FICTICIO', b'', b'', b'.', b'PZ',
            b'00123456', b'00ABC',
        ]

    def limpiar(self):
        for nombre in ('entrada.txt', 'salida.txt', 'salida.auditoria.json'):
            (self.tmp / nombre).unlink(missing_ok=True)
        self.tmp.rmdir()

    def corregir(self):
        with contextlib.redirect_stdout(io.StringIO()):
            programa.corregir_estructura(self.entrada, self.salida)

    def test_conserva_bytes_codigos_y_saltos(self):
        original = self.cabecera + b'|'.join(self.campos) + b'\r\n'
        self.entrada.write_bytes(original)
        self.corregir()
        self.assertEqual(self.salida.read_bytes(), original)
        self.assertEqual(self.entrada.read_bytes(), original)

    def test_anomalia_desconocida_no_genera_salida(self):
        self.entrada.write_bytes(self.cabecera + b'|'.join(self.campos + [b'']))
        with self.assertRaisesRegex(ValueError, 'sin correccion aprobada'):
            self.corregir()
        self.assertFalse(self.salida.exists())
        self.assertFalse(self.salida.with_suffix('.auditoria.json').exists())

    def test_correccion_aprobada_con_datos_ficticios(self):
        campos = self.campos[:10] + [b'   '] + self.campos[10:]
        fila = b'|'.join(campos)
        original = self.cabecera + fila
        self.entrada.write_bytes(original)
        firmas = {hashlib.sha256(fila).hexdigest(): 10}
        with patch.dict(programa.CORRECCIONES_APROBADAS, firmas, clear=True):
            self.corregir()
        self.assertEqual(self.salida.read_bytes(), self.cabecera + b'|'.join(self.campos))
        self.assertEqual(self.entrada.read_bytes(), original)
        auditoria = json.loads(self.salida.with_suffix('.auditoria.json').read_text())
        self.assertEqual(auditoria['correcciones'][0]['bytes_eliminados_hex'], '202020')

    def test_no_sobrescribe_salida_existente(self):
        self.entrada.write_bytes(self.cabecera + b'|'.join(self.campos))
        self.salida.write_bytes(b'CONSERVAR')
        with self.assertRaisesRegex(ValueError, 'ya existe'):
            self.corregir()
        self.assertEqual(self.salida.read_bytes(), b'CONSERVAR')


if __name__ == '__main__':
    unittest.main()
