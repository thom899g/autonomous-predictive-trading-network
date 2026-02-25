"""
Firebase Firestore client for state management and real-time data storage.
Provides centralized database operations with connection pooling and error handling.
"""
import logging
from typing import Dict, Any, List, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError
from google.cloud.firestore_v1.client import Client as FirestoreClient
from google.api_core.exceptions import GoogleAPICallError, RetryError

from config import config

class FirebaseClient:
    """Singleton Firebase Firestore client with connection management."""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Firebase app and Firestore client."""
        self.logger = logging.getLogger(__name__)
        
        try:
            # Check if Firebase app already initialized
            if not firebase_admin._apps:
                cred = credentials.Certificate(config.firebase.cred_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': config.firebase.project_id
                })
            
            self._client = firestore.client()
            self.logger.info("Firebase Firestore client initialized successfully")
            
        except (ValueError, FileNotFoundError) as e:
            self.logger.error(f"Failed to initialize Firebase: {e}")
            raise ConnectionError(f"Firebase initialization failed: {e}")
    
    @property
    def client(self) -> FirestoreClient:
        """Get Firestore client instance."""
        if self._client is None:
            raise RuntimeError("Firebase client not initialized")
        return self._client
    
    def write_market_data(self, 
                         symbol: str, 
                         timeframe: str, 
                         data: Dict[str, Any],
                         batch_size: int = 500) -> bool:
        """
        Write market data to Firestore with batch processing.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            timeframe: Chart timeframe (e.g., "1h")
            data: Market data dictionary with timestamp as key
            batch_size: Maximum documents per batch
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection_path = f"{config.firebase.collection_prefix}/market_data/{symbol.replace('/', '_')}/{timeframe}"
            batch = self.client.batch()
            batch_count = 0
            
            for timestamp, candle_data in data.items():
                doc_ref = self.client.collection(collection_path).document(str(timestamp))
                batch.set(doc_ref, {
                    **candle_data,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': int(timestamp),
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
                batch_count += 1
                
                if batch_count >= batch_size:
                    batch.commit()
                    batch = self.client.batch()
                    batch_count = 0
            
            if batch_count > 0:
                batch.commit()
            
            self.logger.info(f"Successfully wrote {len(data)} records for {symbol} {timeframe}")
            return True
            
        except (GoogleAPICallError, RetryError, FirebaseError) as e:
            self.logger.error(f"Failed to write market data: {e}")
            return False
    
    def read_market_data(self,
                        symbol: str,
                        timeframe: str,
                        limit: int = 1000,
                        order_by: str = "timestamp") -> List[Dict[str, Any]]:
        """
        Read market data from Firestore with pagination.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Chart timeframe
            limit: Maximum documents to return
            order_by: Field to order by
            
        Returns:
            List of market data documents
        """
        try:
            collection_path = f"{config.firebase.collection_prefix}/market_data/{symbol.replace('/', '_')}/{timeframe}"
            query = self.client.collection(collection_path)
            
            # Add ordering and limit
            query = query.order_by(order_by, direction=firestore.Query.DESCENDING).limit(limit)