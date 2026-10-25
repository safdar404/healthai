from datetime import datetime, timezone
from pathlib import Path
import json
import pandas as pd
import streamlit as st
from .core import bmi, urgent_flag, EMERGENCY_MESSAGE
from .workspace import FIELDS, VITAL_FIELDS, now, uid, new_patient, add_vital, completeness, trends, report_html, snapshot, validate_import, demos

PROVINCES=['Punjab','Sindh','Khyber Pakhtunkhwa','Balochistan','Islamabad','Gilgit-Baltistan','Azad Jammu & Kashmir','Other / not recorded']

def event(action,record=''):
    st.session_state.events.append({'timestamp':now(),'action':action,'record':record})

def current():
    return next((p for p in st.session_state.patients if p['id']==st.session_state.get('selected_patient')),None)

def require_patient():
    p=current()
    if not p: st.info('Add or select a patient alias in the sidebar or Patient Registry first.')
    return p

def dashboard(root):
    a,b=st.columns([1.5,1])
    with a:
        st.markdown('<div class="ha-hero"><div class="ha-kicker">HEALTH INTELLIGENCE · AGENTIC WORKSPACE</div><h1>One workspace.<br>A more connected conversation.</h1><p>Intake, longitudinal records, clinical notes, document evidence and a context-aware AI agent.</p></div>',unsafe_allow_html=True)
    with b: st.image(str(root/'assets/healthassist-clinician.webp'),caption='AI-generated illustration',use_container_width=True)
    patients=st.session_state.patients
    cols=st.columns(4)
    for c,label,value in zip(cols,['Workspace records','Recorded readings','Open care tasks','Agent replies'],[len(patients),sum(len(p['vitals']) for p in patients),sum(t.get('status')!='Done' for p in patients for t in p['tasks']),st.session_state.turns]): c.metric(label,value)
    st.subheader('Your connected care workspace')
    a,b,c=st.columns(3)
    with a:
        st.markdown('#### 📋 Structured intake');st.write('Demographics, symptoms, history, medicines, allergies and observations.')
    with b:
        st.markdown('#### 🧠 Context-aware agent');st.write('Tools can retrieve selected patient context, compare readings and draft notes—with your consent.')
    with c:
        st.markdown('#### 🗺️ Health geography');st.write('Map user-entered facilities and organize review tasks. No live hospital availability claims.')
    if patients:
        st.subheader('Recorded encounters')
        st.dataframe(pd.DataFrame([{'Alias':p['alias'],'ID':p['id'],'District':p['district'],'Readings':len(p['vitals']),'Notes':len(p['notes']),'Context fields':f'{completeness(p)}/5'} for p in patients]),hide_index=True,use_container_width=True)
    else: st.info('Start in Patient Intake or load fictional examples below.')
    if st.button('Load fictional training records',disabled=any(p['alias'].startswith('DEMO') for p in patients)):
        st.session_state.patients.extend(demos());event('Loaded fictional samples');st.rerun()
    st.caption('No autonomous diagnosis, prescribing, emergency dispatch, verified risk model or live clinician connection. This version provides actual record management and assisted drafting.')

def intake():
    st.subheader('Patient intake · structured encounter')
    st.caption('Use an alias, not a real name or identifier. Recording permission is separate from permission to send context to an AI provider.')
    with st.form('full_intake'):
        tabs=st.tabs(['1 · Demographics','2 · Symptoms','3 · History','4 · Medicines','5 · Confirmation'])
        with tabs[0]:
            a,b,c=st.columns(3);alias=a.text_input('Patient alias');age=b.number_input('Age (years)',0,120,35);sex=c.selectbox('Reported sex',['Not recorded','Female','Male','Other'])
            a,b=st.columns(2);province=a.selectbox('Province / region',PROVINCES);district=b.text_input('District')
        with tabs[1]:
            concern=st.text_area('Reported concerns / symptoms');duration=st.text_input('Onset and duration')
            st.caption('Urgency is not determined from this form. For possible emergencies, seek immediate human help.')
        with tabs[2]: history=st.text_area('Reported medical and family history / relevant context')
        with tabs[3]: medicines=st.text_area('Reported medicines (not a prescription)');allergies=st.text_area('Reported allergies and reactions')
        with tabs[4]: permission=st.checkbox('I have permission to record this de-identified information.');st.info('This app is not an approved EHR. Data remains in this server session unless exported. Back up what you need before the session ends.')
        submit=st.form_submit_button('Create encounter',type='primary')
    if submit:
        if urgent_flag(concern): st.error(EMERGENCY_MESSAGE)
        if not permission: st.error('Confirm permission before recording.')
        else:
            try:
                p=new_patient(alias,age,sex,province,district,concern=concern,duration=duration,history=history,medicines=medicines,allergies=allergies)
                st.session_state.patients.append(p);st.session_state.selected_patient=p['id'];event('Created encounter',p['id']);st.success('Encounter created. Open Clinical Workspace to add observations and notes.')
            except ValueError as e:st.error(str(e))

