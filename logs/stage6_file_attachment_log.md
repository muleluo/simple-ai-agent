# 阶段 6：文件附加功能（直接阅读）

**日期**：2026-06-22  
**功能**：让 AI 直接读取用户上传的文件内容，无需 RAG  
**技术**：文件读取 + 上下文传递  
**状态**：✅ 已完成

---

## 🎯 目标

实现两种文件上传方式，满足不同需求：

1. **附加文件**（新功能）：临时阅读，AI 直接看到文件内容
2. **上传到知识库**（已有功能）：永久存储，使用 RAG 搜索

---

## 📊 两种方式对比

| 特性 | 附加文件 | 上传到知识库 |
|------|---------|-------------|
| **位置** | 主界面按钮 | 设置菜单（对用户透明） |
| **原理** | 直接放入上下文 | RAG 向量搜索 |
| **适用场景** | 小文件、一次性阅读 | 大量文档、长期查询 |
| **上下文限制** | 受限于模型上下文窗口 | 不受限 |
| **持久性** | 仅当次对话 | 永久存储 |
| **AI 是否需要工具** | 否，直接阅读 | 是，需要调用 search_knowledge_base |
| **类比** | ChatGPT 的文件上传 | 企业知识库系统 |

---

## 🔧 实现步骤

### 步骤 1：添加 QMenu 导入

```python
from PySide6.QtWidgets import (
    # ... 其他导入
    QMenu              # 菜单（用于设置下拉菜单）
)
```

**为什么需要 QMenu？**
- 创建设置按钮的下拉菜单
- 将"上传到知识库"隐藏到设置中

---

### 步骤 2：添加附加文件列表

在 `__init__` 方法中：

```python
# 附加文件列表（用于存储用户临时上传的文件内容）
self.attached_files = []
```

**数据结构**：
```python
[
    {
        "filename": "test.py",
        "content": "print('hello')",
        "path": "/path/to/test.py"
    },
    # 可以附加多个文件
]
```

---

### 步骤 3：修改界面按钮

#### 旧界面：
```
[发送] [⏰ 提醒] [📄 上传] [清空历史]
```

#### 新界面：
```
[发送] [⏰ 提醒] [📎 附加文件] [⚙️ 设置▼] [清空历史]
```

**代码**：

```python
# 附加文件按钮（新功能！）
self.attach_button = QPushButton("📎 附加文件")
self.attach_button.clicked.connect(self.attach_file)

# 设置按钮（包含知识库上传）
self.settings_button = QPushButton("⚙️ 设置")

# 创建设置菜单
settings_menu = QMenu(self)
upload_to_kb_action = settings_menu.addAction("📚 上传到知识库")
upload_to_kb_action.triggered.connect(self.upload_to_knowledge_base)

self.settings_button.setMenu(settings_menu)
```

---

### 步骤 4：实现 attach_file() 方法

```python
def attach_file(self):
    """
    附加文件到当前对话（临时阅读）
    """
    # 1. 打开文件选择对话框
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "选择要附加的文件",
        "",
        "文本文件 (*.txt *.md *.py *.js *.json *.yaml *.yml);;所有文件 (*)"
    )

    if not file_path:
        return

    # 2. 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 3. 获取文件名
    filename = Path(file_path).name

    # 4. 添加到附加文件列表
    self.attached_files.append({
        "filename": filename,
        "content": content,
        "path": file_path
    })

    # 5. 显示成功消息
    self.append_message("系统", f"✅ 已附加文件：{filename} ({len(content)} 字符)")
```

---

### 步骤 5：修改 append_message() 支持"系统"消息

```python
def append_message(self, sender: str, content: str):
    # 根据发送者设置不同的颜色
    if sender == "你":
        color = "#2196F3"
    elif sender == "AI":
        color = "#4CAF50"
    else:  # 系统消息
        color = "#9E9E9E"
```

---

### 步骤 6：修改 send_message() 发送文件内容

