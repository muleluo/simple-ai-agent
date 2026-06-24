# AI 桌面助手 - 错误日志与解决方案

**项目**：简易 AI 桌面助手  
**日期范围**：2026-06-22 至 2026-06-23  
**状态**：所有问题已解决 ✅

---

## 📋 问题列表

| # | 问题 | 严重程度 | 状态 |
|---|------|---------|------|
| 1 | API 无响应 | 🔴 高 | ✅ 已解决 |
| 2 | 敏感词检测错误 500 | 🔴 高 | ✅ 已解决 |
| 3 | AI 回复被截断 | 🟡 中 | ✅ 已解决 |
| 4 | 程序启动失败 | 🟡 中 | ✅ 已解决 |
| 5 | 会话标题生成异常 | 🟡 中 | ✅ 已解决 |
| 6 | 侧边栏水平滚动条 | 🟢 低 | ✅ 已解决 |
| 7 | 启动时加载旧会话 | 🟡 中 | ✅ 已解决 |

---

## 🔴 问题 1：API 无响应

### 现象
- 用户报告：API 没有响应
- 测试发现：API 可连接，但返回空内容

### 原因
使用的模型 `[福利]gemini-3.1-flash-lite-preview` 虽然可以连接，但返回的内容为空或不完整。

### 排查过程

1. **测试当前模型**：
   ```python
   模型: [福利]gemini-3.1-flash-lite-preview
   结果: ✅ API 连接成功，但回复为空字符串
   ```

2. **测试其他模型**：
   ```python
   测试模型列表：
   - gemini-3.5-flash              → ❌ 403 无权限
   - gemini-2.5-flash              → ❌ 403 无权限  
   - gemini-2.5-pro                → ❌ 403 无权限
   - [福利]gemini-3.1-flash-lite-preview → ⚠️ 可用但回复空
   - [满血A]gemini-3.1-flash-lite-preview → ✅ 可用且有回复
   - [满血E]gemini-3.5-flash        → ✅ 可用且有回复
   - [官逆C]gemini-3-flash-preview  → ✅ 可用且有回复
   ```

3. **发现规律**：
   - 不带前缀的模型 → 无权限（403）
   - 带前缀的模型 → 大部分可用
   - `[满血E]gemini-3.5-flash` → 版本最新且稳定

### 解决方案

**文件**：`config.yaml`

```yaml
# 修改前
model: "[福利]gemini-3.1-flash-lite-preview"

# 修改后
model: "[满血E]gemini-3.5-flash"
```

### 测试结果
```
✅ API 工作正常
✅ 回复内容完整
```

### 备用方案
如果 `[满血E]gemini-3.5-flash` 以后出问题，可用模型：
1. `[满血A]gemini-3.1-flash-lite-preview`
2. `[官逆C]gemini-3-flash-preview`
3. `[满血F]gemini-2.5-pro`

---

## 🔴 问题 2：敏感词检测错误（Error 500）

### 现象
```
API 调用失败：InternalServerError(
    "Error code: 500 - {
        'error': {
            'message': 'sensitive_words_detected',
            'type': 'new_api_error',
            'code': 'sensitive_words_detected'
        }
    }"
)
```

### 原因
API 服务商（gemai.cc）的内容审核系统检测到敏感词，拒绝请求。

**触发位置**：
1. 系统提示词中的描述
2. 工具定义中的 description
3. 历史对话记录

### 排查过程

#### 第一次尝试：简化系统提示词
```yaml
# 修改前（触发敏感词）
system_prompt: "你是一个友好的 AI 助手，用简洁友好的语言回答用户的问题。当用户需要设置提醒时，使用 set_reminder 工具。当用户询问需要联网查询的实时信息（如天气、新闻、价格、当前事件等）时，使用 web_search 工具..."

# 修改后
system_prompt: "你是一个助手，简洁地回答问题。"

结果：❌ 仍然报错
```

#### 第二次尝试：简化工具描述
```python
# 修改前（触发敏感词）
{
    "name": "web_search",
    "description": "搜索网络获取最新信息。当用户询问实时信息、新闻、天气、价格、当前事件等需要联网查询的内容时使用。"
}

# 修改后
{
    "name": "web_search",
    "description": "搜索信息"
}

结果：❌ 仍然报错
```

