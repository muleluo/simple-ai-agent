# 联网搜索功能优化 - 说明文档

**功能版本**：v2.1  
**更新日期**：2026-06-23  
**状态**：✅ 已完成

---

## 🎯 解决的问题

### 问题 1：AI 每次都调用搜索
**原因**：工具始终在工具列表中，AI 会频繁调用  
**解决**：添加联网搜索开关，默认关闭

### 问题 2：搜索结果未经整理
**原因**：直接显示原始搜索结果，AI 没有参与  
**解决**：搜索结果返回给 AI，由 AI 整理后再显示

### 问题 3：缺少用户控制
**需求**：用户希望控制是否启用联网搜索  
**解决**：在设置菜单中添加开关

---

## ✅ 新增功能

### 1. 联网搜索开关

**位置**：⚙️ 设置 → 🌐 联网搜索

**状态**：
- ✅ 启用 - AI 可以使用联网搜索
- ❌ 禁用 - AI 无法使用联网搜索（默认）

**操作**：
```
点击 "⚙️ 设置" → 点击 "🌐 联网搜索"
→ 系统提示：✅ 已启用联网搜索 / ❌ 已禁用联网搜索
```

### 2. AI 整理搜索结果

**新流程**：
```
用户提问
    ↓
AI 判断是否需要搜索
    ↓ 需要
执行搜索（如果已启用）
    ↓
搜索结果返回给 AI
    ↓
AI 整理分析搜索结果
    ↓
显示 AI 整理后的回答
```

**旧流程**（已废弃）：
```
用户提问
    ↓
AI 判断需要搜索
    ↓
执行搜索
    ↓
直接显示原始搜索结果
```

---

## 🔧 技术实现

### 1. 动态工具列表

**文件**：`main.py` → `_get_enabled_tools()` 方法

```python
def _get_enabled_tools(self) -> list:
    """
    根据设置获取启用的工具列表
    """
    tools = []

    # 提醒工具（始终启用）
    tools.append({...})

    # 联网搜索工具（可选）
    if self.web_search_enabled:
        tools.append({...})

    # 知识库搜索（始终启用）
    tools.append({...})

    return tools
```

**逻辑**：
- 提醒工具 - 始终启用
- 联网搜索 - 根据开关状态
- 知识库搜索 - 始终启用

### 2. 新的工作线程类

**文件**：`main.py` → `ChatWorkerWithTools` 类

**职责**：
1. 调用 AI API
2. 如果 AI 调用工具，执行工具
3. 将工具结果返回给 AI
4. AI 整理后返回最终结果

**关键代码**：
```python
# 第一次调用 AI
response = client.chat.completions.create(...)

# 如果 AI 调用工具
if message.tool_calls:
    # 执行工具（搜索、知识库等）
    tool_results = execute_tools(...)
    
    # 将工具结果添加到消息列表
    messages.append(assistant_message)
    messages.append(tool_results)
    
    # 再次调用 AI，让它整理结果
    response2 = client.chat.completions.create(...)
    
    # 返回 AI 整理后的结果
    return response2.message.content
```

### 3. 提醒工具的特殊处理

**问题**：提醒需要在主线程设置 QTimer

**解决**：
```python
# 在工作线程中
if tool_name == "set_reminder":
    pending_reminders.append({"minutes": ..., "message": ...})
    # 返回确认消息给 AI

# 在主线程中（handle_ai_reply）
if "pending_reminders" in reply:
    for reminder_data in reply["pending_reminders"]:
        self.reminder_manager.add_reminder(...)
        self._start_reminder_timer(...)
```

---

## 📊 使用示例

### 示例 1：联网搜索已禁用

**场景**：用户问 "今天天气怎么样？"

**流程**：
```
用户：今天天气怎么样？
    ↓
AI 判断：需要搜索天气
    ↓
检查：联网搜索已禁用
    ↓
AI：抱歉，我无法查询实时天气信息。你可以在设置中启用联网搜索功能。
```

### 示例 2：联网搜索已启用

**场景**：用户问 "物语系列人气最高的是谁？"

**流程**：
```
用户：物语系列人气最高的是谁？
    ↓
AI 判断：需要搜索
    ↓
检查：联网搜索已启用
    ↓
执行搜索：search_web("物语系列人气角色")
    ↓
搜索结果（原始）：
  1. 物语系列角色列表 - 维基百科...
  2. 日本网民票选...
  3. 物语系列角色热度排行榜...
    ↓
AI 整理：
根据搜索结果，物语系列中人气最高的角色是**忍野忍**，在多次投票中都位居榜首。
其次是千石抚子和战场原黑仪。这些角色因其独特的性格和故事深受粉丝喜爱。
    ↓
显示 AI 整理后的回答
```