```python
def send_message(self):
    user_message = self.input_box.text().strip()
    
    # 1. 显示用户消息
    self.append_message("你", user_message)
    
    # 2. 如果有附加文件，将文件内容添加到用户消息中
    full_user_message = user_message
    if self.attached_files:
        # 构建文件内容
        files_content = "\n\n【附加文件】\n"
        for file_info in self.attached_files:
            files_content += f"\n--- 文件：{file_info['filename']} ---\n"
            files_content += file_info['content']
            files_content += f"\n--- 文件结束 ---\n"
        
        full_user_message = user_message + files_content
        
        # 显示提示
        self.append_message("系统", f"📎 已将 {len(self.attached_files)} 个文件内容发送给 AI")
    
    # 3. 保存到历史记录（保存原始消息，不包含文件内容）
    self.chat_history.add_message("user", user_message)
    
    # 4-6. 清空输入框、禁用按钮...
    
    # 7. 准备 API 消息
    api_messages = [self.system_prompt] + self.chat_history.get_messages_for_api()
    
    # 8. 如果有附加文件，修改最后一条用户消息
    if self.attached_files:
        api_messages[-1] = {
            "role": "user",
            "content": full_user_message  # ← 包含文件内容的完整消息
        }
        
        # 清空附加文件列表（文件只在这次对话中有效）
        self.attached_files = []
        
        # 恢复输入框提示
        self.input_box.setPlaceholderText("在这里输入消息...")
    
    # 9-10. 创建线程并启动...
```

**关键点**：
- 文件内容只加到 API 消息中，**不保存到历史记录**
- 发送后自动清空附加文件列表（一次性使用）

---

### 步骤 7：重命名方法

```python
# 旧名称
def upload_document(self):

# 新名称
def upload_to_knowledge_base(self):
```

保持功能不变，只是名称更清晰。

---

### 步骤 8：更新系统提示词

```yaml
system_prompt: "你是一个友好的 AI 助手，用简洁友好的语言回答用户的问题。当用户需要设置提醒时，使用 set_reminder 工具。当用户询问需要联网查询的实时信息（如天气、新闻、价格、当前事件等）时，使用 web_search 工具。当用户的问题可能在他们上传到知识库的文档中有答案时，使用 search_knowledge_base 工具。如果用户通过「附加文件」功能上传了文件，文件内容会直接出现在用户消息的【附加文件】部分，你可以直接阅读和回答相关问题，无需使用任何工具。"
```

**要点**：
- 告诉 AI 附加文件会直接出现在消息中
- 无需使用工具，直接阅读即可

---

## 💡 使用示例

### 示例 1：阅读代码文件

```
用户：[点击 📎 附加文件，选择 main.py]
系统：✅ 已附加文件：main.py (5000 字符)

用户：这个代码的主要功能是什么？
系统：📎 已将 1 个文件内容发送给 AI

AI：这是一个 AI 桌面助手程序，主要功能包括：
    1. 与 AI 对话
    2. 设置提醒
    3. 网络搜索
    4. 知识库管理
    ... [基于实际文件内容回答]
```

---

### 示例 2：分析配置文件

```
用户：[附加 config.yaml]
系统：✅ 已附加文件：config.yaml (500 字符)

用户：我的 API 配置对吗？
AI：根据你的配置文件，API 设置如下：
    - API Key: sk-vftb...（已设置）
    - 模型：gemini-3.1-flash-lite-preview
    - 温度：0.7
    配置看起来正常！
```

---

### 示例 3：附加多个文件

```
用户：[附加 file1.py]
系统：✅ 已附加文件：file1.py (2000 字符)

用户：[附加 file2.py]
系统：✅ 已附加文件：file2.py (1500 字符)

用户：这两个文件的关系是什么？
系统：📎 已将 2 个文件内容发送给 AI

AI：file1.py 是主程序，file2.py 是它导入的工具模块...
```

---

## 🔍 技术细节

### 1. 为什么不保存文件内容到历史记录？

**原因**：
- 文件可能很大（几千行代码）
- 保存会导致历史记录文件膨胀
- 用户重新打开程序不一定需要旧文件

**解决方案**：
- 只保存用户的原始问题
- 文件内容仅在当次对话中传递给 API

---

### 2. 附加文件的生命周期

```python
# 附加文件
self.attached_files.append(...)  # 添加到列表

# 发送消息
api_messages[-1] = {"content": user_message + files_content}

# 清空
self.attached_files = []  # ← 发送后立即清空
```

**流程**：
```
附加文件 → 暂存到列表 → 发送消息时添加到上下文 → 清空列表
```

---

### 3. 消息格式

**发送给 API 的消息**：
```python
{
    "role": "user",
    "content": "帮我看看这段代码\n\n【附加文件】\n\n--- 文件：main.py ---\nprint('hello')\n--- 文件结束 ---\n"
}
```

**显示给用户的消息**：
```
你：帮我看看这段代码
系统：✅ 已附加文件：main.py (13 字符)
系统：📎 已将 1 个文件内容发送给 AI
AI：这段代码的作用是...
```

---

