"""Professional Excel report for the independently developed SEO auditor."""
import io
import xlsxwriter

ISSUE_SL = {
 'MISSING_TITLE':'Manjka naslov strani','TITLE_LENGTH':'Dolžina naslova za pregled',
 'MISSING_DESCRIPTION':'Manjka meta opis','DESCRIPTION_LENGTH':'Dolžina meta opisa za pregled',
 'MISSING_H1':'Manjka naslov H1','MULTIPLE_H1':'Več naslovov H1',
 'MISSING_CANONICAL':'Manjka canonical povezava','NOINDEX':'Oznaka noindex',
 'MISSING_IMAGE_ALT':'Slike brez opisnega alt besedila','LOW_VISIBLE_TEXT':'Malo zaznanega besedila',
 'NO_INTERNAL_LINKS':'Ni zaznanih notranjih povezav','NO_RULE_ISSUES':'Brez ugotovitev po pravilih',
}
PRIORITY_SL = {'High':'Visoka','Medium':'Srednja','Low':'Nizka','Info':'Informativno','Error':'Napaka'}

def label_issue(code, lang='sl'):
    return ISSUE_SL.get(code,code) if lang=='sl' else code.replace('_',' ').title()

def label_priority(value,lang='sl'):
    return PRIORITY_SL.get(value,value) if lang=='sl' else value