### 示例 3：提醒功能

**场景**：用户说 "5分钟后提醒我喝水"

**流程**：
```
用户：5分钟后提醒我喝水
    ↓
AI 判断：需要设置提醒
    ↓
调用 set_reminder 工具
    ↓
工作线程：记录 pending_reminders
    ↓
AI 整理：好的！我已经为你设置了 5 分钟后的提醒：喝水 ⏰
    ↓
主线程：实际设置 QTimer
    ↓
5 分钟后弹出提醒
```

---

## 🎨 界面变化

### 设置菜单

**修改前**：
```
⚙️ 设置
├── 📚 上传到知识库
```

**修改后**：
```
⚙️ 设置
├── 📚 上传到知识库
├── 🌐 联网搜索 ☐  （可勾选）
```

### 系统提示

**启用联网搜索**：
```
系统：✅ 已启用联网搜索
```

**禁用联网搜索**：
```
系统：❌ 已禁用联网搜索
```

---

## 💡 优点与改进

### 优点

1. ✅ **用户控制** - 用户可以决定是否启用联网搜索
2. ✅ **结果质量** - AI 整理后的结果更准确、更易读
3. ✅ **减少误触发** - 默认关闭，避免不必要的搜索
4. ✅ **节省成本** - 减少 API 调用次数
5. ✅ **更好体验** - AI 回答而不是原始搜索结果

### 对比

| 维度 | 旧版本 | 新版本 |
|------|--------|--------|
| 搜索控制 | 无法控制 | 可通过开关控制 |
| 结果展示 | 原始搜索结果 | AI 整理后的回答 |
| 默认状态 | 始终启用 | 默认禁用 |
| 用户体验 | 信息过载 | 精准回答 |
| API 调用 | 每次2次 | 关闭时0次，开启时2次 |

---

## 🔮 未来改进

### 1. 搜索来源选择

**功能**：允许用户选择搜索引擎

**实现思路**：
```python
search_engines = {
    "duckduckgo": search_web_ddg,
    "google": search_web_google,
    "bing": search_web_bing
}
```

### 2. 搜索结果缓存

**功能**：相同查询在一定时间内使用缓存结果

**实现思路**：
```python
search_cache = {}  # {query: (result, timestamp)}

def search_with_cache(query):
    if query in search_cache:
        result, timestamp = search_cache[query]
        if time.time() - timestamp < 3600:  # 1小时内
            return result
    # 执行搜索并缓存
```

### 3. 搜索历史记录

**功能**：记录所有搜索查询，方便用户查看

**实现思路**：
```python
search_history = []

def log_search(query, results):
    search_history.append({
        "query": query,
        "timestamp": datetime.now(),
        "result_count": len(results)
    })
```

### 4. 搜索深度控制

**功能**：允许用户设置返回结果数量

**实现思路**：
```python
# 在设置中添加
search_depth = QSpinBox()
search_depth.setRange(1, 10)
search_depth.setValue(5)
```

---

## 📝 配置说明

### 默认配置

```python
# main.py
self.web_search_enabled = False  # 默认关闭
```

### 修改默认值

如果希望默认启用联网搜索：

```python
# main.py → __init__()
self.web_search_enabled = True  # 修改为 True
```

---

## 🐛 故障排查

### 问题 1：开关无效

**现象**：切换开关后仍无法搜索

**排查**：
1. 检查 `self.web_search_enabled` 的值
2. 检查 `_get_enabled_tools()` 是否正确返回工具列表
3. 重启程序

### 问题 2：搜索结果仍是原始格式

**现象**：显示的是原始搜索结果，没有 AI 整理

**原因**：使用了旧的 `ChatWorker` 而不是 `ChatWorkerWithTools`

**解决**：检查 `send_message()` 中是否使用了 `ChatWorkerWithTools`

### 问题 3：提醒无法设置

**现象**：AI 说已设置提醒，但实际没有

**原因**：`pending_reminders` 没有正确传递

**排查**：
1. 检查 `ChatWorkerWithTools` 是否返回了 `pending_reminders`
2. 检查 `handle_ai_reply` 是否处理了 `pending_reminders`

---

## 📖 相关文档

- [会话管理功能](./session_management.md)
- [错误日志](../logs/error_log.md)
- [配置文件](../config.yaml)

---

**维护者**：开发团队  
**最后更新**：2026-06-23
