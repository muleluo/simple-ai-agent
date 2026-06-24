#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试哪些模型可用
"""

from openai import OpenAI
import yaml

# 读取配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

api_key = config['api']['api_key']
base_url = config['api']['base_url']

# 从截图中看到的模型列表（选择一些常用的测试）
models_to_test = [
    "gemini-3.5-flash",
    "[满血A]gemini-3.1-flash-lite-preview",
    "[福利]gemini-3.1-flash-lite-preview",
    "[官逆C]gemini-3-flash-preview",
    "[满血F]gemini-2.5-pro",
    "gemini-2.5-pro",
    "[premium]gemini-2.5-flash",
    "[满血E]gemini-3.5-flash",
]

print("开始测试模型...")
print("=" * 50)

client = OpenAI(api_key=api_key, base_url=base_url)

working_models = []

for model in models_to_test:
    try:
        print(f"\n测试: {model}")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "你好"}
            ],
            max_tokens=50
        )

        reply = response.choices[0].message.content
        print(f"✅ 成功! 回复: {reply[:50]}...")
        working_models.append(model)

    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + "..."
        print(f"❌ 失败: {error_msg}")

print("\n" + "=" * 50)
print(f"\n可用的模型 ({len(working_models)} 个):")
for model in working_models:
    print(f"  ✅ {model}")

if working_models:
    print(f"\n推荐使用: {working_models[0]}")