#### 第三次尝试：禁用所有工具
```python
# 临时禁用
self.tools = []

结果：✅ 测试脚本正常
      ❌ 程序界面仍报错
```

#### 第四次尝试：清空历史记录
```bash
rm -f data/chat_history.json

结果：✅ 完全解决！
```

### 根本原因
**历史对话记录中包含触发敏感词的内容**，每次发送消息都会把历史记录一起发给 API，导致持续报错。

### 解决方案

**1. 清空历史记录**：
```bash
rm -f data/chat_history.json
```

**2. 极简系统提示词**：
```yaml
system_prompt: "你是助手"
```

**3. 极简工具描述**：
```python
{
    "name": "set_reminder",
    "description": "设置提醒"
},
{
    "name": "web_search",
    "description": "搜索信息"
},
{
    "name": "search_knowledge_base",
    "description": "搜索知识库"
}
```

**4. 修改 API 调用逻辑**（只在有工具时传 tools 参数）：
```python
api_params = {
    "model": self.model,
    "messages": encoded_messages,
    "temperature": self.temperature,
    "max_tokens": self.max_tokens
}

if self.tools:
    api_params["tools"] = self.tools

response = client.chat.completions.create(**api_params, timeout=60.0)
```

### 预防措施

**避免敏感词的最佳实践**：
1. ✅ 系统提示词尽量简洁
2. ✅ 工具描述用最少的字
3. ✅ 避免使用："新闻"、"事件"、"政治"等可能敏感的词
4. ✅ 定期清理历史记录
5. ✅ 用户输入无法控制，但系统端要尽量简化

### 测试结果
```
✅ 基础对话正常
✅ 工具调用正常
✅ 无敏感词错误
```

---

## 🟡 问题 3：AI 回复被截断

### 现象
用户提问："我想学习机器学习，知识结构是怎么样的呢？"

AI 回复到一半突然中断：
```
学习机器学习（Machine Learning, ML）是一个循序渐进的过程。它的知识结构非常系统，通常可以分为**数学与编程基础**、**经典机器学习**、**深度学习**以及**实战工程**四个阶段。以下为你整理的**机器学习系统知识结构图谱**，帮助你理清学习路径：一 ### 第一阶段：基石层（数学与编程基础）这是机器学习的"地

[突然中断，没有继续]
```

用户反馈："界面卡住了"

### 原因
配置中 `max_tokens: 1000`，AI 生成到 1000 个 token 后被 API 强制截断。

**Token 换算**：
- 1000 tokens ≈ 750 个中文字
- 对于需要详细解释的问题（知识结构、代码分析等），很容易超过限制

### 问题本质
**治标不治本**：
- 增加 `max_tokens` 只能延缓问题，无法根治
- 用户不知道回复被截断了，以为程序卡住
- 没有给用户任何反馈

### 解决方案（两步）

#### 第一步：增加 max_tokens（治标）

**文件**：`config.yaml`

```yaml
# 修改前
max_tokens: 1000

# 修改后
max_tokens: 4000
```

**效果**：
- 1000 tokens ≈ 750 字
- 4000 tokens ≈ 3000 字
- 足够详细回答大部分问题

#### 第二步：添加截断检测（治本）

**文件**：`main.py`

**1. 检测截断**：
```python
# 在 chat() 方法中
response = client.chat.completions.create(**api_params, timeout=60.0)

# 检查回复是否因 token 限制被截断
finish_reason = response.choices[0].finish_reason
was_truncated = finish_reason == "length"

result = {
    "content": message.content or "",
    "tool_calls": [],
    "truncated": was_truncated  # 新增字段
}
```

**2. 提醒用户**：
```python
# 在 on_reply_received() 方法中
else:
    # 显示 AI 回复
    self.append_message("AI", reply["content"])

    # 检查是否被截断
    if reply.get("truncated", False):
        self.append_message("系统", 
            "⚠️ 回复因长度限制被截断。如需完整回答，请：\n"
            "1. 将问题拆分成多个小问题\n"
            "2. 或要求 AI 简化回答")

    # 保存到历史记录
    self.chat_history.add_message("assistant", reply["content"])
```

