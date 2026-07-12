import unittest
from pathlib import Path
from adapter import OwnedStdioAdapter

SERVER=Path(__file__).with_name('server.py')
class OwnedMcpTests(unittest.TestCase):
    def setUp(self): self.adapter=OwnedStdioAdapter('fixture',SERVER)
    def test_initialize_discover_resources(self):
        self.assertEqual(self.adapter.initialize()['serverInfo']['name'],'owned-readonly-fixture')
        tool=self.adapter.discover()[0]
        self.assertEqual(tool.capability_id,'fixture:read_fixture'); self.assertEqual(tool.side_effect_class,'read_only')
        self.assertEqual(self.adapter.list_resources()[0]['uri'],'fixture://capability-contract')
    def test_exact_allowlist_call_and_receipt(self):
        result=self.adapter.call('fixture:read_fixture',{'fixture_id':'capability-contract'},{'fixture:read_fixture'})
        self.assertFalse(result['result']['structuredContent']['external']); self.assertTrue(result['schema_digest'])
    def test_call_denied_without_exact_capability(self):
        with self.assertRaises(PermissionError): self.adapter.call('fixture:read_fixture',{'fixture_id':'capability-contract'},set())
    def test_unknown_capability_and_fixture_fail(self):
        with self.assertRaises(KeyError): self.adapter.call('fixture:missing',{},set())
        with self.assertRaises(RuntimeError): self.adapter.call('fixture:read_fixture',{'fixture_id':'missing'},{'fixture:read_fixture'})
    def test_namespace_prevents_cross_server_collision(self):
        other=OwnedStdioAdapter('other',SERVER)
        self.assertNotEqual(self.adapter.discover()[0].capability_id,other.discover()[0].capability_id)

if __name__=='__main__': unittest.main()
