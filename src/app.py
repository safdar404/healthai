from pathlib import Path
import hmac
import os
import streamlit as st
from dotenv import load_dotenv
from healthassist import pages
from healthassist.chat import render_agent
from healthassist.workspace import agent_context

load_dotenv()
ROOT=Path(__file__).resolve().parents[1]
st.set_page_config(page_title='HealthAssist · Agentic Health Platform',page_icon='🩺',layout='wide',initial_sidebar_state='expanded')
st.markdown('<style>'+(ROOT/'src/healthassist/style.css').read_text()+'</style>',unsafe_allow_html=True)

def setting(name,default=''):
    try:value=st.secrets.get(name,'')
    except (FileNotFoundError,st.errors.StreamlitSecretNotFoundError):value=''
    return str(value or os.getenv(name,default))

password=setting('APP_ACCESS_PASSWORD')
if password and not st.session_state.get('authorized'):
    st.title('HealthAssist · Private workspace')
    entered=st.text_input('Workspace password',type='password')
    if st.button('Open workspace'):
        if hmac.compare_digest(entered,password):st.session_state.authorized=True;st.rerun()
        else:st.error('Incorrect workspace password.')
    st.stop()

for name,default in [('messages',[]),('passages',[]),('documents',[]),('last_result',{}),('turns',0),('patients',[]),('facilities',[]),('events',[])]:
    if name not in st.session_state:st.session_state[name]=default

with st.sidebar:
    a,b=st.columns([1,3]);a.image(str(ROOT/'assets/healthassist-mark.svg'),width=48);b.markdown('### HealthAssist\nAGENTIC HEALTH PLATFORM')
    st.caption('Python workspace · v2')
    page=st.radio('Workspace navigation',['Overview','Patient Intake','Patient Registry','Clinical Workspace','AI Care Agent','Care Tasks','Facilities & GIS','Calculators','References & Models','Reports & Backup','Settings'],key='navigation')
    st.divider()
    choices={'No patient selected':None, **{p['alias']+' · '+p['id']:p['id'] for p in st.session_state.patients}}
    previous=st.session_state.get('selected_patient')
    values=list(choices.values())
    label=st.selectbox('Active encounter',list(choices),index=values.index(previous) if previous in values else 0)
    selected=choices[label]
    st.session_state.selected_patient=selected
    if st.session_state.get('chat_patient')!=selected:
        st.session_state.messages=[];st.session_state.last_result={};st.session_state.documents=[];st.session_state.passages=[];st.session_state.chat_patient=selected
    role=st.selectbox('Conversation mode',['Patient','Doctor'])
    language=st.selectbox('Reply language',['English','Urdu','English and Urdu'])
    with st.expander('API connection',expanded=page=='AI Care Agent'):
        provider=st.selectbox('API provider',['OpenAI','Gemini'])
        own_key=st.text_input('Your API key (session only)',type='password',key='key_'+provider)
        keyname='OPENAI_API_KEY' if provider=='OpenAI' else 'GEMINI_API_KEY'
        hosted_key=setting(keyname) if password or setting('ALLOW_SHARED_KEY').lower()=='true' else ''
        api_key=own_key or hosted_key
        model=st.text_input('Model ID',value=setting('OPENAI_MODEL','gpt-4.1-mini') if provider=='OpenAI' else setting('GEMINI_MODEL','gemini-2.5-flash'),key='model_'+provider)
        st.caption('Provider API billing applies. Keys are never included in exported backups.')
    st.caption('Session-local records. Export a backup before closing. Doctor mode does not verify credentials.')

st.caption(f'HEALTHASSIST / {page.upper()}   ·   Research prototype · human clinical review required')
if page=='Overview':pages.dashboard(ROOT)
elif page=='Patient Intake':pages.intake()
elif page=='Patient Registry':pages.registry()
elif page=='Clinical Workspace':pages.clinical()
elif page=='AI Care Agent':render_agent(provider,api_key,model,role,language,agent_context(pages.current()))
elif page=='Care Tasks':pages.tasks()
elif page=='Facilities & GIS':pages.facilities()
elif page=='Calculators':pages.calculators()
elif page=='References & Models':pages.resources()
elif page=='Reports & Backup':pages.reports()
elif page=='Settings':
    st.subheader('Workspace configuration & data controls')
    st.info('No hospital backend, pharmacy interaction database, autonomous diagnosis, emergency dispatch or live clinician network is connected. The implemented agent uses your selected provider and explicit tools.')
    st.markdown('### Agent tools\n- Selected encounter context (opt-in)\n- Recorded vital-sign changes\n- Document evidence retrieval\n- BMI arithmetic\n- SOAP review draft\n- Care checklist draft\n- Clinician handoff draft')
    st.write('Clear chat when changing patients; the app also resets chat and uploaded documents on encounter changes. API and retrieved excerpts are processed by the chosen provider according to its policies. No patient locations are sent to the agent.')
    if st.button('Clear conversation and uploaded documents'):
        for k,v in [('messages',[]),('passages',[]),('documents',[]),('last_result',{})]:st.session_state[k]=v
        pages.event('Cleared chat and documents');st.success('Application session values cleared. This does not erase provider retention or certify memory deletion.')
    confirm=st.checkbox('I intend to clear all records, facilities, chat and activity from this session.')
    if st.button('Reset entire workspace',disabled=not confirm):
        for k in ['patients','facilities','events','messages','documents','passages','last_result','selected_patient','chat_patient']:st.session_state.pop(k,None)
        st.rerun()
    st.code('python -m pip install -r requirements.txt\npython -m streamlit run app.py',language='bash')
    st.caption('Streamlit Cloud main file: app.py · Python 3.12 recommended. See README.md for GitHub deployment.')
st.divider()
st.caption('HealthAssist v2 · Muhammad Safdar · Educational and research workspace. No diagnosis, prescribing, emergency monitoring or regulatory approval is claimed.')
