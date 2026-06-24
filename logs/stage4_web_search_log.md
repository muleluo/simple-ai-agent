# 阶段 4：联网搜索功能

**日期**：2026-06-20  
**功能**：让 AI 能搜索网络获取实时信息  
**技术**：DuckDuckGo Search + Function Calling  
**状态**：✅ 已完成

---

## 🎯 目标

**之前**：AI 只能根据训练数据回答，无法获取实时信息

**现在**：AI 可以主动搜索网络，获取最新信息

**用户体验**：
```
用户：今天北京天气怎么样？
AI：🔍 正在搜索：北京天气...
AI：📋 搜索结果：
    1. 北京天气预报...
    2. ...

用户：iPhone 15 多少钱？
AI：🔍 正在搜索：iPhone 15 价格...
AI：📋 搜索结果：...
```

---

## 📊 技术选型

### 为什么选择 DuckDuckGo？

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| **DuckDuckGo** | 完全免费、无需 API Key、支持中文 | 可能被限流 | ✅ 选择 |
| SerpAPI | 结果质量高、稳定 | 需要付费 | ❌ |
| 爬虫 | 免费 | 容易被封、不稳定 | ❌ |

---

## 🔧 实现步骤

### 步骤 1：安装依赖

```bash
pip install duckduckgo-search
```

更新 `requirements.txt`：
```
duckduckgo-search>=4.0.0
```

---

### 步骤 2：创建搜索函数

在 `main.py` 中添加全局函数：

```python
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
        from duckduckgo_search import DDGS
        
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
        return f"搜索失败：{repr(e)}"
```

**关键点**：
- `DDGS()` 是 DuckDuckGo 搜索客户端
- `ddgs.text()` 执行文本搜索
- `with` 语句确保资源正确释放
- 返回格式化的文本，方便显示

---

### 步骤 3：添加工具定义

在 `AIClient.__init__()` 中添加：

```python
self.tools = [
    # ... set_reminder 工具
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索网络获取最新信息。当用户询问实时信息、新闻、天气、价格、当前事件等需要联网查询的内容时使用。",
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

**重点**：
- `description` 告诉 AI 什么时候该用这个工具
- `query` 参数是必需的
- 例子帮助 AI 理解如何构造搜索词

---

### 步骤 4：处理工具调用

在 `_handle_tool_calls()` 中添加：

```python
elif tool_name == "web_search":
    # 解析参数
    import json
    try:
        params = json.loads(tool_call["arguments"])
        query = params.get("query", "")
        
        # 显示搜索提示
        self.append_message("AI", f"🔍 正在搜索：{query}...")
        
        # 执行搜索
        search_results = search_web(query)
        
        # 显示搜索结果
        result_text = f"📋 搜索结果：\n\n{search_results}"
        self.append_message("AI", result_text)
        self.chat_history.add_message("assistant", result_text)
    
    except Exception as e:
        # 如果出错，显示错误
        error_msg = f"搜索失败：{repr(e)}"
        self.append_message("AI", error_msg)
        self.chat_history.add_message("assistant", error_msg)
```

**流程**：
1. 解析 AI 传来的参数
2. 显示"正在搜索..."提示
3. 调用 `search_web()` 执行搜索
4. 显示搜索结果
5. 保存到历史记录

---

### 步骤 5：更新系统提示词

```yaml
system_prompt: "你是一个友好的 AI 助手，用简洁友好的语言回答用户的问题。当用户需要设置提醒时，使用 set_reminder 工具。当用户询问需要联网查询的实时信息（如天气、新闻、价格、当前事件等）时，使用 web_search 工具搜索后再回答。"
```

**作用**：明确告诉 AI 何时使用搜索工具

---

## 📚 核心知识点

### 1. DuckDuckGo 搜索 API

```python
from duckduckgo_search import DDGS

with DDGS() as ddgs:
    # 文本搜索
    results = ddgs.text("搜索词", max_results=5)
    
    # 新闻搜索
    news = ddgs.news("搜索词", max_results=5)
    
    # 图片搜索
    images = ddgs.images("搜索词", max_results=10)
