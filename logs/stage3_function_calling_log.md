# 阶段 3：AI 自动设置提醒（Function Calling）

**日期**：2026-06-20  
**功能**：让 AI 通过对话自动调用工具设置提醒  
**技术**：OpenAI Function Calling  
**状态**：✅ 已完成

---

## 🎯 目标

**之前的方式**：
- 用户点击"⏰ 提醒"按钮
- 弹出输入框，手动输入分钟数
- 设置提醒

**现在的方式**：
- 用户直接说："5 分钟后提醒我喝水"
- AI 自动理解并设置提醒
- 无需点击按钮，无需手动输入

---

## 📊 核心概念：Function Calling

### 什么是 Function Calling？

让 AI 能够"调用工具"——但 AI 本身不能执行代码，它只是**告诉你它想调用什么工具**。

**完整流程**：

```
用户："5 分钟后提醒我喝水"
    ↓
程序发送给 AI（第一次 API 调用）
    ↓
AI 分析：用户想设置提醒
    ↓
AI 返回：{
    "tool_calls": [
        {
            "name": "set_reminder",
            "arguments": '{"minutes": 5, "message": "喝水"}'
        }
    ]
}
    ↓
程序检测到工具调用
    ↓
程序执行：reminder_manager.add_reminder(5, "喝水")
    ↓
显示确认消息："好的！我已经为你设置了 5 分钟后的提醒：喝水 ⏰"
```

---

## 🔧 实现步骤

### 步骤 1：定义工具（AIClient 类）

告诉 AI："你可以用这个工具"

```python
self.tools = [
    {
        "type": "function",
        "function": {
            "name": "set_reminder",              # 工具名称
            "description": "设置一个定时提醒",   # AI 根据这个判断是否该用
            "parameters": {
                "type": "object",
                "properties": {
                    "minutes": {
                        "type": "integer",
                        "description": "多少分钟后提醒，例如：5 表示 5 分钟后"
                    },
                    "message": {
                        "type": "string",
                        "description": "提醒的内容，例如：喝水、休息、开会等"
                    }
                },
                "required": ["minutes", "message"]
            }
        }
    }
]
```

**关键点**：
- `description` 越详细，AI 判断越准确
- `parameters` 遵循 JSON Schema 格式
- `required` 指定必需的参数

---

### 步骤 2：修改 chat() 方法

让它返回 dict 而不是 str：

```python
def chat(self, messages: list) -> dict:
    # ...
    response = client.chat.completions.create(
        model=self.model,
        messages=encoded_messages,
        tools=self.tools,  # ← 关键：传递工具定义
        temperature=self.temperature,
        max_tokens=self.max_tokens
    )
    
    message = response.choices[0].message
    
    result = {
        "content": message.content or "",
        "tool_calls": []
    }
    
    # 如果 AI 想调用工具
    if message.tool_calls:
        for tool_call in message.tool_calls:
            result["tool_calls"].append({
                "id": tool_call.id,
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments  # JSON 字符串
            })
    
    return result
```

---

### 步骤 3：修改 ChatWorker 线程

改变信号类型，从 `Signal(str)` 到 `Signal(dict)`：

```python
class ChatWorker(QThread):
    finished = Signal(dict)  # ← 改成 dict
    
    def run(self):
        reply = self.ai_client.chat(self.messages)
        self.finished.emit(reply)  # 发送 dict
```

**为什么要改？**
- 之前只返回文本：`"你好！有什么可以帮你的？"`
- 现在要返回完整信息：
  ```python
  {
      "content": "让我帮你设置提醒",
      "tool_calls": [...]
  }
  ```

---

### 步骤 4：修改 handle_ai_reply() 方法

处理两种情况：普通回复 vs 工具调用

```python
def handle_ai_reply(self, reply: dict):
    # 检查是否有工具调用
    if reply["tool_calls"]:
        # AI 想调用工具
        self._handle_tool_calls(reply["tool_calls"])
    else:
        # 普通回复
        self.append_message("AI", reply["content"])
        self.chat_history.add_message("assistant", reply["content"])
    
    # 恢复发送按钮
    self.send_button.setEnabled(True)
    self.send_button.setText("发送")
    self.worker = None
```

