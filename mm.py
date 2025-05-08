import os
import platform
from opensdkmodel import OpenAIModel
import sys
import subprocess
# import dotenv # 这行可以移除，因为下面直接 from dotenv import ...
from dotenv import load_dotenv # 确保这行在最顶部且没有被注释或条件化
import distro
import pyperclip
from termcolor import colored
from colorama import init

# 获取系统提示词
def get_system_prompt(shell):
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
  print("mm v0.5 - by @wunderwuzzi23 (June 29, 2024)")
  print()
  print("用法: mm [-a] 列出当前目录信息")
  print("参数: -a: 在执行命令前提示用户确认(仅在安全模式关闭时有用)")
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

def eval_user_intent_and_execute(client, user_input, command, shell, ask_flag):
  if user_input.upper() not in ["", "Y", "C", "M"]:
    print("未执行任何操作。")
    return
  if user_input.upper() == "Y" or user_input == "":
    if shell == "powershell.exe":
      subprocess.run([shell, "/c", command], shell=False)  
    else: 
      subprocess.run([shell, "-c", command], shell=False)
  if os.getenv("MODIFY", "0").lower() in ("true", "1") and user_input.upper() == "M":
    print("修改提示: ", end = '')
    modded_query = input()
    modded_response = chat_completion(client, modded_query, shell)
    check_for_issue(modded_response)
    check_for_markdown(modded_response)
    user_intent = prompt_user_for_action(ask_flag, modded_response)
    print()
    eval_user_intent_and_execute(client, user_intent, modded_response, shell, ask_flag)
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
    shell = os.environ.get("SHELL", "powershell.exe")
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
    shell = os.environ.get("SHELL", "powershell.exe") # 默认为 powershell.exe
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
  shell = os.environ.get("SHELL", "powershell.exe")
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
  
  result = chat_completion(client, user_prompt, shell)
  check_for_issue(result)
  check_for_markdown(result)
  users_intent = prompt_user_for_action(ask_flag, result)
  print()
  eval_user_intent_and_execute(client, users_intent, result, shell, ask_flag)
  