import unittest
from usage_guard import ApiAttemptLimiter,DemoQuotaReached
from ai_engine import DEFAULT_MODEL

class GuardTests(unittest.TestCase):
    def test_daily_cap(self):
        limit=ApiAttemptLimiter(daily_limit=2,minute_limit=5)
        self.assertEqual(limit.remaining_today(),2)
        limit.consume();limit.consume()
        self.assertEqual(limit.remaining_today(),0)
        with self.assertRaisesRegex(DemoQuotaReached,'DAILY'):
            limit.consume()
    def test_minute_cap(self):
        limit=ApiAttemptLimiter(daily_limit=5,minute_limit=1)
        limit.consume()
        with self.assertRaisesRegex(DemoQuotaReached,'MINUTE'):
            limit.consume()
    def test_flash_lite_primary(self):
        self.assertEqual(DEFAULT_MODEL,'gemini-3.5-flash-lite')

if __name__=='__main__':unittest.main()
