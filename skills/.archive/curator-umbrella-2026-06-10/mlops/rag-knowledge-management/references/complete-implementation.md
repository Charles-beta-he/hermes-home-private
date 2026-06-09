# Complete RAG Implementation Example

## Files Created

```
~/hermes-edge-worker/
├── rag_knowledge_manager.py    # RAG知识管理器
├── rag_api.py                  # RAG API接口
└── RAG-KNOWLEDGE-MANAGEMENT-ARCHITECTURE.md  # 架构文档
```

## Implementation Details

### rag_knowledge_manager.py

Core implementation with:
- ChineseTokenizer class for Chinese text support
- RAGKnowledgeManager class for knowledge CRUD and search
- TF-IDF vectorization with scikit-learn
- Persistence with pickle

Key features:
- `add_knowledge(id, content, metadata)` - Add knowledge
- `search(query, top_k)` - Semantic search
- `get_knowledge(id)` - Get specific knowledge
- `delete_knowledge(id)` - Delete knowledge
- `save(filepath)` / `load(filepath)` - Persistence
- `get_metrics()` - Performance metrics

### rag_api.py

RESTful API with:
- HTTP server using http.server
- JSON request/response
- All CRUD endpoints
- Error handling

API endpoints:
```
GET  /health              - Health check
GET  /search?q=...&top_k=...  - Search knowledge
GET  /knowledge           - List all knowledge
GET  /knowledge/<id>      - Get specific knowledge
POST /knowledge           - Add knowledge (JSON body)
DELETE /knowledge/<id>    - Delete knowledge
GET  /metrics             - Get performance metrics
```

## Usage Example

```python
from rag_knowledge_manager import RAGKnowledgeManager
from rag_api import RAGAPIServer

# Create manager
manager = RAGKnowledgeManager()

# Add knowledge
manager.add_knowledge("1", "Python性能优化技巧", {"category": "programming"})
manager.add_knowledge("2", "NumPy数组操作指南", {"category": "library"})

# Search
results = manager.search("Python performance")
for result in results:
    print(f"{result['id']}: {result['content']} (score: {result['score']:.3f})")

# Start API server
server = RAGAPIServer("0.0.0.0", 9005, manager)
server.start()
```

## API Usage

```bash
# Search
curl "http://localhost:9005/search?q=Python+performance&top_k=5"

# Add knowledge
curl -X POST "http://localhost:9005/knowledge" \
  -H "Content-Type: application/json" \
  -d '{"id": "3", "content": "机器学习算法", "metadata": {"category": "ml"}}'

# List knowledge
curl "http://localhost:9005/knowledge"

# Get metrics
curl "http://localhost:9005/metrics"
```

## Dependencies

```bash
pip install scikit-learn numpy
```

## Testing

```bash
cd ~/hermes-edge-worker
python3 rag_knowledge_manager.py
```
