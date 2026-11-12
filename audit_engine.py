"""Deterministic SEO extraction and checks; generative suggestions are separate."""
from __future__ import annotations
import json, re, socket, ipaddress, urllib.parse
from collections import Counter
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup

ALLOWED_HOSTS = {'eurosender.com','www.eurosender.com','blog.eurosender.com'}
MAX_BYTES = 2_000_000
USER_AGENT = 'EurosenderSEOAuditorDemo/1.0 (public pages; educational marketing exercise)'

class AuditError(Exception): pass

def validate_url(raw: str) -> str:
    raw=raw.strip()
    if not raw: raise AuditError('Empty URL')
    u=urllib.parse.urlsplit(raw)
    host=(u.hostname or '').lower().rstrip('.')
    if u.scheme != 'https' or host not in ALLOWED_HOSTS or u.username or u.password or u.port not in (None,443):
        raise AuditError('Only HTTPS public eurosender.com / blog.eurosender.com URLs are accepted.')
    if len(raw)>1500: raise AuditError('URL is too long')
    return urllib.parse.urlunsplit(('https',host,u.path or '/',u.query,''))

def _public_dns(host: str) -> None:
    """Block private network resolution if a host is changed or compromised."""
    try: info=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
    except OSError as e: raise AuditError(f'DNS lookup failed: {e}') from e
    for entry in info:
        addr=ipaddress.ip_address(entry[4][0])
        if not addr.is_global: raise AuditError('Non-public address refused')

def fetch_html(raw: str) -> tuple[str,int,str]:
    url=validate_url(raw)
    session=requests.Session()
    session.trust_env=True
    current=url
    for _ in range(4):
        host=urllib.parse.urlsplit(current).hostname
        _public_dns(host)
        try:
            with session.get(current,headers={'User-Agent':USER_AGENT,'Accept':'text/html'}, timeout=(5,15),allow_redirects=False,stream=True) as response:
                if response.status_code in (301,302,303,307,308):
                    location=response.headers.get('Location')
                    if not location: raise AuditError('Redirect missing destination')
                    current=validate_url(urllib.parse.urljoin(current,location))
                    continue
                status=response.status_code
                if status != 200: raise AuditError(f'HTTP {status}')
                if 'text/html' not in response.headers.get('Content-Type','').lower():
                    raise AuditError('URL did not return HTML')
                chunks=[]; total=0
                for chunk in response.iter_content(16384):
                    total += len(chunk)
                    if total>MAX_BYTES: raise AuditError('Page larger than 2 MB; skipped')
                    chunks.append(chunk)
                response.encoding=response.encoding or 'utf-8'
                return (b''.join(chunks).decode(response.encoding,errors='replace'),status,current)
        except requests.RequestException as e: raise AuditError(f'Page could not be loaded: {str(e)[:150]}') from e
    raise AuditError('Too many redirects')

def clean(s: str) -> str: return ' '.join(str(s or '').split())