def make_report(records, lang='sl') -> bytes:
    sl=lang=='sl'
    f=io.BytesIO()
    wb=xlsxwriter.Workbook(f,{'in_memory':True,'strings_to_urls':False,'strings_to_formulas':False})
    wb.set_properties({'title':'Eurosender SEO Content Auditor','comments':'Independent candidate case study. Checklist results are not Google ranking metrics.'})
    blue='#153762'; bright='#2369AD'; pale='#EAF1FA'; dark='#18304A'; green='#0F766E'
    title_fmt=wb.add_format({'bold':True,'font_size':18,'font_color':'white','bg_color':blue,'valign':'vcenter'})
    subtitle_fmt=wb.add_format({'font_size':10,'font_color':'#475569','text_wrap':True})
    head=wb.add_format({'bold':True,'font_color':'white','bg_color':bright,'valign':'vcenter','text_wrap':True,'border':0})
    body=wb.add_format({'font_color':dark,'valign':'top','text_wrap':True,'bottom':1,'bottom_color':'#EDF2F7'})
    body_odd=wb.add_format({'font_color':dark,'valign':'top','text_wrap':True,'bg_color':'#F5F8FC','bottom':1,'bottom_color':'#EDF2F7'})
    metric=wb.add_format({'font_size':18,'bold':True,'font_color':blue,'bg_color':pale})
    metriclabel=wb.add_format({'font_color':'#475569','bg_color':pale})
    flag_formats={
       'High':wb.add_format({'font_color':'#991B1B','bg_color':'#FEE2E2','bold':True}),
       'Medium':wb.add_format({'font_color':'#92400E','bg_color':'#FEF3C7','bold':True}),
       'Low':wb.add_format({'font_color':'#065F46','bg_color':'#D1FAE5','bold':True}),
       'Info':wb.add_format({'font_color':'#1D4ED8','bg_color':'#DBEAFE','bold':True}),
       'Error':wb.add_format({'font_color':'#991B1B','bg_color':'#FEE2E2','bold':True}),
    }
    link_fmt=wb.add_format({'font_color':'#1265AA','underline':1,'text_wrap':True,'valign':'top'})
    ws=wb.add_worksheet('Povzetek' if sl else 'Overview')
    ws.hide_gridlines(2)
    ws.set_column('A:A',24);ws.set_column('B:B',19);ws.set_column('C:C',18);ws.set_column('D:D',24);ws.set_column('E:E',24)
    ws.merge_range('A1:E2','EUROSENDER  |  '+('SEO PREGLED' if sl else 'SEO AUDIT'),title_fmt)
    ws.set_row(0,25); ws.set_row(1,18)
    ws.merge_range('A4:E4',('Neodvisen projekt za razgovor · javni URL-ji · AI priporočila zahtevajo pregled' if sl else 'Independent candidate project · public pages · AI suggestions require review'),subtitle_fmt)
    valid=[r for r in records if not r.get('error')]
    findings=sum(len(r.get('issues',[])) for r in valid)
    ai_count=sum(bool(r.get('ai')) for r in valid)
    metrics=[('Pregledane strani' if sl else 'Pages analyzed',len(valid)),('Ugotovitve' if sl else 'Findings',findings),('AI pregledane strani' if sl else 'AI-reviewed pages',ai_count)]
    for idx,(name,val) in enumerate(metrics):
        c=idx*2
        if c>4: break
        ws.write(6,c,name,metriclabel);ws.write(7,c,val,metric)
    ws.write('A11','URL',head);ws.write('B11',('Kontrolni rezultat' if sl else 'Checklist score'),head)
    ws.write('C11',('Število ugotovitev' if sl else 'Findings count'),head)
    ws.write('D11',('Slike brez alt' if sl else 'Images without alt'),head);ws.write('E11',('AI pregled' if sl else 'AI review'),head)
    for i,r in enumerate(records,11):
        b=body if i%2 else body_odd
        url=str(r.get('url',''))
        if url.startswith('https://'): ws.write_url(i,0,url,link_fmt,url[:150])
        else: ws.write(i,0,url,b)
        for col,value in enumerate([r.get('review_score','') if not r.get('error') else '',len(r.get('issues',[])),r.get('missing_alt',''),('Da' if sl else 'Yes') if r.get('ai') else ('Ne' if sl else 'No')],1): ws.write(i,col,value,b)
        ws.set_row(i,38)
    ws.autofilter(10,0,max(11,len(records)+10),4)
    ws.freeze_panes(11,1)
    ws.merge_range('A'+str(max(15,len(records)+14))+':E'+str(max(15,len(records)+14)),('Kontrolni rezultat ni Googlov SEO score. Ugotovitve preverite pred objavo. Dekorativne slike lahko pravilno uporabljajo alt="".' if sl else 'Checklist score is not a Google SEO score. Verify findings before publishing. Decorative images may correctly use alt="".'),subtitle_fmt)

    wi=wb.add_worksheet('Ugotovitve' if sl else 'Findings')
    wi.hide_gridlines(2)
    columns=['URL','Prioriteta' if sl else 'Priority','Koda' if sl else 'Code','Preverjanje' if sl else 'Check','Ugotovitev / dokaz' if sl else 'Evidence / finding','Predlagan ukrep' if sl else 'Suggested action','Status' if sl else 'Status']
    wi.set_column('A:A',43);wi.set_column('B:B',14);wi.set_column('C:C',22);wi.set_column('D:D',26);wi.set_column('E:E',55);wi.set_column('F:F',65);wi.set_column('G:G',19)
    wi.set_row(0,34)
    for c,h in enumerate(columns):wi.write(0,c,h,head)
    idx=1
    for rec in records:
        ai=rec.get('ai') or {}
        sugg={s['issue_code']:s['action'] for s in ai.get('recommendations',[]) if s.get('issue_code')}
        issues=rec.get('issues',[]) if not rec.get('error') else [{'code':'FETCH_ERROR','priority':'Error','finding':rec['error'],'evidence':''}]
        if not issues: issues=[{'code':'NO_RULE_ISSUES','priority':'Info','finding':'No rule-based issues','evidence':''}]
        for issue in issues:
            b=body if idx%2 else body_odd
            url=rec.get('url','')
            if url.startswith('https://'):wi.write_url(idx,0,url,link_fmt,url[:200])
            else:wi.write(idx,0,url,b)
            sev=issue.get('priority','Info')
            wi.write(idx,1,label_priority(sev,lang),flag_formats.get(sev,b))
            wi.write(idx,2,issue.get('code',''),b)
            wi.write(idx,3,label_issue(issue.get('code',''),lang),b)
            wi.write(idx,4,(issue.get('finding','')+'\n'+issue.get('evidence','')).strip(),b)
            wi.write(idx,5,sugg.get(issue.get('code',''),''),b)
            wi.write(idx,6,'Za pregled' if sl else 'Needs review',b)
            wi.set_row(idx,72)
            idx+=1
    wi.autofilter(0,0,max(idx-1,1),6)
    wi.freeze_panes(1,1)

    wc=wb.add_worksheet('SEO besedila' if sl else 'SEO copy')
    wc.hide_gridlines(2)
    cols=['URL','Obstoječi naslov' if sl else 'Current title','Predlagani naslov' if sl else 'Suggested title','Obstoječi meta opis' if sl else 'Current meta description','Predlagani meta opis' if sl else 'Suggested meta description','AI povzetek' if sl else 'AI summary']
    for c,h in enumerate(cols):wc.write(0,c,h,head)
    for c,w in enumerate([43,48,48,64,64,85]):wc.set_column(c,c,w)
    wc.set_row(0,34)
    for i,r in enumerate(valid,1):
        ai=r.get('ai') or {}
        values=[r.get('url',''),r.get('title',''),ai.get('suggested_title',''),r.get('description',''),ai.get('suggested_meta_description',''),ai.get('summary','')]
        for c,v in enumerate(values):
            if c==0 and str(v).startswith('https://'):wc.write_url(i,c,v,link_fmt,v[:200])
            else:wc.write(i,c,str(v),body if i%2 else body_odd)
        wc.set_row(i,90)
    wc.freeze_panes(1,1)
    wc.autofilter(0,0,max(len(valid),1),5)
    wb.close()
    return f.getvalue()
