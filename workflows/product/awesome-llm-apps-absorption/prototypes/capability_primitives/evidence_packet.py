from __future__ import annotations
import hashlib, json
from dataclasses import asdict, dataclass
from typing import Any
from primitives import LocalEvidenceRetriever

@dataclass(frozen=True)
class EvidenceItem:
    source_id:str; chunk_id:str; text:str; score:float

@dataclass(frozen=True)
class EvidencePacket:
    query:str; items:tuple[EvidenceItem,...]; digest:str
    @classmethod
    def retrieve(cls,retriever:LocalEvidenceRetriever,query:str,limit:int=5,min_score:float=0.0)->"EvidencePacket":
        hits=retriever.search(query,limit=limit,min_score=min_score)
        items=tuple(EvidenceItem(h['source_id'],h['chunk_id'],h['text'],h['score']) for h in hits)
        canonical=json.dumps({'query':query,'items':[asdict(i) for i in items]},sort_keys=True,separators=(",",":"),ensure_ascii=False)
        return cls(query,items,hashlib.sha256(canonical.encode()).hexdigest())

class GroundedAnswerBoundary:
    """Consumes one packet for both answer context and citation rendering; never re-retrieves."""
    def prepare(self,packet:EvidencePacket)->dict[str,Any]:
        if not packet.items:
            return {'status':'insufficient_evidence','answer_context':(), 'citations':(), 'evidence_digest':packet.digest}
        context=tuple(item.text for item in packet.items)
        citations=tuple({'source_id':item.source_id,'chunk_id':item.chunk_id,'score':item.score} for item in packet.items)
        return {'status':'ready','answer_context':context,'citations':citations,'evidence_digest':packet.digest}
