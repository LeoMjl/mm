#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令缓存配置模块
提供缓存相关的配置选项和环境变量支持
"""

import os
from typing import Dict, Any

class CacheConfig:
    """
    缓存配置类
    从环境变量和默认值中读取缓存配置
    """
    
    def __init__(self):
        """
        初始化缓存配置
        """
        self._load_config()
    
    def _load_config(self) -> None:
        """
        从环境变量加载配置
        """
        # 缓存启用/禁用
        self.enabled = self._get_bool_env("MM_CACHE_ENABLED", True)
        
        # 缓存目录
        default_cache_dir = os.path.join(os.path.expanduser("~"), ".mm_cache")
        self.cache_dir = os.getenv("MM_CACHE_DIR", default_cache_dir)
        
        # 精确匹配缓存设置
        self.max_exact_entries = self._get_int_env("MM_CACHE_MAX_EXACT", 1000)
        
        # 语义相似度缓存设置
        self.max_semantic_entries = self._get_int_env("MM_CACHE_MAX_SEMANTIC", 500)
        self.similarity_threshold = self._get_float_env("MM_CACHE_SIMILARITY_THRESHOLD", 0.85)
        
        # 缓存过期设置（天数）
        self.exact_cache_ttl_days = self._get_int_env("MM_CACHE_EXACT_TTL_DAYS", 30)
        self.semantic_cache_ttl_days = self._get_int_env("MM_CACHE_SEMANTIC_TTL_DAYS", 7)
        
        # 自动保存设置
        self.auto_save_interval = self._get_int_env("MM_CACHE_AUTO_SAVE_INTERVAL", 10)  # 每10次操作保存一次
        
        # 调试模式
        self.debug_mode = self._get_bool_env("MM_CACHE_DEBUG", False)
        
        # 缓存命中提示
        self.show_cache_hits = self._get_bool_env("MM_CACHE_SHOW_HITS", True)
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """
        获取布尔类型环境变量
        
        参数:
            key: 环境变量键
            default: 默认值
            
        返回:
            布尔值
        """
        value = os.getenv(key, "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        else:
            return default
    
    def _get_int_env(self, key: str, default: int) -> int:
        """
        获取整数类型环境变量
        
        参数:
            key: 环境变量键
            default: 默认值
            
        返回:
            整数值
        """
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def _get_float_env(self, key: str, default: float) -> float:
        """
        获取浮点数类型环境变量
        
        参数:
            key: 环境变量键
            default: 默认值
            
        返回:
            浮点数值
        """
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将配置转换为字典
        
        返回:
            配置字典
        """
        return {
            "enabled": self.enabled,
            "cache_dir": self.cache_dir,
            "max_exact_entries": self.max_exact_entries,
            "max_semantic_entries": self.max_semantic_entries,
            "similarity_threshold": self.similarity_threshold,
            "exact_cache_ttl_days": self.exact_cache_ttl_days,
            "semantic_cache_ttl_days": self.semantic_cache_ttl_days,
            "auto_save_interval": self.auto_save_interval,
            "debug_mode": self.debug_mode,
            "show_cache_hits": self.show_cache_hits
        }
    
    def print_config(self) -> None:
        """
        打印当前配置
        """
        from termcolor import colored
        
        print(colored("=== MM 命令缓存配置 ===", "cyan", attrs=['bold']))
        print(f"缓存启用: {colored(str(self.enabled), 'green' if self.enabled else 'red')}")
        print(f"缓存目录: {self.cache_dir}")
        print(f"精确匹配缓存最大条目数: {self.max_exact_entries}")
        print(f"语义相似度缓存最大条目数: {self.max_semantic_entries}")
        print(f"语义相似度阈值: {self.similarity_threshold}")
        print(f"精确匹配缓存TTL: {self.exact_cache_ttl_days} 天")
        print(f"语义相似度缓存TTL: {self.semantic_cache_ttl_days} 天")
        print(f"自动保存间隔: 每 {self.auto_save_interval} 次操作")
        print(f"调试模式: {colored(str(self.debug_mode), 'yellow' if self.debug_mode else 'green')}")
        print(f"显示缓存命中: {colored(str(self.show_cache_hits), 'green' if self.show_cache_hits else 'red')}")
        print()
        print(colored("环境变量配置说明:", "yellow", attrs=['bold']))
        print("MM_CACHE_ENABLED=true/false          - 启用/禁用缓存")
        print("MM_CACHE_DIR=/path/to/cache          - 缓存目录路径")
        print("MM_CACHE_MAX_EXACT=1000              - 精确匹配缓存最大条目数")
        print("MM_CACHE_MAX_SEMANTIC=500            - 语义相似度缓存最大条目数")
        print("MM_CACHE_SIMILARITY_THRESHOLD=0.85   - 语义相似度阈值")
        print("MM_CACHE_EXACT_TTL_DAYS=30           - 精确匹配缓存过期天数")
        print("MM_CACHE_SEMANTIC_TTL_DAYS=7         - 语义相似度缓存过期天数")
        print("MM_CACHE_AUTO_SAVE_INTERVAL=10       - 自动保存间隔")
        print("MM_CACHE_DEBUG=true/false            - 调试模式")
        print("MM_CACHE_SHOW_HITS=true/false        - 显示缓存命中提示")

# 全局配置实例
_global_config = None

def get_cache_config() -> CacheConfig:
    """
    获取全局缓存配置实例
    
    返回:
        CacheConfig实例
    """
    global _global_config
    if _global_config is None:
        _global_config = CacheConfig()
    return _global_config

def reload_cache_config() -> CacheConfig:
    """
    重新加载缓存配置
    
    返回:
        新的CacheConfig实例
    """
    global _global_config
    _global_config = CacheConfig()
    return _global_config