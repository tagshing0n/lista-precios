import json
import unittest
import test_lista_precios
import listaPrecios
from correccion_caracteres import corregir_caracteres, transformar_palabras


class PalabrasTests(unittest.TestCase):
    def test_oem_en_contextos_claros_preserva_cp1252_y_ambiguos(self):
        original=b'DI\x90SEL DI\x90SEL DISCO \x9d308mm \x9d340.5 mm PI\xd1ON DI\xc9SEL'
        esperado=b'DI\xc9SEL DI\xc9SEL DISCO \xd8308mm \xd8340.5 mm PI\xd1ON DI\xc9SEL'
        nuevo,cambios=transformar_palabras(original)
        self.assertEqual(nuevo,esperado)
        self.assertEqual(cambios,{'diesel_oem':2,'diametro_oem_mm':2})
        self.assertEqual(transformar_palabras(nuevo),(nuevo,{}))
        for valor in (b'\x9d',b'ABC\x9d308mm',b'\x9d308',b'\x9d308mmX',b'XDI\x90SEL',b'DI\x90SEL_1',b'\x90'):
            self.assertEqual(transformar_palabras(valor),(valor,{}))

    def test_nuevas_palabras_y_abreviaturas_pendientes(self):
        origen = 'CIGUE¥AL CIGšE¥AL TEFLàN CAMIàN A¥OS BRASILE¥O DISE¥O MU¥ON ANTIEMPA¥ANTE U¥A ARA¥A MALIBé'.encode('cp1252')
        esperado = 'CIGÜEÑAL CIGÜEÑAL TEFLÓN CAMIÓN AÑOS BRASILEÑO DISEÑO MUÑÓN ANTIEMPAÑANTE UÑA ARAÑA MALIBÚ'.encode('cp1252')
        nuevo, cambios = transformar_palabras(origen)
        self.assertEqual(nuevo, esperado)
        self.assertEqual(sum(cambios.values()), 12)
        self.assertEqual(transformar_palabras(nuevo), (nuevo, {}))
        pendiente = 'CIGšE CIGUEÑAL CIG_EÑAL Diésel REPøFNO'.encode('cp1252')
        self.assertEqual(transformar_palabras(pendiente), (pendiente, {}))

    def test_nuevas_reglas_no_modifican_palabras_mas_largas(self):
        for palabra in ('CIGUE¥AL', 'CIGšE¥AL', 'TEFLàN', 'CAMIàN', 'A¥OS',
                        'BRASILE¥O', 'DISE¥O', 'MU¥ON', 'ANTIEMPA¥ANTE', 'U¥A', 'ARA¥A', 'MALIBé'):
            for texto in ('X'+palabra, palabra+'ES', palabra+'_1', 'Ñ'+palabra):
                raw = texto.encode('cp1252')
                self.assertEqual(transformar_palabras(raw), (raw, {}))

    def test_cuatro_sustituciones_y_plural_sin_acento(self):
        origen = b'PI\xa5ON CONEXI\xe0N CONEXI\xe0NES TUBER\xd6A'
        nuevo, cambios = transformar_palabras(origen)
        self.assertEqual(nuevo, b'PI\xd1ON CONEXI\xd3N CONEXIONES TUBER\xcdA')
        self.assertEqual(cambios, dict(pinon=1, conexion=1, conexiones=1, tuberia=1))

    def test_no_reemplaza_fragmentos_de_palabras_o_codigos(self):
        for origen in (b'XPI\xa5ON', b'PI\xa5ONES', b'1PI\xa5ON', b'PI\xa5ON_2',
                       b'\xd1PI\xa5ON', b'PI\xa5ON\xe1', b'CONEXI\xe0NAL'):
            self.assertEqual(transformar_palabras(origen), (origen, {}))

    def test_preserva_espacios_simbolos_y_cuenta_repeticiones(self):
        origen = b' "PI\xa5ON"  (PI\xa5ON), \xa5 \xe0 \xd6 \xb0 \xd8\t.'
        nuevo, cambios = transformar_palabras(origen)
        self.assertEqual(nuevo, b' "PI\xd1ON"  (PI\xd1ON), \xa5 \xe0 \xd6 \xb0 \xd8\t.')
        self.assertEqual(cambios, {'pinon': 2})
        self.assertEqual(transformar_palabras(nuevo), (nuevo, {}))


class ArchivoTests(unittest.TestCase):
    setUp = test_lista_precios.EstructuraTests.setUp
    limpiar = test_lista_precios.EstructuraTests.limpiar

    def ejecutar(self):
        return corregir_caracteres(self.entrada, self.salida, listaPrecios.ENCABEZADOS)

    def test_solo_descripciones_y_auditoria_reversible(self):
        self.campos[6] = b'PI\xa5ON'
        self.campos[8] = b'PI\xa5ON'
        self.campos[15] = b'TUBER\xd6A'
        for i in (9, 10, 11, 12):
            self.campos[i] = b'PI\xa5ON CONEXI\xe0NES'
        original = self.cabecera + b'|'.join(self.campos) + b'\r\n'
        self.entrada.write_bytes(original)
        reporte = self.ejecutar()
        filas = self.salida.read_bytes().split(b'\r\n')
        campos = filas[1].split(b'|')
        for i in (6, 8, 15):
            self.assertEqual(campos[i], self.campos[i])
        self.assertEqual(reporte['campos_modificados'], 4)
        for cambio in reporte['cambios']:
            i = listaPrecios.ENCABEZADOS.index(cambio['columna'])
            self.assertEqual(campos[i], bytes.fromhex(cambio['nuevo_hex']))
            campos[i] = bytes.fromhex(cambio['original_hex'])
        self.assertEqual(self.cabecera + b'|'.join(campos) + b'\r\n', original)
        self.assertEqual(self.entrada.read_bytes(), original)
        self.assertEqual(json.loads(self.salida.with_suffix('.auditoria.json').read_text()), reporte)

    def test_archivo_sin_cambios_sin_salto_final(self):
        original = self.cabecera + b'|'.join(self.campos)
        self.entrada.write_bytes(original)
        reporte = self.ejecutar()
        self.assertEqual(self.salida.read_bytes(), original)
        self.assertEqual(reporte['campos_modificados'], 0)

    def test_estructura_invalida_no_genera_salida(self):
        self.entrada.write_bytes(self.cabecera + b'|'.join(self.campos + [b'']))
        with self.assertRaisesRegex(ValueError, 'estructura incorrecta'):
            self.ejecutar()
        self.assertFalse(self.salida.exists())
        self.assertFalse(self.salida.with_suffix('.auditoria.json').exists())

    def test_no_sobrescribe_entrada_o_resultados(self):
        original = self.cabecera + b'|'.join(self.campos)
        self.entrada.write_bytes(original)
        with self.assertRaisesRegex(ValueError, 'entrada'):
            corregir_caracteres(self.entrada, self.entrada, listaPrecios.ENCABEZADOS)
        self.salida.write_bytes(b'CONSERVAR')
        with self.assertRaisesRegex(ValueError, 'ya existe'):
            self.ejecutar()
        self.assertEqual(self.salida.read_bytes(), b'CONSERVAR')
        self.assertEqual(self.entrada.read_bytes(), original)
