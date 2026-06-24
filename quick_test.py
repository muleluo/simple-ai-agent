#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试几个常用模型
"""

from openai import OpenAI

api_key = "sk-vftbZadWT0gVBAlGMZXJgQGTWqyOM2LcyZb087eDbVnaRQ9z"
base_url = "https://api.gemai.cc/v1"

# 测试这几个最常见的模型
models = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

client = OpenAI(api_key=api_key, base_url=base_url)

for model in models:
    try:
        print(f"测试 {model}...", end=" ")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=20
        )
        print(f"✅ 成功: {response.choices[0].message.content}")
        print(f"推荐使用这个: {model}")
        break
    except Exception as e:
        print(f"❌ 失败: {str(e)[:80]}")
