# -*- coding: utf-8 -*-
"""
Config management module for A-shares watchlist system

Responsibilities:
- Singleton-style global configuration
- Load sensitive values from .env
- Type-safe access helpers
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv, dotenv_values
from dataclasses import dataclass, field


@dataclass
class Config:
    """
    System configuration (singleton)
    
    Design:
    - dataclass for concise field definitions
    - read all values from environment with sensible defaults
    - classmethod get_instance() provides singleton access
    """
    
    # Watchlist
    stock_list: List[str] = field(default_factory=list)

    # Feishu Docs
    feishu_app_id: Optional[str] = None
    feishu_app_secret: Optional[str] = None
    feishu_folder_token: Optional[str] = None

    # Data source tokens
    tushare_token: Optional[str] = None
    
    # AI provider selection (manual priority control)
    ai_provider: str = "auto"  # auto, gemini, openrouter, deepseek, dashscope, openai

    # AI analysis - Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3-flash-preview"
    gemini_model_fallback: str = "gemini-2.5-flash"

    # Gemini API request config (throttling control)
    gemini_request_delay: float = 2.0
    gemini_max_retries: int = 5
    gemini_retry_delay: float = 5.0
    gemini_request_timeout: int = 60
    openai_preferred: bool = False

    # OpenAI-compatible API (fallback or preferred)
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None  # e.g. https://api.openai.com/v1
    openai_model: str = "gpt-4o-mini"

    # OpenRouter (AI model aggregation platform)
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-3.5-sonnet"

    # DeepSeek (convenient config, internally mapped to OpenAI)
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # DashScope / 阿里通义千问
    dashscope_api_key: Optional[str] = None
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_model: str = "qwen-plus"

    # Google Search API (alternative search engine)
    google_search_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None  # Requires custom search engine ID
    
    # Search engines (support multiple keys)
    tavily_api_keys: List[str] = field(default_factory=list)
    serpapi_keys: List[str] = field(default_factory=list)
    
    # Notification channels
    wechat_webhook_url: Optional[str] = None
    feishu_webhook_url: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    email_sender: Optional[str] = None
    email_password: Optional[str] = None
    email_receivers: List[str] = field(default_factory=list)
    custom_webhook_urls: List[str] = field(default_factory=list)
    
    # Message length limits (bytes)
    feishu_max_bytes: int = 20000
    wechat_max_bytes: int = 4000
    
    # Database
    database_path: str = "./data/stock_analysis.db"
    
    # Logging
    log_dir: str = "./logs"
    log_level: str = "INFO"
    
    # System
    max_workers: int = 3
    debug: bool = False
    
    # Scheduler
    schedule_enabled: bool = False
    schedule_time: str = "18:00"
    market_review_enabled: bool = True
    
    # Rate limiting (anti-blocking)
    akshare_sleep_min: float = 2.0
    akshare_sleep_max: float = 5.0
    
    # Tushare quota per minute (free tier)
    tushare_rate_limit_per_minute: int = 80
    
    # Retry config
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0
    
    # Singleton instance
    _instance: Optional['Config'] = None
    
    @classmethod
    def get_instance(cls) -> 'Config':
        """
        Get singleton config instance
        
        Ensures:
        1) only one global instance
        2) env is loaded once
        3) modules share same config
        """
        if cls._instance is None:
            cls._instance = cls._load_from_env()
        return cls._instance
    
    @classmethod
    def _load_from_env(cls) -> 'Config':
        """
        Load config from .env and environment variables
        
        Priority:
        1) OS environment
        2) .env file
        3) code defaults
        """
        env_path = Path(__file__).parent / '.env'
        load_dotenv(dotenv_path=env_path)
        
        # Parse watchlist (comma-separated)
        stock_list_str = os.getenv('STOCK_LIST', '')
        stock_list = [
            code.strip() 
            for code in stock_list_str.split(',') 
            if code.strip()
        ]
        
        # Defaults if not configured
        if not stock_list:
            stock_list = ['600519', '000001', '300750']
        
        # Search engine API keys (comma-separated)
        tavily_keys_str = os.getenv('TAVILY_API_KEYS', '')
        tavily_api_keys = [k.strip() for k in tavily_keys_str.split(',') if k.strip()]
        
        serpapi_keys_str = os.getenv('SERPAPI_API_KEYS', '')
        serpapi_keys = [k.strip() for k in serpapi_keys_str.split(',') if k.strip()]
        
        return cls(
            stock_list=stock_list,
            feishu_app_id=os.getenv('FEISHU_APP_ID'),
            feishu_app_secret=os.getenv('FEISHU_APP_SECRET'),
            feishu_folder_token=os.getenv('FEISHU_FOLDER_TOKEN'),
            tushare_token=os.getenv('TUSHARE_TOKEN'),
            ai_provider=os.getenv('AI_PROVIDER', 'auto'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            gemini_model=os.getenv('GEMINI_MODEL', 'gemini-3-flash-preview'),
            gemini_model_fallback=os.getenv('GEMINI_MODEL_FALLBACK', 'gemini-2.5-flash'),
            gemini_request_delay=float(os.getenv('GEMINI_REQUEST_DELAY', '2.0')),
            gemini_max_retries=int(os.getenv('GEMINI_MAX_RETRIES', '5')),
            gemini_retry_delay=float(os.getenv('GEMINI_RETRY_DELAY', '5.0')),
            gemini_request_timeout=int(os.getenv('GEMINI_REQUEST_TIMEOUT', '60')),
            openai_preferred=os.getenv('OPENAI_PREFERRED', 'false').lower() == 'true',
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            openai_base_url=os.getenv('OPENAI_BASE_URL'),
            openai_model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            openrouter_api_key=os.getenv('OPENROUTER_API_KEY'),
            openrouter_base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1'),
            openrouter_model=os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet'),
            deepseek_api_key=os.getenv('DEEPSEEK_API_KEY'),
            deepseek_base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1'),
            deepseek_model=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
            dashscope_api_key=os.getenv('DASHSCOPE_API_KEY'),
            dashscope_base_url=os.getenv('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            dashscope_model=os.getenv('DASHSCOPE_MODEL', 'qwen-plus'),
            google_search_api_key=os.getenv('GOOGLE_SEARCH_API_KEY'),
            google_search_engine_id=os.getenv('GOOGLE_SEARCH_ENGINE_ID'),
            tavily_api_keys=tavily_api_keys,
            serpapi_keys=serpapi_keys,
            wechat_webhook_url=os.getenv('WECHAT_WEBHOOK_URL'),
            feishu_webhook_url=os.getenv('FEISHU_WEBHOOK_URL'),
            telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),
            email_sender=os.getenv('EMAIL_SENDER'),
            email_password=os.getenv('EMAIL_PASSWORD'),
            email_receivers=[r.strip() for r in os.getenv('EMAIL_RECEIVERS', '').split(',') if r.strip()],
            custom_webhook_urls=[u.strip() for u in os.getenv('CUSTOM_WEBHOOK_URLS', '').split(',') if u.strip()],
            feishu_max_bytes=int(os.getenv('FEISHU_MAX_BYTES', '20000')),
            wechat_max_bytes=int(os.getenv('WECHAT_MAX_BYTES', '4000')),
            database_path=os.getenv('DATABASE_PATH', './data/stock_analysis.db'),
            log_dir=os.getenv('LOG_DIR', './logs'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            max_workers=int(os.getenv('MAX_WORKERS', '3')),
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            schedule_enabled=os.getenv('SCHEDULE_ENABLED', 'false').lower() == 'true',
            schedule_time=os.getenv('SCHEDULE_TIME', '18:00'),
            market_review_enabled=os.getenv('MARKET_REVIEW_ENABLED', 'true').lower() == 'true',
        )
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (primarily for tests)"""
        cls._instance = None

    def refresh_stock_list(self) -> None:
        """
        Hot-load STOCK_LIST env var and update current watchlist.
        
        Supports two ways:
        1) .env file (local/dev/cron) - effective next run
        2) OS environment (CI/Docker) - fixed on startup
        """
        # Prefer .env value if present; otherwise fallback to OS environment
        env_path = Path(__file__).parent / '.env'
        stock_list_str = ''
        if env_path.exists():
            env_values = dotenv_values(env_path)
            stock_list_str = (env_values.get('STOCK_LIST') or '').strip()

        if not stock_list_str:
            stock_list_str = os.getenv('STOCK_LIST', '')

        stock_list = [
            code.strip()
            for code in stock_list_str.split(',')
            if code.strip()
        ]

        if not stock_list:        
            stock_list = ['000001']

        self.stock_list = stock_list
    
    def validate(self) -> List[str]:
        """
        Validate config completeness and return warnings list.
        """
        warnings = []
        
        if not self.stock_list:
            warnings.append("Warning: STOCK_LIST not configured")
        
        if not self.tushare_token:
            warnings.append("Note: Tushare Token not configured; other data sources will be used")
        
        if not self.gemini_api_key and not self.openai_api_key:
            warnings.append("Warning: Neither Gemini nor OpenAI API Key configured; AI analysis unavailable")
        elif not self.gemini_api_key:
            warnings.append("Note: Gemini API Key not configured; OpenAI-compatible API will be used")
        
        if not self.tavily_api_keys and not self.serpapi_keys:
            warnings.append("Note: Search API keys (Tavily/SerpAPI) not configured; news search unavailable")
        
        # Notification configs
        has_notification = (
            self.wechat_webhook_url or 
            self.feishu_webhook_url or
            (self.telegram_bot_token and self.telegram_chat_id) or
            (self.email_sender and self.email_password)
        )
        if not has_notification:
            warnings.append("Note: No notification channels configured; no push messages will be sent")
        
        return warnings
    
    def get_db_url(self) -> str:
        """
        Get SQLAlchemy database URL, auto-creating directory if needed.
        """
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path.absolute()}"

    def get_active_ai_config(self) -> Optional[dict]:
        """
        根据配置的 AI_PROVIDER 返回活动的 AI 配置

        Returns:
            dict: 包含 provider, api_key, base_url, model 的字典，如果没有可用配置则返回 None
        """
        provider = self.ai_provider.lower()

        # 手动指定提供商
        if provider == 'gemini' and self.gemini_api_key:
            return {
                'provider': 'gemini',
                'api_key': self.gemini_api_key,
                'model': self.gemini_model,
                'model_fallback': self.gemini_model_fallback,
            }
        elif provider == 'openrouter' and self.openrouter_api_key:
            return {
                'provider': 'openrouter',
                'api_key': self.openrouter_api_key,
                'base_url': self.openrouter_base_url,
                'model': self.openrouter_model,
            }
        elif provider == 'deepseek' and self.deepseek_api_key:
            return {
                'provider': 'deepseek',
                'api_key': self.deepseek_api_key,
                'base_url': self.deepseek_base_url,
                'model': self.deepseek_model,
            }
        elif provider == 'dashscope' and self.dashscope_api_key:
            return {
                'provider': 'dashscope',
                'api_key': self.dashscope_api_key,
                'base_url': self.dashscope_base_url,
                'model': self.dashscope_model,
            }
        elif provider == 'openai' and self.openai_api_key:
            return {
                'provider': 'openai',
                'api_key': self.openai_api_key,
                'base_url': self.openai_base_url,
                'model': self.openai_model,
            }

        # 自动模式：按优先级查找第一个可用的
        if self.gemini_api_key:
            return {
                'provider': 'gemini',
                'api_key': self.gemini_api_key,
                'model': self.gemini_model,
                'model_fallback': self.gemini_model_fallback,
            }
        if self.openrouter_api_key:
            return {
                'provider': 'openrouter',
                'api_key': self.openrouter_api_key,
                'base_url': self.openrouter_base_url,
                'model': self.openrouter_model,
            }
        if self.deepseek_api_key:
            return {
                'provider': 'deepseek',
                'api_key': self.deepseek_api_key,
                'base_url': self.deepseek_base_url,
                'model': self.deepseek_model,
            }
        if self.dashscope_api_key:
            return {
                'provider': 'dashscope',
                'api_key': self.dashscope_api_key,
                'base_url': self.dashscope_base_url,
                'model': self.dashscope_model,
            }
        if self.openai_api_key:
            return {
                'provider': 'openai',
                'api_key': self.openai_api_key,
                'base_url': self.openai_base_url,
                'model': self.openai_model,
            }

        # 没有可用的 AI 配置
        return None


# === ��ݵ����÷��ʺ��� ===
def get_config() -> Config:
    """Convenience accessor for global config singleton"""
    return Config.get_instance()


if __name__ == "__main__":
    # Config load test
    config = get_config()
    print("=== Config Load Test ===")
    print(f"Watchlist: {config.stock_list}")
    print(f"Database path: {config.database_path}")
    print(f"Max workers: {config.max_workers}")
    print(f"Debug: {config.debug}")
    
    # Validate
    warnings = config.validate()
    if warnings:
        print("\nValidation results:")
        for w in warnings:
            print(f"  - {w}")
