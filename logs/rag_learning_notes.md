# RAG 知识库功能 - 学习笔记

**日期**：2026-06-21  
**主题**：RAG（检索增强生成）  
**状态**：✅ 已完成

---

## 🎯 什么是 RAG？

**RAG = Retrieval-Augmented Generation**
- **Retrieval**：检索（从知识库中搜索）
- **Augmented**：增强（用检索的内容增强 AI）
- **Generation**：生成（AI 生成回答）

**简单理解**：
让 AI 能够基于你给它的文档来回答问题，而不是只靠训练数据。

---

## 🔍 为什么需要 RAG？

### AI 的局限

```
用户：我们公司的请假政策是什么？
普通 AI：我不知道你们公司的具体政策

用户：Python 教程第 5 章讲了什么？
普通 AI：我没有你的教程内容
```

### RAG 的优势

```
用户：上传 员工手册.pdf
用户：我们公司的请假政策是什么？
RAG AI：📚 搜索知识库...
RAG AI：根据员工手册，年假 10 天，病假 5 天...
```

---

## 📊 RAG 工作流程

### 完整流程图

```
第 1 步：建立知识库
┌──────────────────────┐
│  上传文档             │
│  Python教程.txt       │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  文本切片             │
│  500 字/块            │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  向量化 (Embedding)   │
│  文本 → 数字向量       │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  存储到向量数据库      │
│  Chroma               │
└──────────────────────┘

第 2 步：回答问题
┌──────────────────────┐
│  用户提问             │
│  "Python如何定义函数？"│
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  问题向量化           │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  相似度搜索           │
│  找最相关的 3 个块     │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  返回结果             │
│  "使用 def 关键字..." │
└──────────────────────┘
```

---

## 💡 核心概念

### 1. Embedding（文本嵌入）

**是什么？**
把文本转换成数字向量。

**例子**：
```python
文本：   "Python 是一种编程语言"
向量：   [0.23, 0.56, 0.78, -0.12, 0.45, ...]
       ↑ 384 个数字（维度）
```

**为什么需要？**
- 计算机不懂文字，只懂数字
- 相似的文本 → 相似的向量
- 可以用数学方法计算"距离"

**类比**：
就像把每个人的特征（身高、体重、年龄...）转成一组数字，然后可以计算两个人的相似度。

---

### 2. 向量相似度

**原理**：
两个向量越接近，文本越相似。

**计算方法**：
余弦相似度（Cosine Similarity）

```
向量 A: [1, 2, 3]
向量 B: [1, 2, 2]  ← 和 A 很接近
向量 C: [5, 1, 0]  ← 和 A 差很多

相似度(A, B) = 0.98  ← 很相似！
相似度(A, C) = 0.32  ← 不相似
```

**实际例子**：
```
问题："Python 如何定义函数？"
向量 Q: [0.3, 0.6, 0.7, ...]

知识库：
文档 1: "使用 def 关键字定义函数"
向量 D1: [0.32, 0.58, 0.69, ...]
相似度 = 0.95 ✅ 很相关！

文档 2: "Python 的历史和发展"
向量 D2: [0.1, 0.2, 0.3, ...]
相似度 = 0.3 ❌ 不相关
```

---

### 3. 文本切片（Chunking）

**为什么需要切片？**
```
整本书：10 万字 ❌ 太大
    ↓ 切片
每块：500 字 ✅ 合适
```

**切片策略**：

**方式 1：固定长度**
```python
# 每 500 字切一块
for i in range(0, len(text), 500):
    chunk = text[i:i+500]
```

**方式 2：按段落**（更好）
```python
# 按段落分割，每块不超过 500 字
paragraphs = text.split('\n\n')
current_chunk = ""

for para in paragraphs:
    if len(current_chunk) + len(para) < 500:
        current_chunk += para
    else:
        chunks.append(current_chunk)
        current_chunk = para
```

**块大小选择**：
- 太小（100 字）：上下文不够
- 太大（2000 字）：不精确，包含太多无关内容
- 合适（500-1000 字）：平衡精确度和上下文

---

### 4. 向量数据库

**是什么？**
专门存储和搜索向量的数据库。

**普通数据库 vs 向量数据库**：

```
普通数据库（MySQL）：
查询："找 age = 20 的用户"
匹配方式：精确匹配

向量数据库（Chroma）：
查询："找和这个问题最相似的文档"
匹配方式：相似度搜索
```

**Chroma 的特点**：
- 免费开源
- 本地存储
- 自动 Embedding
- 简单易用

---

## 🔧 技术实现

### 1. 安装依赖

```bash
pip install chromadb sentence-transformers
```

---

### 2. 创建知识库

```python
import chromadb

# 创建客户端
client = chromadb.PersistentClient(path="data/kb")

# 创建集合
collection = client.get_or_create_collection("documents")
```

---

### 3. 添加文档

```python
# 读取文档
with open("Python教程.txt", 'r') as f:
    text = f.read()

# 切片
chunks = chunk_text(text, chunk_size=500)

# 添加到 Chroma（自动 Embedding）
collection.add(
    documents=chunks,
    ids=["doc1_chunk0", "doc1_chunk1", ...],
    metadatas=[
        {"filename": "Python教程.txt", "chunk_index": 0},
        {"filename": "Python教程.txt", "chunk_index": 1},
        ...
    ]
)
```

---

### 4. 搜索

