# 会话管理功能说明

**功能版本**：v2.0  
**更新日期**：2026-06-23  
**状态**：✅ 已实现

---

## 📋 功能概述

实现了类似 ChatGPT 的会话管理功能，支持：
- ✅ 创建多个独立对话
- ✅ 保留所有历史记录
- ✅ 左侧边栏显示会话列表
- ✅ 自动生成会话标题
- ✅ 切换、重命名、删除会话

---

## 🎨 界面布局

```
┌────────────────────────────────────────────────┐
│  📝 对话历史  │  💬 和 AI 聊天                 │
├───────────────┼────────────────────────────────┤
│  + 新建对话   │                                │
├───────────────┤                                │
│ 📄 卡兹克出装 │  [聊天显示区域]                │
│ 📄 机器学习入 │                                │
│ 📄 新对话     │                                │
│               │                                │
│               ├────────────────────────────────┤
│               │ [输入框] [发送]                │
│               │ [⏰提醒][📎附加][⚙️设置][🗑️清空]│
└───────────────┴────────────────────────────────┘
```

**侧边栏占比**：1/4 宽度（250px 初始值，可拖动调整）  
**聊天区占比**：3/4 宽度（650px 初始值）

---

## 🚀 核心功能

### 1. 创建新对话

**操作方式**：点击 "+ 新建对话" 按钮

**行为**：
1. 创建新会话（ID 格式：`session_{时间戳}`）
2. 清空聊天显示区域
3. 切换到新会话
4. 在侧边栏顶部显示 "新对话"

**示例**：
```
用户点击 "+ 新建对话"
→ 系统创建 session_1782149529146
→ 显示 "系统：已创建新对话"
```

---

### 2. 自动生成标题

**触发时机**：用户在新对话中发送第一条消息

**生成逻辑**：
1. 调用 AI API（使用相同的模型）
2. 系统提示词：`"将用户的问题总结成一个简短的标题（5-10个字），只返回标题，不要其他内容。"`
3. 自动去除引号和书名号
4. 限制长度：最多 20 字（超出加 "..."）

**示例**：
```
用户输入："卡兹克怎么出装？"
→ AI 生成标题："卡兹克出装建议"
→ 侧边栏显示："📄 卡兹克出装建议"
```

**失败处理**：
- 如果 API 调用失败，使用消息的前 15 个字作为标题
- 标题生成失败不影响消息发送

---

### 3. 切换会话

**操作方式**：点击侧边栏中的会话项

**行为**：
1. 切换到选中的会话
2. 清空当前显示区域
3. 加载该会话的所有历史消息
4. 标记该项为选中状态（蓝色背景）

**技术实现**：
- 使用 `QListWidgetItem.data(Qt.ItemDataRole.UserRole)` 存储会话 ID
- 通过 `itemClicked` 信号触发切换

---

### 4. 右键菜单

**操作方式**：右键点击侧边栏中的会话项

**菜单选项**：
- ✏️ 重命名
- 🗑️ 删除

#### 重命名会话

**行为**：
1. 弹出输入框，显示当前标题
2. 用户输入新标题
3. 更新会话标题
4. 刷新侧边栏显示

**示例**：
```
当前标题："机器学习入门"
→ 右键点击 → 选择 "✏️ 重命名"
→ 修改为："ML 完整学习路线"
```

#### 删除会话

**行为**：
1. 弹出确认对话框
2. 用户确认后删除会话
3. 如果删除的是当前会话：
   - 自动切换到另一个会话
   - 如果没有其他会话，创建一个新的
4. 刷新侧边栏和显示区域

---

### 5. 清空当前对话

**操作方式**：点击 "🗑️ 清空" 按钮

**行为**：
1. 弹出确认对话框
2. 清空当前会话的所有消息
3. 清空聊天显示区域
4. **不删除会话本身**（标题保留）

**与删除会话的区别**：
- **清空**：删除消息，保留会话
- **删除**：删除整个会话

---

## 💾 数据存储

### 存储位置
```
data/sessions/
└── index.json  # 所有会话的索引文件
```

### 数据结构

**index.json 格式**：
```json
{
  "current_session_id": "session_1782149529146",
  "sessions": [
    {
      "session_id": "session_1782149529146",
      "title": "卡兹克出装建议",
      "messages": [
        {
          "role": "user",
          "content": "卡兹克怎么出装？",
          "timestamp": "2026-06-23T01:35:22.123456"
        },
        {
          "role": "assistant",
          "content": "卡兹克的出装推荐...",
          "timestamp": "2026-06-23T01:35:25.789012"
        }
      ],
      "created_at": "2026-06-23T01:32:09.146501",
      "updated_at": "2026-06-23T01:35:25.789012"
    }
  ]
}
```

**字段说明**：
- `current_session_id`：当前激活的会话 ID
- `sessions`：所有会话列表
  - `session_id`：会话唯一标识（时间戳）
  - `title`：会话标题（AI 生成或用户自定义）
  - `messages`：该会话的所有消息
  - `created_at`：创建时间
  - `updated_at`：最后更新时间