---

### 步骤 5：实现工具执行逻辑

新增 `_handle_tool_calls()` 方法：

```python
def _handle_tool_calls(self, tool_calls: list):
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        
        if tool_name == "set_reminder":
            # 解析参数
            import json
            params = json.loads(tool_call["arguments"])
            minutes = params.get("minutes", 1)
            message = params.get("message", "提醒")
            
            # 执行提醒设置
            reminder = self.reminder_manager.add_reminder(minutes, message)
            self._start_reminder_timer(reminder)
            
            # 显示确认消息
            reply_text = f"好的！我已经为你设置了 {minutes} 分钟后的提醒：{message} ⏰"
            self.append_message("AI", reply_text)
            self.chat_history.add_message("assistant", reply_text)
```

**关键点**：
- `tool_call["arguments"]` 是 JSON 字符串，需要 `json.loads()` 解析
- `params.get("minutes", 1)` 提供默认值，防止出错
- 执行完工具后，手动构建回复显示给用户

---

### 步骤 6：更新数据结构

修改 `add_reminder()` 方法，支持 `message` 参数：

```python
def add_reminder(self, minutes: int, message: str = "") -> dict:
    # ...
    reminder = {
        "id": str(int(now.timestamp() * 1000)),
        "created_at": now.isoformat(),
        "due_time": due_time,
        "minutes": minutes,
        "message": message,  # ← 新增字段
        "completed": False
    }
    # ...
```

---

### 步骤 7：更新提醒显示

让提醒弹窗显示提醒内容：

```python
def _show_reminder_notification(self, reminder: dict):
    minutes = reminder["minutes"]
    message = reminder.get("message", "")
    
    if message:
        notification_text = f"⏰ 时间到了！\n\n提醒内容：{message}\n\n({minutes} 分钟已过)"
    else:
        notification_text = f"时间到了！{minutes} 分钟已过。"
    
    QMessageBox.information(self, "⏰ 提醒", notification_text)
    # ...
```

---

### 步骤 8：优化系统提示词

告诉 AI 如何使用工具：

```yaml
system_prompt: "你是一个友好的 AI 助手，用简洁友好的语言回答用户的问题。当用户需要设置提醒时，使用 set_reminder 工具来帮助他们。"
```

---

## 📚 关键知识点

### 1. JSON 字符串 vs Python 字典

```python
# AI 返回的是 JSON 字符串
arguments = '{"minutes": 5, "message": "喝水"}'

# 需要解析成 Python 字典
import json
params = json.loads(arguments)

# 现在可以访问
print(params["minutes"])  # 5
print(params["message"])  # "喝水"
```

---

### 2. dict.get() 的安全用法

```python
# ❌ 不安全：如果键不存在会报错
message = params["message"]

# ✅ 安全：提供默认值
message = params.get("message", "提醒")
```

---

### 3. Signal 类型变化的影响

```python
# 之前
finished = Signal(str)
self.finished.connect(self.handle_ai_reply)

def handle_ai_reply(self, reply: str):
    # reply 是字符串
    pass

# 之后
finished = Signal(dict)
self.finished.connect(self.handle_ai_reply)

def handle_ai_reply(self, reply: dict):
    # reply 是字典
    pass
```

**重要**：Signal 类型改变后，连接的槽函数参数类型也要改！

---

## 🧪 测试场景

### 场景 1：正常设置提醒

```
用户输入：5 分钟后提醒我喝水
预期：
  1. AI 调用 set_reminder(5, "喝水")
  2. 提醒被保存
  3. 定时器启动
  4. 显示："好的！我已经为你设置了 5 分钟后的提醒：喝水 ⏰"
  5. 5 分钟后弹出提示
```

### 场景 2：不同的时间表达

```
用户输入：10 分钟后提醒我开会
用户输入：3 分钟后提醒我休息
用户输入：1 分钟后提醒我测试
```

### 场景 3：普通对话

```
用户输入：你好
预期：AI 正常回复，不调用工具
```

### 场景 4：模糊表达

```
用户输入：待会儿提醒我一下
预期：AI 可能会询问具体时间，或使用默认值
```

