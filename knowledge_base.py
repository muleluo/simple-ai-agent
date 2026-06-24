# RAG 知识库管理器

import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime


class KnowledgeBase:
    """
    RAG 知识库管理器

    功能：
    1. 添加文档到知识库
    2. 搜索相关文档
    3. 管理文档
    """

    def __init__(self, persist_directory: str = "data/knowledge_base"):
        """
        初始化知识库

        参数：
            persist_directory: 知识库存储目录
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # 创建 Chroma 客户端
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "用户上传的文档"}
        )

    def add_document(self, text: str, filename: str) -> dict:
        """
        添加文档到知识库

        参数：
            text: 文档内容
            filename: 文件名

        返回：
            添加结果
        """
        # 切片：把长文本切成小块
        chunks = self._chunk_text(text, chunk_size=500)

        # 生成唯一 ID
        doc_id = str(int(datetime.now().timestamp() * 1000))

        # 准备数据
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "filename": filename,
                "chunk_index": i,
                "doc_id": doc_id,
                "created_at": datetime.now().isoformat()
            }
            for i in range(len(chunks))
        ]

        # 添加到 Chroma
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )

        return {
            "doc_id": doc_id,
            "filename": filename,
            "chunks": len(chunks),
            "total_chars": len(text)
        }

    def search(self, query: str, n_results: int = 3) -> list:
        """
        搜索相关文档

        参数：
            query: 搜索问题
            n_results: 返回多少条结果

        返回：
            相关文档列表
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        # 格式化结果
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                formatted_results.append({
                    "text": doc,
                    "filename": metadata.get("filename", "未知"),
                    "chunk_index": metadata.get("chunk_index", 0)
                })

        return formatted_results

    def list_documents(self) -> list:
        """
        列出所有文档

        返回：
            文档列表
        """
        # 获取所有数据
        all_data = self.collection.get()

        # 按文档分组
        docs = {}
        for metadata in all_data['metadatas']:
            doc_id = metadata.get('doc_id')
            if doc_id not in docs:
                docs[doc_id] = {
                    "doc_id": doc_id,
                    "filename": metadata.get('filename'),
                    "created_at": metadata.get('created_at'),
                    "chunks": 1
                }
            else:
                docs[doc_id]['chunks'] += 1

        return list(docs.values())

    def delete_document(self, doc_id: str):
        """
        删除文档

        参数：
            doc_id: 文档 ID
        """
        # 查找所有相关的 chunk
        all_data = self.collection.get()
        ids_to_delete = []

        for i, metadata in enumerate(all_data['metadatas']):
            if metadata.get('doc_id') == doc_id:
                ids_to_delete.append(all_data['ids'][i])

        # 删除
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)

    def _chunk_text(self, text: str, chunk_size: int = 500) -> list:
        """
        把长文本切成小块

        参数：
            text: 原始文本
            chunk_size: 每块的字符数

        返回：
            文本块列表
        """
        # 按段落分割
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            # 如果当前块 + 新段落不超过限制
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # 如果段落本身太长，强制切分
                if len(para) > chunk_size:
                    for i in range(0, len(para), chunk_size):
                        chunks.append(para[i:i+chunk_size])
                    current_chunk = ""
                else:
                    current_chunk = para + "\n\n"

        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
