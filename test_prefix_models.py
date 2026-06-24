#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试带前缀的模型
"""

from openai import OpenAI

api_key = "sk-vftbZadWT0gVBAlGMZXJgQGTWqyOM2LcyZb087eDbVnaRQ9z"
base_url = "https://api.gemai.cc/v1"

# 测试截图中看到的带前缀的模型
models = [
    "[福利]gemini-3.1-flash-lite-preview",
    "[满血A]gemini-3.1-flash-lite-preview",
    "[满血E]gemini-3.5-flash",
    "[满血F]gemini-2.5-pro",
    "[官逆C]gemini-3-flash-preview",
    "[premium]gemini-2.5-flash",
]

client = OpenAI(api_key=api_key, base_url=base_url)

print("测试带前缀的模型...")
print("=" * 60)

for model in models:
    try:
        print(f"\n测试 {model}...", end=" ")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "1+1=?"}],
            max_tokens=20,
            timeout=10
        )
        reply = response.choices[0].message.content
        print(f"✅ 成功!")
        print(f"  回复: {reply}")
        print(f"\n✅✅✅ 推荐使用这个模型: {model}")
        break
    except Exception as e:
        error = str(e)[:150]
        print(f"❌ 失败")
        print(f"  错误: {error}")

print("\n" + "=" * 60)
