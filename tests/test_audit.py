import unittest
from unittest.mock import Mock,patch
from audit_engine import validate_url,AuditError,analyze_html,audit_sample,build_rows
from ai_engine import improve_with_ai,generate_with_retries

class AuditTests(unittest.TestCase):
    def test_url_allowlist(self):
        self.assertTrue(validate_url('https://www.eurosender.com/en').startswith('https://'))
        for bad in ['http://www.eurosender.com/','https://eurosender.com.evil.com/','https://localhost/','https://www.eurosender.com@localhost','file:///etc/passwd']:
            with self.subTest(url=bad),self.assertRaises(AuditError): validate_url(bad)
    def test_extraction(self):
        r=audit_sample()[0]
        codes={i['code'] for i in r['issues']}
        self.assertIn('MISSING_DESCRIPTION',codes)
        self.assertIn('MISSING_CANONICAL',codes)
        self.assertIn('MISSING_IMAGE_ALT',codes)
        self.assertIn('TITLE_LENGTH',codes)
        self.assertEqual(r['source'],'SYNTHETIC DEMO — not a real Eurosender page')
    def test_ai_path_with_mock(self):
        rec=audit_sample()[0]
        reply={'summary':'Observed missing description.','suggested_title':'International parcel delivery options and guidance','suggested_meta_description':'Read parcel delivery advice and compare the shipment options that suit your needs.','recommendations':[{'issue_code':'MISSING_DESCRIPTION','action':'Draft a unique description.'},{'issue_code':'FAKE_ISSUE','action':'Do not use.'}]}
        client=Mock()
        client.models.generate_content.return_value.text=__import__('json').dumps(reply)
        ai=improve_with_ai(rec,'',client=client)
        self.assertEqual(len(ai['recommendations']),1)
        self.assertEqual(ai['recommendations'][0]['issue_code'],'MISSING_DESCRIPTION')
        rec['ai']=ai
        self.assertTrue(any(x['Suggested action']=='Draft a unique description.' for x in build_rows([rec])))
    def test_transient_outage_fallback(self):
        client=Mock()
        client.models.generate_content.side_effect=[RuntimeError('503 UNAVAILABLE'),RuntimeError('503 high demand'),Mock(text='{}')]
        response, model=generate_with_retries(client, 'test', sleep=lambda seconds: None)
        self.assertEqual(model,'gemini-3.5-flash-lite')
        self.assertEqual(client.models.generate_content.call_count,3)
    def test_permission_error_no_fallback(self):
        client=Mock()
        client.models.generate_content.side_effect=RuntimeError('403 permission denied')
        with self.assertRaisesRegex(RuntimeError,'403'):
            generate_with_retries(client, 'test', sleep=lambda seconds: None)
        self.assertEqual(client.models.generate_content.call_count,1)
    def test_block_redirect_to_other_host(self):
        from audit_engine import fetch_html
        rsp=Mock()
        rsp.status_code=302
        rsp.headers={'Location':'https://evil.example/path'}
        manager=Mock(); manager.__enter__=Mock(return_value=rsp); manager.__exit__=Mock(return_value=False)
        with patch('audit_engine._public_dns'),patch('audit_engine.requests.Session') as ses:
            ses.return_value.get.return_value=manager
            with self.assertRaises(AuditError): fetch_html('https://www.eurosender.com/en')

if __name__=='__main__': unittest.main()
