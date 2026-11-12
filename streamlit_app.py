"""Eurosender SEO Content Auditor — public pages, bilingual UI, Excel reports."""
import csv,io,os,json,hashlib
from datetime import datetime,timezone
import streamlit as st
from audit_engine import audit_live,audit_sample,build_rows,validate_url
from ai_engine import improve_with_ai, DEFAULT_MODEL
from usage_guard import ApiAttemptLimiter, DemoQuotaReached
from report_xlsx import make_report,label_priority,label_issue

WORDS={
'sl':{
 'headline':'🔎 SEO Content Auditor','tagline':'Eurosender · javne strani → SEO pregled → AI priporočila → pregledno Excel poročilo',
 'disclaimer':'Neodvisen projekt kandidata. Ni povezan z internimi sistemi podjetja Eurosender.',
 'settings':'⚙️ Nastavitve','language':'Jezik vmesnika','ai':'AI priporočila','enable':'Omogoči Gemini AI',
 'help_ai':'Glavni model: Flash-Lite. Uporablja 24-urni predpomnilnik in omejitev novih AI zahtevkov.',
 'key':'Gemini API ključ','key_missing':'Dodajte Gemini API ključ. SEO pregled lahko še vedno opravite brez AI.',
 'scope':'Omejitve','guard':'Samo javni HTTPS URL-ji domen eurosender.com in blog.eurosender.com. Največ 10 URL-jev na analizo, največ 2 MB na stran. Brez prijave in brez zasebnih podatkov.',
 'scoring':'Rezultat je interna kontrolna ocena, NE Googlov SEO rezultat.',
 'choose':'1 · Izberite vhod','input':'Vrsta analize','live':'Dejanski Eurosender URL-ji','demo':'Sintetična testna stran',
 'paste':'Vnesite po en Eurosender URL v vsako vrstico','selected':'Izbranih URL-jev: {n} (največ 10). Dostop do javnih strani je lahko omejen.',
 'demo_info':'Testni način uporablja lokalni primer HTML; ne predstavlja dejanske Eurosenderjeve strani.',
 'run':'▶ Zaženi SEO pregled','invalid':'Vnesite od 1 do 10 URL-jev.','progress':'Preverjenih {i}/{n} strani',
 'loading':'AI pripravlja priporočila …','results':'2 · Rezultati analize','pages':'Pregledane strani','findings':'Ugotovitve','high':'Visoka prioriteta','ai_pages':'Strani z AI pregledom',
 'last':'Zadnji pregled: {date} · To niso meritve uvrstitev ali prometa.','source':'Vir','title':'Naslov strani','description':'Meta opis','h1':'H1 naslov',
 'signals':'Podatki: {links} notranjih povezav · {images} slik · {alt} brez alt besedila · {words} zaznanih besed · kontrolna ocena {score}/100',
 'evidence':'Dokaz','none':'Po pravilih ni zaznanih težav. To ne pomeni, da je stran popolnoma optimizirana.',
 'suggestions':'✨ Gemini AI priporočila (za ročni pregled)','proposed_title':'Predlagani SEO naslov','proposed_desc':'Predlagani meta opis',
 'gemini_error':'Gemini trenutno ni na voljo: ','export':'3 · Prenos poročila','xlsx':'⬇ Prenesi urejeno Excel poročilo (.xlsx)',
 'csv':'⬇ Prenesi surovi CSV (za nadaljnjo obdelavo)','json':'⬇ Prenesi dokaze v JSON',
 'review':'AI predlogi zahtevajo pregled pred objavo. Orodje ne spreminja Eurosenderjevih strani.',
 'begin':'Izberite vhod in kliknite Zaženi SEO pregled.',
 'quota':'Demo zaščita: največ 3 AI strani na zagon, 12 dejanskih API zahtevkov na dan na strežniški proces. Ponovni pregledi iste vsebine se 24 ur pridobijo iz predpomnilnika.',
 'remaining':'Preostalih AI zahtevkov v lokalnem strežniškem števcu: {n} (ne prikazuje Googlove kvote).',
 'skipped':'AI analiza je omejena na prve 3 uspešno pregledane strani na zagon. Ostale dobijo običajni SEO pregled.',
 'quota_error':'Demo AI omejitev je dosežena. Poskusite kasneje ali uporabite že analiziran URL.',
 'cache_note':'AI odgovori za isto vsebino in jezik so 24 ur shranjeni v predpomnilniku. Model: '+ 'Flash-Lite.' ,
 },
'en':{
 'headline':'🔎 SEO Content Auditor','tagline':'Eurosender · public pages → SEO audit → AI recommendations → formatted Excel report',
 'disclaimer':'Independent candidate project. Not connected to Eurosender internal systems.',
 'settings':'⚙️ Settings','language':'Interface language','ai':'AI recommendations','enable':'Enable Gemini AI',
 'help_ai':'Primary model: Flash-Lite. Includes 24-hour caching and limits on new AI requests.',
 'key':'Gemini API key','key_missing':'Add a Gemini API key. SEO checks will work without one.',
 'scope':'Guardrails','guard':'Public HTTPS URLs at eurosender.com and blog.eurosender.com only. Up to 10 URLs per run, 2 MB per page. No login or private files.',
 'scoring':'The score is an internal checklist, NOT a Google SEO score.',
 'choose':'1 · Choose input','input':'Input type','live':'Live Eurosender URLs','demo':'Synthetic demo page',
 'paste':'One Eurosender URL per line','selected':'{n} URLs selected (maximum 10). Public website requests may be blocked.',
 'demo_info':'This demo uses local sample HTML, not an actual Eurosender page.',
 'run':'▶ Run SEO audit','invalid':'Please enter between 1 and 10 URLs.','progress':'Checked {i}/{n}',
 'loading':'Generating AI recommendations…','results':'2 · Audit results','pages':'Pages analyzed','findings':'Checklist findings','high':'High priority','ai_pages':'AI-reviewed pages',
 'last':'Last run: {date} · Not search ranking or traffic metrics.','source':'Source','title':'Title','description':'Meta description','h1':'H1 heading',
 'signals':'Signals: {links} internal links · {images} images · {alt} without alt · {words} extracted words · checklist score {score}/100',
 'evidence':'Evidence','none':'No rule-based issues detected. This does not imply full optimization.',
 'suggestions':'✨ Gemini AI suggestions (requires manual review)','proposed_title':'Suggested SEO title','proposed_desc':'Suggested meta description',
 'gemini_error':'Gemini unavailable: ','export':'3 · Export report','xlsx':'⬇ Download formatted Excel report (.xlsx)',
 'csv':'⬇ Download raw CSV (advanced)','json':'⬇ Download complete JSON evidence',
 'review':'AI suggestions require manual review before publishing. No website changes are made.',
 'begin':'Select an input and click Run SEO audit.',
 'quota':'Demo protection: at most 3 AI pages per run and 12 real API attempts per server process per UTC day. Identical content is cached for 24 hours.',
 'remaining':'AI calls left in local server counter: {n} (not the Google quota).',
 'skipped':'AI is limited to the first 3 successfully audited pages per run. Other pages still receive the rule-based SEO audit.',
 'quota_error':'Demo AI limit reached. Retry later or analyze previously cached content.',
 'cache_note':'AI responses are cached for 24 hours for identical content and language. Model: Flash-Lite.',
 }}

