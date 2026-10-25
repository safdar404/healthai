"""Session-scoped workspace models. No cross-user storage or clinical predictions."""
from datetime import datetime, timezone, timedelta
import copy
import html
import json
import math
import re
import uuid

FIELDS = ['concern','duration','history','medicines','allergies']
VITAL_FIELDS = {'systolic':(40,300),'diastolic':(20,200),'heart_rate':(15,250),'spo2':(30,100),
                'temperature':(30,44),'respiratory_rate':(1,80),'glucose':(10,1000)}

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def uid(prefix='P'): return prefix+'-'+uuid.uuid4().hex[:8].upper()

def new_patient(alias,age,sex,province='',district='',**reported):
    if not alias.strip() or len(alias)>80: raise ValueError('Use an alias of 1–80 characters.')
    if not 0<=int(age)<=120: raise ValueError('Age must be 0–120.')
    return {'id':uid(),'alias':alias.strip(),'age':int(age),'sex':sex,'province':province[:80],
            'district':district[:80],'created_at':now(),'updated_at':now(),
            **{k:str(reported.get(k,''))[:4000] for k in FIELDS},
            'vitals':[],'labs':[],'notes':[],'tasks':[],'consent_to_record':True}

def completeness(patient): return sum(bool(str(patient.get(k,'')).strip()) for k in FIELDS)

def add_vital(patient, recorded_at=None, **values):
    record={'timestamp':recorded_at or now()}
    datetime.fromisoformat(record['timestamp'])
    for name,value in values.items():
        if name not in VITAL_FIELDS: raise ValueError('Unknown vital field')
        if value is None: continue
        n=float(value); low,high=VITAL_FIELDS[name]
        if not math.isfinite(n) or not low<=n<=high: raise ValueError(f'{name} outside input range {low}–{high}. Check units.')
        record[name]=n
    if len(record)==1: raise ValueError('Provide at least one reading.')
    if 'systolic' in record and 'diastolic' in record and record['systolic']<=record['diastolic']:
        raise ValueError('Systolic must exceed diastolic; check entry.')
    patient['vitals'].append(record);patient['updated_at']=now();return record

def trends(patient):
    output={}
    for key in VITAL_FIELDS:
        vals=sorted([v for v in patient.get('vitals',[]) if key in v],key=lambda v:datetime.fromisoformat(v['timestamp']).timestamp())
        if vals:
            output[key]={'first':vals[0][key],'latest':vals[-1][key],'difference':round(vals[-1][key]-vals[0][key],2),'readings':len(vals)}
    return {'values':output,'note':'Numerical differences only. No improvement, deterioration, diagnosis or urgency is inferred.'}

def agent_context(patient):
    if not patient: return None
    context={k:copy.deepcopy(patient.get(k)) for k in ['age','sex',*FIELDS]}
    context.update(vitals=copy.deepcopy(patient.get('vitals',[])[-30:]),labs=copy.deepcopy(patient.get('labs',[])[-15:]),notes=copy.deepcopy(patient.get('notes',[])[-5:]))
    context['scope']='Last 30 readings, 15 lab entries and 5 notes; history is partial. Alias, ID, district, facility and coordinates excluded.'
    return context

def snapshot(patients,facilities,events):
    return json.dumps({'format':'healthassist-workspace-v2','exported_at':now(),'patients':patients,
                       'facilities':facilities,'events':events},ensure_ascii=False,indent=2)

def validate_import(data):
    if len(data)>5*1024*1024: raise ValueError('Backup limit: 5 MB.')
    obj=json.loads(data)
    if obj.get('format')!='healthassist-workspace-v2': raise ValueError('Not a HealthAssist v2 backup.')
    patients=obj.get('patients',[])
    if not isinstance(patients,list) or len(patients)>250: raise ValueError('Invalid patient list (max 250).')
    ids=set();clean=[]
    for p in patients:
        if not isinstance(p,dict) or not isinstance(p.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',p['id']) or p['id'] in ids: raise ValueError('Missing or duplicate patient ID.')
        ids.add(p['id']); r=new_patient(str(p.get('alias','')),p.get('age',-1),str(p.get('sex','')),str(p.get('province','')),str(p.get('district','')),**{k:p.get(k,'') for k in FIELDS})
        r['id']=p['id'][:80]
        for v in p.get('vitals',[])[:1000]: add_vital(r,recorded_at=v.get('timestamp'),**{k:v[k] for k in VITAL_FIELDS if k in v})
        # Whitelist imported fields; no executable data or arbitrary rendering.
        for category in ['labs','notes','tasks']:
            if not isinstance(p.get(category,[]),list): raise ValueError('Invalid '+category)
            r[category]=[{str(k)[:80]:str(v)[:6000] for k,v in row.items()} for row in p.get(category,[])[:500] if isinstance(row,dict)]
        clean.append(r)
    return clean

def report_html(patient):
    esc=lambda x:html.escape(str(x))
    content=f'<h1>HealthAssist · Encounter report</h1><p>Unreviewed workspace export • {esc(now())}</p><h2>{esc(patient["alias"])} · {esc(patient["id"])}</h2>'
    for k in ['age','sex','province','district',*FIELDS]: content+=f'<h3>{esc(k.replace("_"," ").title())}</h3><p>{esc(patient.get(k,"Not recorded"))}</p>'
    for k in ['vitals','labs','notes','tasks']:
        content+=f'<h2>{esc(k.title())}</h2><pre>{esc(json.dumps(patient.get(k,[]),ensure_ascii=False,indent=2))}</pre>'
    return '<!doctype html><html><meta charset="utf-8"><title>HealthAssist report</title><style>body{max-width:850px;margin:40px auto;font:15px/1.7 Arial;color:#23484e;padding:20px}h1,h2{color:#087f83}pre{white-space:pre-wrap;overflow-wrap:anywhere;border:1px solid #ddd;padding:18px}h3{margin-bottom:0}p{margin-top:4px}@media print{body{margin:0}pre{break-inside:avoid}}</style>'+content+'<hr><p>Educational workspace. Not a diagnosis, prescription, referral acceptance or verified clinical record. Review with a licensed professional.</p></html>'

def demos():
    p=new_patient('DEMO · River',42,'Female','Punjab','Lahore',concern='Questions about recent tiredness',duration='One week',history='Fictional training example',medicines='Not supplied',allergies='Not supplied')
    for i,bp in enumerate([128,126,130]): add_vital(p,(datetime.now(timezone.utc)-timedelta(days=2-i)).isoformat(),systolic=bp,diastolic=80,heart_rate=76+i,spo2=98,temperature=36.8)
    q=new_patient('DEMO · Cedar',57,'Male','Sindh','Karachi',concern='Preparing a follow-up visit',duration='Routine appointment',history='Fictional training example',medicines='Bring list to appointment',allergies='Unknown')
    return [p,q]
