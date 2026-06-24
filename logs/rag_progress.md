# RAG 知识库功能 - 开发进度

**日期**：2026-06-20  
**功能**：让 AI 基于上传的文档回答问题  
**状态**：🚧 进行中（70% 完成）

---

## ✅ 已完成

### 1. 依赖安装
```bash
pip install chromadb sentence-transformers
```

**库的作用**：
- `chromadb`：向量数据库（存储和搜索文档）
- `sentence-transformers`：把文本转成向量（Embedding）

---

### 2. 知识库管理器

创建了 `knowledge_base.py`，包含：

**核心功能**：
```python
class KnowledgeBase:
    def add_document(text, filename)    # 添加文档
    def search(query, n_results=3)      # 搜索相关文档
    def list_documents()                # 列出所有文档
    def delete_document(doc_id)         # 删除文档
    def _chunk_text(text, chunk_size)   # 文本切片
```

**已测试通过**：
- ✅ 添加文档
- ✅ 搜索功能
- ✅ 文本切片

---

## 🚧 待完成

### 3. 集成到 AI 助手

需要做：
1. 在 `main.py` 中导入 `KnowledgeBase`
2. 添加 `upload_document` 工具
3. 修改 `web_search` 工具，优先搜索知识库
4. 添加文件上传按钮
5. 添加知识库管理界面

---

### 4. 添加工具定义

```python
{
    "name": "search_knowledge_base",
    "description": "在用户上传的文档中搜索信息",
    "parameters": {
        "query": {
            "type": "string",
            "description": "搜索问题"
        }
    }
}
```

---

### 5. 文件上传功能

添加按钮：
```python
self.upload_button = QPushButton("📄 上传文档")
self.upload_button.clicked.connect(self.upload_document)
```

上传处理：
```python
def upload_document(self):
    # 1. 打开文件选择对话框
    file_path = QFileDialog.getOpenFileName(...)
    
    # 2. 读取文件内容
    with open(file_path, 'r') as f:
        text = f.read()
    
    # 3. 添加到知识库
    result = self.knowledge_base.add_document(text, filename)
    
    # 4. 显示确认
    QMessageBox.information(...)
```

---

## 📚 核心概念

### 1. 文本切片（Chunking）

**为什么需要切片？**
- 长文档太大，AI 无法一次处理
- 切成小块，每块 500-1000 字

**实现**：
```python
def _chunk_text(self, text: str, chunk_size: int = 500):
    paragraphs = text.split('\n\n')  # 按段落分割
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            chunks.append(current_chunk)
            current_chunk = para + "\n\n"
    
    return chunks
```

---

### 2. 向量化（Embedding）

**文本 → 数字向量**：
```
"Python 是一种编程语言" → [0.2, 0.5, 0.8, -0.3, ...]
```

**为什么？**
- 计算机只懂数字
- 相似的文本 → 相似的向量
- 可以计算"距离"

**Chroma 自动处理**：
```python
collection.add(documents=chunks)  # 自动向量化
results = collection.query(query_texts=[query])  # 自动搜索
```

---

### 3. 向量相似度搜索

**原理**：
```
用户问题："Python 是什么？"
    ↓ 向量化
问题向量：[0.3, 0.6, 0.7, ...]
    ↓ 搜索
知识库中最相似的文档：
1. "Python 是一种编程语言" (相似度 0.95)
2. "Python 支持面向对象" (相似度 0.82)
```

---

### 4. 完整 RAG 流程

```
1. 上传文档
   用户：上传 Python教程.txt
   系统：切片 → 向量化 → 存储到 Chroma

2. 提问
   用户：Python 是什么？
   
3. 搜索
   系统：在知识库中找相关文档
   找到："Python 是一种高级编程语言..."
   
4. 生成回答
   系统：把文档给 AI
   AI：根据文档，Python 是一种...
```

---

## 🔧 明天要做的

1. **集成知识库到 main.py**
   - 初始化 KnowledgeBase
   - 添加文件上传按钮
   - 实现上传处理

2. **添加工具**
   - `search_knowledge_base` 工具
   - AI 自动搜索知识库

3. **测试完整流程**
   - 上传文档
   - 提问
   - 验证 AI 回答基于文档

4. **编写完整文档**

---

## 📊 技术栈

- **Chroma**：向量数据库
- **Sentence Transformers**：文本嵌入模型
- **all-MiniLM-L6-v2**：默认嵌入模型（79MB）

---

## 🎓 学到的概念

1. **RAG（检索增强生成）**
2. **Embedding（文本嵌入）**
3. **向量数据库**
4. **文本切片（Chunking）**
5. **向量相似度搜索**

---

**今日进度**：70%  
**明天继续**：集成到 UI + 完整测试

**晚安！🌙**
