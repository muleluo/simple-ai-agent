#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 AI 对话功能
"""

from openai import OpenAI
import yaml

# 读取配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

api_config = config['api']
client = OpenAI(
    api_key=api_config['api_key'],
    base_url=api_config['base_url']
)

print(f"测试模型: {api_config['model']}")
print(f"API 地址: {api_config['base_url']}")
print("=" * 60)

try:
    print("\n发送消息: 你好，请介绍一下你自己")

    response = client.chat.completions.create(
        model=api_config['model'],
        messages=[
            {"role": "system", "content": "你是一个友好的 AI 助手"},
            {"role": "user", "content": "你好，请介绍一下你自己"}
        ],
        temperature=0.7,
        max_tokens=200
    )

    reply = response.choices[0].message.content
    print(f"\n✅ AI 回复:\n{reply}")

    print("\n" + "=" * 60)
    print("✅ API 工作正常！")
    print(f"✅ 当前模型可用: {api_config['model']}")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    print("\n建议:")
    print("1. 检查 API Key 是否正确")
    print("2. 检查网络连接")
    print("3. 检查 API 地址是否正确")
