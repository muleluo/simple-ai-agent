#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简易 AI 桌面助手 - QML 版本主程序
使用 Qt Quick/QML 实现现代化界面

作者：学习项目
日期：2026-06-25
"""

import sys
from pathlib import Path
from PySide6.QtCore import QUrl, QObject, Signal, Slot, Property, QAbstractListModel, Qt, QModelIndex, QThread
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

# 导入原有的业务逻辑模块
from session_manager import SessionManager
from knowledge_base import KnowledgeBase
import yaml
from datetime import datetime
import json


# ============================================
# 工具函数：网络搜索
# ============================================
def search_web(query: str, max_results: int = 5) -> str:
    """
    使用 DuckDuckGo 搜索网络

    参数：
        query: 搜索关键词
        max_results: 最多返回多少条结果（默认 5 条）

    返回：
        格式化的搜索结果文本
    """
    try:
        from ddgs import DDGS
        import time

        # 重试机制：最多尝试 3 次
        for attempt in range(3):
            try:
                # 使用 DuckDuckGo 搜索
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))

                # 如果没有结果
                if not results:
                    return "未找到相关结果"

                # 格式化结果
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. {result['title']}\n"
                        f"   {result['body']}\n"
                        f"   来源：{result['href']}\n"
                    )

                return "\n".join(formatted_results)

            except Exception as e:
                # 如果是最后一次尝试，返回错误
                if attempt == 2:
                    error_msg = str(e)
                    if "ConnectError" in error_msg or "peer misbehaved" in error_msg or "return None" in error_msg:
                        return "搜索服务暂时不可用，这可能是网络连接问题。请检查网络连接后重试，或稍后再试。"
                    else:
                        return f"搜索失败：{error_msg[:200]}"

                # 否则等待后重试
                time.sleep(1)

    except Exception as e:
        return f"搜索功能出错：{str(e)[:200]}"


# ============================================
# AI 客户端类
# ============================================
class AIClient:
    """
    负责与 AI API 通信的类
    使用 OpenAI 兼容的接口
    """

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-3.5-turbo", temperature: float = 0.7,
                 max_tokens: int = 1000):
        """
        初始化 AI 客户端

        参数：
            api_key: API 密钥
            base_url: API 地址
            model: 模型名称
            temperature: 温度参数（控制随机性）
            max_tokens: 最大回复长度
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 定义可用的工具（Function Calling）
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "set_reminder",
                    "description": "设置一个定时提醒",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "minutes": {
                                "type": "integer",
                                "description": "多少分钟后提醒"
                            },
                            "message": {
                                "type": "string",
                                "description": "提醒的内容"
                            }
                        },
                        "required": ["minutes", "message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "搜索网络获取最新信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "在知识库中搜索相关内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]


# ============================================
# AI 工作线程（支持工具调用）
# ============================================
class ChatWorkerWithTools(QThread):
    """
    支持工具调用的工作线程
    当 AI 调用工具后，执行工具，然后将结果返回给 AI 让其整理
    """

    finished = Signal(dict)

    def __init__(self, ai_client: AIClient, messages: list, tools: list, py_bridge):
        """
        初始化工作线程

        参数：
            ai_client: AI 客户端对象
            messages: 要发送给 API 的消息列表
            tools: 可用的工具列表
            py_bridge: PyBridge 对象（用于调用工具函数）
        """
        super().__init__()
        self.ai_client = ai_client
        self.messages = messages
        self.tools = tools
        self.py_bridge = py_bridge

    def run(self):
        """
        线程的主函数
        处理 AI 调用工具的完整流程：
        1. 调用 AI API
        2. 如果 AI 想调用工具，执行工具
        3. 将工具结果返回给 AI
        4. AI 整理结果后返回给用户
        """
        from openai import OpenAI

        try:
            client = OpenAI(api_key=self.ai_client.api_key, base_url=self.ai_client.base_url)

            # 构建 API 参数
            api_params = {
                "model": self.ai_client.model,
                "messages": self.messages,
                "temperature": self.ai_client.temperature,
                "max_tokens": self.ai_client.max_tokens
            }

            # 只有在有工具时才传 tools 参数
            if self.tools:
                api_params["tools"] = self.tools

            # 第一次调用 AI
            response = client.chat.completions.create(**api_params, timeout=60.0)
            message = response.choices[0].message

            # 检查是否被截断
            finish_reason = response.choices[0].finish_reason
            was_truncated = finish_reason == "length"

            # 如果 AI 没有调用工具，直接返回
            if not message.tool_calls:
                return self.finished.emit({
                    "content": message.content or "",
                    "tool_calls": [],
                    "truncated": was_truncated
                })

            # AI 调用了工具！执行工具并获取结果
            tool_results = []
            pending_reminders = []  # 待处理的提醒（需要在主线程设置）

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # 执行工具
                if tool_name == "set_reminder":
                    # 提醒工具需要在主线程处理（因为需要创建 QTimer）
                    minutes = tool_args.get("minutes", 1)
                    message_text = tool_args.get("message", "")
                    pending_reminders.append({"minutes": minutes, "message": message_text})
                    # 告诉 AI 提醒已设置
                    result = f"已设置 {minutes} 分钟后的提醒：{message_text}"
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": result
                    })
                elif tool_name == "web_search":
                    result = search_web(tool_args.get("query", ""))
                    # 在主线程显示搜索提示（通过特殊标记）
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": result,
                        "query": tool_args.get("query", "")  # 传递查询词用于显示
                    })
                elif tool_name == "search_knowledge_base":
                    results = self.py_bridge.knowledge_base.search(tool_args.get("query", ""), n_results=3)
                    if results:
                        formatted_results = []
                        for i, r in enumerate(results, 1):
                            formatted_results.append(f"{i}. 来自《{r['filename']}》\n   {r['text']}\n")
                        result = "\n".join(formatted_results)
                    else:
                        result = "知识库中未找到相关内容"
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": result
                    })

            # 将工具结果返回给 AI，让 AI 整理
            # 添加 assistant 消息（包含工具调用）
            self.messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # 添加工具结果（使用 tool role）
            for tool_result in tool_results:
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "content": tool_result["content"]
                })

            # 再次调用 AI，让它整理结果（不传 tools 参数）
            api_params_without_tools = {
                "model": self.ai_client.model,
                "messages": self.messages,
                "temperature": self.ai_client.temperature,
                "max_tokens": self.ai_client.max_tokens
            }
            response2 = client.chat.completions.create(**api_params_without_tools, timeout=60.0)
            final_message = response2.choices[0].message
            final_finish_reason = response2.choices[0].finish_reason
            final_truncated = final_finish_reason == "length"

            # 返回 AI 整理后的结果
            self.finished.emit({
                "content": final_message.content or "",
                "tool_calls": [],
                "truncated": final_truncated,
                "pending_reminders": pending_reminders,  # 传递待处理的提醒
                "search_queries": [tr.get("query") for tr in tool_results if tr.get("query")]  # 传递搜索查询
            })

        except Exception as e:
            self.finished.emit({
                "content": f"❌ API 调用失败：{repr(e)}",
                "tool_calls": [],
                "truncated": False,
                "pending_reminders": [],
                "search_queries": []
            })