```python
# 搜索（自动 Embedding 问题）
results = collection.query(
    query_texts=["Python 如何定义函数？"],
    n_results=3  # 返回最相似的 3 个
)

# 结果
for doc in results['documents'][0]:
    print(doc)
```

---

## 📚 关键代码

### 完整的 KnowledgeBase 类

```python
import chromadb
from pathlib import Path
from datetime import datetime

class KnowledgeBase:
    def __init__(self, persist_directory):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # 创建客户端
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )
        
        # 创建集合
        self.collection = self.client.get_or_create_collection("documents")
    
    def add_document(self, text: str, filename: str):
        # 切片
        chunks = self._chunk_text(text, chunk_size=500)
        
        # 生成 ID
        doc_id = str(int(datetime.now().timestamp() * 1000))
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        
        # 元数据
        metadatas = [
            {
                "filename": filename,
                "chunk_index": i,
                "doc_id": doc_id
            }
            for i in range(len(chunks))
        ]
        
        # 添加
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
        
        return {"doc_id": doc_id, "chunks": len(chunks)}
    
    def search(self, query: str, n_results: int = 3):
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # 格式化
        formatted = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                formatted.append({
                    "text": doc,
                    "filename": metadata.get("filename"),
                    "chunk_index": metadata.get("chunk_index")
                })
        
        return formatted
    
    def _chunk_text(self, text: str, chunk_size: int = 500):
        # 按段落分割
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # 如果段落本身太长，强制切分
                if len(para) > chunk_size:
                    for i in range(0, len(para), chunk_size):
                        chunks.append(para[i:i+chunk_size])
                    current_chunk = ""
                else:
                    current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
```

---

## 🧪 实际例子

### 例子 1：添加文档

```python
kb = KnowledgeBase("data/kb")

text = """
Python 是一种编程语言。
使用 def 关键字定义函数。
Python 支持面向对象编程。
"""

result = kb.add_document(text, "Python教程.txt")
print(result)
# 输出：{'doc_id': '1781977686002', 'chunks': 1}
```

---

### 例子 2：搜索

```python
results = kb.search("Python 如何定义函数？")

for r in results:
    print(f"文件：{r['filename']}")
    print(f"内容：{r['text']}")
    print("---")

# 输出：
# 文件：Python教程.txt
# 内容：使用 def 关键字定义函数。
```

---

## 🎯 RAG vs 其他方案

### 方案对比

| 方案 | 优点 | 缺点 | 使用场景 |
|------|------|------|----------|
| **Fine-tuning** | 深度定制 | 成本高，更新慢 | 固定领域 |
| **RAG** | 灵活，易更新 | 依赖检索质量 | 知识问答 |
| **Prompt** | 简单快速 | 受限于上下文 | 小量数据 |

---

### 何时用 RAG？

✅ **适合 RAG**：
- 知识库经常更新
- 文档量大（超过上下文限制）
- 需要引用来源
- 私有数据（不能 fine-tune）

❌ **不适合 RAG**：
- 需要深度理解和推理
- 数据量很小（直接放 prompt）
- 实时性要求极高

---

## 💡 优化技巧

### 1. 改进切片质量

```python
# 方法 1：按标题切片
chunks = split_by_headers(text)

# 方法 2：重叠切片
chunks = create_overlapping_chunks(text, size=500, overlap=50)
```

---

### 2. 混合搜索

```python
# 关键词搜索 + 向量搜索
keyword_results = keyword_search(query)
vector_results = vector_search(query)
final_results = combine(keyword_results, vector_results)
```

---

### 3. 重排序（Reranking）

```python
# 第一步：粗排（返回 20 个）
candidates = collection.query(query, n_results=20)

# 第二步：精排（用更好的模型重新排序）
reranked = reranker.rank(query, candidates)

# 第三步：取 top 3
final_results = reranked[:3]
```

---

### 4. 上下文压缩

```python
# 只提取相关句子，而不是整个文档块
relevant_sentences = extract_relevant_sentences(chunks, query)
```

---

## 🐛 常见问题

### Q1：搜索结果不准确？

**原因**：
- 切片太大或太小
- 问题描述不清晰
- Embedding 模型不适合

**解决**：
- 调整 chunk_size
- 增加 n_results
- 尝试其他模型

---

### Q2：中文效果差？

**解决**：
使用中文模型
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    'paraphrase-multilingual-MiniLM-L12-v2'
)
```

---

### Q3：速度慢？

**优化**：
- 减少文档数量
- 使用更小的模型
- 增加索引
- GPU 加速

---

## 🚀 进阶方向

### 1. 多模态 RAG
支持图片、表格、PDF

### 2. 混合检索
关键词 + 向量

### 3. Agent + RAG
AI 自动决定何时查询知识库

### 4. 知识图谱
文档之间的关系

---

## 📖 相关资源

- **Chroma 文档**：https://docs.trychroma.com/
- **Sentence Transformers**：https://www.sbert.net/
- **RAG 论文**：Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

---

## ✅ 学习总结

### 核心理解

1. **RAG = 检索 + 生成**
2. **Embedding 把文本变成向量**
3. **相似度搜索找相关文档**
4. **切片是关键步骤**

### 实践能力

- ✅ 能创建向量数据库
- ✅ 能实现文本切片
- ✅ 能进行相似度搜索
- ✅ 能集成到 AI 系统

---

**学习时间**：2 小时  
**难度**：⭐⭐⭐⭐（中高）  
**收获**：理解了 RAG 的完整工作原理

**下一步**：优化搜索质量，支持更多文件格式
