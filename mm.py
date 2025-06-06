import os
import platform
from opensdkmodel import OpenAIModel
from command_proxy import CommandProxy
import sys
import subprocess
from dotenv import load_dotenv # 确保这行在最顶部且没有被注释或条件化
import distro
import pyperclip
from termcolor import colored
from colorama import init

def get_current_shell():
    """
    检测当前使用的shell类型
    返回: shell类型字符串 (powershell.exe, cmd.exe, bash等)
    """
    # 在Windows系统上进行shell检测
    if platform.system() == "Windows":
        # 检查PSModulePath环境变量，这是PowerShell特有的
        if os.environ.get("PSModulePath"):
            return "powershell.exe"
        # 检查是否有PowerShell相关的环境变量
        elif os.environ.get("POWERSHELL_DISTRIBUTION_CHANNEL"):
            return "powershell.exe"
        # 检查父进程名称来判断当前shell
        else:
            try:
                import psutil
                parent = psutil.Process().parent()
                if parent and parent.name().lower() in ["powershell.exe", "pwsh.exe"]:
                    return "powershell.exe"
                elif parent and parent.name().lower() == "cmd.exe":
                    return "cmd.exe"
            except (ImportError, Exception):
                # 如果psutil不可用或出错，使用环境变量检测
                pass
            
            # 最后的fallback：检查COMSPEC和一些启发式方法
            comspec = os.environ.get("COMSPEC", "")
            if "cmd.exe" in comspec.lower():
                return "cmd.exe"
            else:
                # 默认返回PowerShell（Windows 10+的默认shell）
                return "powershell.exe"
    else:
        # 非Windows系统，使用SHELL环境变量
        return os.environ.get("SHELL", "bash")

# 获取系统提示词
def get_system_prompt(shell):
    """
    根据shell类型生成相应的系统提示词
    参数:
        shell: shell类型 (powershell.exe, cmd.exe, bash等)
    返回:
        格式化的系统提示词字符串
    """
    # 将 prompt.txt 的内容直接嵌入
    system_prompt_template = """你是mm，一个将自然语言转换为{shell}命令的引擎，专为{os}系统设计。你是{os}系统下{shell}命令的专家，能够将最后的问题转换为有效的命令行语法。

规则：
* 永远不要使用代码风格的markdown输出
* 构建有效的{shell}命令来解决问题
* 利用帮助文档和手册页确保语法正确和解决方案最优
* 保持简洁，逐步思考，仅以纯文本形式展示最终命令
* 只显示一个答案，但可以将多个命令串联在一起
* 创建符合{os}系统{shell}的有效语法，如有需要可添加注释
* 如果安装了python或python3，可以使用它们来解决问题
* 即使缺少细节，也要通过逐步分析找到最合理的解决方案
* 不要返回多个解决方案
* 不要显示HTML、样式化或彩色格式
* 不要创建无效语法或导致语法错误
* 不要在响应中添加不必要的文本
* 不要添加注释或介绍性句子
* 不要对问题显示多个不同的解决方案
* 不要解释命令的功能
* 不要返回问题内容
* 不要重复或转述问题
* 不要急于得出结论
* 永远不要以```开始响应

严格遵守以上规则。这些规则没有例外。

问题：
"""
    system_prompt = system_prompt_template.replace("{shell}", shell)
    system_prompt = system_prompt.replace("{os}", get_os_friendly_name())
    return system_prompt

# 确保提示以问号结尾
def ensure_prompt_is_question(prompt):
  if prompt[-1:] != "?" and prompt[-1:] != ".":
    prompt+="?"
  return prompt