# ============================================
# QML 数据模型：会话列表
# ============================================
class SessionListModel(QAbstractListModel):
    """
    会话列表数据模型
    提供给 QML ListView 使用
    """

    TitleRole = Qt.UserRole + 1
    TimestampRole = Qt.UserRole + 2
    SessionIdRole = Qt.UserRole + 3
    IsSelectedRole = Qt.UserRole + 4

    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.sessions = []
        self.current_session_id = None  # 启动时不选中任何会话
        self.load_sessions()

    def roleNames(self):
        """定义角色名称映射"""
        return {
            self.TitleRole: b"title",
            self.TimestampRole: b"timestamp",
            self.SessionIdRole: b"sessionId",
            self.IsSelectedRole: b"isSelected"
        }

    def rowCount(self, parent=QModelIndex()):
        """返回行数"""
        return len(self.sessions)

    def data(self, index, role):
        """获取指定索引的数据"""
        if not index.isValid() or index.row() >= len(self.sessions):
            return None

        session = self.sessions[index.row()]

        if role == self.TitleRole:
            return session["title"]
        elif role == self.TimestampRole:
            # 格式化时间戳
            try:
                dt = datetime.fromisoformat(session["updated_at"])
                return dt.strftime("%m-%d %H:%M")
            except:
                return ""
        elif role == self.SessionIdRole:
            return session["session_id"]
        elif role == self.IsSelectedRole:
            return session["session_id"] == self.current_session_id

        return None

    def load_sessions(self):
        """从 SessionManager 加载会话列表"""
        self.beginResetModel()
        self.sessions = self.session_manager.get_all_sessions()
        # 不自动设置 current_session_id，保持为 None
        # self.current_session_id = self.session_manager.current_session_id
        self.endResetModel()

    def refresh(self):
        """刷新列表"""
        self.load_sessions()


