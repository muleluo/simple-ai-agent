# 提醒功能开发 - 学习笔记

**日期**：2026-06-17  
**功能**：给 AI 助手添加定时提醒功能  
**状态**：✅ 基础版已完成

---

## 📚 已学概念总结

### 1. Qt 按钮的三部曲

```python
# 第一步：创建按钮
self.reminder_button = QPushButton("⏰ 提醒")

# 第二步：连接点击事件（信号与槽机制）
self.reminder_button.clicked.connect(self.show_reminder_dialog)
# 注意：只写方法名，不要加括号 ()

# 第三步：添加到布局
input_layout.addWidget(self.reminder_button)
```

**关键点**：
- `clicked` 是按钮的"信号"（Signal）
- `connect()` 把信号连接到"槽"（Slot，就是一个方法）
- 点击按钮 → 自动调用连接的方法

---

### 2. QInputDialog - 快速输入对话框

```python
from PySide6.QtWidgets import QInputDialog

# 弹出输入框
value, ok = QInputDialog.getInt(
    self,              # 父窗口
    "标题",             # 对话框标题
    "提示文字",         # 输入提示
    默认值,             # 默认显示的数字
    最小值,             # 允许的最小值
    最大值              # 允许的最大值
)

# 检查用户是点了"确定"还是"取消"
if ok:
    print(f"用户输入了：{value}")
else:
    print("用户取消了")
```

**返回值**：
- `value`：用户输入的值
- `ok`：布尔值，`True` = 确定，`False` = 取消

**其他输入框**：
- `QInputDialog.getText()` - 输入文本
- `QInputDialog.getDouble()` - 输入小数
- `QInputDialog.getItem()` - 从列表选择

---

### 3. QTimer - 定时器

```python
from PySide6.QtCore import QTimer

# 创建定时器
timer = QTimer(self)  # 传入父对象，防止被垃圾回收

# 设置为单次触发（默认会重复触发）
timer.setSingleShot(True)

# 设置时间间隔（单位：毫秒）
timer.setInterval(5000)  # 5000 毫秒 = 5 秒

# 时间到了做什么？（连接信号）
timer.timeout.connect(self.某个方法)

# 启动定时器
timer.start()
```

**重要概念**：

| 方法 | 作用 |
|------|------|
| `setSingleShot(True)` | 只触发一次 |
| `setSingleShot(False)` | 重复触发（默认） |
| `setInterval(ms)` | 设置间隔（毫秒） |
| `start()` | 启动定时器 |
| `stop()` | 停止定时器 |
| `isActive()` | 检查是否正在运行 |

**时间单位转换**：
```python
# 分钟 → 毫秒
milliseconds = minutes * 60 * 1000

# 例子：
# 1 分钟 = 60 秒 = 60,000 毫秒
# 5 分钟 = 300 秒 = 300,000 毫秒
```

---

### 4. lambda 函数（匿名函数）

**问题**：如何给信号传递参数？

```python
# ❌ 错误：timeout 信号不会传递参数
timer.timeout.connect(self.show_reminder)

# ✅ 正确：用 lambda 包装，手动传入参数
timer.timeout.connect(lambda: self.show_reminder(minutes))
```

**lambda 是什么？**

```python
# 普通函数写法
def 临时函数():
    self.show_reminder(5)

timer.timeout.connect(临时函数)

# lambda 简写（等价于上面）
timer.timeout.connect(lambda: self.show_reminder(5))
```

**语法**：
```python
lambda 参数: 表达式

# 例子：
add = lambda x, y: x + y
print(add(2, 3))  # 输出 5

# 等价于：
def add(x, y):
    return x + y
```

---

### 5. hasattr() - 检查对象是否有某个属性

```python
hasattr(对象, '属性名')  # 返回 True 或 False
```

**用法**：
```python
# 第一次使用时创建列表
if not hasattr(self, 'active_reminders'):
    self.active_reminders = []  # 初始化

self.active_reminders.append(timer)
```

