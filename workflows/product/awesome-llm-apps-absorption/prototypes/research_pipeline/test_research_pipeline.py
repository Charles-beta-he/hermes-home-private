import tempfile
import unittest
from pathlib import Path
from research_pipeline import CitationGate, Claim, render_report, write_packet


class CitationGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        (self.root/'README.md').write_text('source')
        self.gate=CitationGate(self.root)
    def tearDown(self): self.tmp.cleanup()

    def test_static_claim_requires_existing_source_and_boundary(self):
        claim=Claim('c1','Source exists',('README.md',),'verified_static',('runtime not tested',))
        verdict=self.gate.validate([claim])
        self.assertEqual(verdict['status'],'PASS')

    def test_missing_source_fails(self):
        claim=Claim('c1','Missing',('missing.md',),'verified_static',('runtime not tested',))
        self.assertEqual(self.gate.validate([claim])['status'],'FAIL')

    def test_static_claim_without_cannot_prove_fails(self):
        claim=Claim('c1','Overclaim',('README.md',),'verified_static')
        self.assertIn('missing_static_boundary:c1',self.gate.validate([claim])['issues'])

    def test_outside_root_and_duplicate_ids_fail(self):
        claims=[Claim('c','x',('../x',),'verified_static',('runtime',)),Claim('c','y',(), 'assumption')]
        verdict=self.gate.validate(claims)
        self.assertEqual(verdict['status'],'FAIL')
        self.assertTrue(any(x.startswith('outside_source_root') for x in verdict['issues']))
        self.assertIn('duplicate_or_empty_id:c',verdict['issues'])

    def test_packet_writes_readable_artifacts(self):
        claim=Claim('c1','Source exists',('README.md',),'verified_static',('runtime not tested',))
        verdict=self.gate.validate([claim]); out=self.root/'out'
        report=render_report('Test',[claim],verdict); write_packet(out,'Test',[claim],verdict,report)
        self.assertIn('Citation gate: **PASS**',(out/'report.md').read_text())
        self.assertTrue((out/'claims.json').is_file())

if __name__=='__main__': unittest.main()