def analyze_html(url: str, html: str, status: int=200, source: str='live') -> dict:
    soup=BeautifulSoup(html,'html.parser')
    title=clean(soup.title.get_text(' ',strip=True)) if soup.title else ''
    def meta(name):
        node=soup.find('meta',attrs={'name':name})
        return clean(node.get('content','')) if node else ''
    desc=meta('description')
    robots=meta('robots')
    h1=[clean(e.get_text(' ',strip=True)) for e in soup.find_all('h1')]
    h2=[clean(e.get_text(' ',strip=True)) for e in soup.find_all('h2')]
    can=soup.find('link',attrs={'rel':lambda v: v and 'canonical' in v})
    canonical=clean(can.get('href','')) if can else ''
    images=soup.find_all('img')
    missing_alt=sum(1 for i in images if not clean(i.get('alt','')))
    links=[]
    for a in soup.find_all('a',href=True):
        full=urllib.parse.urljoin(url, a['href'])
        p=urllib.parse.urlsplit(full)
        if p.scheme in ('http','https') and p.hostname and (p.hostname.lower().rstrip('.') in ALLOWED_HOSTS):
            links.append(full)
    for node in soup(['script','style','noscript','nav','footer','header']): node.decompose()
    main=soup.find('main') or soup.find('article') or soup.body or soup
    body=clean(main.get_text(' ',strip=True))[:6500]
    words=len(re.findall(r'\b\w+\b',body,flags=re.UNICODE))
    issues=[]
    def add(code, severity, why, evidence):
        issues.append({'code':code,'priority':severity,'finding':why,'evidence':str(evidence)[:250]})
    if not title: add('MISSING_TITLE','High','Page has no HTML <title>','Absent')
    elif len(title)<25 or len(title)>65: add('TITLE_LENGTH','Medium','Title length outside review range (25–65 characters)',f'{len(title)} characters: {title}')
    if not desc: add('MISSING_DESCRIPTION','High','Meta description is missing','Absent')
    elif len(desc)<70 or len(desc)>165: add('DESCRIPTION_LENGTH','Low','Meta description length outside review range (70–165 characters)',f'{len(desc)} characters')
    if not h1: add('MISSING_H1','High','Page has no H1 heading','Absent')
    if len(h1)>1: add('MULTIPLE_H1','Low','Page has multiple H1 headings',len(h1))
    if not canonical: add('MISSING_CANONICAL','Medium','No HTML canonical link found','Absent')
    if 'noindex' in robots.lower(): add('NOINDEX','High','Robots meta tag includes noindex',robots)
    if missing_alt: add('MISSING_IMAGE_ALT','Medium','Images without non-empty alt attributes',f'{missing_alt} of {len(images)} images')
    if words<150: add('LOW_VISIBLE_TEXT','Low','Little extracted main text: review manually (dynamic pages can cause false positives)',f'{words} words')
    if not links: add('NO_INTERNAL_LINKS','Low','No internal links found in downloaded HTML','0')
    # Not a search-ranking score; review signal only
    score=max(0,100-sum({'High':18,'Medium':9,'Low':4}[i['priority']] for i in issues))
    return {'url':url,'status':status,'source':source,'title':title,'title_length':len(title),'description':desc,'description_length':len(desc),'h1':h1,'h2_count':len(h2),'canonical':canonical,'robots':robots,'image_count':len(images),'missing_alt':missing_alt,'internal_link_count':len(set(links)),'word_count':words,'content_excerpt':body[:2200],'issues':issues,'review_score':score,'ai':None}

def audit_live(url: str) -> dict:
    html,status,final_url=fetch_html(url)
    rec=analyze_html(final_url,html,status,'live')
    rec['requested_url']=validate_url(url)
    return rec

def audit_sample() -> list[dict]:
    from pathlib import Path
    fixture=Path(__file__).parent/'examples'/'synthetic_page.html'
    return [analyze_html('https://www.eurosender.com/en/dd/sample-demo',fixture.read_text(encoding='utf-8'),source='SYNTHETIC DEMO — not a real Eurosender page')]

def build_rows(records: list[dict]) -> list[dict]:
    out=[]
    for r in records:
        if r.get('error'):
            out.append({'URL':r['url'],'Source':r.get('source','live'),'Severity':'Error','Check':'Fetch failed','Finding':r['error'],'Evidence':'','Suggested action':'Review URL, network, and access','AI mode':'Not run','AI summary':'','Proposed title':'','Proposed description':'','Review score':''})
            continue
        ai=r.get('ai') or {}
        suggestions=ai.get('recommendations') or []
        for issue in r['issues'] or [{'code':'NO_RULE_ISSUES','priority':'Info','finding':'No rule-based issues detected','evidence':''}]:
            matching=[x for x in suggestions if x.get('issue_code')==issue['code']]
            out.append({'URL':r['url'],'Source':r['source'],'Severity':issue['priority'],'Check':issue['code'],'Finding':issue['finding'],'Evidence':issue['evidence'],'Suggested action':'; '.join(x.get('action','') for x in matching),'AI mode':ai.get('mode','Not run'),'AI summary':ai.get('summary',''),'Proposed title':ai.get('suggested_title',''),'Proposed description':ai.get('suggested_meta_description',''),'Review score':r['review_score']})
    return out
