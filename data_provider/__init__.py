# -*- coding: utf-8 -*-
"""
===================================
数据源策略层 - 包初始化
===================================

本包实现策略模式管理多个数据源，实现：
1. 统一的数据获取接口
2. 自动故障切换
3. 防封禁流控策略
"""

from .base import BaseFetcher, DataFetcherManager
# from .akshare_fetcher import AkshareFetcher  # 已禁用：SSL/proxy 错误
from .tushare_fetcher import TushareFetcher, StockBasicInfo
from .baostock_fetcher import BaostockFetcher
from .yfinance_fetcher import YfinanceFetcher

__all__ = [
    'BaseFetcher',
    'DataFetcherManager',
    # 'AkshareFetcher',  # 已禁用：SSL/proxy 错误
    'TushareFetcher',
    'StockBasicInfo',  # Tushare 股票基础信息
    'BaostockFetcher',
    'YfinanceFetcher',
]