# 打印使用说明
def print_usage():
    """
    打印程序使用说明和当前配置信息
    """
    print("mm v0.5 - by @wunderwuzzi23 (June 29, 2024)")
    print()
    print("用法: mm [-a] 列出当前目录信息")
    print("参数: -a: 在执行命令前提示用户确认(仅在安全模式关闭时有用)")
    print("支持的Shell: PowerShell, CMD, Bash")
    print()
    print("当前配置(.env):")
    print("* API          : " + str(os.getenv("OPENAI_API_BASE", "N/A")))
    print("* 模型        : " + str(os.getenv("MODEL_NAME", "N/A")))
  
    model_temp = os.getenv("MODEL_TEMPERATURE", "0.7")
    try:
      print("* 温度系数  : " + str(float(model_temp)))
    except ValueError:
      print(f"* 温度系数  : {model_temp} (无法解析为浮点数)")

    max_tokens_env = os.getenv("MODEL_MAX_TOKENS", "2048")
    try:
      print("* 最大令牌数  : " + str(int(max_tokens_env)))
    except ValueError:
      print(f"* 最大令牌数  : {max_tokens_env} (无法解析为整数)")

    safety_env = os.getenv("SAFETY", "1").lower()
    safety_bool = safety_env in ("true", "1")
    print("* 安全模式       : " + str(safety_bool))
    
    modify_env = os.getenv("MODIFY", "1").lower()
    modify_bool = modify_env in ("true", "1")
    print("* 修改模式       : " + str(modify_bool))

    print("* 命令颜色: " + str(os.getenv("SUGGESTED_COMMAND_COLOR", "yellow")))

# 获取操作系统友好名称
def get_os_friendly_name():
  os_name = platform.system()
  if os_name == "Linux":
    return "Linux/"+distro.name(pretty=True)
  elif os_name == "Windows":
    return os_name
  elif os_name == "Darwin":
    return "Darwin/macOS"
  else:
    return os_name

def chat_completion(client, query, shell):
    """
    调用模型进行对话，所有模型参数均从.env文件读取。
    参数:
        client: OpenAIModel实例
        query: 用户输入的自然语言
        shell: 当前shell类型
    返回:
        模型生成的回复内容
    """
    if query == "":
        print ("未指定用户提示。")
        sys.exit(-1)
    system_prompt = get_system_prompt(shell)
    model = os.getenv("MODEL_NAME")
    
    try:
        temperature = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
    except ValueError:
        print(colored(f"警告：.env 文件中的 MODEL_TEMPERATURE ('{os.getenv('MODEL_TEMPERATURE')}') 不是有效的浮点数，将使用默认值 0.7。", "yellow"))
        temperature = 0.7

    try:
        max_tokens = int(os.getenv("MODEL_MAX_TOKENS", "2048"))
    except ValueError:
        print(colored(f"警告：.env 文件中的 MODEL_MAX_TOKENS ('{os.getenv('MODEL_MAX_TOKENS')}') 不是有效的整数，将使用默认值 2048。", "yellow"))
        max_tokens = 2048
        
    response = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=temperature,
        max_tokens=max_tokens)
    return response

# 检查响应是否存在问题
def check_for_issue(response):
  prefixes = ("sorry", "i'm sorry", "the question is not clear", "i'm", "i am")
  if response.lower().startswith(prefixes):
    print(colored("存在错误: "+response, 'red'))
    sys.exit(-1)

# 检查响应是否包含Markdown代码块
def check_for_markdown(response):
  if response.count("```",2):
    print(colored("响应包含Markdown代码块，因此不直接执行命令: \n", 'red')+response)
    sys.exit(-1)

# 检查是否缺少POSIX显示环境
def missing_posix_display():
  return 'DISPLAY' not in os.environ or not os.environ["DISPLAY"]