def registry():
    st.subheader('Patient registry')
    query=st.text_input('Search aliases, IDs, district or concern').casefold()
    patients=[p for p in st.session_state.patients if query in ' '.join(str(p.get(k,'')) for k in ['alias','id','district','concern']).casefold()]
    st.write(f'{len(patients)} matching records')
    for p in patients:
        with st.expander(f"{p['alias']} · {p['id']} · {p['district'] or 'No district'}"):
            st.write(p['concern'] or 'No concern recorded');st.caption(f"Context fields present: {completeness(p)}/5. This is not a clinical-quality score.")
            a,b=st.columns(2)
            if a.button('Select this encounter',key='select_'+p['id']): st.session_state.selected_patient=p['id'];event('Selected encounter',p['id']);st.rerun()
            b.download_button('Export record JSON',json.dumps(p,ensure_ascii=False,indent=2),f"{p['id']}.json",'application/json',key='dl_'+p['id'])
    p=current()
    if p:
        st.subheader('Edit selected encounter')
        with st.form('edit_record'):
            values={k:st.text_area(k.title(),value=p.get(k,''),key='edit_'+k) for k in FIELDS}
            alias=st.text_input('Alias',value=p['alias'])
            submit=st.form_submit_button('Save edits')
        if submit:
            if not alias.strip():st.error('Alias cannot be empty.')
            else:p.update(values,alias=alias[:80],updated_at=now());event('Edited encounter',p['id']);st.success('Saved.')
        confirm=st.checkbox('I intend to remove the selected record from this session.')
        if st.button('Remove selected record',disabled=not confirm):
            st.session_state.patients=[x for x in st.session_state.patients if x['id']!=p['id']];st.session_state.selected_patient=None;event('Removed encounter',p['id']);st.rerun()

def clinical():
    st.subheader('Clinical workspace · human review')
    p=require_patient()
    if not p:return
    st.markdown(f"### {p['alias']} · {p['id']}")
    if urgent_flag(p.get('concern','')):st.error(EMERGENCY_MESSAGE)
    st.write('Reported concern:',p['concern']);st.caption('All observations and notes are user entered. No machine-generated risk probability is supplied.')
    obs,labs,notes,overview=st.tabs(['Vital signs & trends','Laboratory context','Review notes','Encounter summary'])
    with obs:
        st.caption('Enter only measured readings. Unchecked values are not saved. Input limits are plausibility checks, not clinical normal ranges.')
        with st.form('add_vitals'):
            day=st.date_input('Measurement date');tm=st.time_input('Measurement time (UTC)')
            values={};cols=st.columns(3)
            labels={'systolic':'Systolic BP · mmHg','diastolic':'Diastolic BP · mmHg','heart_rate':'Pulse · bpm','spo2':'SpO₂ · %','temperature':'Temperature · °C','respiratory_rate':'Respiratory rate · /min','glucose':'Glucose · mg/dL'}
            defaults=[120.,80.,75.,98.,36.8,16.,100.]
            for i,(key,(low,high)) in enumerate(VITAL_FIELDS.items()):
                with cols[i%3]:
                    enabled=st.checkbox('Record '+labels[key],key='enabled_'+key)
                    value=st.number_input(labels[key],float(low),float(high),defaults[i],key='value_'+key)
                    if enabled:values[key]=value
            submitted=st.form_submit_button('Save measured readings')
        if submitted:
            try:add_vital(p,datetime.combine(day,tm,tzinfo=timezone.utc).isoformat(),**values);event('Recorded observations',p['id']);st.success('Readings saved.')
            except ValueError as e:st.error(str(e))
        if p['vitals']:
            frame=pd.DataFrame(p['vitals']).sort_values('timestamp');st.dataframe(frame,hide_index=True,use_container_width=True)
            choices=[k for k in VITAL_FIELDS if k in frame]
            chosen=st.multiselect('Plot measured values (check units before combining)',choices,default=choices[:1])
            if chosen:st.line_chart(frame.set_index('timestamp')[chosen])
            st.json(trends(p));st.download_button('Download observation CSV',frame.to_csv(index=False),f"{p['id']}-vitals.csv",'text/csv')
    with labs:
        with st.form('add_lab'):
            a,b,c=st.columns(3);name=a.text_input('Test name');value=b.text_input('Reported value');unit=c.text_input('Unit')
            reference=st.text_input('Laboratory-supplied reference interval (optional)');date=st.date_input('Lab date')
            if st.form_submit_button('Record lab result'):
                if not name.strip() or not value.strip():st.error('Test name and reported value are required.')
                else:p['labs'].append({'test':name[:200],'value':value[:200],'unit':unit[:80],'reference':reference[:200],'date':str(date)});event('Recorded lab context',p['id']);st.success('Recorded. No automatic interpretation applied.')
        st.dataframe(pd.DataFrame(p['labs']),use_container_width=True)
    with notes:
        st.caption('Editable SOAP structure. Notes are not signed prescriptions or verified clinician records. Use AI Agent to draft a note, then review and paste it here.')
        with st.form('review_note'):
            reviewer=st.text_input('Reviewer alias')
            subject=st.text_area('S · Reported history and concerns')
            objective=st.text_area('O · Measured observations / documented results')
            assessment=st.text_area('A · Clinician-entered assessment / uncertainties')
            plan=st.text_area('P · Clinician-entered follow-up / discussion plan')
            reviewed=st.checkbox('I have reviewed these notes for accuracy. This checkbox does not verify my identity.')
            if st.form_submit_button('Save review note'):
                if not subject.strip() and not objective.strip() and not assessment.strip() and not plan.strip():st.error('Write a note first.')
                else:p['notes'].append({'timestamp':now(),'reviewer':reviewer[:80],'subjective':subject,'objective':objective,'assessment':assessment,'plan':plan,'review_status':'User marked reviewed' if reviewed else 'Unreviewed draft'});event('Saved review note',p['id']);st.success('Note saved.')
        for note in reversed(p['notes']):
            with st.expander(note.get('timestamp','Note')+' · '+note.get('review_status','Unreviewed')):st.json(note)
    with overview:
        st.json({k:v for k,v in p.items() if k not in ['vitals','labs','notes','tasks']})
        st.download_button('Download printable encounter report',report_html(p),f"{p['id']}-report.html",'text/html')

