# Chinese Text Tokenization Pitfalls in Python

## The Problem

Chinese text has NO word boundaries (no spaces). Naive regex patterns silently produce wrong tokenization, breaking search and vectorization.

## Pitfall 1: Contiguous Chinese as Single Token

```python
import re

text = "测试知识"

# WRONG — matches entire contiguous Chinese string as ONE token
re.findall(r'[\u4e00-\u9fff]+', text)
# → ['测试知识']  (1 token)

# RIGHT — matches individual Chinese characters
re.findall(r'[\u4e00-\u9fff]', text)
# → ['测', '试', '知', '识']  (4 tokens)
```

**When this breaks search**: A keyword search for "测试" won't match the token "测试知识" because substring matching on tokens fails. The query produces `['测', '试']` but the stored token is `['测试知识']` — no overlap.

**When this breaks TF-IDF**: If ALL documents produce single-character tokens via `+` pattern, and the query uses character-level, the vocabulary may be empty or mismatched, causing `empty vocabulary; perhaps the documents only contain stop words`.

## Pitfall 2: TF-IDF Vectorizer with Chinese

scikit-learn's `TfidfVectorizer` defaults to `token_pattern=r"(?u)\b\w\b"` which doesn't handle Chinese well. When using a custom tokenizer:

```python
class ChineseTokenizer:
    def __call__(self, text):
        # English words
        tokens = re.findall(r'[a-zA-Z]+', text.lower())
        # Individual Chinese characters (NOT contiguous groups)
        tokens += re.findall(r'[\u4e00-\u9fff]', text)
        return tokens

vectorizer = TfidfVectorizer(tokenizer=ChineseTokenizer())
```

**Key**: Use character-level (`[\u4e00-\u9fff]`) not group-level (`[\u4e00-\u9fff]+`) for search/vectorization tasks.

## Pitfall 3: Module Cache Masking Fixes

When debugging tokenization in Python, module caching can make it look like your fix didn't work:

```python
# WRONG — old module still in memory
from knowledge_manager import KnowledgeManager

# RIGHT — force reload
import sys
if 'knowledge_manager' in sys.modules:
    del sys.modules['knowledge_manager']
from knowledge_manager import KnowledgeManager
```

## Decision Matrix

| Use Case | Pattern | Rationale |
|----------|---------|-----------|
| Keyword search | `[\u4e00-\u9fff]` (char-level) | Enables substring-like matching |
| TF-IDF vectorization | `[\u4e00-\u9fff]` (char-level) | Builds meaningful vocabulary |
| Named entity extraction | `[\u4e00-\u9fff]+` (group-level) | Preserves multi-char entities |
| Sentence segmentation | `[\u4e00-\u9fff]+` (group-level) | Groups meaningful text chunks |

## Real-World Fix (hermes-edge-worker, 2026-05)

**Symptom**: KnowledgeManager.search_experience("测试") returned 0 results despite storing "测试知识".

**Root cause**: `_extract_keywords` used `re.findall(r'[\u4e00-\u9fff]+', text)` — stored keywords were `['测试知识']` but query keywords were `['测试']`. No match.

**Fix**: Changed to `re.findall(r'[\u4e00-\u9fff]', text)` — both stored and query produce character-level tokens: `['测', '试', '知', '识']` vs `['测', '试']`. Score: 6.0 (matched).

**RAG system also failed**: `ChineseTokenizer` only matched hardcoded vocabulary words. Adding `re.findall(r'[\u4e00-\u9fff]', text)` to the tokenizer fixed `empty vocabulary` errors in TF-IDF.
