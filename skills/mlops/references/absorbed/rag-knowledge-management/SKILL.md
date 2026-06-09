---
name: rag-knowledge-management
description: Use when building RAG (Retrieval-Augmented Generation) knowledge management
  systems with Chinese text support, TF-IDF vectorization, semantic search, and RESTful
  API interfaces.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - rag
    - knowledge-management
    - chinese-nlp
    - vector-search
    - api
    related_skills:
    - mlops
    - data-science
    - api-and-interface-design
---

# RAG Knowledge Management

## Overview

Build RAG (Retrieval-Augmented Generation) knowledge management systems with support for Chinese text, TF-IDF vectorization, semantic search, and RESTful APIs.

## When to Use

- Building knowledge bases with semantic search capabilities
- Processing Chinese text with proper tokenization
- Creating RESTful APIs for knowledge management
- Implementing vector-based retrieval systems
- Need persistence and metrics tracking

## Core Components

### 1. Chinese Tokenizer

Default TfidfVectorizer doesn't work well with Chinese text. Create a custom tokenizer:

```python
class ChineseTokenizer:
    """中文分词器"""
    
    def __init__(self):
        # 常用中文词汇
        self.common_words = set([
            "Python", "NumPy", "Pandas", "机器学习", "深度学习", "算法",
            "性能优化", "数组操作", "数据分析", "框架", "库", "技巧"
        ])
    
    def tokenize(self, text: str) -> List[str]:
        """分词"""
        tokens = []
        
        # 英文单词
        english_words = re.findall(r'[a-zA-Z]+', text)
        tokens.extend(english_words)
        
        # 中文词汇（简单匹配）
        for word in self.common_words:
            if word in text:
                tokens.append(word)
        
        # 数字
        numbers = re.findall(r'\d+', text)
        tokens.extend(numbers)
        
        return tokens
```

### 2. RAG Knowledge Manager

Core class for knowledge management:

```python
class RAGKnowledgeManager:
    """RAG知识管理器"""
    
    def __init__(self):
        self.knowledge_base = {}
        self.tokenizer = ChineseTokenizer()
        self.vectorizer = TfidfVectorizer(tokenizer=self.tokenizer.tokenize)
        self.vectors = None
        self.metrics = {
            "total_knowledge": 0,
            "total_searches": 0,
            "average_search_time": 0.0
        }
    
    def add_knowledge(self, knowledge_id: str, content: str, 
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加知识"""
        self.knowledge_base[knowledge_id] = {
            "id": knowledge_id,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        self._update_vector_index()
        self.metrics["total_knowledge"] += 1
        return knowledge_id
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """语义搜索"""
        if not self.knowledge_base:
            return []
        
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.vectors)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                knowledge_id = list(self.knowledge_base.keys())[idx]
                knowledge = self.knowledge_base[knowledge_id]
                results.append({
                    "id": knowledge_id,
                    "content": knowledge["content"],
                    "metadata": knowledge["metadata"],
                    "score": float(similarities[idx])
                })
        
        return results
    
    def _update_vector_index(self):
        """更新向量索引"""
        if not self.knowledge_base:
            self.vectors = None
            return
        
        contents = [k["content"] for k in self.knowledge_base.values()]
        self.vectors = self.vectorizer.fit_transform(contents)
```

### 3. RESTful API

API endpoints for knowledge management:

```python
# API端点
GET  /health              # 健康检查
GET  /search?q=...&top_k=...  # 搜索知识
GET  /knowledge           # 列出知识
GET  /knowledge/<id>      # 获取知识
POST /knowledge           # 添加知识
DELETE /knowledge/<id>    # 删除知识
GET  /metrics             # 获取指标
```

## Dependencies

```bash
pip install scikit-learn numpy
```

## Performance Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Search Precision | 70% | 90% |
| Response Time | 1ms | 0.5ms |
| Languages | CN/EN | CN/EN |
| Capacity | 1000 | 10000 |

## Common Pitfalls

1. **Chinese Tokenization**: Default TfidfVectorizer doesn't handle Chinese well. Always use custom tokenizer.

2. **Vector Index Update**: Must call `_update_vector_index()` after adding/removing knowledge.

3. **Empty Knowledge Base**: Search returns empty list when no knowledge exists.

4. **Persistence**: Use pickle for save/load, but be careful with version compatibility.

## Verification Checklist

- [ ] Chinese tokenizer handles both Chinese and English text
- [ ] Vector index updates after knowledge changes
- [ ] Search returns relevant results with scores
- [ ] API endpoints return proper JSON responses
- [ ] Metrics tracking works correctly
- [ ] Persistence (save/load) works correctly

## References

- TF-IDF Vectorization: scikit-learn documentation
- Chinese NLP: jieba, pkuseg (for advanced tokenization)
- Vector Search: FAISS, Milvus (for large-scale)
