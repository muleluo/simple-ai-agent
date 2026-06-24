# 联网搜索功能 - 学习笔记

**日期**：2026-06-20  
**功能**：让 AI 通过对话自动搜索网络  
**状态**：✅ 已完成并测试通过

---

## 🎯 核心概念

### 1. 为什么需要联网搜索？

**AI 的局限**：
- 训练数据有时效性
- 无法获取实时信息
- 不知道"今天"、"最新"的事情

**联网搜索解决**：
- 实时查询网络
- 获取最新信息
- 回答动态问题

---

## 📚 技术选型：DDGS

### 库的演变

```python
# 旧库名（已废弃）
from duckduckgo_search import DDGS

# 新库名（推荐）
from ddgs import DDGS
```

**为什么选择 DuckDuckGo？**
- ✅ 完全免费
- ✅ 无需 API Key
- ✅ 安装简单
- ✅ 支持中文搜索

---

## 🔧 实现步骤

### 步骤 1：安装库

```bash
pip install ddgs
```

---

### 步骤 2：创建搜索函数

```python
def search_web(query: str, max_results: int = 5) -> str:
    """搜索网络"""
    from ddgs import DDGS
    
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    
    # 格式化结果
    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(
            f"{i}. {result['title']}\n"
            f"   {result['body']}\n"
            f"   来源：{result['href']}\n"
        )
    
    return "\n".join(formatted)
```

**关键点**：
- `DDGS()` 是搜索客户端
- `ddgs.text()` 执行文本搜索
- `with` 语句自动释放资源
- 返回格式化的字符串

---

### 步骤 3：添加工具定义

```python
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
                    "description": "搜索关键词"
                }
            },
            "required": ["query"]
        }
    }
}
```

---

### 步骤 4：处理工具调用

```python
elif tool_name == "web_search":
    params = json.loads(tool_call["arguments"])
    query = params.get("query", "")
    
    # 显示提示
    self.append_message("AI", f"🔍 正在搜索：{query}...")
    
    # 执行搜索
    search_results = search_web(query)
    
    # 显示结果
    result_text = f"📋 搜索结果：\n\n{search_results}"
    self.append_message("AI", result_text)
```

---

## 💡 重要知识点

### 1. with 语句（上下文管理器）

```python
# ✅ 推荐：自动释放资源
with DDGS() as ddgs:
    results = ddgs.text("查询")
# 退出 with 块后自动关闭连接

# ❌ 不推荐：需要手动关闭
ddgs = DDGS()
results = ddgs.text("查询")
ddgs.close()  # 容易忘记
```

**什么是上下文管理器？**
- 自动管理资源（文件、网络连接等）
- 进入时：初始化资源
- 退出时：自动释放资源
- 即使出错也会正确清理

**常见例子**：
```python
# 文件操作
with open('file.txt', 'r') as f:
    content = f.read()
# 自动关闭文件

# 网络请求
with DDGS() as ddgs:
    results = ddgs.text("查询")
# 自动关闭连接
```

---

### 2. enumerate() 函数

```python
items = ['苹果', '香蕉', '橙子']

# 方式 1：手动计数（不推荐）
index = 1
for item in items:
    print(f"{index}. {item}")
    index += 1

# 方式 2：enumerate（推荐）
for i, item in enumerate(items, 1):  # 从 1 开始
    print(f"{i}. {item}")

# 输出：
# 1. 苹果
# 2. 香蕉
# 3. 橙子
```

**参数说明**：
- 第一个参数：可迭代对象（列表、元组等）
- 第二个参数：起始数字（默认 0）

---

### 3. 重试机制

```python
for attempt in range(3):  # 最多尝试 3 次
    try:
        # 尝试操作
        result = do_something()
        return result  # 成功就返回
    except Exception as e:
        if attempt == 2:  # 最后一次尝试
            return "失败"
        time.sleep(1)  # 等待 1 秒后重试
```