**3. 错误处理也返回 truncated**：
```python
except Exception as e:
    return {
        "content": f"❌ API 调用失败：{repr(e)}",
        "tool_calls": [],
        "truncated": False
    }
```

### API 返回的 finish_reason 值

| 值 | 含义 |
|---|------|
| `stop` | 正常结束（AI 完成了回答） |
| `length` | 因 max_tokens 限制被截断 |
| `tool_calls` | AI 调用了工具 |
| `content_filter` | 内容过滤（敏感词） |

### 测试结果

**测试方法**：
1. 临时设置 `max_tokens: 500`
2. 提问："详细介绍一下机器学习的知识结构"
3. 观察截断提醒

**预期结果**：
```
AI：学习机器学习（Machine Learning, ML）是一个循序渐进的过程。它的知识结构非常系统，通常可以分为**数学与编程基础**、**经典机器学习**、**深度学习**...

系统：⚠️ 回复因长度限制被截断。如需完整回答，请：
1. 将问题拆分成多个小问题
2. 或要求 AI 简化回答
```

**实际结果**：✅ 符合预期

### 用户体验改进

**改进前**：
```
用户：我想学习机器学习，知识结构是怎么样的呢？
AI：学习机器学习是一个循序渐进的过程...这是机器学习的"地
[突然中断，用户困惑]
用户：？？？卡住了？
```

**改进后**：
```
用户：我想学习机器学习，知识结构是怎么样的呢？
AI：学习机器学习是一个循序渐进的过程...这是机器学习的"地
系统：⚠️ 回复因长度限制被截断。如需完整回答，请：
1. 将问题拆分成多个小问题
2. 或要求 AI 简化回答

用户：好的，那先讲第一部分：数学基础
AI：[继续回答]
```

### 恢复正常配置

测试完成后：
```yaml
# 测试时
max_tokens: 500

# 恢复正常
max_tokens: 4000
```

---

## 🟡 问题 4：程序启动失败

### 现象
- 执行 `python main.py` 后进程启动但立即退出
- 或进程卡住无响应

### 原因
1. **命令错误**：使用 `python` 而不是 `python3`
2. **进程冲突**：多个实例同时运行
3. **GUI 问题**：后台启动时输出重定向导致 Qt 界面异常

### 解决方案

**1. 使用正确的 Python 命令**：
```bash
# ❌ 错误
python main.py

# ✅ 正确
python3 main.py
```

**2. 清理旧进程**：
```bash
# 强制终止所有相关进程
pkill -9 -f "Python main.py"

# 等待进程完全退出
sleep 2

# 重新启动
python3 main.py &
```

**3. 后台启动的正确方式**：
```bash
# 方式 1：重定向到日志（可能导致 GUI 问题）
python3 main.py > /tmp/ai_agent.log 2>&1 &

# 方式 2：直接后台（推荐）
python3 main.py &

# 方式 3：使用 nohup（持久运行）
nohup python3 main.py > /dev/null 2>&1 &
```

**4. 检查进程状态**：
```bash
# 检查是否启动
ps aux | grep "main.py" | grep -v grep

# 查看日志（如果有重定向）
tail -f /tmp/ai_agent.log
```

### 启动脚本模板

```bash
#!/bin/bash
# 启动 AI 助手的标准脚本

# 1. 清理旧进程
pkill -9 -f "Python main.py"

# 2. 等待清理完成
sleep 2

# 3. 启动新进程
python3 main.py &

# 4. 等待启动
sleep 3

# 5. 检查状态
if ps aux | grep "[P]ython main.py" > /dev/null; then
    echo "✅ 程序启动成功"
else
    echo "❌ 程序启动失败"
    exit 1
fi
```

---

## 📊 问题统计

### 按类型分类

