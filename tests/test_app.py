from pathlib import Path
import io
import json
from types import SimpleNamespace
import pytest
from healthassist.core import bmi, chunks, extract, retrieve, urgent_flag, handoff
from healthassist.agent import run_agent


def test_bmi_and_limits():
    assert bmi(70,170)['bmi']==24.2
    for args in [(float('nan'),170),(0,170),(70,0)]:
        with pytest.raises(ValueError): bmi(*args)


def test_extraction_and_retrieval():
    p=extract('care.txt',b'Bring a list of your medications and allergies to your appointment. Ask what follow-up is needed.')
    assert retrieve('medications allergies',p)[0]['source']=='care.txt'
    assert retrieve('volcano astronomy',p)==[]
    for name,data in [('bad.txt',b'%PDF-1.4binary'),('image.png',b'123'),('empty.txt',b'')]:
        with pytest.raises(ValueError): extract(name,data)
    from docx import Document
    d=Document();d.add_paragraph('Documented appointment questions for a clinician to review.');b=io.BytesIO();d.save(b)
    assert 'appointment' in extract('sample.docx',b.getvalue())[0]['text']


def test_pdf_page_citation():
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject, DictionaryObject
    w=PdfWriter();p=w.add_blank_page(600,800)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    p[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):w._add_object(font)})})
    stream=DecodedStreamObject();stream.set_data(b'BT /F1 12 Tf 50 700 Td (Bring medication details and appointment questions.) Tj ET')
    p[NameObject('/Contents')]=w._add_object(stream);b=io.BytesIO();w.write(b)
    out=extract('guide.pdf',b.getvalue());assert out[0]['page']==1
    assert 'medication' in out[0]['text']


def test_escalation_and_handoff():
    assert urgent_flag('severe chest pain and sweating')
    assert urgent_flag('سینے میں درد')
    assert not urgent_flag('help prepare my appointment questions')
    assert handoff(concern='cough')['type'].endswith('not sent')


class Msg:
    def __init__(self,calls=None,text=None):self.tool_calls=calls;self.content=text
    def model_dump(self,**kw):
        return {'role':'assistant','content':self.content,'tool_calls':[{'id':c.id,'type':'function','function':{'name':c.function.name,'arguments':c.function.arguments}} for c in self.tool_calls]}


def fake_client(responses):
    class Completions:
        def __init__(self):self.calls=[]
        def create(self,**kw):
            self.calls.append(kw)
            return SimpleNamespace(choices=[SimpleNamespace(message=responses.pop(0))])
    return SimpleNamespace(chat=SimpleNamespace(completions=Completions()))


def tool(name,args,ident='t1'):
    return SimpleNamespace(id=ident,function=SimpleNamespace(name=name,arguments=json.dumps(args)))


def test_real_tool_loop_with_fake_provider():
    c=fake_client([Msg([tool('calculate_bmi',{'weight_kg':70,'height_cm':170})]),Msg(text='BMI is 24.2. Arithmetic only.')])
    r=run_agent(c,'test',[{'role':'user','content':'BMI 70kg 170cm'}],'Patient','English',[])
    assert r['trace'][0]['result']['bmi']==24.2
    assert c.chat.completions.calls[1]['messages'][-1]['role']=='tool'


def test_unknown_tool_blocked_and_evidence_returned():
    c=fake_client([Msg([tool('send_email',{}),tool('search_documents',{'query':'allergies'},'t2')]),Msg(text='See [S1].')])
    r=run_agent(c,'test',[],'Doctor','English',chunks('Record reported allergies for discussion.','guide'))
    assert 'error' in r['trace'][0]['result']
    assert r['sources'][0]['citation']=='S1'


def test_streamlit_startup():
    from streamlit.testing.v1 import AppTest
    at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
    assert not at.exception
    assert len(at.metric)==4
    for page in ['Patient Intake','Patient Registry','Clinical Workspace','AI Care Agent','Care Tasks','Facilities & GIS','Calculators','References & Models','Reports & Backup','Settings','Overview']:
        at.sidebar.radio[0].set_value(page).run(timeout=30)
        assert not at.exception, page


def test_password_gate(monkeypatch):
    monkeypatch.setenv('APP_ACCESS_PASSWORD','test-only-pass')
    from streamlit.testing.v1 import AppTest
    at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
    assert not at.exception
    assert len(at.metric)==0
    at.text_input[0].set_value('test-only-pass')
    at.button[0].click().run()
    assert len(at.metric)==4
