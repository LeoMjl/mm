
from abc import ABC, abstractmethod
from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# OpenAI通用模型实现类，支持OpenAI SDK兼容的所有模型（如deepseek、豆包、openrouter等）
class OpenAIModel:
    """
    OpenAIModel 仅支持OpenAI SDK及其兼容API的模型调用。
    """
    def __init__(self):
        """
        初始化OpenAIModel，自动从环境变量加载API密钥和API_BASE等参数。
        """
        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE")
        self.model_name = os.getenv("MODEL_NAME")  # 从.env读取模型名称
        self.client = OpenAI(api_key=api_key, base_url=api_base) if api_base else OpenAI(api_key=api_key)

    def chat(self, messages, model=None, temperature=0.7, max_tokens=2048):
        """
        通用聊天方法，支持OpenAI SDK兼容的所有模型。
        参数:
            messages: 聊天消息列表
            model: 使用的模型名称（如gpt-3.5-turbo、deepseek-chat等），默认读取.env中的MODEL_NAME
            temperature: 生成文本的温度参数
            max_tokens: 生成文本的最大token数
        返回:
            模型生成的回复内容
        """
        use_model = model if model else self.model_name
        resp = self.client.chat.completions.create(
            model=use_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content

    def moderate(self, message):
        """
        使用OpenAI接口进行内容审核。
        参数:
            message: 需要审核的消息内容
        返回:
            审核结果
        """
        return self.client.moderations.create(input=message)