| 类型 | 数量 | 占比 |
|------|------|------|
| API 配置问题 | 1 | 25% |
| 内容审核问题 | 1 | 25% |
| 参数配置问题 | 1 | 25% |
| 运行环境问题 | 1 | 25% |

### 按严重程度分类

| 严重程度 | 数量 | 占比 |
|---------|------|------|
| 🔴 高（影响核心功能） | 2 | 50% |
| 🟡 中（影响用户体验） | 2 | 50% |
| 🟢 低（小问题） | 0 | 0% |

### 解决时间

| 问题 | 解决时间 |
|------|---------|
| API 无响应 | 30 分钟 |
| 敏感词检测 | 1 小时 |
| 回复截断 | 30 分钟 |
| 启动失败 | 15 分钟 |
| **总计** | **2 小时 15 分钟** |

---

## 🎓 经验教训

### 1. API 调试经验

**教训**：
- 不要假设配置的模型一定可用
- API 可连接 ≠ API 可正常工作
- 空回复也是一种"成功"响应，需要特殊处理

**最佳实践**：
```python
# 创建测试脚本
def test_model(model_name):
    response = api.chat([{"role": "user", "content": "你好"}])
    
    # 检查 1：是否有错误
    if "error" in response:
        return False, "API 错误"
    
    # 检查 2：回复是否为空
    if not response.get("content", "").strip():
        return False, "回复为空"
    
    # 检查 3：回复是否完整
    if response.get("finish_reason") != "stop":
        return False, f"未正常结束：{response.get('finish_reason')}"
    
    return True, "正常"
```

### 2. 内容审核应对

**教训**：
- 第三方 API 可能有严格的内容审核
- 敏感词检测可能触发在：系统提示词、工具描述、历史记录、用户输入
- 历史记录是隐藏的"地雷"

**最佳实践**：
1. **系统提示词极简化**：
   ```
   ❌ "你是一个友好的 AI 助手，帮助用户解决问题，可以查询新闻、天气..."
   ✅ "你是助手"
   ```

2. **工具描述极简化**：
   ```
   ❌ "搜索网络获取最新信息。当用户询问实时信息、新闻、天气、价格..."
   ✅ "搜索信息"
   ```

3. **定期清理历史**：
   ```python
   # 添加清理功能
   def clear_old_history(self, days=7):
       # 删除 7 天前的记录
       cutoff = datetime.now() - timedelta(days=days)
       self.messages = [
           msg for msg in self.messages
           if datetime.fromisoformat(msg["timestamp"]) > cutoff
       ]
   ```

4. **添加历史记录清空按钮**（已实现）

### 3. 用户体验设计

**教训**：
- 技术问题要转化为用户能理解的提示
- "卡住"可能只是用户对不完整输出的感知
- 自动检测 > 手动排查

**最佳实践**：
```python
# ❌ 糟糕的设计
# AI 回复突然中断，没有任何提示

# ✅ 良好的设计
if reply.get("truncated"):
    show_warning("⚠️ 回复被截断，建议：...")
```

### 4. 调试技巧

**多层次测试**：
```bash
# 层次 1：导入测试
python3 -c "import main"

# 层次 2：语法检查
python3 -m py_compile main.py

# 层次 3：独立功能测试
python3 test_chat.py

# 层次 4：完整程序测试
python3 main.py
```

**日志记录**：
```python
# 添加详细日志
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# 关键位置添加日志
logger.debug(f"API 请求: {messages}")
logger.debug(f"API 响应: {response}")
logger.debug(f"finish_reason: {finish_reason}")
```

---

## 🔧 工具脚本

### 1. 快速诊断脚本

