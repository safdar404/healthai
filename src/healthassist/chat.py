from pathlib import Path
import json
from datetime import datetime, timezone
import streamlit as st
from openai import AuthenticationError, RateLimitError
from .agent import make_client, run_agent
from .core import bmi, extract, handoff, urgent_flag, EMERGENCY_MESSAGE

def render_agent(provider, api_key, model, role, language, workspace_context=None):
    st.subheader('AI Care Agent · connected reasoning and tools')
    st.caption('Ask to review an included encounter, compare readings, search documents, draft SOAP notes, prepare a handoff or create an appointment checklist. Drafts require human review.')
    chat, docs, tools, export_tab = st.tabs(['💬 Agent conversation','📚 Document knowledge','🧰 Care preparation','↓ Export & setup'])
    with docs:
        st.subheader('Bring context to the conversation')
        st.write('PDF, Word, TXT and Markdown are extracted on this server. Only documents explicitly included below can be retrieved by the agent.')
        files = st.file_uploader('Select documents', type=['pdf','docx','txt','md'], accept_multiple_files=True)
        if st.button('Process selected documents'):
            passages=[]; names=[]
            if len(files)>8: st.error('Select at most 8 files.')
            elif sum(f.size for f in files)>25*1024*1024: st.error('Combined limit: 25 MB.')
            else:
                for f in files:
                    try: passages.extend(extract(f.name,f.getvalue())); names.append(f.name)
                    except Exception as exc:
                        st.error(f'{f.name}: extraction failed. Check that the file is readable and unencrypted; scans need OCR.')
                st.session_state.passages=passages; st.session_state.documents=names
                st.success(f'{len(names)} documents processed. {len(passages)} text passages available.'); st.rerun()
        st.write('Loaded:', ', '.join(st.session_state.documents) or 'None')
        if st.session_state.passages:
            st.text_area('Extraction preview', '\n\n'.join(c['text'] for c in st.session_state.passages[:3]), height=200, disabled=True)
        st.caption('Keyword RAG retrieval, not semantic vector search. Documents may be outdated or incorrect. No OCR or live medical web search is included.')
    with tools:
        st.subheader('Prepare a clinician handoff')
        with st.form('handoff'):
            concern=st.text_area('Main concern (avoid names and identifiers)')
            duration=st.text_input('When did it start?')
            medicines=st.text_area('Reported medicines — include only what you know')
            allergies=st.text_input('Reported allergies')
            questions=st.text_area('Questions for the clinician')
            submitted=st.form_submit_button('Prepare draft')
        if submitted: st.session_state.draft=handoff(concern,duration,medicines,allergies,questions)
        if st.session_state.get('draft'):
            st.json(st.session_state.draft)
            st.download_button('Download handoff JSON',json.dumps(st.session_state.draft,ensure_ascii=False,indent=2),'healthassist-handoff.json','application/json')
        st.subheader('BMI arithmetic')
        a,b=st.columns(2); w=a.number_input('Weight (kg)',1.0,500.0,70.0); h=b.number_input('Height (cm)',30.0,260.0,170.0)
        if st.button('Calculate BMI'): st.json(bmi(w,h))
    with chat:
        include_encounter = st.checkbox('Include the selected de-identified encounter in agent tools (age, reported history, observations, labs and notes)', value=False, disabled=workspace_context is None)
        include_docs = st.checkbox('Include loaded documents in agent retrieval', value=False)
        consent = st.checkbox('I agree to send this conversation and any included document excerpts to the selected API provider. I have removed identifiers or have appropriate permission.',value=False)
        st.caption('Do not enter names, phone numbers, IDs or identifiable patient records. Uploaded excerpts are sent only if included and retrieved. Switching providers sends retained conversation to the newly selected provider when you submit.')
        for message in st.session_state.messages:
            with st.chat_message(message['role']): st.markdown(message['content'])
        prompt=st.chat_input('Ask about symptoms, documents, care options or questions for your doctor',max_chars=8000)
        with st.expander('Voice input · optional (OpenAI only)'):
            st.caption('Record, transcribe, review the text, then submit it. Audio is sent to OpenAI only when you press Transcribe.')
            audio=st.audio_input('Record a question')
            if st.button('Transcribe recording',disabled=provider!='OpenAI'):
                if not consent or not api_key: st.error('Add your OpenAI key and tick the data-sharing consent first.')
                elif not audio: st.error('Record a question first.')
                elif audio.size>10*1024*1024: st.error('Use a shorter recording (maximum 10 MB).')
                else:
                    try:
                        result=make_client(provider,api_key).audio.transcriptions.create(model='gpt-4o-mini-transcribe',file=('question.wav',audio.getvalue(),'audio/wav'))
                        st.session_state.voice_text=result.text
                    except Exception: st.error('Transcription failed. Check key, quota, model access and connection.')
            voice=st.text_area('Review transcription',key='voice_text')
            send_voice=st.button('Send reviewed text')
            if send_voice: prompt=voice
        if prompt:
            if urgent_flag(prompt): st.error(EMERGENCY_MESSAGE)
            if not consent: st.error('Please review and accept data-sharing consent before sending to the API.')
            elif not api_key or not model.strip(): st.error('Add your API key and model ID in the sidebar.')
            else:
                st.session_state.messages.append({'role':'user','content':prompt})
                with st.chat_message('user'): st.markdown(prompt)
                try:
                    with st.spinner('Reviewing context and using tools when relevant…'):
                        result=run_agent(make_client(provider,api_key),model.strip(),st.session_state.messages,role,language,
                                         st.session_state.passages if include_docs else [],
                                         workspace_context=workspace_context if include_encounter else None)
                    if urgent_flag(prompt): result['text']=EMERGENCY_MESSAGE+'\n\n'+result['text']
                    st.session_state.messages.append({'role':'assistant','content':result['text']})
                    st.session_state.last_result=result; st.session_state.turns+=1
                    with st.chat_message('assistant'): st.markdown(result['text'])
                except AuthenticationError: st.error('Authentication failed. Check the key and selected provider.')
                except RateLimitError: st.error('Provider quota or rate limit reached. Check billing or wait and retry.')
                except Exception: st.error('The request failed. Check provider availability, model ID, billing and connection. No final answer was generated.')
        result=st.session_state.last_result
        if result and result.get('drafts'):
            for i, draft in enumerate(result['drafts']):
                st.download_button('Download agent draft '+str(i+1),json.dumps(draft,ensure_ascii=False,indent=2),f'healthassist-agent-draft-{i+1}.json','application/json',key='agentdraft_'+str(i))
        if result:
            with st.expander('Agent tool activity and retrieved sources'):
                for item in result.get('trace',[]):
                    st.write('Tool:',item['tool']); st.json(item['result'])
                for item in result.get('sources',[]):
                    st.markdown(f"**[{item['citation']}] {item['source']} · page {item.get('page') or 'not available'}**")
                    st.write(item['text'])
                if not result.get('trace'): st.caption('No tools were called for this answer.')
    with export_tab:
        st.subheader('Export this session')
        text='HealthAssist — unreviewed conversation\n'+datetime.now(timezone.utc).isoformat()+'\n\n'+ '\n\n'.join(m['role'].upper()+': '+m['content'] for m in st.session_state.messages)
        st.download_button('Download conversation Markdown',text,'healthassist-conversation.md','text/markdown')
        payload={'generated_at':datetime.now(timezone.utc).isoformat(),'messages':st.session_state.messages,'last_agent_result':st.session_state.last_result}
        st.download_button('Download conversation + evidence JSON',json.dumps(payload,ensure_ascii=False,indent=2),'healthassist-session.json','application/json')
        st.info('To print: download the Markdown, open it in VS Code preview or a document editor, and print. Exports may contain sensitive information; store them appropriately.')
        st.code('python -m pip install -r requirements.txt\npython -m streamlit run app.py',language='bash')
        st.write('For Streamlit Cloud: connect the GitHub repository, choose app.py, set Python 3.12, and configure Secrets. Read README.md for the complete steps.')
