import os
import sys
import subprocess
import threading
import time
from collections import deque
from typing import Optional, Tuple, Dict, Any
from termcolor import colored

# 条件导入Unix特有模块（Windows系统不支持）
try:
    import pty
    import select
    import fcntl
    import termios
    import struct
    UNIX_MODULES_AVAILABLE = True
except ImportError:
    # Windows系统下这些模块不可用
    UNIX_MODULES_AVAILABLE = False
    pty = None
    select = None
    fcntl = None
    termios = None
    struct = None

class CommandProxy:
    """
    命令代理类，使用PTY实现终端输出镜像和增量缓存策略
    保持用户与终端的交互性，同时为AI模型提供错误反馈能力
    """
    
    def __init__(self, buffer_size: int = 1000):
        """
        初始化命令代理
        
        参数:
            buffer_size: 输出缓冲区大小，用于存储最近的命令输出
        """
        self.buffer_size = buffer_size
        self.output_buffer = deque(maxlen=buffer_size)  # 循环缓冲区
        self.error_buffer = deque(maxlen=buffer_size)   # 错误输出缓冲区
        self.last_command = None
        self.last_exit_code = None
        self.is_windows = os.name == 'nt'
        self.unix_modules_available = UNIX_MODULES_AVAILABLE
        
    def _get_terminal_size(self) -> Tuple[int, int]:
        """
        获取终端窗口大小
        
        返回:
            (行数, 列数) 元组
        """
        try:
            if self.is_windows:
                # Windows系统获取终端大小
                import shutil
                size = shutil.get_terminal_size()
                return size.lines, size.columns
            else:
                # Unix系统获取终端大小
                rows, cols = os.popen('stty size', 'r').read().split()
                return int(rows), int(cols)
        except:
            return 24, 80  # 默认大小
    
    def _setup_pty_size(self, fd: int):
        """
        设置PTY的终端大小
        
        参数:
            fd: PTY文件描述符
        """
        if not self.is_windows and self.unix_modules_available:
            try:
                rows, cols = self._get_terminal_size()
                # 设置PTY窗口大小
                winsize = struct.pack('HHHH', rows, cols, 0, 0)
                fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
            except:
                pass
    
    def execute_command_with_pty(self, command: str, shell: str = None) -> Dict[str, Any]:
        """
        使用PTY执行命令，保持交互性并镜像输出
        
        参数:
            command: 要执行的命令
            shell: 使用的shell类型
            
        返回:
            包含执行结果的字典
        """
        if self.is_windows or not self.unix_modules_available:
            # Windows系统或Unix模块不可用时使用传统方式，但增加输出镜像
            return self._execute_windows(command, shell)
        else:
            # Unix系统且模块可用时使用PTY
            return self._execute_unix_pty(command, shell)
    
    def _execute_windows(self, command: str, shell: str = None) -> Dict[str, Any]:
        """
        Windows系统下的命令执行（带输出镜像）
        
        参数:
            command: 要执行的命令
            shell: shell类型
            
        返回:
            执行结果字典
        """
        self.last_command = command
        self.output_buffer.clear()
        self.error_buffer.clear()
        
        # 确定shell命令
        if shell == "powershell.exe":
            cmd_args = ["powershell.exe", "-Command", command]
        elif shell == "cmd.exe":
            cmd_args = ["cmd.exe", "/c", command]
        else:
            cmd_args = ["powershell.exe", "-Command", command]
        
        try:
            print(colored(f"正在执行: {command}", "cyan"))
            
            # 检查是否是交互式命令
            interactive_commands = ['mysql', 'psql', 'mongo', 'redis-cli', 'ssh', 'telnet', 'ftp', 'conda', 'pip']
            is_interactive = any(cmd in command.lower() for cmd in interactive_commands)
            
            if is_interactive:
                # 对于交互式命令，直接继承当前终端的stdin/stdout/stderr
                process = subprocess.Popen(
                    cmd_args,
                    stdin=None,  # 继承父进程的stdin
                    stdout=None,  # 继承父进程的stdout
                    stderr=None,  # 继承父进程的stderr
                    text=True
                )
                
                # 等待进程结束
                exit_code = process.wait()
                self.last_exit_code = exit_code
                
                return {
                    'exit_code': exit_code,
                    'stdout': '交互式命令执行完成',
                    'stderr': '',
                    'success': exit_code == 0,
                    'buffered_output': ['交互式命令执行完成'],
                    'buffered_errors': []
                }
            else:
                # 对于非交互式命令，使用原来的PIPE模式
                process = subprocess.Popen(
                    cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # 实时读取并显示输出
                stdout_lines = []
                stderr_lines = []
                
                # 使用线程同时处理stdout和stderr
                import threading
                import queue
                
                stdout_queue = queue.Queue()
                stderr_queue = queue.Queue()
                
                def read_stdout():
                    """读取标准输出的线程函数"""
                    try:
                        for line in iter(process.stdout.readline, ''):
                            if line:
                                stdout_queue.put(line.rstrip())
                        stdout_queue.put(None)  # 结束标记
                    except Exception as e:
                        stdout_queue.put(f"读取stdout错误: {e}")
                        stdout_queue.put(None)
                
                def read_stderr():
                    """读取错误输出的线程函数"""
                    try:
                        for line in iter(process.stderr.readline, ''):
                            if line:
                                stderr_queue.put(line.rstrip())
                        stderr_queue.put(None)  # 结束标记
                    except Exception as e:
                        stderr_queue.put(f"读取stderr错误: {e}")
                        stderr_queue.put(None)
                
                # 启动读取线程
                stdout_thread = threading.Thread(target=read_stdout)
                stderr_thread = threading.Thread(target=read_stderr)
                stdout_thread.daemon = True
                stderr_thread.daemon = True
                stdout_thread.start()
                stderr_thread.start()
                
                # 实时处理输出
                stdout_done = False
                stderr_done = False
                
                while not (stdout_done and stderr_done):
                    # 处理stdout
                    if not stdout_done:
                        try:
                            line = stdout_queue.get(timeout=0.1)
                            if line is None:
                                stdout_done = True
                            else:
                                print(line)  # 显示给用户
                                stdout_lines.append(line)
                                self.output_buffer.append(line)
                        except queue.Empty:
                            pass
                    
                    # 处理stderr
                    if not stderr_done:
                        try:
                            line = stderr_queue.get(timeout=0.1)
                            if line is None:
                                stderr_done = True
                            else:
                                print(colored(line, "red"))  # 显示给用户
                                stderr_lines.append(line)
                                self.error_buffer.append(line)
                        except queue.Empty:
                            pass
                
                # 等待线程结束
                stdout_thread.join(timeout=1.0)
                stderr_thread.join(timeout=1.0)
                
                # 等待进程结束
                process.wait()
                self.last_exit_code = process.returncode
                
                # 构建stderr输出字符串
                stderr_output = '\n'.join(stderr_lines) if stderr_lines else ''
            
            return {
                'exit_code': process.returncode,
                'stdout': '\n'.join(stdout_lines),
                'stderr': stderr_output,
                'success': process.returncode == 0,
                'buffered_output': list(self.output_buffer),
                'buffered_errors': list(self.error_buffer)
            }
            
        except Exception as e:
            error_msg = f"执行命令时发生错误: {str(e)}"
            print(colored(error_msg, "red"))
            self.error_buffer.append(error_msg)
            self.last_exit_code = -1
            
            return {
                'exit_code': -1,
                'stdout': '',
                'stderr': error_msg,
                'success': False,
                'buffered_output': [],
                'buffered_errors': [error_msg]
            }
    
    def _execute_unix_pty(self, command: str, shell: str = None) -> Dict[str, Any]:
        """
        Unix系统下使用PTY执行命令
        
        参数:
            command: 要执行的命令
            shell: shell类型
            
        返回:
            执行结果字典
        """
        # 如果Unix模块不可用，回退到Windows方法
        if not self.unix_modules_available:
            return self._execute_windows(command, shell)
            
        self.last_command = command
        self.output_buffer.clear()
        self.error_buffer.clear()
        
        # 确定shell
        if shell is None:
            shell = os.environ.get('SHELL', '/bin/bash')
        
        try:
            print(colored(f"正在执行: {command}", "cyan"))
            
            # 检查是否是交互式命令
            interactive_commands = ['mysql', 'psql', 'mongo', 'redis-cli', 'ssh', 'telnet', 'ftp', 'conda', 'pip']
            is_interactive = any(cmd in command.lower() for cmd in interactive_commands)
            
            if is_interactive:
                # 对于交互式命令，使用简单的subprocess调用以保持完整交互
                process = subprocess.Popen(
                    [shell, '-c', command],
                    stdin=None,  # 继承父进程的stdin
                    stdout=None,  # 继承父进程的stdout
                    stderr=None,  # 继承父进程的stderr
                    preexec_fn=os.setsid
                )
                
                # 等待进程结束
                exit_code = process.wait()
                self.last_exit_code = exit_code
                
                return {
                    'exit_code': exit_code,
                    'stdout': '交互式命令执行完成',
                    'stderr': '',
                    'success': exit_code == 0,
                    'buffered_output': ['交互式命令执行完成'],
                    'buffered_errors': []
                }
            
            # 创建PTY
            master_fd, slave_fd = pty.openpty()
            
            # 设置PTY大小
            self._setup_pty_size(slave_fd)
            
            # 启动进程
            process = subprocess.Popen(
                [shell, '-c', command],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                preexec_fn=os.setsid
            )
            
            # 关闭slave端（子进程会使用）
            os.close(slave_fd)
            
            # 设置master_fd为非阻塞
            fcntl.fcntl(master_fd, fcntl.F_SETFL, fcntl.fcntl(master_fd, fcntl.F_GETFL) | os.O_NONBLOCK)
            
            output_lines = []
            
            # 设置stdin为非阻塞（用于读取用户输入）
            stdin_fd = sys.stdin.fileno()
            old_stdin_flags = fcntl.fcntl(stdin_fd, fcntl.F_GETFL)
            fcntl.fcntl(stdin_fd, fcntl.F_SETFL, old_stdin_flags | os.O_NONBLOCK)
            
            try:
                # 双向通信循环
                while True:
                    # 检查进程是否结束
                    process_ended = process.poll() is not None
                    
                    # 使用select检查是否有数据可读（从子进程或用户输入）
                    ready_read, _, _ = select.select([master_fd, stdin_fd], [], [], 0.1)
                    
                    data_read = False
                    for fd in ready_read:
                        if fd == master_fd:
                            # 从子进程读取输出
                            try:
                                data = os.read(master_fd, 1024).decode('utf-8', errors='ignore')
                                if data:
                                    data_read = True
                                    # 显示给用户（保持交互性）
                                    sys.stdout.write(data)
                                    sys.stdout.flush()
                                    
                                    # 镜像到缓冲区
                                    lines = data.split('\n')
                                    for line in lines:
                                        if line.strip():
                                            output_lines.append(line)
                                            self.output_buffer.append(line)
                            except OSError:
                                break
                        
                        elif fd == stdin_fd:
                            # 从用户读取输入并转发给子进程
                            try:
                                user_input = os.read(stdin_fd, 1024)
                                if user_input:
                                    os.write(master_fd, user_input)
                            except OSError:
                                pass  # 忽略非阻塞读取的错误
                    
                    # 如果进程已结束且没有更多数据可读，则退出循环
                    if process_ended and not data_read:
                        # 尝试最后一次读取剩余数据
                        try:
                            final_data = os.read(master_fd, 4096).decode('utf-8', errors='ignore')
                            if final_data:
                                sys.stdout.write(final_data)
                                sys.stdout.flush()
                                lines = final_data.split('\n')
                                for line in lines:
                                    if line.strip():
                                        output_lines.append(line)
                                        self.output_buffer.append(line)
                        except OSError:
                            pass
                        break
            
            finally:
                # 恢复stdin的原始标志
                fcntl.fcntl(stdin_fd, fcntl.F_SETFL, old_stdin_flags)
            
            # 等待进程结束
            exit_code = process.wait()
            self.last_exit_code = exit_code
            
            # 关闭master_fd
            os.close(master_fd)
            
            return {
                'exit_code': exit_code,
                'stdout': '\n'.join(output_lines),
                'stderr': '',  # PTY模式下stderr会重定向到stdout
                'success': exit_code == 0,
                'buffered_output': list(self.output_buffer),
                'buffered_errors': list(self.error_buffer)
            }
            
        except Exception as e:
            error_msg = f"执行命令时发生错误: {str(e)}"
            print(colored(error_msg, "red"))
            self.error_buffer.append(error_msg)
            self.last_exit_code = -1
            
            return {
                'exit_code': -1,
                'stdout': '',
                'stderr': error_msg,
                'success': False,
                'buffered_output': [],
                'buffered_errors': [error_msg]
            }
    
    def get_last_output(self) -> str:
        """
        获取最后一次命令的输出（用于AI模型分析）
        
        返回:
            格式化的输出字符串
        """
        if not self.output_buffer and not self.error_buffer:
            return "无输出数据"
        
        output_text = "\n".join(self.output_buffer) if self.output_buffer else ""
        error_text = "\n".join(self.error_buffer) if self.error_buffer else ""
        
        result = f"命令: {self.last_command}\n"
        result += f"退出码: {self.last_exit_code}\n"
        
        if output_text:
            result += f"标准输出:\n{output_text}\n"
        
        if error_text:
            result += f"错误输出:\n{error_text}\n"
        
        return result
    
    def should_retry(self) -> bool:
        """
        判断是否应该重试（基于退出码和错误输出）
        
        返回:
            是否建议重试
        """
        if self.last_exit_code is None:
            return False
        
        # 退出码非0表示可能需要重试
        if self.last_exit_code != 0:
            return True
        
        # 检查是否有明显的错误信息
        error_keywords = ['error', 'failed', 'not found', 'permission denied', 'access denied']
        all_output = ' '.join(self.output_buffer).lower() + ' '.join(self.error_buffer).lower()
        
        return any(keyword in all_output for keyword in error_keywords)
    
    def clear_buffers(self):
        """
        清空所有缓冲区
        """
        self.output_buffer.clear()
        self.error_buffer.clear()
        self.last_command = None
        self.last_exit_code = None