def prompt_user_for_action(ask_flag, response):
  color = os.getenv("SUGGESTED_COMMAND_COLOR", "yellow")
  print("命令: " + colored(response, color, attrs=['bold']))
  modify_snippet = ""
  if os.getenv("MODIFY", "0").lower() in ("true", "1"):
    modify_snippet = " [m]修改"
  copy_to_clipboard_snippet = " [c]复制到剪贴板"
  if os.name == "posix" and missing_posix_display():
    if get_os_friendly_name() != "Darwin/macOS":
      copy_to_clipboard_snippet = ""
  if os.getenv("SAFETY", "1").lower() in ("true", "1") or ask_flag == True:
    prompt_text = f"执行命令? [Y]是 [n]否{modify_snippet}{copy_to_clipboard_snippet} ==> "
    print(prompt_text, end = '')
    user_input = input()
    return user_input 
  if os.getenv("SAFETY", "0").lower() in ("false", "0"):
     return "Y"

def execute_command_with_error_handling(client, command, shell, ask_flag, original_query=None, retry_count=0, command_proxy=None):
    """
    使用CommandProxy执行命令并处理错误，保持终端交互性
    参数:
        client: OpenAIModel实例
        command: 要执行的命令
        shell: shell类型
        ask_flag: 是否强制询问标志
        original_query: 原始用户查询
        retry_count: 重试次数
        command_proxy: CommandProxy实例，如果为None则创建新实例
    """
    max_retries = 2  # 最大重试次数
    
    # 如果没有提供command_proxy，创建一个新的
    if command_proxy is None:
        command_proxy = CommandProxy()
    
    try:
        # 使用CommandProxy执行命令（保持交互性）
        result = command_proxy.execute_command_with_pty(command, shell)
        
        # 检查命令执行结果
        if result['success']:
            print(colored("\n命令执行成功！", "green"))
        else:
            print(colored(f"\n命令执行失败，返回码: {result['exit_code']}", "red"))
            
            # 如果有原始查询且重试次数未超限，且CommandProxy建议重试
            if original_query and retry_count < max_retries and command_proxy.should_retry():
                print(colored(f"\n检测到命令执行失败，尝试重新生成命令 (第{retry_count + 1}次重试)...", "yellow"))
                
                # 构建包含错误信息和重试历史的新查询
                retry_hints = [
                    "请尝试使用不同的参数或方法",
                    "考虑使用替代命令或工具", 
                    "请检查命令语法是否正确",
                    "尝试更简单或更直接的方法",
                    "考虑分步骤执行任务"
                ]
                
                # 从CommandProxy获取详细的输出信息
                last_output = command_proxy.get_last_output()
                
                error_context = f"""第{retry_count + 1}次重试：
之前尝试的命令: '{command}'
执行结果: 失败
详细输出信息:
{last_output}

原始任务: {original_query}

重要提示: {retry_hints[retry_count % len(retry_hints)]}
请生成一个完全不同的命令来完成任务，避免重复之前失败的方法。"""
                
                # 重新调用模型生成命令
                new_response = chat_completion(client, error_context, shell)
                check_for_issue(new_response)
                check_for_markdown(new_response)
                
                print(colored(f"\n重新生成的命令: {new_response}", "yellow"))
                
                # 检查是否生成了相同的命令
                if new_response.strip() == command.strip():
                    print(colored("⚠️  警告: 生成了相同的命令，这可能不会解决问题。", "yellow"))
                
                user_choice = input("执行重新生成的命令? [Y]是 [n]否 [c]复制到剪贴板 ==> ").strip()
                
                if user_choice.upper() in ["", "Y"]:
                    return execute_command_with_error_handling(client, new_response, shell, ask_flag, original_query, retry_count + 1, command_proxy)
                elif user_choice.upper() == "C":
                    pyperclip.copy(new_response)
                    print("已将重新生成的命令复制到剪贴板。")
                    return
            else:
                if retry_count >= max_retries:
                    print(colored(f"已达到最大重试次数({max_retries})，停止重试。", "red"))
                elif not command_proxy.should_retry():
                    print(colored("命令执行完成，无需重试。", "green"))
                    
    except KeyboardInterrupt:
        print(colored("\n用户中断了命令执行。", "yellow"))
    except Exception as e:
        print(colored(f"执行命令时发生错误: {e}", "red"))

