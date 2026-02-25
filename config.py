"""
Configuration management for the Autonomous Predictive Trading Network.
Centralizes environment variables, exchange credentials, and system constants.
"""
import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

@dataclass
class FirebaseConfig:
    """Firebase configuration and credentials."""
    project_id: str = os.getenv("FIREBASE_PROJECT_ID", "autonomous-trading")
    cred_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-creds.json")
    collection_prefix: str = os.getenv("FIREBASE_COLLECTION_PREFIX", "trading_system")

@dataclass
class ExchangeConfig:
    """Exchange API configuration."""
    exchange_id: str = os.getenv("EXCHANGE_ID", "binance")
    api_key: Optional[str] = os.getenv("EXCHANGE_API_KEY")
    api_secret: Optional[str] = os.getenv("EXCHANGE_API_SECRET")
    testnet: bool = os.getenv("EXCHANGE_TESTNET", "true").lower() == "true"
    rate_limit: int = int(os.getenv("EXCHANGE_RATE_LIMIT", "1200"))

@dataclass
class DataConfig:
    """Data collection and processing configuration."""
    default_symbols: list = None
    timeframes: list = None
    max_retries: int = 3
    retry_delay: int = 5
    chunk_size: int = 500
    
    def __post_init__(self):
        if self.default_symbols is None:
            self.default_symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
        if self.timeframes is None:
            self.timeframes = ["1h", "4h", "1d"]

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: int = logging.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "./logs/trading_system.log"

class Config:
    """Main configuration aggregator."""
    
    def __init__(self):
        self.firebase = FirebaseConfig()
        self.exchange = ExchangeConfig()
        self.data = DataConfig()
        self.logging = LoggingConfig()
        
        # Validate critical configurations
        self._validate()
    
    def _validate(self):
        """Validate critical configuration values."""
        if not os.path.exists(self.firebase.cred_path):
            logging.warning(f"Firebase credentials not found at {self.firebase.cred_path}")
        
        if not self.exchange.api_key or not self.exchange.api_secret:
            logging.warning("Exchange API credentials not set. Some functionality will be limited.")

# Global configuration instance
config = Config()