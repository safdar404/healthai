import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from healthassist.workspace import new_patient, add_vital, trends, agent_context, snapshot, validate_import, report_html, demos
from healthassist.agent import run_agent
from test_app import Msg, tool, fake_client


def test_vital_trends_chronological_and_validation():
    p=new_patient('Alias',40,'Male')
    add_vital(p,'2026-10-26T10:00:00+00:00',systolic=125,diastolic=80)
    add_vital(p,'2026-10-25T10:00:00+00:00',systolic=130,diastolic=82)
    assert trends(p)['values']['systolic']['difference']==-5
    with pytest.raises(ValueError):add_vital(p,systolic=60,diastolic=80)
    with pytest.raises(ValueError):add_vital(p,spo2=float('nan'))
    with pytest.raises(ValueError):add_vital(p)


def test_context_minimizes_fields_and_caps_history():
    p=new_patient('PRIVATE ALIAS',40,'Male','Punjab','Lahore',concern='reported concern')
    for _ in range(35):add_vital(p,heart_rate=75)
    ctx=agent_context(p)
    assert 'alias' not in ctx and 'id' not in ctx and 'district' not in ctx
    assert len(ctx['vitals'])==30


def test_backup_roundtrip_and_invalid_import():
    records=demos();restored=validate_import(snapshot(records,[],[]).encode())
    assert len(restored)==2 and len(restored[0]['vitals'])==3
    obj=json.loads(snapshot(records,[],[]));obj['patients'].append(obj['patients'][0])
    with pytest.raises(ValueError):validate_import(json.dumps(obj).encode())
    with pytest.raises(ValueError):validate_import(b'{}')


def test_printable_report_escapes_user_html():
    p=new_patient('<script>evil</script>',20,'Other',concern='<img onerror=x>')
    page=report_html(p)
    assert '<script>evil' not in page
    assert '&lt;script&gt;' in page


def test_agent_context_tool_consent_boundary():
    c=fake_client([Msg([tool('get_selected_patient_context',{})]),Msg(text='Please include encounter context.')])
    result=run_agent(c,'test',[],'Doctor','English',[],workspace_context=None)
    assert 'error' in result['trace'][0]['result']
    p=new_patient('Alias',50,'Female',concern='preparing visit')
    c=fake_client([Msg([tool('get_selected_patient_context',{})]),Msg(text='Discuss with a clinician.')])
    result=run_agent(c,'test',[],'Doctor','English',[],workspace_context=agent_context(p))
    assert result['trace'][0]['result']['encounter']['age']==50


def test_patient_workspace_page_flows():
    from streamlit.testing.v1 import AppTest
    at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
    at.button[0].click().run() # Load fictional examples
    at.sidebar.selectbox[0].select_index(1).run()
    for page in ['Patient Registry','Clinical Workspace','Care Tasks','Reports & Backup','AI Care Agent']:
        at.sidebar.radio[0].set_value(page).run(timeout=30)
        assert not at.exception,page
    assert len(at.chat_input)==1
