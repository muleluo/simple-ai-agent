# 文件附加功能 - 学习笔记

**日期**：2026-06-22  
**主题**：文件上传的两种实现方式  
**状态**：✅ 已完成

---

## 🎯 核心问题

**用户问**："AI 怎么读取我上传的文件？"

**两种答案**：

### 方式 1：直接阅读（本次实现）
```
用户上传 → 读取文件 → 文件内容放进消息 → AI 直接看到
```

### 方式 2：RAG 搜索（上次实现）
```
用户上传 → 切片 → 向量化 → 存储
用户提问 → 搜索 → 返回相关片段 → AI 看到片段
```

---

## 💡 关键区别

### 类比理解

**直接阅读**：
```
学生：老师，这道题怎么做？[递上整张试卷]
老师：[看完整张试卷] 第 3 题是这样解的...
```

**RAG 搜索**：
```
学生：老师，"二次函数"怎么解？
老师：[在笔记本里搜索"二次函数"] 找到了，你看这一页...
```

---

## 📊 对比表格

| 特性 | 直接阅读 | RAG 搜索 |
|------|---------|---------|
| **原理** | 文件内容 → 消息 | 文件内容 → 向量库 |
| **AI 怎么看** | 直接读整个文件 | 搜索后读片段 |
| **上下文占用** | 占用 ✅ | 不占用 ❌ |
| **文件大小限制** | 受限（上下文窗口） | 不受限 |
| **持久性** | 一次性 | 永久存储 |
| **适合场景** | 小文件、临时问题 | 大量文档、长期使用 |
| **ChatGPT 用的** | 这个 ✓ | 不一定 |

---

## 🔧 技术实现

### 数据流

```
┌─────────────┐
│ 用户点击按钮 │
└──────┬──────┘
       ↓
┌─────────────┐
│ 选择文件     │
└──────┬──────┘
       ↓
┌──────────────────┐
│ 读取文件内容      │
│ with open(...):  │
│   content = f.read()
└──────┬───────────┘
       ↓
┌─────────────────────┐
│ 存到临时列表         │
│ self.attached_files │
└──────┬──────────────┘
       ↓
┌────────────────────────┐
│ 用户输入问题并发送      │
└──────┬─────────────────┘
       ↓
┌─────────────────────────┐
│ 拼接消息                 │
│ message = question +    │
│   "\n【附加文件】\n" +   │
│   file_content          │
└──────┬──────────────────┘
       ↓
┌─────────────────┐
│ 发送给 AI API    │
└──────┬──────────┘
       ↓
┌─────────────────┐
│ 清空附加列表     │
│ attached_files=[]│
└──────────────────┘
```

---

## 📚 关键代码

### 1. 附加文件

```python
def attach_file(self):
    # 1. 选择文件
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "选择要附加的文件",
        "",
        "文本文件 (*.txt *.md *.py);;所有文件 (*)"
    )
    
    if not file_path:
        return
    
    # 2. 读取内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 3. 获取文件名
    filename = Path(file_path).name
    
    # 4. 存到列表
    self.attached_files.append({
        "filename": filename,
        "content": content
    })
    
    # 5. 提示用户
    self.append_message("系统", f"✅ 已附加：{filename}")
```

---

### 2. 发送消息时拼接文件

```python
def send_message(self):
    user_message = self.input_box.text().strip()
    
    # 构建完整消息
    full_message = user_message
    
    # 如果有附加文件
    if self.attached_files:
        full_message += "\n\n【附加文件】\n"
        
        for file in self.attached_files:
            full_message += f"\n--- 文件：{file['filename']} ---\n"
            full_message += file['content']
            full_message += "\n--- 文件结束 ---\n"
    
    # 准备 API 消息
    api_messages = [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": full_message}  # ← 包含文件内容
    ]
    
    # 发送给 API
    reply = ai_client.chat(api_messages)
    
    # 清空附加文件（一次性使用）
    self.attached_files = []
```

