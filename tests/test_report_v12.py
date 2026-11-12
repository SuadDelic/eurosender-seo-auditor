import io,sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_engine import audit_sample
from report_xlsx import make_report
from ai_engine import improve_with_ai

class ExcelTests(unittest.TestCase):
 def test_xlsx_format_and_sheets(self):
  content=make_report(audit_sample(),'sl')
  archive=zipfile.ZipFile(io.BytesIO(content))
  self.assertIn('xl/workbook.xml',archive.namelist())
  book=archive.read('xl/workbook.xml').decode('utf-8')
  for name in ('Povzetek','Ugotovitve','SEO besedila'):
   self.assertIn(name,book)
 def test_english_sheets(self):
  book=zipfile.ZipFile(io.BytesIO(make_report(audit_sample(),'en'))).read('xl/workbook.xml').decode()
  self.assertIn('Overview',book)
  self.assertIn('Findings',book)
 def test_language_prompt(self):
  class FakeResp:text='{"summary":"Pregled strani", "suggested_title":"", "suggested_meta_description":"", "recommendations": []}'
  class Models:
   def generate_content(self,model,contents):
    self.text=contents
    assert 'in Slovenian' in contents
    return FakeResp()
  class Client:models=Models()
  result=improve_with_ai(audit_sample()[0],'',client=Client(),language='sl')
  self.assertEqual(result['summary'],'Pregled strani')

if __name__=='__main__':unittest.main()