```bash
#!/bin/bash
# diagnose.sh - 快速诊断工具

echo "=== AI 助手诊断工具 ==="
echo

# 检查 Python
echo "1. 检查 Python..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3: $(python3 --version)"
else
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查依赖
echo "2. 检查依赖..."
python3 -c "import PySide6, openai, yaml" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 依赖完整"
else
    echo "❌ 缺少依赖，请运行: pip install -r requirements.txt"
    exit 1
fi

# 检查配置文件
echo "3. 检查配置文件..."
if [ -f "config.yaml" ]; then
    echo "✅ config.yaml 存在"
    
    # 检查 API Key
    api_key=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yaml'))['api']['api_key'])")
    if [ -n "$api_key" ]; then
        echo "✅ API Key: ${api_key:0:10}..."
    else
        echo "❌ API Key 未设置"
    fi
    
    # 检查模型
    model=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yaml'))['api']['model'])")
    echo "✅ 模型: $model"
else
    echo "❌ config.yaml 不存在"
    exit 1
fi

# 测试 API
echo "4. 测试 API..."
python3 test_chat.py 2>&1 | tail -3

# 检查进程
echo "5. 检查运行状态..."
if ps aux | grep "[P]ython main.py" > /dev/null; then
    echo "✅ 程序正在运行"
    ps aux | grep "[P]ython main.py" | awk '{print "   PID:", $2, "内存:", $6}'
else
    echo "⚠️  程序未运行"
fi

echo
echo "=== 诊断完成 ==="
```

### 2. 安全重启脚本

```bash
#!/bin/bash
# restart.sh - 安全重启脚本

echo "正在重启 AI 助手..."

# 1. 保存当前历史记录
if [ -f "data/chat_history.json" ]; then
    cp data/chat_history.json data/chat_history.backup.json
    echo "✅ 已备份历史记录"
fi

# 2. 停止旧进程
pkill -9 -f "Python main.py"
echo "✅ 已停止旧进程"

# 3. 等待清理
sleep 2

# 4. 启动新进程
python3 main.py &
NEW_PID=$!
echo "✅ 已启动新进程 (PID: $NEW_PID)"

# 5. 验证启动
sleep 3
if ps -p $NEW_PID > /dev/null; then
    echo "✅ 程序运行正常"
else
    echo "❌ 程序启动失败，恢复备份"
    cp data/chat_history.backup.json data/chat_history.json
    exit 1
fi
```

---

## 📝 配置检查清单

在部署或排查问题时，按此清单检查：

- [ ] Python 3 已安装
- [ ] 所有依赖已安装（`pip install -r requirements.txt`）
- [ ] `config.yaml` 存在且格式正确
- [ ] API Key 已设置且有效
- [ ] 模型名称正确（带前缀）
- [ ] `max_tokens` 设置合理（推荐 4000）
- [ ] 系统提示词简洁（避免敏感词）
- [ ] 工具描述简洁（避免敏感词）
- [ ] 历史记录不过大（定期清理）
- [ ] 没有重复进程运行
- [ ] 测试脚本运行正常

---

## 🎯 未来改进建议

### 1. 添加配置验证

```python
def validate_config():
    """启动时验证配置"""
    issues = []
    
    # 检查 API Key
    if not config['api']['api_key']:
        issues.append("API Key 未设置")
    
    # 检查模型
    if not config['api']['model']:
        issues.append("模型未设置")
    
    # 检查 max_tokens
    if config['api']['max_tokens'] < 500:
        issues.append(f"max_tokens 太小: {config['api']['max_tokens']}")
    
    return issues
```

### 2. 添加健康检查

```python
def health_check():
    """定期健康检查"""
    try:
        # 测试 API 连接
        response = client.chat([{"role": "user", "content": "ping"}])
        
        if response.get("content"):
            return True, "正常"
        else:
            return False, "API 返回空"
            
    except Exception as e:
        return False, str(e)
```

### 3. 自动清理历史

```python
# 在 ChatHistory 类中
def auto_cleanup(self, max_messages=100):
    """自动清理过多的历史记录"""
    if len(self.messages) > max_messages:
        # 保留最近的消息
        self.messages = self.messages[-max_messages:]
        self.save()
```

### 4. 更好的错误提示

```python
# 针对不同错误给出具体建议
error_suggestions = {
    "sensitive_words_detected": "建议：清空历史记录或简化提问",
    "timeout": "建议：检查网络连接或增加超时时间",
    "403": "建议：检查 API Key 或更换模型",
    "500": "建议：服务器错误，请稍后重试"
}
```

---

## 📞 问题报告模板

如果遇到新问题，按此模板记录：