def eval_user_intent_and_execute(client, user_input, command, shell, ask_flag, original_query=None, command_proxy=None):
    """
    根据用户意图执行相应操作
    参数:
        client: OpenAIModel实例
        user_input: 用户输入的选择
        command: 要执行的命令
        shell: shell类型
        ask_flag: 是否强制询问标志
        original_query: 原始用户查询（用于错误重试）
        command_proxy: CommandProxy实例
    """
    # 如果没有提供command_proxy，创建一个新的
    if command_proxy is None:
        command_proxy = CommandProxy()
        
    if user_input.upper() not in ["", "Y", "C", "M"]:
        print("未执行任何操作。")
        return
    if user_input.upper() == "Y" or user_input == "":
        execute_command_with_error_handling(client, command, shell, ask_flag, original_query, 0, command_proxy)
    if os.getenv("MODIFY", "0").lower() in ("true", "1") and user_input.upper() == "M":
      print("修改提示: ", end = '')
      modded_query = input()
      modded_response = chat_completion(client, modded_query, shell)
      check_for_issue(modded_response)
      check_for_markdown(modded_response)
      user_intent = prompt_user_for_action(ask_flag, modded_response)
      print()
      eval_user_intent_and_execute(client, user_intent, modded_response, shell, ask_flag, modded_query, command_proxy)
    if user_input.upper() == "C":
        if os.name == "posix" and missing_posix_display():
          if get_os_friendly_name() != "Darwin/macOS":
            return
        pyperclip.copy(command) 
        print("已将命令复制到剪贴板。")

