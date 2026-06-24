# Function Calling 学习笔记

**日期**：2026-06-17  
**功能**：让 AI 能通过对话调用工具（如设置提醒）  
**技术**：OpenAI Function Calling

---

## 🎯 什么是 Function Calling？

**传统对话**：
```
用户：5 分钟后提醒我喝水
AI：好的，我会提醒你的（但实际上做不到）
```

**有 Function Calling**：
```
用户：5 分钟后提醒我喝水
AI：[调用 set_reminder(minutes=5, message="喝水")]
程序：执行提醒设置
AI：好的，我已经为你设置了 5 分钟后的提醒 ⏰
```

---

## 📚 核心概念

### 1. 定义工具（Tool Definition）

告诉 AI："你可以用这些工具"

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "set_reminder",              # 工具名称
            "description": "设置一个定时提醒",   # 工具的作用
            "parameters": {                      # 参数定义
                "type": "object",
                "properties": {
                    "minutes": {
                        "type": "integer",
                        "description": "多少分钟后提醒"
                    },
                    "message": {
                        "type": "string",
                        "description": "提醒的内容"
                    }
                },
                "required": ["minutes", "message"]  # 必需参数
            }
        }
    }
]
```

**关键点**：
- `name`：方法名（后面程序会根据这个名字执行）
- `description`：AI 会根据这个描述判断是否该用这个工具
- `parameters`：遵循 JSON Schema 格式

---

### 2. AI 的决策过程

```
用户输入："5 分钟后提醒我喝水"
    ↓
AI 分析：
  - 用户想设置提醒 ✓
  - 有一个叫 set_reminder 的工具 ✓
  - 参数：minutes=5, message="喝水" ✓
    ↓
AI 返回：
  {
    "tool_calls": [
      {
        "id": "call_abc123",
        "name": "set_reminder",
        "arguments": '{"minutes": 5, "message": "喝水"}'
      }
    ]
  }
```

**注意**：
- AI **不会真的执行**工具
- AI 只是**告诉你它想调用什么**
- 你的程序负责真正执行

---

### 3. 完整流程

```
第一轮：
  用户 → "5 分钟后提醒我喝水"
  AI   → tool_call: set_reminder(5, "喝水")

程序执行：
  reminder_manager.add_reminder(5, "喝水")
  result = "提醒已设置"

第二轮：
  程序 → 告诉 AI："工具执行成功，result=提醒已设置"
  AI   → "好的，我已经为你设置了 5 分钟后的喝水提醒 ⏰"
  
显示给用户：
  "好的，我已经为你设置了 5 分钟后的喝水提醒 ⏰"
```

---

## 🔧 代码实现

### 步骤 1：定义工具

```python
self.tools = [
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "设置一个定时提醒",
            "parameters": {
                "type": "object",
                "properties": {
                    "minutes": {
                        "type": "integer",
                        "description": "多少分钟后提醒"
                    },
                    "message": {
                        "type": "string",
                        "description": "提醒的内容"
                    }
                },
                "required": ["minutes", "message"]
            }
        }
    }
]
```

---

### 步骤 2：调用 API 时传递工具

```python
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages,
    tools=self.tools  # ← 关键：告诉 AI 可用的工具
)
```

---

### 步骤 3：检查 AI 是否想调用工具

```python
message = response.choices[0].message

# 如果 AI 想调用工具
if message.tool_calls:
    for tool_call in message.tool_calls:
        name = tool_call.function.name
        arguments = tool_call.function.arguments  # JSON 字符串
        
        # 解析参数
        import json
        params = json.loads(arguments)
        
        # 根据工具名执行
        if name == "set_reminder":
            minutes = params["minutes"]
            message_text = params["message"]
            # 执行真正的提醒设置
            reminder_manager.add_reminder(minutes, message_text)
```

---

### 步骤 4：告诉 AI 工具执行结果

需要再调用一次 API，把结果告诉 AI：

```python
# 第二次调用
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": "提醒设置成功"
})

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages
)

# 这次 AI 会回复用户
final_reply = response.choices[0].message.content
```

---

## 📊 数据结构

### AI 的回复格式

```python
{
    "content": "让我帮你设置提醒",  # 可能为空
    "tool_calls": [
        {
            "id": "call_abc123",
            "name": "set_reminder",
            "arguments": '{"minutes": 5, "message": "喝水"}'
        }
    ]
}
```

### 工具执行结果消息

```python
{
    "role": "tool",
    "tool_call_id": "call_abc123",
    "content": "提醒设置成功"
}
```

---

## 💡 常见问题

### Q1：AI 什么时候会调用工具？

**看 `description` 是否匹配**：

```python
# 好的描述（清晰明确）
"description": "设置一个定时提醒"

# 不好的描述（太模糊）
"description": "做一些事情"
```

**用户输入匹配度**：
- "5 分钟后提醒我" → 高匹配 ✓
- "你好" → 不匹配，不会调用工具

---

### Q2：如果 AI 判断错了怎么办？

**AI 可能会**：
- 该调用工具时不调用
- 不该调用时乱调用
- 参数解析错误

**解决方法**：
- 改进 `description`（更详细）
- 在系统提示词中说明工具用法
- 添加参数验证

---

### Q3：为什么要调用两次 API？

```
第一次：获取 AI 想调用什么工具
程序：执行工具
第二次：把执行结果告诉 AI，让 AI 生成最终回复
```

**为什么不能一次？**
- AI 不能直接执行代码
- 需要程序在中间执行真正的操作
- 再把结果反馈给 AI

---

## 🎯 我们的实现流程

```
用户输入
    ↓
ChatWorker 调用 AI（第一次）
    ↓
AI 返回：tool_call: set_reminder(5, "喝水")
    ↓
ChatWorker 检测到工具调用
    ↓
执行：reminder_manager.add_reminder(5, "喝水")
    ↓
再次调用 AI（第二次），传入执行结果
    ↓
AI 返回：文字回复给用户
    ↓
显示在界面
```

---

## 📖 相关资源

- **OpenAI 官方文档**：搜索 "OpenAI Function Calling"
- **JSON Schema**：https://json-schema.org/
- **调试技巧**：打印 `tool_calls`，看 AI 返回了什么

---

**下一步**：修改 `ChatWorker`，让它能处理工具调用