---

## 🔍 调试技巧

### 打印工具调用信息

在 `_handle_tool_calls()` 开头添加：

```python
def _handle_tool_calls(self, tool_calls: list):
    print("=== AI 想调用工具 ===")
    print(f"工具数量：{len(tool_calls)}")
    for tool_call in tool_calls:
        print(f"工具名：{tool_call['name']}")
        print(f"参数：{tool_call['arguments']}")
    print("==================")
```

---

## 💡 优化建议

### 优化 1：二次确认

AI 调用工具后，再次询问 AI 生成友好的回复：

```python
# 当前版本：手动构建回复
reply_text = f"好的！我已经为你设置了 {minutes} 分钟后的提醒：{message} ⏰"

# 优化版本：让 AI 生成回复
# 1. 执行工具
reminder = self.reminder_manager.add_reminder(minutes, message)

# 2. 告诉 AI 工具执行成功
messages.append({
    "role": "tool",
    "tool_call_id": tool_call["id"],
    "content": "提醒设置成功"
})

# 3. 再次调用 AI
response = self.ai_client.chat(messages)
# AI 会生成更自然的回复
```

---

### 优化 2：参数验证

```python
if tool_name == "set_reminder":
    params = json.loads(tool_call["arguments"])
    minutes = params.get("minutes", 1)
    message = params.get("message", "提醒")
    
    # 验证参数
    if minutes < 1:
        minutes = 1
    if minutes > 60:
        minutes = 60
    
    # ...
```

---

### 优化 3：支持更多工具

```python
if tool_name == "set_reminder":
    # 设置提醒
    pass
elif tool_name == "cancel_reminder":
    # 取消提醒
    pass
elif tool_name == "list_reminders":
    # 列出所有提醒
    pass
```

---

## 📊 架构对比

### 之前：按钮驱动

```
用户点击按钮 → 输入框 → 设置提醒
```

### 现在：对话驱动

```
用户说话 → AI 理解 → 自动设置提醒
```

**好处**：
- ✅ 更自然的交互
- ✅ 不需要记住按钮在哪
- ✅ 可以处理复杂的自然语言

**挑战**：
- ⚠️ AI 可能理解错误
- ⚠️ 需要处理异常情况
- ⚠️ 需要更多的错误处理

---

## 📖 相关资源

- **OpenAI Function Calling 文档**：https://platform.openai.com/docs/guides/function-calling
- **JSON Schema 规范**：https://json-schema.org/
- **学习笔记**：`logs/function_calling_notes.md`

---

## 🎓 学到的新概念

### 1. Function Calling 机制
- AI 不执行代码，只告诉你它想调用什么
- 你的程序负责真正执行
- 执行后可以把结果再告诉 AI

### 2. JSON Schema
- 用于定义 API 参数的格式
- 包含类型、描述、必需字段等
- AI 会根据 schema 生成参数

### 3. 两阶段流程
- 第一阶段：AI 决策（想调用什么工具）
- 第二阶段：程序执行（真正执行工具）
- 可选第三阶段：AI 生成最终回复

---

## ✅ 完成情况

- ✅ 定义工具（set_reminder）
- ✅ 修改 AIClient.chat() 返回格式
- ✅ 修改 ChatWorker 信号类型
- ✅ 实现工具调用处理逻辑
- ✅ 更新数据结构（支持 message 字段）
- ✅ 优化提醒显示
- ✅ 更新系统提示词
- ✅ 编写完整文档

---

## 🚀 下一步

### 可选方向 1：完善 Function Calling
- 实现第二次 API 调用，让 AI 生成更自然的回复
- 添加更多工具（取消提醒、列出提醒等）

### 可选方向 2：添加其他功能
- 网页搜索
- 天气查询
- 计算器

### 可选方向 3：UI 改进
- 显示提醒列表
- 提醒历史记录
- 提醒编辑功能

---

**开发时间**：约 2 小时  
**难度**：⭐⭐⭐⭐（中高难度）  
**核心挑战**：理解 Function Calling 的两阶段流程

**下次学习重点**：如何实现第二次 API 调用，让 AI 生成更自然的回复