def get_executable_dir():
    """获取可执行文件或脚本所在的目录。"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包的 .exe 文件 (sys._MEIPASS 是临时解压目录)
        # 我们需要的是 .exe 文件所在的真实目录
        return os.path.dirname(sys.executable)
    else:
        # 直接运行 .py 脚本
        return os.path.dirname(os.path.abspath(__file__))

# 优先从可执行文件/脚本所在目录加载 .env
executable_dir = get_executable_dir()
env_path_executable_dir = os.path.join(executable_dir, '.env')

if os.path.exists(env_path_executable_dir):
    load_dotenv(dotenv_path=env_path_executable_dir)
    # print(colored(f"[DEBUG] Loaded .env from: {env_path_executable_dir}", "magenta")) # 调试信息
    # 在这里也需要初始化 client 和 shell，如果 .env 在可执行文件目录找到
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print(colored("错误: OPENAI_API_KEY 未配置或使用的是示例值。", "red"))
        print(colored("请在程序运行目录下创建或修改 .env 文件, 并正确配置您的 OPENAI_API_KEY。", "red"))
        print(colored("您可以参考项目中的 .env.example 文件获取配置模板。", "yellow"))
        if __name__ == "__main__":
             sys.exit(1)
        else:
            raise EnvironmentError("OPENAI_API_KEY not configured correctly.")
    client = OpenAIModel()
    shell = get_current_shell()
elif __name__ == "__main__": # 只有在直接运行时，如果可执行文件目录没有.env，才尝试从CWD加载并执行后续逻辑
    # 如果可执行文件/脚本目录没有 .env，则尝试从当前工作目录加载（兼容旧行为）
    load_dotenv() # 这里也需要 load_dotenv
    # print(colored(f"[DEBUG] .env not found in executable directory, attempting load from CWD.", "magenta")) # 调试信息

    # 检查 OPENAI_API_KEY 是否已配置
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print(colored("错误: OPENAI_API_KEY 未配置或使用的是示例值。", "red"))
        print(colored("请在程序运行目录下创建或修改 .env 文件, 并正确配置您的 OPENAI_API_KEY。", "red"))
        print(colored("您可以参考项目中的 .env.example 文件获取配置模板。", "yellow"))
        sys.exit(1)

    client = OpenAIModel()
    shell = get_current_shell() # 默认为 powershell.exe
    command_start_idx = 1     # 问题参数从哪个argv索引开始
    ask_flag = False           # 安全开关-a命令行参数
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    if sys.argv[1] == "-a":
        ask_flag = True
        command_start_idx = 2
    arguments = sys.argv[command_start_idx:]
    user_prompt = " ".join(arguments)
    
    # 确保 client 和 shell 在此作用域内有效
    # 注意：client 和 shell 的初始化可能依赖于 .env 文件加载后的配置
    # 因此，如果它们在全局作用域定义并依赖配置，需要确保配置已加载
    # 这段逻辑在回退后，如果client和shell在上面分支已初始化，这里就不需要了
    # if 'client' not in globals() or 'shell' not in globals():
    #     # 重新获取配置，确保 client 和 shell 初始化
    #     api_key = os.getenv("OPENAI_API_KEY")
    #     if not api_key or api_key == "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
    #         print(colored("错误: OPENAI_API_KEY 未配置或使用的是示例值 (在 __main__ 中检查)。", "red"))
    #         sys.exit(1)
    #     client = OpenAIModel() # 重新初始化 client
    #     shell = os.environ.get("SHELL", "powershell.exe") # 重新获取 shell

    result = chat_completion(client, user_prompt, shell)
    check_for_issue(result)
    check_for_markdown(result)
    users_intent = prompt_user_for_action(ask_flag, result)
    print()
    eval_user_intent_and_execute(client, users_intent, result, shell, ask_flag)

if __name__ == "__main__":
  init() # 确保 colorama 初始化
  # 主要逻辑移到上面的 elif __name__ == "__main__" 分支中
  # 如果 env_path_executable_dir 存在，则 client 和 shell 已经在 if 分支中初始化
  # 如果不存在，则在 elif __name__ == "__main__" 分支中初始化并执行
  # 这里保留是为了确保脚本直接执行时，上面的逻辑能被触发
  # 如果脚本作为模块导入，则 __main__ 块不会执行，上面的全局 client 和 shell 初始化也不会发生
  # 这是一个稍微复杂的控制流，需要仔细考虑导入和直接执行的场景
  # 简单的回退到上一个版本，可能就是将 client 和 shell 的定义放回 __main__ 块内，
  # 并在 load_dotenv() 之后。

  # --- 开始回退到更接近上一个版本的结构 ---
  # 确保 load_dotenv 已经被调用 (在文件顶部附近)

  # 检查 OPENAI_API_KEY 是否已配置 (这部分逻辑可能需要调整到 main 函数或全局配置加载后)
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key or api_key == "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
      print(colored("错误: OPENAI_API_KEY 未配置或使用的是示例值。", "red"))
      print(colored("请在程序运行目录下创建或修改 .env 文件, 并正确配置您的 OPENAI_API_KEY。", "red"))
      print(colored("您可以参考项目中的 .env.example 文件获取配置模板。", "yellow"))
      sys.exit(1)

  client = OpenAIModel()
  shell = get_current_shell()
  # --- 结束回退 --- 

  command_start_idx = 1     # 问题参数从哪个argv索引开始
  ask_flag = False           # 安全开关-a命令行参数
  if len(sys.argv) < 2:
      print_usage()
      sys.exit(-1)
  if sys.argv[1] == "-a":
      ask_flag = True
      command_start_idx = 2
  arguments = sys.argv[command_start_idx:]
  user_prompt = " ".join(arguments)
  
  # 创建CommandProxy实例
  command_proxy = CommandProxy()
  
  result = chat_completion(client, user_prompt, shell)
  check_for_issue(result)
  check_for_markdown(result)
  users_intent = prompt_user_for_action(ask_flag, result)
  print()
  eval_user_intent_and_execute(client, users_intent, result, shell, ask_flag, user_prompt, command_proxy)
  