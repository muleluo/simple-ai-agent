# 简易 AI 桌面助手 - 使用指南

## 📦 项目结构

```
simple-ai-agent/
├── main.py              # 主程序文件（包含所有核心代码）
├── config.yaml          # 配置文件（API 密钥、系统提示词等）
├── requirements.txt     # Python 依赖包列表
├── README.md            # 本文档
├── data/                # 数据目录
│   └── chat_history.json  # 聊天历史记录（自动生成）
├── logs/                # 日志目录
└── assets/              # 资源目录（暂时为空）
```

---

## 🚀 快速开始

### 第一步：安装依赖

在终端（Terminal）中进入项目目录，执行：

```bash
cd simple-ai-agent
pip3 install -r requirements.txt
```

这会安装两个必需的库：
- **PySide6**：Qt 图形界面库（用于创建窗口）
- **openai**：OpenAI Python 客户端（用于调用 AI API）

---

### 第二步：配置 API 密钥

1. 打开 `config.yaml` 文件
2. 找到 `api_key` 这一行
3. 替换成你的真实 API Key：

```yaml
api:
  api_key: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # ← 改成你的密钥
```

**如何获取 API Key？**
- **OpenAI**：https://platform.openai.com/api-keys
- **国内镜像服务**：可以搜索 "OpenAI API 中转服务"

如果使用其他服务（如 Claude），修改 `base_url` 和 `model`：

```yaml
api:
  base_url: "https://api.anthropic.com/v1"  # Claude API 地址
  model: "claude-3-sonnet-20240229"         # Claude 模型
```

---

### 第三步：运行程序

在终端执行：

```bash
python3 main.py
```

你会看到一个窗口弹出：

```
┌─────────────────────────────────┐
│  🤖 简易 AI 桌面助手              │
├─────────────────────────────────┤
│                                 │
│  [对话显示区域]                  │
│                                 │
├─────────────────────────────────┤
│  [输入框]  [发送]  [清空历史]    │
└─────────────────────────────────┘
```

---

## 📝 功能说明

### 1. 发送消息
- 在输入框输入文字
- 点击"发送"按钮，或按 **回车键**
- AI 会在 2-5 秒内回复

### 2. 聊天历史
- 所有对话会自动保存到 `data/chat_history.json`
- 下次打开程序时会自动加载历史记录
- 点击"清空历史"可以删除所有记录

### 3. 注意事项
- 在 AI 回复期间，发送按钮会显示"思考中..."，无法发送新消息
- 如果 API 调用失败，会显示错误信息（例如密钥无效、网络问题等）

---

## 🔧 代码结构详解

### 核心类（Classes）

| 类名 | 作用 | 主要方法 |
|------|------|----------|
| **AIClient** | 负责与 AI API 通信 | `chat()` - 发送消息并获取回复 |
| **ChatHistory** | 管理聊天记录的保存/加载 | `add_message()` - 添加消息<br>`save()` - 保存到文件<br>`load()` - 从文件加载 |
| **ChatWorker** | 后台线程（避免界面卡顿） | `run()` - 在后台调用 API |
| **SimpleAIAgent** | 主窗口界面 | `send_message()` - 发送消息<br>`handle_ai_reply()` - 处理回复 |

### 主要流程

```
用户输入消息
    ↓
保存到历史记录
    ↓
创建后台线程 (ChatWorker)
    ↓
调用 AI API (AIClient.chat)
    ↓
收到 AI 回复
    ↓
显示在界面 + 保存到历史
```

---

## 🐛 常见问题

### 问题 1：`ModuleNotFoundError: No module named 'PySide6'`
**解决**：没有安装依赖，执行 `pip3 install -r requirements.txt`

### 问题 2：`API 调用失败：Incorrect API key`
**解决**：API 密钥错误，检查 `config.yaml` 中的 `api_key`

### 问题 3：程序运行后窗口闪退
**解决**：在终端运行，查看错误信息

### 问题 4：界面卡住不动
**解决**：检查网络连接，API 可能无法访问（可以尝试使用国内镜像服务）

---

## 📚 学习资源

- **PySide6 官方文档**：https://doc.qt.io/qtforpython-6/
- **OpenAI API 文档**：https://platform.openai.com/docs/
- **Python 多线程教程**：搜索 "Python QThread 教程"

---

## 🎯 下一步扩展方向

完成阶段 1 后，可以尝试：

1. **添加角色立绘**（阶段 2）
   - 在窗口显示一张图片
   - 根据对话内容切换表情

2. **美化界面**
   - 修改配色方案
   - 添加气泡对话框样式

3. **添加语音功能**（阶段 3）
   - 使用 `edge-tts` 或 `pyttsx3` 库
   - 让 AI 能"说话"

4. **添加工具调用**（阶段 4）
   - 让 AI 能执行操作（如搜索、设置提醒）
   - 使用 OpenAI 的 Function Calling 功能

---

## 📄 许可证

本项目仅供学习使用，随意修改和分发。
