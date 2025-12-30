"""
Configuration module for Doc Generator
"""
from .settings import Config, get_config, load_config
from .agents import (
    AgentConfig, AgentName, AgentConfigManager,
    get_agent_config, load_agent_configs
)

# 全域便捷訪問
config = get_config()

__all__ = [
    # App config
    "Config", "get_config", "load_config", "config",
    # Agent config
    "AgentConfig", "AgentName", "AgentConfigManager",
    "get_agent_config", "load_agent_configs"
]