```markdown
## 问题标题

### 现象
[描述用户看到的现象]

### 复现步骤
1. 
2. 
3. 

### 错误信息
```
[完整的错误信息]
```

### 环境信息
- Python 版本：
- 操作系统：
- 模型配置：
- max_tokens：

### 尝试过的解决方案
1. [方案 1] → [结果]
2. [方案 2] → [结果]

### 最终解决方案
[详细描述]

### 预防措施
[如何避免再次出现]
```

---

**文档版本**：v1.0  
**最后更新**：2026-06-23  
**维护者**：开发团队

**问题状态**：所有已知问题已解决 ✅

## 🟡 问题 5：会话标题生成异常

### 现象
用户报告：实现会话管理功能后，标题生成不符合预期

**问题截图**：
- 标题显示为 "好" 或 "用户" 等单字
- 标题显示为 "日常问" 这样的不完整词
- 标题直接复述用户问题："香蕉什么种类的好吃"

### 原因
尝试使用 AI API 自动生成标题，但模型返回结果不稳定：
1. **返回格式不规范** - AI 返回了回复内容而不是标题
2. **复述原句** - AI 没有提取关键词，只是复述问题
3. **返回单字** - 生成的内容被截断或格式错误

### 排查过程

#### 第一次尝试：优化 AI 提示词

**修改前**：
```python
"将用户的问题总结成一个简短的标题（5-10个字），只返回标题，不要其他内容。"
```

**修改后**：
```python
"你是标题生成助手。用户会给你一个问题，你只需要返回一个5-10字的简短标题..."
```

**结果**：❌ 仍然不稳定

#### 第二次尝试：添加示例和更严格的规则

**添加示例**：
```python
示例：
- 用户问"苹果什么品种好吃" → 标题"苹果品种推荐"
- 用户问"你好" → 标题"日常问候"
```

**结果**：❌ 改善有限

#### 第三次尝试：放弃 AI 生成，直接使用用户消息

**最终方案**：
```python
# 直接使用用户消息的前15个字作为标题
title = user_message[:15] if len(user_message) <= 15 else user_message[:15] + "..."
```

**结果**：✅ 稳定可靠

### 解决方案

**文件**：`main.py`

```python
# 如果是新对话的第一条消息，使用用户输入作为标题
if len(current_session.messages) == 0:
    title = user_message[:15] if len(user_message) <= 15 else user_message[:15] + "..."
    self.session_manager.update_session_title(current_session.session_id, title)
    self.load_session_list()
```

### 优点

1. ✅ 简单可靠 - 不依赖 AI
2. ✅ 无额外开销 - 不消耗 API
3. ✅ 即时生成 - 无延迟
4. ✅ 符合预期 - ChatGPT 也这样做

---

## 🟢 问题 6：侧边栏出现水平滚动条

### 现象
会话标题太长时，侧边栏底部出现水平滚动条

### 解决方案

#### 方案 1：禁用水平滚动条
```python
self.session_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
```

#### 方案 2：限制标题显示长度
```python
if len(title) > 20:
    display_title = title[:20] + "..."
else:
    display_title = title

item = QListWidgetItem(display_title)
item.setToolTip(session["title"])  # 鼠标悬停显示完整标题
```

✅ 测试通过

---

## 🟡 问题 7：程序启动时加载旧会话

### 现象
期望启动时显示空白新对话，但实际加载了上次的会话

### 原因
启动时自动加载了 `current_session_id` 对应的会话

### 解决方案

#### 步骤 1：SessionManager 不自动创建会话
```python
# 不自动创建新会话，由界面控制
```

#### 步骤 2：添加临时会话标记
```python
self.temp_session = None  # 临时会话标记
```

#### 步骤 3：启动时显示临时会话
```python
def load_history(self):
    self.temp_session = True  # 启动时始终显示临时会话
```

#### 步骤 4：发送消息时转为真实会话
```python
if self.temp_session:
    session_id = self.session_manager.create_new_session()
    # 使用用户消息作为标题
    title = user_message[:15] if len(user_message) <= 15 else user_message[:15] + "..."
    self.session_manager.update_session_title(session_id, title)
    self.temp_session = None
```