### 4. 支持的文件类型

```python
"文本文件 (*.txt *.md *.py *.js *.json *.yaml *.yml);;所有文件 (*)"
```

**可以读取**：
- ✅ 代码文件（.py, .js, .java, .cpp）
- ✅ 配置文件（.yaml, .json, .xml）
- ✅ 文档文件（.txt, .md）

**不能读取**：
- ❌ 二进制文件（.pdf, .docx, .xlsx）
- ❌ 图片文件（.jpg, .png）

---

## 🎯 RAG vs 附加文件 - 何时用哪个？

### 用附加文件：

✅ **小文件（<10KB）**
```
代码文件、配置文件、小文档
```

✅ **一次性问题**
```
"这个错误怎么回事？"
"帮我优化这段代码"
```

✅ **需要完整上下文**
```
理解整个文件的逻辑
跨行推理
```

---

### 用知识库（RAG）：

✅ **大量文档**
```
整个项目文档
课程教材（多个章节）
公司知识库
```

✅ **长期使用**
```
反复查询
文档会更新
```

✅ **超过上下文窗口**
```
单个文件 > 100KB
文档总量 > 1MB
```

---

## 🐛 常见问题

### Q1：附加的文件下次对话还在吗？

**答**：不在。
- 附加文件只对当次消息有效
- 发送后自动清空
- 如果需要持久化，使用"上传到知识库"

---

### Q2：可以附加多个文件吗？

**答**：可以。
```
点击 3 次"附加文件" → 3 个文件都会添加
发送消息时 → 所有文件内容一起发送给 AI
```

---

### Q3：文件太大会怎样？

**问题**：
- 超过模型上下文窗口（如 128K tokens）
- API 调用会失败

**解决**：
- 使用"上传到知识库"
- 或者只附加文件的关键部分

---

### Q4：为什么放到"设置"里？

**原因**：
- RAG 是开发者技术，对普通用户不直观
- 用户只需要"问问题"功能
- 将技术细节隐藏在设置中

**类比**：
```
用户看到：附加文件 → 问问题
开发者看到：设置 → 上传到知识库（RAG）
```

---

## 🚀 可能的优化

### 优化 1：显示已附加的文件列表

在界面上显示当前附加的文件：

```python
# 添加标签显示
self.attached_label = QLabel("附加文件：无")

# 更新标签
def attach_file(self):
    # ... 附加文件代码
    
    # 更新显示
    filenames = [f['filename'] for f in self.attached_files]
    self.attached_label.setText(f"附加文件：{', '.join(filenames)}")
```

---

### 优化 2：支持取消附加

添加"清除附加"按钮：

```python
def clear_attachments(self):
    self.attached_files = []
    self.append_message("系统", "已清除所有附加文件")
```

---

### 优化 3：支持 PDF

安装 PDF 解析库：

```bash
pip install PyPDF2
```

读取 PDF：

```python
import PyPDF2

def read_pdf(file_path):
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text
```

---

### 优化 4：智能压缩

如果文件太大，自动提取关键部分：

```python
def smart_compress(content, max_chars=10000):
    if len(content) <= max_chars:
        return content
    
    # 提取：
    # 1. 开头（了解结构）
    # 2. 函数定义（关键逻辑）
    # 3. 注释（理解意图）
    # ...
```

---

## ✅ 完成情况

- ✅ 添加 QMenu 导入
- ✅ 添加附加文件列表
- ✅ 修改界面按钮布局
- ✅ 实现 attach_file() 方法
- ✅ 修改 append_message() 支持系统消息
- ✅ 修改 send_message() 发送文件内容
- ✅ 重命名 upload_document() → upload_to_knowledge_base()
- ✅ 更新系统提示词
- ✅ 编写完整文档

---

## 🎓 学到的新概念

1. **QMenu**：Qt 菜单组件
2. **上下文传递**：将文件内容直接放入消息
3. **临时状态管理**：附加文件只在当次对话有效
4. **用户体验设计**：隐藏技术细节

---

## 📝 代码变更总结

### 修改的文件：
1. `main.py` - 添加附加文件功能
2. `config.yaml` - 更新系统提示词

### 新增的概念：
- 附加文件 vs 知识库上传
- 临时阅读 vs 永久存储
- 直接上下文 vs RAG 搜索

---

**开发时间**：1 小时  
**难度**：⭐⭐⭐（中等）  
**核心技术**：文件读取 + 消息拼接

**最大收获**：理解了 ChatGPT 式文件上传和 RAG 的区别