```

---

### 2. 搜索结果格式

```python
[
    {
        'title': '结果标题',
        'body': '结果摘要（200-300 字）',
        'href': 'https://example.com'
    },
    ...
]
```

---

### 3. with 语句（上下文管理器）

```python
# ✅ 推荐：自动释放资源
with DDGS() as ddgs:
    results = ddgs.text("查询")
# 执行完后自动关闭连接

# ❌ 不推荐：需要手动关闭
ddgs = DDGS()
results = ddgs.text("查询")
ddgs.close()  # 容易忘记
```

---

### 4. enumerate() 函数

```python
items = ['a', 'b', 'c']

# 方式 1：手动计数
index = 1
for item in items:
    print(f"{index}. {item}")
    index += 1

# 方式 2：enumerate（推荐）
for i, item in enumerate(items, 1):  # 从 1 开始计数
    print(f"{i}. {item}")
```

---

### 5. 字符串 join() 方法

```python
lines = ["第一行", "第二行", "第三行"]

# 用换行符连接
text = "\n".join(lines)
# 结果：
# 第一行
# 第二行
# 第三行
```

---

## 🧪 测试场景

### 场景 1：天气查询

```
输入：今天北京天气怎么样？
预期：
  1. AI 检测需要搜索
  2. 调用 web_search("北京天气")
  3. 显示搜索结果
```

---

### 场景 2：价格查询

```
输入：iPhone 15 Pro 多少钱？
预期：
  1. AI 调用 web_search("iPhone 15 Pro 价格")
  2. 显示最新价格信息
```

---

### 场景 3：新闻查询

```
输入：今天有什么新闻？
预期：
  1. AI 调用 web_search("今日新闻")
  2. 显示新闻列表
```

---

### 场景 4：普通对话

```
输入：你好，你是谁？
预期：
  1. AI 直接回答
  2. 不调用搜索工具
```

---

## 💡 优化方向

### 优化 1：AI 总结搜索结果（推荐）

**当前问题**：直接显示原始搜索结果，太长、不友好

**优化方案**：让 AI 总结搜索结果

```python
elif tool_name == "web_search":
    params = json.loads(tool_call["arguments"])
    query = params.get("query", "")
    
    # 1. 显示提示
    self.append_message("AI", f"🔍 正在搜索：{query}...")
    
    # 2. 执行搜索
    search_results = search_web(query)
    
    # 3. 把搜索结果告诉 AI
    messages = self.chat_history.get_messages_for_api()
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": search_results
    })
    
    # 4. 让 AI 总结
    response = self.ai_client.chat([self.system_prompt] + messages)
    summary = response["content"]
    
    # 5. 显示 AI 的总结
    self.append_message("AI", summary)
    self.chat_history.add_message("assistant", summary)
```

**效果**：
```
用户：今天北京天气怎么样？
AI：🔍 正在搜索：北京天气...
AI：根据搜索结果，今天北京晴天，气温 20-28°C，空气质量良好，适合户外活动。
```

---

### 优化 2：搜索缓存

避免重复搜索：

```python
# 在 SimpleAIAgent 类中添加
def __init__(self):
    # ...
    self.search_cache = {}  # 搜索缓存

def _handle_tool_calls(self, tool_calls: list):
    # ...
    elif tool_name == "web_search":
        query = params.get("query", "")
        
        # 检查缓存
        if query in self.search_cache:
            search_results = self.search_cache[query]
            self.append_message("AI", f"📋 (来自缓存) {search_results}")
        else:
            # 执行搜索
            search_results = search_web(query)
            self.search_cache[query] = search_results
            self.append_message("AI", f"📋 {search_results}")
