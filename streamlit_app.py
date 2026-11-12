"""Eurosender SEO Content Auditor — independent portfolio demonstration."""
import csv,io,os,time,json
from datetime import datetime,timezone
import streamlit as st
from audit_engine import audit_live,audit_sample,build_rows,validate_url,AuditError
from ai_engine import improve_with_ai,DEFAULT_MODEL

st.set_page_config(page_title='SEO Content Auditor | Eurosender case study',page_icon='🔎',layout='wide')
st.markdown('''<style>
.hero{padding:22px 26px;background:linear-gradient(115deg,#132D54,#2366B0);border-radius:14px;color:white;margin-bottom:16px}
.hero h1{color:white;font-size:2.05rem;margin:0 0 5px}
.hero p{margin:0;color:#E3EDFF}
small{color:#6C7F96}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🔎 SEO Content Auditor</h1><p>Eurosender case study · public web pages → SEO signals → AI suggestions → Excel-ready export</p></div>',unsafe_allow_html=True)
st.caption('Independent candidate portfolio project. Not affiliated with, endorsed by, or connected to Eurosender internal systems.')

with st.sidebar:
    st.header('⚙️ Settings')
    st.markdown('**AI recommendations**')
    use_ai=st.toggle('Enable Gemini AI',value=False,help='Requires your own key. The factual SEO scan works without AI.')
    api_key=''
    if use_ai:
        try: secret=st.secrets.get('GEMINI_API_KEY','')
        except Exception: secret=''
        api_key=os.getenv('GEMINI_API_KEY') or secret or st.text_input('Gemini API key',type='password',help='Never paste keys into public documentation or code.')
        if not api_key: st.warning('Add a key to run AI recommendations. SEO rules will still work.')
    st.divider()
    st.markdown('**Guardrails**')
    st.caption('Only eurosender.com or blog.eurosender.com HTTPS URLs. Maximum 10 URLs, 2 MB per page. No login, no private files. No search ranking or traffic claims.')
    st.caption('Scoring is a custom checklist, NOT a Google SEO score.')

st.subheader('1 · Choose input')
mode=st.radio('Input type',['Live Eurosender URLs','Synthetic demo page'],horizontal=True,help='Synthetic demo is clearly labeled and does not claim to represent the current Eurosender website.')
seed='https://www.eurosender.com/en/dd/slovenia-germany\nhttps://www.eurosender.com/sl/stroski-posiljanja'
urls=[]
if mode=='Live Eurosender URLs':
    pasted=st.text_area('Paste one Eurosender URL per line',value=seed,height=106)
    urls=list(dict.fromkeys(line.strip() for line in pasted.splitlines() if line.strip()))
    st.caption(f'{len(urls)} URLs selected (maximum 10). Public website requests can be blocked or change over time.')
else:
    st.info('This mode analyzes a deliberately incomplete local HTML example; it never fetches Eurosender.')

start=st.button('▶ Run SEO audit',type='primary',use_container_width=True)
if start:
    if mode=='Live Eurosender URLs' and (not urls or len(urls)>10): st.error('Please enter between 1 and 10 URLs.')
    else:
        results=[]
        if mode=='Synthetic demo page': results=audit_sample()
        else:
            progress=st.progress(0,text='Checking URLs…')
            for i,url in enumerate(urls):
                try:
                    validated=validate_url(url)
                    results.append(audit_live(validated))
                except Exception as e:
                    results.append({'url':url,'source':'live','error':str(e)[:260]})
                progress.progress((i+1)/len(urls),text=f'Checked {i+1}/{len(urls)}')
            progress.empty()
        if use_ai and api_key:
            with st.spinner('Generating AI recommendations…'):
                for r in results:
                    if r.get('error'): continue
                    try: r['ai']=improve_with_ai(r,api_key)
                    except Exception as e: r['ai_error']=str(e)[:260]
        st.session_state['seo_records']=results
        st.session_state['last_audit']=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

if 'seo_records' in st.session_state:
    records=st.session_state['seo_records']
    valid=[r for r in records if not r.get('error')]
    num_issues=sum(len(r['issues']) for r in valid)
    num_high=sum(sum(i['priority']=='High' for i in r['issues']) for r in valid)
    num_ai=sum(bool(r.get('ai')) for r in valid)
    st.divider()
    st.subheader('2 · Audit results')
    a,b,c,d=st.columns(4)
    a.metric('Pages analyzed',len(valid))
    b.metric('Checklist findings',num_issues)
    c.metric('High-priority findings',num_high)
    d.metric('AI-reviewed pages',num_ai)
    st.caption(f'Last run: {st.session_state.get("last_audit","")} · These metrics describe checklist results, not SEO performance.')
    for r in records:
        with st.expander(('⚠️ ' if r.get('error') else '📄 ')+r.get('url',''),expanded=len(records)==1):
            if r.get('error'):
                st.error(r['error']); continue
            st.caption('Source: '+r['source'])
            st.write('**Title:**',r['title'] or 'Missing')
            st.write('**Meta description:**',r['description'] or 'Missing')
            st.write('**H1:**', ' | '.join(r['h1']) or 'Missing')
            st.write(f'**Signals:** {r["internal_link_count"]} internal links · {r["image_count"]} images · {r["missing_alt"]} without alt · {r["word_count"]} extracted words · Checklist score {r["review_score"]}/100')
            if r['issues']:
                for i in r['issues']:
                    st.markdown(f'**{i["priority"]}: {i["code"]}** — {i["finding"]}  \nEvidence: `{i["evidence"]}`')
            else: st.success('No rule-based issues detected; this does not imply that the page is fully optimized.')
            if r.get('ai'):
                ai=r['ai']; st.markdown('#### ✨ Gemini AI suggestions (not verified facts)')
                st.write(ai['summary'])
                if ai['suggested_title']: st.write('**Proposed title:**',ai['suggested_title'])
                if ai['suggested_meta_description']: st.write('**Proposed description:**',ai['suggested_meta_description'])
                for sug in ai['recommendations']: st.markdown(f'- **{sug["issue_code"]}:** {sug["action"]}')
            elif r.get('ai_error'): st.warning('Gemini unavailable: '+r['ai_error'])
    st.subheader('3 · Export for Excel')
    rows=build_rows(records)
    if rows:
        st.dataframe(rows,use_container_width=True,hide_index=True)
        f=io.StringIO(newline='')
        wr=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator='\r\n')
        wr.writeheader();wr.writerows(rows)
        st.download_button('⬇ Download Excel-ready CSV',data='\ufeff'+f.getvalue(),file_name='eurosender_seo_audit.csv',mime='text/csv',use_container_width=True)
        st.download_button('⬇ Download complete JSON evidence',data=json.dumps({'generated_at':st.session_state.get('last_audit'),'records':records},ensure_ascii=False,indent=2),file_name='eurosender_seo_audit.json',mime='application/json',use_container_width=True)
    st.info('Manual review is required before publishing suggested copy. CSV opens in Excel; no changes are made to the website.')
else:
    st.caption('Select an input and click Run SEO audit to start. AI is opt-in and requires a Gemini API key.')
