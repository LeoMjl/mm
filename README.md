# mm - 智能命令行助手

`mm` 是一个基于大型语言模型 (LLM) 的智能命令行助手。您可以用自然语言向它提问，它会尝试将您的问题转换成在当前操作系统 (Windows, Linux, macOS) 和 Shell 环境 (PowerShell, Bash等) 下可执行的命令。

## 特性

*   自然语言转命令行：用日常语言描述您的需求。
*   多平台支持：可在 Windows, Linux, macOS 上运行。
*   Shell 适应性：根据当前 Shell (如 PowerShell, CMD, bash) 生成相应命令。
*   安全交互：默认在执行命令前请求用户确认 (可配置)。
*   命令修改：允许用户在 AI 生成命令后修改原始提问并重新生成。
*   剪贴板复制：方便地将生成的命令复制到剪贴板。
*   高度可配置：通过 `.env` 文件轻松配置 API 密钥、模型、行为参数等。

## 安装与配置

有多种方式可以安装和使用 `mm`：

### 方式一：直接下载可执行文件 (推荐给 Windows 非开发者用户)

如果您使用的是 Windows 系统并且不希望进行复杂的环境配置，可以直接下载预编译的可执行文件。

1.  访问项目的 [Releases 页面](https://github.com/LeoMjl/mm/releases) (如果尚未创建 Releases，可以先跳过此链接或后续补充)
2.  下载最新的 `mm.exe` 文件。
3.  **重要：配置 `.env` 文件**
    *   **核心原则**：`mm` 程序在启动时，会优先尝试从其可执行文件 (`mm.exe`) 或脚本 (`mm.py`) 所在的目录加载名为 `.env` 的配置文件。如果在该位置找不到 `.env` 文件，它会尝试从您执行 `mm` 命令时所在的**当前工作目录**加载。
    *   **对于 `mm.exe` 用户**：请在 `mm.exe` 文件所在的同一个文件夹内，创建一个名为 `.env` 的文本文件。
    *   复制项目中的 `.env.example` 文件的内容到您创建的 `.env` 文件中，或者参考以下模板：

    ```env
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

### 方式二：通过 pip 安装 (推荐给 Python 开发者或熟悉命令行的用户)

如果您熟悉 Python 和 pip，可以通过以下步骤安装：

1.  **确保已安装 Python 3.7+ 和 pip。**
2.  克隆本项目仓库 (如果您尚未克隆)：
    ```bash
    git clone https://github.com/LeoMjl/mm.git
    cd mm
    ```
3.  **(推荐) 创建并激活虚拟环境：**
    ```bash
    python -m venv venv
    # Windows (PowerShell)
    .\venv\Scripts\Activate.ps1
    # Windows (CMD)
    # .\venv\Scripts\activate.bat
    # macOS/Linux
    # source ./venv/bin/activate
    ```
4.  **安装依赖并安装 `mm`：**
    在项目根目录下 (包含 `setup.py` 文件的目录)，运行：
    ```bash
    pip install .
    ```
    如果您希望从 PyPI 直接安装 (假设项目已发布到 PyPI，包名为 `mm-cmdbot`)：
    ```bash
    pip install mm-cmdbot
    ```
5.  **重要：配置 `.env` 文件**
    *   **核心原则**：`mm` 程序在启动时，会优先尝试从其可执行文件 (`mm.exe`) 或脚本 (`mm.py`) 所在的目录加载名为 `.env` 的配置文件。如果在该位置找不到 `.env` 文件，它会尝试从您执行 `mm` 命令时所在的**当前工作目录**加载。
    *   **对于通过 `pip install .` 安装的用户**：
        *   当您通过 `pip install .` 安装后，`mm` 命令通常会被安装到 Python 环境的 `Scripts` (Windows) 或 `bin` (Linux/macOS) 目录下。程序会首先尝试从这个目录（即 `mm` 可执行文件所在的目录）加载 `.env` 文件。
        *   因此，您可以将 `.env` 文件放置在 `mm` 可执行文件所在的目录中（例如，Python 的 `Scripts` 目录）。
        *   或者，您也可以在您**希望运行 `mm` 命令的当前工作目录**下放置 `.env` 文件，如果程序在可执行文件目录未找到 `.env`，则会使用当前工作目录的配置。
    *   复制项目中的 `.env.example` 文件的内容到您选择的 `.env` 文件位置，或者参考方式一中提供的 `.env` 模板进行配置。
    *   **请务必将 `OPENAI_API_KEY` 替换为您自己的有效 OpenAI API 密钥。**

### `.env` 文件参数说明

*   `OPENAI_API_KEY` (必需): 您的 OpenAI API 密钥。
*   `MODEL_NAME` (必需): 您希望使用的语言模型名称 (例如 `gpt-3.5-turbo`, `gpt-4`, `deepseek-chat` 等)。
*   `OPENAI_API_BASE` (可选): 如果您使用非 OpenAI 官方的兼容 API (如 DeepSeek, Moonshot, OpenRouter, Groq 或自建服务)，请在此处填写其基础 URL。如果使用官方 OpenAI API，请注释掉或留空此行。
*   `MODEL_TEMPERATURE` (可选): 模型温度，控制生成文本的随机性 (0.0 - 2.0)。默认 `0.7`。
*   `MODEL_MAX_TOKENS` (可选): 模型生成内容的最大长度 (tokens)。默认 `2048`。
*   `SAFETY` (可选): 安全模式开关 (1=开启, 0=关闭)。开启时，执行命令前会提示确认。默认 `1`。
*   `MODIFY` (可选): 是否允许在交互中修改命令 (1=允许, 0=不允许)。默认 `1`。
*   `SUGGESTED_COMMAND_COLOR` (可选): 生成的命令在终端显示的颜色 (如 `red`, `green`, `yellow`)。默认 `yellow`。

## 使用方法

安装并正确配置 `.env` 文件后 (确保 `OPENAI_API_KEY` 已设置)，打开您的终端 (PowerShell, CMD, Bash 等)。程序会自动检测当前使用的Shell环境并生成相应的命令，然后输入：

**关于 `.env` 文件的加载位置：**
`mm` 会按以下顺序查找并加载 `.env` 文件：
1.  **程序所在目录**：即 `mm.exe` (通过 PyInstaller 打包) 或 `mm.py` (直接运行脚本) 或 `mm` (通过 `pip install` 安装的可执行命令) 所在的目录。
2.  **当前工作目录**：即您在终端中执行 `mm` 命令时所在的目录。

建议将 `.env` 文件放置在程序所在目录，这样无论您在哪个路径下调用 `mm` 命令，都能使用统一的配置。

现在，您可以输入：

```bash
mm <您的自然语言指令>
```

例如：

```bash
mm 列出当前目录下所有的 txt 文件
mm 我现在的 IP 地址是什么
mm -a 创建一个名为 backup 的文件夹然后把所有的 .log 文件复制进去
```

参数：
*   `-a`: 即使在安全模式关闭的情况下，也强制在执行命令前进行用户确认。

## 示例

以下是一些如何使用此实用程序的示例。

```
mm 现在几点了？
mm 北京的日期和时间是什么？
mm 给我看一些有趣的 unicode 字符
mm 我的用户名和机器名是什么？
mm 是否有 nano 进程正在运行？
mm 查找 index.html 中的所有唯一网址
mm 创建一个名为 test.txt 的文件并将我的用户名写入其中
mm 打印 test.txt 文件的内容
mm -a 删除 test.txt 文件
mm 比特币当前以美元计价的价格是多少？
mm 比特币当前以美元计价的价格是多少？仅提取价格
mm 查看 ssh 日志，看是否有任何可疑登录
mm 查看 ssh 日志并显示所有最近的登录
mm 用户 hacker 现在是否已登录？
mm 我是否正在运行防火墙？
mm 创建一个 name.txt 文件，并逐行向其中添加 10 个基于国家命名的人名，然后显示其内容
mm 编写一个名为 scan.sh 的新 bash 脚本文件，其内容是迭代  name.txt并对每个主机调用默认的 nmap 扫描。然后显示该文件。
mm 编写一个名为 scan.sh 的新 bash 脚本文件，其内容是迭代 hostnames.txt 并对每个主机调用默认的 nmap 扫描。然后显示该文件。使其包含多行注释和注解。
```

## 感谢！

感谢您的使用！如果您有任何问题或建议，欢迎通过 GitHub Issues 提出。

## 许可证

MIT