---

### 3. 实际发送的消息格式

**用户输入**：
```
帮我看看这段代码
```

**附加文件**：
```python
# test.py
def hello():
    print("hello")
```

**实际发送给 API 的消息**：
```
帮我看看这段代码

【附加文件】

--- 文件：test.py ---
def hello():
    print("hello")
--- 文件结束 ---
```

**AI 看到的就是完整内容！**

---

## 🎭 界面变化

### 旧界面
```
┌────────────────────────────────┐
│ [输入框] [发送] [提醒] [上传] [清空]│
└────────────────────────────────┘
```

### 新界面
```
┌────────────────────────────────────────┐
│ [输入框] [发送] [提醒] [📎 附加文件] [⚙️ 设置▼] [清空]│
└────────────────────────────────────────┘
                                    ↓
                            ┌───────────────┐
                            │ 📚 上传到知识库 │
                            └───────────────┘
```

**变化**：
1. "上传" 按钮 → 改为 "附加文件"
2. 新增 "设置" 下拉菜单
3. "上传到知识库" 隐藏在设置中

---

## 💡 核心概念

### 1. 上下文窗口

**是什么？**
AI 一次能"看到"的内容量。

**比喻**：
```
上下文窗口 = 你的视野范围

小窗口（4K tokens）：
只能看一页纸

大窗口（128K tokens）：
能看一整本书
```

**限制**：
```python
文件大小 < 上下文窗口 - 对话历史 - 系统提示词

例如：
128K tokens 窗口
- 对话历史：10K
- 系统提示词：1K
- 剩余：117K ← 文件内容不能超过这个
```

---

### 2. 临时 vs 永久存储

**临时存储**（附加文件）：
```python
self.attached_files = []  # 存在内存里

# 发送消息
send_message()
    ↓
self.attached_files = []  # 清空！
```

**永久存储**（知识库）：
```python
knowledge_base.add_document(text, filename)
    ↓
# 存到磁盘：data/knowledge_base/
# 永久保存，程序关闭也不会丢失
```

---

### 3. QMenu（菜单组件）

**是什么？**
下拉菜单。

**代码**：
```python
# 创建按钮
settings_button = QPushButton("⚙️ 设置")

# 创建菜单
menu = QMenu(self)
action1 = menu.addAction("选项 1")
action2 = menu.addAction("选项 2")

# 绑定点击事件
action1.triggered.connect(do_something)

# 把菜单绑定到按钮
settings_button.setMenu(menu)
```

**效果**：
```
[⚙️ 设置 ▼]  ← 点击
    ↓
┌────────────┐
│ 选项 1      │ ← 点击触发 do_something()
│ 选项 2      │
└────────────┘
```

---

## 🧪 实际例子

### 例子 1：查看代码

```
1. 用户：[点击 📎 附加文件]
2. 系统：[打开文件选择对话框]
3. 用户：[选择 main.py]
4. 系统：✅ 已附加文件：main.py (5000 字符)

5. 用户：这个程序的主要功能是什么？
6. 系统：📎 已将 1 个文件内容发送给 AI

7. AI：这是一个 AI 桌面助手，主要功能包括：
       - 与 AI 对话
       - 设置提醒
       - 网络搜索
       ...
```

**背后发生了什么？**
```python
# 步骤 3-4：附加文件
attached_files = [{
    "filename": "main.py",
    "content": "#!/usr/bin/env python3\n..."  # 完整代码
}]

# 步骤 5-6：发送消息
api_message = {
    "role": "user",
    "content": "这个程序的主要功能是什么？\n\n【附加文件】\n\n--- 文件：main.py ---\n#!/usr/bin/env python3\n..."
}

# 步骤 7：AI 直接读到了完整代码！
```

---

### 例子 2：分析错误日志

```
用户：[附加 error.log]
系统：✅ 已附加文件：error.log (2000 字符)

用户：这个错误怎么解决？
AI：根据日志，错误原因是...
    解决方法：...
```