---

## 🔧 技术实现

### 核心类

#### 1. Session（会话类）

**文件**：`session_manager.py`

**职责**：
- 管理单个会话的消息列表
- 提供消息的增删改查
- 序列化与反序列化

**关键方法**：
```python
class Session:
    def __init__(self, session_id: str, title: str = "新对话", messages: list = None)
    def add_message(self, role: str, content: str)
    def get_messages_for_api(self) -> list
    def to_dict(self) -> dict
    @staticmethod
    def from_dict(data: dict)
```

#### 2. SessionManager（会话管理器）

**文件**：`session_manager.py`

**职责**：
- 管理所有会话
- 会话的创建、删除、切换
- 持久化存储
- 标题自动生成

**关键方法**：
```python
class SessionManager:
    def __init__(self, storage_dir: str = "data/sessions")
    def create_new_session(self) -> str
    def get_current_session(self) -> Session
    def switch_session(self, session_id: str)
    def delete_session(self, session_id: str)
    def update_session_title(self, session_id: str, title: str)
    def get_all_sessions(self) -> list
    def generate_title_from_message(self, message: str, api_key, base_url, model) -> str
```

---

### 界面组件

#### 侧边栏（QListWidget）

**创建代码**：
```python
def create_sidebar(self) -> QWidget:
    # 标题
    title = QLabel("📝 对话历史")
    
    # 新建按钮
    new_chat_button = QPushButton("+ 新建对话")
    new_chat_button.clicked.connect(self.create_new_chat)
    
    # 会话列表
    self.session_list = QListWidget()
    self.session_list.itemClicked.connect(self.on_session_clicked)
    self.session_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    self.session_list.customContextMenuRequested.connect(self.show_session_context_menu)
```

**样式**：
- 选中项：蓝色背景（`#e3f2fd`）+ 蓝色文字（`#1976d2`）
- 悬停项：浅灰色背景（`#f0f0f0`）
- 列表项：10px 内边距，底部 1px 分割线

---

### 布局（QSplitter）

**代码**：
```python
splitter = QSplitter(Qt.Orientation.Horizontal)
splitter.addWidget(sidebar)
splitter.addWidget(chat_area)
splitter.setStretchFactor(0, 1)  # 侧边栏占 1 份
splitter.setStretchFactor(1, 3)  # 聊天区占 3 份
splitter.setSizes([250, 650])     # 初始宽度
```

**优势**：
- 用户可以拖动调整左右比例
- 自动处理窗口缩放

---

## 🔄 消息流程

### 发送消息流程（已更新）

```
用户输入消息
    ↓
检查是否是新对话的第一条消息
    ↓ 是
调用 AI 生成标题（后台，不阻塞）
    ↓
保存消息到当前会话
    ↓
保存到 SessionManager
    ↓
发送给 AI API
    ↓
接收回复
    ↓
保存回复到当前会话
    ↓
显示在聊天区域
```

### 切换会话流程

```
用户点击会话列表项
    ↓
获取会话 ID
    ↓
调用 SessionManager.switch_session()
    ↓
清空聊天显示区域
    ↓
加载该会话的所有消息
    ↓
逐条显示在聊天区域
```

---

## 🎯 使用场景

### 场景 1：多任务并行

**示例**：
1. 对话 1：学习机器学习
2. 对话 2：讨论代码问题
3. 对话 3：查询天气信息

**优势**：
- 每个对话独立，不会混淆
- 随时切换，保留完整上下文

---

### 场景 2：长期项目追踪

**示例**：
- "项目 A 需求讨论"（持续 2 周）
- "英语学习计划"（持续 1 个月）

**优势**：
- 历史记录永久保存
- 可以回顾之前的讨论

---

### 场景 3：主题分类

**示例**：
- "编程问题"
- "生活建议"
- "学习笔记"

**优势**：
- 通过标题快速定位
- 避免不同主题互相干扰

---

## ⚙️ 配置说明

### 窗口宽度调整

**文件**：`config.yaml`

```yaml
ui:
  window_width: 900  # 增加到 900px 以容纳侧边栏
```

**推荐值**：
- 最小：800px
- 推荐：900px - 1200px

---

## 🐛 已知问题与解决

### 问题 1：标题生成失败

**现象**：侧边栏显示 "新对话" 或消息前 15 字

**原因**：
- API 调用超时
- 网络连接问题
- API Key 无效

**解决方案**：
- 手动重命名会话
- 检查网络和 API 配置

---

### 问题 2：切换会话时历史记录未显示

**现象**：切换会话后聊天区域为空

**原因**：
- 会话数据未正确加载
- `load_session_list()` 未调用

**解决方案**：
- 确保 `__init__` 中调用了 `self.load_session_list()`
- 检查 `data/sessions/index.json` 是否存在

---

### 问题 3：会话列表未刷新