@st.cache_resource
def shared_limiter():
    return ApiAttemptLimiter(daily_limit=12, minute_limit=8)

@st.cache_data(ttl=86400, max_entries=250, show_spinner=False)
def cached_ai(evidence_signature: str, language: str, model: str, _record: dict, _api_key: str):
    # underscore arguments are intentionally omitted from the Streamlit cache key.
    # This project scans public pages only, and the digest binds the cached result
    # to the observed content and language without storing credentials.
    return improve_with_ai(_record, _api_key, language=language, model=model,
                           before_attempt=shared_limiter().consume)

def signature_for_record(record: dict) -> str:
    fields=('url','title','description','h1','canonical','word_count','content_excerpt','issues')
    data={field:record.get(field) for field in fields}
    raw=json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

st.set_page_config(page_title='SEO Content Auditor | Eurosender',page_icon='🔎',layout='wide')
with st.sidebar:
    lang=st.selectbox('🌐 Language / Jezik',['Slovenščina','English'],index=0)
    code='sl' if lang=='Slovenščina' else 'en'
    t=WORDS[code]
    st.header(t['settings'])
    st.markdown('**'+t['ai']+'**')
    use_ai=st.toggle(t['enable'],value=False,help=t['help_ai'])
    api_key=''
    if use_ai:
        try: secret=st.secrets.get('GEMINI_API_KEY','')
        except Exception: secret=''
        api_key=os.getenv('GEMINI_API_KEY') or secret or st.text_input(t['key'],type='password')
        if not api_key: st.warning(t['key_missing'])
    st.divider()
    st.markdown('**'+t['scope']+'**');st.caption(t['guard']);st.caption(t['scoring'])
    st.caption(t['quota'])
    if use_ai: st.caption(t['remaining'].format(n=shared_limiter().remaining_today()))

st.markdown('''<style>.hero{padding:22px 26px;background:linear-gradient(115deg,#132D54,#2366B0);border-radius:14px;color:white;margin-bottom:16px}.hero h1{color:white;font-size:2rem;margin:0 0 5px}.hero p{margin:0;color:#E3EDFF}</style>''',unsafe_allow_html=True)
st.markdown(f'<div class="hero"><h1>{t["headline"]}</h1><p>{t["tagline"]}</p></div>',unsafe_allow_html=True)
st.caption(t['disclaimer'])
st.subheader(t['choose'])
mode=st.radio(t['input'],[t['live'],t['demo']],horizontal=True)
seed='https://www.eurosender.com/en/dd/slovenia-germany\nhttps://www.eurosender.com/sl/stroski-posiljanja'
urls=[]
if mode==t['live']:
    pasted=st.text_area(t['paste'],value=seed,height=105)
    urls=list(dict.fromkeys(line.strip() for line in pasted.splitlines() if line.strip()))
    st.caption(t['selected'].format(n=len(urls)))
