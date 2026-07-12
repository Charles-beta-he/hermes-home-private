import dataclasses, unittest
from evidence_packet import EvidencePacket, GroundedAnswerBoundary
from primitives import LocalEvidenceRetriever

class EvidencePacketTests(unittest.TestCase):
    def setUp(self): self.retriever=LocalEvidenceRetriever.from_texts({'a':'RAG citations share retrieval evidence.','b':'Memory has owner isolation.'},100)
    def test_packet_is_immutable_and_digest_deterministic(self):
        first=EvidencePacket.retrieve(self.retriever,'RAG citations'); second=EvidencePacket.retrieve(self.retriever,'RAG citations')
        self.assertEqual(first.digest,second.digest)
        with self.assertRaises(dataclasses.FrozenInstanceError): setattr(first,'query','changed')
    def test_answer_context_and_citations_share_packet(self):
        packet=EvidencePacket.retrieve(self.retriever,'RAG citations'); prepared=GroundedAnswerBoundary().prepare(packet)
        self.assertEqual(prepared['status'],'ready'); self.assertEqual(prepared['evidence_digest'],packet.digest)
        self.assertEqual(len(prepared['answer_context']),len(prepared['citations']))
        self.assertEqual(prepared['citations'][0]['chunk_id'],packet.items[0].chunk_id)
    def test_empty_packet_abstains(self):
        packet=EvidencePacket.retrieve(self.retriever,'unrelated-token'); prepared=GroundedAnswerBoundary().prepare(packet)
        self.assertEqual(prepared['status'],'insufficient_evidence'); self.assertEqual(prepared['citations'],())
    def test_high_threshold_abstains(self):
        packet=EvidencePacket.retrieve(self.retriever,'RAG',min_score=999)
        self.assertEqual(GroundedAnswerBoundary().prepare(packet)['status'],'insufficient_evidence')

if __name__=='__main__': unittest.main()
