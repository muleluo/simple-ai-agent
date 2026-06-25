#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 QML 版本的 AI 集成
"""

import sys
from PySide6.QtCore import QCoreApplication
from main_qml import AIClient, ChatWorkerWithTools, PyBridge, SessionListModel, MessageListModel
from session_manager import SessionManager

def test_ai_client():
    """测试 AI 客户端初始化"""
    print("=" * 50)
    print("测试 1: AIClient 初始化")
    print("=" * 50)

    ai_client = AIClient(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model="gpt-3.5-turbo"
    )

    print(f"✅ API Key: {ai_client.api_key[:10]}...")
    print(f"✅ Base URL: {ai_client.base_url}")
    print(f"✅ Model: {ai_client.model}")
    print(f"✅ Tools count: {len(ai_client.tools)}")

    for tool in ai_client.tools:
        tool_name = tool["function"]["name"]
        print(f"   - {tool_name}")

    print()

def test_pybridge():
    """测试 PyBridge 初始化"""
    print("=" * 50)
    print("测试 2: PyBridge 初始化")
    print("=" * 50)

    session_manager = SessionManager("data/sessions")
    session_list_model = SessionListModel(session_manager)
    message_list_model = MessageListModel()

    py_bridge = PyBridge(session_list_model, message_list_model)

    print(f"✅ AI Client initialized: {py_bridge.ai_client is not None}")
    print(f"✅ Model: {py_bridge.ai_client.model}")
    print(f"✅ System prompt: {py_bridge.system_prompt['content'][:50]}...")
    print(f"✅ Web search enabled: {py_bridge._web_search_enabled}")
    print()

def test_message_flow():
    """测试消息流程"""
    print("=" * 50)
    print("测试 3: 消息流程")
    print("=" * 50)

    session_manager = SessionManager("data/sessions")
    session_list_model = SessionListModel(session_manager)
    message_list_model = MessageListModel()

    py_bridge = PyBridge(session_list_model, message_list_model)

    # 模拟发送消息
    print("添加用户消息...")
    message_list_model.add_message("user", "你好")
    print(f"✅ 消息数量: {len(message_list_model.messages)}")

    print("添加助手消息...")
    message_list_model.add_message("assistant", "你好！有什么可以帮助你的吗？")
    print(f"✅ 消息数量: {len(message_list_model.messages)}")

    print("添加系统消息...")
    message_list_model.add_message("system", "AI 正在思考...")
    print(f"✅ 消息数量: {len(message_list_model.messages)}")

    print()

    return py_bridge

if __name__ == "__main__":
    print("\n🧪 开始测试 QML 版本 AI 集成\n")

    # 创建应用程序（只创建一次）
    app = QCoreApplication(sys.argv)

    test_ai_client()
    bridge = test_pybridge()
    test_message_flow()

    print("=" * 50)
    print("✅ 所有测试完成！")
    print("=" * 50)
    print("\n提示：要测试真实 AI 调用，请：")
    print("1. 在 config.yaml 中配置正确的 API key")
    print("2. 运行 python3 main_qml.py")
    print("3. 发送消息测试 AI 回复\n")
