"""
EnvPilot - Lightweight Environment Variables Intelligent Management Engine
轻量级环境变量智能管理引擎

A zero-dependency (except cryptography) CLI tool for managing environment variables
with encryption, multi-environment support, and leak detection.
"""

__version__ = "1.0.0"
__author__ = "gitstq"
__license__ = "MIT"

from envpilot.core import EnvManager, EnvVariable
from envpilot.crypto import CryptoEngine
from envpilot.scanner import LeakScanner

__all__ = [
    "EnvManager",
    "EnvVariable", 
    "CryptoEngine",
    "LeakScanner",
    "__version__",
]
