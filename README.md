# mm - 智能命令行助手

`mm` 是一个基于大型语言模型 (LLM) 的智能命令行助手。您可以用自然语言向它提问，它会尝试将您的问题转换成在当前操作系统 (Windows, Linux, macOS) 和 Shell 环境 (PowerShell, Bash等) 下可执行的命令。

## 特性

*   **自然语言转命令行**：用日常语言描述您的需求。
*   **多平台支持**：可在 Windows, Linux, macOS 上运行。
*   **Shell 适应性**：根据当前 Shell (如 PowerShell, CMD, bash) 生成相应命令。
*   **安全交互**：默认在执行命令前请求用户确认 (可配置)。
*   **命令修改**：允许用户在 AI 生成命令后修改原始提问并重新生成。
*   **剪贴板复制**：方便地将生成的命令复制到剪贴板。
*   **智能缓存系统** ⭐：
    - **双层缓存架构**：精确匹配缓存 + 语义相似度缓存
    - **节省 API 调用**：重复或相似查询直接从缓存获取结果
    - **快速响应**：缓存命中时响应时间 < 100ms
    - **智能匹配**：使用 TF-IDF 和余弦相似度匹配相似查询
    - **自动管理**：LRU 淘汰策略和自动持久化
*   **高度可配置**：通过 `.env` 文件轻松配置 API 密钥、模型、行为参数和缓存设置。

## 安装与配置

有多种方式可以安装和使用 `mm`：

### 方式一：直接下载可执行文件 (推荐给 Windows 非开发者用户)

如果您使用的是 Windows 系统并且不希望进行复杂的环境配置，可以直接下载预编译的可执行文件。

