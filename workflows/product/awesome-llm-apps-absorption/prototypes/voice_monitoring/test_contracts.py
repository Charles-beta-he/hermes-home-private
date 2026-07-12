import unittest
from contracts import MonitorDeduplicator, TranscriptEvent, TranscriptRouter

class VoiceTests(unittest.TestCase):
    def test_empty_transcript_fails_closed(self):
        result=TranscriptRouter().route(TranscriptEvent('s1','   ',True))
        self.assertEqual(result['status'],'blocked'); self.assertFalse(result['append_to_ledger'])
    def test_partial_is_visible_but_not_committed(self):
        result=TranscriptRouter().route(TranscriptEvent('s1','hello',False))
        self.assertEqual(result['status'],'partial'); self.assertFalse(result['append_to_ledger'])
    def test_final_real_text_is_committable(self):
        result=TranscriptRouter().route(TranscriptEvent('s1',' hello  world ',True))
        self.assertEqual(result['text'],'hello world'); self.assertTrue(result['append_to_ledger'])

class MonitorTests(unittest.TestCase):
    def test_duplicate_event_is_suppressed_and_never_dispatches(self):
        d=MonitorDeduplicator(); first=d.evaluate('feed','item'); second=d.evaluate('feed','item')
        self.assertEqual(first['status'],'new'); self.assertEqual(second['status'],'duplicate')
        self.assertFalse(first['should_dispatch']); self.assertFalse(second['should_dispatch'])
    def test_invalid_event_rejected(self):
        with self.assertRaises(ValueError): MonitorDeduplicator().evaluate('','item')

if __name__=='__main__': unittest.main()