else:st.info(t['demo_info'])
if st.button(t['run'],type='primary',use_container_width=True):
    if mode==t['live'] and (not urls or len(urls)>10):st.error(t['invalid'])
    else:
        results=[]
        if mode==t['demo']:results=audit_sample()
        else:
            prog=st.progress(0)
            for i,url in enumerate(urls):
                try:results.append(audit_live(validate_url(url)))
                except Exception as e:results.append({'url':url,'source':'live','error':str(e)[:260]})
                prog.progress((i+1)/len(urls),text=t['progress'].format(i=i+1,n=len(urls)))
            prog.empty()
        if use_ai and api_key:
            with st.spinner(t['loading']):
                successful=[r for r in results if not r.get('error')]
                for r in successful[:3]:
                    try:
                        r['ai']=cached_ai(signature_for_record(r),code,DEFAULT_MODEL,r,api_key)
                    except DemoQuotaReached:
                        r['ai_error']=t['quota_error']
                    except Exception as e:
                        r['ai_error']=str(e)[:260]
                for r in successful[3:]: r['ai_notice']=t['skipped']
        st.session_state['seo_records']=results
        st.session_state['last_audit']=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

if 'seo_records' in st.session_state:
    records=st.session_state['seo_records']
    valid=[r for r in records if not r.get('error')]
    st.divider();st.subheader(t['results'])
    a,b,c,d=st.columns(4)
    a.metric(t['pages'],len(valid));b.metric(t['findings'],sum(len(r['issues']) for r in valid))
    c.metric(t['high'],sum(sum(i['priority']=='High' for i in r['issues']) for r in valid))
    d.metric(t['ai_pages'],sum(bool(r.get('ai')) for r in valid))
    st.caption(t['last'].format(date=st.session_state.get('last_audit','')))
    for r in records:
        with st.expander(('⚠️ ' if r.get('error') else '📄 ')+r.get('url',''),expanded=len(records)==1):
            if r.get('error'):st.error(r['error']);continue
            st.caption(t['source']+': '+r['source'])
            st.write('**'+t['title']+':**',r['title'] or '—');st.write('**'+t['description']+':**',r['description'] or '—')
            st.write('**'+t['h1']+':**',' | '.join(r['h1']) or '—')
            st.write(t['signals'].format(links=r['internal_link_count'],images=r['image_count'],alt=r['missing_alt'],words=r['word_count'],score=r['review_score']))
            if r['issues']:
                for issue in r['issues']:
                    st.markdown('**'+label_priority(issue['priority'],code)+': '+label_issue(issue['code'],code)+'**  \n'+issue['finding']+'  \n'+t['evidence']+': `'+issue['evidence']+'`')
            else:st.success(t['none'])
            if r.get('ai'):
                ai=r['ai'];st.markdown('#### '+t['suggestions']);st.write(ai['summary'])
                if ai['suggested_title'] and ai['suggested_title'].strip()!=r['title'].strip():st.write('**'+t['proposed_title']+':**',ai['suggested_title'])
                if ai['suggested_meta_description'] and ai['suggested_meta_description'].strip()!=r['description'].strip():st.write('**'+t['proposed_desc']+':**',ai['suggested_meta_description'])
                for sug in ai['recommendations']:st.markdown('- **'+label_issue(sug['issue_code'],code)+':** '+sug['action'])
            elif r.get('ai_error'):st.warning(t['gemini_error']+r['ai_error'])
            elif r.get('ai_notice'):st.info(r['ai_notice'])
    st.subheader(t['export'])
    try:
        book=make_report(records,code)
        st.download_button(t['xlsx'],data=book,file_name='eurosender_seo_pregled.xlsx' if code=='sl' else 'eurosender_seo_audit.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',use_container_width=True,type='primary')
    except Exception as e:st.error('Excel export error: '+str(e))
    with st.expander(t['csv']+' / JSON'):
        rows=build_rows(records)
        if rows:
            buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=list(rows[0]),lineterminator='\r\n');writer.writeheader();writer.writerows(rows)
            st.download_button(t['csv'],data='\ufeff'+buf.getvalue(),file_name='eurosender_seo_audit.csv',mime='text/csv')
        st.download_button(t['json'],data=json.dumps({'generated_at':st.session_state.get('last_audit'),'records':records},ensure_ascii=False,indent=2),file_name='eurosender_seo_audit.json',mime='application/json')
    st.info(t['review'])
    st.caption(t['cache_note'])
else:st.caption(t['begin'])