1.  访问项目的 [Releases 页面](https://github.com/LeoMjl/mm/releases) 
2.  下载最新的 `mm.exe` 文件。
3.  **重要：配置 `.env` 文件**
    *   **核心原则**：`mm` 程序在启动时，会优先尝试从其可执行文件 (`mm.exe`) 或脚本 (`mm.py`) 所在的目录加载名为 `.env` 的配置文件。如果在该位置找不到 `.env` 文件，它会尝试从您执行 `mm` 命令时所在的**当前工作目录**加载。
    *   **对于 `mm.exe` 用户**：请在 `mm.exe` 文件所在的同一个文件夹内，创建一个名为 `.env` 的文本文件。
    *   复制项目中的 `.env.example` 文件的内容到您创建的 `.env` 文件中，或者参考以下模板：

    ```env
    # ===== 基本配置 =====
    # 【必填项】您的 OpenAI API 密钥
    OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    # 【必填项】您希望使用的语言模型的名称
    MODEL_NAME="gpt-3.5-turbo"

    # 【可选项】如果您使用非 OpenAI 官方的兼容 API
    # OPENAI_API_BASE="https://api.deepseek.com/v1"

    # 【可选项】模型温度 (0.0 - 2.0)
    MODEL_TEMPERATURE="0.7"

    # 【可选项】模型生成内容的最大长度 (tokens)
    MODEL_MAX_TOKENS="2048"

    # 【可选项】安全模式开关 (1 表示开启，0 表示关闭)
    SAFETY="1"

    # 【可选项】是否允许在交互中修改命令 (1 表示允许，0 表示不允许)
    MODIFY="1"

    # 【可选项】建议命令在终端中显示的颜色
    SUGGESTED_COMMAND_COLOR="yellow"

    # ===== 缓存配置 ⭐ =====
    # 【可选项】缓存功能开关 (true=开启, false=关闭)
    MM_CACHE_ENABLED="true"

    # 【可选项】缓存存储目录 (默认: ~/.mm_cache)
    # MM_CACHE_DIR="C:\\Users\\YourName\\.mm_cache"

    # 【可选项】精确匹配缓存最大条目数
    MM_CACHE_MAX_EXACT="1000"

    # 【可选项】语义相似度缓存最大条目数
    MM_CACHE_MAX_SEMANTIC="500"

    # 【可选项】语义相似度匹配阈值 (0.0-1.0)
    MM_CACHE_SIMILARITY_THRESHOLD="0.85"

    # 【可选项】精确匹配缓存过期时间（天）
    MM_CACHE_EXACT_TTL_DAYS="30"

    # 【可选项】语义相似度缓存过期时间（天）
    MM_CACHE_SEMANTIC_TTL_DAYS="7"

    # 【可选项】自动保存间隔（操作次数）
    MM_CACHE_AUTO_SAVE_INTERVAL="10"

    # 【可选项】是否显示缓存命中提示 (true/false)
    MM_CACHE_SHOW_HITS="true"

    # 【可选项】调试模式 (true/false)
    MM_CACHE_DEBUG="false"
    ```
    *   **请务必将 `OPENAI_API_KEY` 替换为您自己的有效 OpenAI API 密钥。** 其他参数可根据需要调整。
4.  **（可选但推荐）将 `mm.exe` 所在目录添加到系统 PATH 环境变量：**
    为了能够在任何路径下直接通过输入 `mm <您的指令>` 来运行程序，而不是每次都需要切换到 `mm.exe` 所在的目录或者输入完整路径，您可以将其所在目录添加到系统的 `PATH` 环境变量中。步骤如下 (以 Windows 10/11 为例)：
    1.  **复制 `mm.exe` 所在的文件夹路径。** 例如，如果您将 `mm.exe` 放在 `D:\Tools\mm` 文件夹下，就复制这个路径。
    2.  在 Windows 搜索框中输入“环境变量”，然后选择“编辑系统环境变量”。
    3.  在弹出的“系统属性”对话框中，点击右下角的“环境变量(N)...”按钮。
    4.  在“环境变量”对话框中，找到“系统变量(S)”区域下的“Path”变量，选中它，然后点击“编辑(E)...”按钮。
    5.  在“编辑环境变量”对话框中，点击右侧的“新建(N)”按钮。
    6.  将您在步骤1中复制的 `mm.exe` 文件夹路径粘贴到新出现的文本框中。
    7.  点击“确定”关闭所有打开的对话框以保存更改。
    8.  **重要**：为了使 `PATH` 环境变量的更改生效，您可能需要**关闭并重新打开**所有已打开的命令行窗口 (CMD, PowerShell 等)。在某些情况下，可能需要重启电脑。
    9.  配置完成后，您就可以在任何目录下打开新的命令行窗口，直接输入 `mm <您的自然语言指令>` 来使用它了。
5.  现在您可以双击运行 `mm.exe` (如果未配置PATH) 或者在命令行中通过 `mm <您的自然语言指令>` (如果已配置PATH) 来使用它。

### 方式二：通过 pip 安装 ⚠️ (暂不可用)

> **注意**：此安装方式目前暂不可用，正在开发中。请使用方式一进行安装。

~~如果您熟悉 Python 和 pip，可以通过以下步骤安装：~~

~~1. 确保已安装 Python 3.7+ 和 pip~~
~~2. 通过 pip 安装：~~
```bash
# 此功能暂不可用
# pip install mm-cmdbot
```

**推荐使用方式一直接下载可执行文件。**

### `.env` 文件参数说明

#### 基本配置
*   `OPENAI_API_KEY` (必需): 您的 OpenAI API 密钥。
*   `MODEL_NAME` (必需): 您希望使用的语言模型名称 (例如 `gpt-3.5-turbo`, `gpt-4`, `deepseek-chat` 等)。
*   `OPENAI_API_BASE` (可选): 如果您使用非 OpenAI 官方的兼容 API (如 DeepSeek, Moonshot, OpenRouter, Groq 或自建服务)，请在此处填写其基础 URL。如果使用官方 OpenAI API，请注释掉或留空此行。
*   `MODEL_TEMPERATURE` (可选): 模型温度，控制生成文本的随机性 (0.0 - 2.0)。默认 `0.7`。
*   `MODEL_MAX_TOKENS` (可选): 模型生成内容的最大长度 (tokens)。默认 `2048`。
*   `SAFETY` (可选): 安全模式开关 (1=开启, 0=关闭)。开启时，执行命令前会提示确认。默认 `1`。
*   `MODIFY` (可选): 是否允许在交互中修改命令 (1=允许, 0=不允许)。默认 `1`。
*   `SUGGESTED_COMMAND_COLOR` (可选): 生成的命令在终端显示的颜色 (如 `red`, `green`, `yellow`)。默认 `yellow`。

#### 缓存配置 ⭐
*   `MM_CACHE_ENABLED` (可选): 缓存功能开关 (`true`=开启, `false`=关闭)。默认 `true`。
*   `MM_CACHE_DIR` (可选): 缓存存储目录。默认 `~/.mm_cache`。
*   `MM_CACHE_MAX_EXACT` (可选): 精确匹配缓存最大条目数。默认 `1000`。
*   `MM_CACHE_MAX_SEMANTIC` (可选): 语义相似度缓存最大条目数。默认 `500`。
*   `MM_CACHE_SIMILARITY_THRESHOLD` (可选): 语义相似度匹配阈值 (0.0-1.0)。默认 `0.85`。
*   `MM_CACHE_EXACT_TTL_DAYS` (可选): 精确匹配缓存过期时间（天）。默认 `30`。
*   `MM_CACHE_SEMANTIC_TTL_DAYS` (可选): 语义相似度缓存过期时间（天）。默认 `7`。
*   `MM_CACHE_AUTO_SAVE_INTERVAL` (可选): 自动保存间隔（操作次数）。默认 `10`。
*   `MM_CACHE_SHOW_HITS` (可选): 是否显示缓存命中提示 (`true`/`false`)。默认 `true`。
*   `MM_CACHE_DEBUG` (可选): 调试模式 (`true`/`false`)。默认 `false`。

## 使用方法

基本语法：

```bash
mm "您的自然语言描述"
```

使用 `-a` 参数可以自动执行命令（跳过确认）：

```bash
mm -a "您的自然语言描述"
```

### 基本使用示例

```bash
# 列出当前目录的文件
mm "列出当前目录的文件"

# 查找包含特定文本的文件
mm "查找包含 'hello' 的文件"

# 创建一个新目录
mm "创建一个名为 'test' 的目录"

# 压缩文件
mm "将 documents 文件夹压缩为 backup.zip"

# 查看系统信息
mm "显示系统信息"

# 自动执行（跳过确认）
mm -a "显示当前时间"
```

### 缓存管理 ⭐

MM 提供了强大的缓存管理工具，帮助您监控和管理缓存：

```bash
# 查看缓存统计信息
python cache_manager.py stats

# 列出所有缓存条目
python cache_manager.py list

# 搜索特定查询的缓存
python cache_manager.py search "列出文件"

# 清理过期缓存
python cache_manager.py clean

# 清理所有缓存
python cache_manager.py clean --all
```

#### 缓存工作原理

1. **精确匹配**：相同查询直接返回缓存结果
2. **语义匹配**：相似查询（如"列出文件"和"显示目录内容"）也能命中缓存
3. **自动管理**：缓存会自动保存到磁盘，重启后依然有效
4. **智能淘汰**：使用 LRU 策略，自动清理最少使用的缓存

#### 缓存效果示例

```bash
# 第一次查询（调用 API）
$ mm "列出当前目录的文件"
💭 正在思考...
建议命令: ls -la

# 相同查询（精确匹配缓存）
$ mm "列出当前目录的文件"
🎯 缓存命中！
建议命令: ls -la

# 相似查询（语义匹配缓存）
$ mm "显示目录内容"
🎯 语义缓存命中！（相似度: 0.89）
建议命令: ls -la
```

**关于 `.env` 文件的加载位置：**
`mm` 会按以下顺序查找并加载 `.env` 文件：
1.  **程序所在目录**：即 `mm.exe` (通过 PyInstaller 打包) 或 `mm.py` (直接运行脚本) 或 `mm` (通过 `pip install` 安装的可执行命令) 所在的目录。
2.  **当前工作目录**：即您在终端中执行 `mm` 命令时所在的目录。

建议将 `.env` 文件放置在程序所在目录，这样无论您在哪个路径下调用 `mm` 命令，都能使用统一的配置。

参数：
*   `-a`: 自动执行生成的命令（跳过确认步骤）。

## 性能优化建议 🚀

### 缓存优化
- **调整缓存大小**：根据使用频率调整 `MM_CACHE_MAX_EXACT` 和 `MM_CACHE_MAX_SEMANTIC`
- **相似度阈值**：降低 `MM_CACHE_SIMILARITY_THRESHOLD` 可提高缓存命中率，但可能降低精确度
- **定期清理**：使用 `python cache_manager.py clean` 清理过期缓存

### API 调用优化
- **模型选择**：`gpt-3.5-turbo` 速度更快，`gpt-4` 准确性更高
- **温度设置**：较低的 `MODEL_TEMPERATURE` (0.3-0.5) 可获得更一致的结果
- **Token 限制**：适当的 `MODEL_MAX_TOKENS` 可减少响应时间

## 故障排除 🔧

### 常见问题

**Q: 缓存不工作？**
```bash
# 检查缓存配置
python -c "from cache_config import get_cache_config; print(get_cache_config())"

# 查看缓存状态
python cache_manager.py stats
```

**Q: API 调用失败？**
- 检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确
- 验证 `OPENAI_API_BASE` 设置（如使用第三方 API）
- 确认网络连接正常

**Q: 命令生成不准确？**
- 尝试更详细的描述
- 调整 `MODEL_TEMPERATURE` 参数
- 考虑使用更强大的模型（如 `gpt-4`）

**Q: 缓存占用空间过大？**
```bash
# 清理过期缓存
python cache_manager.py clean

# 清理所有缓存
python cache_manager.py clean --all
```

### 调试模式
启用调试模式获取详细信息：
```bash
# 在 .env 文件中设置
MM_CACHE_DEBUG=true
```

## 文档资源 📚

- **[配置示例](.env.example)** - 完整的配置文件模板

## 贡献指南 🤝

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

### 开发环境设置
```bash
# 克隆仓库
git clone <repository-url>
cd mm

# 安装依赖
pip install -r requirements.txt

# 运行测试
python test_cache.py
```

## 许可证 📄

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 更新日志 📝

### v0.8.0 (最新)
- ✨ 新增智能缓存系统
- 🚀 双层缓存架构（精确匹配 + 语义相似度）
- 📊 缓存管理工具
- 🎯 显著提升响应速度
- 💾 自动持久化缓存

### v0.7.x
- 🔧 改进命令生成准确性
- 🛡️ 增强安全模式
- 🎨 优化用户界面

---

**享受更快、更智能的命令行体验！** 🎉

如有问题或建议，请提交 [Issue](../../issues) 或联系开发团队。

## 使用示例 💡

### 基础操作示例

```bash
# 文件和目录操作
mm "列出当前目录的所有文件"
mm "创建一个名为 project 的文件夹"
mm "将所有 .txt 文件移动到 backup 文件夹"
mm "压缩 documents 文件夹为 backup.zip"

# 系统信息查询
mm "显示当前时间和日期"
mm "查看系统内存使用情况"
mm "显示我的 IP 地址"
mm "检查磁盘空间使用情况"

# 进程和服务管理
mm "查看正在运行的 Python 进程"
mm "结束名为 notepad 的进程"
mm "检查端口 8080 是否被占用"

# 文本处理
mm "在 config.txt 中查找包含 'database' 的行"
mm "统计 README.md 文件的行数"
mm "将文件内容按字母顺序排序"
```

### 高级用法示例

```bash
# 自动执行模式
mm -a "显示当前时间"

# 复杂文件操作
mm "查找所有大于 100MB 的文件"
mm "批量重命名所有 .jpeg 文件为 .jpg"
mm "创建包含系统信息的报告文件"

# 网络和安全
mm "测试与 google.com 的网络连接"
mm "查看最近的登录记录"
mm "检查防火墙状态"

# 开发相关
mm "启动本地 HTTP 服务器在端口 8000"
mm "查找项目中所有的 TODO 注释"
mm "统计代码行数（排除注释）"
```

---

**🎉 感谢使用 MM！享受更智能、更快速的命令行体验！**