---

### 例子 3：对比两个文件

```
用户：[附加 old_version.py]
系统：✅ 已附加文件：old_version.py

用户：[附加 new_version.py]
系统：✅ 已附加文件：new_version.py

用户：新版本改了什么？
系统：📎 已将 2 个文件内容发送给 AI

AI：主要变化：
    1. 新增了 XXX 功能
    2. 修复了 YYY bug
    3. 重构了 ZZZ 模块
```

---

## 🤔 常见疑问

### Q1：为什么不保存文件内容到历史记录？

**原因**：
```
假设文件 5000 行代码
→ 保存到历史记录
→ 历史文件变成几 MB
→ 下次打开程序加载很慢
→ 而且用户可能不再需要这个文件
```

**解决**：
```python
# 历史记录只保存用户的问题
chat_history.add_message("user", "这段代码的作用？")

# 不保存文件内容！
# ❌ chat_history.add_message("user", "这段代码的作用？\n\n【附加文件】\n...")
```

---

### Q2：附加文件和知识库，用户怎么选？

**用户不需要选！**

**用户视角**：
- "我要问关于这个文件的问题" → 点 📎 附加文件
- （知识库对用户透明，AI 自动搜索）

**开发者视角**：
- 小文件、临时问题 → 附加文件
- 大量文档、长期使用 → 知识库

---

### Q3：文件太大怎么办？

**问题**：
```
文件 10 万行 → 超过上下文窗口 → API 调用失败
```

**解决方法 1**：提示用户
```python
if len(content) > 100000:
    QMessageBox.warning(self, "文件太大", 
        "文件太大，建议使用「设置 → 上传到知识库」功能")
    return
```

**解决方法 2**：自动切换到知识库
```python
if len(content) > 100000:
    # 自动添加到知识库
    self.knowledge_base.add_document(content, filename)
    self.append_message("系统", "文件较大，已自动添加到知识库")
```

---

### Q4：可以附加图片吗？

**当前不行。**

**原因**：
```python
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()  # 只能读文本文件
```

**如果要支持**：
1. 转成 base64 编码
2. 使用支持视觉的模型（如 GPT-4 Vision）
3. 修改消息格式

```python
import base64

# 读取图片
with open("image.jpg", 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# 发送给 API
message = {
    "role": "user",
    "content": [
        {"type": "text", "text": "这是什么？"},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
    ]
}
```

---

## 🎯 设计思想

### 为什么隐藏"知识库上传"？

**原则**：对用户暴露功能，隐藏技术

**用户需要**：
- "我想问关于这个文件的问题"

**用户不关心**：
- 文件是怎么处理的
- 用的是 RAG 还是直接阅读
- 向量化是什么

**类比**：
```
用户使用 Google
  ↓
输入关键词 → 得到结果

用户不关心：
  - PageRank 算法
  - 倒排索引
  - 分布式爬虫
```

**所以**：
- 主界面：📎 附加文件（用户理解）
- 设置菜单：📚 上传到知识库（开发者理解）

---

## ✅ 总结

### 核心理解

1. **两种文件上传方式**
   - 附加文件 = 直接阅读
   - 知识库 = RAG 搜索

2. **适用场景**
   - 小文件、临时问题 → 附加
   - 大量文档、长期使用 → 知识库

3. **技术本质**
   - 附加 = 文件内容放进上下文
   - 知识库 = 文件存到向量数据库

4. **设计原则**
   - 对用户暴露功能
   - 隐藏技术细节

---

**学习时间**：1 小时  
**难度**：⭐⭐⭐（中等）  
**收获**：理解了 ChatGPT 式文件上传的实现原理

**关键代码**：
```python
# 读取文件
content = open(file_path).read()

# 拼接到消息
message = question + "\n\n【附加文件】\n" + content

# 发送给 AI
ai_client.chat([{"role": "user", "content": message}])

# 就这么简单！
```