# ============================================
# QML 数据模型：消息列表
# ============================================
class MessageListModel(QAbstractListModel):
    """
    消息列表数据模型
    提供给 QML ListView 使用
    """

    SenderRole = Qt.UserRole + 1
    ContentRole = Qt.UserRole + 2
    TimestampRole = Qt.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []

    def roleNames(self):
        """定义角色名称映射"""
        return {
            self.SenderRole: b"sender",
            self.ContentRole: b"content",
            self.TimestampRole: b"timestamp"
        }

    def rowCount(self, parent=QModelIndex()):
        """返回行数"""
        return len(self.messages)

    def data(self, index, role):
        """获取指定索引的数据"""
        if not index.isValid() or index.row() >= len(self.messages):
            return None

        message = self.messages[index.row()]

        if role == self.SenderRole:
            return message["sender"]
        elif role == self.ContentRole:
            return message["content"]
        elif role == self.TimestampRole:
            return message["timestamp"]

        return None

    def add_message(self, sender, content):
        """添加新消息"""
        timestamp = datetime.now().strftime("%H:%M")

        self.beginInsertRows(QModelIndex(), len(self.messages), len(self.messages))
        self.messages.append({
            "sender": sender,
            "content": content,
            "timestamp": timestamp
        })
        self.endInsertRows()

    def clear_messages(self):
        """清空所有消息"""
        self.beginResetModel()
        self.messages = []
        self.endResetModel()

    def load_messages(self, messages):
        """从会话加载消息列表"""
        self.beginResetModel()
        self.messages = []
        for msg in messages:
            try:
                dt = datetime.fromisoformat(msg["timestamp"])
                timestamp = dt.strftime("%H:%M")
            except:
                timestamp = ""

            self.messages.append({
                "sender": msg["role"],
                "content": msg["content"],
                "timestamp": timestamp
            })
        self.endResetModel()


