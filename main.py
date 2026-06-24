#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简易 AI 桌面助手 - 主程序入口
功能：一个最基础的对话窗口，能和 AI 聊天

作者：学习项目
日期：2026-06-15
"""

import sys
import json
from pathlib import Path
from datetime import datetime

try:
    import yaml  # 用于读取 YAML 配置文件
except ImportError:
    yaml = None  # 如果没安装 yaml，用默认配置

# 导入知识库管理器
from knowledge_base import KnowledgeBase

# 导入会话管理器（新增！）
from session_manager import SessionManager

# PySide6 是 Qt 的 Python 绑定库，用于创建图形界面
from PySide6.QtWidgets import (
    QApplication,      # 应用程序对象
    QWidget,           # 基础窗口控件
    QVBoxLayout,       # 垂直布局管理器
    QHBoxLayout,       # 水平布局管理器
    QTextEdit,         # 多行文本显示框
    QListWidget,       # 列表控件（新增！用于显示会话列表）
    QListWidgetItem,   # 列表项（新增！）
    QSplitter,         # 分割器（新增！用于左右分栏）
    QLineEdit,         # 单行输入框
    QPushButton,       # 按钮
    QLabel,            # 文本标签
    QMessageBox,       # 消息提示框
    QInputDialog,      # 输入对话框
    QFileDialog,       # 文件选择对话框
    QMenu              # 菜单（用于设置下拉菜单）
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont


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
# 配置加载函数
# ============================================
def load_config(config_path: str = "config.yaml") -> dict:
    """
    从 YAML 文件加载配置

    参数：
        config_path: 配置文件路径

    返回：
        配置字典
    """
    # 默认配置（如果配置文件不存在或读取失败）
    default_config = {
        "api": {
            "api_key": "your-api-key-here",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "system_prompt": "你是一个友好的 AI 助手，用简洁友好的语言回答用户的问题。",
        "ui": {
            "window_title": "🤖 简易 AI 桌面助手",
            "window_width": 600,
            "window_height": 700,
            "font_size": 11
        }
    }

    # 如果没安装 yaml 库，返回默认配置
    if yaml is None:
        print("⚠️ 未安装 PyYAML，使用默认配置")
        return default_config

    try:
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"⚠️ 配置文件 {config_path} 不存在，使用默认配置")
            return default_config

        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 合并默认配置（填补缺失的字段）
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in config[key]:
                        config[key][sub_key] = sub_value

        print(f"✅ 成功加载配置：{config_path}")
        return config

    except Exception as e:
        print(f"❌ 配置文件读取失败：{e}")
        return default_config


# ============================================
# 第一部分：AI API 调用类
# ============================================
class AIClient:
    """
    负责与 AI API 通信的类
    这里使用 OpenAI 兼容的接口（可以对接 OpenAI、Claude、本地模型等）
    """

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-3.5-turbo", temperature: float = 0.7,
                 max_tokens: int = 1000):
        """
        初始化 AI 客户端

        参数：
            api_key: API 密钥（从 OpenAI 官网获取）
            base_url: API 地址（默认 OpenAI，也可以改成其他兼容的服务）
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
                    "description": "设置提醒",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "minutes": {
                                "type": "integer",
                                "description": "分钟数"
                            },
                            "message": {
                                "type": "string",
                                "description": "提醒内容"
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
                    "description": "搜索信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "关键词"
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
                    "description": "搜索知识库",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "关键词"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def chat(self, messages: list) -> dict:
        """
        发送对话消息并获取 AI 回复

        参数：
            messages: 对话历史列表，格式如：
                [
                    {"role": "system", "content": "你是一个助手"},
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "你好！有什么可以帮你的吗？"}
                ]

        返回：
            包含回复和工具调用的字典：
            {
                "content": "AI 的文字回复",
                "tool_calls": [...]  # 如果 AI 想调用工具
            }
        """
        try:
            # 这里使用 openai 库来调用 API
            from openai import OpenAI

            # 确保消息内容都是 UTF-8 编码的字符串
            # 这可以避免某些 API 服务的编码问题
            encoded_messages = []
            for msg in messages:
                encoded_msg = {
                    "role": msg["role"],
                    "content": str(msg["content"])  # 确保是字符串类型
                }
                encoded_messages.append(encoded_msg)

            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            # 调用 Chat Completions API
            # 只有在有工具时才传 tools 参数
            api_params = {
                "model": self.model,
                "messages": encoded_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }

            if self.tools:
                api_params["tools"] = self.tools

            # 添加超时设置（60秒）
            response = client.chat.completions.create(**api_params, timeout=60.0)

            # 提取 AI 的回复
            message = response.choices[0].message

            # 检查回复是否因 token 限制被截断
            finish_reason = response.choices[0].finish_reason
            was_truncated = finish_reason == "length"

            # 返回结果
            result = {
                "content": message.content or "",  # 文字回复
                "tool_calls": [],                   # 工具调用
                "truncated": was_truncated          # 是否被截断
            }

            # 如果 AI 想调用工具
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments  # JSON 字符串
                    })

            return result

        except Exception as e:
            # 如果出错，返回错误信息（使用 repr 避免编码问题）
            error_msg = repr(e)
            return {
                "content": f"❌ API 调用失败：{error_msg}",
                "tool_calls": [],
                "truncated": False
            }