#### 步骤 5：点击历史会话取消临时会话
```python
def on_session_clicked(self, item):
    self.temp_session = None  # 取消临时会话
```

### 测试结果

✅ 启动后显示空白临时会话
✅ 输入消息后创建真实会话
✅ 点击历史会话正常切换

### 临时会话生命周期

```
启动 / 点击"新建对话"
    ↓
临时会话（temp_session = True）
    ↓
    ├── 输入消息 → 创建真实会话 → 保存
    └── 点击历史 → 取消临时会话 → 不保存
```

---


## 🟡 问题 8：联网搜索功能优化

### 现象
用户提出三个问题：
1. AI 每次都调用联网搜索，即使不需要
2. 搜索结果直接显示，没有经过 AI 整理
3. 缺少联网搜索的开关控制

### 解决方案

#### 1. 添加联网搜索开关

**文件**：`main.py`

```python
# 初始化时添加开关（默认关闭）
self.web_search_enabled = False

# 设置菜单中添加开关
self.web_search_action = settings_menu.addAction("🌐 联网搜索")
self.web_search_action.setCheckable(True)
self.web_search_action.setChecked(self.web_search_enabled)
self.web_search_action.triggered.connect(self.toggle_web_search)

# 切换方法
def toggle_web_search(self):
    self.web_search_enabled = self.web_search_action.isChecked()
    if self.web_search_enabled:
        self.append_message("系统", "✅ 已启用联网搜索")
    else:
        self.append_message("系统", "❌ 已禁用联网搜索")
```

#### 2. 动态工具列表

**文件**：`main.py` → `_get_enabled_tools()` 方法

```python
def _get_enabled_tools(self) -> list:
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

#### 3. AI 整理搜索结果

**新增类**：`ChatWorkerWithTools`

**职责**：
1. 第一次调用 AI API
2. 如果 AI 调用工具，执行工具
3. 将工具结果返回给 AI
4. AI 整理后返回最终答案

**关键代码**：
```python
# 第一次调用（带 tools 参数）
response = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=tools  # 包含工具列表
)

# 执行工具
if message.tool_calls:
    tool_results = execute_tools(...)
    
    # 添加工具调用和结果到消息历史
    messages.append({"role": "assistant", "content": None, "tool_calls": [...]})
    messages.append({"role": "tool", "tool_call_id": ..., "content": ...})
    
    # 第二次调用（不带 tools 参数）
    response2 = client.chat.completions.create(
        model=model,
        messages=messages
        # 不传 tools 参数！
    )
    
    return response2.message.content
```

#### 4. 联网搜索留痕

**显示搜索提示**：
```python
# 在 handle_ai_reply 中
if "search_queries" in reply and reply["search_queries"]:
    for query in reply["search_queries"]:
        self.append_message("系统", f"🔍 已联网搜索：{query}")
```

### 测试结果

✅ 联网搜索默认关闭  
✅ 用户可通过设置菜单控制  
✅ 搜索结果经过 AI 整理  
✅ 显示搜索关键词提示

---

## 🎨 问题 9：AI 输出格式美化

### 现象
AI 输出包含大量 Markdown 符号（`**`、`#`、`*`），不美观

### 解决方案

**文件**：`main.py` → `_beautify_markdown()` 方法

**转换规则**：
```python
# 标题
# 标题     → <h1 style="color: #0d47a1; font-size: 16px;">标题</h1>
## 标题    → <h2 style="color: #1565c0; font-size: 15px;">标题</h2>
### 标题   → <h3 style="color: #1976d2; font-size: 14px;">标题</h3>

# 文本样式
**粗体**   → <b style="color: #d32f2f;">粗体</b>
*斜体*     → <i style="color: #7b1fa2;">斜体</i>
`代码`     → <code style="background: #f5f5f5; color: #c62828;">代码</code>

# 列表
- 列表项   → <li style="margin-left: 20px;">列表项</li>
1. 列表项  → <li style="margin-left: 20px;"><b>1.</b> 列表项</li>
```

