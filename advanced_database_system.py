#!/usr/bin/env python3
"""
Advanced Database System for Cryptocurrency Trading
PostgreSQL, SQLite, Data Warehousing, and Analytics
"""

import sqlite3
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import threading
import time

# Try to import PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.sqlite_path = "crypto_trading_data.db"
        self.backup_path = "backups/"
        self.postgresql_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'crypto_trading',
            'user': 'crypto_user',
            'password': 'crypto_password'
        }
        
        # Create backup directory
        Path(self.backup_path).mkdir(exist_ok=True)

class AdvancedSQLiteManager:
    """Advanced SQLite database manager with optimizations"""
    
    def __init__(self, db_path: str = "crypto_trading_data.db"):
        self.db_path = db_path
        self.connection = None
        self.lock = threading.Lock()
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with optimized settings"""
        try:
            self.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            
            # Enable WAL mode for better concurrency
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=10000")
            self.connection.execute("PRAGMA temp_store=MEMORY")
            
            self._create_tables()
            logger.info(f"✅ SQLite database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing SQLite database: {e}")
    
    def _create_tables(self):
        """Create all necessary tables"""
        tables = {
            'price_data': '''
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    market_cap REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp)
                )
            ''',
            'trading_signals': '''
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    confidence REAL,
                    price REAL,
                    timestamp DATETIME NOT NULL,
                    model_name TEXT,
                    features TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'portfolio_history': '''
                CREATE TABLE IF NOT EXISTS portfolio_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    total_value REAL,
                    cash_balance REAL,
                    positions TEXT,
                    pnl REAL,
                    drawdown REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'trades': '''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL,
                    price REAL,
                    timestamp DATETIME NOT NULL,
                    order_id TEXT,
                    commission REAL,
                    pnl REAL,
                    strategy TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'market_data': '''
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    total_market_cap REAL,
                    total_volume REAL,
                    btc_dominance REAL,
                    fear_greed_index INTEGER,
                    active_cryptocurrencies INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'model_performance': '''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    symbol TEXT,
                    accuracy REAL,
                    precision_score REAL,
                    recall REAL,
                    f1_score REAL,
                    mse REAL,
                    mae REAL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'system_metrics': '''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    network_io TEXT,
                    api_calls INTEGER,
                    response_time REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            '''
        }
        
        # Create tables
        for table_name, sql in tables.items():
            try:
                self.connection.execute(sql)
                logger.info(f"✅ Created/verified table: {table_name}")
            except Exception as e:
                logger.error(f"Error creating table {table_name}: {e}")
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_price_symbol_timestamp ON price_data(symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp ON trading_signals(symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp ON trades(symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_portfolio_timestamp ON portfolio_history(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_market_timestamp ON market_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_performance_model ON model_performance(model_name, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp)"
        ]
        
        for index_sql in indexes:
            try:
                self.connection.execute(index_sql)
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")
        
        self.connection.commit()
    
    def insert_price_data(self, data: List[Dict]) -> bool:
        """Insert price data with batch processing"""
        try:
            with self.lock:
                sql = '''
                    INSERT OR REPLACE INTO price_data 
                    (symbol, timestamp, open, high, low, close, volume, market_cap)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                '''
                
                batch_data = []
                for item in data:
                    batch_data.append((
                        item.get('symbol'),
                        item.get('timestamp'),
                        item.get('open'),
                        item.get('high'),
                        item.get('low'),
                        item.get('close'),
                        item.get('volume'),
                        item.get('market_cap')
                    ))
                
                self.connection.executemany(sql, batch_data)
                self.connection.commit()
                
                logger.info(f"✅ Inserted {len(batch_data)} price data records")
                return True
                
        except Exception as e:
            logger.error(f"Error inserting price data: {e}")
            return False
    
    def insert_trading_signal(self, signal: Dict) -> bool:
        """Insert trading signal"""
        try:
            with self.lock:
                sql = '''
                    INSERT INTO trading_signals 
                    (symbol, signal_type, direction, confidence, price, timestamp, model_name, features)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                '''
                
                self.connection.execute(sql, (
                    signal.get('symbol'),
                    signal.get('signal_type'),
                    signal.get('direction'),
                    signal.get('confidence'),
                    signal.get('price'),
                    signal.get('timestamp'),
                    signal.get('model_name'),
                    json.dumps(signal.get('features', {}))
                ))
                
                self.connection.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error inserting trading signal: {e}")
            return False
    
    def get_price_history(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get price history for a symbol"""
        try:
            sql = '''
                SELECT * FROM price_data 
                WHERE symbol = ? AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp ASC
            '''.format(days)
            
            df = pd.read_sql_query(sql, self.connection, params=(symbol,))
            return df
            
        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return pd.DataFrame()
    
    def get_trading_signals(self, symbol: str = None, hours: int = 24) -> pd.DataFrame:
        """Get recent trading signals"""
        try:
            if symbol:
                sql = '''
                    SELECT * FROM trading_signals 
                    WHERE symbol = ? AND timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                '''.format(hours)
                params = (symbol,)
            else:
                sql = '''
                    SELECT * FROM trading_signals 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                '''.format(hours)
                params = ()
            
            df = pd.read_sql_query(sql, self.connection, params=params)
            return df
            
        except Exception as e:
            logger.error(f"Error getting trading signals: {e}")
            return pd.DataFrame()
    
    def get_portfolio_performance(self, days: int = 30) -> pd.DataFrame:
        """Get portfolio performance history"""
        try:
            sql = '''
                SELECT * FROM portfolio_history 
                WHERE timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp ASC
            '''.format(days)
            
            df = pd.read_sql_query(sql, self.connection)
            return df
            
        except Exception as e:
            logger.error(f"Error getting portfolio performance: {e}")
            return pd.DataFrame()
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to maintain database size"""
        try:
            with self.lock:
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                tables_to_clean = [
                    'price_data',
                    'trading_signals', 
                    'system_metrics'
                ]
                
                for table in tables_to_clean:
                    sql = f"DELETE FROM {table} WHERE created_at < ?"
                    cursor = self.connection.execute(sql, (cutoff_date,))
                    deleted_rows = cursor.rowcount
                    
                    if deleted_rows > 0:
                        logger.info(f"🧹 Cleaned {deleted_rows} old records from {table}")
                
                self.connection.commit()
                
                # Vacuum to reclaim space
                self.connection.execute("VACUUM")
                logger.info("✅ Database cleanup completed")
                
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
    
    def backup_database(self) -> str:
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backups/crypto_db_backup_{timestamp}.db"
            
            # Create backup using SQLite backup API
            backup_conn = sqlite3.connect(backup_file)
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            logger.info(f"✅ Database backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return ""

class PostgreSQLManager:
    """PostgreSQL database manager for production use"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.connection = None
        self.available = POSTGRESQL_AVAILABLE
        
        if self.available:
            self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize PostgreSQL connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            
            self._create_tables()
            logger.info("✅ PostgreSQL database connected")
            
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}")
            self.available = False
    
    def _create_tables(self):
        """Create PostgreSQL tables with advanced features"""
        if not self.available or not self.connection:
            return
        
        tables = {
            'price_data_pg': '''
                CREATE TABLE IF NOT EXISTS price_data_pg (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    open DECIMAL(20,8),
                    high DECIMAL(20,8),
                    low DECIMAL(20,8),
                    close DECIMAL(20,8),
                    volume DECIMAL(20,8),
                    market_cap BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp)
                )
            ''',
            'trading_signals_pg': '''
                CREATE TABLE IF NOT EXISTS trading_signals_pg (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    signal_type VARCHAR(50) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    confidence DECIMAL(5,4),
                    price DECIMAL(20,8),
                    timestamp TIMESTAMP NOT NULL,
                    model_name VARCHAR(100),
                    features JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        }
        
        try:
            cursor = self.connection.cursor()
            
            for table_name, sql in tables.items():
                cursor.execute(sql)
                logger.info(f"✅ Created/verified PostgreSQL table: {table_name}")
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_pg_price_symbol_timestamp ON price_data_pg(symbol, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_pg_signals_symbol_timestamp ON trading_signals_pg(symbol, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_pg_signals_features ON trading_signals_pg USING GIN (features)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            self.connection.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error creating PostgreSQL tables: {e}")
    
    def insert_price_data_batch(self, data: List[Dict]) -> bool:
        """Batch insert price data to PostgreSQL"""
        if not self.available or not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            sql = '''
                INSERT INTO price_data_pg 
                (symbol, timestamp, open, high, low, close, volume, market_cap)
                VALUES %s
                ON CONFLICT (symbol, timestamp) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                market_cap = EXCLUDED.market_cap
            '''
            
            values = []
            for item in data:
                values.append((
                    item.get('symbol'),
                    item.get('timestamp'),
                    item.get('open'),
                    item.get('high'),
                    item.get('low'),
                    item.get('close'),
                    item.get('volume'),
                    item.get('market_cap')
                ))
            
            from psycopg2.extras import execute_values
            execute_values(cursor, sql, values)
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Inserted {len(values)} records to PostgreSQL")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting to PostgreSQL: {e}")
            return False

class DataWarehouse:
    """Data warehouse for analytics and reporting"""
    
    def __init__(self, sqlite_manager: AdvancedSQLiteManager):
        self.sqlite_manager = sqlite_manager
        self.analytics_cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    def generate_market_analytics(self) -> Dict:
        """Generate comprehensive market analytics"""
        try:
            # Check cache
            cache_key = "market_analytics"
            if self._is_cache_valid(cache_key):
                return self.analytics_cache[cache_key]['data']
            
            analytics = {}
            
            # Price analytics
            price_sql = '''
                SELECT 
                    symbol,
                    COUNT(*) as data_points,
                    AVG(close) as avg_price,
                    MIN(close) as min_price,
                    MAX(close) as max_price,
                    AVG(volume) as avg_volume,
                    MAX(timestamp) as last_update
                FROM price_data 
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY symbol
                ORDER BY avg_volume DESC
                LIMIT 50
            '''
            
            price_df = pd.read_sql_query(price_sql, self.sqlite_manager.connection)
            analytics['top_cryptocurrencies'] = price_df.to_dict('records')
            
            # Trading signals analytics
            signals_sql = '''
                SELECT 
                    direction,
                    COUNT(*) as signal_count,
                    AVG(confidence) as avg_confidence,
                    model_name
                FROM trading_signals 
                WHERE timestamp >= datetime('now', '-24 hours')
                GROUP BY direction, model_name
                ORDER BY signal_count DESC
            '''
            
            signals_df = pd.read_sql_query(signals_sql, self.sqlite_manager.connection)
            analytics['signal_distribution'] = signals_df.to_dict('records')
            
            # Portfolio performance
            portfolio_sql = '''
                SELECT 
                    DATE(timestamp) as date,
                    AVG(total_value) as avg_portfolio_value,
                    AVG(pnl) as avg_pnl,
                    AVG(drawdown) as avg_drawdown
                FROM portfolio_history 
                WHERE timestamp >= datetime('now', '-30 days')
                GROUP BY DATE(timestamp)
                ORDER BY date ASC
            '''
            
            portfolio_df = pd.read_sql_query(portfolio_sql, self.sqlite_manager.connection)
            analytics['portfolio_performance'] = portfolio_df.to_dict('records')
            
            # System performance
            system_sql = '''
                SELECT 
                    AVG(cpu_usage) as avg_cpu,
                    AVG(memory_usage) as avg_memory,
                    AVG(response_time) as avg_response_time,
                    SUM(api_calls) as total_api_calls
                FROM system_metrics 
                WHERE timestamp >= datetime('now', '-24 hours')
            '''
            
            system_df = pd.read_sql_query(system_sql, self.sqlite_manager.connection)
            analytics['system_performance'] = system_df.to_dict('records')[0] if not system_df.empty else {}
            
            # Cache results
            self.analytics_cache[cache_key] = {
                'data': analytics,
                'timestamp': time.time()
            }
            
            logger.info("✅ Generated market analytics")
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating market analytics: {e}")
            return {}
    
    def generate_model_performance_report(self) -> Dict:
        """Generate model performance report"""
        try:
            cache_key = "model_performance"
            if self._is_cache_valid(cache_key):
                return self.analytics_cache[cache_key]['data']
            
            sql = '''
                SELECT 
                    model_name,
                    COUNT(*) as evaluations,
                    AVG(accuracy) as avg_accuracy,
                    AVG(precision_score) as avg_precision,
                    AVG(recall) as avg_recall,
                    AVG(f1_score) as avg_f1,
                    AVG(mse) as avg_mse,
                    AVG(mae) as avg_mae,
                    MAX(timestamp) as last_evaluation
                FROM model_performance 
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY model_name
                ORDER BY avg_accuracy DESC
            '''
            
            df = pd.read_sql_query(sql, self.sqlite_manager.connection)
            report = {
                'model_rankings': df.to_dict('records'),
                'best_model': df.iloc[0].to_dict() if not df.empty else {},
                'total_models': len(df)
            }
            
            # Cache results
            self.analytics_cache[cache_key] = {
                'data': report,
                'timestamp': time.time()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating model performance report: {e}")
            return {}
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid"""
        if cache_key not in self.analytics_cache:
            return False
        
        cache_age = time.time() - self.analytics_cache[cache_key]['timestamp']
        return cache_age < self.cache_timeout

class DatabaseManager:
    """Main database manager coordinating all database operations"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.sqlite_manager = AdvancedSQLiteManager(self.config.sqlite_path)
        self.postgresql_manager = PostgreSQLManager(self.config.postgresql_config)
        self.data_warehouse = DataWarehouse(self.sqlite_manager)
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        def cleanup_task():
            while True:
                time.sleep(3600)  # Run every hour
                self.sqlite_manager.cleanup_old_data()
        
        def backup_task():
            while True:
                time.sleep(86400)  # Run daily
                self.sqlite_manager.backup_database()
        
        # Start background threads
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        backup_thread = threading.Thread(target=backup_task, daemon=True)
        
        cleanup_thread.start()
        backup_thread.start()
        
        logger.info("✅ Background database tasks started")
    
    def store_market_data(self, data: List[Dict]) -> bool:
        """Store market data in both SQLite and PostgreSQL"""
        success = True
        
        # Store in SQLite
        if not self.sqlite_manager.insert_price_data(data):
            success = False
        
        # Store in PostgreSQL if available
        if self.postgresql_manager.available:
            if not self.postgresql_manager.insert_price_data_batch(data):
                logger.warning("PostgreSQL insert failed, continuing with SQLite")
        
        return success
    
    def store_trading_signal(self, signal: Dict) -> bool:
        """Store trading signal"""
        return self.sqlite_manager.insert_trading_signal(signal)
    
    def get_analytics_dashboard(self) -> Dict:
        """Get comprehensive analytics for dashboard"""
        return {
            'market_analytics': self.data_warehouse.generate_market_analytics(),
            'model_performance': self.data_warehouse.generate_model_performance_report(),
            'database_status': {
                'sqlite_available': True,
                'postgresql_available': self.postgresql_manager.available,
                'last_backup': 'Available',
                'total_records': self._get_total_records()
            }
        }
    
    def _get_total_records(self) -> Dict:
        """Get total record counts"""
        try:
            tables = ['price_data', 'trading_signals', 'trades', 'portfolio_history']
            counts = {}
            
            for table in tables:
                cursor = self.sqlite_manager.connection.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            
            return counts
            
        except Exception as e:
            logger.error(f"Error getting record counts: {e}")
            return {}

# Usage example and testing
if __name__ == "__main__":
    print("🗄️ Advanced Database System Test")
    print("=" * 50)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Test data insertion
    test_data = [
        {
            'symbol': 'BTC',
            'timestamp': datetime.now(),
            'open': 50000.0,
            'high': 51000.0,
            'low': 49000.0,
            'close': 50500.0,
            'volume': 1000000.0,
            'market_cap': 1000000000000
        },
        {
            'symbol': 'ETH',
            'timestamp': datetime.now(),
            'open': 3000.0,
            'high': 3100.0,
            'low': 2900.0,
            'close': 3050.0,
            'volume': 500000.0,
            'market_cap': 400000000000
        }
    ]
    
    print("📊 Testing data insertion...")
    success = db_manager.store_market_data(test_data)
    print(f"✅ Data insertion: {'Success' if success else 'Failed'}")
    
    # Test trading signal
    test_signal = {
        'symbol': 'BTC',
        'signal_type': 'ML_PREDICTION',
        'direction': 'BUY',
        'confidence': 0.85,
        'price': 50500.0,
        'timestamp': datetime.now(),
        'model_name': 'LSTM_Ensemble',
        'features': {'rsi': 45, 'macd': 0.02}
    }
    
    print("📡 Testing signal storage...")
    signal_success = db_manager.store_trading_signal(test_signal)
    print(f"✅ Signal storage: {'Success' if signal_success else 'Failed'}")
    
    # Test analytics
    print("📈 Generating analytics...")
    analytics = db_manager.get_analytics_dashboard()
    
    print(f"📊 Database Status:")
    print(f"   SQLite: Available")
    print(f"   PostgreSQL: {'Available' if db_manager.postgresql_manager.available else 'Not Available'}")
    
    if analytics['database_status']['total_records']:
        print(f"📋 Record Counts:")
        for table, count in analytics['database_status']['total_records'].items():
            print(f"   {table}: {count}")
    
    print("\n✅ Advanced Database System test completed!") 