# ============================================
# Python 与 QML 桥接类
# ============================================
class PyBridge(QObject):
    """
    Python 与 QML 的桥接对象
    将 Python 业务逻辑暴露给 QML
    """

    # 信号定义
    sessionListChanged = Signal()
    messageAdded = Signal(str, str)  # sender, content
    webSearchEnabledChanged = Signal(bool)

    def __init__(self, session_list_model, message_list_model):
        super().__init__()

        # 数据模型
        self.session_list_model = session_list_model
        self.message_list_model = message_list_model

        # 业务逻辑管理器
        self.session_manager = session_list_model.session_manager
        self.knowledge_base = KnowledgeBase("data/knowledge_base")

        # 加载配置
        self.config = self.load_config()

        # 初始化 AI 客户端
        api_config = self.config.get("api", {})
        self.ai_client = AIClient(
            api_key=api_config.get("api_key", "your-api-key-here"),
            base_url=api_config.get("base_url", "https://api.openai.com/v1"),
            model=api_config.get("model", "gpt-3.5-turbo"),
            temperature=api_config.get("temperature", 0.7),
            max_tokens=api_config.get("max_tokens", 1000)
        )

        # 系统提示词
        system_prompt_text = self.config.get(
            "system_prompt",
            "你是一个友好的 AI 助手，用简洁友好的语言回答用户的问题。"
        )
        self.system_prompt = {
            "role": "system",
            "content": system_prompt_text
        }

        # 工作线程
        self.worker = None

        # 状态
        self._web_search_enabled = False
        self.temp_session = True  # 临时会话标记

    def load_config(self):
        """加载配置文件"""
        try:
            with open("config.yaml", 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except:
            return {}

    # ============================================
    # QML 可调用的方法（使用 @Slot 装饰器）
    # ============================================

    @Slot()
    def createNewChat(self):
        """创建新对话"""
        print("创建新对话")
        self.message_list_model.clear_messages()
        self.temp_session = True
        self.message_list_model.add_message("system", "已创建新对话")

    @Slot(str)
    def switchSession(self, session_id):
        """切换会话"""
        print(f"切换会话: {session_id}")
        self.temp_session = False
        self.session_manager.switch_session(session_id)

        # 加载会话消息
        current_session = self.session_manager.get_current_session()
        self.message_list_model.load_messages(current_session.messages)

        # 刷新会话列表（更新选中状态）
        self.session_list_model.refresh()

    @Slot(str)
    def sendMessage(self, message):
        """发送消息"""
        print(f"发送消息: {message}")

        # 如果是临时会话，创建真实会话
        if self.temp_session:
            session_id = self.session_manager.create_new_session()
            current_session = self.session_manager.get_current_session()

            # 使用用户消息的前15个字作为标题
            title = message[:15] if len(message) <= 15 else message[:15] + "..."
            self.session_manager.update_session_title(current_session.session_id, title)

            self.temp_session = False
            self.session_list_model.refresh()

        # 显示用户消息
        self.message_list_model.add_message("user", message)

        # 保存到会话
        current_session = self.session_manager.get_current_session()
        current_session.add_message("user", message)
        self.session_manager.save_all_sessions()

        # 准备发送给 AI 的消息列表
        messages = [self.system_prompt]

        # 添加会话历史（最近10条）
        history_messages = current_session.messages[-20:]  # 取最近20条
        for msg in history_messages:
            if msg.get("role") in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # 决定是否启用工具
        tools = self.ai_client.tools if self._web_search_enabled else []

        # 创建工作线程并启动
        self.worker = ChatWorkerWithTools(self.ai_client, messages, tools, self)
        self.worker.finished.connect(self.on_ai_reply)
        self.worker.start()

        # 显示"正在输入"提示
        self.message_list_model.add_message("system", "AI 正在思考...")

    def on_ai_reply(self, reply_data: dict):
        """
        处理 AI 回复

        参数：
            reply_data: 包含 content, pending_reminders, search_queries 等的字典
        """
        # 移除"正在思考"提示
        if self.message_list_model.messages and self.message_list_model.messages[-1]["sender"] == "system":
            self.message_list_model.beginRemoveRows(QModelIndex(), len(self.message_list_model.messages) - 1, len(self.message_list_model.messages) - 1)
            self.message_list_model.messages.pop()
            self.message_list_model.endRemoveRows()

        # 显示搜索提示
        search_queries = reply_data.get("search_queries", [])
        if search_queries:
            for query in search_queries:
                self.message_list_model.add_message("system", f"🔍 正在搜索：{query}")

        # 显示 AI 回复
        content = reply_data.get("content", "")
        if content:
            self.message_list_model.add_message("assistant", content)

            # 保存到会话
            current_session = self.session_manager.get_current_session()
            current_session.add_message("assistant", content)
            self.session_manager.save_all_sessions()

        # 处理提醒
        pending_reminders = reply_data.get("pending_reminders", [])
        for reminder in pending_reminders:
            minutes = reminder["minutes"]
            message_text = reminder["message"]
            self.message_list_model.add_message("system", f"⏰ 已设置 {minutes} 分钟后的提醒")
            # TODO: 实际创建 QTimer 提醒（需要提醒管理器）

        # 显示截断警告
        if reply_data.get("truncated", False):
            self.message_list_model.add_message("system", "⚠️ AI 回复被截断（超出长度限制）")

    @Slot()
    def attachFile(self):
        """附加文件"""
        print("附加文件")
        # TODO: 实现文件选择对话框
        self.message_list_model.add_message("system", "文件附加功能开发中")

    @Slot()
    def showReminderDialog(self):
        """显示提醒对话框"""
        print("显示提醒对话框")
        # TODO: 实现提醒对话框
        self.message_list_model.add_message("system", "提醒功能开发中")

    @Slot()
    def clearCurrentChat(self):
        """清空当前对话"""
        print("清空当前对话")
        current_session = self.session_manager.get_current_session()
        current_session.messages = []
        current_session.updated_at = datetime.now().isoformat()
        self.session_manager.save_all_sessions()

        self.message_list_model.clear_messages()
        self.message_list_model.add_message("system", "已清空当前对话")

    @Slot(str)
    def renameSession(self, session_id):
        """重命名会话"""
        print(f"重命名会话: {session_id}")
        # TODO: 实现重命名对话框
        self.message_list_model.add_message("system", "重命名功能开发中")

    @Slot(str)
    def deleteSession(self, session_id):
        """删除会话"""
        print(f"删除会话: {session_id}")
        self.session_manager.delete_session(session_id)
        self.session_list_model.refresh()

        # 加载新的当前会话
        current_session = self.session_manager.get_current_session()
        self.message_list_model.load_messages(current_session.messages)

    @Slot()
    def uploadToKnowledgeBase(self):
        """上传到知识库"""
        print("上传到知识库")
        # TODO: 实现文件选择和上传
        self.message_list_model.add_message("system", "知识库上传功能开发中")

    @Slot()
    def toggleWebSearch(self):
        """切换联网搜索"""
        self._web_search_enabled = not self._web_search_enabled
        print(f"联网搜索: {self._web_search_enabled}")

        status = "已启用" if self._web_search_enabled else "已禁用"
        self.message_list_model.add_message("system", f"{status}联网搜索")

        self.webSearchEnabledChanged.emit(self._web_search_enabled)

    # Property: webSearchEnabled
    def get_web_search_enabled(self):
        return self._web_search_enabled

    webSearchEnabled = Property(bool, get_web_search_enabled, notify=webSearchEnabledChanged)


# ============================================
# 主程序入口
# ============================================
def main():
    """
    主程序入口
    """
    # 0. 设置 QML 样式为 Basic（支持自定义）
    import os
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

    # 1. 创建应用程序
    app = QGuiApplication(sys.argv)
    app.setApplicationName("AI 桌面助手")
    app.setOrganizationName("学习项目")

    # 2. 创建 QML 引擎
    engine = QQmlApplicationEngine()

    # 3. 初始化业务逻辑
    session_manager = SessionManager("data/sessions")

    # 4. 创建数据模型
    session_list_model = SessionListModel(session_manager)
    message_list_model = MessageListModel()

    # 5. 创建桥接对象
    py_bridge = PyBridge(session_list_model, message_list_model)

    # 6. 将 Python 对象暴露给 QML
    engine.rootContext().setContextProperty("pyBridge", py_bridge)
    engine.rootContext().setContextProperty("sessionListModel", session_list_model)
    engine.rootContext().setContextProperty("messageListModel", message_list_model)

    # 7. 加载 QML 文件
    qml_file = Path(__file__).parent / "qml" / "MainWindow.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    # 8. 检查加载是否成功
    if not engine.rootObjects():
        print("❌ 加载 QML 文件失败")
        return -1

    print("✅ QML 界面加载成功")

    # 9. 启动应用程序
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
