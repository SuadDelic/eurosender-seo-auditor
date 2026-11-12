"""Grounded Gemini SEO advice; the low-cost Flash-Lite model is primary."""
from __future__ import annotations
import json
import re
import time

DEFAULT_MODEL = 'gemini-3.5-flash-lite'
# Explicitly avoid exhausted 3.8 Flash when the free-tier daily limit is hit.
# Transient service problems get just one retry; 429 errors are not retried.

def generate_with_retries(client, prompt, primary_model=DEFAULT_MODEL, sleep=time.sleep, before_attempt=None):
    last_error = None
    for attempt in range(2):
        if before_attempt is not None:
            before_attempt()
        try:
            return client.models.generate_content(model=primary_model, contents=prompt), primary_model
        except Exception as exc:
            last_error = exc
            error = str(exc).lower()
            temporary = any(token in error for token in ('503', 'high demand', 'overloaded', 'service unavailable'))
            if not temporary or attempt == 1:
                raise
            sleep(2)
    raise last_error


def improve_with_ai(record:dict, api_key:str, model:str=DEFAULT_MODEL, client=None, language:str='sl', before_attempt=None)->dict:
    if not api_key and client is None:
        raise ValueError('Gemini API key is required')
    if client is None:
        from google import genai
        client=genai.Client(api_key=api_key)
    evidence={key:record.get(key) for key in ('url','title','description','h1','canonical','word_count','content_excerpt','issues')}
    codes=[i['code'] for i in record.get('issues',[])]
    language_instruction = ('Write the summary and action recommendations in Slovenian (sl-SI). ' if language=='sl' else 'Write the summary and action recommendations in English. ')
    prompt=(
        'You are an SEO analyst reviewing a PUBLIC Eurosender webpage. Return ONLY a valid JSON object with keys '
        '"summary" (one or two sentences), "suggested_title" (string), "suggested_meta_description" (string), '
        '"recommendations" (array of objects with "issue_code" and "action"). '
        +language_instruction
        +'Keep the existing and proposed SEO title and meta description in the ORIGINAL language of the webpage. '
        'If the current title or description needs no change, return an empty string for its suggestion. '
        'Use only observed evidence. Do not claim search ranking, traffic, page speed, indexing, conversion, or keyword volume. '
        'Do not invent delivery times, shipping rates, insurance details or services. '
        'Decorative images may appropriately have empty alt attributes; flag for human review, not blanket repair. '
        'Use only these issue codes: '+json.dumps(codes)+'. Evidence:\n'+json.dumps(evidence,ensure_ascii=False)
    )
    response,used_model=generate_with_retries(client,prompt,model,before_attempt=before_attempt)
    raw=(response.text or '').strip()
    if raw.startswith('```'):
        raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw).strip()
    data=json.loads(raw)
    if not isinstance(data,dict):
        raise ValueError('AI response is not a JSON object')
    recommendations=[]
    for item in data.get('recommendations',[]):
        if isinstance(item,dict) and item.get('issue_code') in codes:
            recommendations.append({'issue_code':item['issue_code'],'action':str(item.get('action',''))[:450]})
    title=str(data.get('suggested_title') or '')[:150].strip()
    description=str(data.get('suggested_meta_description') or '')[:250].strip()
    if title.casefold()==str(record.get('title') or '').strip().casefold(): title=''
    if description.casefold()==str(record.get('description') or '').strip().casefold():description=''
    return {'mode':f'Gemini ({used_model})','summary':str(data.get('summary') or '')[:700],
            'suggested_title':title,'suggested_meta_description':description,
            'recommendations':recommendations}