**现象**：创建新会话后侧边栏未更新

**原因**：
- 未调用 `self.load_session_list()`

**解决方案**：
- 在 `create_new_chat()` 中添加 `self.load_session_list()`
- 在 `delete_session()` 中添加 `self.load_session_list()`

---

## 🔮 未来改进方向

### 1. 会话搜索

**功能**：在侧边栏顶部添加搜索框，支持按标题或内容搜索会话

**实现思路**：
```python
def search_sessions(self, keyword: str) -> list:
    results = []
    for session in self.sessions.values():
        # 搜索标题
        if keyword in session.title:
            results.append(session)
            continue
        # 搜索消息内容
        for msg in session.messages:
            if keyword in msg["content"]:
                results.append(session)
                break
    return results
```

---

### 2. 会话分组

**功能**：支持创建文件夹，将会话分组管理

**示例**：
```
📂 工作
  📄 项目 A 需求讨论
  📄 代码审查笔记
📂 学习
  📄 机器学习入门
  📄 Python 进阶
📂 其他
  📄 天气查询
```

---

### 3. 会话导出

**功能**：将会话导出为 Markdown 或 PDF 文件

**格式示例**：
```markdown
# 卡兹克出装建议

**创建时间**：2026-06-23 01:35  
**消息数量**：12 条

---

## 对话记录

**你**：卡兹克怎么出装？

**AI**：卡兹克的出装推荐...
```

---

### 4. 会话置顶

**功能**：支持将重要会话置顶显示

**实现思路**：
```python
class Session:
    def __init__(self, ...):
        self.pinned = False  # 是否置顶

def get_all_sessions(self) -> list:
    sessions = list(self.sessions.values())
    # 置顶会话排在前面
    sessions.sort(key=lambda x: (not x.pinned, x.updated_at), reverse=True)
    return sessions
```

---

### 5. 会话备份

**功能**：定期自动备份会话数据

**实现思路**：
```python
import shutil
from datetime import datetime

def backup_sessions(self):
    backup_path = Path("data/backups") / f"sessions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(self.storage_dir / "index.json", backup_path)
```

---

## 📊 测试清单

### 基础功能测试

- [ ] 启动程序，自动创建默认会话
- [ ] 点击 "+ 新建对话"，创建新会话
- [ ] 在新会话中发送第一条消息，检查标题自动生成
- [ ] 点击侧边栏中的会话，切换会话
- [ ] 右键点击会话，选择 "重命名"
- [ ] 右键点击会话，选择 "删除"
- [ ] 点击 "🗑️ 清空" 按钮，清空当前对话

### 边界情况测试

- [ ] 删除最后一个会话，检查是否自动创建新会话
- [ ] 删除当前会话，检查是否自动切换到其他会话
- [ ] 在有多个会话时切换，检查历史记录是否正确加载
- [ ] 标题生成失败时，检查是否使用消息前 15 字作为标题

### 数据持久化测试

- [ ] 创建多个会话后关闭程序
- [ ] 重新启动程序，检查会话列表是否完整
- [ ] 切换到之前的会话，检查历史记录是否完整

---

## 📝 代码注释规范

所有新增代码都包含详细的中文注释，方便学习：

```python
def create_new_chat(self):
    """
    创建新对话（会话管理）
    
    流程：
    1. 调用 SessionManager 创建新会话
    2. 清空显示区域
    3. 刷新会话列表
    4. 显示确认消息
    """
    # 创建新会话
    session_id = self.session_manager.create_new_session()
    
    # 清空显示区域
    self.chat_display.clear()
    
    # 刷新会话列表
    self.load_session_list()
    
    # 显示提示
    self.append_message("系统", "已创建新对话")
```

---

## 🎓 学习要点

### 1. Qt 布局管理

**QSplitter**：
- 用于创建可拖动调整大小的分栏布局
- 支持水平（Horizontal）和垂直（Vertical）方向
- `setStretchFactor()` 控制各部分的拉伸比例

### 2. Qt 列表控件

**QListWidget**：
- `addItem()`：添加列表项
- `itemClicked`：点击事件
- `customContextMenuRequested`：右键菜单事件
- `item.setData(Qt.ItemDataRole.UserRole, data)`：存储自定义数据

### 3. 数据持久化

**JSON 存储**：
- 所有会话存储在一个 JSON 文件中
- 使用 `indent=2` 格式化输出，方便人类阅读
- 时间戳使用 ISO 8601 格式（`isoformat()`）

### 4. 信号与槽

**Qt 信号机制**：
```python
# 连接信号
button.clicked.connect(self.on_button_clicked)

# 带参数的信号
item.clicked.connect(lambda: self.on_item_clicked(item_id))
```

---

## 📖 相关文档

- [错误日志](../logs/error_log.md)
- [配置说明](../config.yaml)
- [开发历史](../README.md)

---

**文档版本**：v1.0  
**最后更新**：2026-06-23  
**维护者**：开发团队
