# -*- coding: utf-8 -*-
"""
会话管理器 - 管理多个对话会话
每个会话有独立的历史记录和标题
"""

import json
from pathlib import Path
from datetime import datetime
from openai import OpenAI


class Session:
    """
    单个对话会话
    """
    def __init__(self, session_id: str, title: str = "新对话", messages: list = None):
        """
        初始化会话

        参数：
            session_id: 会话唯一 ID
            title: 会话标题
            messages: 消息列表
        """
        self.session_id = session_id
        self.title = title
        self.messages = messages or []
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def add_message(self, role: str, content: str):
        """添加消息"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()

    def get_messages_for_api(self) -> list:
        """获取适合发送给 API 的消息格式（去掉时间戳）"""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]

    def to_dict(self) -> dict:
        """转换为字典（用于保存）"""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "messages": self.messages,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_dict(data: dict):
        """从字典创建会话对象"""
        session = Session(
            session_id=data["session_id"],
            title=data.get("title", "新对话"),
            messages=data.get("messages", [])
        )
        session.created_at = data.get("created_at", datetime.now().isoformat())
        session.updated_at = data.get("updated_at", datetime.now().isoformat())
        return session


class SessionManager:
    """
    会话管理器 - 管理所有对话会话
    """
    def __init__(self, storage_dir: str = "data/sessions"):
        """
        初始化会话管理器

        参数：
            storage_dir: 会话存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.sessions = {}  # {session_id: Session}
        self.current_session_id = None

        # 加载所有会话
        self.load_all_sessions()

        # 不自动创建新会话，由界面控制
        # 如果没有会话，current_session_id 保持为 None

    def load_all_sessions(self):
        """加载所有会话"""
        index_file = self.storage_dir / "index.json"

        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 加载每个会话
                    for session_data in data.get("sessions", []):
                        session = Session.from_dict(session_data)
                        self.sessions[session.session_id] = session

                    # 设置当前会话
                    self.current_session_id = data.get("current_session_id")

                    # 如果当前会话不存在，选择第一个
                    if self.current_session_id not in self.sessions and self.sessions:
                        self.current_session_id = list(self.sessions.keys())[0]

            except Exception as e:
                print(f"加载会话失败：{e}")

    def save_all_sessions(self):
        """保存所有会话到索引文件"""
        index_file = self.storage_dir / "index.json"

        data = {
            "current_session_id": self.current_session_id,
            "sessions": [session.to_dict() for session in self.sessions.values()]
        }

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_new_session(self) -> str:
        """
        创建新会话

        返回：
            新会话的 ID
        """
        # 生成新 ID（使用时间戳）
        session_id = f"session_{int(datetime.now().timestamp() * 1000)}"

        # 创建新会话
        session = Session(session_id=session_id, title="新对话")
        self.sessions[session_id] = session

        # 设置为当前会话
        self.current_session_id = session_id

        # 保存
        self.save_all_sessions()

        return session_id

    def get_current_session(self) -> Session:
        """获取当前会话"""
        if self.current_session_id and self.current_session_id in self.sessions:
            return self.sessions[self.current_session_id]

        # 如果没有当前会话，创建一个
        session_id = self.create_new_session()
        return self.sessions[session_id]

    def switch_session(self, session_id: str):
        """切换到指定会话"""
        if session_id in self.sessions:
            self.current_session_id = session_id
            self.save_all_sessions()
            return True
        return False

    def delete_session(self, session_id: str):
        """删除指定会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]

            # 如果删除的是当前会话，切换到其他会话
            if self.current_session_id == session_id:
                if self.sessions:
                    self.current_session_id = list(self.sessions.keys())[0]
                else:
                    # 没有会话了，创建一个新的
                    self.create_new_session()

            self.save_all_sessions()
            return True
        return False

    def update_session_title(self, session_id: str, title: str):
        """更新会话标题"""
        if session_id in self.sessions:
            self.sessions[session_id].title = title
            self.sessions[session_id].updated_at = datetime.now().isoformat()
            self.save_all_sessions()

    def get_all_sessions(self) -> list:
        """
        获取所有会话列表（按更新时间倒序）

        返回：
            [
                {
                    "session_id": "xxx",
                    "title": "xxx",
                    "updated_at": "xxx",
                    "message_count": 10
                },
                ...
            ]
        """
        sessions = []
        for session in self.sessions.values():
            sessions.append({
                "session_id": session.session_id,
                "title": session.title,
                "updated_at": session.updated_at,
                "message_count": len(session.messages),
                "created_at": session.created_at
            })

        # 按更新时间倒序排序
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)

        return sessions

    def generate_title_from_message(self, message: str, api_key: str, base_url: str, model: str) -> str:
        """
        根据用户第一条消息生成会话标题

        参数：
            message: 用户消息
            api_key: API 密钥
            base_url: API 地址
            model: 模型名称

        返回：
            生成的标题
        """
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)

            # 让 AI 生成一个简短的标题
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是标题生成专家。根据用户的问题，提取核心主题词生成4-8字的标题。\n\n规则：\n1. 只返回标题，不要任何解释\n2. 不要标点符号和引号\n3. 提取主题关键词，不要照搬原句\n\n示例：\n- 用户问\"苹果什么品种好吃\" → 标题\"苹果品种推荐\"\n- 用户问\"你好\" → 标题\"日常问候\"\n- 用户问\"机器学习怎么入门\" → 标题\"机器学习入门\""
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                max_tokens=20,
                temperature=0.2,
                timeout=10.0
            )

            title = response.choices[0].message.content.strip()

            # 去掉所有标点符号和引号
            for char in ['"', "'", "《", "》", "：", ":", "。", ".", "、", ",", "，", "?", "？", "!", "！", "\n", "\r"]:
                title = title.replace(char, "")

            # 如果标题太短或太长，使用备用方案
            if len(title) <= 2 or len(title) > 20:
                title = self._extract_keywords(message)

            # 如果标题和原消息完全相同（AI 只是复述），提取关键词
            if title == message[:len(title)]:
                title = self._extract_keywords(message)

            return title or "新对话"

        except Exception as e:
            print(f"生成标题失败：{e}")
            return self._extract_keywords(message)

    def _extract_keywords(self, message: str) -> str:
        """
        从消息中提取关键词作为标题（备用方案）

        参数：
            message: 用户消息

        返回：
            提取的关键词标题
        """
        # 清理常见的语气词和疑问词
        clean_msg = message

        # 移除常见语气词
        for word in ["请问", "想问", "能不能", "可以", "帮我", "一下", "吗", "呢", "啊", "吧"]:
            clean_msg = clean_msg.replace(word, "")

        # 移除标点符号
        for char in ["？", "?", "。", ".", "！", "!", "，", ",", "、"]:
            clean_msg = clean_msg.replace(char, "")

        clean_msg = clean_msg.strip()

        # 特殊处理简短问候
        greetings = ["你好", "您好", "hi", "hello", "嗨"]
        if clean_msg.lower() in greetings or len(clean_msg) <= 3:
            return "日常问候"

        # 返回前10个字
        return clean_msg[:10] if len(clean_msg) <= 10 else clean_msg[:10] + "..."