def tasks():
    st.subheader('Care tasks & appointment preparation')
    p=require_patient()
    if not p:return
    st.info('Tasks are records in this session. They do not send reminders, book appointments or contact a clinician.')
    with st.form('task'):
        title=st.text_input('Task / appointment preparation');detail=st.text_area('Details');due=st.date_input('Planned date');assignee=st.selectbox('Responsible role',['Patient','Doctor','Caregiver','Other'])
        if st.form_submit_button('Add task'):
            if title.strip():p['tasks'].append({'id':uid('T'),'title':title[:200],'details':detail[:4000],'date':str(due),'assignee':assignee,'status':'Open'});event('Added care task',p['id']);st.success('Task recorded.')
            else:st.error('Enter a title.')
    for i,t in enumerate(p['tasks']):
        a,b=st.columns([3,1]);a.write(f"**{t['title']}** · {t['date']} · {t['assignee']}");a.caption(t.get('details',''))
        state=b.selectbox('Status',['Open','In progress','Done'],index=['Open','In progress','Done'].index(t.get('status','Open')) if t.get('status') in ['Open','In progress','Done'] else 0,key=f"taskstate_{p['id']}_{i}")
        if state!=t['status']:t['status']=state;event('Changed task status',p['id'])

def facilities():
    st.subheader('Facilities & health geography')
    st.caption('A user-maintained directory, not a verified doctor network. Check credentials, location and availability independently. No patient coordinates are mapped or sent to the agent.')
    with st.form('facility'):
        a,b=st.columns(2);name=a.text_input('Facility name');city=b.text_input('City / district')
        a,b=st.columns(2);lat=a.number_input('Facility latitude',-90.,90.,31.52);lon=b.number_input('Facility longitude',-180.,180.,74.35)
        specialty=st.text_input('Reported services / specialty');clinician=st.text_input('Clinician name or alias (optional, user supplied)');url=st.text_input('Official website (https://...)')
        checked=st.checkbox('I checked these details against an official source.')
        if st.form_submit_button('Add directory entry'):
            if not name.strip():st.error('Enter facility name.')
            elif url and not url.startswith('https://'):st.error('Use an HTTPS official URL.')
            else:st.session_state.facilities.append({'id':uid('F'),'name':name[:200],'city':city[:100],'latitude':lat,'longitude':lon,'services':specialty[:400],'clinician':clinician[:150],'website':url[:400],'verification':'User reported checked' if checked else 'Unverified','added_at':now()});event('Added facility');st.success('Entry recorded.')
    query=st.text_input('Filter directory by name, city or services').casefold()
    records=[f for f in st.session_state.facilities if query in ' '.join([f['name'],f['city'],f['services']]).casefold()]
    if records:
        st.dataframe(pd.DataFrame(records),hide_index=True,use_container_width=True)
        if st.checkbox('Load facility map (map tiles are fetched from an external map provider)',value=False):st.map(pd.DataFrame(records),latitude='latitude',longitude='longitude')
        st.download_button('Export directory CSV',pd.DataFrame(records).to_csv(index=False),'healthassist-facilities.csv','text/csv')
    else:st.info('No matching facilities. Add verified details to build your directory.')

