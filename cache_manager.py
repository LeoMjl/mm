#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令缓存管理工具
提供缓存查看、清理、统计等功能
"""

import sys
import os
from command_cache import get_cache
from termcolor import colored
from colorama import init

def print_cache_stats():
    """
    打印缓存统计信息
    """
    cache = get_cache()
    stats = cache.get_cache_stats()
    
    print(colored("=== 命令缓存统计 ===", "cyan", attrs=['bold']))
    print(f"精确匹配缓存条目数: {stats['exact_cache_size']}")
    print(f"语义相似度缓存条目数: {stats['semantic_cache_size']}")
    print(f"总命中次数: {stats['total_hits']}")
    print(f"缓存目录: {stats['cache_dir']}")
    print()

def list_cache_entries(cache_type="all", limit=10):
    """
    列出缓存条目
    
    参数:
        cache_type: 缓存类型 ("exact", "semantic", "all")
        limit: 显示条目数限制
    """
    cache = get_cache()
    
    if cache_type in ["exact", "all"]:
        print(colored("=== 精确匹配缓存 ===", "yellow", attrs=['bold']))
        exact_entries = list(cache.exact_cache.values())[:limit]
        
        if not exact_entries:
            print("暂无精确匹配缓存条目")
        else:
            for i, entry in enumerate(exact_entries, 1):
                print(f"{i}. 查询: {entry.query[:60]}...")
                print(f"   命令: {colored(entry.command[:80], 'green')}...")
                print(f"   Shell: {entry.shell} | 命中次数: {entry.hit_count}")
                print(f"   创建时间: {_format_timestamp(entry.timestamp)}")
                print()
    
    if cache_type in ["semantic", "all"]:
        print(colored("=== 语义相似度缓存 ===", "blue", attrs=['bold']))
        semantic_entries = cache.semantic_cache[:limit]
        
        if not semantic_entries:
            print("暂无语义相似度缓存条目")
        else:
            for i, entry in enumerate(semantic_entries, 1):
                print(f"{i}. 查询: {entry.query[:60]}...")
                print(f"   命令: {colored(entry.command[:80], 'green')}...")
                print(f"   Shell: {entry.shell} | 命中次数: {entry.hit_count}")
                print(f"   创建时间: {_format_timestamp(entry.timestamp)}")
                print()

def _format_timestamp(timestamp):
    """
    格式化时间戳
    
    参数:
        timestamp: 时间戳
        
    返回:
        格式化的时间字符串
    """
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

def clear_cache(cache_type="all"):
    """
    清理缓存
    
    参数:
        cache_type: 要清理的缓存类型 ("exact", "semantic", "all")
    """
    cache = get_cache()
    
    if cache_type == "all":
        cache.clear_cache()
        print(colored("已清空所有缓存", "green"))
    elif cache_type == "exact":
        cache.exact_cache.clear()
        print(colored("已清空精确匹配缓存", "green"))
    elif cache_type == "semantic":
        cache.semantic_cache.clear()
        print(colored("已清空语义相似度缓存", "green"))
    else:
        print(colored(f"未知的缓存类型: {cache_type}", "red"))
        return
    
    # 保存更改
    cache.save_cache()

def search_cache(keyword):
    """
    在缓存中搜索包含关键词的条目
    
    参数:
        keyword: 搜索关键词
    """
    cache = get_cache()
    keyword_lower = keyword.lower()
    
    print(colored(f"=== 搜索结果: '{keyword}' ===", "magenta", attrs=['bold']))
    
    found_count = 0
    
    # 搜索精确匹配缓存
    for entry in cache.exact_cache.values():
        if (keyword_lower in entry.query.lower() or 
            keyword_lower in entry.command.lower()):
            found_count += 1
            print(f"{found_count}. [精确匹配] 查询: {entry.query[:60]}...")
            print(f"   命令: {colored(entry.command[:80], 'green')}...")
            print(f"   命中次数: {entry.hit_count}")
            print()
    
    # 搜索语义相似度缓存
    for entry in cache.semantic_cache:
        if (keyword_lower in entry.query.lower() or 
            keyword_lower in entry.command.lower()):
            found_count += 1
            print(f"{found_count}. [语义相似度] 查询: {entry.query[:60]}...")
            print(f"   命令: {colored(entry.command[:80], 'green')}...")
            print(f"   命中次数: {entry.hit_count}")
            print()
    
    if found_count == 0:
        print("未找到匹配的缓存条目")
    else:
        print(colored(f"共找到 {found_count} 个匹配条目", "cyan"))

def print_usage():
    """
    打印使用说明
    """
    print(colored("MM 命令缓存管理工具", "cyan", attrs=['bold']))
    print()
    print("用法: python cache_manager.py [命令] [参数]")
    print()
    print("可用命令:")
    print("  stats                    - 显示缓存统计信息")
    print("  list [type] [limit]      - 列出缓存条目")
    print("    type: exact|semantic|all (默认: all)")
    print("    limit: 显示条目数 (默认: 10)")
    print("  clear [type]             - 清理缓存")
    print("    type: exact|semantic|all (默认: all)")
    print("  search <keyword>         - 搜索缓存条目")
    print("  help                     - 显示此帮助信息")
    print()
    print("示例:")
    print("  python cache_manager.py stats")
    print("  python cache_manager.py list exact 5")
    print("  python cache_manager.py clear semantic")
    print("  python cache_manager.py search 'list files'")

def main():
    """
    主函数
    """
    init()  # 初始化colorama
    
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "stats":
            print_cache_stats()
        
        elif command == "list":
            cache_type = sys.argv[2] if len(sys.argv) > 2 else "all"
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            
            if cache_type not in ["exact", "semantic", "all"]:
                print(colored(f"错误: 无效的缓存类型 '{cache_type}'", "red"))
                return
            
            list_cache_entries(cache_type, limit)
        
        elif command == "clear":
            cache_type = sys.argv[2] if len(sys.argv) > 2 else "all"
            
            if cache_type not in ["exact", "semantic", "all"]:
                print(colored(f"错误: 无效的缓存类型 '{cache_type}'", "red"))
                return
            
            # 确认清理操作
            confirm = input(f"确定要清理 {cache_type} 缓存吗? [y/N]: ").strip().lower()
            if confirm in ['y', 'yes']:
                clear_cache(cache_type)
            else:
                print("操作已取消")
        
        elif command == "search":
            if len(sys.argv) < 3:
                print(colored("错误: 请提供搜索关键词", "red"))
                return
            
            keyword = " ".join(sys.argv[2:])
            search_cache(keyword)
        
        elif command in ["help", "-h", "--help"]:
            print_usage()
        
        else:
            print(colored(f"错误: 未知命令 '{command}'", "red"))
            print("使用 'python cache_manager.py help' 查看帮助信息")
    
    except Exception as e:
        print(colored(f"执行命令时发生错误: {e}", "red"))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()