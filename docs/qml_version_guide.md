# QML 版本使用说明

**日期**：2026-06-25  
**版本**：v3.0 QML  
**状态**：✅ 基础功能完成

---

## 📋 文件说明

### 新增文件

1. **qml/MainWindow.qml** - 主窗口界面
   - 左侧会话列表
   - 右侧聊天区域
   - 现代化 UI 设计

2. **qml/MessageBubble.qml** - 消息气泡组件
   - 支持用户/AI/系统三种消息类型
   - 带阴影和动画效果

3. **main_qml.py** - QML 版本主程序
   - Python 与 QML 桥接
   - 数据模型管理

### 保留文件

- **main.py** - 原 QWidget 版本（可随时切换回去）

---

## 🎨 视觉效果

### 1. 阴影效果
- **按钮阴影**：所有按钮带有轻微阴影
- **卡片阴影**：消息区域、输入框都有卡片阴影
- **消息气泡阴影**：每条消息都有独立阴影

### 2. 动画效果
- **按钮弹性动画**：点击时有 0.95x 缩放效果
- **消息出现动画**：新消息淡入 + 缩放动画
- **颜色过渡动画**：所有颜色变化都有 200ms 平滑过渡

### 3. 交互光效
- **悬停高亮**：按钮悬停时背景变化
- **焦点光效**：输入框获取焦点时有蓝色边框
- **发送按钮发光**：悬停时蓝色光晕增强

### 4. 移除 Emoji
- ✅ 所有图标都改为文字
- "新建对话" 按钮使用 "+"
- 设置按钮使用 "···"
- 无任何 emoji 图标

---

## 🚀 启动方式

### QML 版本（新）

```bash
python3 main_qml.py
```

### QWidget 版本（旧）

```bash
python3 main.py
```

---

## 🎯 已实现功能

### 基础功能
- ✅ 会话列表显示
- ✅ 创建新对话
- ✅ 切换会话
- ✅ 发送消息
- ✅ 清空对话
- ✅ 删除会话

### AI 功能
- ✅ AI API 调用（OpenAI 兼容接口）
- ✅ 工具调用支持（Function Calling）
- ✅ 联网搜索（DuckDuckGo）
- ✅ 知识库搜索
- ✅ 提醒功能（后端支持，待 UI 集成）
- ✅ 异步处理（QThread）
- ✅ 历史消息上下文

### 视觉效果
- ✅ 阴影效果（DropShadow）
- ✅ 弹性动画（scale + easing）
- ✅ 颜色过渡动画
- ✅ 消息淡入动画
- ✅ 悬停光效

### UI 细节
- ✅ 无 emoji 图标
- ✅ 圆角设计
- ✅ 自定义滚动条
- ✅ 选中指示器
- ✅ 时间戳显示
- ✅ "正在思考"提示
- ✅ 搜索提示显示

---

## 🔧 待完成功能

### 对话框
- ⏳ 重命名会话对话框
- ⏳ 确认删除对话框
- ⏳ 提醒设置对话框
- ⏳ 文件选择对话框

### 美化功能
- ⏳ Markdown 渲染（HTML 格式）
- ⏳ 代码高亮
- ⏳ 加载动画优化
- ⏳ 输入中提示优化

---

## 📐 技术架构

### QML 部分
```
MainWindow.qml
├── 左侧边栏
│   ├── 标题
│   ├── 新建按钮（阴影 + 动画）
│   └── 会话列表（ListView）
└── 右侧聊天区
    ├── 标题栏（卡片阴影）
    ├── 消息列表（ListView）
    │   └── MessageBubble 组件
    └── 输入区（卡片阴影）
        ├── 输入框
        └── 按钮行
```

### Python 部分
```
main_qml.py
├── SessionListModel（会话列表数据）
├── MessageListModel（消息列表数据）
├── PyBridge（Python-QML 桥接）
│   ├── 会话管理
│   ├── 消息发送
│   └── 工具调用
└── QML 引擎加载
```

---

## 🎨 配色方案

```python
primaryColor: "#2563eb"      # 主色调（蓝色）
surfaceColor: "#ffffff"       # 表面白色
backgroundColor: "#f8fafc"    # 背景浅灰
borderColor: "#e2e8f0"        # 边框颜色
textPrimary: "#1e293b"        # 主文字
textSecondary: "#64748b"      # 次要文字
hoverColor: "#f1f5f9"         # 悬停背景
selectedColor: "#dbeafe"      # 选中背景
```

---

## 🔄 Git 分支管理

### 当前分支结构

```
main           ← QWidget 版本（稳定）
└── qml-ui     ← QML 版本（开发中）
```

### 切换回 QWidget 版本

```bash
git checkout main
python3 main.py
```

### 切换到 QML 版本

```bash
git checkout qml-ui
python3 main_qml.py
```

---

## 📝 下一步工作

### 优先级 P0（核心功能）

1. **集成 AI API**
   - 将原 `main.py` 的 AI 调用逻辑迁移到 `PyBridge`
   - 实现 `ChatWorkerWithTools` 的 QML 版本
   - 支持工具调用（提醒、搜索、知识库）

2. **实现对话框**
   - 重命名会话对话框
   - 确认删除对话框
   - 提醒设置对话框
   - 文件选择对话框

### 优先级 P1（增强体验）

3. **Markdown 渲染**
   - 将 `_beautify_markdown()` 集成到消息显示
   - 支持代码块高亮
   - 支持表格、列表等

4. **加载状态**
   - AI 思考中的加载动画
   - 消息发送中的状态指示
   - 文件上传进度

### 优先级 P2（锦上添花）

5. **更多动画**
   - 会话切换过渡动画
   - 菜单弹出动画
   - 消息删除动画

6. **可配置主题**
   - 支持深色模式
   - 支持自定义配色
   - 支持字体大小调整

---

## 🐛 已知问题

### 样式警告（已解决）
- ✅ 设置 `QT_QUICK_CONTROLS_STYLE=Basic` 解决

### Qt 版本兼容
- ✅ 使用 `Qt5Compat.GraphicalEffects` 代替 `QtQuick.Effects`
- ✅ 使用 `DropShadow` 代替 `MultiEffect`

---

## 💡 学习要点

### QML 核心概念

1. **声明式 UI**：通过属性和层级描述界面
2. **数据绑定**：属性自动同步更新
3. **信号槽**：事件驱动的通信机制
4. **动画系统**：`Behavior` 和 `Animation`
5. **Layer Effects**：阴影、模糊等视觉效果

### Python-QML 桥接

1. **QObject 子类**：暴露给 QML 的 Python 对象
2. **@Slot 装饰器**：QML 可调用的 Python 方法
3. **Signal**：Python 向 QML 发送信号
4. **Property**：QML 可读取的 Python 属性
5. **QAbstractListModel**：列表数据模型

### Qt Quick Controls

1. **Button**：自定义 background 和 contentItem
2. **ListView**：列表视图 + delegate
3. **TextArea**：多行文本输入
4. **Menu**：上下文菜单
5. **SplitView**：可拖动分栏

---

**维护者**：开发团队  
**最后更新**：2026-06-25