**为什么需要？**

如果直接写：
```python
self.active_reminders.append(timer)  # ❌ 第一次会报错
# AttributeError: 'SimpleAIAgent' object has no attribute 'active_reminders'
```

---

### 6. Python 垃圾回收（GC）

**问题**：为什么要保存定时器引用？

```python
def show_reminder_dialog(self):
    timer = QTimer(self)  # 创建定时器
    timer.start()
    # 方法结束后，timer 变量消失
    # 如果没有其他引用，定时器对象会被删除
    # 定时器失效！
```

**解决**：把定时器保存到 `self`
```python
self.active_reminders = []  # 类的属性，不会消失
self.active_reminders.append(timer)  # 保存引用
# 现在定时器有引用，不会被删除
```

**什么是垃圾回收？**
- Python 会自动删除没有被引用的对象
- 释放内存空间
- 但定时器不能被删除，否则会失效

---

### 7. QApplication.beep() - 系统提示音

```python
from PySide6.QtWidgets import QApplication

QApplication.beep()  # 发出"哔"的一声
```

**效果**：
- Windows：默认提示音
- macOS：默认警报音
- Linux：根据系统配置

---

## 🧩 Qt 信号与槽机制（重要！）

这是 Qt 的核心概念，贯穿整个项目。

### 什么是信号？

**信号（Signal）**：某件事情发生了

```python
# 按钮被点击 → 发出 clicked 信号
button.clicked

# 定时器时间到 → 发出 timeout 信号
timer.timeout

# 输入框按下回车 → 发出 returnPressed 信号
input_box.returnPressed
```

### 什么是槽？

**槽（Slot）**：处理信号的方法

```python
def handle_click(self):  # 这是一个槽
    print("按钮被点击了")
```

### 如何连接？

```python
# 信号.connect(槽)
button.clicked.connect(self.handle_click)

# 点击按钮 → clicked 信号发出 → handle_click 方法被调用
```

**可视化流程**：
```
用户点击按钮
    ↓
clicked 信号发出
    ↓
connect 的作用：连接信号和槽
    ↓
handle_click 方法被调用
```

---

## 💡 实际应用总结

### 我们的提醒功能流程

```python
# 1. 用户点击"⏰ 提醒"按钮
self.reminder_button.clicked.connect(self.show_reminder_dialog)

# 2. 弹出输入框，获取分钟数
minutes, ok = QInputDialog.getInt(...)

# 3. 创建定时器
timer = QTimer(self)
timer.setSingleShot(True)
timer.setInterval(minutes * 60 * 1000)

# 4. 连接超时信号
timer.timeout.connect(lambda: self._show_reminder_notification(minutes))

# 5. 启动定时器
timer.start()

# 6. 保存引用（防止被垃圾回收）
self.active_reminders.append(timer)

# 7. 时间到了 → timeout 信号 → 弹出提示
```

---

## 🎯 下一步计划

### 第三步：保存提醒记录

**目标**：让提醒能持久化

**需要做的**：
1. 把提醒保存到 JSON 文件
2. 程序启动时加载未完成的提醒
3. 重新启动定时器

**涉及概念**：
- 文件读写（已经用过了，在 `ChatHistory` 里）
- 时间戳（记录设置时间和到期时间）
- 列表管理（多个提醒）

---

## 📖 相关文档

- **Qt 官方文档**：https://doc.qt.io/qtforpython-6/
- **QTimer 文档**：搜索 "PySide6 QTimer"
- **信号与槽**：搜索 "Qt signals and slots"

---

**学习进度**：
- ✅ 阶段 1：最小可行版本（MVP）
- ✅ 阶段 2：功能扩展 - 提醒功能（基础版）
- ⏳ 第三步：提醒持久化（下一步）

**下次学习**：保存提醒到文件，重启程序也不会丢失