**实现**：
```python
def _beautify_markdown(self, text: str) -> str:
    import re
    
    # 转义 HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # 处理标题
    lines = text.split('\n')
    for line in lines:
        if line.startswith('### '):
            line = f'<h3 style="...">{line[4:]}</h3>'
        # ...
    
    # 处理粗体、斜体、代码、列表
    text = re.sub(r'\*\*(.+?)\*\*', r'<b style="...">\1</b>', text)
    # ...
    
    return text
```

### 测试结果

✅ 标题显示为蓝色大字  
✅ 粗体显示为红色  
✅ 斜体显示为紫色  
✅ 代码有灰色背景  
✅ 列表自动缩进

---

## 🔴 问题 10：Gemini API 工具调用格式错误

### 现象
```
BadRequestError: Error code: 400 - {'error': {'message': 'Please ensure that function call turn comes immediately after a user turn or after a function response turn.'}}
```

### 原因
Gemini API 对工具调用有严格要求：
1. `assistant` 消息必须包含 `content: None`
2. 第二次调用时不能传 `tools` 参数

### 排查过程

#### 第一次尝试：添加 content 字段

```python
# 修改前
self.messages.append({
    "role": "assistant",
    "tool_calls": [...]
})

# 修改后
self.messages.append({
    "role": "assistant",
    "content": None,  # 添加
    "tool_calls": [...]
})
```

**结果**：❌ 仍然报错

#### 第二次尝试：移除第二次调用的 tools 参数

**问题发现**：
```python
# 第一次调用
api_params = {
    "model": model,
    "messages": messages,
    "tools": tools  # ✅ 需要
}

# 第二次调用（错误）
response2 = client.chat.completions.create(**api_params)
# 仍然包含 tools 参数 ❌
```

**解决方案**：
```python
# 第二次调用时创建新的参数（不包含 tools）
api_params_without_tools = {
    "model": self.ai_client.model,
    "messages": self.messages,
    "temperature": self.ai_client.temperature,
    "max_tokens": self.ai_client.max_tokens
    # 不传 tools 参数
}
response2 = client.chat.completions.create(**api_params_without_tools, timeout=60.0)
```

**结果**：✅ 解决

### 测试结果

✅ 工具调用正常  
✅ AI 能整理搜索结果  
✅ 无 API 错误

### 预防措施

**Gemini API 工具调用规则**：
1. ✅ 第一次调用：传 `tools` 参数
2. ❌ 第二次调用：不传 `tools` 参数
3. ✅ assistant 消息：必须有 `content: None`
4. ✅ 消息顺序：user → assistant+tool_calls → tool_result → assistant

---

## 📊 今日工作总结

**日期**：2026-06-23

### 完成功能

1. ✅ 会话管理功能（问题 5、6、7）
2. ✅ 联网搜索优化（问题 8）
3. ✅ AI 输出美化（问题 9）
4. ✅ Gemini API 兼容（问题 10）

### 新增文件

- `session_manager.py` - 会话管理核心
- `docs/session_management.md` - 会话管理文档
- `docs/session_management_summary.md` - 简要总结
- `docs/web_search_optimization.md` - 联网搜索优化文档

### 关键技术

1. **Qt 布局** - QSplitter 分栏
2. **临时会话机制** - 启动时不保存
3. **动态工具列表** - 根据开关控制
4. **双重 API 调用** - 工具执行 + AI 整理
5. **Markdown 转 HTML** - 美化显示

### 遇到的挑战

1. AI 标题生成不稳定 → 直接使用用户消息
2. 侧边栏水平滚动 → 限制长度 + 禁用滚动条
3. 启动加载旧会话 → 临时会话机制
4. Gemini 工具调用格式 → 研究 API 规则

### 学习要点

1. **会话管理模式** - 类似 ChatGPT
2. **工具调用流程** - 两次 API 调用
3. **Gemini API 限制** - 严格的消息格式
4. **Markdown 渲染** - 正则表达式转换
5. **用户体验优化** - 搜索留痕、格式美化

---

**维护者**：开发团队  
**最后更新**：2026-06-23
