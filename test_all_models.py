#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有带前缀的模型，找出最好用的
"""

from openai import OpenAI

api_key = "sk-vftbZadWT0gVBAlGMZXJgQGTWqyOM2LcyZb087eDbVnaRQ9z"
base_url = "https://api.gemai.cc/v1"

# 从截图中提取的所有模型
models = [
    "[满血E]gemini-3.5-flash",
    "[官]gemini-3-pro-image-preview",
    "[满血D]gemini-3-pro-preview",
    "[满血G]gemini-3.5-flash",
    "[满血A]gemini-2.5-pro",
    "[满血F]gemini-2.5-pro",
    "[福利]gemini-3-flash-preview",
    "[满血F]gemini-3-pro-preview-search-maxthinking",
    "[满血A]gemini-3.1-flash-lite-preview",
    "[福利]gemini-3.1-flash-lite-preview",
    "[官逆C]gemini-3-flash-preview",
    "[满血A]gemini-3.1-flash-lite-preview-search-maxthinking",
    "[满血F]gemini-3.1-pro-preview",
    "[premium]gemini-2.5-pro",
    "[官逆C]gemini-3-pro-preview",
    "[满血F]gemini-2.5-pro",
    "[福利]gemini-3.5-flash",
    "[premium]gemini-2.5-flash",
]

client = OpenAI(api_key=api_key, base_url=base_url)

print("测试所有模型...")
print("=" * 70)

working_models = []

for i, model in enumerate(models, 1):
    try:
        print(f"\n[{i}/{len(models)}] 测试: {model[:50]}...")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "说一句话"}],
            max_tokens=50,
            timeout=10
        )
        reply = response.choices[0].message.content.strip()

        if reply:  # 只记录有内容的回复
            print(f"  ✅ 成功! 回复: {reply[:60]}")
            working_models.append((model, reply))
        else:
            print(f"  ⚠️  成功但回复为空")

    except Exception as e:
        error = str(e)
        if "403" in error:
            print(f"  ❌ 无权限")
        elif "timeout" in error.lower():
            print(f"  ⏱️  超时")
        else:
            print(f"  ❌ 失败: {error[:60]}")

print("\n" + "=" * 70)
print(f"\n可用的模型 ({len(working_models)} 个):")
print("-" * 70)

for model, reply in working_models:
    print(f"\n✅ {model}")
    print(f"   回复示例: {reply[:80]}")

if working_models:
    best_model = working_models[0][0]
    print("\n" + "=" * 70)
    print(f"🎯 推荐使用: {best_model}")
    print("=" * 70)
