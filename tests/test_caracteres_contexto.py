import unittest
from caracteres_contexto import corregir_grados, tiene_pendientes

class ContextoTests(unittest.TestCase):
    def test_grados_con_contexto_y_numeros_intactos(self):
        original='CODO90ø JIC 37º ANGULO 36ø ASIENTO 30ø TERMOST 89ø -40øF 82§C 92¦C'
        esperado='CODO90° JIC 37° ANGULO 36° ASIENTO 30° TERMOST 89° -40°F 82°C 92°C'
        self.assertEqual(corregir_grados(original.encode('cp1252')),(esperado.encode('cp1252'),8))
        self.assertEqual(corregir_grados(esperado.encode('cp1252')),(esperado.encode('cp1252'),0))

    def test_ambiguos_diametro_ordinal_y_espacios_intactos(self):
        original='REPøFNO TRKµD21 180Ý Ø308mm 1º MODELO 93-02ø CIGšE A\u00a0B'
        self.assertEqual(corregir_grados(original.encode('cp1252')),(original.encode('cp1252'),0))
        self.assertTrue(tiene_pendientes(original.encode('cp1252'),'Descripcion 1'))

    def test_validos_y_campo_mixto(self):
        for text in ('CONEXIÓN CIGÜEÑAL ESTÁNDAR DIÉSEL', 'Ø308mmBALATA', 'CODO90° 87°C'):
            self.assertFalse(tiene_pendientes(text.encode('cp1252'),'Descripcion 1'))
            self.assertTrue(tiene_pendientes((text+' REPøFNO').encode('cp1252'),'Descripcion 1'))
        self.assertTrue(tiene_pendientes('CONEXIÓN'.encode('cp1252'),'Codigo de Articulo'))
        self.assertTrue(tiene_pendientes(b'CONEXI\xd3N\x00','Descripcion 1'))
