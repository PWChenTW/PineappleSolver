"""
OFC Solver 結構化日誌系統配置

該模組提供：
1. JSON 格式的結構化日誌
2. 日誌輪轉機制
3. 敏感信息過濾
4. 性能日誌記錄
5. 組件級別的日誌器
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import re
import traceback
import uuid
from functools import wraps
import time


class SensitiveDataFilter(logging.Filter):
    """敏感信息過濾器，用於遮蔽日誌中的敏感數據"""
    
    # 定義需要遮蔽的模式
    PATTERNS = [
        # 撲克牌手牌信息（例如：['As', 'Kd', 'Qh']）
        (r'\[[\'"]?[2-9TJQKA][schd][\'"]?(?:,\s*[\'"]?[2-9TJQKA][schd][\'"]?)*\]', '[CARDS_MASKED]'),
        # 單張牌信息
        (r'\b[2-9TJQKA][schd]\b', 'XX'),
        # API 金鑰模式
        (r'\b[A-Za-z0-9]{32,}\b', '[API_KEY_MASKED]'),
        # IP 地址
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP_MASKED]'),
    ]
    
    def __init__(self, mask_cards: bool = True, mask_api_keys: bool = True):
        super().__init__()
        self.mask_cards = mask_cards
        self.mask_api_keys = mask_api_keys
    
    def filter(self, record: logging.LogRecord) -> bool:
        """過濾並遮蔽日誌記錄中的敏感信息"""
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            
            for pattern, replacement in self.PATTERNS:
                if (pattern.startswith(r'\[') and self.mask_cards) or \
                   (pattern.startswith(r'\b[A-Za-z0-9]') and self.mask_api_keys):
                    msg = re.sub(pattern, replacement, msg)
            
            record.msg = msg
        
        # 同樣處理 args 中的敏感信息
        if hasattr(record, 'args') and record.args:
            filtered_args = []
            for arg in record.args:
                arg_str = str(arg)
                for pattern, replacement in self.PATTERNS:
                    if (pattern.startswith(r'\[') and self.mask_cards) or \
                       (pattern.startswith(r'\b[A-Za-z0-9]') and self.mask_api_keys):
                        arg_str = re.sub(pattern, arg_str, replacement)
                filtered_args.append(arg_str)
            record.args = tuple(filtered_args)
        
        return True


class StructuredFormatter(logging.Formatter):
    """結構化 JSON 格式化器"""
    
    def __init__(self, component: str = "unknown"):
        super().__init__()
        self.component = component
        self.hostname = os.environ.get('HOSTNAME', 'localhost')
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日誌記錄為 JSON"""
        # 基本日誌結構
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "component": getattr(record, 'component', self.component),
            "message": record.getMessage(),
            "logger": record.name,
            "hostname": self.hostname,
        }
        
        # 添加上下文信息
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        # 添加請求 ID（如果存在）
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        # 添加異常信息
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # 添加額外字段
        extra_fields = {
            'filename': record.filename,
            'line_number': record.lineno,
            'function': record.funcName,
            'process_id': record.process,
            'thread_id': record.thread,
        }
        
        # 只添加非空的額外字段
        log_data['details'] = {k: v for k, v in extra_fields.items() if v}
        
        return json.dumps(log_data, ensure_ascii=False)


