#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令缓存模块
实现双层缓存策略：精确匹配缓存和语义相似度缓存
"""

import os
import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
from cache_config import get_cache_config

@dataclass
class CacheEntry:
    """
    缓存条目数据结构
    """
    query: str              # 原始查询
    command: str            # 生成的命令
    shell: str              # shell类型
    timestamp: float        # 创建时间戳
    hit_count: int = 1      # 命中次数
    last_used: float = None # 最后使用时间
    success_rate: float = 1.0  # 成功率（预留）
    
    def __post_init__(self):
        if self.last_used is None:
            self.last_used = self.timestamp

class CommandCache:
    """
    命令缓存管理器
    实现精确匹配缓存和语义相似度缓存
    """
    
    def __init__(self, cache_dir: str = None, max_exact_entries: int = None, 
                 max_semantic_entries: int = None, similarity_threshold: float = None):
        """
        初始化缓存管理器
        
        参数:
            cache_dir: 缓存目录路径（可选，默认从配置读取）
            max_exact_entries: 精确匹配缓存最大条目数（可选，默认从配置读取）
            max_semantic_entries: 语义相似度缓存最大条目数（可选，默认从配置读取）
            similarity_threshold: 语义相似度阈值（可选，默认从配置读取）
        """
        # 获取配置
        self.config = get_cache_config()
        
        # 使用传入参数或配置默认值
        self.cache_dir = cache_dir or self.config.cache_dir
        self.max_exact_entries = max_exact_entries or self.config.max_exact_entries
        self.max_semantic_entries = max_semantic_entries or self.config.max_semantic_entries
        self.similarity_threshold = similarity_threshold or self.config.similarity_threshold
        
        # 缓存存储
        self.exact_cache: Dict[str, CacheEntry] = {}  # 精确匹配缓存
        self.semantic_cache: List[CacheEntry] = []    # 语义相似度缓存
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 操作计数器（用于自动保存）
        self._operation_count = 0
        
        # 缓存文件路径
        self.exact_cache_file = os.path.join(self.cache_dir, "exact_cache.json")
        self.semantic_cache_file = os.path.join(self.cache_dir, "semantic_cache.json")
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 加载现有缓存
        self._load_cache()
    
    def _generate_cache_key(self, query: str, shell: str) -> str:
        """
        生成缓存键
        
        参数:
            query: 用户查询
            shell: shell类型
            
        返回:
            缓存键字符串
        """
        # 标准化查询：去除多余空格，转换为小写
        normalized_query = " ".join(query.strip().lower().split())
        cache_input = f"{normalized_query}|{shell}"
        return hashlib.md5(cache_input.encode('utf-8')).hexdigest()
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """
        计算两个查询的相似度
        使用简单的词汇重叠度算法
        
        参数:
            query1: 查询1
            query2: 查询2
            
        返回:
            相似度分数 (0-1)
        """
        # 标准化查询
        words1 = set(query1.strip().lower().split())
        words2 = set(query2.strip().lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def get_command(self, query: str, shell: str) -> Optional[str]:
        """
        从缓存中获取命令
        
        参数:
            query: 用户查询
            shell: shell类型
            
        返回:
            缓存的命令或None
        """
        # 检查缓存是否启用
        if not self.config.enabled:
            return None
            
        with self._lock:
            # 第一层：精确匹配缓存
            cache_key = self._generate_cache_key(query, shell)
            if cache_key in self.exact_cache:
                entry = self.exact_cache[cache_key]
                entry.hit_count += 1
                entry.last_used = time.time()
                
                if self.config.show_cache_hits:
                    from termcolor import colored
                    print(colored(f"[缓存命中] 精确匹配: {query[:50]}...", "green"))
                
                if self.config.debug_mode:
                    print(f"[DEBUG] 精确匹配缓存命中，命中次数: {entry.hit_count}")
                
                return entry.command
            
            # 第二层：语义相似度缓存
            best_match = None
            best_similarity = 0.0
            
            for entry in self.semantic_cache:
                if entry.shell != shell:
                    continue
                    
                similarity = self._calculate_similarity(query, entry.query)
                if similarity >= self.similarity_threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = entry
            
            if best_match:
                best_match.hit_count += 1
                best_match.last_used = time.time()
                
                if self.config.show_cache_hits:
                    from termcolor import colored
                    print(colored(f"[缓存命中] 语义相似度: {best_similarity:.2f} - {query[:50]}...", "blue"))
                
                if self.config.debug_mode:
                    print(f"[DEBUG] 语义相似度缓存命中，相似度: {best_similarity:.3f}, 命中次数: {best_match.hit_count}")
                
                return best_match.command
            
            if self.config.debug_mode:
                print(f"[DEBUG] 缓存未命中: {query[:50]}...")
            
            return None
    
    def store_command(self, query: str, command: str, shell: str) -> None:
        """
        存储命令到缓存
        
        参数:
            query: 用户查询
            command: 生成的命令
            shell: shell类型
        """
        # 检查缓存是否启用
        if not self.config.enabled:
            return
            
        with self._lock:
            current_time = time.time()
            
            # 创建缓存条目
            entry = CacheEntry(
                query=query,
                command=command,
                shell=shell,
                timestamp=current_time,
                last_used=current_time
            )
            
            # 存储到精确匹配缓存
            cache_key = self._generate_cache_key(query, shell)
            self.exact_cache[cache_key] = entry
            
            # 存储到语义相似度缓存（避免重复）
            if not any(self._calculate_similarity(query, e.query) > 0.95 and e.shell == shell 
                      for e in self.semantic_cache):
                self.semantic_cache.append(entry)
            
            # 清理过期缓存
            self._cleanup_cache()
            
            # 增加操作计数
            self._operation_count += 1
            
            if self.config.debug_mode:
                print(f"[DEBUG] 缓存存储: {query[:50]}..., 操作计数: {self._operation_count}")
            
            # 自动保存检查
            if self._operation_count % self.config.auto_save_interval == 0:
                if self.config.debug_mode:
                    print(f"[DEBUG] 触发自动保存，操作计数: {self._operation_count}")
                self.save_cache()
    
    def _cleanup_cache(self) -> None:
        """
        清理过期和超量的缓存条目
        """
        current_time = time.time()
        
        # 清理精确匹配缓存（LRU策略）
        if len(self.exact_cache) > self.max_exact_entries:
            # 按最后使用时间排序，移除最旧的条目
            sorted_entries = sorted(self.exact_cache.items(), 
                                  key=lambda x: x[1].last_used)
            
            entries_to_remove = len(self.exact_cache) - self.max_exact_entries
            for i in range(entries_to_remove):
                del self.exact_cache[sorted_entries[i][0]]
        
        # 清理语义相似度缓存（LRU + 命中频率策略）
        if len(self.semantic_cache) > self.max_semantic_entries:
            # 按综合分数排序（命中次数 * 最近使用权重）
            def calculate_score(entry):
                time_weight = max(0.1, 1.0 - (current_time - entry.last_used) / (7 * 24 * 3600))  # 7天衰减
                return entry.hit_count * time_weight
            
            self.semantic_cache.sort(key=calculate_score, reverse=True)
            self.semantic_cache = self.semantic_cache[:self.max_semantic_entries]
    
    def _load_cache(self) -> None:
        """
        从文件加载缓存数据
        """
        try:
            # 加载精确匹配缓存
            if os.path.exists(self.exact_cache_file):
                with open(self.exact_cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, entry_dict in data.items():
                        self.exact_cache[key] = CacheEntry(**entry_dict)
            
            # 加载语义相似度缓存
            if os.path.exists(self.semantic_cache_file):
                with open(self.semantic_cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.semantic_cache = [CacheEntry(**entry_dict) for entry_dict in data]
                    
        except Exception as e:
            print(f"[警告] 加载缓存失败: {e}")
            # 重置缓存
            self.exact_cache = {}
            self.semantic_cache = []
    
    def save_cache(self) -> None:
        """
        保存缓存数据到文件
        """
        with self._lock:
            try:
                # 保存精确匹配缓存
                exact_data = {key: asdict(entry) for key, entry in self.exact_cache.items()}
                with open(self.exact_cache_file, 'w', encoding='utf-8') as f:
                    json.dump(exact_data, f, ensure_ascii=False, indent=2)
                
                # 保存语义相似度缓存
                semantic_data = [asdict(entry) for entry in self.semantic_cache]
                with open(self.semantic_cache_file, 'w', encoding='utf-8') as f:
                    json.dump(semantic_data, f, ensure_ascii=False, indent=2)
                    
            except Exception as e:
                print(f"[警告] 保存缓存失败: {e}")
    
    def get_cache_stats(self) -> Dict:
        """
        获取缓存统计信息
        
        返回:
            缓存统计字典
        """
        with self._lock:
            total_hits = sum(entry.hit_count for entry in self.exact_cache.values())
            total_hits += sum(entry.hit_count for entry in self.semantic_cache)
            
            return {
                "exact_cache_size": len(self.exact_cache),
                "semantic_cache_size": len(self.semantic_cache),
                "total_hits": total_hits,
                "cache_dir": self.cache_dir
            }
    
    def clear_cache(self) -> None:
        """
        清空所有缓存
        """
        with self._lock:
            self.exact_cache.clear()
            self.semantic_cache.clear()
            
            # 删除缓存文件
            for cache_file in [self.exact_cache_file, self.semantic_cache_file]:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            
            print("[缓存] 已清空所有缓存")

# 全局缓存实例
_global_cache = None

def get_cache() -> CommandCache:
    """
    获取全局缓存实例
    
    返回:
        CommandCache实例
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = CommandCache()
    return _global_cache

def cleanup_cache_on_exit():
    """
    程序退出时保存缓存
    """
    global _global_cache
    if _global_cache:
        _global_cache.save_cache()

# 注册退出时保存缓存
import atexit
atexit.register(cleanup_cache_on_exit)