# ============================================
# 第二部分：聊天历史管理类
# ============================================
class ChatHistory:
    """
    负责保存和加载聊天记录
    使用 JSON 文件存储，格式简单易读
    """

    def __init__(self, file_path: str):
        """
        初始化聊天历史管理器

        参数：
            file_path: 历史记录保存的文件路径
        """
        self.file_path = Path(file_path)
        self.messages = []  # 对话消息列表

        # 如果文件存在，加载历史记录
        if self.file_path.exists():
            self.load()

    def add_message(self, role: str, content: str):
        """
        添加一条消息到历史记录

        参数：
            role: 角色（"user" 用户 / "assistant" AI助手）
            content: 消息内容
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()  # 记录时间戳
        }
        self.messages.append(message)
        self.save()  # 每次添加消息后自动保存

    def get_messages_for_api(self) -> list:
        """
        获取适合发送给 API 的消息格式
        （去掉时间戳，只保留 role 和 content）

        返回：
            格式化的消息列表
        """
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]

    def save(self):
        """
        保存聊天记录到 JSON 文件
        """
        try:
            # 确保目录存在
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入 JSON 文件（格式化输出，方便人类阅读）
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存聊天记录失败：{e}")

    def load(self):
        """
        从 JSON 文件加载聊天记录
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.messages = json.load(f)
        except Exception as e:
            print(f"加载聊天记录失败：{e}")
            self.messages = []

    def clear(self):
        """
        清空聊天记录
        """
        self.messages = []
        self.save()


