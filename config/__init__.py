"""
Configuration module for Doc Generator
"""
from .settings import Config, get_config, load_config

# 全域便捷訪問
config = get_config()

__all__ = ["Config", "get_config", "load_config", "config"]