**为什么需要重试？**
- 网络请求可能暂时失败
- 服务可能暂时不可用
- 提高成功率

**注意事项**：
- 不要无限重试
- 每次重试间隔等待
- 最终要返回错误

---

### 4. 错误处理的层级

```python
try:
    # 外层：捕获所有错误
    try:
        # 内层：捕获特定错误
        results = search()
    except SpecificError:
        # 处理特定错误
        handle_specific()
except Exception as e:
    # 处理所有其他错误
    handle_all()
```

---

### 5. 搜索结果数据结构

```python
# DuckDuckGo 返回的格式
[
    {
        'title': '结果标题',
        'body': '结果摘要（200-300字）',
        'href': 'https://example.com'
    },
    ...
]
```

---

## 🐛 问题排查

### 问题 1：库名错误

**现象**：
```
ImportError: No module named 'duckduckgo_search'
```

**原因**：
- 旧库名 `duckduckgo-search` 已废弃
- 新库名是 `ddgs`

**解决**：
```bash
pip uninstall duckduckgo-search
pip install ddgs
```

---

### 问题 2：网络连接错误

**现象**：
```
ConnectError: peer misbehaved
```

**原因**：
- 网络问题
- SSL/TLS 握手失败
- 防火墙阻止

**解决**：
1. 检查网络连接
2. 添加重试机制
3. 友好的错误提示

---

### 问题 3：搜索返回 None

**现象**：
```
return None
```

**原因**：
- 搜索关键词问题
- 服务暂时不可用

**解决**：
```python
if not results:
    return "未找到相关结果"
```

---

## 🎯 多工具管理

### 现在我们有两个工具

```python
tools = [
    set_reminder,  # 设置提醒
    web_search,    # 搜索网络
]
```

### AI 如何选择工具？

**根据 description 判断**：

```
用户："5 分钟后提醒我"
AI：检测到"提醒" → 选择 set_reminder

用户："今天天气怎么样？"
AI：检测到需要"实时信息" → 选择 web_search

用户："你好"
AI：普通对话 → 不选择工具
```

---

## 📝 最佳实践

### 1. 清晰的工具描述

```python
# ❌ 不好
"description": "搜索"

# ✅ 好
"description": "搜索网络获取最新信息。当用户询问实时信息、新闻、天气、价格等需要联网查询的内容时使用。"
```

---

### 2. 友好的用户提示

```python
# 显示正在搜索
self.append_message("AI", f"🔍 正在搜索：{query}...")

# 显示搜索结果
self.append_message("AI", f"📋 搜索结果：\n\n{results}")
```

---

### 3. 完整的错误处理

```python
try:
    results = search_web(query)
except Exception as e:
    error_msg = f"搜索失败：{str(e)[:200]}"
    self.append_message("AI", error_msg)
```

---

## 🚀 可能的优化

### 优化 1：AI 总结结果

当前直接显示原始搜索结果，可以让 AI 总结后再显示。

---

### 优化 2：搜索缓存

避免重复搜索相同内容。

---

### 优化 3：搜索历史

记录所有搜索，方便回顾。

---

## 📊 学习进度

- ✅ 阶段 1：基础对话功能
- ✅ 阶段 2：提醒功能
- ✅ 阶段 3：AI 自动设置提醒（Function Calling）
- ✅ 阶段 4：联网搜索功能

---

## 🎓 今日收获

### 新概念

1. **上下文管理器（with 语句）**
2. **enumerate() 函数**
3. **重试机制**
4. **多工具管理**
5. **错误处理层级**

### 新技能

1. 集成第三方搜索 API
2. 处理网络错误
3. 格式化搜索结果
4. 管理多个 AI 工具

---

**下次学习方向**：
- 文件上传分析（图片、PDF）
- 知识库（RAG）
- 更多 AI 工具

**今日完成时间**：2026-06-20  
**总开发时间**：约 5 小时  
**完成功能**：4 个主要功能

---

**做得很好！🎉**
