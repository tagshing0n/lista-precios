from pathlib import Path
import unittest,uuid,shutil,hashlib
from zipfile import ZipFile
from openpyxl import Workbook,load_workbook
from presentacion_comercial import COLUMNAS,generar_comercial,disponibilidad

class ComercialTests(unittest.TestCase):
    def setUp(self):
        self.work=Path(__file__).resolve().parents[1]/'work'
        self.root=self.work/('test_comercial_'+uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        self.addCleanup(self.limpiar)
        self.source=self.root/'origen.xlsx';self.dest=self.root/'comercial.xlsx'

    def limpiar(self):
        assert self.root.resolve().is_relative_to(self.work.resolve())
        assert self.root.name.startswith('test_comercial_')
        shutil.rmtree(self.root)

    def fuente(self,valor=0):
        wb=Workbook();ws=wb.active;ws.title='Lista de precios'
        ws.append(['Almacen',*COLUMNAS,'Codigo Fabricante'])
        for i,cantidad in enumerate((valor,4,-1,0.5)):
            ws.append(['SECRETO-ALMACEN','LINEA','000'+str(i),12.35,'MARCA',
                       '=TEXTO','DESC 3','DETALLE','PZ','00123456',cantidad,'SECRETO-FABRICANTE'])
            ws.cell(i+2,6).data_type='s'
        wb.create_sheet('Incidencias')['A1']='SECRETO-OBSERVACION'
        wb.save(self.source)

    def test_disponibilidad_y_errores_no_se_confunden_con_agotados(self):
        for valor in (0,'0.000','-0.0'):self.assertEqual(disponibilidad(valor),'')
        for valor in (-2,0.5,'1,000.00'):self.assertEqual(disponibilidad(valor),'D')
        for valor in (None,True,'','NaN','1,23','=1+1'):
            with self.assertRaises(ValueError):disponibilidad(valor)

    def test_solo_columnas_autorizadas_y_cantidades_no_exportadas(self):
        self.fuente()
        original=hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.assertEqual(generar_comercial(self.source,self.dest),{'articulos':4,'disponibles':3,'agotados':1})
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),original)
        wb=load_workbook(self.dest);self.addCleanup(wb.close)
        self.assertEqual(wb.sheetnames,['Lista comercial'])
        ws=wb.active
        self.assertEqual(tuple(c.value for c in ws[5]),COLUMNAS)
        self.assertEqual([ws.cell(i,10).value for i in range(6,10)],[None,'D','D','D'])
        self.assertEqual(ws['B6'].value,'0000')
        self.assertEqual(ws['I6'].value,'00123456')
        self.assertEqual(ws['E6'].value,'=TEXTO')
        self.assertEqual(ws['E6'].data_type,'s')
        self.assertEqual(ws['C6'].value,12.35)
        self.assertEqual(ws.tables['CatalogoComercial'].ref,'A5:J9')
        with ZipFile(self.dest) as z:
            self.assertFalse(any('externalLink' in n or 'comments' in n for n in z.namelist()))
            self.assertNotIn(b'SECRETO',b''.join(z.read(n) for n in z.namelist()))

    def test_no_sobrescribe_ni_genera_salida_con_existencia_invalida(self):
        self.fuente('DESCONOCIDO')
        with self.assertRaises(ValueError):generar_comercial(self.source,self.dest)
        self.assertFalse(self.dest.exists())
        self.dest.write_bytes(b'CONSERVAR')
        with self.assertRaises(ValueError):generar_comercial(self.source,self.dest)
        self.assertEqual(self.dest.read_bytes(),b'CONSERVAR')
