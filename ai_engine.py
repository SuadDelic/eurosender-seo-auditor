"""Gemini-generated guidance; always clearly marked as suggestions rather than observed facts."""
from __future__ import annotations
import json,re,time

DEFAULT_MODEL='gemini-3.8-flash'
FALLBACK_MODEL='gemini-3.5-flash-lite'

def generate_with_retries(client, prompt, primary_model=DEFAULT_MODEL, sleep=time.sleep):
    """Retry temporary 503 outages, then attempt an available lower-cost backup model."""
    last_error = None
    for model in dict.fromkeys((primary_model, FALLBACK_MODEL)):
        for attempt in range(2):
            try:
                return client.models.generate_content(model=model, contents=prompt), model
            except Exception as exc:
                last_error = exc
                error = str(exc).lower()
                transient = any(x in error for x in ('503', 'unavailable', 'high demand', 'overloaded'))
                if not transient:
                    raise
                if attempt == 0:
                    sleep(2)
    raise RuntimeError(f'Gemini models unavailable after retries: {str(last_error)[:220]}')


def improve_with_ai(record:dict, api_key:str, model:str=DEFAULT_MODEL, client=None, language:str="sl")->dict:
    if not api_key and client is None: raise ValueError('Gemini API key is required for AI recommendations')
    if client is None:
        from google import genai
        client=genai.Client(api_key=api_key)
    evidence={key:record.get(key) for key in ('url','title','description','h1','canonical','word_count','content_excerpt','issues')}
    codes=[i['code'] for i in record.get('issues',[])]
    lang_instruction = ('Write the summary and recommendation action text in Slovenian (sl-SI). ' if language=='sl' else 'Write the summary and recommendation action text in English. ')
    prompt=(
        'You are an SEO analyst reviewing a PUBLIC Eurosender webpage. Return ONLY a valid JSON object with keys '
        '"summary" (one or two sentences), "suggested_title" (string), "suggested_meta_description" (string), '
        '"recommendations" (array of objects with "issue_code" and "action"). ' +
        lang_instruction + 'Do not translate the current page title or its meta description; suggested SEO title and description must stay in the ORIGINAL LANGUAGE of the webpage. If no change is justified, return empty strings for suggested_title and suggested_meta_description. ' +
        'Use only the supplied observed evidence; do not claim you measured rankings, traffic, page speed, conversion, '
        'search volume, actual Google indexation, or competitors. Do not invent shipping rates, delivery times, guarantees, '
        'business facts or product features. Keep suggestions usable and cautious. '
        'Each issue_code must be in this list: '+json.dumps(codes)+'. '
        'If the main content is insufficient, do not fabricate page text. '
        'Evidence:\n'+json.dumps(evidence,ensure_ascii=False)
    )
    response, used_model=generate_with_retries(client,prompt,model)
    raw=(response.text or '').strip()
    if raw.startswith('```'):
        raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw).strip()
    data=json.loads(raw)
    if not isinstance(data,dict): raise ValueError('AI response is not a JSON object')
    rec=[]
    for r in data.get('recommendations',[]):
        if isinstance(r,dict) and r.get('issue_code') in codes:
            rec.append({'issue_code':r['issue_code'],'action':str(r.get('action',''))[:450]})
    return {'mode':f'Gemini ({used_model})','summary':str(data.get('summary',''))[:700],
            'suggested_title':str(data.get('suggested_title',''))[:150],
            'suggested_meta_description':str(data.get('suggested_meta_description',''))[:250],
            'recommendations':rec}