```

---

### 优化 3：搜索历史记录

保存所有搜索记录：

```python
class SearchHistory:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.searches = []
        if self.file_path.exists():
            self.load()
    
    def add_search(self, query: str, results: str):
        search = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        self.searches.append(search)
        self.save()
    
    def save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.searches, f, ensure_ascii=False, indent=2)
    
    def load(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.searches = json.load(f)
```

---

### 优化 4：支持更多搜索类型

```python
# 新闻搜索
{
    "name": "search_news",
    "description": "搜索最新新闻"
}

# 图片搜索
{
    "name": "search_images",
    "description": "搜索图片"
}
```

---

## 🔍 常见问题

### Q1：搜索失败怎么办？

**可能原因**：
- 网络问题
- DuckDuckGo 限流
- 搜索词不合适

**解决方法**：
```python
try:
    results = search_web(query)
except Exception as e:
    # 显示友好的错误提示
    return "搜索暂时不可用，请稍后再试"
```

---

### Q2：搜索结果太多怎么办？

**调整 max_results**：
```python
# 少一点结果
search_web(query, max_results=3)

# 多一点结果
search_web(query, max_results=10)
```

---

### Q3：AI 不调用搜索怎么办？

**检查以下几点**：
1. `description` 是否清晰？
2. 系统提示词是否告诉 AI 何时搜索？
3. 用户问题是否明确需要实时信息？

**改进 description**：
```python
# ❌ 不好
"description": "搜索"

# ✅ 好
"description": "搜索网络获取最新信息。当用户询问实时信息、新闻、天气、价格、当前事件等需要联网查询的内容时使用。"
```

---

### Q4：搜索结果是英文怎么办？

**中文搜索词**：
```python
# AI 应该自动生成中文搜索词
web_search("北京天气")  # ✅ 中文结果
web_search("Beijing weather")  # ❌ 英文结果
```

**在 description 中提示**：
```python
"description": "搜索网络获取最新信息。搜索词应该用中文。"
```

---

## 📊 多工具协作

现在我们有两个工具：

```python
tools = [
    set_reminder,   # 设置提醒
    web_search,     # 搜索网络
]
```

**AI 如何选择？**

```
用户："5 分钟后提醒我查天气"
AI 分析：
  1. 需要设置提醒 → 调用 set_reminder
  2. "查天气"只是提醒内容，不是现在要查

用户："现在天气怎么样？"
AI 分析：
  1. 需要实时信息 → 调用 web_search
  2. 不需要提醒

用户："搜索一下天气，然后 10 分钟后提醒我"
AI 分析：
  1. 先调用 web_search 搜索天气
  2. 再调用 set_reminder 设置提醒
  
（注意：当前实现不支持一次调用多个工具，这是一个可优化的点）
```

---

## 🎯 架构对比

### 之前：静态知识

```
用户提问 → AI 根据训练数据回答
```

**局限**：
- 无法获取实时信息
- 知识有时效性
- 无法回答"今天"、"最新"等问题

---

### 现在：动态知识

```
用户提问 → AI 判断是否需要搜索 → 搜索 → AI 回答
```

**优势**：
- ✅ 可以获取实时信息
- ✅ 知识始终最新
- ✅ 可以回答实时问题

---

## 📖 相关资源

- **DuckDuckGo Search GitHub**：https://github.com/deedy5/duckduckgo_search
- **DuckDuckGo 官网**：https://duckduckgo.com
- **Function Calling 文档**：见 `logs/function_calling_notes.md`

---

## ✅ 完成情况

- ✅ 安装 duckduckgo-search
- ✅ 创建 search_web() 函数
- ✅ 添加 web_search 工具定义
- ✅ 实现工具调用处理
- ✅ 更新系统提示词
- ✅ 更新 requirements.txt
- ✅ 编写完整文档

---

## 🚀 下一步

### 方向 1：优化搜索体验
- 实现 AI 总结搜索结果
- 添加搜索缓存
- 添加搜索历史记录

### 方向 2：添加更多工具
- 计算器
- 天气 API（专用）
- 翻译工具

### 方向 3：文件上传分析
- 上传图片让 AI 分析
- 上传 PDF 提取内容
- 上传文档建立知识库

---

**开发时间**：1 小时  
**难度**：⭐⭐⭐（中等）  
**核心技能**：多工具管理、网络请求、错误处理

**学习重点**：如何让 AI 在多个工具间正确选择