# ============================================
# 第二部分之二：提醒管理类
# ============================================
class ReminderManager:
    """
    负责保存和加载提醒记录
    使用 JSON 文件存储
    """

    def __init__(self, file_path: str):
        """
        初始化提醒管理器

        参数：
            file_path: 提醒记录保存的文件路径
        """
        self.file_path = Path(file_path)
        self.reminders = []  # 提醒列表

        # 如果文件存在，加载提醒记录
        if self.file_path.exists():
            self.load()

    def add_reminder(self, minutes: int, message: str = "") -> dict:
        """
        添加一条提醒

        参数：
            minutes: 多少分钟后提醒
            message: 提醒的内容（可选）

        返回：
            提醒记录字典
        """
        now = datetime.now()
        # 计算到期时间
        due_time = now.timestamp() + (minutes * 60)  # timestamp() 返回秒级时间戳

        reminder = {
            "id": str(int(now.timestamp() * 1000)),  # 用时间戳作为唯一 ID（毫秒级）
            "created_at": now.isoformat(),           # 创建时间
            "due_time": due_time,                    # 到期时间（时间戳）
            "minutes": minutes,                      # 原始分钟数
            "message": message,                      # 提醒内容（新增！）
            "completed": False                       # 是否已完成
        }

        self.reminders.append(reminder)
        self.save()
        return reminder

    def get_pending_reminders(self) -> list:
        """
        获取所有未完成的提醒

        返回：
            未完成的提醒列表
        """
        return [r for r in self.reminders if not r["completed"]]

    def mark_completed(self, reminder_id: str):
        """
        标记提醒为已完成

        参数：
            reminder_id: 提醒的 ID
        """
        for reminder in self.reminders:
            if reminder["id"] == reminder_id:
                reminder["completed"] = True
                break
        self.save()

    def save(self):
        """
        保存提醒记录到 JSON 文件
        """
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.reminders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存提醒记录失败：{e}")

    def load(self):
        """
        从 JSON 文件加载提醒记录
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.reminders = json.load(f)
        except Exception as e:
            print(f"加载提醒记录失败：{e}")
            self.reminders = []


# ============================================
# 第三部分：后台工作线程
# ============================================
class ChatWorker(QThread):
    """
    用于在后台调用 AI API 的工作线程
    为什么需要线程？因为 API 调用可能需要几秒钟，如果在主线程执行会导致界面卡死

    Signal（信号）是 Qt 的线程间通信机制：
        - finished: 当 API 调用完成时发出信号，携带 AI 的回复（dict 格式）
    """

    finished = Signal(dict)  # 改成 dict 类型（包含 content 和 tool_calls）

    def __init__(self, ai_client: AIClient, messages: list):
        """
        初始化工作线程

        参数：
            ai_client: AI 客户端对象
            messages: 要发送给 API 的消息列表
        """
        super().__init__()
        self.ai_client = ai_client
        self.messages = messages

    def run(self):
        """
        线程的主函数（自动在后台执行）
        """
        # 调用 AI API 获取回复（现在返回 dict）
        reply = self.ai_client.chat(self.messages)

        # 发出 finished 信号，把回复传回主线程
        self.finished.emit(reply)


class ChatWorkerWithTools(QThread):
    """
    支持工具调用的工作线程
    当 AI 调用工具后，执行工具，然后将结果返回给 AI 让其整理
    """

    finished = Signal(dict)

    def __init__(self, ai_client: AIClient, messages: list, tools: list, main_window):
        """
        初始化工作线程

        参数：
            ai_client: AI 客户端对象
            messages: 要发送给 API 的消息列表
            tools: 可用的工具列表
            main_window: 主窗口对象（用于调用工具函数）
        """
        super().__init__()
        self.ai_client = ai_client
        self.messages = messages
        self.tools = tools
        self.main_window = main_window

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
        import json

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
                    results = self.main_window.knowledge_base.search(tool_args.get("query", ""), n_results=3)
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
# 第四部分：主窗口界面
# ============================================
class SimpleAIAgent(QWidget):
    """
    主窗口类 - 继承自 QWidget（Qt 的基础窗口）

    界面布局：
        ┌─────────────────────────────────┐
        │  🤖 简易 AI 桌面助手              │  ← 标题
        ├─────────────────────────────────┤
        │                                 │
        │  [对话显示区域]                  │  ← QTextEdit（多行文本）
        │                                 │
        ├─────────────────────────────────┤
        │  [输入框]  [发送]  [清空历史]    │  ← 输入区
        └─────────────────────────────────┘
    """

    def __init__(self):
        super().__init__()

        # 加载配置文件
        self.config = load_config("config.yaml")

        # 初始化 AI 客户端（从配置文件读取参数）
        api_config = self.config.get("api", {})
        self.ai_client = AIClient(
            api_key=api_config.get("api_key", "your-api-key-here"),
            base_url=api_config.get("base_url", "https://api.openai.com/v1"),
            model=api_config.get("model", "gpt-3.5-turbo"),
            temperature=api_config.get("temperature", 0.7),
            max_tokens=api_config.get("max_tokens", 1000)
        )

        # 初始化会话管理器（新增！）
        self.session_manager = SessionManager("data/sessions")

        # 临时会话（启动时的新对话，未保存）
        self.temp_session = None

        # 初始化聊天历史管理器（保留用于兼容）
        self.chat_history = ChatHistory("data/chat_history.json")

        # 初始化提醒管理器
        self.reminder_manager = ReminderManager("data/reminders.json")

        # 初始化知识库（新增！）
        self.knowledge_base = KnowledgeBase("data/knowledge_base")

        # 联网搜索开关（新增！默认关闭）
        self.web_search_enabled = False

        # 附加文件列表（用于存储用户临时上传的文件内容）
        self.attached_files = []

        # 工作线程（初始为 None）
        self.worker = None

        # 系统提示词（从配置文件读取）
        system_prompt_text = self.config.get(
            "system_prompt",
            "你是一个友好的 AI 助手，用简洁友好的语言回答用户的问题。"
        )
        self.system_prompt = {
            "role": "system",
            "content": system_prompt_text
        }

        # 设置窗口界面
        self.init_ui()

        # 加载会话列表（新增！）
        self.load_session_list()

        # 加载历史对话
        self.load_history()

        # 加载未完成的提醒（新增！）
        self.load_pending_reminders()

    def init_ui(self):
        """
        初始化用户界面（带侧边栏的布局）
        """
        # 从配置文件读取界面设置
        ui_config = self.config.get("ui", {})
        window_title = ui_config.get("window_title", "🤖 简易 AI 桌面助手")
        window_width = ui_config.get("window_width", 900)  # 增加宽度以容纳侧边栏
        window_height = ui_config.get("window_height", 700)

        # 1. 设置窗口基本属性
        self.setWindowTitle(window_title)
        self.setGeometry(100, 100, window_width, window_height)

        # 2. 创建主布局
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 3. 创建左侧边栏
        sidebar = self.create_sidebar()

        # 4. 创建右侧聊天区域
        chat_area = self.create_chat_area()

        # 5. 使用 QSplitter 分割左右区域（用户可以拖动调整大小）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(sidebar)
        splitter.addWidget(chat_area)
        splitter.setStretchFactor(0, 1)  # 侧边栏占 1 份
        splitter.setStretchFactor(1, 3)  # 聊天区占 3 份
        splitter.setSizes([250, 650])     # 初始宽度

        main_layout.addWidget(splitter)

        # 6. 设置主布局
        self.setLayout(main_layout)

    def create_sidebar(self) -> QWidget:
        """
        创建左侧边栏（会话列表）
        """
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(10)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = QLabel("📝 对话历史")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title)

        # 新建对话按钮
        new_chat_button = QPushButton("+ 新建对话")
        new_chat_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        new_chat_button.clicked.connect(self.create_new_chat)
        new_chat_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        sidebar_layout.addWidget(new_chat_button)

        # 会话列表
        self.session_list = QListWidget()
        self.session_list.setFont(QFont("Arial", 10))
        self.session_list.itemClicked.connect(self.on_session_clicked)
        self.session_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self.show_session_context_menu)
        self.session_list.setStyleSheet("""
            QListWidget {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
        """)
        # 禁用水平滚动条
        self.session_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar_layout.addWidget(self.session_list, stretch=1)

        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-right: 1px solid #ddd;
            }
        """)

        return sidebar_widget

    def create_chat_area(self) -> QWidget:
        """
        创建右侧聊天区域
        """
        chat_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 1. 顶部标题
        title = QLabel("💬 和 AI 聊天")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 2. 对话显示区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 11))
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.chat_display, stretch=1)

        # 3. 输入区域（水平布局）
        input_layout = QHBoxLayout()

        # 输入框
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("在这里输入消息...")
        self.input_box.setFont(QFont("Arial", 11))
        self.input_box.returnPressed.connect(self.send_message)
        self.input_box.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        input_layout.addWidget(self.input_box, stretch=1)

        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # 4. 功能按钮区域
        button_layout = QHBoxLayout()

        # 提醒按钮
        self.reminder_button = QPushButton("⏰ 提醒")
        self.reminder_button.setFont(QFont("Arial", 11))
        self.reminder_button.clicked.connect(self.show_reminder_dialog)
        self.reminder_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        button_layout.addWidget(self.reminder_button)

        # 附加文件按钮
        self.attach_button = QPushButton("📎 附加文件")
        self.attach_button.setFont(QFont("Arial", 11))
        self.attach_button.clicked.connect(self.attach_file)
        self.attach_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(self.attach_button)

        # 设置按钮
        self.settings_button = QPushButton("⚙️ 设置")
        self.settings_button.setFont(QFont("Arial", 11))
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        button_layout.addWidget(self.settings_button)

        # 创建设置菜单
        settings_menu = QMenu(self)

        # 上传到知识库
        upload_to_kb_action = settings_menu.addAction("📚 上传到知识库")
        upload_to_kb_action.triggered.connect(self.upload_to_knowledge_base)

        # 联网搜索开关
        self.web_search_action = settings_menu.addAction("🌐 联网搜索")
        self.web_search_action.setCheckable(True)
        self.web_search_action.setChecked(self.web_search_enabled)
        self.web_search_action.triggered.connect(self.toggle_web_search)

        self.settings_button.setMenu(settings_menu)

        # 清空当前对话按钮
        self.clear_button = QPushButton("🗑️ 清空")
        self.clear_button.setFont(QFont("Arial", 11))
        self.clear_button.clicked.connect(self.clear_current_chat)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        button_layout.addWidget(self.clear_button)

        layout.addLayout(button_layout)

        chat_widget.setLayout(layout)
        return chat_widget

    def load_history(self):
        """
        加载当前会话的历史对话到显示区域
        """
        # 启动时始终显示临时会话（空白）
        self.temp_session = True
        # 不显示任何历史记录，保持空白

    def append_message(self, sender: str, content: str):
        """
        在对话显示区域添加一条消息

        参数：
            sender: 发送者名称（"你" 或 "AI" 或 "系统"）
            content: 消息内容
        """
        # 根据发送者设置不同的颜色
        if sender == "你":
            color = "#2196F3"
        elif sender == "AI":
            color = "#4CAF50"
        else:  # 系统消息
            color = "#9E9E9E"

        # 如果是 AI 消息，美化 Markdown 格式
        if sender == "AI":
            content = self._beautify_markdown(content)

        # 使用 HTML 格式化消息（支持富文本显示）
        html = f"""
        <div style="margin: 10px 0;">
            <b style="color: {color};">{sender}：</b>
            <span style="white-space: pre-wrap;">{content}</span>
        </div>
        """
        self.chat_display.append(html)

        # 自动滚动到底部（显示最新消息）
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _beautify_markdown(self, text: str) -> str:
        """
        美化 AI 输出的 Markdown 格式

        将 Markdown 语法转换为 HTML 样式：
        - **粗体** → <b>粗体</b>
        - *斜体* → <i>斜体</i>
        - # 标题 → <h3>标题</h3>
        - - 列表 → <li>列表</li>
        - 1. 列表 → <li>列表</li>

        参数：
            text: 原始文本

        返回：
            美化后的 HTML 文本
        """
        import re

        # 转义 HTML 特殊字符
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # 1. 处理标题（# ## ###）
        lines = text.split('\n')
        processed_lines = []

        for line in lines:
            # 三级标题 ###
            if line.startswith('### '):
                line = f'<h3 style="color: #1976d2; margin: 10px 0 5px 0; font-size: 14px;">{line[4:]}</h3>'
            # 二级标题 ##
            elif line.startswith('## '):
                line = f'<h2 style="color: #1565c0; margin: 12px 0 6px 0; font-size: 15px; font-weight: bold;">{line[3:]}</h2>'
            # 一级标题 #
            elif line.startswith('# '):
                line = f'<h1 style="color: #0d47a1; margin: 15px 0 8px 0; font-size: 16px; font-weight: bold;">{line[2:]}</h1>'

            processed_lines.append(line)

        text = '\n'.join(processed_lines)

        # 2. 处理粗体 **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<b style="color: #d32f2f;">\1</b>', text)

        # 3. 处理斜体 *text*（但不处理已经在 ** 中的）
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i style="color: #7b1fa2;">\1</i>', text)

        # 4. 处理无序列表 - item
        text = re.sub(r'^- (.+)$', r'<li style="margin-left: 20px; color: #424242;">\1</li>', text, flags=re.MULTILINE)

        # 5. 处理有序列表 1. item
        text = re.sub(r'^(\d+)\. (.+)$', r'<li style="margin-left: 20px; color: #424242;"><b>\1.</b> \2</li>', text, flags=re.MULTILINE)

        # 6. 处理代码块 `code`
        text = re.sub(r'`(.+?)`', r'<code style="background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; color: #c62828; font-family: monospace;">\1</code>', text)

        return text

    def _get_enabled_tools(self) -> list:
        """
        根据设置获取启用的工具列表

        返回：
            启用的工具列表
        """
        tools = []

        # 提醒工具（始终启用）
        tools.append({
            "type": "function",
            "function": {
                "name": "set_reminder",
                "description": "设置提醒",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "minutes": {
                            "type": "integer",
                            "description": "分钟数"
                        },
                        "message": {
                            "type": "string",
                            "description": "提醒内容"
                        }
                    },
                    "required": ["minutes", "message"]
                }
            }
        })

        # 联网搜索工具（可选）
        if self.web_search_enabled:
            tools.append({
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "搜索信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "关键词"
                            }
                        },
                        "required": ["query"]
                    }
                }
            })

        # 知识库搜索（始终启用）
        tools.append({
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "搜索知识库",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "关键词"
                        }
                    },
                    "required": ["query"]
                }
            }
        })

        return tools

    def send_message(self):
        """
        发送消息的主函数
        """
        # 获取用户输入
        user_message = self.input_box.text().strip()

        # 如果输入为空，不处理
        if not user_message:
            return

        # 如果正在等待 AI 回复，不允许发送新消息
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "请稍候", "AI 正在思考中，请稍等...")
            return

        # 1. 显示用户消息
        self.append_message("你", user_message)

        # 2. 如果有附加文件，将文件内容添加到用户消息中
        full_user_message = user_message
        if self.attached_files:
            # 构建文件内容
            files_content = "\n\n【附加文件】\n"
            for file_info in self.attached_files:
                files_content += f"\n--- 文件：{file_info['filename']} ---\n"
                files_content += file_info['content']
                files_content += f"\n--- 文件结束 ---\n"

            full_user_message = user_message + files_content

            # 显示提示
            self.append_message("系统", f"📎 已将 {len(self.attached_files)} 个文件内容发送给 AI")

        # 3. 获取当前会话（如果是临时会话，发送消息时创建真实会话）
        if self.temp_session:
            # 临时会话变为真实会话
            session_id = self.session_manager.create_new_session()
            current_session = self.session_manager.get_current_session()

            # 使用用户消息的前15个字作为标题
            title = user_message[:15] if len(user_message) <= 15 else user_message[:15] + "..."
            self.session_manager.update_session_title(current_session.session_id, title)

            # 清除临时会话标记
            self.temp_session = None

            # 刷新会话列表以显示新会话
            self.load_session_list()
        else:
            # 正常获取当前会话
            current_session = self.session_manager.get_current_session()

            # 如果是新对话的第一条消息，更新标题
            if len(current_session.messages) == 0:
                title = user_message[:15] if len(user_message) <= 15 else user_message[:15] + "..."
                self.session_manager.update_session_title(current_session.session_id, title)
                # 刷新会话列表以显示新标题
                self.load_session_list()

        # 4. 保存到当前会话
        current_session.add_message("user", user_message)
        self.session_manager.save_all_sessions()

        # 6. 兼容：也保存到旧的历史记录系统
        self.chat_history.add_message("user", user_message)

        # 5. 清空输入框
        self.input_box.clear()

        # 6. 禁用发送按钮（防止重复点击）
        self.send_button.setEnabled(False)
        self.send_button.setText("思考中...")

        # 7. 准备发送给 API 的消息（包含系统提示词 + 当前会话的历史对话）
        api_messages = [self.system_prompt] + current_session.get_messages_for_api()

        # 8. 如果有附加文件，修改最后一条用户消息（添加文件内容）
        if self.attached_files:
            # 替换最后一条用户消息为包含文件内容的完整消息
            api_messages[-1] = {
                "role": "user",
                "content": full_user_message
            }

            # 清空附加文件列表（文件只在这次对话中有效）
            self.attached_files = []

            # 恢复输入框提示
            self.input_box.setPlaceholderText("在这里输入消息...")

        # 9. 根据联网搜索开关决定是否包含搜索工具
        tools = self._get_enabled_tools()

        # 10. 创建后台工作线程（传入工具列表）
        self.worker = ChatWorkerWithTools(self.ai_client, api_messages, tools, self)

        # 11. 连接信号：当 AI 回复完成时，调用 handle_ai_reply 函数
        self.worker.finished.connect(self.handle_ai_reply)

        # 12. 启动线程
        self.worker.start()

    def handle_ai_reply(self, reply: dict):
        """
        处理 AI 的回复

        参数：
            reply: AI 返回的回复字典，格式：
                {
                    "content": "AI 的文字回复",
                    "tool_calls": [],  # 已在线程中处理
                    "truncated": bool,
                    "pending_reminders": [],  # 待处理的提醒（需要在主线程设置）
                    "search_queries": []  # 已执行的搜索查询
                }
        """
        # 1. 处理待设置的提醒（必须在主线程）
        if "pending_reminders" in reply:
            for reminder_data in reply["pending_reminders"]:
                minutes = reminder_data["minutes"]
                message = reminder_data["message"]
                reminder = self.reminder_manager.add_reminder(minutes, message)
                self._start_reminder_timer(reminder)

        # 2. 显示搜索提示（如果进行了搜索）
        if "search_queries" in reply and reply["search_queries"]:
            for query in reply["search_queries"]:
                self.append_message("系统", f"🔍 已联网搜索：{query}")

        # 3. 显示 AI 回复
        self.append_message("AI", reply["content"])

        # 4. 检查是否被截断
        if reply.get("truncated", False):
            self.append_message("系统", "⚠️ 回复因长度限制被截断。如需完整回答，请：\n1. 将问题拆分成多个小问题\n2. 或要求 AI 简化回答")

        # 5. 保存到当前会话
        current_session = self.session_manager.get_current_session()
        current_session.add_message("assistant", reply["content"])
        self.session_manager.save_all_sessions()

        # 6. 兼容：也保存到旧的历史记录系统
        self.chat_history.add_message("assistant", reply["content"])

        # 7. 恢复发送按钮
        self.send_button.setEnabled(True)
        self.send_button.setText("发送")

        # 8. 清理工作线程
        self.worker = None

    def create_new_chat(self):
        """
        创建新对话（临时会话，用户发送消息后才保存）
        """
        # 清空显示区域
        self.chat_display.clear()

        # 设置为临时会话
        self.temp_session = True

        # 显示提示
        self.append_message("系统", "已创建新对话")

    def on_session_clicked(self, item: QListWidgetItem):
        """
        点击会话列表项，切换到该会话
        """
        # 获取会话 ID（存储在 item 的 data 中）
        session_id = item.data(Qt.ItemDataRole.UserRole)

        if session_id:
            # 取消临时会话状态
            self.temp_session = None

            # 切换会话
            self.session_manager.switch_session(session_id)

            # 清空显示区域
            self.chat_display.clear()

            # 加载该会话的历史记录
            current_session = self.session_manager.get_current_session()
            for msg in current_session.messages:
                role = "你" if msg["role"] == "user" else "AI"
                self.append_message(role, msg["content"])

    def show_session_context_menu(self, position):
        """
        显示会话列表的右键菜单（删除/重命名）
        """
        # 获取点击的项
        item = self.session_list.itemAt(position)
        if not item:
            return

        session_id = item.data(Qt.ItemDataRole.UserRole)

        # 创建菜单
        menu = QMenu(self)

        # 重命名操作
        rename_action = menu.addAction("✏️ 重命名")
        rename_action.triggered.connect(lambda: self.rename_session(session_id))

        # 删除操作
        delete_action = menu.addAction("🗑️ 删除")
        delete_action.triggered.connect(lambda: self.delete_session(session_id))

        # 显示菜单
        menu.exec(self.session_list.mapToGlobal(position))

    def rename_session(self, session_id: str):
        """
        重命名会话
        """
        # 获取当前标题
        session = self.session_manager.sessions.get(session_id)
        if not session:
            return

        # 弹出输入框
        new_title, ok = QInputDialog.getText(
            self,
            "重命名对话",
            "请输入新标题：",
            text=session.title
        )

        if ok and new_title.strip():
            # 更新标题
            self.session_manager.update_session_title(session_id, new_title.strip())

            # 刷新列表
            self.load_session_list()

    def delete_session(self, session_id: str):
        """
        删除会话
        """
        # 确认
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个对话吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 删除会话
            self.session_manager.delete_session(session_id)

            # 刷新列表
            self.load_session_list()

            # 清空显示区域并加载新的当前会话
            self.chat_display.clear()
            current_session = self.session_manager.get_current_session()
            for msg in current_session.messages:
                role = "你" if msg["role"] == "user" else "AI"
                self.append_message(role, msg["content"])

    def load_session_list(self):
        """
        加载会话列表到侧边栏
        """
        # 清空列表
        self.session_list.clear()

        # 获取所有会话
        sessions = self.session_manager.get_all_sessions()

        # 添加到列表
        for session in sessions:
            # 创建列表项，限制标题长度
            title = session["title"]
            if len(title) > 20:
                display_title = title[:20] + "..."
            else:
                display_title = title

            item = QListWidgetItem(display_title)

            # 设置完整标题为 tooltip（鼠标悬停时显示）
            item.setToolTip(session["title"])

            # 存储会话 ID
            item.setData(Qt.ItemDataRole.UserRole, session["session_id"])

            # 如果是当前会话，标记为选中
            if session["session_id"] == self.session_manager.current_session_id:
                item.setSelected(True)

            self.session_list.addItem(item)

    def clear_current_chat(self):
        """
        清空当前对话
        """
        # 弹出确认对话框
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空当前对话吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 获取当前会话
            current_session = self.session_manager.get_current_session()

            # 清空消息
            current_session.messages = []
            current_session.updated_at = datetime.now().isoformat()

            # 保存
            self.session_manager.save_all_sessions()

            # 清空显示区域
            self.chat_display.clear()

            # 显示提示
            QMessageBox.information(self, "已清空", "当前对话已清空！")

    def clear_history(self):
        """
        清空聊天历史（保留用于兼容）
        """
        # 弹出确认对话框
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有聊天记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 清空历史记录
            self.chat_history.clear()

            # 清空显示区域
            self.chat_display.clear()

            # 显示提示
            QMessageBox.information(self, "已清空", "聊天记录已清空！")

    def show_reminder_dialog(self):
        """
        显示设置提醒的对话框

        流程：
        1. 弹出输入框让用户输入分钟数
        2. 保存提醒到文件
        3. 创建定时器
        4. 时间到了弹出提示
        """
        # 弹出对话框，让用户输入分钟数
        minutes, ok = QInputDialog.getInt(
            self,                              # 父窗口
            "设置提醒",                         # 对话框标题
            "多少分钟后提醒你？",               # 提示文字
            1,                                 # 默认值
            1,                                 # 最小值
            60                                 # 最大值（最多 60 分钟）
        )

        # 如果用户点了"确定"（而不是"取消"）
        if ok:
            # 保存提醒到文件
            reminder = self.reminder_manager.add_reminder(minutes)

            # 显示确认消息
            QMessageBox.information(
                self,
                "提醒已设置",
                f"好的！我会在 {minutes} 分钟后提醒你 ⏰"
            )

            # 启动定时器
            self._start_reminder_timer(reminder)

    def _start_reminder_timer(self, reminder: dict):
        """
        为一个提醒启动定时器

        参数：
            reminder: 提醒记录字典（包含 id, due_time, minutes 等）
        """
        # 计算还剩多少时间（秒）
        now = datetime.now().timestamp()
        remaining_seconds = reminder["due_time"] - now

        # 如果已经过期，直接提醒
        if remaining_seconds <= 0:
            self._show_reminder_notification(reminder)
            return

        # 创建定时器
        reminder_timer = QTimer(self)
        reminder_timer.setSingleShot(True)

        # 设置时间间隔（秒 → 毫秒）
        milliseconds = int(remaining_seconds * 1000)
        reminder_timer.setInterval(milliseconds)

        # 时间到了做什么？
        reminder_timer.timeout.connect(lambda: self._show_reminder_notification(reminder))

        # 启动定时器
        reminder_timer.start()

        # 保存定时器引用（防止被垃圾回收）
        if not hasattr(self, 'active_reminders'):
            self.active_reminders = {}  # 改用字典，键是 reminder_id
        self.active_reminders[reminder["id"]] = reminder_timer

    def load_pending_reminders(self):
        """
        加载所有未完成的提醒，并重新启动定时器
        """
        pending = self.reminder_manager.get_pending_reminders()
        for reminder in pending:
            self._start_reminder_timer(reminder)

        # 如果有未完成的提醒，显示提示
        if pending:
            print(f"已加载 {len(pending)} 个未完成的提醒")

    def _show_reminder_notification(self, reminder: dict):
        """
        时间到了，弹出提醒

        参数：
            reminder: 提醒记录字典
        """
        minutes = reminder["minutes"]
        message = reminder.get("message", "")  # 获取提醒内容

        # 构建提示文字
        if message:
            notification_text = f"⏰ 时间到了！\n\n提醒内容：{message}\n\n({minutes} 分钟已过)"
        else:
            notification_text = f"时间到了！{minutes} 分钟已过。"

        # 弹出提示框
        QMessageBox.information(
            self,
            "⏰ 提醒",
            notification_text
        )

        # 发出系统声音
        from PySide6.QtWidgets import QApplication
        QApplication.beep()

        # 标记为已完成
        self.reminder_manager.mark_completed(reminder["id"])

        # 从活动列表中移除
        if hasattr(self, 'active_reminders') and reminder["id"] in self.active_reminders:
            del self.active_reminders[reminder["id"]]

    def attach_file(self):
        """
        附加文件到当前对话（临时阅读）

        流程：
        1. 打开文件选择对话框
        2. 读取文件内容
        3. 存储到附加文件列表
        4. 显示确认消息
        """
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要附加的文件",
            "",
            "文本文件 (*.txt *.md *.py *.js *.json *.yaml *.yml);;所有文件 (*)"
        )

        # 如果用户取消了
        if not file_path:
            return

        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 获取文件名
            from pathlib import Path
            filename = Path(file_path).name

            # 添加到附加文件列表
            self.attached_files.append({
                "filename": filename,
                "content": content,
                "path": file_path
            })

            # 显示成功消息
            self.append_message("系统", f"✅ 已附加文件：{filename} ({len(content)} 字符)")

            # 在输入框提示用户可以提问了
            if not self.input_box.text():
                self.input_box.setPlaceholderText(f"现在可以问关于 {filename} 的问题了...")

        except Exception as e:
            QMessageBox.critical(self, "读取失败", f"无法读取文件：{str(e)}")

    def toggle_web_search(self):
        """
        切换联网搜索开关
        """
        self.web_search_enabled = self.web_search_action.isChecked()

        # 显示提示
        if self.web_search_enabled:
            self.append_message("系统", "✅ 已启用联网搜索")
        else:
            self.append_message("系统", "❌ 已禁用联网搜索")

    def upload_to_knowledge_base(self):
        """
        上传文档到知识库（永久存储，使用 RAG）

        流程：
        1. 打开文件选择对话框
        2. 读取文件内容
        3. 添加到知识库
        4. 显示确认消息
        """
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文档",
            "",
            "文本文件 (*.txt *.md);;所有文件 (*)"
        )

        # 如果用户取消了
        if not file_path:
            return

        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # 获取文件名
            filename = Path(file_path).name

            # 添加到知识库
            result = self.knowledge_base.add_document(text, filename)

            # 显示确认消息
            QMessageBox.information(
                self,
                "上传成功",
                f"✅ 文档已添加到知识库\n\n"
                f"文件名：{result['filename']}\n"
                f"文本块数：{result['chunks']}\n"
                f"总字符数：{result['total_chars']}"
            )

            # 在对话中显示
            self.append_message("系统", f"📄 已上传文档：{filename}")

        except Exception as e:
            # 如果出错，显示错误
            QMessageBox.critical(
                self,
                "上传失败",
                f"❌ 上传文档失败：{str(e)}"
            )


# ============================================
# 主程序入口
# ============================================
if __name__ == "__main__":
    # 1. 创建应用程序对象（每个 Qt 程序必须有一个 QApplication）
    app = QApplication(sys.argv)

    # 2. 创建主窗口
    window = SimpleAIAgent()

    # 3. 显示窗口
    window.show()

    # 4. 进入事件循环（程序会一直运行，直到窗口关闭）
    sys.exit(app.exec())