class PerformanceLogger:
    """性能日誌記錄器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_timing(self, operation: str):
        """裝飾器：記錄函數執行時間"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                request_id = str(uuid.uuid4())
                
                # 記錄開始
                self.logger.info(
                    f"Operation {operation} started",
                    extra={
                        'component': 'performance',
                        'request_id': request_id,
                        'context': {
                            'operation': operation,
                            'start_time': start_time
                        }
                    }
                )
                
                try:
                    result = func(*args, **kwargs)
                    elapsed_time = time.time() - start_time
                    
                    # 記錄成功完成
                    self.logger.info(
                        f"Operation {operation} completed",
                        extra={
                            'component': 'performance',
                            'request_id': request_id,
                            'context': {
                                'operation': operation,
                                'elapsed_time': elapsed_time,
                                'status': 'success'
                            }
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    elapsed_time = time.time() - start_time
                    
                    # 記錄失敗
                    self.logger.error(
                        f"Operation {operation} failed",
                        extra={
                            'component': 'performance',
                            'request_id': request_id,
                            'context': {
                                'operation': operation,
                                'elapsed_time': elapsed_time,
                                'status': 'failed',
                                'error': str(e)
                            }
                        },
                        exc_info=True
                    )
                    raise
            
            return wrapper
        return decorator


def setup_logger(
    name: str,
    component: str,
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    mask_sensitive_data: bool = True
) -> logging.Logger:
    """
    設置結構化日誌器
    
    Args:
        name: 日誌器名稱
        component: 組件名稱（如 mcts_engine, solver, evaluator）
        log_level: 日誌級別
        log_dir: 日誌目錄
        max_bytes: 單個日誌文件最大大小
        backup_count: 保留的備份文件數量
        mask_sensitive_data: 是否遮蔽敏感數據
    
    Returns:
        配置好的日誌器
    """
    # 創建日誌目錄
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 創建日誌器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 避免重複添加處理器
    if logger.handlers:
        return logger
    
    # 創建文件處理器（輪轉）
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / f"{component}.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # 創建控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    
    # 設置格式化器
    formatter = StructuredFormatter(component)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加敏感信息過濾器
    if mask_sensitive_data:
        sensitive_filter = SensitiveDataFilter()
        file_handler.addFilter(sensitive_filter)
        console_handler.addFilter(sensitive_filter)
    
    # 添加處理器到日誌器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


class LoggerManager:
    """日誌管理器，提供集中的日誌器配置和管理"""
    
    _instance = None
    _loggers: Dict[str, logging.Logger] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.log_dir = os.environ.get('OFC_LOG_DIR', 'logs')
        self.log_level = os.environ.get('OFC_LOG_LEVEL', 'INFO')
        self.mask_sensitive = os.environ.get('OFC_MASK_SENSITIVE', 'true').lower() == 'true'
    
    def get_logger(self, component: str) -> logging.Logger:
        """獲取或創建組件日誌器"""
        if component not in self._loggers:
            self._loggers[component] = setup_logger(
                name=f"ofc.{component}",
                component=component,
                log_level=self.log_level,
                log_dir=self.log_dir,
                mask_sensitive_data=self.mask_sensitive
            )
        return self._loggers[component]
    
    def get_performance_logger(self, component: str) -> PerformanceLogger:
        """獲取性能日誌器"""
        logger = self.get_logger(component)
        return PerformanceLogger(logger)


# 預定義的組件日誌器
def get_mcts_logger() -> logging.Logger:
    """獲取 MCTS 引擎日誌器"""
    return LoggerManager().get_logger("mcts_engine")


def get_solver_logger() -> logging.Logger:
    """獲取求解器日誌器"""
    return LoggerManager().get_logger("solver")


def get_evaluator_logger() -> logging.Logger:
    """獲取評估器日誌器"""
    return LoggerManager().get_logger("evaluator")


def get_api_logger() -> logging.Logger:
    """獲取 API 日誌器"""
    return LoggerManager().get_logger("api")


def get_performance_logger(component: str) -> PerformanceLogger:
    """獲取性能日誌器"""
    return LoggerManager().get_performance_logger(component)


# 日誌上下文管理器
class LogContext:
    """日誌上下文管理器，用於添加請求級別的上下文信息"""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.request_id = context.get('request_id', str(uuid.uuid4()))
    
    def __enter__(self):
        # 可以在這裡設置線程本地存儲
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 清理上下文
        pass
    
    def log(self, level: str, message: str, **extra_context):
        """記錄帶上下文的日誌"""
        context = {**self.context, **extra_context}
        extra = {
            'request_id': self.request_id,
            'context': context
        }
        
        log_method = getattr(self.logger, level.lower())
        log_method(message, extra=extra)