def calculators():
    st.subheader('Clinical arithmetic · no diagnosis')
    tabs=st.tabs(['BMI','Blood-pressure arithmetic','Glucose units','Body temperature'])
    with tabs[0]:
        a,b=st.columns(2);w=a.number_input('Weight kg',1.,500.,70.);h=b.number_input('Height cm',30.,260.,170.)
        st.metric('BMI',bmi(w,h)['bmi']);st.caption('Arithmetic only. Age, pregnancy and other clinical factors change interpretation.')
    with tabs[1]:
        a,b=st.columns(2);s=a.number_input('SBP · mmHg',40.,300.,120.);d=b.number_input('DBP · mmHg',20.,200.,80.)
        if s>d:
            a,b=st.columns(2);a.metric('Pulse pressure · mmHg',round(s-d,1));b.metric('Estimated MAP · mmHg',round((s+2*d)/3,1))
            st.caption('MAP ≈ (SBP + 2 × DBP) / 3 is an approximation, not an urgency score or treatment target.')
        else:st.error('SBP must exceed DBP. Check the reading.')
    with tabs[2]:
        value=st.number_input('Glucose value',0.,1000.,100.);unit=st.radio('Input unit',['mg/dL','mmol/L'],horizontal=True)
        st.metric('Converted value',f'{value/18.0182:.2f} mmol/L' if unit=='mg/dL' else f'{value*18.0182:.1f} mg/dL')
    with tabs[3]:
        t=st.number_input('Temperature value',-100.,250.,37.);unit=st.radio('Temperature unit',['Celsius','Fahrenheit'],horizontal=True)
        st.metric('Converted temperature',f'{t*9/5+32:.1f} °F' if unit=='Celsius' else f'{(t-32)*5/9:.1f} °C')

def resources():
    st.subheader('Reference library & model transparency')
    st.write('These are external reference links, not an automatically updated guideline database. Uploaded documents are searched only when explicitly included in the agent session.')
    for title,url in [('NHS · Chest pain','https://www.nhs.uk/symptoms/chest-pain/'),('NHS · Stroke symptoms','https://www.nhs.uk/conditions/stroke/symptoms/'),('NHS · Blood pressure test','https://www.nhs.uk/tests-and-treatments/blood-pressure-test/'),('WHO · Governance of health AI','https://www.who.int/publications/i/item/9789240084759')]:st.link_button(title,url)
    st.markdown('#### Implemented methods')
    st.table(pd.DataFrame([['Chat model','Your selected OpenAI/Gemini model; no clinical validation'],['Document retrieval','Local keyword ranking and source excerpts; no vector embeddings'],['Urgency notice','Conservative text patterns; incomplete and not validated triage'],['Vital trends','Arithmetic differences; no risk forecasting'],['Calculators','Deterministic formulas; no clinical interpretation'],['Professional roles','Self-selected interface mode, not credential verification']],columns=['Component','Implementation']))

def reports():
    st.subheader('Reports, backup & session activity')
    p=current()
    if p:st.download_button('Selected patient · printable HTML / save as PDF',report_html(p),f"{p['id']}-report.html",'text/html')
    st.caption('Open the downloaded HTML in a browser and use Print → Save as PDF. Unicode text is preserved. Reports are not encrypted or signed.')
    st.download_button('Export full workspace backup JSON',snapshot(st.session_state.patients,st.session_state.facilities,st.session_state.events),'healthassist-workspace.json','application/json')
    st.download_button('Export activity log CSV',pd.DataFrame(st.session_state.events).to_csv(index=False),'healthassist-activity.csv','text/csv')
    st.caption('Activity is session-local, user-visible and mutable in an export. It is not a tamper-proof regulatory audit log.')
    with st.expander('Restore patient records from a v2 workspace backup'):
        data=st.file_uploader('Backup JSON',type=['json']);confirm=st.checkbox('Replace this session’s patient records with the uploaded patient records.')
        st.caption('Restores patients, observations, notes and tasks. Directory and activity-log fields are exported for reference but are not restored by this importer. Chat/API keys are not in this backup.')
        if st.button('Restore patient records',disabled=not confirm or data is None):
            try:
                patients=validate_import(data.getvalue());st.session_state.patients=patients;st.session_state.selected_patient=patients[0]['id'] if patients else None;event('Restored patient backup');st.success('Restored. Other sessions are unaffected.')
            except Exception:st.error('Invalid backup or unsupported values. No records were replaced.')
    st.dataframe(pd.DataFrame(st.session_state.events),hide_index=True,use_container_width=True)
