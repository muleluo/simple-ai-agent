# 联网搜索功能 - 规划文档

**日期**：2026-06-20  
**功能**：让 AI 能搜索网络获取实时信息  
**状态**：🚧 规划中

---

## 🎯 目标

**用户场景**：
```
用户：今天北京天气怎么样？
AI：让我帮你搜索一下... [调用搜索]
AI：根据搜索结果，今天北京晴天，温度 25°C...

用户：最新的 iPhone 多少钱？
AI：让我搜索最新信息... [调用搜索]
AI：根据搜索结果，最新款 iPhone 15 Pro 售价...
```

---

## 📊 技术方案对比

### 方案 1：DuckDuckGo 搜索（推荐）

**库**：`duckduckgo-search`

**优点**：
- ✅ 完全免费
- ✅ 无需 API Key
- ✅ 安装简单：`pip install duckduckgo-search`
- ✅ 支持中文搜索

**缺点**：
- ⚠️ 可能被限流
- ⚠️ 结果质量一般

**代码示例**：
```python
from duckduckgo_search import DDGS

def search_web(query: str):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
    return results
```

---

### 方案 2：SerpAPI（付费但质量高）

**库**：`google-search-results`

**优点**：
- ✅ 结果质量高（直接用 Google）
- ✅ 稳定可靠
- ✅ 支持多种搜索引擎

**缺点**：
- ❌ 需要付费（免费版每月 100 次）
- ❌ 需要注册获取 API Key

**代码示例**：
```python
from serpapi import GoogleSearch

params = {
    "q": query,
    "api_key": "your_api_key"
}
search = GoogleSearch(params)
results = search.get_dict()
```

---

### 方案 3：Requests + 爬虫（不推荐）

**优点**：
- ✅ 完全免费

**缺点**：
- ❌ 容易被封 IP
- ❌ 需要解析 HTML
- ❌ 不稳定
- ❌ 可能违反服务条款

---

## 🎯 选择方案 1：DuckDuckGo

**原因**：
- 学习项目，免费最重要
- 安装简单，无需配置
- 功能足够用

---

## 🔧 实现步骤

### 第 1 步：安装依赖

```bash
pip install duckduckgo-search
```

更新 `requirements.txt`：
```
PySide6>=6.5.0
openai>=1.0.0
PyYAML>=6.0
duckduckgo-search>=4.0.0
```

---

### 第 2 步：创建搜索函数

在 `main.py` 中添加：

```python
def search_web(query: str, max_results: int = 5) -> str:
    """
    搜索网络
    
    参数：
        query: 搜索关键词
        max_results: 最多返回多少条结果
    
    返回：
        格式化的搜索结果文本
    """
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
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
        return f"搜索失败：{repr(e)}"
```

---

### 第 3 步：在 AIClient 中添加 web_search 工具

```python
self.tools = [
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "设置一个定时提醒",
            "parameters": {
                # ... 已有的 set_reminder 参数
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索网络获取最新信息。当用户询问实时信息、新闻、天气、价格等需要联网查询的内容时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，例如：北京天气、iPhone 15 价格、今日新闻"
                    }
                },
                "required": ["query"]
            }
        }
    }
]
```

---

### 第 4 步：处理 web_search 工具调用

在 `_handle_tool_calls()` 中添加：

```python
def _handle_tool_calls(self, tool_calls: list):
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        
        if tool_name == "set_reminder":
            # ... 已有的提醒逻辑
        
        elif tool_name == "web_search":
            # 解析参数
            import json
            params = json.loads(tool_call["arguments"])
            query = params.get("query", "")
            
            # 显示搜索提示
            self.append_message("AI", f"🔍 正在搜索：{query}...")
            
            # 执行搜索
            search_results = search_web(query)
            
            # 显示搜索结果
            result_text = f"搜索结果：\n\n{search_results}"
            self.append_message("AI", result_text)
            self.chat_history.add_message("assistant", result_text)
```

---

### 第 5 步：优化系统提示词

```yaml
system_prompt: "你是一个友好的 AI 助手，用简洁友好的语言回答用户的问题。当用户需要设置提醒时，使用 set_reminder 工具。当用户询问需要联网查询的实时信息（如天气、新闻、价格等）时，使用 web_search 工具搜索后再回答。"
```

---

## 🧪 测试场景

### 场景 1：天气查询
```
用户：今天北京天气怎么样？
预期：AI 调用 web_search("北京天气") → 显示搜索结果
```

### 场景 2：价格查询
```
用户：iPhone 15 多少钱？
预期：AI 调用 web_search("iPhone 15 价格") → 显示搜索结果
```

### 场景 3：新闻查询
```
用户：今天有什么新闻？
预期：AI 调用 web_search("今日新闻") → 显示搜索结果
```

### 场景 4：普通对话（不需要搜索）
```
用户：你好
预期：AI 直接回复，不调用搜索
```

---

## 💡 优化方向

### 优化 1：二次总结

搜索后不直接显示原始结果，而是让 AI 总结：

```python
# 1. 搜索
search_results = search_web(query)

# 2. 把搜索结果告诉 AI
messages.append({
    "role": "tool",
    "tool_call_id": tool_call["id"],
    "content": search_results
})

# 3. 让 AI 总结
response = self.ai_client.chat(messages)
summary = response["content"]

# 4. 显示 AI 的总结
self.append_message("AI", summary)
```

---

### 优化 2：缓存搜索结果

避免重复搜索相同内容：

```python
search_cache = {}

if query in search_cache:
    results = search_cache[query]
else:
    results = search_web(query)
    search_cache[query] = results
```

---

### 优化 3：搜索历史

记录搜索历史，方便回顾：

```json
{
    "searches": [
        {
            "query": "北京天气",
            "timestamp": "2026-06-20T10:30:00",
            "results": "..."
        }
    ]
}
```

---

## 📚 关键知识点

### 1. DuckDuckGo 搜索结果格式

```python
[
    {
        'title': '结果标题',
        'body': '结果摘要',
        'href': 'https://example.com'
    },
    ...
]
```

---

### 2. 多工具协作

一个 AI 可以同时拥有多个工具：

```python
tools = [
    set_reminder,  # 提醒工具
    web_search,    # 搜索工具
    calculator,    # 计算器（未来添加）
]
```

AI 会根据用户意图选择合适的工具。

---

## 🚀 下一步

1. 安装 `duckduckgo-search`
2. 创建 `search_web()` 函数
3. 添加 `web_search` 工具定义
4. 实现工具调用处理
5. 测试功能
6. 编写完整文档

---

**预计开发时间**：1-2 小时  
**难度**：⭐⭐⭐（中等）
