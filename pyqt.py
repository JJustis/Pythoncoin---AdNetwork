#!/usr/bin/env python3
"""
Fixed Unified PythonCoin P2P Ad Network Wallet
Combines cryptocurrency wallet functionality with P2P advertising network
Automatic payments to developers on ad clicks with proper genesis distribution
"""
from urllib.parse import parse_qs
import sys
# Enhanced Database Auto-Registration for P2P Clients
import mysql.connector
import requests
import atexit
import signal
import socket

# Enhanced Database Manager for Full Integration

# Enhanced Database Manager for Full Integration
class EnhancedDatabaseManager:
    """
    Comprehensive database manager for PythonCoin P2P Ad Network.
    Handles connection, table creation, and data operations for developers,
    P2P clients, ad clicks, and ad caching.
    """
    
    def __init__(self, db_config=None):
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'adnetwrk',
            'user': 'root',
            'password': ''
        }
        self.connection = None
        self.is_connected = False
        self._ensure_db_exists()
        self.connect()
        self._create_tables()
        
    def _ensure_db_exists(self):
        """Ensures the 'adnetwrk' database exists. Creates it if not present."""
        temp_conn = None
        try:
            import mysql.connector
            temp_conn = mysql.connector.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            cursor = temp_conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.close()
            logger.info(f"Database '{self.db_config['database']}' ensured to exist.")
        except Exception as err:
            logger.error(f"Error ensuring database exists: {err}")
        finally:
            if temp_conn:
                temp_conn.close()

    def connect(self):
        """Establishes a connection to the MySQL database."""
        if self.is_connected and self.connection and hasattr(self.connection, 'is_connected') and self.connection.is_connected():
            return True
        try:
            import mysql.connector
            self.connection = mysql.connector.connect(
                host=self.db_config['host'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                autocommit=True,
                charset='utf8mb4'
            )
            self.is_connected = True
            logger.info("✅ Enhanced database connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Enhanced database connection failed: {e}")
            self.is_connected = False
            self.connection = None
            return False
            
    def _create_tables(self):
        """Creates necessary tables for the ad network if they don't already exist."""
        if not self.connect():
            logger.error("Cannot create tables: Database not connected.")
            return

        cursor = self.connection.cursor()
        try:
            tables = {
                'developers': """
                    CREATE TABLE IF NOT EXISTS developers (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        pythoncoin_address VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                'p2p_clients': """
                    CREATE TABLE IF NOT EXISTS p2p_clients (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        client_id VARCHAR(100) UNIQUE NOT NULL,
                        name VARCHAR(255),
                        host VARCHAR(255),
                        port VARCHAR(10),
                        status VARCHAR(50),
                        ad_count INT DEFAULT 0,
                        peers INT DEFAULT 0,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """,
                'ad_clicks': """
                    CREATE TABLE IF NOT EXISTS ad_clicks (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        ad_id VARCHAR(100),
                        client_id VARCHAR(100),
                        developer_address VARCHAR(100),
                        zone VARCHAR(100),
                        payout_amount DECIMAL(16,8),
                        click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        processed BOOLEAN DEFAULT FALSE
                    )
                """
            }

            for table_name, create_sql in tables.items():
                cursor.execute(create_sql)
                logger.info(f"Table '{table_name}' ensured to exist.")
            self.connection.commit()
            logger.info("Enhanced database tables initialized successfully.")
        except Exception as err:
            logger.error(f"Error creating enhanced tables: {err}")
        finally:
            cursor.close()

    def add_developer(self, username, pythoncoin_address, email=None):
        """Adds a new developer to the database if they don't already exist."""
        if not self.connect(): 
            return False
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO developers (username, pythoncoin_address, email) VALUES (%s, %s, %s)",
                (username, pythoncoin_address, email)
            )
            self.connection.commit()
            logger.info(f"Enhanced: Developer {username} registered.")
            return True
        except Exception as err:
            if hasattr(err, 'errno') and err.errno == 1062:
                logger.warning(f"Enhanced: Developer {username} already exists.")
                return True
            logger.error(f"Enhanced: Error adding developer: {err}")
            return False
        finally:
            cursor.close()

    def record_ad_click(self, ad_id, client_id, developer_address, zone, payout_amount, ip_address, user_agent):
        """Records an ad click event in the database."""
        if not self.connect(): 
            return False
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO ad_clicks (ad_id, client_id, developer_address, zone, payout_amount, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (ad_id, client_id, developer_address, zone, payout_amount, ip_address, user_agent))
            self.connection.commit()
            logger.info(f"Enhanced: Recorded click for ad {ad_id} from {developer_address}")
            return True
        except Exception as err:
            logger.error(f"Enhanced: Error recording ad click: {err}")
            return False
        finally:
            cursor.close()

class DatabaseManager:
    """Comprehensive database manager for PythonCoin P2P Ad Network"""
    
    def __init__(self, db_config=None):
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'adnetwrk',
            'user': 'root',
            'password': ''
        }
        self.connection = None
        self.is_connected = False
        
    def connect(self):
        """Connect to database"""
        try:
            import mysql.connector
            self.connection = mysql.connector.connect(
                host=self.db_config['host'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                autocommit=True,
                charset='utf8mb4'
            )
            self.is_connected = True
            logger.info("✅ Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            try:
                self.connection.close()
                self.is_connected = False
                logger.info("Database disconnected")
            except:
                pass
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute database query safely"""
        if not self.is_connected and not self.connect():
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                cursor.close()
                return True
                
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return None
    
    def register_client(self, client_data):
        """Register or update P2P client in database"""
        try:
            query = """
                INSERT INTO p2p_clients 
                (client_id, name, host, port, username, wallet_address, status, version, capabilities, metadata, ad_count)
                VALUES (%(client_id)s, %(name)s, %(host)s, %(port)s, %(username)s, %(wallet_address)s, 
                        %(status)s, %(version)s, %(capabilities)s, %(metadata)s, %(ad_count)s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                host = VALUES(host),
                port = VALUES(port),
                username = VALUES(username),
                wallet_address = VALUES(wallet_address),
                status = VALUES(status),
                version = VALUES(version),
                capabilities = VALUES(capabilities),
                metadata = VALUES(metadata),
                ad_count = VALUES(ad_count),
                last_seen = CURRENT_TIMESTAMP
            """
            
            params = {
                'client_id': client_data.get('client_id', ''),
                'name': client_data.get('name', ''),
                'host': client_data.get('host', '127.0.0.1'),
                'port': client_data.get('port', 8082),
                'username': client_data.get('username', ''),
                'wallet_address': client_data.get('wallet_address', ''),
                'status': 'online',
                'version': client_data.get('version', '2.1.0'),
                'capabilities': json.dumps(client_data.get('capabilities', [])),
                'metadata': json.dumps(client_data.get('metadata', {})),
                'ad_count': client_data.get('ad_count', 0)
            }
            
            return self.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error registering client: {e}")
            return False
    
    def create_ad(self, ad_data):
        """Create new advertisement in database"""
        try:
            query = """
                INSERT INTO ads 
                (ad_id, client_id, advertiser_address, title, description, image_url, click_url, 
                 category, payout_rate, daily_budget, max_clicks_daily, targeting, status, expires_at)
                VALUES (%(ad_id)s, %(client_id)s, %(advertiser_address)s, %(title)s, %(description)s,
                        %(image_url)s, %(click_url)s, %(category)s, %(payout_rate)s, %(daily_budget)s,
                        %(max_clicks_daily)s, %(targeting)s, %(status)s, %(expires_at)s)
                ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                description = VALUES(description),
                image_url = VALUES(image_url),
                click_url = VALUES(click_url),
                category = VALUES(category),
                payout_rate = VALUES(payout_rate),
                daily_budget = VALUES(daily_budget),
                max_clicks_daily = VALUES(max_clicks_daily),
                targeting = VALUES(targeting),
                status = VALUES(status),
                expires_at = VALUES(expires_at),
                updated_at = CURRENT_TIMESTAMP
            """
            
            params = {
                'ad_id': ad_data.get('id', ''),
                'client_id': ad_data.get('peer_source', ''),
                'advertiser_address': ad_data.get('advertiser_address', ''),
                'title': ad_data.get('title', ''),
                'description': ad_data.get('description', ''),
                'image_url': ad_data.get('image_url', ''),
                'click_url': ad_data.get('click_url', ''),
                'category': ad_data.get('category', 'general'),
                'payout_rate': ad_data.get('payout_rate', 0.001),
                'daily_budget': ad_data.get('targeting', {}).get('budget_daily', 1.0),
                'max_clicks_daily': ad_data.get('targeting', {}).get('max_clicks_daily', 1000),
                'targeting': json.dumps(ad_data.get('targeting', {})),
                'status': 'active',
                'expires_at': ad_data.get('expires_at', None)
            }
            
            result = self.execute_query(query, params)
            if result:
                # Update client ad count
                self.update_client_ad_count(ad_data.get('peer_source', ''))
            return result
            
        except Exception as e:
            logger.error(f"Error creating ad: {e}")
            return False
    
    def update_client_ad_count(self, client_id):
        """Update ad count for a client"""
        try:
            query = """
                UPDATE p2p_clients 
                SET ad_count = (
                    SELECT COUNT(*) FROM ads WHERE client_id = %s AND status = 'active'
                )
                WHERE client_id = %s
            """
            return self.execute_query(query, (client_id, client_id))
        except Exception as e:
            logger.error(f"Error updating client ad count: {e}")
            return False
    
    def get_all_clients(self):
        """Get all P2P clients"""
        query = "SELECT * FROM p2p_clients ORDER BY last_seen DESC"
        return self.execute_query(query, fetch=True) or []
    
    def get_active_ads(self):
        """Get all active advertisements"""
        query = """
            SELECT a.*, c.name as client_name 
            FROM ads a 
            LEFT JOIN p2p_clients c ON a.client_id = c.client_id 
            WHERE a.status = 'active' 
            ORDER BY a.created_at DESC
        """
        return self.execute_query(query, fetch=True) or []
    
    def record_ad_click(self, click_data):
        """Record an ad click"""
        try:
            query = """
                INSERT INTO ad_clicks 
                (ad_id, client_id, zone, payout_amount, ip_address, user_agent, metadata)
                VALUES (%(ad_id)s, %(client_id)s, %(zone)s, %(payout_amount)s, 
                        %(ip_address)s, %(user_agent)s, %(metadata)s)
            """
            
            params = {
                'ad_id': click_data.get('ad_id', ''),
                'client_id': click_data.get('client_id', ''),
                'zone': click_data.get('zone', ''),
                'payout_amount': click_data.get('payout_amount', 0.001),
                'ip_address': click_data.get('ip_address', ''),
                'user_agent': click_data.get('user_agent', ''),
                'metadata': json.dumps(click_data.get('metadata', {}))
            }
            
            return self.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error recording ad click: {e}")
            return False
    
    def create_notification(self, notification_data):
        """Create system notification"""
        try:
            query = """
                INSERT INTO notifications (type, title, message, recipient_type, metadata, priority)
                VALUES (%(type)s, %(title)s, %(message)s, %(recipient_type)s, %(metadata)s, %(priority)s)
            """
            
            params = {
                'type': notification_data.get('type', 'system'),
                'title': notification_data.get('title', ''),
                'message': notification_data.get('message', ''),
                'recipient_type': notification_data.get('recipient_type', 'all'),
                'metadata': json.dumps(notification_data.get('metadata', {})),
                'priority': notification_data.get('priority', 'normal')
            }
            
            return self.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return False
    
    def get_recent_notifications(self, limit=10):
        """Get recent notifications"""
        query = """
            SELECT * FROM notifications 
            WHERE recipient_type IN ('all', 'clients')
            ORDER BY created_at DESC 
            LIMIT %s
        """
        return self.execute_query(query, (limit,), fetch=True) or []
    
    def update_client_status(self, client_id, status):
        """Update client status"""
        query = """
            UPDATE p2p_clients 
            SET status = %s, last_seen = CURRENT_TIMESTAMP 
            WHERE client_id = %s
        """
        return self.execute_query(query, (status, client_id))


class DatabaseAutoRegistration:
    """Handles automatic database registration for P2P clients"""
    
    def __init__(self, username, wallet_address, client_name="PythonCoin P2P Client", port=8082):
        self.username = username
        self.wallet_address = wallet_address
        self.client_name = client_name
        self.client_id = f"pyc_{username}_{uuid.uuid4().hex[:8]}"
        self.host = self.get_local_ip()
        self.port = port
        self.version = "2.1.0"
        
        # Database config
        self.db_config = {
            'host': 'localhost',
            'database': 'adnetwrk',
            'user': 'root',
            'password': ''
        }
        
        # Server config
        self.server_config = {
            'api_url': 'http://secupgrade.com/livepy/pythoncoin/api.php'
        }
        
        self.db_connection = None
        self.registered = False
        
        # Setup cleanup handlers
        atexit.register(self.cleanup_on_exit)
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "secupgrade.com"
    
    def connect_database(self):
        """Connect to MySQL database"""
        try:
            self.db_connection = mysql.connector.connect(
                host=self.db_config['host'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                autocommit=True
            )
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def register_client(self, wallet=None, blockchain=None):
        """Register client with database and server"""
        if self.registered:
            return True
        
        # Generate sample ad inventory
        ad_inventory = [
            {
                'ad_id': f'pyc_ad_{self.client_id}_1',
                'title': f'PythonCoin Mining Pool - {self.username}',
                'description': 'Join our decentralized mining pool for consistent PYC rewards',
                'category': 'cryptocurrency',
                'payout_rate': 0.00250000,
                'click_url': 'https://pythoncoin-mining.example.com',
                'image_url': '',
                'targeting_tags': ['mining', 'cryptocurrency', 'python'],
                'active': True
            }
        ]
        
        # Prepare registration data
        registration_data = {
            'action': 'client_register_live',
            'client_id': self.client_id,
            'username': self.username,
            'wallet_address': self.wallet_address,
            'client_name': self.client_name,
            'host': self.host,
            'port': self.port,
            'version': self.version,
            'capabilities': ['ad_serving', 'payment_processing'],
            'ad_inventory': ad_inventory,
            'metadata': {
                'start_time': datetime.now().isoformat(),
                'python_version': sys.version,
                'platform': os.name
            }
        }
        
        # Try to register with server
        success = self.register_with_server(registration_data)
        
        # If server registration fails, try direct database registration
        if not success:
            success = self.register_with_database(registration_data)
        
        if success:
            self.registered = True
            logger.info(f"✅ Client registered successfully: {self.client_id}")
            # Start background heartbeat
            self.start_heartbeat()
        
        return success
    
    def register_with_server(self, data):
        """Register with remote server"""
        try:
            response = requests.post(
                self.server_config['api_url'],
                json=data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"✅ Registered with server")
                    return True
            return False
        except Exception as e:
            logger.error(f"Server registration error: {e}")
            return False
    
    def register_with_database(self, data):
        """Register directly with database"""
        if not self.connect_database():
            return False
        
        cursor = self.db_connection.cursor()
        
        try:
            # Register client
            cursor.execute("""
                INSERT INTO p2p_clients 
                (client_id, name, host, port, username, wallet_address, status, version, 
                 capabilities, metadata, ad_count, last_seen, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, 'online', %s, %s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE 
                status = 'online',
                last_seen = NOW()
            """, (
                data['client_id'], data['client_name'], data['host'], data['port'],
                data['username'], data['wallet_address'], data['version'],
                json.dumps(data['capabilities']), json.dumps(data['metadata']),
                len(data['ad_inventory'])
            ))
            
            logger.info(f"✅ Registered directly with database: {data['client_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Database registration failed: {e}")
            return False
        finally:
            cursor.close()
    
    def start_heartbeat(self):
        """Start heartbeat thread"""
    def heartbeat_worker():
            while self.registered:
                try:
                    # Send heartbeat
                    if self.db_connection:
                        cursor = self.db_connection.cursor()
                        cursor.execute("""
                            UPDATE p2p_clients 
                            SET last_seen = NOW(), status = 'online'
                            WHERE client_id = %s
                        """, (self.client_id,))
                        cursor.close()
                    
                    time.sleep(60)  # Heartbeat every minute
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    time.sleep(120)
        
            heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
            heartbeat_thread.start()
    
    def cleanup_on_exit(self):
        """Clean up on exit"""
        if self.registered and self.db_connection:
            try:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    UPDATE p2p_clients 
                    SET status = 'offline', last_seen = NOW()
                    WHERE client_id = %s
                """, (self.client_id,))
                cursor.close()
                self.db_connection.close()
                logger.info(f"✅ Client cleanup completed: {self.client_id}")
            except:
                pass


import os
import json
import hashlib
import base64
import time
import random
import re
import qrcode
from io import BytesIO
import traceback
import threading
import logging
import uuid
import struct
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from PyQt5.QtCore import QThread, pyqtSignal
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import socketserver
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PythonCoin-P2P-Wallet")

# PyQt5 imports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QLineEdit, 
                           QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
                           QHeaderView, QFileDialog, QMessageBox, QDialog,
                           QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox,
                           QProgressBar, QProgressDialog, QSplashScreen, QToolBar,
                           QStatusBar, QGroupBox, QScrollArea, QFrame,
                           QSpinBox, QRadioButton, QButtonGroup, QListWidget,
                           QMenu, QInputDialog, QAction, QColorDialog)
from datetime import datetime, timedelta
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                           QPushButton, QCheckBox, QLabel, QMessageBox, QHeaderView,
                           QGroupBox, QFormLayout, QDoubleSpinBox, QSpinBox, QProgressBar)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QImage, QClipboard
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QByteArray, QBuffer

# HTTP server imports
# aiohttp replaced with standard HTTP server
# aiohttp replaced with standard HTTP server
import asyncio
# aiohttp replaced with standard HTTP server
# Import PythonCoin core components
from pythoncoin import (Blockchain, Wallet, Transaction, TransactionInput, TransactionOutput,
                      DataTransaction, DSAVerificationTransaction, CryptoUtils, Node, Block)


# Enhanced imports for enterprise features
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("⚠️ mysql-connector-python not installed. Enhanced database features disabled.")
    print("Install with: pip install mysql-connector-python")

from decimal import Decimal
from urllib.parse import urlparse, parse_qs

# ============================================================================
# Data Classes for P2P Ad Network (same as before)
# ============================================================================

@dataclass
class AdContent:
    id: str
    title: str
    description: str
    image_url: str
    click_url: str
    category: str
    targeting: Dict
    created_at: str
    expires_at: str
    peer_source: str
    payout_rate: float = 0.001  # PYC per click
    advertiser_address: str = ""  # PythonCoin address for payments
    
    def to_dict(self):
        return asdict(self)

@dataclass
class PeerInfo:
    peer_id: str
    host: str
    port: int
    status: str
    last_seen: str
    ad_count: int
    capabilities: List[str]
    wallet_address: str = ""  # PythonCoin address

@dataclass
class UserProfile:
    user_id: str
    interests: List[str]
    demographics: Dict
    behavior_score: Dict
    privacy_level: str
    last_updated: str
    wallet_address: str = ""  # Developer's PythonCoin address

@dataclass
class ClickEvent:
    ad_id: str
    user_id: str
    developer_address: str
    advertiser_address: str
    payout_amount: float
    timestamp: str
    processed: bool = False
    transaction_id: str = ""

# ============================================================================
# Enhanced P2P Manager with Genesis Coordination
# ============================================================================

class CryptoP2PManager(QThread):
    """Enhanced P2P Manager with genesis coordination and cryptocurrency payment processing"""
    
    peerDiscovered = pyqtSignal(str, str, int)
    peerConnected = pyqtSignal(str)
    peerDisconnected = pyqtSignal(str)
    adsReceived = pyqtSignal(list)
    statusUpdate = pyqtSignal(str)
    clickReceived = pyqtSignal(object)  # ClickEvent
    paymentSent = pyqtSignal(str, float)  # address, amount
    genesisReady = pyqtSignal(list)  # List of peer addresses for genesis
    
    def __init__(self, client_id: str, port: int, blockchain: Blockchain, wallet: Wallet):
        super().__init__()
        self.client_id = client_id
        self.port = port
        self.blockchain = blockchain
        self.wallet = wallet
        self.peers: Dict[str, PeerInfo] = {}
        self.peer_sockets: Dict[str, socket.socket] = {}
        self.server_socket = None
        self.running = False
        self.pending_clicks: List[ClickEvent] = []
        self.genesis_coordination_complete = False
        self.discovery_timeout = 30  # Wait 30 seconds for peer discovery before genesis
        
    def run(self):
        """Start P2P socket manager with genesis coordination"""
        self.running = True
        self.statusUpdate.emit("Starting crypto P2P discovery...")
        
        # Start discovery server
        threading.Thread(target=self._discovery_server, daemon=True).start()
        
        # Start peer discovery broadcast
        threading.Thread(target=self._discovery_broadcast, daemon=True).start()
        
        # Start peer connection handler
        threading.Thread(target=self._peer_handler, daemon=True).start()
        
        # Start click processing thread
        threading.Thread(target=self._process_clicks, daemon=True).start()
        
        # Start genesis coordination
        threading.Thread(target=self._coordinate_genesis, daemon=True).start()
        
        self.statusUpdate.emit("Crypto P2P Manager started")
    
    def _coordinate_genesis(self):
        """Coordinate genesis block creation with connected peers"""
        if self.blockchain.genesis_complete:
            logger.info("Genesis block already exists")
            return
        
        logger.info(f"Starting genesis coordination - waiting {self.discovery_timeout} seconds for peers...")
        start_time = time.time()
        
        # Wait for peer discovery or timeout
        while time.time() - start_time < self.discovery_timeout and self.running:
            time.sleep(1)
            
            # Check if we have enough peers for a meaningful distribution
            connected_peers = [p for p in self.peers.values() if p.status == 'connected' and p.wallet_address]
            
            if len(connected_peers) >= 2:  # Wait for at least 2 other peers
                logger.info(f"Found {len(connected_peers)} peers, proceeding with genesis coordination")
                break
        
        # Collect all peer addresses including our own
        genesis_addresses = [self.wallet.address]
        for peer in self.peers.values():
            if peer.status == 'connected' and peer.wallet_address:
                genesis_addresses.append(peer.wallet_address)
        
        if len(genesis_addresses) == 1:
            logger.warning("No peers found, creating single-address genesis block")
        else:
            logger.info(f"Creating genesis block with {len(genesis_addresses)} addresses")
        
        # Set genesis addresses and create genesis block
        self.blockchain.set_genesis_addresses(genesis_addresses)
        self.genesis_coordination_complete = True
        
        # Notify main application
        self.genesisReady.emit(genesis_addresses)
        
        self.statusUpdate.emit(f"Genesis block created with {len(genesis_addresses)} participants")
    
    def _discovery_server(self):
        """UDP discovery server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind(('', self.port + 1000))
            sock.settimeout(1.0)
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    self._handle_discovery_message(data, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.debug(f"Discovery server error: {e}")
                    
        except Exception as e:
            logger.error(f"Discovery server failed: {e}")
        finally:
            sock.close()
    
    def _discovery_broadcast(self):
        """Broadcast presence with wallet info"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        while self.running:
            try:
                message = {
                    'type': 'peer_announce',
                    'peer_id': self.client_id,
                    'port': self.port,
                    'timestamp': datetime.now().isoformat(),
                    'capabilities': ['ad_serving', 'p2p', 'custom_js', 'crypto_payments'],
                    'wallet_address': self.wallet.address if self.wallet else "",
                    'blockchain_height': len(self.blockchain.chain) if self.blockchain else 0,
                    'genesis_complete': self.blockchain.genesis_complete if self.blockchain else False
                }
                
                data = json.dumps(message).encode()
                sock.sendto(data, ('255.255.255.255', self.port + 1000))
                
                time.sleep(10)  # More frequent broadcasts during startup
                
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                time.sleep(5)
        
        sock.close()
    
    def _handle_discovery_message(self, data: bytes, addr):
        """Handle discovery messages"""
        try:
            message = json.loads(data.decode())
            
            if message.get('type') == 'peer_announce':
                peer_id = message.get('peer_id')
                if peer_id != self.client_id:
                    self._add_discovered_peer(message, addr[0])
                    
        except Exception as e:
            logger.debug(f"Discovery message error: {e}")
    
    def _add_discovered_peer(self, message: Dict, host: str):
        """Add discovered peer"""
        peer_id = message['peer_id']
        
        if peer_id not in self.peers:
            peer = PeerInfo(
                peer_id=peer_id,
                host=host,
                port=message['port'],
                status='discovered',
                last_seen=datetime.now().isoformat(),
                ad_count=0,
                capabilities=message.get('capabilities', []),
                wallet_address=message.get('wallet_address', '')
            )
            
            self.peers[peer_id] = peer
            self.peerDiscovered.emit(peer_id, host, message['port'])
            
            # Attempt connection
            threading.Thread(target=self._connect_to_peer, args=(peer,), daemon=True).start()
        else:
            # Update existing peer info
            self.peers[peer_id].last_seen = datetime.now().isoformat()
            self.peers[peer_id].wallet_address = message.get('wallet_address', '')
    
    def _connect_to_peer(self, peer: PeerInfo):
        """Connect to peer"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((peer.host, peer.port + 2000))
            
            handshake = {
                'type': 'handshake',
                'peer_id': self.client_id,
                'timestamp': datetime.now().isoformat(),
                'wallet_address': self.wallet.address if self.wallet else "",
                'capabilities': ['crypto_payments', 'ad_serving'],
                'genesis_complete': self.blockchain.genesis_complete if self.blockchain else False
            }
            
            self._send_message(sock, handshake)
            
            response = self._receive_message(sock)
            if response and response.get('type') == 'handshake_ack':
                self.peer_sockets[peer.peer_id] = sock
                peer.status = 'connected'
                peer.wallet_address = response.get('wallet_address', '')
                self.peerConnected.emit(peer.peer_id)
                
                self._request_ads_from_peer(peer.peer_id)
                self._handle_peer_messages(sock, peer.peer_id)
            else:
                sock.close()
                
        except Exception as e:
            logger.debug(f"Failed to connect to peer {peer.peer_id}: {e}")
    
    def _peer_handler(self):
        """Handle incoming connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.port + 2000))
            self.server_socket.listen(10)
            self.server_socket.settimeout(1.0)
            
            while self.running:
                try:
                    client_sock, addr = self.server_socket.accept()
                    threading.Thread(
                        target=self._handle_peer_connection,
                        args=(client_sock, addr),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
                    
        except Exception as e:
            logger.error(f"Peer handler error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def _handle_peer_connection(self, client_sock, addr):
        """Handle peer connection"""
        try:
            client_sock.settimeout(30)
            
            message = self._receive_message(client_sock)
            if message and message.get('type') == 'handshake':
                peer_id = message.get('peer_id')
                
                ack = {
                    'type': 'handshake_ack',
                    'peer_id': self.client_id,
                    'timestamp': datetime.now().isoformat(),
                    'wallet_address': self.wallet.address if self.wallet else "",
                    'genesis_complete': self.blockchain.genesis_complete if self.blockchain else False
                }
                self._send_message(client_sock, ack)
                
                if peer_id:
                    self.peer_sockets[peer_id] = client_sock
                    if peer_id in self.peers:
                        self.peers[peer_id].status = 'connected'
                        self.peers[peer_id].wallet_address = message.get('wallet_address', '')
                    
                    self.peerConnected.emit(peer_id)
                    self._handle_peer_messages(client_sock, peer_id)
                    
        except Exception as e:
            logger.debug(f"Peer connection error: {e}")
        finally:
            client_sock.close()
    
    def _handle_peer_messages(self, sock, peer_id):
        """Handle peer messages"""
        while self.running:
            try:
                message = self._receive_message(sock)
                if not message:
                    break
                
                if message.get('type') == 'ad_response':
                    ads = message.get('ads', [])
                    self.adsReceived.emit(ads)
                elif message.get('type') == 'click_notification':
                    self._handle_click_notification(message)
                elif message.get('type') == 'payment_request':
                    self._handle_payment_request(message)
                elif message.get('type') == 'blockchain_sync':
                    self._handle_blockchain_sync(message)
                    
            except Exception:
                break
        
        if peer_id in self.peer_sockets:
            del self.peer_sockets[peer_id]
        if peer_id in self.peers:
            self.peers[peer_id].status = 'disconnected'
        self.peerDisconnected.emit(peer_id)
    
    def _handle_click_notification(self, message):
        """Handle click notification from peer"""
        try:
            click_data = message.get('click_data', {})
            
            click_event = ClickEvent(
                ad_id=click_data.get('ad_id', ''),
                user_id=click_data.get('user_id', ''),
                developer_address=click_data.get('developer_address', ''),
                advertiser_address=click_data.get('advertiser_address', ''),
                payout_amount=click_data.get('payout_amount', 0.001),
                timestamp=click_data.get('timestamp', datetime.now().isoformat())
            )
            
            self.pending_clicks.append(click_event)
            self.clickReceived.emit(click_event)
            
        except Exception as e:
            logger.error(f"Error handling click notification: {e}")
    
    def _handle_payment_request(self, message):
        """Handle payment request from peer"""
        try:
            payment_data = message.get('payment_data', {})
            recipient = payment_data.get('recipient_address', '')
            amount = payment_data.get('amount', 0)
            
            if recipient and amount > 0 and self.wallet:
                # Verify we have enough balance
                # Use corrected balance calculation
                try:
                    balance = self.override_wallet_get_balance()
                except AttributeError:
                    balance = self.wallet.get_balance() if hasattr(self.wallet, "get_balance") else 0.0
                if balance >= amount:
                    # Create and send payment transaction
                    tx = self.wallet.send(recipient, amount)
                    if tx:
                        self.paymentSent.emit(recipient, amount)
                        logger.info(f"Payment sent: {amount} PYC to {recipient}")
                        
        except Exception as e:
            logger.error(f"Error handling payment request: {e}")
    
    def _handle_blockchain_sync(self, message):
        """Handle blockchain synchronization request"""
        try:
            sync_data = message.get('sync_data', {})
            peer_height = sync_data.get('blockchain_height', 0)
            our_height = len(self.blockchain.chain)
            
            if peer_height > our_height:
                logger.info(f"Peer has longer chain ({peer_height} vs {our_height}), requesting sync")
                # TODO: Implement actual blockchain sync
                # When implemented, should call main_window.add_block_to_blockchain(block)
                # for each received block to ensure immediate commit
                # In a full implementation, we would request the longer chain
                
        except Exception as e:
            logger.error(f"Error handling blockchain sync: {e}")
    
    def _process_clicks(self):
        """Process pending click events and send payments"""
        while self.running:
            try:
                if self.pending_clicks and self.wallet:
                    click = self.pending_clicks.pop(0)
                    
                    if not click.processed and click.developer_address:
                        # Send payment to developer
                        # Use corrected balance calculation
                        try:
                            balance = self.override_wallet_get_balance()
                        except AttributeError:
                            balance = self.wallet.get_balance() if hasattr(self.wallet, "get_balance") else 0.0
                                
                        if balance >= click.payout_amount:
                            tx = self.wallet.send(click.developer_address, click.payout_amount)
                            if tx:
                                click.processed = True
                                click.transaction_id = tx.tx_id
                                self.paymentSent.emit(click.developer_address, click.payout_amount)
                                
                                logger.info(f"Click payment sent: {click.payout_amount} PYC to {click.developer_address}")
                        else:
                            logger.warning(f"Insufficient balance for click payment: {balance} < {click.payout_amount}")
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error processing clicks: {e}")
                time.sleep(5)
    
    def _send_message(self, sock, message):
        """Send message to peer"""
        data = json.dumps(message).encode()
        length = struct.pack('!I', len(data))
        sock.sendall(length + data)
    
    def _receive_message(self, sock):
        """Receive message from peer"""
        try:
            length_data = sock.recv(4)
            if len(length_data) < 4:
                return None
            
            length = struct.unpack('!I', length_data)[0]
            
            data = b''
            while len(data) < length:
                chunk = sock.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk
            
            return json.loads(data.decode())
            
        except Exception:
            return None
    
    def _request_ads_from_peer(self, peer_id):
        """Request ads from peer"""
        if peer_id not in self.peer_sockets:
            return
        
        request = {
            'type': 'ad_request',
            'requesting_peer': self.client_id,
            'categories': ['all'],
            'max_ads': 10,
            'timestamp': datetime.now().isoformat(),
            'payment_capable': True
        }
        
        try:
            self._send_message(self.peer_sockets[peer_id], request)
        except Exception as e:
            logger.error(f"Failed to request ads from {peer_id}: {e}")
    
    def notify_click(self, ad_id: str, user_id: str, developer_address: str):
        """Notify peers of an ad click"""
        click_data = {
            'type': 'click_notification',
            'click_data': {
                'ad_id': ad_id,
                'user_id': user_id,
                'developer_address': developer_address,
                'timestamp': datetime.now().isoformat(),
                'notifier_address': self.wallet.address if self.wallet else ""
            }
        }
        
        # Send to all connected peers
        for peer_id, sock in self.peer_sockets.items():
            try:
                self._send_message(sock, click_data)
            except Exception as e:
                logger.error(f"Failed to notify peer {peer_id} of click: {e}")
    

    def ensure_coinbase_transaction_exists(self):
        """Ensure a coinbase transaction exists before mining"""
        try:
            # Check if pending transactions already has a coinbase
            has_coinbase = any(getattr(tx, 'tx_type', '') == 'coinbase' 
                             for tx in self.blockchain.pending_transactions)
            
            if not has_coinbase:
                # Create coinbase transaction
                coinbase_tx = self.create_coinbase_transaction()
                if coinbase_tx:
                    self.blockchain.pending_transactions.insert(0, coinbase_tx)
                    logger.info(f"Created coinbase transaction for mining: {coinbase_tx.tx_id}")
            
        except Exception as e:
            logger.error(f"Error ensuring coinbase transaction: {str(e)}")
    
    def create_coinbase_transaction(self):
        """Create a proper coinbase transaction for mining rewards"""
        try:
            from pythoncoin import Transaction, TransactionOutput
            
            # Create coinbase transaction (no inputs, only output to miner)
            mining_reward = 50.0  # Standard mining reward
            
            coinbase_tx = Transaction(
                sender="",  # Coinbase has no sender
                inputs=[],  # Coinbase has no inputs (created from nothing)
                outputs=[TransactionOutput(address=self.wallet.address, amount=mining_reward)]
            )
            
            # Set coinbase-specific properties
            coinbase_tx.tx_type = 'coinbase'
            coinbase_tx.timestamp = time.time()
            coinbase_tx.tx_id = f"coinbase_{uuid.uuid4().hex[:16]}"
            coinbase_tx.signature = ""  # Coinbase doesn't need signature
            
            logger.info(f"Created coinbase transaction: {mining_reward} PYC to {self.wallet.address[:8]}...")
            return coinbase_tx
            
        except Exception as e:
            logger.error(f"Error creating coinbase transaction: {str(e)}")
            return None
    
    def validate_mined_block_has_coinbase(self, block):
        """Validate that the mined block has a proper coinbase transaction"""
        try:
            if not block or not hasattr(block, 'transactions'):
                return False
            
            # Check if first transaction is coinbase
            if not block.transactions:
                logger.warning("Mined block has no transactions!")
                return False
            
            first_tx = block.transactions[0]
            if getattr(first_tx, 'tx_type', '') != 'coinbase':
                logger.warning("Mined block's first transaction is not coinbase!")
                return False
            
            # Check if coinbase goes to our address
            coinbase_reward = 0
            for output in first_tx.outputs:
                if output.address == self.wallet.address:
                    coinbase_reward += output.amount
            
            if coinbase_reward == 0:
                logger.warning("Coinbase transaction doesn't reward our address!")
                return False
            
            logger.info(f"Validated coinbase: {coinbase_reward} PYC to our address")
            return True
            
        except Exception as e:
            logger.error(f"Error validating coinbase: {str(e)}")
            return False

    def stop(self):
        """Stop the P2P manager"""
        self.running = False
        self.statusUpdate.emit("Crypto P2P Manager stopped")

# ============================================================================
# Enhanced Mining Thread with Better Integration
# ============================================================================

class CryptoMiningThread(QThread):
    """Enhanced mining thread with better blockchain integration"""
    
    status_update = pyqtSignal(str)
    hashrate_update = pyqtSignal(float)
    new_block = pyqtSignal(object)
    payment_processed = pyqtSignal(str, float)  # address, amount
    
    def __init__(self, blockchain, wallet, threads=1):
        super().__init__()
        self.blockchain = blockchain
        self.wallet = wallet
        self.threads = threads
        self.running = False
        self.blocks_mined = 0
        self.start_time = 0
        self.hash_count = 0
        self.ad_payments_processed = 0
        
    def run(self):
        """Run the mining process with better integration"""
        self.running = True
        self.status_update.emit("🔍 Mining thread started - checking components...")
        
        # Debug: Check if we have required components
        if not self.blockchain:
            self.status_update.emit("❌ Error: No blockchain available")
            return
        
        if not self.wallet:
            self.status_update.emit("❌ Error: No wallet available")
            return
        
        self.status_update.emit(f"✅ Components ready - wallet: {self.wallet.address[:8]}...")
        print(f"time variable: {locals().get('time', 'NOT FOUND')}")
        #start_time = some_value
        self.start_time = time.time()  # Works!
        self.status_update.emit("Crypto mining started")
        
        # Wait for genesis block if not ready
        if not self.blockchain.genesis_complete:
            self.status_update.emit("Waiting for genesis block...")
            while not self.blockchain.genesis_complete and self.running:
                time.sleep(1)
        
        self.status_update.emit("Genesis block ready, starting mining...")
        
        while self.running:
            try:
                # Simple mining process - ensure we have transactions
                if len(self.blockchain.pending_transactions) == 0:
                    self.status_update.emit("No pending transactions, creating data transaction")
                    try:
                        dummy_tx = DataTransaction(
                            sender=self.wallet.public_key,  # Use public key, not address
                            data_content=f"Mining block at {time.time()}",
                            private_key=self.wallet.private_key  # Provide private key for signing
                        )
                        
                        if self.blockchain.add_transaction(dummy_tx):
                            self.status_update.emit("Added data transaction to pending pool")
                        else:
                            self.status_update.emit("Failed to add data transaction")
                            time.sleep(5)
                            continue
                    except Exception as e:
                        self.status_update.emit(f"Error creating data transaction: {str(e)}")
                        time.sleep(5)
                        continue
                
                # Start mining
                tx_count = len(self.blockchain.pending_transactions)
                self.status_update.emit(f"Mining block with {tx_count} transactions")
                
                # Create coinbase transaction if needed
                if not any(getattr(tx, 'tx_type', '') == 'coinbase' for tx in self.blockchain.pending_transactions):
                    self.status_update.emit("Creating coinbase transaction for mining...")
                    try:
                        
                        # Create coinbase transaction
                        coinbase_tx = Transaction(
                            sender="",  # Coinbase has no sender
                            inputs=[],  # Coinbase has no inputs
                            outputs=[TransactionOutput(address=self.wallet.address, amount=50.0)]
                        )
                        coinbase_tx.tx_type = 'coinbase'
                        coinbase_tx.timestamp = time.time()
                        coinbase_tx.tx_id = f"coinbase_{uuid.uuid4().hex[:16]}"
                        coinbase_tx.signature = ""
                        
                        # Add to pending transactions at the beginning
                        self.blockchain.pending_transactions.insert(0, coinbase_tx)
                        self.status_update.emit("Coinbase transaction created")
                        
                    except Exception as e:
                        self.status_update.emit(f"Coinbase creation error: {str(e)}")
                
                # Mine a new block
                new_block = self.blockchain.mine_pending_transactions(self.wallet.address)
                
                if new_block and self.running:
                    # Validate the mined block has proper coinbase
                    if self.validate_mined_block_has_coinbase(new_block):
                        self.blocks_mined += 1
                        self.status_update.emit(f"Block mined! Height: {new_block.index}, Hash: {new_block.hash[:16]}...")
                        self.new_block.emit(new_block)
                        
                        # Log coinbase details
                        if new_block.transactions:
                            first_tx = new_block.transactions[0]
                            if getattr(first_tx, 'tx_type', '') == 'coinbase':
                                reward = sum(output.amount for output in first_tx.outputs if output.address == self.wallet.address)
                                self.status_update.emit(f"Mining reward: {reward} PYC")
                    else:
                        self.status_update.emit("⚠️ Mined block failed coinbase validation!")
                    self.new_block.emit(new_block)
                    
                    # Calculate hashrate
                    elapsed_time = time.time() - self.start_time
                    hashrate = new_block.nonce / elapsed_time if elapsed_time > 0 else 0
                    self.hashrate_update.emit(hashrate)
                    
                    # Reset timing for next block
                    self.start_time = time.time()
                    
                    # Brief pause before mining next block
                    time.sleep(2)
                else:
                    self.status_update.emit("Mining failed, retrying...")
                    time.sleep(5)
                    
            except Exception as e:
                self.status_update.emit(f"Mining error: {str(e)}")
                logger.error(f"Mining error: {str(e)}")
                time.sleep(5)
    def validate_mined_block_has_coinbase(self, block):
        """Validate that the mined block has a proper coinbase transaction"""
        if not block.transactions:
            return False
        
        # Check if first transaction is coinbase
        coinbase_tx = block.transactions[0]
        
        # Coinbase transaction should have no inputs (or special input)
        if hasattr(coinbase_tx, 'inputs') and coinbase_tx.inputs:
            # Check if it's a proper coinbase input (usually empty or special)
            return len(coinbase_tx.inputs) == 0 or coinbase_tx.inputs[0].get('coinbase', False)
        
        return True  # or implement your specific validation logic
    def stop(self):
        """Stop the mining process"""
        self.running = False
        self.status_update.emit("Crypto mining stopped")

# ============================================================================
# Main Unified Wallet Application (Enhanced)
# ============================================================================


class WorkingDeveloperPortalServer:
    """
    HTTP Server for the PythonCoin Developer Portal API that actually works.
    This server handles API requests including developer registration and ad serving.
    """
    def __init__(self, host='0.0.0.0', port=8082, wallet=None, blockchain=None, db_manager=None):
        self.host = host
        self.port = port
        self.wallet = wallet
        self.blockchain = blockchain
        self.db_manager = db_manager
        self.httpd = None
        self.server_thread = None
        self.running = False
        self.registered_developers = {}
        
        # Define explicit routes for better clarity and control
        self.router = {
            '/register_developer': self._handle_register_developer,
            '/ads': self._handle_get_ads,
            '/ad_click': self._handle_ad_click,
            '/click': self._handle_ad_click,  # Alias for compatibility
            '/client_info': self._handle_client_info,
            '/status': self._handle_status_info,
        }
        
        logger.info(f"Portal server initialized on {host}:{port}")

    def start(self):
        """Starts the HTTP server in a separate thread"""
        if self.running:
            logger.warning("Server is already running")
            return
            
        try:
            from http.server import HTTPServer
            
            # Create the server
            self.httpd = HTTPServer((self.host, self.port), self._create_handler_class())
            self.running = True
            
            # Start server in a separate daemon thread
            self.server_thread = threading.Thread(target=self._serve_forever, daemon=True)
            self.server_thread.start()
            
            logger.info(f"✅ Working portal server started on http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start portal server: {e}")
            self.running = False
            return False

    def stop(self):
        """Stops the HTTP server"""
        try:
            self.running = False
            if self.httpd:
                self.httpd.shutdown()
                self.httpd.server_close()
                self.httpd = None
            logger.info("✅ Portal server stopped")
        except Exception as e:
            logger.error(f"Error stopping server: {e}")

    def _serve_forever(self):
        """Serve requests forever (runs in separate thread)"""
        try:
            logger.info(f"Server listening on {self.host}:{self.port}...")
            self.httpd.serve_forever()
        except Exception as e:
            if self.running:
                logger.error(f"Server error: {e}")

    def _create_handler_class(self):
        """Creates a handler class with access to the server instance"""
        server_instance = self
        
        class WorkingPortalHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                # Custom logging to avoid spam
                timestamp = time.strftime("%H:%M:%S", time.localtime())
                logger.debug(f"[{timestamp}] {format % args}")

            def _parse_request_body(self):
                """Parses the request body based on Content-Type header"""
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = self.rfile.read(content_length).decode('utf-8')
                    content_type = self.headers.get('Content-Type', '').lower()
                    
                    if 'application/json' in content_type:
                        try:
                            return json.loads(body)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON Decode Error: {e}")
                            return {}
                    elif 'application/x-www-form-urlencoded' in content_type:
                        from urllib.parse import parse_qs
                        parsed_data = parse_qs(body)
                        # Convert lists to single values
                        return {k: v[0] if isinstance(v, list) and len(v) == 1 else v 
                               for k, v in parsed_data.items()}
                return {}

            def _send_cors_headers(self):
                """Send CORS headers"""
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                self.send_header('Access-Control-Max-Age', '86400')

            def _send_json_response(self, data, status_code=200):
                """Helper to send a JSON response with CORS headers"""
                self.send_response(status_code)
                self.send_header('Content-Type', 'application/json')
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))

            def do_OPTIONS(self):
                """Handle CORS preflight requests"""
                self.send_response(200)
                self._send_cors_headers()
                self.end_headers()

            def do_GET(self):
                """Handle GET requests"""
                try:
                    parsed_path = urllib.parse.urlparse(self.path)
                    path = parsed_path.path
                    query_params = urllib.parse.parse_qs(parsed_path.query)
                    
                    logger.info(f"GET request to {path}")
                    
                    if path in server_instance.router:
                        server_instance.router[path](self, query_params)
                    elif path == '/' or path == '/test':
                        self._send_json_response({
                            "success": True,
                            "status": "PythonCoin Portal Server Active",
                            "message": "Server is running and accepting connections",
                            "endpoints": list(server_instance.router.keys())
                        })
                    else:
                        self._send_json_response({
                            "success": False, 
                            "error": f"Unknown GET endpoint: {path}"
                        }, 404)
                        
                except Exception as e:
                    logger.error(f"GET error: {e}")
                    self._send_json_response({
                        "success": False, 
                        "error": str(e)
                    }, 500)

            def do_POST(self):
                """Handle POST requests"""
                try:
                    parsed_path = urllib.parse.urlparse(self.path)
                    path = parsed_path.path
                    data = self._parse_request_body()
                    
                    logger.info(f"POST request to {path} with data: {data}")
                    
                    if path in server_instance.router:
                        server_instance.router[path](self, data)
                    else:
                        self._send_json_response({
                            "success": False, 
                            "error": f"Unknown POST endpoint: {path}",
                            "available_endpoints": list(server_instance.router.keys())
                        }, 404)
                        
                except Exception as e:
                    logger.error(f"POST error: {e}")
                    self._send_json_response({
                        "success": False, 
                        "error": str(e)
                    }, 500)
        
        return WorkingPortalHandler

    def _handle_register_developer(self, handler, data):
        """Handle developer registration"""
        try:
            # Support multiple field names for compatibility
            developer = (data.get('developer') or 
                        data.get('developer_name') or 
                        data.get('username') or '')
            
            pythoncoin_address = (data.get('pythoncoin_address') or 
                                data.get('wallet_address') or 
                                data.get('address') or 
                                data.get('developer_address') or '')
            
            email = data.get('email', '')
            
            logger.info(f"Registration attempt: {developer} -> {pythoncoin_address}")
            
            # Validation
            if not developer:
                return handler._send_json_response({
                    'success': False, 
                    'error': 'Missing developer name'
                })
            
            if not pythoncoin_address:
                return handler._send_json_response({
                    'success': False, 
                    'error': 'Missing PythonCoin address'
                })
            
            # Store registration
            self.registered_developers[developer] = pythoncoin_address
            
            # Try to save to database if available
            if self.db_manager and hasattr(self.db_manager, 'add_developer'):
                try:
                    self.db_manager.add_developer(developer, pythoncoin_address, email)
                    logger.info("Developer saved to database")
                except Exception as db_error:
                    logger.warning(f"Database save failed: {db_error}")
            
            logger.info(f"✅ Developer registered: {developer}")
            
            return handler._send_json_response({
                'success': True,
                'message': 'Developer registered successfully',
                'developer': developer,
                'wallet_address': pythoncoin_address
            })
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return handler._send_json_response({
                'success': False, 
                'error': str(e)
            })

    def _handle_get_ads(self, handler, query_params):
        """Handle requests for advertisements"""
        try:
            # Get sample ads for now
            ads = self._get_sample_ads()
            
            logger.info(f"Serving {len(ads)} ads")
            return handler._send_json_response({
                "success": True, 
                "ads": ads,
                "total": len(ads)
            })
            
        except Exception as e:
            logger.error(f"Get ads error: {e}")
            return handler._send_json_response({
                "success": False, 
                "error": str(e)
            })

    def _handle_ad_click(self, handler, data):
        """Handle ad click recording"""
        try:
            ad_id = data.get('ad_id', '')
            developer = data.get('developer', '')
            payout_amount = float(data.get('payout_amount', 0.001))
            
            logger.info(f"Ad click: {ad_id} by {developer} for {payout_amount} PYC")
            
            # In a real implementation, this would process the payment
            return handler._send_json_response({
                'success': True,
                'message': 'Click recorded',
                'payout': payout_amount
            })
            
        except Exception as e:
            logger.error(f"Click recording error: {e}")
            return handler._send_json_response({
                'success': False, 
                'error': str(e)
            })

    def _handle_client_info(self, handler, query_params):
        """Provide client information"""
        try:
            info = {
                "success": True,
                "client_id": "pyqt_client_001",
                "name": "PythonCoin Wallet Client",
                "version": "2.0.0",
                "status": "online",
                "host": self.host,
                "port": self.port,
                "wallet_address": self.wallet.address if self.wallet else '',
                "ad_count": len(self._get_sample_ads()),
                "registered_developers": len(self.registered_developers)
            }
            
            return handler._send_json_response(info)
            
        except Exception as e:
            logger.error(f"Client info error: {e}")
            return handler._send_json_response({
                "success": False, 
                "error": str(e)
            })

    def _handle_status_info(self, handler, query_params):
        """Provide server status"""
        try:
            status = {
                "success": True,
                "server_status": "online",
                "running": self.running,
                "message": "Portal server is operational"
            }
            
            return handler._send_json_response(status)
            
        except Exception as e:
            logger.error(f"Status info error: {e}")
            return handler._send_json_response({
                "success": False, 
                "error": str(e)
            })

    def _get_sample_ads(self):
        """Get real advertisements from storage and network"""
        try:
            if hasattr(self, 'wallet_instance') and self.wallet_instance:
                if hasattr(self.wallet_instance, 'ad_fetcher'):
                    real_ads = self.wallet_instance.ad_fetcher.get_real_ads(limit=10)
                    
                    formatted_ads = []
                    for ad in real_ads:
                        formatted_ad = {
                            "id": ad['id'],
                            "client_id": ad.get('peer_source', 'local'),
                            "title": ad['title'],
                            "description": ad['description'],
                            "category": ad['category'],
                            "payout": ad['payout_rate'],
                            "svg_url": f"http://{self.host}:{self.port}/svg/{ad['id']}",
                            "target_url": ad['click_url']
                        }
                        formatted_ads.append(formatted_ad)
                    
                    if formatted_ads:
                        return formatted_ads
            
            return [
                {
                    "id": "demo_crypto_001",
                    "client_id": "demo_client",
                    "title": "Learn Cryptocurrency Basics",
                    "description": "Educational content about blockchain and cryptocurrency technology.",
                    "category": "education",
                    "payout": 0.001,
                    "svg_url": f"http://{self.host}:{self.port}/svg/demo_crypto_001",
                    "target_url": "https://example.com/learn-crypto"
                }
            ]
            
        except Exception as e:
            print(f"Error getting real ads: {e}")
            return []
class RobustPythonCoinHandler(BaseHTTPRequestHandler):
    """HTTP request handler for PythonCoin server with robust error handling"""
    
    def __init__(self, *args, **kwargs):
        self.server_instance = kwargs.pop('server_instance', None)
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Custom logging to avoid spam"""
        pass
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        try:
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
        except Exception as e:
            if self.server_instance:
                self.server_instance.status_update.emit(f"OPTIONS error: {str(e)}")
    
    def send_cors_headers(self):
        """Send CORS headers"""
        try:
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
            self.send_header('Connection', 'close')
        except Exception:
            pass
    
    def do_GET(self):
        """Handle GET requests with robust error handling"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            self.send_response(200)
            self.send_cors_headers()
            
            if path == '/' or path == '/test':
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {
                    'success': True,
                    'status': 'PythonCoin Portal Server Active',
                    'port': self.server_instance.actual_port,
                    'wallet': self.server_instance.wallet.address[:8] + '...' if self.server_instance.wallet else 'None',
                    'blockchain_height': len(self.server_instance.blockchain.chain) if self.server_instance.blockchain else 0,
                    'server_time': datetime.now().isoformat(),
                    'message': 'Server is running and accepting connections'
                }
                self.wfile.write(json.dumps(response).encode())
                
            elif path == '/client_info':
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = self.server_instance.handle_client_info()
                self.wfile.write(response.encode())
                
            elif path == '/portal':
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                html_content = self.server_instance.generate_portal_html()
                self.wfile.write(html_content.encode())
                
            elif path == '/stats':
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = self.server_instance.handle_stats()
                self.wfile.write(response.encode())
                
            elif path == '/ads':
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = self.server_instance.handle_get_ads()
                self.wfile.write(response.encode())
                
            elif path.endswith('.svg'):
                self.send_header('Content-Type', 'image/svg+xml')
                self.send_header('Cache-Control', 'public, max-age=3600')
                # Add CSP-friendly headers for SVG
                self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' data: blob:; media-src 'self' data: blob:;")
                self.end_headers()
                
                # Serve SVG file if it exists
                svg_file_path = self.server_instance.get_svg_file_path(path)
                if svg_file_path and os.path.exists(svg_file_path):
                    with open(svg_file_path, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    # Generate a default SVG
                    default_svg = self.server_instance.generate_default_svg()
                    self.wfile.write(default_svg.encode())
                    
            elif path == '/debug_ads':
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                
                # Get ads data
                ads_response = self.server_instance.handle_get_ads()
                
                debug_html = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>PythonCoin Ads Debug</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .ad-item {{ border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 8px; }}
                    .json-data {{ background: #f5f5f5; padding: 10px; font-family: monospace; white-space: pre-wrap; }}
                </style>
            </head>
            <body>
                <h1>PythonCoin Ads Debug</h1>
                <h2>Raw Ads Data:</h2>
                <div class="json-data">{ads_response}</div>
                
                <h2>Test Links:</h2>
                <ul>
                    <li><a href="/ads">Get Ads JSON</a></li>
                    <li><a href="/client_info">Client Info</a></li>
                    <li><a href="/stats">Server Stats</a></li>
                    <li><a href="/portal">Developer Portal</a></li>
                </ul>
                
                <script>
                    // Test the ads endpoint
                    fetch('/ads')
                        .then(response => response.json())
                        .then(data => {{
                            console.log('Ads data:', data);
                            if (data.success) {{
                                document.body.innerHTML += '<h2>✅ Ads endpoint working!</h2>';
                                document.body.innerHTML += '<p>Found ' + data.total + ' ads</p>';
                            }} else {{
                                document.body.innerHTML += '<h2>❌ Ads endpoint failed</h2>';
                                document.body.innerHTML += '<p>Error: ' + data.error + '</p>';
                            }}
                        }})
                        .catch(error => {{
                            console.error('Error:', error);
                            document.body.innerHTML += '<h2>❌ Network error</h2>';
                        }});
                </script>
            </body>
            </html>"""
                
                self.wfile.write(debug_html.encode())
                
            else:
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                default_response = json.dumps({
                    'status': 'unknown_endpoint',
                    'available_endpoints': ['/test', '/client_info', '/portal', '/stats', '/ads', '/debug_ads'],
                    'requested_path': path
                })
                self.wfile.write(default_response.encode())
                
        except Exception as e:
            try:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps({'success': False, 'error': str(e)})
                self.wfile.write(error_response.encode())
            except:
                pass
    
    def _parse_request_body(self):
        """Parses the request body based on Content-Type header."""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length).decode('utf-8')
            content_type = self.headers.get('Content-Type', '').lower()
            logger.debug(f"Raw request body received: {body[:200]}...")
            logger.debug(f"Content-Type received: {content_type}")

            if 'application/json' in content_type:
                try:
                    parsed_data = json.loads(body)
                    logger.debug(f"Parsed JSON data: {parsed_data}")
                    return parsed_data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON Decode Error: {e}, Body snippet: {body[:200]}...", exc_info=True)
                    return {}
            elif 'application/x-www-form-urlencoded' in content_type:
                from urllib.parse import parse_qs
                parsed_data = parse_qs(body)
                # parse_qs returns lists for each value, convert to scalar for single values
                converted_data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed_data.items()}
                logger.debug(f"Parsed form-urlencoded data: {converted_data}")
                return converted_data
            else:
                logger.warning(f"Unsupported Content-Type: {content_type}. Body snippet: {body[:200]}...")
                return {}
        logger.debug("Empty request body.")
        return {}
    
    def do_POST(self):
        """Handle POST requests with enhanced debugging"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            
            # Log the incoming request for debugging
            path = urllib.parse.urlparse(self.path).path
            logger.debug(f"POST request to: {path}")
            logger.debug(f"Content-Length: {content_length}")
            logger.debug(f"Raw data: {post_data}")
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                logger.debug(f"Parsed JSON: {data}")
            except Exception as json_error:
                logger.debug(f"JSON parse error: {json_error}")
                data = {}
            
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Route POST requests to appropriate handlers
            if path == '/register_developer':
                logger.debug("Handling register_developer request")
                response = self.server_instance.handle_register_developer(data)
                logger.debug(f"Response: {response}")
            elif path == '/click':
                response = self.server_instance.handle_click(data)
            elif path == '/enhanced_click':
                response = self.server_instance.handle_enhanced_ad_click(data)
            elif path == '/test_enhanced':
                test_response = {
                    'success': True,
                    'message': 'Enhanced endpoints are working',
                    'enhanced_features': True,
                    'endpoints': ['/register_developer', '/enhanced_click', '/test_enhanced'],
                    'server_time': datetime.now().isoformat(),
                    'request_data': data
                }
                response = json.dumps(test_response)
            elif path == '/advertise_client':
                response = self.server_instance.handle_advertise_client(data)
            elif path == '/select_client':
                response = self.server_instance.handle_select_client(data)
            elif path == '/generate_custom_js':
                response = self.server_instance.handle_generate_custom_js(data)
            elif path == '/impression':
                response = self.server_instance.handle_impression(data)
            elif path == '/notify_ad_created':
                response = self.server_instance.handle_notify_ad_created(data)
            else:
                logger.debug(f"Unknown POST endpoint: {path}")
                response = json.dumps({
                    'success': False, 
                    'error': f'Unknown endpoint: {path}',
                    'available_endpoints': [
                        '/register_developer',
                        '/click', 
                        '/enhanced_click',
                        '/test_enhanced',
                        '/advertise_client',
                        '/select_client',
                        '/generate_custom_js',
                        '/impression',
                        '/notify_ad_created'
                    ]
                })
            
            self.wfile.write(response.encode())
            
        except Exception as e:
            logger.error(f"POST handler error: {str(e)}", exc_info=True)
            
            try:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps({
                    'success': False, 
                    'error': str(e),
                    'debug': 'POST handler exception'
                })
                self.wfile.write(error_response.encode())
            except:
                pass

    
    def quick_server_test(self):
        """Quick test of server after creation"""
        try:
            time.sleep(0.2)  # Brief delay
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                test_socket.settimeout(2)
                result = test_socket.connect_ex(('127.0.0.1', self.actual_port))
                if result == 0:
                    self.status_update.emit(f"✅ Server connectivity test passed on port {self.actual_port}")
                else:
                    self.status_update.emit(f"⚠️ Server connectivity test failed: error code {result}")
                    
        except Exception as e:
            self.status_update.emit(f"⚠️ Server connectivity test error: {str(e)}")
    
    def handle_client_info(self):
        """Handle client info requests"""
        try:
            client_info = {
                'success': True,
                'client_id': f'pyc_{self.wallet.address[:8]}' if self.wallet else 'pyc_unknown',
                'name': f'PythonCoin Wallet - {self.wallet.address[:8]}...' if self.wallet else 'PythonCoin Wallet',
                'status': 'online',
                'host': '127.0.0.1',
                'port': self.actual_port,
                'wallet_address': self.wallet.address if self.wallet else '',
                'server_version': '2.1.0',
                'blockchain_height': len(self.blockchain.chain) if self.blockchain else 0,
                'last_updated': datetime.now().isoformat(),
                'server_started': self.server_started
            }
            
            return json.dumps(client_info)
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_stats(self):
        """Handle stats requests"""
        try:
            stats = {
                'success': True,
                'server_port': self.actual_port,
                'server_status': 'online' if self.running and self.server_started else 'offline',
                'wallet_address': self.wallet.address if self.wallet else '',
                'blockchain_height': len(self.blockchain.chain) if self.blockchain else 0,
                'ads_served': self.ads_served,
                'registered_developers': len(self.registered_developers),
                'total_clicks': len(self.click_payments),
                'last_updated': datetime.now().isoformat()
            }
            
            return json.dumps(stats)
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_click(self, data):
        """Enhanced ad click handling with developer tracking"""
        try:
            ad_id = data.get('ad_id', '')
            developer = data.get('developer', '')
            pythoncoin_address = data.get('pythoncoin_address', '')
            payout_amount = float(data.get('payout_amount', 0.001))
            zone = data.get('zone', 'unknown')
            
            if not all([ad_id, developer, pythoncoin_address]):
                return json.dumps({'success': False, 'error': 'Missing required fields'})
            
            if hasattr(self, 'wallet_instance') and self.wallet_instance:
                if hasattr(self.wallet_instance, 'dev_registration'):
                    self.wallet_instance.dev_registration.update_developer_activity(developer)
                    self.wallet_instance.dev_registration.record_developer_click(developer, payout_amount)
                
                if hasattr(self.wallet_instance, 'on_enhanced_portal_click_received'):
                    click_data_enhanced = {
                        'developer': developer,
                        'amount': payout_amount,
                        'ad_id': ad_id,
                        'pythoncoin_address': pythoncoin_address,
                        'zone': zone,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.wallet_instance.on_enhanced_portal_click_received(click_data_enhanced)
            
            return json.dumps({
                'success': True,
                'payment_processing': True,
                'amount': payout_amount,
                'message': 'Click processed with enhanced tracking',
                'enhanced': True
            })
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e), 'enhanced': True})
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_register_developer(self, data):
        """Enhanced developer registration with session tracking"""
        try:
            developer = (data.get('developer') or 
                        data.get('developer_name') or 
                        data.get('username') or '')
            
            pythoncoin_address = (data.get('pythoncoin_address') or 
                                data.get('wallet_address') or 
                                data.get('address') or 
                                data.get('developer_address') or '')
            
            email = data.get('email', '')
            
            logger.info(f"[ENHANCED] Registration: {developer} -> {pythoncoin_address}")
            
            if not developer:
                return json.dumps({'success': False, 'error': 'Missing developer name'})
            
            if not pythoncoin_address:
                return json.dumps({'success': False, 'error': 'Missing PythonCoin address'})
            
            self.registered_developers[developer] = pythoncoin_address
            
            session_info = {
                'ip_address': getattr(self, 'client_ip', 'unknown'),
                'user_agent': data.get('user_agent', ''),
                'registration_time': datetime.now().isoformat(),
                'email': email
            }
            
            if hasattr(self, 'wallet_instance') and self.wallet_instance:
                if hasattr(self.wallet_instance, 'dev_registration'):
                    self.wallet_instance.dev_registration.register_developer(
                        developer, pythoncoin_address, session_info
                    )
                
                if hasattr(self.wallet_instance, 'on_enhanced_developer_registered'):
                    self.wallet_instance.on_enhanced_developer_registered(
                        developer, pythoncoin_address, session_info
                    )
            
            if hasattr(self, 'db_manager') and self.db_manager:
                try:
                    self.db_manager.add_developer(developer, pythoncoin_address, email)
                except Exception as db_error:
                    logger.warning(f"Database save failed: {db_error}")
            
            logger.info(f"✅ Enhanced developer registered: {developer}")
            
            return json.dumps({
                'success': True,
                'message': 'Developer registered successfully',
                'developer': developer,
                'wallet_address': pythoncoin_address,
                'enhanced': True,
                'session_tracked': True
            })
            
        except Exception as e:
            logger.error(f"Enhanced registration error: {e}")
            return json.dumps({'success': False, 'error': str(e), 'enhanced': True})
            
            if not pythoncoin_address:
                return json.dumps({'success': False, 'error': 'Missing PythonCoin wallet address'})
            
            # Validate address format
            if len(pythoncoin_address) < 26 or len(pythoncoin_address) > 35:
                return json.dumps({'success': False, 'error': 'Invalid PythonCoin address format'})
            
            # Store in original format for compatibility
            if not hasattr(self, 'registered_developers'):
                self.registered_developers = {}
            
            self.registered_developers[developer] = pythoncoin_address
            
            # Enhanced database storage
            if hasattr(self, 'enhanced_db_manager') and self.enhanced_db_manager:
                try:
                    self.enhanced_db_manager.add_developer(developer, pythoncoin_address, email)
                    logger.info(f"[ENHANCED_REGISTER] Saved to enhanced database")
                except Exception as db_error:
                    logger.error(f"[ENHANCED_REGISTER] Database error: {db_error}")
            elif hasattr(self, 'db_manager') and self.db_manager:
                try:
                    # Try with existing db_manager
                    if hasattr(self.db_manager, 'add_developer'):
                        self.db_manager.add_developer(developer, pythoncoin_address, email)
                    logger.info(f"[ENHANCED_REGISTER] Saved to existing database")
                except Exception as db_error:
                    logger.error(f"[ENHANCED_REGISTER] Existing DB error: {db_error}")
            
            # Emit signal if available
            if hasattr(self, 'developer_registered'):
                try:
                    self.developer_registered.emit(developer, pythoncoin_address)
                    logger.info(f"[ENHANCED_REGISTER] Signal emitted")
                except Exception as signal_error:
                    logger.error(f"[ENHANCED_REGISTER] Signal error: {signal_error}")
            
            logger.info(f"[ENHANCED_REGISTER] ✅ Success: {developer} registered")
            
            return json.dumps({
                'success': True,
                'message': 'Developer registered successfully',
                'developer': developer,
                'wallet_address': pythoncoin_address,
                'enhanced_features': True,
                'server_info': {
                    'server_port': getattr(self, 'actual_port', getattr(self, 'port', 8082)),
                    'enhanced_db': hasattr(self, 'enhanced_db_manager'),
                    'timestamp': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            error_msg = f"Enhanced registration error: {str(e)}"
            logger.error(f"[ENHANCED_REGISTER] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
            return json.dumps({
                'success': False, 
                'error': error_msg,
                'enhanced_features': True
            })
    
    def generate_portal_html(self):
        """Generate portal HTML page"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>PythonCoin Developer Portal</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        h1 {{ color: #0066cc; }}
        .status {{ padding: 15px; background: #d4edda; border-radius: 8px; margin: 20px 0; }}
        .info {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        button {{ background: #0066cc; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; margin: 5px; }}
        button:hover {{ background: #0056b3; }}
        .result {{ margin: 20px 0; padding: 15px; border-radius: 8px; }}
        .success {{ background: #d4edda; border: 1px solid #c3e6cb; }}
        .error {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 PythonCoin Developer Portal</h1>
        
        <div class="status">
            ✅ Server is running successfully on port {self.actual_port}
        </div>
        
        <div class="info">
            <h3>📊 Server Information</h3>
            <p><strong>Status:</strong> Online and accepting connections</p>
            <p><strong>Port:</strong> {self.actual_port}</p>
            <p><strong>Wallet:</strong> {self.wallet.address[:16] + '...' if self.wallet else 'None'}</p>
            <p><strong>Blockchain Height:</strong> {len(self.blockchain.chain) if self.blockchain else 0}</p>
            <p><strong>Ads Served:</strong> {self.ads_served}</p>
            <p><strong>Registered Developers:</strong> {len(self.registered_developers)}</p>
            <p><strong>Server Started:</strong> {self.server_started}</p>
        </div>
        
        <div class="info">
            <h3>🔗 API Endpoints</h3>
            <ul>
                <li><code>GET /test</code> - Test server connection</li>
                <li><code>GET /client_info</code> - Get client information</li>
                <li><code>GET /stats</code> - Get server statistics</li>
                <li><code>GET /portal</code> - This portal page</li>
                <li><code>POST /click</code> - Record ad click</li>
                <li><code>POST /register_developer</code> - Register developer</li>
            </ul>
        </div>
        
        <div>
            <button onclick="testConnection()">🔍 Test Connection</button>
            <button onclick="getStats()">📊 Get Statistics</button>
            <button onclick="getClientInfo()">📋 Client Info</button>
        </div>
        
        <div id="result"></div>
        
        <script>
            function showResult(content, isSuccess = true) {{
                const resultDiv = document.getElementById('result');
                resultDiv.className = 'result ' + (isSuccess ? 'success' : 'error');
                resultDiv.innerHTML = content;
            }}
            
            function testConnection() {{
                fetch('/test')
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            showResult('✅ Connection test successful!<br>' + 
                                     'Server: ' + data.status + '<br>' +
                                     'Time: ' + data.server_time);
                        }} else {{
                            showResult('❌ Connection test failed: ' + (data.error || 'Unknown error'), false);
                        }}
                    }})
                    .catch(error => {{
                        showResult('❌ Connection failed: ' + error, false);
                    }});
            }}
            
            function getStats() {{
                fetch('/stats')
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            showResult('<h4>📊 Current Statistics:</h4><pre>' + 
                                     JSON.stringify(data, null, 2) + '</pre>');
                        }} else {{
                            showResult('❌ Stats request failed: ' + (data.error || 'Unknown error'), false);
                        }}
                    }})
                    .catch(error => {{
                        showResult('❌ Stats request failed: ' + error, false);
                    }});
            }}
            
            function getClientInfo() {{
                fetch('/client_info')
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            showResult('<h4>📋 Client Information:</h4><pre>' + 
                                     JSON.stringify(data, null, 2) + '</pre>');
                        }} else {{
                            showResult('❌ Client info request failed: ' + (data.error || 'Unknown error'), false);
                        }}
                    }})
                    .catch(error => {{
                        showResult('❌ Client info request failed: ' + error, false);
                    }});
            }}
            
            // Test connection on page load
            window.onload = function() {{
                testConnection();
            }};
        </script>
    </div>
</body>
</html>"""
    
    
    def get_svg_file_path(self, path):
        """Get the file path for SVG files"""
        try:
            # Remove leading slash and get filename
            filename = path.lstrip('/')
            
            # Check in ads storage directory
            if hasattr(self, 'wallet_instance') and self.wallet_instance:
                storage_base = getattr(self.wallet_instance, 'ad_storage', None)
                if storage_base and hasattr(storage_base, 'base_dir'):
                    svg_path = storage_base.base_dir / "active" / filename
                    if svg_path.exists():
                        return str(svg_path)
            
            # Check in current directory
            local_path = os.path.join(os.getcwd(), filename)
            if os.path.exists(local_path):
                return local_path
                
            return None
            
        except Exception as e:
            print(f"Error getting SVG path: {e}")
            return None

    def generate_default_svg(self):
        """Generate a default SVG when file not found"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
    <rect width="400" height="300" fill="#f0f9ff" stroke="#0066cc" stroke-width="2"/>
    <text x="200" y="150" text-anchor="middle" font-family="Arial" font-size="16" fill="#0066cc">
        PythonCoin Ad
    </text>
    <text x="200" y="180" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">
        Loading...
    </text>
</svg>"""

    def stop(self):
        """Stop the server"""
        try:
            self.running = False
            self.server_started = False
            
            if self.httpd:
                try:
                    self.httpd.shutdown()
                    self.httpd.server_close()
                except:
                    pass
                self.httpd = None
            
            self.status_update.emit("🛑 Portal server stopped cleanly")
            
        except Exception as e:
            self.status_update.emit(f"Error stopping server: {str(e)}")

class EnhancedPythonCoinHandler(BaseHTTPRequestHandler):
        
    def log_message(self, format, *args):
            
        pass
                
    def do_OPTIONS(self):
                    """Handle CORS preflight requests"""
                    self.send_response(200)
                    self.send_cors_headers()
                    self.end_headers()
                
    def send_cors_headers(self):
        """Send enhanced CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, X-Developer-Address, X-Zone')
        self.send_header('Access-Control-Max-Age', '86400')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        # Add these critical headers
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Vary', 'Origin')
    # In your PyQt P2P client HTTP server
    def add_cors_headers(self, response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Developer-Address, X-Zone'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response
                
    # Add this to the do_GET method in EnhancedPythonCoinHandler class
# Find the do_GET method around line 600-800 and add this case:
    def handle_get_ads(self):
        """Get available ads in the format expected by JavaScript"""
        try:
            # Get ads from the wallet instance
            if hasattr(self, 'wallet_instance') and self.wallet_instance:
                ads_list = getattr(self.wallet_instance, 'ads', [])
            else:
                ads_list = self.get_available_ads()  # Fallback method
            
            # Format ads for JavaScript consumption
            formatted_ads = []
            for ad in ads_list:
                # Handle both AdContent objects and dictionaries
                if hasattr(ad, 'to_dict'):
                    ad_dict = ad.to_dict()
                elif hasattr(ad, '__dict__'):
                    ad_dict = ad.__dict__
                else:
                    ad_dict = ad
                
                formatted_ad = {
                    'id': ad_dict.get('id', ''),
                    'title': ad_dict.get('title', 'Untitled Ad'),
                    'description': ad_dict.get('description', 'No description'),
                    'category': ad_dict.get('category', 'general'),
                    'payout_rate': float(ad_dict.get('payout_rate', 0.001)),
                    'click_url': ad_dict.get('click_url', '#'),
                    'image_url': ad_dict.get('image_url', ''),
                    'advertiser_address': ad_dict.get('advertiser_address', ''),
                    'created_at': ad_dict.get('created_at', ''),
                    'expires_at': ad_dict.get('expires_at', ''),
                    'targeting': ad_dict.get('targeting', {}),
                    'peer_source': ad_dict.get('peer_source', 'local')
                }
                formatted_ads.append(formatted_ad)
            
            response_data = {
                'success': True,
                'ads': formatted_ads,
                'total': len(formatted_ads),
                'server_time': datetime.now().isoformat(),
                'server_info': {
                    'client_id': getattr(self, 'client_id', 'unknown'),
                    'port': getattr(self, 'port', 8082),
                    'wallet_address': self.wallet.address if self.wallet else ''
                }
            }
            
            return json.dumps(response_data)
            
        except Exception as e:
            error_response = {
                'success': False,
                'error': str(e),
                'ads': [],
                'total': 0
            }
            return json.dumps(error_response)
    def do_GET(self):
        """Handle GET requests with enhanced routing"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            query = urllib.parse.parse_qs(parsed_path.query)
            
            self.send_response(200)
            self.send_cors_headers()
            
            # Route handling
            if path == '/client_info':
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = self.server_instance.handle_client_info()
                self.wfile.write(response.encode())
                
            elif path == '/discover_clients':
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = self.server_instance.handle_discover_clients()
                self.wfile.write(response.encode())
                
            elif path == '/active_clients':
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = self.server_instance.handle_get_active_clients()
                self.wfile.write(response.encode())
                
            # Ads endpoint handler
            elif path == '/ads':
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = self.server_instance.handle_get_ads()
                self.wfile.write(response.encode())
                
            elif path.startswith('/custom_') and path.endswith('.js'):
                self.send_header('Content-Type', 'application/javascript')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                js_content = self.server_instance.handle_custom_js(path)
                self.wfile.write(js_content.encode())
                
            elif path.startswith('/verify_js/'):
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = self.server_instance.handle_verify_js(path)
                self.wfile.write(response.encode())
                
            elif path == '/notifications':
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = self.server_instance.handle_get_notifications()
                self.wfile.write(response.encode())
                
            elif path == '/stats':
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = self.server_instance.handle_stats()
                self.wfile.write(response.encode())
                    
            elif path == '/portal':
                # Serve the developer portal HTML
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                html_content = self.server_instance.generate_developer_portal_html()
                self.wfile.write(html_content.encode())
                
            elif path == '/test_ads':
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                test_response = {
                    'success': True,
                    'message': 'Ads endpoint test',
                    'available_ads': len(self.server_instance.get_available_ads()),
                    'endpoints_working': ['/ads', '/client_info', '/stats', '/portal']
                }
                self.wfile.write(json.dumps(test_response).encode())
                
            elif path.endswith('.svg'):
                self.send_header('Content-Type', 'image/svg+xml')
                self.send_header('Cache-Control', 'public, max-age=3600')
                # Add CSP-friendly headers for SVG
                self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' data: blob:; media-src 'self' data: blob:;")
                self.end_headers()
                
                # Serve SVG file if it exists
                svg_file_path = self.server_instance.get_svg_file_path(path)
                if svg_file_path and os.path.exists(svg_file_path):
                    with open(svg_file_path, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    # Generate a default SVG
                    default_svg = self.server_instance.generate_default_svg()
                    self.wfile.write(default_svg.encode())
                    
            elif path == '/debug_ads':
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                
                # Get ads data
                ads_response = self.server_instance.handle_get_ads()
                
                debug_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <title>PythonCoin Ads Debug</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .ad-item {{ border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 8px; }}
            .json-data {{ background: #f5f5f5; padding: 10px; font-family: monospace; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <h1>PythonCoin Ads Debug</h1>
        <h2>Raw Ads Data:</h2>
        <div class="json-data">{ads_response}</div>
        
        <h2>Test Links:</h2>
        <ul>
            <li><a href="/ads">Get Ads JSON</a></li>
            <li><a href="/client_info">Client Info</a></li>
            <li><a href="/stats">Server Stats</a></li>
            <li><a href="/portal">Developer Portal</a></li>
        </ul>
        
        <script>
            // Test the ads endpoint
            fetch('/ads')
                .then(response => response.json())
                .then(data => {{
                    console.log('Ads data:', data);
                    if (data.success) {{
                        document.body.innerHTML += '<h2>✅ Ads endpoint working!</h2>';
                        document.body.innerHTML += '<p>Found ' + data.total + ' ads</p>';
                    }} else {{
                        document.body.innerHTML += '<h2>❌ Ads endpoint failed</h2>';
                        document.body.innerHTML += '<p>Error: ' + data.error + '</p>';
                    }}
                }})
                .catch(error => {{
                    console.error('Error:', error);
                    document.body.innerHTML += '<h2>❌ Network error</h2>';
                }});
        </script>
    </body>
    </html>"""
                
                self.wfile.write(debug_html.encode())
                
            else:
                # Default handler for unmatched routes
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                status_response = json.dumps({
                    'status': 'PythonCoin Wallet Server Active',
                    'port': self.server_instance.port,
                    'endpoints': [
                        '/client_info', '/discover_clients', '/active_clients',
                        '/ads',
                        '/custom_ADDRESS.js', '/verify_js/FILENAME',
                        '/notifications', '/stats', '/portal', '/debug_ads'
                    ]
                })
                self.wfile.write(status_response.encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({'success': False, 'error': str(e)})
            self.wfile.write(error_response.encode())
                
    def do_POST(self):
        """Handle POST requests with enhanced debugging"""
        try:
            # Use the enhanced request body parsing
            data = self._parse_request_body()
            
            # Log the incoming request for debugging
            path = urllib.parse.urlparse(self.path).path
            logger.info(f"[DEBUG] POST request to: {path}")
            logger.debug(f"[DEBUG] Parsed data: {data}")
            
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Enhanced routing with debugging
            if path == '/register_developer':
                logger.info(f"[DEBUG] Handling register_developer request")
                response = self.server_instance.handle_register_developer(data)
                logger.debug(f"[DEBUG] Response: {response}")
            elif path == '/click':
                response = self.server_instance.handle_click(data)
            elif path == '/advertise_client':
                response = self.server_instance.handle_advertise_client(data)
            elif path == '/select_client':
                response = self.server_instance.handle_select_client(data)
            elif path == '/generate_custom_js':
                response = self.server_instance.handle_generate_custom_js(data)
            elif path == '/impression':
                response = self.server_instance.handle_impression(data)
            elif path == '/notify_ad_created':
                response = self.server_instance.handle_notify_ad_created(data)
            else:
                logger.warning(f"[DEBUG] Unknown POST endpoint: {path}")
                response = json.dumps({
                    'success': False, 
                    'error': f'Unknown endpoint: {path}',
                    'available_endpoints': [
                        '/register_developer',
                        '/click', 
                        '/advertise_client',
                        '/select_client',
                        '/generate_custom_js',
                        '/impression',
                        '/notify_ad_created'
                    ]
                })
            
            self.wfile.write(response.encode())
            
        except Exception as e:
            logger.error(f"[DEBUG] POST handler error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            try:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps({
                    'success': False, 
                    'error': str(e),
                    'debug': 'POST handler exception'
                })
                self.wfile.write(error_response.encode())
            except:
                pass
                
            # Use ThreadingHTTPServer for better performance
    def handler(*args, **kwargs):
                return EnhancedPythonCoinHandler(*args, server_instance=self, **kwargs)

#!/usr/bin/env python3
"""
Enhanced Ad Click Payment Processor Injection Script
Fixes MySQL connection issues and implements auto-payment for unprocessed ad clicks
"""

import sys
import json
import time
import uuid
import threading
import mysql.connector
from datetime import datetime, timedelta
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                           QPushButton, QCheckBox, QLabel, QMessageBox, QHeaderView,
                           QGroupBox, QFormLayout, QDoubleSpinBox, QSpinBox, QProgressBar)
from PyQt5.QtGui import QColor, QFont

class EnhancedAdClickProcessor(QThread):
    """Enhanced processor for unprocessed ad clicks with auto-payment"""
    
    # Signals for UI updates
    new_click_detected = pyqtSignal(dict)
    payment_completed = pyqtSignal(str, float, str)  # click_id, amount, developer_address
    payment_failed = pyqtSignal(str, str)  # click_id, error_message
    status_update = pyqtSignal(str)
    
    def __init__(self, wallet_instance):
        super().__init__()
        self.wallet_instance = wallet_instance
        self.running = False
        self.auto_payment_enabled = False
        self.auto_payment_limit = 0.1  # Max auto-payment amount
        self.check_interval = 5  # Check every 5 seconds
        self.processed_clicks = set()  # Track processed clicks to avoid duplicates
        
        # Database connection
        self.db_connection = None
        self.setup_database_connection()
        
    def setup_database_connection(self):
        """Setup enhanced database connection with retry logic"""
        try:
            db_config = {
                'host': 'localhost',
                'database': 'adnetwrk',
                'user': 'root',
                'password': '',
                'autocommit': True,
                'charset': 'utf8mb4',
                'connection_timeout': 10,
                'autocommit': True
            }
            
            self.db_connection = mysql.connector.connect(**db_config)
            
            # Ensure required tables exist
            self.ensure_tables_exist()
            
            self.status_update.emit("✅ Enhanced database connection established")
            return True
            
        except Exception as e:
            self.status_update.emit(f"❌ Database connection failed: {str(e)}")
            return False
    
    def ensure_tables_exist(self):
        """Ensure all required tables exist with proper structure"""
        try:
            cursor = self.db_connection.cursor()
            
            # Enhanced ad_clicks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ad_clicks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ad_id VARCHAR(100) NOT NULL,
                    client_id VARCHAR(100),
                    developer_address VARCHAR(100) NOT NULL,
                    developer_name VARCHAR(100),
                    zone VARCHAR(100) DEFAULT 'default',
                    payout_amount DECIMAL(16,8) NOT NULL DEFAULT 0.00100000,
                    click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    processed TINYINT(1) DEFAULT 0,
                    processed_time TIMESTAMP NULL,
                    transaction_id VARCHAR(100),
                    payment_status VARCHAR(20) DEFAULT 'pending',
                    error_message TEXT,
                    retry_count INT DEFAULT 0,
                    INDEX idx_processed (processed),
                    INDEX idx_click_time (click_time),
                    INDEX idx_developer (developer_address),
                    INDEX idx_payment_status (payment_status)
                )
            """)
            
            # Payment queue table for batch processing
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_queue (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    click_id INT NOT NULL,
                    developer_address VARCHAR(100) NOT NULL,
                    amount DECIMAL(16,8) NOT NULL,
                    status VARCHAR(20) DEFAULT 'queued',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP NULL,
                    transaction_id VARCHAR(100),
                    error_message TEXT,
                    FOREIGN KEY (click_id) REFERENCES ad_clicks(id),
                    INDEX idx_status (status),
                    INDEX idx_created (created_at)
                )
            """)
            
            # Developer payment history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS developer_payments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    developer_address VARCHAR(100) NOT NULL,
                    developer_name VARCHAR(100),
                    total_clicks INT DEFAULT 0,
                    total_earnings DECIMAL(16,8) DEFAULT 0.00000000,
                    last_payment TIMESTAMP NULL,
                    last_click TIMESTAMP NULL,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_developer (developer_address),
                    INDEX idx_developer (developer_address),
                    INDEX idx_last_payment (last_payment)
                )
            """)
            
            cursor.close()
            self.status_update.emit("✅ Database tables verified/created")
            
        except Exception as e:
            self.status_update.emit(f"❌ Table creation error: {str(e)}")
    
    def run(self):
        """Main processing loop"""
        self.running = True
        self.status_update.emit("🔄 Ad click processor started")
        
        while self.running:
            try:
                # Check for unprocessed clicks
                unprocessed_clicks = self.fetch_unprocessed_clicks()
                
                if unprocessed_clicks:
                    self.status_update.emit(f"📨 Found {len(unprocessed_clicks)} unprocessed clicks")
                    
                    for click in unprocessed_clicks:
                        if not self.running:
                            break
                        
                        # Emit signal for UI update
                        self.new_click_detected.emit(click)
                        
                        # Process auto-payments if enabled
                        if self.auto_payment_enabled:
                            self.process_auto_payment(click)
                
                # Sleep before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.status_update.emit(f"❌ Processing error: {str(e)}")
                time.sleep(10)  # Wait longer on error
    
    def fetch_unprocessed_clicks(self):
        """Fetch unprocessed ad clicks from database"""
        try:
            if not self.db_connection or not self.db_connection.is_connected():
                if not self.setup_database_connection():
                    return []
            
            cursor = self.db_connection.cursor(dictionary=True)
            
            # Fetch unprocessed clicks with developer info
            query = """
                SELECT 
                    ac.*,
                    COALESCE(ac.developer_name, CONCAT('Dev_', SUBSTRING(ac.developer_address, 1, 8))) as display_name
                FROM ad_clicks ac
                WHERE ac.processed = 0 
                AND ac.payment_status = 'pending'
                AND ac.payout_amount > 0
                ORDER BY ac.click_time ASC
                LIMIT 100
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            # Filter out already processed clicks to avoid duplicates
            new_clicks = []
            for click in results:
                click_id = click['id']
                if click_id not in self.processed_clicks:
                    new_clicks.append(click)
                    self.processed_clicks.add(click_id)
            
            return new_clicks
            
        except Exception as e:
            self.status_update.emit(f"❌ Error fetching clicks: {str(e)}")
            return []
    
    def process_auto_payment(self, click):
        """Process automatic payment for eligible clicks"""
        try:
            click_id = click['id']
            amount = float(click['payout_amount'])
            developer_address = click['developer_address']
            
            # Check if eligible for auto-payment
            if amount <= self.auto_payment_limit:
                success = self.execute_payment(click)
                
                if success:
                    self.payment_completed.emit(str(click_id), amount, developer_address)
                else:
                    self.payment_failed.emit(str(click_id), "Auto-payment failed")
            else:
                self.status_update.emit(f"💰 Click {click_id} requires manual approval (${amount:.6f} > ${self.auto_payment_limit:.6f})")
                
        except Exception as e:
            self.status_update.emit(f"❌ Auto-payment error: {str(e)}")
    
    def execute_payment(self, click):
        """Execute payment to developer"""
        try:
            click_id = click['id']
            amount = float(click['payout_amount'])
            developer_address = click['developer_address']
            
            # Check wallet balance
            if not self.wallet_instance.wallet:
                self.update_click_status(click_id, 'failed', 'No wallet available')
                return False
            
            try:
                current_balance = self.wallet_instance.get_current_balance()
            except:
                current_balance = 0.0
            
            if current_balance < amount:
                self.update_click_status(click_id, 'failed', f'Insufficient balance: {current_balance:.8f} < {amount:.8f}')
                return False
            
            # Execute transaction
            tx = self.wallet_instance.wallet.send(developer_address, amount)
            
            if tx:
                # Update database
                self.update_click_status(click_id, 'completed', transaction_id=tx.tx_id)
                self.update_developer_stats(developer_address, amount)
                
                self.status_update.emit(f"💰 Payment sent: {amount:.6f} PYC to {developer_address[:8]}...")
                
                # Save blockchain state
                if hasattr(self.wallet_instance, 'save_blockchain'):
                    self.wallet_instance.save_blockchain()
                
                return True
            else:
                self.update_click_status(click_id, 'failed', 'Transaction creation failed')
                return False
                
        except Exception as e:
            self.update_click_status(click_id, 'failed', str(e))
            return False
    
    def update_click_status(self, click_id, status, error_message=None, transaction_id=None):
        """Update click processing status in database"""
        try:
            cursor = self.db_connection.cursor()
            
            if status == 'completed':
                query = """
                    UPDATE ad_clicks 
                    SET processed = 1, 
                        processed_time = NOW(), 
                        payment_status = %s,
                        transaction_id = %s
                    WHERE id = %s
                """
                cursor.execute(query, (status, transaction_id, click_id))
            else:
                query = """
                    UPDATE ad_clicks 
                    SET payment_status = %s,
                        error_message = %s,
                        retry_count = retry_count + 1
                    WHERE id = %s
                """
                cursor.execute(query, (status, error_message, click_id))
            
            cursor.close()
            
        except Exception as e:
            self.status_update.emit(f"❌ Error updating click status: {str(e)}")
    
    def update_developer_stats(self, developer_address, amount):
        """Update developer payment statistics"""
        try:
            cursor = self.db_connection.cursor()
            
            query = """
                INSERT INTO developer_payments 
                (developer_address, total_clicks, total_earnings, last_payment, last_click)
                VALUES (%s, 1, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                total_clicks = total_clicks + 1,
                total_earnings = total_earnings + %s,
                last_payment = NOW(),
                last_click = NOW(),
                updated_at = NOW()
            """
            
            cursor.execute(query, (developer_address, amount, amount))
            cursor.close()
            
        except Exception as e:
            self.status_update.emit(f"❌ Error updating developer stats: {str(e)}")
    
    def manual_process_click(self, click_id):
        """Manually process a specific click"""
        try:
            cursor = self.db_connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM ad_clicks WHERE id = %s", (click_id,))
            click = cursor.fetchone()
            cursor.close()
            
            if click:
                success = self.execute_payment(click)
                return success
            else:
                return False
                
        except Exception as e:
            self.status_update.emit(f"❌ Manual processing error: {str(e)}")
            return False
    
    def set_auto_payment_enabled(self, enabled):
        """Enable/disable auto-payment"""
        self.auto_payment_enabled = enabled
        self.status_update.emit(f"🤖 Auto-payment {'enabled' if enabled else 'disabled'}")
    
    def set_auto_payment_limit(self, limit):
        """Set auto-payment limit"""
        self.auto_payment_limit = limit
        self.status_update.emit(f"💰 Auto-payment limit set to {limit:.6f} PYC")
    
    def stop(self):
        """Stop the processor"""
        self.running = False
        if self.db_connection:
            self.db_connection.close()
class EnhancedAdClickProcessor(QThread):
    """Enhanced processor for unprocessed ad clicks with auto-payment"""
    
    # Signals for UI updates
    new_click_detected = pyqtSignal(dict)
    payment_completed = pyqtSignal(str, float, str)  # click_id, amount, developer_address
    payment_failed = pyqtSignal(str, str)  # click_id, error_message
    status_update = pyqtSignal(str)
    
    def __init__(self, wallet_instance):
        super().__init__()
        self.wallet_instance = wallet_instance
        self.running = False
        self.auto_payment_enabled = False
        self.auto_payment_limit = 0.1  # Max auto-payment amount
        self.check_interval = 5  # Check every 5 seconds
        self.processed_clicks = set()  # Track processed clicks to avoid duplicates
        
        # Database connection
        self.db_connection = None
        self.setup_database_connection()
        
    def setup_database_connection(self):
        """Setup enhanced database connection with retry logic"""
        try:
            db_config = {
                'host': 'localhost',
                'database': 'adnetwrk',
                'user': 'root',
                'password': '',
                'autocommit': True,
                'charset': 'utf8mb4',
                'connection_timeout': 10,
                'autocommit': True
            }
            
            self.db_connection = mysql.connector.connect(**db_config)
            
            # Ensure required tables exist
            self.ensure_tables_exist()
            
            self.status_update.emit("✅ Enhanced database connection established")
            return True
            
        except Exception as e:
            self.status_update.emit(f"❌ Database connection failed: {str(e)}")
            return False
    
    def ensure_tables_exist(self):
        """Ensure all required tables exist with proper structure"""
        try:
            cursor = self.db_connection.cursor()
            
            # Enhanced ad_clicks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ad_clicks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ad_id VARCHAR(100) NOT NULL,
                    client_id VARCHAR(100),
                    developer_address VARCHAR(100) NOT NULL,
                    developer_name VARCHAR(100),
                    zone VARCHAR(100) DEFAULT 'default',
                    payout_amount DECIMAL(16,8) NOT NULL DEFAULT 0.00100000,
                    click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    processed TINYINT(1) DEFAULT 0,
                    processed_time TIMESTAMP NULL,
                    transaction_id VARCHAR(100),
                    payment_status VARCHAR(20) DEFAULT 'pending',
                    error_message TEXT,
                    retry_count INT DEFAULT 0,
                    INDEX idx_processed (processed),
                    INDEX idx_click_time (click_time),
                    INDEX idx_developer (developer_address),
                    INDEX idx_payment_status (payment_status)
                )
            """)
            
            # Payment queue table for batch processing
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_queue (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    click_id INT NOT NULL,
                    developer_address VARCHAR(100) NOT NULL,
                    amount DECIMAL(16,8) NOT NULL,
                    status VARCHAR(20) DEFAULT 'queued',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP NULL,
                    transaction_id VARCHAR(100),
                    error_message TEXT,
                    FOREIGN KEY (click_id) REFERENCES ad_clicks(id),
                    INDEX idx_status (status),
                    INDEX idx_created (created_at)
                )
            """)
            
            # Developer payment history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS developer_payments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    developer_address VARCHAR(100) NOT NULL,
                    developer_name VARCHAR(100),
                    total_clicks INT DEFAULT 0,
                    total_earnings DECIMAL(16,8) DEFAULT 0.00000000,
                    last_payment TIMESTAMP NULL,
                    last_click TIMESTAMP NULL,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_developer (developer_address),
                    INDEX idx_developer (developer_address),
                    INDEX idx_last_payment (last_payment)
                )
            """)
            
            cursor.close()
            self.status_update.emit("✅ Database tables verified/created")
            
        except Exception as e:
            self.status_update.emit(f"❌ Table creation error: {str(e)}")
    
    def run(self):
        """Main processing loop"""
        self.running = True
        self.status_update.emit("🔄 Ad click processor started")
        
        while self.running:
            try:
                # Check for unprocessed clicks
                unprocessed_clicks = self.fetch_unprocessed_clicks()
                
                if unprocessed_clicks:
                    self.status_update.emit(f"📨 Found {len(unprocessed_clicks)} unprocessed clicks")
                    
                    for click in unprocessed_clicks:
                        if not self.running:
                            break
                        
                        # Emit signal for UI update
                        self.new_click_detected.emit(click)
                        
                        # Process auto-payments if enabled
                        if self.auto_payment_enabled:
                            self.process_auto_payment(click)
                
                # Sleep before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.status_update.emit(f"❌ Processing error: {str(e)}")
                time.sleep(10)  # Wait longer on error
    
    def fetch_unprocessed_clicks(self):
        """Fetch unprocessed ad clicks from database"""
        try:
            if not self.db_connection or not self.db_connection.is_connected():
                if not self.setup_database_connection():
                    return []
            
            cursor = self.db_connection.cursor(dictionary=True)
            
            # Fetch unprocessed clicks with developer info
            query = """
                SELECT 
                    ac.*,
                    COALESCE(ac.developer_name, CONCAT('Dev_', SUBSTRING(ac.developer_address, 1, 8))) as display_name
                FROM ad_clicks ac
                WHERE ac.processed = 0 
                AND ac.payment_status = 'pending'
                AND ac.payout_amount > 0
                ORDER BY ac.click_time ASC
                LIMIT 100
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            # Filter out already processed clicks to avoid duplicates
            new_clicks = []
            for click in results:
                click_id = click['id']
                if click_id not in self.processed_clicks:
                    new_clicks.append(click)
                    self.processed_clicks.add(click_id)
            
            return new_clicks
            
        except Exception as e:
            self.status_update.emit(f"❌ Error fetching clicks: {str(e)}")
            return []
    
    def process_auto_payment(self, click):
        """Process automatic payment for eligible clicks"""
        try:
            click_id = click['id']
            amount = float(click['payout_amount'])
            developer_address = click['developer_address']
            
            # Check if eligible for auto-payment
            if amount <= self.auto_payment_limit:
                success = self.execute_payment(click)
                
                if success:
                    self.payment_completed.emit(str(click_id), amount, developer_address)
                else:
                    self.payment_failed.emit(str(click_id), "Auto-payment failed")
            else:
                self.status_update.emit(f"💰 Click {click_id} requires manual approval (${amount:.6f} > ${self.auto_payment_limit:.6f})")
                
        except Exception as e:
            self.status_update.emit(f"❌ Auto-payment error: {str(e)}")
    
    def execute_payment(self, click):
        """Execute payment to developer"""
        try:
            click_id = click['id']
            amount = float(click['payout_amount'])
            developer_address = click['developer_address']
            
            # Check wallet balance
            if not self.wallet_instance.wallet:
                self.update_click_status(click_id, 'failed', 'No wallet available')
                return False
            
            try:
                current_balance = self.wallet_instance.get_current_balance()
            except:
                current_balance = 0.0
            
            if current_balance < amount:
                self.update_click_status(click_id, 'failed', f'Insufficient balance: {current_balance:.8f} < {amount:.8f}')
                return False
            
            # Execute transaction
            tx = self.wallet_instance.wallet.send(developer_address, amount)
            
            if tx:
                # Update database
                self.update_click_status(click_id, 'completed', transaction_id=tx.tx_id)
                self.update_developer_stats(developer_address, amount)
                
                self.status_update.emit(f"💰 Payment sent: {amount:.6f} PYC to {developer_address[:8]}...")
                
                # Save blockchain state
                if hasattr(self.wallet_instance, 'save_blockchain'):
                    self.wallet_instance.save_blockchain()
                
                return True
            else:
                self.update_click_status(click_id, 'failed', 'Transaction creation failed')
                return False
                
        except Exception as e:
            self.update_click_status(click_id, 'failed', str(e))
            return False
    
    def update_click_status(self, click_id, status, error_message=None, transaction_id=None):
        """Update click processing status in database"""
        try:
            cursor = self.db_connection.cursor()
            
            if status == 'completed':
                query = """
                    UPDATE ad_clicks 
                    SET processed = 1, 
                        processed_time = NOW(), 
                        payment_status = %s,
                        transaction_id = %s
                    WHERE id = %s
                """
                cursor.execute(query, (status, transaction_id, click_id))
            else:
                query = """
                    UPDATE ad_clicks 
                    SET payment_status = %s,
                        error_message = %s,
                        retry_count = retry_count + 1
                    WHERE id = %s
                """
                cursor.execute(query, (status, error_message, click_id))
            
            cursor.close()
            
        except Exception as e:
            self.status_update.emit(f"❌ Error updating click status: {str(e)}")
    
    def update_developer_stats(self, developer_address, amount):
        """Update developer payment statistics"""
        try:
            cursor = self.db_connection.cursor()
            
            query = """
                INSERT INTO developer_payments 
                (developer_address, total_clicks, total_earnings, last_payment, last_click)
                VALUES (%s, 1, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                total_clicks = total_clicks + 1,
                total_earnings = total_earnings + %s,
                last_payment = NOW(),
                last_click = NOW(),
                updated_at = NOW()
            """
            
            cursor.execute(query, (developer_address, amount, amount))
            cursor.close()
            
        except Exception as e:
            self.status_update.emit(f"❌ Error updating developer stats: {str(e)}")
    
    def manual_process_click(self, click_id):
        """Manually process a specific click"""
        try:
            cursor = self.db_connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM ad_clicks WHERE id = %s", (click_id,))
            click = cursor.fetchone()
            cursor.close()
            
            if click:
                success = self.execute_payment(click)
                return success
            else:
                return False
                
        except Exception as e:
            self.status_update.emit(f"❌ Manual processing error: {str(e)}")
            return False
    
    def set_auto_payment_enabled(self, enabled):
        """Enable/disable auto-payment"""
        self.auto_payment_enabled = enabled
        self.status_update.emit(f"🤖 Auto-payment {'enabled' if enabled else 'disabled'}")
    
    def set_auto_payment_limit(self, limit):
        """Set auto-payment limit"""
        self.auto_payment_limit = limit
        self.status_update.emit(f"💰 Auto-payment limit set to {limit:.6f} PYC")
    
    def stop(self):
        """Stop the processor"""
        self.running = False
        if self.db_connection:
            self.db_connection.close()
class EnhancedPaymentTab:
    """Enhanced payment tab with unprocessed ad clicks integration"""
    
    def __init__(self, wallet_instance):
        self.wallet_instance = wallet_instance
        self.click_processor = None
        self.setup_enhanced_payment_tab()
        self.start_click_processor()
    
    def setup_enhanced_payment_tab(self):
        """Setup the enhanced payment tab UI"""
        try:
            # Find existing payment tab or create new one
            payment_tab = None
            for i in range(self.wallet_instance.tab_widget.count()):
                if "Payment" in self.wallet_instance.tab_widget.tabText(i):
                    payment_tab = self.wallet_instance.tab_widget.widget(i)
                    break
            
            if not payment_tab:
                self.create_new_payment_tab()
            else:
                self.enhance_existing_payment_tab(payment_tab)
                
        except Exception as e:
            print(f"Error setting up enhanced payment tab: {e}")
    
    def create_new_payment_tab(self):
        """Create new enhanced payment tab"""
        from PyQt5.QtWidgets import QWidget
        
        payment_widget = QWidget()
        layout = QVBoxLayout()
        payment_widget.setLayout(layout)
        
        # Add enhanced payment controls
        self.add_payment_controls(layout)
        
        # Add to tab widget
        self.wallet_instance.tab_widget.addTab(payment_widget, "💰 Enhanced Payments")
    
    def enhance_existing_payment_tab(self, payment_tab):
        """Enhance existing payment tab"""
        layout = payment_tab.layout()
        if layout:
            # Add enhanced controls to existing layout
            self.add_payment_controls(layout)
    
    def add_payment_controls(self, layout):
        """Add enhanced payment controls to layout"""
        
        # Status and controls group
        status_group = QGroupBox("🔄 Ad Click Payment Processor")
        status_layout = QVBoxLayout()
        
        # Status label
        self.processor_status = QLabel("Status: Initializing...")
        self.processor_status.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        status_layout.addWidget(self.processor_status)
        
        # Auto-payment controls
        auto_controls = QHBoxLayout()
        
        self.auto_payment_checkbox = QCheckBox("Enable Auto-Payment")
        self.auto_payment_checkbox.stateChanged.connect(self.toggle_auto_payment)
        auto_controls.addWidget(self.auto_payment_checkbox)
        
        auto_controls.addWidget(QLabel("Max Amount:"))
        
        self.auto_limit_spinbox = QDoubleSpinBox()
        self.auto_limit_spinbox.setDecimals(6)
        self.auto_limit_spinbox.setRange(0.000001, 1.0)
        self.auto_limit_spinbox.setValue(0.1)
        self.auto_limit_spinbox.valueChanged.connect(self.update_auto_limit)
        auto_controls.addWidget(self.auto_limit_spinbox)
        
        auto_controls.addWidget(QLabel("PYC"))
        auto_controls.addStretch()
        
        status_layout.addLayout(auto_controls)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Unprocessed clicks table
        clicks_group = QGroupBox("📨 Unprocessed Ad Clicks")
        clicks_layout = QVBoxLayout()
        
        # Table for unprocessed clicks
        self.clicks_table = QTableWidget()
        self.clicks_table.setColumnCount(8)
        self.clicks_table.setHorizontalHeaderLabels([
            "ID", "Developer", "Amount", "Time", "Ad ID", "Zone", "Status", "Action"
        ])
        
        # Configure table
        header = self.clicks_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.clicks_table.setAlternatingRowColors(True)
        self.clicks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        clicks_layout.addWidget(self.clicks_table)
        
        # Batch processing controls
        batch_controls = QHBoxLayout()
        
        self.select_all_btn = QPushButton("☑️ Select All")
        self.select_all_btn.clicked.connect(self.select_all_clicks)
        batch_controls.addWidget(self.select_all_btn)
        
        self.process_selected_btn = QPushButton("💸 Process Selected")
        self.process_selected_btn.clicked.connect(self.process_selected_clicks)
        self.process_selected_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        batch_controls.addWidget(self.process_selected_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_clicks_table)
        batch_controls.addWidget(self.refresh_btn)
        
        batch_controls.addStretch()
        
        # Statistics
        self.stats_label = QLabel("Processed: 0 | Pending: 0 | Total Paid: 0.000000 PYC")
        batch_controls.addWidget(self.stats_label)
        
        clicks_layout.addLayout(batch_controls)
        clicks_group.setLayout(clicks_layout)
        layout.addWidget(clicks_group)
    
    def start_click_processor(self):
        """Start the click processor thread"""
        try:
            self.click_processor = EnhancedAdClickProcessor(self.wallet_instance)
            
            # Connect signals
            self.click_processor.new_click_detected.connect(self.add_click_to_table)
            self.click_processor.payment_completed.connect(self.on_payment_completed)
            self.click_processor.payment_failed.connect(self.on_payment_failed)
            self.click_processor.status_update.connect(self.update_status)
            
            # Start processor
            self.click_processor.start()
            
        except Exception as e:
            print(f"Error starting click processor: {e}")
    
    def add_click_to_table(self, click):
        """Add new click to the table"""
        try:
            row = self.clicks_table.rowCount()
            self.clicks_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(str(click['id']))
            self.clicks_table.setItem(row, 0, id_item)
            
            # Developer
            dev_name = click.get('display_name', click['developer_address'][:8] + '...')
            dev_item = QTableWidgetItem(dev_name)
            dev_item.setToolTip(click['developer_address'])
            self.clicks_table.setItem(row, 1, dev_item)
            
            # Amount
            amount_item = QTableWidgetItem(f"{click['payout_amount']:.6f} PYC")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            if float(click['payout_amount']) <= self.auto_limit_spinbox.value():
                amount_item.setForeground(QColor(40, 167, 69))  # Green for auto-eligible
            else:
                amount_item.setForeground(QColor(220, 53, 69))  # Red for manual
            self.clicks_table.setItem(row, 2, amount_item)
            
            # Time
            time_item = QTableWidgetItem(str(click['click_time']))
            self.clicks_table.setItem(row, 3, time_item)
            
            # Ad ID
            ad_item = QTableWidgetItem(str(click['ad_id'])[:8] + '...')
            ad_item.setToolTip(str(click['ad_id']))
            self.clicks_table.setItem(row, 4, ad_item)
            
            # Zone
            zone_item = QTableWidgetItem(str(click.get('zone', 'default')))
            self.clicks_table.setItem(row, 5, zone_item)
            
            # Status
            status_item = QTableWidgetItem(click.get('payment_status', 'pending'))
            self.clicks_table.setItem(row, 6, status_item)
            
            # Action button
            pay_btn = QPushButton("💰 Pay Now")
            pay_btn.clicked.connect(lambda: self.manual_pay_click(click['id']))
            pay_btn.setStyleSheet("background-color: #007bff; color: white;")
            self.clicks_table.setCellWidget(row, 7, pay_btn)
            
            # Update statistics
            self.update_statistics()
            
        except Exception as e:
            print(f"Error adding click to table: {e}")
    
    def manual_pay_click(self, click_id):
        """Manually process a specific click"""
        try:
            if self.click_processor:
                success = self.click_processor.manual_process_click(click_id)
                if success:
                    self.update_status(f"✅ Manual payment for click {click_id} completed")
                    self.refresh_clicks_table()
                else:
                    self.update_status(f"❌ Manual payment for click {click_id} failed")
            
        except Exception as e:
            self.update_status(f"❌ Manual payment error: {str(e)}")
    
    def toggle_auto_payment(self, state):
        """Toggle auto-payment on/off"""
        enabled = state == 2  # Qt.Checked
        if self.click_processor:
            self.click_processor.set_auto_payment_enabled(enabled)
    
    def update_auto_limit(self, value):
        """Update auto-payment limit"""
        if self.click_processor:
            self.click_processor.set_auto_payment_limit(value)
    
    def select_all_clicks(self):
        """Select all rows in the table"""
        self.clicks_table.selectAll()
    
    def process_selected_clicks(self):
        """Process all selected clicks"""
        try:
            selected_rows = set()
            for item in self.clicks_table.selectedItems():
                selected_rows.add(item.row())
            
            if not selected_rows:
                QMessageBox.warning(None, "No Selection", "Please select clicks to process")
                return
            
            # Confirm processing
            reply = QMessageBox.question(None, "Confirm Processing", 
                                       f"Process {len(selected_rows)} selected clicks?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                processed_count = 0
                for row in selected_rows:
                    click_id_item = self.clicks_table.item(row, 0)
                    if click_id_item:
                        click_id = int(click_id_item.text())
                        if self.click_processor.manual_process_click(click_id):
                            processed_count += 1
                
                self.update_status(f"✅ Processed {processed_count}/{len(selected_rows)} selected clicks")
                self.refresh_clicks_table()
            
        except Exception as e:
            self.update_status(f"❌ Batch processing error: {str(e)}")
    
    def refresh_clicks_table(self):
        """Refresh the clicks table"""
        try:
            # Clear existing rows
            self.clicks_table.setRowCount(0)
            
            # Reload data
            if self.click_processor:
                unprocessed = self.click_processor.fetch_unprocessed_clicks()
                for click in unprocessed:
                    self.add_click_to_table(click)
            
        except Exception as e:
            print(f"Error refreshing table: {e}")
    
    def update_statistics(self):
        """Update statistics display"""
        try:
            # Get statistics from database
            if self.click_processor and self.click_processor.db_connection:
                cursor = self.click_processor.db_connection.cursor()
                
                # Count processed vs pending
                cursor.execute("SELECT COUNT(*) FROM ad_clicks WHERE processed = 1")
                processed_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM ad_clicks WHERE processed = 0")
                pending_count = cursor.fetchone()[0]
                
                # Total paid amount
                cursor.execute("SELECT COALESCE(SUM(payout_amount), 0) FROM ad_clicks WHERE processed = 1")
                total_paid = cursor.fetchone()[0]
                
                cursor.close()
                
                self.stats_label.setText(
                    f"Processed: {processed_count} | Pending: {pending_count} | Total Paid: {total_paid:.6f} PYC"
                )
            
        except Exception as e:
            print(f"Error updating statistics: {e}")
    
    def update_status(self, message):
        """Update status display"""
        if hasattr(self, 'processor_status'):
            self.processor_status.setText(f"Status: {message}")
    
    def on_payment_completed(self, click_id, amount, developer_address):
        """Handle payment completion"""
        self.update_status(f"✅ Payment completed: {amount:.6f} PYC to {developer_address[:8]}...")
        self.refresh_clicks_table()
    
    def on_payment_failed(self, click_id, error_message):
        """Handle payment failure"""
        self.update_status(f"❌ Payment failed for click {click_id}: {error_message}")

def inject_enhanced_payment_system(wallet_instance):
    """Main injection function to enhance the payment system"""
    try:
        print("🔄 Injecting enhanced ad click payment system...")
        
        # Add enhanced payment tab
        enhanced_payment_tab = EnhancedPaymentTab(wallet_instance)
        
        # Add method to wallet instance for external access
        wallet_instance.enhanced_payment_processor = enhanced_payment_tab.click_processor
        
        # Add convenience methods
        def get_payment_statistics():
            """Get payment processing statistics"""
            try:
                if hasattr(wallet_instance, 'enhanced_payment_processor') and wallet_instance.enhanced_payment_processor:
                    processor = wallet_instance.enhanced_payment_processor
                    if processor.db_connection:
                        cursor = processor.db_connection.cursor(dictionary=True)
                        
                        cursor.execute("""
                            SELECT 
                                COUNT(*) as total_clicks,
                                SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed_clicks,
                                SUM(CASE WHEN processed = 0 THEN 1 ELSE 0 END) as pending_clicks,
                                COALESCE(SUM(CASE WHEN processed = 1 THEN payout_amount ELSE 0 END), 0) as total_paid
                            FROM ad_clicks
                        """)
                        
                        stats = cursor.fetchone()
                        cursor.close()
                        return stats
                return {}
            except Exception as e:
                print(f"Error getting payment stats: {e}")
                return {}
        
        wallet_instance.get_payment_statistics = get_payment_statistics
        
        print("✅ Enhanced ad click payment system injected successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Injection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
            
            # Optimize server settings
class OptimizedServer(ThreadingHTTPServer):
    def start_notification_broadcaster(self):
        """Start background thread for broadcasting notifications"""
    def broadcast_worker():
            while self.running:
                try:
                    # Check for new notifications every 2 seconds
                    self.broadcast_pending_notifications()
                    time.sleep(2)
                except Exception as e:
                    print(f"Notification broadcaster error: {e}")
                    time.sleep(5)
        
                    broadcaster_thread = threading.Thread(target=broadcast_worker, daemon=True)
                    broadcaster_thread.start()
    
    def broadcast_pending_notifications(self):
        """Broadcast pending notifications to connected developers"""
        try:
            notifications_file = os.path.join(self.notifications_dir, 'pending.json')
            if os.path.exists(notifications_file):
                with open(notifications_file, 'r') as f:
                    notifications = json.load(f)
                
                if notifications:
                    # Emit signal for UI update
                    self.client_notification.emit({'notifications': notifications})
                    
                    # Clear processed notifications
                    with open(notifications_file, 'w') as f:
                        json.dump([], f)
                        
        except Exception as e:
            print(f"Notification broadcast error: {e}")
    
    def handle_client_info(self):
        """Enhanced client info with more details"""
        try:
            client_info = {
                'client_id': f'pyc_{self.wallet.address[:8]}' if self.wallet else 'pyc_unknown',
                'name': f'PythonCoin Wallet - {self.wallet.address[:8]}...' if self.wallet else 'PythonCoin Wallet',
                'status': 'online',
                'host': '127.0.0.1',
                'port': self.port,
                'wallet_address': self.wallet.address if self.wallet else '',
                'ad_count': len(self.get_available_ads()),
                'active_developers': len(self.registered_developers),
                'total_payments': len(self.click_payments),
                'server_version': '2.1.0',
                'capabilities': ['ad_serving', 'payments', 'p2p', 'notifications', 'file_verification'],
                'blockchain_height': len(self.blockchain.chain) if self.blockchain else 0,
                'last_updated': datetime.now().isoformat()
            }
            
            return json.dumps({'success': True, 'client': client_info})
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_discover_clients(self):
        """Handle client discovery requests"""
        try:
            # Return list of discovered clients with their ad offerings
            discovered_clients = []
            
            for client_id, client_info in self.active_clients.items():
                client_data = {
                    'client_id': client_id,
                    'name': client_info.get('name', 'Unknown Client'),
                    'wallet_address': client_info.get('wallet_address', ''),
                    'ad_count': client_info.get('ad_count', 0),
                    'categories': client_info.get('categories', []),
                    'payout_rates': client_info.get('payout_rates', {}),
                    'last_seen': client_info.get('last_seen', ''),
                    'status': 'online' if client_info.get('last_seen_timestamp', 0) > (datetime.now().timestamp() - 300) else 'offline'
                }
                discovered_clients.append(client_data)
            
            return json.dumps({
                'success': True,
                'clients': discovered_clients,
                'total': len(discovered_clients)
            })
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_get_active_clients(self):
        """Get currently active advertising clients"""
        return self.handle_discover_clients()
    
    def handle_advertise_client(self, data):
        """Handle client advertising their services"""
        try:
            client_id = data.get('client_id', '')
            client_name = data.get('name', '')
            wallet_address = data.get('wallet_address', '')
            ad_count = data.get('ad_count', 0)
            categories = data.get('categories', [])
            payout_rates = data.get('payout_rates', {})
            
            if not client_id or not wallet_address:
                return json.dumps({'success': False, 'error': 'Missing client_id or wallet_address'})
            
            # Store client information
            self.active_clients[client_id] = {
                'name': client_name,
                'wallet_address': wallet_address,
                'ad_count': ad_count,
                'categories': categories,
                'payout_rates': payout_rates,
                'last_seen': datetime.now().isoformat(),
                'last_seen_timestamp': datetime.now().timestamp()
            }
            
            self.status_update.emit(f"Client advertised: {client_name} ({ad_count} ads)")
            
            return json.dumps({'success': True, 'message': 'Client advertisement recorded'})
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_select_client(self, data):
        """Handle developer selecting a client for ads"""
        try:
            developer_address = data.get('developer_address', '')
            client_id = data.get('client_id', '')
            selected_categories = data.get('categories', [])
            
            if not developer_address or not client_id:
                return json.dumps({'success': False, 'error': 'Missing developer_address or client_id'})
            
            if client_id not in self.active_clients:
                return json.dumps({'success': False, 'error': 'Client not found or offline'})
            
            # Generate custom JS for this developer-client combination
            js_filename = f"custom_{developer_address}_{client_id}.js"
            js_content = self.generate_enhanced_custom_js(developer_address, client_id, selected_categories)
            
            # Save JS file
            js_filepath = os.path.join(self.js_dir, js_filename)
            with open(js_filepath, 'w', encoding='utf-8') as f:
                f.write(js_content)
            
            # Calculate and store file hash
            file_hash = self.calculate_file_hash(js_filepath)
            self.js_file_hashes[js_filename] = file_hash
            
            self.status_update.emit(f"Generated custom JS: {js_filename} (hash: {file_hash[:8]}...)")
            
            return json.dumps({
                'success': True,
                'js_filename': js_filename,
                'js_url': f'http://127.0.0.1:{self.port}/{js_filename}',
                'file_hash': file_hash,
                'client_info': self.active_clients[client_id]
            })
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_generate_custom_js(self, data):
        """Generate custom JS file with hash verification"""
        try:
            developer_address = data.get('developer_address', '')
            client_preferences = data.get('client_preferences', {})
            
            if not developer_address:
                return json.dumps({'success': False, 'error': 'Missing developer_address'})
            
            # Generate JS filename based on developer address
            js_filename = f"custom_{developer_address}.js"
            js_content = self.generate_developer_custom_js(developer_address, client_preferences)
            
            # Save JS file
            js_filepath = os.path.join(self.js_dir, js_filename)
            with open(js_filepath, 'w', encoding='utf-8') as f:
                f.write(js_content)
            
            # Calculate file hash for verification
            file_hash = self.calculate_file_hash(js_filepath)
            self.js_file_hashes[js_filename] = file_hash
            
            return json.dumps({
                'success': True,
                'js_filename': js_filename,
                'js_url': f'http://127.0.0.1:{self.port}/{js_filename}',
                'file_hash': file_hash,
                'verification_url': f'http://127.0.0.1:{self.port}/verify_js/{js_filename}'
            })
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_verify_js(self, path):
        """Verify JS file integrity using hash"""
        try:
            filename = path.split('/')[-1]
            
            if filename not in self.js_file_hashes:
                return json.dumps({'success': False, 'error': 'File not found in hash registry'})
            
            js_filepath = os.path.join(self.js_dir, filename)
            if not os.path.exists(js_filepath):
                return json.dumps({'success': False, 'error': 'JS file not found on disk'})
            
            # Calculate current hash
            current_hash = self.calculate_file_hash(js_filepath)
            stored_hash = self.js_file_hashes[filename]
            
            is_valid = current_hash == stored_hash
            
            return json.dumps({
                'success': True,
                'filename': filename,
                'is_valid': is_valid,
                'current_hash': current_hash,
                'stored_hash': stored_hash,
                'verified_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_notify_ad_created(self, data):
        """Handle notification when new ad is created"""
        try:
            ad_data = data.get('ad_data', {})
            advertiser_address = data.get('advertiser_address', '')
            
            # Create notification
            notification = {
                'type': 'new_ad_available',
                'timestamp': datetime.now().isoformat(),
                'advertiser_address': advertiser_address,
                'ad_title': ad_data.get('title', 'New Advertisement'),
                'ad_category': ad_data.get('category', 'general'),
                'payout_rate': ad_data.get('payout_rate', 0.001),
                'message': f"New ad available: {ad_data.get('title', 'Untitled')} - {ad_data.get('payout_rate', 0.001)} PYC per click"
            }
            
            # Save notification
            self.save_notification(notification)
            
            # Emit signal for immediate UI update
            self.client_notification.emit(notification)
            
            return json.dumps({'success': True, 'notification_sent': True})
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_get_notifications(self):
        """Get pending notifications"""
        try:
            notifications_file = os.path.join(self.notifications_dir, 'recent.json')
            
            if os.path.exists(notifications_file):
                with open(notifications_file, 'r') as f:
                    notifications = json.load(f)
            else:
                notifications = []
            
            return json.dumps({
                'success': True,
                'notifications': notifications,
                'count': len(notifications)
            })
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def save_notification(self, notification):
        """Save notification to file system"""
        try:
            # Save to pending notifications
            pending_file = os.path.join(self.notifications_dir, 'pending.json')
            pending_notifications = []
            
            if os.path.exists(pending_file):
                with open(pending_file, 'r') as f:
                    pending_notifications = json.load(f)
            
            pending_notifications.append(notification)
            
            with open(pending_file, 'w') as f:
                json.dump(pending_notifications, f, indent=2)
            
            # Also save to recent notifications (keep last 50)
            recent_file = os.path.join(self.notifications_dir, 'recent.json')
            recent_notifications = []
            
            if os.path.exists(recent_file):
                with open(recent_file, 'r') as f:
                    recent_notifications = json.load(f)
            
            recent_notifications.insert(0, notification)
            recent_notifications = recent_notifications[:50]  # Keep only last 50
            
            with open(recent_file, 'w') as f:
                json.dump(recent_notifications, f, indent=2)
                
        except Exception as e:
            print(f"Error saving notification: {e}")
    
    def calculate_file_hash(self, filepath):
        """Calculate SHA256 hash of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            return ""
    
    def generate_enhanced_custom_js(self, developer_address, client_id, categories):
        """Generate enhanced custom JS with client-specific ads"""
        try:
            client_info = self.active_clients.get(client_id, {})
            ads = self.get_client_specific_ads(client_id, categories)
            
            js_template = """// PythonCoin Enhanced Custom Ad JavaScript
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
// Developer: {developer_address}
// Client: {client_name} ({client_id})
// Categories: {categories}
// Generated: {timestamp}
// File Hash: Will be calculated after generation

(function() {{
    'use strict';
    
    console.log('[PYC-ENHANCED] Loading ads from client: {client_name}');
    
    const PYC_CONFIG = {{
        developerAddress: '{developer_address}',
        clientId: '{client_id}',
        clientName: '{client_name}',
        serverHost: 'http://127.0.0.1:{server_port}',
        ads: {ads_json},
        categories: {categories_json},
        verificationUrl: 'http://127.0.0.1:{server_port}/verify_js/custom_{developer_address}_{client_id}.js',
        loadTime: new Date().toISOString()
    }};
    
    // Verify file integrity on load
    function verifyFileIntegrity() {{
        fetch(PYC_CONFIG.verificationUrl)
            .then(response => response.json())
            .then(data => {{
                if (data.success && data.is_valid) {{
                    console.log('[PYC-ENHANCED] File integrity verified ✓');
                }} else {{
                    console.warn('[PYC-ENHANCED] File integrity check failed!');
                }}
            }})
            .catch(error => console.warn('[PYC-ENHANCED] Could not verify file integrity:', error));
    }}
    
    // Initialize enhanced ad system
    function initEnhancedAds() {{
        console.log('[PYC-ENHANCED] Initializing enhanced ad system');
        console.log('[PYC-ENHANCED] Available ads:', PYC_CONFIG.ads.length);
        
        // Verify file integrity
        verifyFileIntegrity();
        
        if (PYC_CONFIG.ads.length > 0) {{
            displayClientAd(PYC_CONFIG.ads[0]);
            if (PYC_CONFIG.ads.length > 1) {{
                startSmartAdRotation();
            }}
        }} else {{
            displayNoAdsMessage();
        }}
        
        // Track impression
        trackEnhancedImpression();
    }}
    
    function displayClientAd(ad) {{
        const containers = document.querySelectorAll('[data-pyc-zone]');
        
        containers.forEach(container => {{
            const zone = container.getAttribute('data-pyc-zone') || 'default';
            container.innerHTML = createEnhancedAdHTML(ad, zone);
            
            // Add enhanced click handler
            const adElement = container.querySelector('.pyc-enhanced-ad');
            if (adElement) {{
                adElement.onclick = function() {{
                    handleEnhancedAdClick(ad.id, zone);
                }};
                
                // Add premium hover effects
                adElement.addEventListener('mouseenter', function() {{
                    this.style.transform = 'translateY(-3px) scale(1.02)';
                    this.style.boxShadow = '0 12px 35px rgba(0,102,204,0.3)';
                }});
                adElement.addEventListener('mouseleave', function() {{
                    this.style.transform = 'translateY(0) scale(1)';
                    this.style.boxShadow = '0 6px 20px rgba(0,102,204,0.15)';
                }});
            }}
        }});
    }}
    
    function createEnhancedAdHTML(ad, zone) {{
        return `
            <div class="pyc-enhanced-ad" style="
                border: 2px solid #0066cc; 
                border-radius: 16px; 
                padding: 24px; 
                background: linear-gradient(135deg, #ffffff 0%, #f8fffe 50%, #f0f9ff 100%); 
                margin: 20px 0; 
                cursor: pointer;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                box-shadow: 0 6px 20px rgba(0,102,204,0.15);
                overflow: hidden;
            ">
                <div style="position: absolute; top: 0; right: 0; width: 100px; height: 100px; background: linear-gradient(45deg, transparent 40%, rgba(255,215,0,0.1) 50%, transparent 60%); pointer-events: none;"></div>
                <div style="position: absolute; top: 12px; right: 12px; background: linear-gradient(45deg, #ff6b35, #f7931e); color: white; padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; box-shadow: 0 2px 8px rgba(255,107,53,0.3);">💎 PYC Network</div>
                <div style="position: absolute; bottom: 12px; left: 12px; background: rgba(0,102,204,0.1); color: #0066cc; padding: 4px 8px; border-radius: 12px; font-size: 9px; font-weight: 600;">Client: ${{PYC_CONFIG.clientName}}</div>
                <h3 style="color: #0066cc; margin: 0 0 12px 0; font-size: 20px; font-weight: 800; line-height: 1.3;">${{ad.title}}</h3>
                <p style="color: #555; margin: 0 0 16px 0; font-size: 15px; line-height: 1.6;">${{ad.description}}</p>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px;">
                    <span style="color: #0066cc; font-weight: 600; font-size: 13px;">📱 ${{ad.category}} • 🌐 Verified Client</span>
                    <span style="background: linear-gradient(45deg, #28a745, #20c997); color: white; padding: 8px 16px; border-radius: 25px; font-size: 12px; font-weight: bold; box-shadow: 0 3px 12px rgba(40,167,69,0.3);">+${{ad.payout.toFixed(6)}} PYC</span>
                </div>
            </div>
        `;
    }}
    
    function handleEnhancedAdClick(adId, zone) {{
        console.log('[PYC-ENHANCED] Enhanced ad clicked:', adId);
        
        const ad = PYC_CONFIG.ads.find(a => a.id === adId);
        if (!ad) return;
        
        // Show enhanced earning animation
        showEnhancedEarningPopup(ad.payout);
        
        // Send enhanced click data
        fetch(PYC_CONFIG.serverHost + '/click', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                ad_id: adId,
                developer: 'dev_' + PYC_CONFIG.developerAddress.substring(0, 8),
                pythoncoin_address: PYC_CONFIG.developerAddress,
                payout_amount: ad.payout,
                zone: zone,
                client_id: PYC_CONFIG.clientId,
                timestamp: new Date().toISOString(),
                enhanced: true
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            if (data.success) {{
                console.log('[PYC-ENHANCED] Payment processed:', data.amount, 'PYC');
                showSuccessNotification('Payment sent: ' + data.amount + ' PYC from ' + PYC_CONFIG.clientName);
            }}
        }})
        .catch(error => console.error('[PYC-ENHANCED] Payment error:', error));
        
        // Open ad URL
        if (ad.click_url && ad.click_url !== '#') {{
            setTimeout(() => window.open(ad.click_url, '_blank'), 600);
        }}
    }}
    
    function showEnhancedEarningPopup(amount) {{
        const popup = document.createElement('div');
        popup.style.cssText = `
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: linear-gradient(135deg, #28a745, #20c997, #17a2b8);
            color: white; padding: 30px 40px; border-radius: 20px; z-index: 10001;
            text-align: center; font-family: 'Segoe UI', Arial, sans-serif; font-weight: bold;
            box-shadow: 0 20px 60px rgba(40, 167, 69, 0.4);
            animation: enhancedPopupAnimation 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        `;
        
        popup.innerHTML = `
            <div style="font-size: 36px; margin-bottom: 10px;">💰</div>
            <div style="font-size: 22px; margin-bottom: 8px;">PythonCoin Earned!</div>
            <div style="font-size: 18px; opacity: 0.95;">+${{amount.toFixed(6)}} PYC</div>
            <div style="font-size: 12px; opacity: 0.8; margin-top: 8px;">from ${{PYC_CONFIG.clientName}}</div>
        `;
        
        document.body.appendChild(popup);
        setTimeout(() => popup.remove(), 3500);
    }}
    
    function startSmartAdRotation() {{
        let rotationInterval = setInterval(() => {{
            const currentIndex = Math.floor(Math.random() * PYC_CONFIG.ads.length);
            displayClientAd(PYC_CONFIG.ads[currentIndex]);
        }}, 45000); // 45 second smart rotation
    }}
    
    function trackEnhancedImpression() {{
        fetch(PYC_CONFIG.serverHost + '/impression', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                developer: 'dev_' + PYC_CONFIG.developerAddress.substring(0, 8),
                client_id: PYC_CONFIG.clientId,
                enhanced: true,
                timestamp: new Date().toISOString()
            }})
        }}).catch(console.warn);
    }}
    
    // Add enhanced popup animation styles
    if (!document.querySelector('#pyc-enhanced-styles')) {{
        const style = document.createElement('style');
        style.id = 'pyc-enhanced-styles';
        style.textContent = `
            @keyframes enhancedPopupAnimation {{
                0% {{ transform: translate(-50%, -50%) scale(0.3) rotate(-10deg); opacity: 0; }}
                50% {{ transform: translate(-50%, -50%) scale(1.05) rotate(2deg); opacity: 1; }}
                100% {{ transform: translate(-50%, -50%) scale(1) rotate(0deg); opacity: 1; }}
            }}
        `;
        document.head.appendChild(style);
    }}
    
    // Initialize when ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initEnhancedAds);
    }} else {{
        initEnhancedAds();
    }}
    
    console.log('[PYC-ENHANCED] Enhanced PythonCoin ad script loaded successfully');
    
}})();
"""
            
            return js_template.format(
                developer_address=developer_address,
                client_id=client_id,
                client_name=client_info.get('name', 'Unknown Client'),
                categories=', '.join(categories),
                timestamp=datetime.now().isoformat(),
                server_port=self.port,
                ads_json=json.dumps(ads),
                categories_json=json.dumps(categories)
            )
            
        except Exception as e:
            return f"// Error generating enhanced custom JS: {str(e)}"
    
    def generate_developer_custom_js(self, developer_address, preferences):
        """Generate custom JS for developer without specific client"""
        ads = self.get_available_ads()
        
        js_content = f"""// PythonCoin Developer Custom JavaScript
// Developer: {developer_address}
// Generated: {datetime.now().isoformat()}

(function() {{
    'use strict';
    
    const PYC_CONFIG = {{
        developerAddress: '{developer_address}',
        serverHost: 'http://127.0.0.1:{self.port}',
        ads: {json.dumps(ads)},
        preferences: {json.dumps(preferences)}
    }};
    
    // Basic ad initialization
    function initDeveloperAds() {{
        console.log('[PYC-DEV] Loading developer ads');
        
        if (PYC_CONFIG.ads.length > 0) {{
            displayDeveloperAd(PYC_CONFIG.ads[0]);
        }}
    }}
    
    function displayDeveloperAd(ad) {{
        const containers = document.querySelectorAll('[data-pyc-zone]');
        containers.forEach(container => {{
            container.innerHTML = `
                <div style="border: 2px solid #0066cc; padding: 20px; border-radius: 12px; margin: 15px 0; background: white;">
                    <h3 style="color: #0066cc; margin: 0 0 10px 0;">${{ad.title}}</h3>
                    <p style="margin: 0 0 15px 0;">${{ad.description}}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #666;">${{ad.category}}</span>
                        <span style="background: #28a745; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px;">+${{ad.payout}} PYC</span>
                    </div>
                </div>
            `;
        }});
    }}
    
    // Initialize
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initDeveloperAds);
    }} else {{
        initDeveloperAds();
    }}
    
}})();
"""
        
        return js_content
    
    def get_client_specific_ads(self, client_id, categories):
        """Get ads specific to a client and categories"""
        base_ads = self.get_available_ads()
        
        # Filter by categories if specified
        if categories:
            filtered_ads = [ad for ad in base_ads if ad.get('category') in categories]
            if filtered_ads:
                return filtered_ads
        
        return base_ads
    
    def generate_developer_portal_html(self):
        """Generate developer portal HTML page"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PythonCoin Developer Portal</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0; padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px; margin: 0 auto; padding: 20px;
            background: rgba(255,255,255,0.95);
            border-radius: 20px; margin-top: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center; padding: 30px 0;
            border-bottom: 2px solid #eee; margin-bottom: 30px;
        }}
        .client-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px; margin: 30px 0;
        }}
        .client-card {{
            border: 2px solid #ddd; border-radius: 12px; padding: 20px;
            background: white; transition: all 0.3s ease;
            cursor: pointer;
        }}
        .client-card:hover {{
            border-color: #0066cc; transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,102,204,0.2);
        }}
        .btn {{
            background: #0066cc; color: white; border: none;
            padding: 12px 24px; border-radius: 8px; cursor: pointer;
            font-weight: 600; transition: all 0.3s ease;
        }}
        .btn:hover {{ background: #0052a3; transform: translateY(-1px); }}
        .notification {{
            background: #d4edda; border: 1px solid #c3e6cb;
            padding: 15px; border-radius: 8px; margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 PythonCoin Developer Portal</h1>
            <p>Connect to advertising clients and earn PythonCoin</p>
        </div>
        
        <div id="notifications"></div>
        
        <div class="section">
            <h2>Available Advertising Clients</h2>
            <div id="clientsGrid" class="client-grid">
                <div style="text-align: center; padding: 40px;">
                    <p>Loading advertising clients...</p>
                    <button onclick="loadClients()" class="btn">Refresh Clients</button>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Generate Custom Ad Script</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 12px;">
                <label>Your PythonCoin Address:</label>
                <input type="text" id="developerAddress" placeholder="Enter your PythonCoin wallet address" style="width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 6px;">
                <button onclick="generateCustomScript()" class="btn">Generate Custom Script</button>
                <div id="scriptResult" style="margin-top: 20px;"></div>
            </div>
        </div>
    </div>
    
    <script>
        const SERVER_URL = 'http://127.0.0.1:{self.port}';
        
        function loadClients() {{
            fetch(SERVER_URL + '/discover_clients')
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        displayClients(data.clients);
                    }}
                }})
                .catch(error => console.error('Error loading clients:', error));
        }}
        
        function displayClients(clients) {{
            const grid = document.getElementById('clientsGrid');
            
            if (clients.length === 0) {{
                grid.innerHTML = '<div style="text-align: center; padding: 40px;"><p>No advertising clients available</p></div>';
                return;
            }}
            
            grid.innerHTML = clients.map(client => `
                <div class="client-card" onclick="selectClient('${{client.client_id}}')">
                    <h3>${{client.name}}</h3>
                    <p>Ads Available: ${{client.ad_count}}</p>
                    <p>Categories: ${{client.categories.join(', ') || 'All'}}</p>
                    <p>Status: <span style="color: ${{client.status === 'online' ? '#28a745' : '#dc3545'}}">${{client.status}}</span></p>
                    <div style="margin-top: 15px;">
                        <span class="btn" style="font-size: 12px;">Select Client</span>
                    </div>
                </div>
            `).join('');
        }}
        
        function selectClient(clientId) {{
            const developerAddress = document.getElementById('developerAddress').value;
            
            if (!developerAddress) {{
                alert('Please enter your PythonCoin address first');
                return;
            }}
            
            fetch(SERVER_URL + '/select_client', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    developer_address: developerAddress,
                    client_id: clientId,
                    categories: []
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showScriptResult(data);
                }}
            }})
            .catch(error => console.error('Error selecting client:', error));
        }}
        
        function generateCustomScript() {{
            const developerAddress = document.getElementById('developerAddress').value;
            
            if (!developerAddress) {{
                alert('Please enter your PythonCoin address');
                return;
            }}
            
            fetch(SERVER_URL + '/generate_custom_js', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    developer_address: developerAddress,
                    client_preferences: {{}}
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showScriptResult(data);
                }}
            }})
            .catch(error => console.error('Error generating script:', error));
        }}
        
        function showScriptResult(data) {{
            const result = document.getElementById('scriptResult');
            result.innerHTML = `
                <div style="background: #d4edda; padding: 15px; border-radius: 8px;">
                    <h4>✅ Custom Script Generated!</h4>
                    <p><strong>File:</strong> ${{data.js_filename}}</p>
                    <p><strong>URL:</strong> <a href="${{data.js_url}}" target="_blank">${{data.js_url}}</a></p>
                    <p><strong>Hash:</strong> ${{data.file_hash}}</p>
                    <button onclick="copyToClipboard('${{data.js_url}}')" class="btn">Copy URL</button>
                </div>
            `;
        }}
        
        function copyToClipboard(text) {{
            navigator.clipboard.writeText(text).then(() => {{
                alert('Copied to clipboard!');
            }});
        }}
        
        // Load notifications
        function loadNotifications() {{
            fetch(SERVER_URL + '/notifications')
                .then(response => response.json())
                .then(data => {{
                    if (data.success && data.notifications.length > 0) {{
                        displayNotifications(data.notifications);
                    }}
                }})
                .catch(error => console.error('Error loading notifications:', error));
        }}
        
        function displayNotifications(notifications) {{
            const container = document.getElementById('notifications');
            container.innerHTML = notifications.slice(0, 3).map(notif => `
                <div class="notification">
                    <strong>${{notif.type.replace('_', ' ').toUpperCase()}}</strong>: ${{notif.message}}
                    <small style="float: right;">${{new Date(notif.timestamp).toLocaleString()}}</small>
                </div>
            `).join('');
        }}
        
        // Initialize
        loadClients();
        loadNotifications();
        
        // Refresh every 30 seconds
        setInterval(() => {{
            loadClients();
            loadNotifications();
        }}, 30000);
    </script>
</body>
</html>"""
    
    # Add remaining methods from original class (handle_click, handle_impression, etc.)
    def handle_register_developer(self, data):
        """Enhanced developer registration with session tracking"""
        try:
            developer = (data.get('developer') or 
                        data.get('developer_name') or 
                        data.get('username') or '')
            
            pythoncoin_address = (data.get('pythoncoin_address') or 
                                data.get('wallet_address') or 
                                data.get('address') or 
                                data.get('developer_address') or '')
            
            email = data.get('email', '')
            
            logger.info(f"[ENHANCED] Registration: {developer} -> {pythoncoin_address}")
            
            if not developer:
                return json.dumps({'success': False, 'error': 'Missing developer name'})
            
            if not pythoncoin_address:
                return json.dumps({'success': False, 'error': 'Missing PythonCoin address'})
            
            self.registered_developers[developer] = pythoncoin_address
            
            session_info = {
                'ip_address': getattr(self, 'client_ip', 'unknown'),
                'user_agent': data.get('user_agent', ''),
                'registration_time': datetime.now().isoformat(),
                'email': email
            }
            
            if hasattr(self, 'wallet_instance') and self.wallet_instance:
                if hasattr(self.wallet_instance, 'dev_registration'):
                    self.wallet_instance.dev_registration.register_developer(
                        developer, pythoncoin_address, session_info
                    )
                
                if hasattr(self.wallet_instance, 'on_enhanced_developer_registered'):
                    self.wallet_instance.on_enhanced_developer_registered(
                        developer, pythoncoin_address, session_info
                    )
            
            if hasattr(self, 'db_manager') and self.db_manager:
                try:
                    self.db_manager.add_developer(developer, pythoncoin_address, email)
                except Exception as db_error:
                    logger.warning(f"Database save failed: {db_error}")
            
            logger.info(f"✅ Enhanced developer registered: {developer}")
            
            return json.dumps({
                'success': True,
                'message': 'Developer registered successfully',
                'developer': developer,
                'wallet_address': pythoncoin_address,
                'enhanced': True,
                'session_tracked': True
            })
            
        except Exception as e:
            logger.error(f"Enhanced registration error: {e}")
            return json.dumps({'success': False, 'error': str(e), 'enhanced': True})
            
            if not self.is_valid_pythoncoin_address(pythoncoin_address):
                return json.dumps({'success': False, 'error': 'Invalid PythonCoin address'})
            
            self.registered_developers[developer] = pythoncoin_address
            self.developer_registered.emit(developer, pythoncoin_address)
            
            self.status_update.emit(f"Developer registered: {developer} -> {pythoncoin_address[:8]}...")
            
            return json.dumps({'success': True, 'message': 'Developer registered successfully'})
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_click(self, data):
        """Enhanced ad click handling with developer tracking"""
        try:
            ad_id = data.get('ad_id', '')
            developer = data.get('developer', '')
            pythoncoin_address = data.get('pythoncoin_address', '')
            payout_amount = float(data.get('payout_amount', 0.001))
            zone = data.get('zone', 'unknown')
            
            if not all([ad_id, developer, pythoncoin_address]):
                return json.dumps({'success': False, 'error': 'Missing required fields'})
            
            if hasattr(self, 'wallet_instance') and self.wallet_instance:
                if hasattr(self.wallet_instance, 'dev_registration'):
                    self.wallet_instance.dev_registration.update_developer_activity(developer)
                    self.wallet_instance.dev_registration.record_developer_click(developer, payout_amount)
                
                if hasattr(self.wallet_instance, 'on_enhanced_portal_click_received'):
                    click_data_enhanced = {
                        'developer': developer,
                        'amount': payout_amount,
                        'ad_id': ad_id,
                        'pythoncoin_address': pythoncoin_address,
                        'zone': zone,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.wallet_instance.on_enhanced_portal_click_received(click_data_enhanced)
            
            return json.dumps({
                'success': True,
                'payment_processing': True,
                'amount': payout_amount,
                'message': 'Click processed with enhanced tracking',
                'enhanced': True
            })
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e), 'enhanced': True})
            
            if not self.wallet or not self.blockchain:
                return json.dumps({'success': False, 'error': 'Wallet or blockchain not available'})
            
            # Quick balance check (optimized)
            try:
                balance = self.wallet.get_balance() if hasattr(self.wallet, 'get_balance') else 0
                if balance < payout_amount:
                    return json.dumps({
                        'success': False, 
                        'error': f'Insufficient balance: {balance:.8f} < {payout_amount:.8f}'
                    })
            except Exception as e:
                return json.dumps({'success': False, 'error': f'Balance check failed: {str(e)}'})
            
            # Define payment processing function
            def process_payment():
                try:
                    tx = self.wallet.send(pythoncoin_address, payout_amount)
                    if tx:
                        payment_record = {
                            'developer': developer,
                            'address': pythoncoin_address,
                            'amount': payout_amount,
                            'ad_id': ad_id,
                            'zone': zone,
                            'client_id': client_id,
                            'tx_id': tx.tx_id,
                            'timestamp': datetime.now().isoformat()
                        }
                        self.click_payments.append(payment_record)
                        self.click_received.emit({
                            'ad_id': ad_id,
                            'developer': developer,
                            'amount': payout_amount,
                            'zone': zone,
                            'client_id': client_id,
                            'timestamp': datetime.now().isoformat()
                        })
                        self.status_update.emit(f"💰 Click payment: {payout_amount:.6f} PYC -> {developer}")
                except Exception as e:
                    self.status_update.emit(f"Payment error: {str(e)}")
            
            # Run payment processing in background thread to prevent UI freezing
            threading.Thread(target=process_payment, daemon=True).start()
            
            return json.dumps({
                'success': True,
                'payment_processing': True,
                'amount': payout_amount,
                'message': 'Payment is being processed in background'
            })
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_impression(self, data):
        """Handle ad impression tracking (optimized)"""
        try:
            self.ads_served += 1
            # Don't emit signal for every impression to reduce UI updates
            if self.ads_served % 10 == 0:  # Only emit every 10th impression
                self.status_update.emit(f"📊 Impressions: {self.ads_served}")
            return json.dumps({'success': True, 'impressions': self.ads_served})
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_get_ads(self):
        """Get available ads (cached for performance)"""
        try:
            ads = self.get_available_ads()
            return json.dumps({
                'success': True,
                'ads': ads,
                'total': len(ads),
                'cached_at': datetime.now().isoformat()
            })
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def handle_stats(self):
        """Get server statistics (optimized)"""
        try:
            stats = {
                'total_developers': len(self.registered_developers),
                'total_clicks': len(self.click_payments),
                'ads_served': self.ads_served,
                'active_clients': len(self.active_clients),
                'available_ads': len(self.get_available_ads()),
                'server_port': self.port,
                'server_status': 'online' if self.running else 'offline',
                'wallet_address': self.wallet.address if self.wallet else '',
                'last_updated': datetime.now().isoformat()
            }
            
            # Only include balance if specifically requested to avoid frequent calculations
            if hasattr(self.wallet, 'get_balance'):
                try:
                    stats['wallet_balance'] = float(self.wallet.get_balance())
                except:
                    stats['wallet_balance'] = 0.0
            
            return json.dumps({'success': True, 'stats': stats})
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
    
    def get_available_ads(self):
        """Get real available ads with intelligent caching"""
        try:
            if hasattr(self, 'wallet_instance') and self.wallet_instance:
                if hasattr(self.wallet_instance, 'ad_fetcher'):
                    return self.wallet_instance.ad_fetcher.get_real_ads(limit=20)
            
            current_time = datetime.now().timestamp()
            if not hasattr(self, '_cached_ads_time') or current_time - self._cached_ads_time > 60:
                
                if hasattr(self, 'wallet') and hasattr(self.wallet, 'ads'):
                    real_ads = []
                    for ad in self.wallet.ads:
                        ad_dict = ad.to_dict() if hasattr(ad, 'to_dict') else ad.__dict__
                        real_ads.append({
                            'id': ad_dict.get('id', ''),
                            'title': ad_dict.get('title', 'Real Ad'),
                            'description': ad_dict.get('description', ''),
                            'category': ad_dict.get('category', 'general'),
                            'payout': ad_dict.get('payout_rate', 0.001),
                            'click_url': ad_dict.get('click_url', '#'),
                            'advertiser': ad_dict.get('advertiser_address', ''),
                            'created_at': ad_dict.get('created_at', ''),
                            'expires_at': ad_dict.get('expires_at', '')
                        })
                    
                    if real_ads:
                        self._cached_ads = real_ads
                        self._cached_ads_time = current_time
                        return real_ads
            
            return getattr(self, '_cached_ads', [])
            
        except Exception as e:
            print(f"Error getting available ads: {e}")
            return []
    
    def is_valid_pythoncoin_address(self, address):
        """Validate PythonCoin address format"""
        return (address and 
                len(address) >= 26 and 
                len(address) <= 35 and 
                address.isalnum())
    
    def stop(self):
        """Stop the enhanced server"""
        self.running = False
        if self.server:
            try:
                self.server.shutdown()
            except:
                pass
            self.server = None
        self.status_update.emit("Enhanced portal server stopped")



# ============================================================================
# Enhanced Advertisement Storage System
# ============================================================================

class AdStorageManager:
    """Manages saving and loading of advertisements as HTML/SVG files"""
    
    def __init__(self, base_dir="ads_storage"):
        self.base_dir = Path(base_dir)
        self.setup_directory_structure()
    
    def setup_directory_structure(self):
        """Create directory structure for ad storage"""
        directories = [
            self.base_dir,
            self.base_dir / "active",
            self.base_dir / "inactive", 
            self.base_dir / "templates",
            self.base_dir / "assets" / "images",
            self.base_dir / "assets" / "css",
            self.base_dir / "exports",
            self.base_dir / "analytics"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.create_default_templates()
    
    def create_default_templates(self):
        """Create default HTML/SVG ad templates"""
        
        # Enhanced HTML template with modern design
        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{AD_TITLE}} - PythonCoin Network</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        .pyc-ad-container {
            border: 2px solid #0066cc;
            border-radius: 16px;
            padding: 24px;
            background: linear-gradient(135deg, #ffffff 0%, #f8fffe 40%, #f0f9ff 100%);
            margin: 15px auto;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            max-width: 420px;
            font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            box-shadow: 0 8px 32px rgba(0,102,204,0.12);
            overflow: hidden;
        }
        
        .pyc-ad-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #ff6b35, #f7931e, #0066cc, #28a745);
            background-size: 300% 100%;
            animation: shimmer 3s ease-in-out infinite;
        }
        
        @keyframes shimmer {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .pyc-ad-container:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 20px 60px rgba(0,102,204,0.25);
            border-color: #0056b3;
        }
        
        .pyc-ad-badge {
            position: absolute;
            top: 16px;
            right: 16px;
            background: linear-gradient(45deg, #ff6b35, #f7931e);
            color: white;
            padding: 8px 16px;
            border-radius: 25px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 4px 15px rgba(255,107,53,0.4);
        }
        
        .pyc-ad-image {
            width: 100%;
            height: 180px;
            object-fit: cover;
            border-radius: 12px;
            margin-bottom: 16px;
            background: linear-gradient(45deg, #f0f9ff, #e0f2fe);
        }
        
        .pyc-ad-title {
            color: #0066cc;
            margin: 0 0 16px 0;
            font-size: 22px;
            font-weight: 800;
            line-height: 1.3;
            letter-spacing: -0.5px;
        }
        
        .pyc-ad-description {
            color: #374151;
            margin: 0 0 20px 0;
            font-size: 16px;
            line-height: 1.6;
            opacity: 0.9;
        }
        
        .pyc-ad-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid rgba(0,102,204,0.1);
        }
        
        .pyc-ad-category {
            color: #0066cc;
            font-weight: 600;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .pyc-ad-payout {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            padding: 10px 20px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 700;
            box-shadow: 0 4px 20px rgba(40,167,69,0.3);
            transition: all 0.3s ease;
        }
        
        .pyc-ad-payout:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 25px rgba(40,167,69,0.4);
        }
        
        .pyc-ad-stats {
            position: absolute;
            bottom: 12px;
            left: 12px;
            background: rgba(0,102,204,0.1);
            color: #0066cc;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 10px;
            font-weight: 600;
        }
        
        @media (max-width: 480px) {
            .pyc-ad-container {
                margin: 10px;
                padding: 20px;
            }
            
            .pyc-ad-title {
                font-size: 20px;
            }
            
            .pyc-ad-description {
                font-size: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="pyc-ad-container" onclick="handleAdClick('{{AD_ID}}')">
        <div class="pyc-ad-badge">💎 PYC Network</div>
        {{#AD_IMAGE_URL}}
        <img src="{{AD_IMAGE_URL}}" alt="{{AD_TITLE}}" class="pyc-ad-image" 
             onerror="this.style.display='none'">
        {{/AD_IMAGE_URL}}
        <h3 class="pyc-ad-title">{{AD_TITLE}}</h3>
        <p class="pyc-ad-description">{{AD_DESCRIPTION}}</p>
        <div class="pyc-ad-footer">
            <span class="pyc-ad-category">
                <span>📱</span>
                <span>{{AD_CATEGORY}} • P2P Network</span>
            </span>
            <span class="pyc-ad-payout" id="payout-{{AD_ID}}">
                +{{AD_PAYOUT}} PYC
            </span>
        </div>
        <div class="pyc-ad-stats">
            ID: {{AD_ID_SHORT}}
        </div>
    </div>
    
    <script>
        // Enhanced click tracking
        function handleAdClick(adId) {
            console.log('[PYC] Ad clicked:', adId);
            
            // Animate payout button
            const payoutBtn = document.getElementById('payout-' + adId);
            if (payoutBtn) {
                payoutBtn.style.transform = 'scale(1.2)';
                payoutBtn.innerHTML = '✅ Earning...';
                setTimeout(() => {
                    payoutBtn.style.transform = 'scale(1)';
                    payoutBtn.innerHTML = '+{{AD_PAYOUT}} PYC';
                }, 1000);
            }
            
            // Track click with wallet
            if (window.pythonCoinWallet) {
                window.pythonCoinWallet.recordClick(adId, {
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent,
                    viewportSize: window.innerWidth + 'x' + window.innerHeight
                });
            }
            
            // Send to analytics
            fetch('/api/analytics/click', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    ad_id: adId,
                    timestamp: new Date().toISOString(),
                    payout_amount: parseFloat('{{AD_PAYOUT}}')
                })
            }).catch(console.warn);
            
            // Open click URL with delay
            setTimeout(() => {
                const clickUrl = '{{AD_CLICK_URL}}';
                if (clickUrl && clickUrl !== '#') {
                    window.open(clickUrl, '_blank', 'noopener,noreferrer');
                }
            }, 500);
        }
        
        // Track impression
        if (window.pythonCoinWallet) {
            window.pythonCoinWallet.recordImpression('{{AD_ID}}');
        }
        
        // Analytics impression tracking
        fetch('/api/analytics/impression', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                ad_id: '{{AD_ID}}',
                timestamp: new Date().toISOString()
            })
        }).catch(console.warn);
    </script>
</body>
</html>"""
        
        # SVG template with animations
        svg_template = """<svg width="400" height="280" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#ffffff"/>
            <stop offset="50%" style="stop-color:#f8fffe"/>
            <stop offset="100%" style="stop-color:#f0f9ff"/>
        </linearGradient>
        <linearGradient id="badgeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#ff6b35"/>
            <stop offset="100%" style="stop-color:#f7931e"/>
        </linearGradient>
        <linearGradient id="payoutGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#28a745"/>
            <stop offset="100%" style="stop-color:#20c997"/>
        </linearGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#0066cc" flood-opacity="0.15"/>
        </filter>
    </defs>
    
    <!-- Main container with animation -->
    <rect x="8" y="8" width="384" height="264" rx="16" ry="16" 
          fill="url(#bgGrad)" stroke="#0066cc" stroke-width="2" filter="url(#shadow)">
        <animate attributeName="stroke-width" values="2;3;2" dur="3s" repeatCount="indefinite"/>
    </rect>
    
    <!-- Animated top border -->
    <rect x="8" y="8" width="384" height="4" rx="2" ry="2">
        <animate attributeName="fill" values="#ff6b35;#f7931e;#0066cc;#28a745;#ff6b35" dur="5s" repeatCount="indefinite"/>
    </rect>
    
    <!-- Badge -->
    <rect x="300" y="20" width="85" height="28" rx="14" ry="14" fill="url(#badgeGrad)"/>
    <text x="342" y="37" text-anchor="middle" fill="white" font-family="Arial, sans-serif" 
          font-size="11" font-weight="bold">💎 PYC</text>
    
    <!-- Title -->
    <text x="24" y="60" fill="#0066cc" font-family="Arial, sans-serif" font-size="22" font-weight="bold">
        {{AD_TITLE}}
    </text>
    
    <!-- Description -->
    <foreignObject x="24" y="75" width="350" height="80">
        <div xmlns="http://www.w3.org/1999/xhtml" 
             style="color: #374151; font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6;">
            {{AD_DESCRIPTION}}
        </div>
    </foreignObject>
    
    <!-- Category -->
    <text x="24" y="200" fill="#0066cc" font-family="Arial, sans-serif" 
          font-size="14" font-weight="600">📱 {{AD_CATEGORY}} • 🌐 P2P Network</text>
    
    <!-- Payout button with hover effect -->
    <g id="payoutButton">
        <rect x="280" y="180" width="110" height="35" rx="17" ry="17" fill="url(#payoutGrad)" filter="url(#shadow)">
            <animate attributeName="y" values="180;178;180" dur="2s" repeatCount="indefinite"/>
        </rect>
        <text x="335" y="200" text-anchor="middle" fill="white" font-family="Arial, sans-serif" 
              font-size="13" font-weight="bold">+{{AD_PAYOUT}} PYC</text>
    </g>
    
    <!-- Stats -->
    <rect x="20" y="240" width="120" height="24" rx="12" ry="12" 
          fill="rgba(0,102,204,0.1)" stroke="rgba(0,102,204,0.3)" stroke-width="1"/>
    <text x="80" y="254" text-anchor="middle" fill="#0066cc" font-family="Arial, sans-serif" 
          font-size="10" font-weight="600">ID: {{AD_ID_SHORT}}</text>
    
    <!-- Click area -->
    <rect x="0" y="0" width="400" height="280" fill="transparent" style="cursor: pointer"
          onclick="handleAdClick('{{AD_ID}}')"/>
    
    <script type="application/ecmascript"><![CDATA[
        function handleAdClick(adId) {
            if (window.pythonCoinWallet) {
                window.pythonCoinWallet.recordClick(adId);
            }
            
            const clickUrl = '{{AD_CLICK_URL}}';
            if (clickUrl && clickUrl !== '#') {
                window.open(clickUrl, '_blank');
            }
        }
    ]]></script>
</svg>"""
        
        # Save templates
        templates = {
            'enhanced_html.template': html_template,
            'enhanced_svg.template': svg_template
        }
        
        for filename, template_content in templates.items():
            template_path = self.base_dir / "templates" / filename
            if not template_path.exists():
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(template_content)
    
    def save_ad(self, ad_data, format_type='html'):
        """Save advertisement as HTML or SVG file with enhanced features"""
        try:
            ad_id = ad_data.get('id', str(uuid.uuid4()))
            
            # Enhanced metadata
            metadata = {
                'id': ad_id,
                'title': ad_data.get('title', ''),
                'description': ad_data.get('description', ''),
                'category': ad_data.get('category', 'general'),
                'click_url': ad_data.get('click_url', '#'),
                'image_url': ad_data.get('image_url', ''),
                'payout_rate': ad_data.get('payout_rate', 0.001),
                'advertiser_address': ad_data.get('advertiser_address', ''),
                'targeting': ad_data.get('targeting', {}),
                'created_at': ad_data.get('created_at', datetime.now().isoformat()),
                'expires_at': ad_data.get('expires_at', ''),
                'status': 'active',
                'format': format_type,
                'click_count': 0,
                'impression_count': 0,
                'revenue_generated': 0.0,
                'conversion_rate': 0.0
            }
            
            # Generate content
            if format_type == 'html':
                content = self.generate_html_ad(metadata)
                file_extension = '.html'
            elif format_type == 'svg':
                content = self.generate_svg_ad(metadata)
                file_extension = '.svg'
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            # Save files
            filename = f"{ad_id}_{format_type}{file_extension}"
            file_path = self.base_dir / "active" / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            metadata['file_path'] = str(file_path)
            
            # Save metadata
            metadata_path = self.base_dir / "active" / f"{ad_id}_meta.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            return {
                'success': True,
                'ad_id': ad_id,
                'file_path': str(file_path),
                'metadata_path': str(metadata_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_html_ad(self, metadata):
        """Generate enhanced HTML ad from template"""
        template_path = self.base_dir / "templates" / "enhanced_html.template"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except:
            template = "<div><h3>{{AD_TITLE}}</h3><p>{{AD_DESCRIPTION}}</p></div>"
        
        # Enhanced replacements
        replacements = {
            '{{AD_ID}}': metadata['id'],
            '{{AD_ID_SHORT}}': metadata['id'][:8],
            '{{AD_TITLE}}': metadata['title'],
            '{{AD_DESCRIPTION}}': metadata['description'],
            '{{AD_CATEGORY}}': metadata['category'].title(),
            '{{AD_CLICK_URL}}': metadata['click_url'],
            '{{AD_PAYOUT}}': f"{metadata['payout_rate']:.8f}",
            '{{AD_IMAGE_URL}}': metadata.get('image_url', ''),
            '{{#AD_IMAGE_URL}}': '' if metadata.get('image_url') else '<!--',
            '{{/AD_IMAGE_URL}}': '' if metadata.get('image_url') else '-->'
        }
        
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, str(value))
        
        return template
    
    def generate_svg_ad(self, metadata):
        """Generate enhanced SVG ad from template"""
        template_path = self.base_dir / "templates" / "enhanced_svg.template"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except:
            template = '<svg><text>{{AD_TITLE}}</text></svg>'
        
        # Truncate text for SVG
        title = metadata['title'][:25] + ('...' if len(metadata['title']) > 25 else '')
        description = metadata['description'][:80] + ('...' if len(metadata['description']) > 80 else '')
        
        replacements = {
            '{{AD_ID}}': metadata['id'],
            '{{AD_ID_SHORT}}': metadata['id'][:8],
            '{{AD_TITLE}}': title,
            '{{AD_DESCRIPTION}}': description,
            '{{AD_CATEGORY}}': metadata['category'].title(),
            '{{AD_CLICK_URL}}': metadata['click_url'],
            '{{AD_PAYOUT}}': f"{metadata['payout_rate']:.8f}"
        }
        
        for placeholder, value in replacements.items():
                    # Enhanced SVG template with image support
            svg_template = """<svg width="400" height="280" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <defs>
        <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#ffffff"/>
            <stop offset="50%" style="stop-color:#f8fffe"/>
            <stop offset="100%" style="stop-color:#f0f9ff"/>
        </linearGradient>
        <linearGradient id="badgeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#ff6b35"/>
            <stop offset="100%" style="stop-color:#f7931e"/>
        </linearGradient>
        <linearGradient id="payoutGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#28a745"/>
            <stop offset="100%" style="stop-color:#20c997"/>
        </linearGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#0066cc" flood-opacity="0.15"/>
        </filter>
        <pattern id="bgImage" patternUnits="userSpaceOnUse" width="400" height="280">
            <rect width="400" height="280" fill="url(#bgGrad)"/>
            {{#AD_IMAGE_URL}}
            <image href="{{AD_IMAGE_URL}}" x="0" y="0" width="400" height="280" opacity="0.3" preserveAspectRatio="xMidYMid slice"/>
            {{/AD_IMAGE_URL}}
        </pattern>
    </defs>
    
    <!-- Main container with image background -->
    <rect x="8" y="8" width="384" height="264" rx="16" ry="16" 
          fill="url(#bgImage)" stroke="#0066cc" stroke-width="2" filter="url(#shadow)">
        <animate attributeName="stroke-width" values="2;3;2" dur="3s" repeatCount="indefinite"/>
    </rect>
    
    <!-- Semi-transparent overlay for text readability -->
    <rect x="8" y="8" width="384" height="264" rx="16" ry="16" 
          fill="rgba(255,255,255,0.85)" stroke="none"/>
    
    <!-- Animated top border -->
    <rect x="8" y="8" width="384" height="4" rx="2" ry="2">
        <animate attributeName="fill" values="#ff6b35;#f7931e;#0066cc;#28a745;#ff6b35" dur="5s" repeatCount="indefinite"/>
    </rect>
    
    <!-- Badge -->
    <rect x="300" y="20" width="85" height="28" rx="14" ry="14" fill="url(#badgeGrad)"/>
    <text x="342" y="37" text-anchor="middle" fill="white" font-family="Arial, sans-serif" 
          font-size="11" font-weight="bold">💎 PYC</text>
    
    <!-- Title with background for readability -->
    <rect x="20" y="45" width="360" height="25" rx="4" ry="4" fill="rgba(255,255,255,0.9)"/>
    <text x="24" y="62" fill="#0066cc" font-family="Arial, sans-serif" font-size="22" font-weight="bold">
        {{AD_TITLE}}
    </text>
    
    <!-- Description with background -->
    <rect x="20" y="75" width="360" height="80" rx="4" ry="4" fill="rgba(255,255,255,0.9)"/>
    <foreignObject x="24" y="80" width="350" height="70">
        <div xmlns="http://www.w3.org/1999/xhtml" 
             style="color: #374151; font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6; padding: 5px;">
            {{AD_DESCRIPTION}}
        </div>
    </foreignObject>
    
    <!-- Category -->
    <rect x="20" y="190" width="250" height="20" rx="4" ry="4" fill="rgba(255,255,255,0.9)"/>
    <text x="24" y="203" fill="#0066cc" font-family="Arial, sans-serif" 
          font-size="14" font-weight="600">📱 {{AD_CATEGORY}} • 🌐 P2P Network</text>
    
    <!-- Payout button with hover effect -->
    <g id="payoutButton">
        <rect x="280" y="180" width="110" height="35" rx="17" ry="17" fill="url(#payoutGrad)" filter="url(#shadow)">
            <animate attributeName="y" values="180;178;180" dur="2s" repeatCount="indefinite"/>
        </rect>
        <text x="335" y="200" text-anchor="middle" fill="white" font-family="Arial, sans-serif" 
              font-size="13" font-weight="bold">+{{AD_PAYOUT}} PYC</text>
    </g>
    
    <!-- Stats -->
    <rect x="20" y="240" width="120" height="24" rx="12" ry="12" 
          fill="rgba(0,102,204,0.9)" stroke="rgba(0,102,204,0.3)" stroke-width="1"/>
    <text x="80" y="254" text-anchor="middle" fill="white" font-family="Arial, sans-serif" 
          font-size="10" font-weight="600">ID: {{AD_ID_SHORT}}</text>
    
    <!-- Click area -->
    <rect x="0" y="0" width="400" height="280" fill="transparent" style="cursor: pointer"
          onclick="handleAdClick('{{AD_ID}}')"/>
    
    <script type="application/ecmascript"><![CDATA[
        function handleAdClick(adId) {
            if (window.pythonCoinWallet) {
                window.pythonCoinWallet.recordClick(adId);
            }
            
            const clickUrl = '{{AD_CLICK_URL}}';
            if (clickUrl && clickUrl !== '#') {
                window.open(clickUrl, '_blank');
            }
        }
    ]]></script>
</svg>"""
        
        # Prepare image handling
        image_url = metadata.get('image_url', '')
        
        # Convert local file paths to data URLs for embedding
        if image_url and image_url.startswith('file://'):
            try:
                import base64
                from pathlib import Path
                
                file_path = image_url.replace('file://', '')
                if Path(file_path).exists():
                    with open(file_path, 'rb') as img_file:
                        img_data = base64.b64encode(img_file.read()).decode()
                        file_ext = Path(file_path).suffix.lower()
                        
                        # Determine MIME type
                        mime_types = {
                            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                            '.png': 'image/png', '.gif': 'image/gif',
                            '.webp': 'image/webp', '.svg': 'image/svg+xml'
                        }
                        mime_type = mime_types.get(file_ext, 'image/png')
                        
                        # Create data URL
                        image_url = f"data:{mime_type};base64,{img_data}"
                else:
                    image_url = ""  # File not found
            except Exception as e:
                print(f"Error processing image: {e}")
                image_url = ""
        
        # Enhanced replacements with image support
        replacements = {
            '{{AD_ID}}': metadata['id'],
            '{{AD_ID_SHORT}}': metadata['id'][:8],
            '{{AD_TITLE}}': metadata['title'][:30] + ('...' if len(metadata['title']) > 30 else ''),
            '{{AD_DESCRIPTION}}': metadata['description'][:100] + ('...' if len(metadata['description']) > 100 else ''),
            '{{AD_CATEGORY}}': metadata['category'].title(),
            '{{AD_CLICK_URL}}': metadata['click_url'],
            '{{AD_PAYOUT}}': f"{metadata['payout_rate']:.8f}",
            '{{AD_IMAGE_URL}}': image_url,
            '{{#AD_IMAGE_URL}}': '' if image_url else '<!--',
            '{{/AD_IMAGE_URL}}': '' if image_url else '-->'
        }
        
        # Apply replacements
        for placeholder, value in replacements.items():
            svg_template = svg_template.replace(placeholder, str(value))
        
        return svg_template
        
        return template
    
    def load_all_ads(self):
        """Load all active advertisements"""
        ads = []
        active_dir = self.base_dir / "active"
        
        try:
            for metadata_file in active_dir.glob("*_meta.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                ads.append(metadata)
        except Exception as e:
            pass
        
        return ads
    
    def update_ad_stats(self, ad_id, clicks=0, impressions=0):
        """Update advertisement statistics"""
        try:
            metadata_file = self.base_dir / "active" / f"{ad_id}_meta.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                metadata['click_count'] = metadata.get('click_count', 0) + clicks
                metadata['impression_count'] = metadata.get('impression_count', 0) + impressions
                metadata['last_updated'] = datetime.now().isoformat()
                
                if metadata['impression_count'] > 0:
                    metadata['conversion_rate'] = metadata['click_count'] / metadata['impression_count']
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
                
                return True
        except:
            pass
        
        return False
    
    def get_storage_stats(self):
        """Get comprehensive storage statistics"""
        try:
            active_ads = len(list((self.base_dir / "active").glob("*_meta.json")))
            inactive_ads = len(list((self.base_dir / "inactive").glob("*_meta.json")))
            total_size = sum(f.stat().st_size for f in self.base_dir.rglob("*") if f.is_file())
            
            return {
                'active_ads': active_ads,
                'inactive_ads': inactive_ads,
                'total_ads': active_ads + inactive_ads,
                'storage_size_bytes': total_size,
                'storage_size_mb': total_size / (1024 * 1024),
                'base_directory': str(self.base_dir)
            }
        except:
            return {}



# Enhanced Ad Fetcher and Developer Registration - Injected Enhancement
class EnhancedAdFetcher:
    """Fetches real ads from storage, P2P network, and database instead of placeholders"""
    
    def __init__(self, wallet_instance):
        self.wallet = wallet_instance
        self.cached_ads = []
        self.cache_timestamp = 0
        self.cache_duration = 30
        
    def get_real_ads(self, category_filter=None, limit=10):
        """Get real advertisements from all available sources"""
        try:
            current_time = time.time()
            if (current_time - self.cache_timestamp < self.cache_duration and self.cached_ads):
                return self._filter_ads(self.cached_ads, category_filter, limit)
            
            all_ads = []
            all_ads.extend(self._load_from_storage())
            all_ads.extend(self._load_from_p2p_network())
            all_ads.extend(self._load_from_database())
            
            if not all_ads:
                all_ads = self._generate_realistic_fallback_ads()
            
            unique_ads = self._remove_duplicates(all_ads)
            self.cached_ads = unique_ads
            self.cache_timestamp = current_time
            
            return self._filter_ads(unique_ads, category_filter, limit)
            
        except Exception as e:
            self.wallet.log_message(f"❌ Error fetching real ads: {str(e)}")
            return self._generate_realistic_fallback_ads()
    
    def _load_from_storage(self):
        """Load ads from file storage"""
        try:
            if hasattr(self.wallet, 'ad_storage'):
                stored_ads = self.wallet.ad_storage.load_all_ads()
                formatted_ads = []
                for ad_meta in stored_ads:
                    formatted_ad = {
                        'id': ad_meta['id'],
                        'title': ad_meta['title'],
                        'description': ad_meta['description'],
                        'category': ad_meta['category'],
                        'payout_rate': ad_meta['payout_rate'],
                        'click_url': ad_meta['click_url'],
                        'image_url': ad_meta.get('image_url', ''),
                        'advertiser_address': ad_meta['advertiser_address'],
                        'created_at': ad_meta['created_at'],
                        'expires_at': ad_meta.get('expires_at', ''),
                        'source': 'local_storage',
                        'status': 'active'
                    }
                    formatted_ads.append(formatted_ad)
                self.wallet.log_message(f"📁 Loaded {len(formatted_ads)} ads from storage")
                return formatted_ads
        except Exception as e:
            self.wallet.log_message(f"⚠️ Error loading from storage: {str(e)}")
        return []
    
    def _load_from_p2p_network(self):
        """Load ads from P2P network"""
        try:
            if hasattr(self.wallet, 'ads') and self.wallet.ads:
                p2p_ads = []
                for ad in self.wallet.ads:
                    if hasattr(ad, 'to_dict'):
                        ad_dict = ad.to_dict()
                    else:
                        ad_dict = ad.__dict__
                    
                    formatted_ad = {
                        'id': ad_dict.get('id', ''),
                        'title': ad_dict.get('title', 'Untitled Ad'),
                        'description': ad_dict.get('description', ''),
                        'category': ad_dict.get('category', 'general'),
                        'payout_rate': ad_dict.get('payout_rate', 0.001),
                        'click_url': ad_dict.get('click_url', '#'),
                        'image_url': ad_dict.get('image_url', ''),
                        'advertiser_address': ad_dict.get('advertiser_address', ''),
                        'created_at': ad_dict.get('created_at', ''),
                        'expires_at': ad_dict.get('expires_at', ''),
                        'source': 'p2p_network',
                        'peer_source': ad_dict.get('peer_source', 'unknown')
                    }
                    p2p_ads.append(formatted_ad)
                self.wallet.log_message(f"🌐 Loaded {len(p2p_ads)} ads from P2P network")
                return p2p_ads
        except Exception as e:
            self.wallet.log_message(f"⚠️ Error loading from P2P: {str(e)}")
        return []
    
    def _load_from_database(self):
        """Load ads from database"""
        try:
            if (hasattr(self.wallet, 'db_manager') and 
                self.wallet.db_manager and 
                self.wallet.db_connected):
                
                db_ads = self.wallet.db_manager.get_active_ads()
                formatted_ads = []
                for ad in db_ads:
                    formatted_ad = {
                        'id': ad.get('ad_id', ''),
                        'title': ad.get('title', 'Database Ad'),
                        'description': ad.get('description', ''),
                        'category': ad.get('category', 'general'),
                        'payout_rate': float(ad.get('payout_rate', 0.001)),
                        'click_url': ad.get('click_url', '#'),
                        'image_url': ad.get('image_url', ''),
                        'advertiser_address': ad.get('advertiser_address', ''),
                        'created_at': ad.get('created_at', ''),
                        'expires_at': ad.get('expires_at', ''),
                        'source': 'database',
                        'client_name': ad.get('client_name', 'Unknown')
                    }
                    formatted_ads.append(formatted_ad)
                self.wallet.log_message(f"🗄️ Loaded {len(formatted_ads)} ads from database")
                return formatted_ads
        except Exception as e:
            self.wallet.log_message(f"⚠️ Error loading from database: {str(e)}")
        return []
    
    def _generate_realistic_fallback_ads(self):
        """Generate realistic fallback ads only when no real ads exist"""
        current_time = int(time.time() * 1000)
        wallet_addr = self.wallet.wallet.address if self.wallet.wallet else "demo_address"
        
        fallback_ads = [
            {
                'id': f'demo_ad_crypto_{current_time}',
                'title': 'Start Your Crypto Journey',
                'description': 'Learn about cryptocurrency mining and earning with secure, decentralized networks.',
                'category': 'cryptocurrency',
                'payout_rate': 0.002,
                'click_url': 'https://learn-crypto.example.com',
                'image_url': '',
                'advertiser_address': wallet_addr,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
                'source': 'fallback',
                'status': 'demo'
            }
        ]
        self.wallet.log_message(f"📝 Generated {len(fallback_ads)} fallback demo ads")
        return fallback_ads
    
    def _remove_duplicates(self, ads):
        """Remove duplicate ads based on ID"""
        seen_ids = set()
        unique_ads = []
        for ad in ads:
            ad_id = ad.get('id', '')
            if ad_id and ad_id not in seen_ids:
                seen_ids.add(ad_id)
                unique_ads.append(ad)
        return unique_ads
    
    def _filter_ads(self, ads, category_filter=None, limit=10):
        """Filter and limit ads"""
        filtered_ads = ads
        if category_filter and category_filter != 'all':
            filtered_ads = [ad for ad in ads 
                          if ad.get('category', '').lower() == category_filter.lower()]
        try:
            filtered_ads.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        except:
            pass
        return filtered_ads[:limit]

class EnhancedDeveloperRegistration:
    """Manages online developer registration and status tracking"""
    
    def __init__(self, wallet_instance):
        self.wallet = wallet_instance
        self.registered_developers = {}
        self.online_developers = {}
        self.last_activity = {}
        
    def register_developer(self, developer_name, wallet_address, session_info=None):
        """Register a developer and track their session"""
        try:
            self.registered_developers[developer_name] = {
                'wallet_address': wallet_address,
                'registered_at': datetime.now().isoformat(),
                'total_clicks': 0,
                'total_earnings': 0.0,
                'last_seen': datetime.now().isoformat(),
                'session_info': session_info or {}
            }
            
            self.mark_developer_online(developer_name, session_info)
            self.wallet.log_message(f"👤 Developer registered: {developer_name} -> {wallet_address[:8]}...")
            
            # Update UI
            if hasattr(self.wallet, 'update_developers_table_enhanced'):
                QTimer.singleShot(100, self.wallet.update_developers_table_enhanced)
            return True
        except Exception as e:
            self.wallet.log_message(f"❌ Error registering developer: {str(e)}")
            return False
    
    def mark_developer_online(self, developer_name, session_info=None):
        """Mark developer as online"""
        try:
            self.online_developers[developer_name] = {
                'online_since': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'session_info': session_info or {}
            }
            self.last_activity[developer_name] = datetime.now().timestamp()
            
            if hasattr(self.wallet, 'update_developers_table_enhanced'):
                QTimer.singleShot(100, self.wallet.update_developers_table_enhanced)
        except Exception as e:
            self.wallet.log_message(f"❌ Error marking developer online: {str(e)}")
    
    def mark_developer_offline(self, developer_name):
        """Mark developer as offline"""
        try:
            if developer_name in self.online_developers:
                del self.online_developers[developer_name]
            
            if developer_name in self.registered_developers:
                self.registered_developers[developer_name]['last_seen'] = datetime.now().isoformat()
            
            if hasattr(self.wallet, 'update_developers_table_enhanced'):
                QTimer.singleShot(100, self.wallet.update_developers_table_enhanced)
        except Exception as e:
            self.wallet.log_message(f"❌ Error marking developer offline: {str(e)}")
    
    def update_developer_activity(self, developer_name):
        """Update developer's last activity timestamp"""
        try:
            self.last_activity[developer_name] = datetime.now().timestamp()
            if developer_name in self.online_developers:
                self.online_developers[developer_name]['last_activity'] = datetime.now().isoformat()
        except Exception as e:
            self.wallet.log_message(f"❌ Error updating developer activity: {str(e)}")
    
    def record_developer_click(self, developer_name, amount):
        """Record a click and earnings for a developer"""
        try:
            if developer_name in self.registered_developers:
                self.registered_developers[developer_name]['total_clicks'] += 1
                self.registered_developers[developer_name]['total_earnings'] += amount
                self.registered_developers[developer_name]['last_seen'] = datetime.now().isoformat()
                
                self.update_developer_activity(developer_name)
                
                if hasattr(self.wallet, 'update_developers_table_enhanced'):
                    QTimer.singleShot(100, self.wallet.update_developers_table_enhanced)
        except Exception as e:
            self.wallet.log_message(f"❌ Error recording developer click: {str(e)}")
    
    def cleanup_offline_developers(self):
        """Clean up developers who haven't been active for 5 minutes"""
        try:
            current_time = datetime.now().timestamp()
            offline_threshold = 300  # 5 minutes
            
            offline_devs = []
            for dev_name, last_time in self.last_activity.items():
                if current_time - last_time > offline_threshold:
                    offline_devs.append(dev_name)
            
            for dev_name in offline_devs:
                self.mark_developer_offline(dev_name)
            
            if offline_devs:
                self.wallet.log_message(f"🔄 Marked {len(offline_devs)} developers as offline")
        except Exception as e:
            self.wallet.log_message(f"❌ Error cleaning up offline developers: {str(e)}")



class UnifiedPythonCoinWallet(QMainWindow):
    """Enhanced Unified PythonCoin wallet with proper genesis coordination"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize basic properties first
        self.db_manager = DatabaseManager()
        self.db_connected = False
        self.db_registration = None
        
        # Core components
        self.blockchain = None
        self.wallet = None
        self.node = None
        
        # P2P Ad Network components
        self.client_id = str(uuid.uuid4())[:8]
        # P2P Ad Network components with validated port
        self.client_id = str(uuid.uuid4())[:8]
        try:
            self.port = self.validate_port(8082, 8082)  # Ensure port is always valid integer
        except:
            self.port = 8082  # Fallback if validation method not available yet
        
        # Developer Portal Integration
        self.portal_server = None
        self.portal_enabled = False
        self.p2p_manager = None
        self.js_generator = None
        
        # Mining and networking
        self.mining_thread = None
        self.network_thread = None
        
        # Ad network data
        self.peers: Dict[str, PeerInfo] = {}
        self.ads: List[AdContent] = []
        self.user_sessions: Dict[str, Dict] = {}
        self.click_events: List[ClickEvent] = []
        
        # Stats
        self.stats = {
            'ads_served': 0,
            'impressions': 0,
            'clicks': 0,
            'payments_sent': 0,
            'revenue_generated': 0.0,
            'blocks_mined': 0,
            'uptime_start': time.time()
        }
        
                
        # Enhanced Ad Storage System
        self.ad_storage = AdStorageManager()
        
        # Initialize UI FIRST
        self.init_ui()
        
        # Initialize database with proper registration
        self.init_database()
        
        # Load blockchain and wallet
        if not self.load_blockchain():
            self.blockchain = Blockchain()
            self.log_message("Created new blockchain")
        
        self.load_wallet()
        self.load_wallet_state()        
        # Load saved advertisements from storage
        self.load_saved_ads()
        
        

        # Enhanced database initialization
        try:
            self.enhanced_db_manager = EnhancedDatabaseManager()
            self.log_message("✅ Enhanced database manager initialized")
        except Exception as e:
            self.log_message(f"⚠️ Enhanced database manager failed: {str(e)}")
            self.enhanced_db_manager = None

        # Initialize P2P components
        self.init_p2p_components()
        
        # Setup timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(5000)
        
        QTimer.singleShot(1000, self.delayed_initial_update)
        self.setup_auto_save_timer()
        
        # Initialize enhanced ad system
        QTimer.singleShot(3000, self.initialize_enhanced_ad_system)
    def start_node(self):
        """Start blockchain node - wrapper for enhanced version"""
        try:
            # Call the enhanced node server method if it exists
            if hasattr(self, 'start_enhanced_node_server'):
                self.start_enhanced_node_server()
            else:
                # Fallback to original implementation
                if self.node:
                    return
                
                host = "0.0.0.0"
                port = 5000
                
                if hasattr(self, 'node_host') and self.node_host:
                    host_text = self.node_host.text().strip()
                    if host_text:
                        host = host_text
                
                if hasattr(self, 'node_port') and self.node_port:
                    try:
                        port = self.get_safe_port_from_ui(self.node_port, 5000)
                    except:
                        port = 5000
                
                self.log_message(f"🚀 Starting node on {host}:{port}")
                
                # Create enhanced node
                self.node = EnhancedPythonCoinNode(
                    host=host, 
                    port=port, 
                    blockchain=self.blockchain, 
                    wallet=self.wallet,
                    main_wallet_instance=self
                )
                
                # Start node in thread
                threading.Thread(target=self.node.start, daemon=True).start()
                
                if hasattr(self, 'node_status'):
                    self.node_status.setText(f"Status: Enhanced node running on {host}:{port}")
                if hasattr(self, 'start_node_button'):
                    self.start_node_button.setEnabled(False)
                if hasattr(self, 'stop_node_button'):
                    self.stop_node_button.setEnabled(True)
                
                self.log_message(f"✅ Enhanced node started")
                
        except Exception as e:
            self.log_message(f"❌ Error starting node: {str(e)}")
    def validate_port(self, port_value, default_port=8082):
        """Validate and convert port value to integer"""
        try:
            # Handle various input types
            if isinstance(port_value, str):
                # Remove any whitespace
                port_value = port_value.strip()
                
                # Handle empty string
                if not port_value:
                    self.log_message(f"⚠️ Empty port value, using default: {default_port}")
                    return default_port
                
                # Convert to integer
                port_int = int(port_value)
            elif isinstance(port_value, (int, float)):
                port_int = int(port_value)
            else:
                self.log_message(f"⚠️ Invalid port type {type(port_value)}, using default: {default_port}")
                return default_port
            
            # Validate port range
            if port_int < 1024 or port_int > 65535:
                self.log_message(f"⚠️ Port {port_int} out of range (1024-65535), using default: {default_port}")
                return default_port
            
            return port_int
            
        except (ValueError, TypeError) as e:
            self.log_message(f"⚠️ Port validation error: {str(e)}, using default: {default_port}")
            return default_port
    
    def get_safe_port_from_ui(self, ui_element=None, default_port=8082):
        """Safely get port value from UI element"""
        try:
            if ui_element is None:
                return default_port
            
            # Handle different UI element types
            if hasattr(ui_element, 'value'):
                # QSpinBox
                port_value = ui_element.value()
            elif hasattr(ui_element, 'text'):
                # QLineEdit
                port_value = ui_element.text()
            else:
                # Unknown type
                self.log_message(f"⚠️ Unknown UI element type: {type(ui_element)}")
                return default_port
            
            return self.validate_port(port_value, default_port)
            
        except Exception as e:
            self.log_message(f"⚠️ Error getting port from UI: {str(e)}")
            return default_port



    def load_saved_ads(self):
        """Load saved ads from storage with enhanced error handling"""
        try:
            saved_ads = self.ad_storage.load_all_ads()
            
            loaded_ads = []
            for ad_metadata in saved_ads:
                try:
                    ad = AdContent(
                        id=ad_metadata['id'],
                        title=ad_metadata['title'],
                        description=ad_metadata['description'],
                        image_url=ad_metadata.get('image_url', ''),
                        click_url=ad_metadata['click_url'],
                        category=ad_metadata['category'],
                        targeting=ad_metadata.get('targeting', {}),
                        created_at=ad_metadata['created_at'],
                        expires_at=ad_metadata.get('expires_at', ''),
                        peer_source=ad_metadata.get('peer_source', self.client_id),
                        payout_rate=ad_metadata['payout_rate'],
                        advertiser_address=ad_metadata['advertiser_address']
                    )
                    loaded_ads.append(ad)
                except Exception as e:
                    self.log_message(f"⚠️ Error loading ad {ad_metadata.get('id', 'unknown')}: {str(e)}")
                    continue
            
            self.ads = loaded_ads
            self.log_message(f"✅ Loaded {len(self.ads)} saved advertisements from storage")
            
            # Schedule UI update
            if hasattr(self, 'update_my_ads_table'):
                QTimer.singleShot(1000, self.update_my_ads_table)
            
        except Exception as e:
            self.log_message(f"❌ Error loading saved ads: {str(e)}")
            self.ads = []

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("PythonCoin P2P Ad Network Wallet")
        self.setGeometry(100, 100, 1200, 800)
        
        # Apply unified stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: 2px solid #0066cc;
                background-color: #ffffff;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #0066cc;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: #0066cc;
                color: white;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #0066cc;
            }
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #0066cc;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar - more robust version
        try:
            self.statusBar = QStatusBar()
            self.setStatusBar(self.statusBar)
            self.statusBar.showMessage("Welcome to PythonCoin P2P Ad Network Wallet")
        except Exception as e:
            print(f"Status bar initialization error: {e}")
            # Create a simple fallback
            self.statusBar = None
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        # Create wallet header
        self.create_wallet_header()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_wallet_tab()
        self.create_mining_tab()
        self.create_network_tab()
        self.create_ad_creation_tab()
        self.create_developer_portal_tab()
        # Create transaction queue management tab
        self.create_transaction_queue_tab()

    def log_message(self, message: str):
        """Log message to console and status bar - defensive version"""
        logger.info(message)
        
        # Only try to update status bar if UI is initialized
        if hasattr(self, 'statusBar') and self.statusBar and hasattr(self.statusBar, 'showMessage'):
            try:
                self.statusBar.showMessage(message, 5000)
            except (AttributeError, RuntimeError):
                # Fallback if status bar isn't properly initialized yet
                pass
        
        # Also log to network log if available
        if hasattr(self, 'network_log') and hasattr(self.network_log, 'append'):
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.network_log.append(f"[{timestamp}] {message}")
                self.network_log.ensureCursorVisible()
            except:
                pass

    def init_ui(self):
        """Initialize the user interface (same as before but with genesis status)"""
        self.setWindowTitle("PythonCoin P2P Ad Network Wallet")
        self.setGeometry(100, 100, 1200, 800)
        
        # Apply unified stylesheet (same as before)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: 2px solid #0066cc;
                background-color: #ffffff;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #0066cc;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: #0066cc;
                color: white;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #0066cc;
            }
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #0066cc;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Welcome to PythonCoin P2P Ad Network Wallet")
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        # Create wallet header
        self.create_wallet_header()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_wallet_tab()
        self.create_mining_tab()
        self.create_network_tab()
        self.create_ad_creation_tab()
        self.create_developer_portal_tab()
        # Create transaction queue management tab
        self.create_transaction_queue_tab()
    
    def create_menu_bar(self):
        """Create the menu bar (same as before)"""
        menu_bar = self.menuBar()
        
        # Wallet menu
        wallet_menu = menu_bar.addMenu("Wallet")
        
        new_wallet_action = QAction("New Wallet", self)
        new_wallet_action.triggered.connect(self.create_new_wallet)
        wallet_menu.addAction(new_wallet_action)
        
        import_wallet_action = QAction("Import Wallet", self)
        import_wallet_action.triggered.connect(self.import_wallet)
        wallet_menu.addAction(import_wallet_action)
        
        export_wallet_action = QAction("Export Wallet", self)
        export_wallet_action.triggered.connect(self.export_wallet)
        wallet_menu.addAction(export_wallet_action)
        
        wallet_menu.addSeparator()
        
        backup_action = QAction("Backup Data", self)
        backup_action.triggered.connect(self.backup_all_data)
        wallet_menu.addAction(backup_action)
        
        # P2P Network menu
        network_menu = menu_bar.addMenu("P2P Network")
        
        start_network_action = QAction("Start Ad Network", self)
        start_network_action.triggered.connect(self.start_ad_network)
        network_menu.addAction(start_network_action)
        
        stop_network_action = QAction("Stop Ad Network", self)
        stop_network_action.triggered.connect(self.stop_ad_network)
        network_menu.addAction(stop_network_action)
        
        # Mining menu
        mining_menu = menu_bar.addMenu("Mining")
        
        start_mining_action = QAction("Start Mining", self)
        start_mining_action.triggered.connect(self.toggle_mining)
        mining_menu.addAction(start_mining_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_wallet_header(self):
        """Create enhanced wallet header with genesis status"""
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        header_frame.setFrameShadow(QFrame.Shadow.Raised)
        header_frame.setMaximumHeight(140)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0066cc, stop:1 #004494);
                border-radius: 12px;
                margin: 5px;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QPushButton {
                background-color: rgba(255,255,255,0.2);
                color: white;
                border: 2px solid rgba(255,255,255,0.3);
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.3);
            }
        """)
        
        header_layout = QHBoxLayout()
        header_frame.setLayout(header_layout)
        
        # Left side - Wallet info
        wallet_info_layout = QVBoxLayout()
        
        self.wallet_label = QLabel("PythonCoin P2P Ad Wallet")
        self.wallet_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        wallet_info_layout.addWidget(self.wallet_label)
        
        self.address_label = QLabel("Address: Loading...")
        self.address_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        wallet_info_layout.addWidget(self.address_label)
        
        self.balance_label = QLabel("Balance: 0.00000000 PYC")
        self.balance_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        wallet_info_layout.addWidget(self.balance_label)
        
        # Genesis status
        self.genesis_status_label = QLabel("Genesis: Coordinating...")
        self.genesis_status_label.setFont(QFont('Arial', 12))
        wallet_info_layout.addWidget(self.genesis_status_label)
        
        header_layout.addLayout(wallet_info_layout, 3)
        
        # Center - Quick stats
        stats_layout = QVBoxLayout()
        
        self.quick_stats_label = QLabel("Network Status")
        self.quick_stats_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        stats_layout.addWidget(self.quick_stats_label)
        
        self.peers_status = QLabel("Peers: 0 connected")
        stats_layout.addWidget(self.peers_status)
        
        self.blockchain_status = QLabel("Blockchain: 0 blocks")
        
        self.persistence_status = QLabel("Auto-save: Active")
        stats_layout.addWidget(self.persistence_status)
        stats_layout.addWidget(self.blockchain_status)
        
        self.mining_status_label = QLabel("Mining: Stopped")
        stats_layout.addWidget(self.mining_status_label)
        
        header_layout.addLayout(stats_layout, 2)
        
        # Right side - QR code and controls
        qr_layout = QVBoxLayout()
        
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(100, 100)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setStyleSheet("border: 2px solid white; border-radius: 8px; background: white;")
        qr_layout.addWidget(self.qr_label)
        
        copy_button = QPushButton("Copy Address")
        copy_button.clicked.connect(self.copy_address_to_clipboard)
        qr_layout.addWidget(copy_button)
        
        header_layout.addLayout(qr_layout, 1)
        
        self.main_layout.addWidget(header_frame)
    
    def create_dashboard_tab(self):
        """Create enhanced dashboard with genesis info"""
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout()
        dashboard_widget.setLayout(dashboard_layout)
        
        # Genesis status section
        genesis_group = QGroupBox("🏗️ Genesis Block Status")
        genesis_layout = QVBoxLayout()
        
        self.genesis_info_label = QLabel("Coordinating with peers for initial coin distribution...")
        genesis_layout.addWidget(self.genesis_info_label)
        
        self.genesis_participants_label = QLabel("Participants: Waiting for peers...")
        genesis_layout.addWidget(self.genesis_participants_label)
        
        genesis_group.setLayout(genesis_layout)
        dashboard_layout.addWidget(genesis_group)
        
        # Top stats row
        stats_row = QHBoxLayout()
        
        # Wallet stats
        wallet_group = QGroupBox("💰 Wallet Statistics")
        wallet_layout = QVBoxLayout()
        
        self.dashboard_balance = QLabel("0.00000000 PYC")
        self.dashboard_balance.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        wallet_layout.addWidget(self.dashboard_balance)
        
        self.pending_balance = QLabel("Pending: 0.00000000 PYC")
        wallet_layout.addWidget(self.pending_balance)
        
        self.total_transactions = QLabel("Total Transactions: 0")
        wallet_layout.addWidget(self.total_transactions)
        
        wallet_group.setLayout(wallet_layout)
        stats_row.addWidget(wallet_group)
        
        # Network stats
        network_group = QGroupBox("🌐 Network Statistics")
        network_layout = QVBoxLayout()
        
        self.connected_peers = QLabel("Connected Peers: 0")
        network_layout.addWidget(self.connected_peers)
        
        self.blockchain_height_dash = QLabel("Blockchain Height: 0")
        network_layout.addWidget(self.blockchain_height_dash)
        
        self.network_status_dash = QLabel("P2P Status: Offline")
        network_layout.addWidget(self.network_status_dash)
        
        network_group.setLayout(network_layout)
        stats_row.addWidget(network_group)
        
        # Mining stats
        mining_group = QGroupBox("⛏️ Mining Statistics")
        mining_layout = QVBoxLayout()
        
        self.blocks_mined_label = QLabel("Blocks Mined: 0")
        mining_layout.addWidget(self.blocks_mined_label)
        
        self.mining_hashrate = QLabel("Hash Rate: 0 H/s")
        mining_layout.addWidget(self.mining_hashrate)
        
        self.mining_difficulty = QLabel("Difficulty: 0")
        mining_layout.addWidget(self.mining_difficulty)
        
        mining_group.setLayout(mining_layout)
        stats_row.addWidget(mining_group)
        
        dashboard_layout.addLayout(stats_row)
        
        # Recent activity
        activity_group = QGroupBox("📊 Recent Activity")
        activity_layout = QVBoxLayout()
        
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Time", "Type", "Details", "Amount"])
        
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        activity_layout.addWidget(self.activity_table)
        activity_group.setLayout(activity_layout)
        
        dashboard_layout.addWidget(activity_group)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        send_money_btn = QPushButton("💸 Send PYC")
        send_money_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        actions_layout.addWidget(send_money_btn)
        
        start_mining_btn = QPushButton("⛏️ Start Mining")
        start_mining_btn.clicked.connect(self.toggle_mining)
        actions_layout.addWidget(start_mining_btn)
        
        start_network_btn = QPushButton("🌐 Start Network")
        start_network_btn.clicked.connect(self.start_ad_network)
        actions_layout.addWidget(start_network_btn)
        
        actions_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.update_ui)
        actions_layout.addWidget(refresh_btn)
        
        debug_balance_btn = QPushButton("🔍 Debug Balance")
        debug_balance_btn.clicked.connect(self.debug_balance_calculation)
        debug_balance_btn.setStyleSheet("background-color: #17a2b8;")
        actions_layout.addWidget(debug_balance_btn)
        
        fix_rewards_btn = QPushButton("🔧 Fix Rewards")
        fix_rewards_btn.clicked.connect(self.fix_missing_coinbase_transactions)
        fix_rewards_btn.setStyleSheet("background-color: #ffc107; color: black;")
        actions_layout.addWidget(fix_rewards_btn)
        
        verify_coinbase_btn = QPushButton("🔍 Verify Coinbase")
        verify_coinbase_btn.clicked.connect(self.verify_blockchain_coinbase_integrity)
        verify_coinbase_btn.setStyleSheet("background-color: #6f42c1; color: white;")
        actions_layout.addWidget(verify_coinbase_btn)
        
        repair_coinbase_btn = QPushButton("🔧 Repair All Coinbase")
        repair_coinbase_btn.clicked.connect(self.repair_all_missing_coinbase_transactions)
        repair_coinbase_btn.setStyleSheet("background-color: #dc3545; color: white;")
        actions_layout.addWidget(repair_coinbase_btn)
        
        validate_blockchain_btn = QPushButton("🔍 Debug Blockchain Validation")
        validate_blockchain_btn.clicked.connect(self.debug_blockchain_validation_issues)
        validate_blockchain_btn.setStyleSheet("background-color: #fd7e14; color: white;")
        actions_layout.addWidget(validate_blockchain_btn)
        
        compare_balance_btn = QPushButton("⚖️ Compare Balance Methods")
        compare_balance_btn.clicked.connect(self.compare_balance_calculation_methods)
        compare_balance_btn.setStyleSheet("background-color: #6610f2; color: white;")
        actions_layout.addWidget(compare_balance_btn)
        
        dashboard_layout.addLayout(actions_layout)
        
        self.tab_widget.addTab(dashboard_widget, "📊 Dashboard")
    
    def create_wallet_tab(self):
        """Create wallet tab (same as before)"""
        wallet_widget = QWidget()
        wallet_layout = QVBoxLayout()
        wallet_widget.setLayout(wallet_layout)
        
        # Send transaction section
        send_group = QGroupBox("💸 Send PythonCoin")
        send_layout = QFormLayout()
        
        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("Recipient's PythonCoin address")
        send_layout.addRow("Recipient:", self.recipient_input)
        
        amount_layout = QHBoxLayout()
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setDecimals(8)
        self.amount_input.setRange(0.00000001, 1000000000)
        self.amount_input.setSingleStep(0.1)
        amount_layout.addWidget(self.amount_input)
        
        pyc_label = QLabel("PYC")
        pyc_label.setStyleSheet("font-weight: bold;")
        amount_layout.addWidget(pyc_label)
        
        max_button = QPushButton("Max")
        max_button.clicked.connect(self.set_max_amount)
        amount_layout.addWidget(max_button)
        
        send_layout.addRow("Amount:", amount_layout)
        
        send_button = QPushButton("💸 Send Transaction")
        send_button.setMinimumHeight(40)
        send_button.clicked.connect(self.send_transaction)
        send_layout.addRow(send_button)
        
        send_group.setLayout(send_layout)
        wallet_layout.addWidget(send_group)
        
        # Transaction history
        history_group = QGroupBox("📜 Transaction History")
        history_layout = QVBoxLayout()
        
        self.tx_table = QTableWidget()
        self.tx_table.setColumnCount(6)
        self.tx_table.setHorizontalHeaderLabels(["Time", "Type", "From/To", "Amount", "Status", "TX ID"])
        
        header = self.tx_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        self.tx_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tx_table.itemDoubleClicked.connect(self.show_transaction_details)
        
        history_layout.addWidget(self.tx_table)
        
        # Transaction controls
        tx_controls = QHBoxLayout()
        
        export_tx_btn = QPushButton("📤 Export History")
        export_tx_btn.clicked.connect(self.export_transactions)
        tx_controls.addWidget(export_tx_btn)
        
        refresh_tx_btn = QPushButton("🔄 Refresh")
        refresh_tx_btn.clicked.connect(self.update_transactions)
        tx_controls.addWidget(refresh_tx_btn)
        
        tx_controls.addStretch()
        
        history_layout.addLayout(tx_controls)
        history_group.setLayout(history_layout)
        wallet_layout.addWidget(history_group)
        
        self.tab_widget.addTab(wallet_widget, "💰 Wallet")
    
    def create_mining_tab(self):
        """Create enhanced mining tab"""
        mining_widget = QWidget()
        mining_layout = QVBoxLayout()
        mining_widget.setLayout(mining_layout)
        
        # Mining status
        status_group = QGroupBox("⛏️ Mining Status")
        status_layout = QHBoxLayout()
        
        # Left side - Status info
        status_info = QVBoxLayout()
        
        self.mining_status = QLabel("Status: Not mining")
        self.mining_status.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        status_info.addWidget(self.mining_status)
        
        self.mining_hashrate_label = QLabel("Hash Rate: 0 H/s")
        status_info.addWidget(self.mining_hashrate_label)
        
        self.blocks_mined_count = QLabel("Blocks Mined: 0")
        status_info.addWidget(self.blocks_mined_count)
        
        self.mining_rewards = QLabel("Mining Rewards: 0.00000000 PYC")
        
        self.coinbase_status = QLabel("Coinbase Status: Checking...")
        status_info.addWidget(self.coinbase_status)
        status_info.addWidget(self.mining_rewards)
        
        self.genesis_mining_status = QLabel("Genesis: Not ready")
        status_info.addWidget(self.genesis_mining_status)
        
        status_layout.addLayout(status_info)
        
        # Right side - Mining controls
        controls_layout = QVBoxLayout()
        
        self.start_mining_button = QPushButton("🚀 Start Mining")
        self.start_mining_button.clicked.connect(self.toggle_mining)
        self.start_mining_button.setMinimumHeight(50)
        controls_layout.addWidget(self.start_mining_button)
        
        self.stop_mining_button = QPushButton("⏹️ Stop Mining")
        self.stop_mining_button.clicked.connect(self.toggle_mining)
        self.stop_mining_button.setEnabled(False)
        self.stop_mining_button.setMinimumHeight(50)
        controls_layout.addWidget(self.stop_mining_button)
        
        status_layout.addLayout(controls_layout)
        status_group.setLayout(status_layout)
        mining_layout.addWidget(status_group)
        
        # Mining settings
        settings_group = QGroupBox("⚙️ Mining Settings")
        settings_layout = QFormLayout()
        
        self.mining_threads = QComboBox()
        for i in range(1, min(9, os.cpu_count() + 1)):
            self.mining_threads.addItem(f"{i} {'Thread' if i == 1 else 'Threads'}")
        settings_layout.addRow("CPU Threads:", self.mining_threads)
        
        self.mining_address = QLineEdit()
        settings_layout.addRow("Mining Address:", self.mining_address)
        
        settings_group.setLayout(settings_layout)
        mining_layout.addWidget(settings_group)
        
        # Mining log
        log_group = QGroupBox("📜 Mining Log")
        log_layout = QVBoxLayout()
        
        self.mining_log = QTextEdit()
        self.mining_log.setReadOnly(True)
        self.mining_log.setMaximumHeight(200)
        log_layout.addWidget(self.mining_log)
        
        clear_log_btn = QPushButton("🗑️ Clear Log")
        clear_log_btn.clicked.connect(lambda: self.mining_log.clear())
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        mining_layout.addWidget(log_group)
        
        self.tab_widget.addTab(mining_widget, "⛏️ Mining")
    
    def create_network_tab(self):
        """Create enhanced network tab"""
        network_widget = QWidget()
        network_layout = QVBoxLayout()
        network_widget.setLayout(network_layout)
        
        # P2P Network status
        p2p_group = QGroupBox("🌐 P2P Ad Network")
        p2p_layout = QVBoxLayout()
        
        self.network_status = QLabel("Status: Offline")
        self.network_status.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        p2p_layout.addWidget(self.network_status)
        
        # Network controls
        network_controls = QHBoxLayout()
        
        self.start_network_btn = QPushButton("🚀 Start P2P Network")
        self.start_network_btn.clicked.connect(self.start_ad_network)
        network_controls.addWidget(self.start_network_btn)
        
        self.stop_network_btn = QPushButton("⏹️ Stop P2P Network")
        self.stop_network_btn.clicked.connect(self.stop_ad_network)
        self.stop_network_btn.setEnabled(False)
        network_controls.addWidget(self.stop_network_btn)
        
        network_controls.addStretch()
        p2p_layout.addLayout(network_controls)
        
        p2p_group.setLayout(p2p_layout)
        network_layout.addWidget(p2p_group)
        
        # Blockchain node status
        node_group = QGroupBox("🖥️ Blockchain Node")
        node_layout = QVBoxLayout()
        
        self.node_status = QLabel("Status: Node not running")
        self.node_status.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        node_layout.addWidget(self.node_status)
        
        # Node controls
        node_controls = QHBoxLayout()
        
        host_port_layout = QHBoxLayout()
        host_port_layout.addWidget(QLabel("Host:"))
        
        self.node_host = QLineEdit("127.0.0.1")
        host_port_layout.addWidget(self.node_host)
        
        host_port_layout.addWidget(QLabel("Port:"))
        
        self.node_port = QSpinBox()
        self.node_port.setRange(1024, 65535)
        self.node_port.setValue(5000)  # Ensure integer value
        host_port_layout.addWidget(self.node_port)
        
        node_controls.addLayout(host_port_layout)
        
        self.start_node_button = QPushButton("🚀 Start Node")
        self.start_node_button.clicked.connect(self.start_node)
        node_controls.addWidget(self.start_node_button)
        
        self.stop_node_button = QPushButton("⏹️ Stop Node")
        self.stop_node_button.clicked.connect(self.stop_node)
        self.stop_node_button.setEnabled(False)
        node_controls.addWidget(self.stop_node_button)
        
        node_layout.addLayout(node_controls)
        node_group.setLayout(node_layout)
        network_layout.addWidget(node_group)
        
        # Blockchain info
        blockchain_group = QGroupBox("⛓️ Blockchain Information")
        blockchain_layout = QFormLayout()
        
        self.blockchain_height_label = QLabel("0")
        blockchain_layout.addRow("Current Height:", self.blockchain_height_label)
        
        self.blockchain_difficulty = QLabel("0")
        blockchain_layout.addRow("Mining Difficulty:", self.blockchain_difficulty)
        
        self.pending_transactions = QLabel("0")
        blockchain_layout.addRow("Pending Transactions:", self.pending_transactions)
        
        self.genesis_status_detail = QLabel("Waiting for genesis...")
        blockchain_layout.addRow("Genesis Status:", self.genesis_status_detail)
        
        blockchain_group.setLayout(blockchain_layout)
        network_layout.addWidget(blockchain_group)
        
        # Peers table
        peers_group = QGroupBox("👥 Connected Peers")
        peers_layout = QVBoxLayout()
        
        self.peers_table = QTableWidget()
        self.peers_table.setColumnCount(5)
        self.peers_table.setHorizontalHeaderLabels(["Peer ID", "Host", "Status", "Wallet", "Last Seen"])
        
        peers_header = self.peers_table.horizontalHeader()
        peers_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        peers_layout.addWidget(self.peers_table)
        peers_group.setLayout(peers_layout)
        network_layout.addWidget(peers_group)
        
        # Network log
        network_log_group = QGroupBox("📡 Network Log")
        network_log_layout = QVBoxLayout()
        
        self.network_log = QTextEdit()
        self.network_log.setReadOnly(True)
        self.network_log.setMaximumHeight(150)
        network_log_layout.addWidget(self.network_log)
        
        network_log_group.setLayout(network_log_layout)
        network_layout.addWidget(network_log_group)
        
        self.tab_widget.addTab(network_widget, "🌐 Network")
    
    # ============================================================================
    # Core Wallet Functions (Enhanced)
    # ============================================================================
    
    def create_ad_creation_tab(self):
        """Create ad creation and management tab for home advertisers"""
        ad_creation_widget = QWidget()
        ad_creation_layout = QHBoxLayout()
        ad_creation_widget.setLayout(ad_creation_layout)
        
        # Left panel - Ad creation form
        left_panel = QWidget()
        left_panel.setFixedWidth(400)
        left_layout = QVBoxLayout(left_panel)
        
        # Ad details form
        form_group = QGroupBox("🎯 Create New Advertisement")
        form_layout = QFormLayout()
        
        self.ad_title_input = QLineEdit()
        self.ad_title_input.setPlaceholderText("Enter catchy ad title...")
        self.ad_title_input.textChanged.connect(self.preview_ad)
        form_layout.addRow("Title:", self.ad_title_input)
        
        self.ad_description_input = QTextEdit()
        self.ad_description_input.setPlaceholderText("Describe your product or service...")
        self.ad_description_input.setMaximumHeight(80)
        self.ad_description_input.textChanged.connect(self.preview_ad)
        form_layout.addRow("Description:", self.ad_description_input)
        
        self.ad_category_combo = QComboBox()
        self.ad_category_combo.addItems([
            "technology", "automotive", "fashion", "travel", 
            "food", "sports", "health", "business", "entertainment", 
            "cryptocurrency", "gaming", "education", "finance",
            "real-estate", "home-services", "beauty", "pets"
        ])
        self.ad_category_combo.currentTextChanged.connect(self.preview_ad)
        form_layout.addRow("Category:", self.ad_category_combo)
        
        self.ad_click_url_input = QLineEdit()
        self.ad_click_url_input.setPlaceholderText("https://your-website.com")
        form_layout.addRow("Click URL:", self.ad_click_url_input)
        
        # Payout settings
        payout_layout = QHBoxLayout()
        self.ad_payout_input = QDoubleSpinBox()
        self.ad_payout_input.setDecimals(8)
        self.ad_payout_input.setRange(0.00000001, 1.0)
        self.ad_payout_input.setValue(0.00100000)  # Default 0.00100000 PYC per click
        self.ad_payout_input.valueChanged.connect(self.preview_ad)
        payout_layout.addWidget(self.ad_payout_input)
        payout_layout.addWidget(QLabel("PYC per click"))
        form_layout.addRow("Payout Rate:", payout_layout)
        
        form_group.setLayout(form_layout)
        left_layout.addWidget(form_group)
        
        # Image upload section
        image_group = QGroupBox("🖼️ Ad Image")
        image_layout = QVBoxLayout()
        
        self.upload_image_btn = QPushButton("📁 Upload Image")
        self.upload_image_btn.clicked.connect(self.upload_ad_image)
        image_layout.addWidget(self.upload_image_btn)
        
        self.image_path_label = QLabel("No image selected")
        self.image_path_label.setWordWrap(True)
        self.image_path_label.setStyleSheet("color: #666; font-style: italic;")
        image_layout.addWidget(self.image_path_label)
        
        # Image preview
        self.image_preview_label = QLabel()
        self.image_preview_label.setFixedSize(150, 100)
        self.image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; background: #f8f9fa;")
        self.image_preview_label.setText("Image Preview")
        image_layout.addWidget(self.image_preview_label)
        
        image_group.setLayout(image_layout)
        left_layout.addWidget(image_group)
        
        # Targeting options
        targeting_group = QGroupBox("🎯 Targeting Options")
        targeting_layout = QVBoxLayout()
        
        targeting_layout.addWidget(QLabel("Target Interests:"))
        self.target_interests = QLineEdit()
        self.target_interests.setPlaceholderText("technology, gaming, crypto (comma-separated)")
        targeting_layout.addWidget(self.target_interests)
        
        targeting_layout.addWidget(QLabel("Geographic Targeting:"))
        self.target_geo = QComboBox()
        self.target_geo.addItems(["Global", "North America", "Europe", "Asia", "Local"])
        targeting_layout.addWidget(self.target_geo)
        
        targeting_group.setLayout(targeting_layout)
        left_layout.addWidget(targeting_group)
        
        # Budget settings
        budget_group = QGroupBox("💰 Budget Settings")
        budget_layout = QFormLayout()
        
        self.daily_budget_input = QDoubleSpinBox()
        self.daily_budget_input.setDecimals(8)
        self.daily_budget_input.setRange(0.001, 10000)
        self.daily_budget_input.setValue(1.0)
        budget_layout.addRow("Daily Budget (PYC):", self.daily_budget_input)
        
        self.max_clicks_input = QSpinBox()
        self.max_clicks_input.setRange(1, 100000)
        self.max_clicks_input.setValue(1000)
        budget_layout.addRow("Max Clicks/Day:", self.max_clicks_input)
        
        budget_group.setLayout(budget_layout)
        left_layout.addWidget(budget_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        preview_btn = QPushButton("👁️ Preview")
        preview_btn.clicked.connect(self.preview_ad)
        action_layout.addWidget(preview_btn)
        
        create_btn = QPushButton("🚀 Create & Publish")
        create_btn.clicked.connect(self.create_advertisement)
        create_btn.setStyleSheet("background-color: #28a745; font-size: 14px; padding: 10px;")
        action_layout.addWidget(create_btn)
        
        left_layout.addLayout(action_layout)
        left_layout.addStretch()
        
        ad_creation_layout.addWidget(left_panel)
        
        # Right panel - Ad preview and management
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Preview section
        preview_group = QGroupBox("👁️ Live Preview")
        preview_layout = QVBoxLayout()
        
        self.ad_preview_area = QTextEdit()
        self.ad_preview_area.setHtml(self.get_default_preview_html())
        self.ad_preview_area.setMaximumHeight(250)
        self.ad_preview_area.setReadOnly(True)
        preview_layout.addWidget(self.ad_preview_area)
        
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        # My ads management
        my_ads_group = QGroupBox("📊 My Advertisements")
        my_ads_layout = QVBoxLayout()
        
        self.my_ads_table = QTableWidget()
        self.my_ads_table.setColumnCount(7)
        self.my_ads_table.setHorizontalHeaderLabels(["Title", "Category", "Payout", "Clicks", "Spent", "Status", "Actions"])
        
        my_ads_header = self.my_ads_table.horizontalHeader()
        my_ads_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        my_ads_layout.addWidget(self.my_ads_table)
        
        # My ads controls
        my_ads_controls = QHBoxLayout()
        
        edit_ad_btn = QPushButton("✏️ Edit Selected")
        edit_ad_btn.clicked.connect(self.edit_advertisement)
        my_ads_controls.addWidget(edit_ad_btn)
        
        pause_ad_btn = QPushButton("⏸️ Pause Selected")
        pause_ad_btn.clicked.connect(self.pause_advertisement)
        my_ads_controls.addWidget(pause_ad_btn)
        
        delete_ad_btn = QPushButton("🗑️ Delete Selected")
        delete_ad_btn.clicked.connect(self.delete_advertisement)
        delete_ad_btn.setStyleSheet("background-color: #dc3545;")
        my_ads_controls.addWidget(delete_ad_btn)
        
        my_ads_controls.addStretch()
        
        refresh_ads_btn = QPushButton("🔄 Refresh")
        refresh_ads_btn.clicked.connect(self.update_my_ads_table)
        my_ads_controls.addWidget(refresh_ads_btn)
        
        my_ads_layout.addLayout(my_ads_controls)
        
        my_ads_group.setLayout(my_ads_layout)
        right_layout.addWidget(my_ads_group)
        
        # Ad network stats
        stats_group = QGroupBox("📈 Ad Network Statistics")
        stats_layout = QVBoxLayout()
        
        self.ad_stats_layout = QVBoxLayout()
        self.update_ad_network_stats()
        stats_layout.addLayout(self.ad_stats_layout)
        
        stats_group.setLayout(stats_layout)
        right_layout.addWidget(stats_group)
        
        ad_creation_layout.addWidget(right_panel)
        
        self.tab_widget.addTab(ad_creation_widget, "🎯 Create Ads")
    
    def get_default_preview_html(self):
        """Get default preview HTML for ad"""
        return """
        <div style="border: 2px solid #0066cc; border-radius: 12px; padding: 15px; background: white; margin: 10px; position: relative;">
            <div style="position: absolute; top: 10px; right: 10px; background: linear-gradient(45deg, #ff6b35, #f7931e); color: white; padding: 4px 8px; border-radius: 12px; font-size: 10px; font-weight: bold;">💎 PYC</div>
            <h3 style="color: #0066cc; margin: 0 0 10px 0; font-size: 18px;">Your Ad Preview</h3>
            <p style="color: #666; margin: 0 0 10px 0; font-size: 14px;">Fill in the form to see your ad preview here...</p>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; margin-top: 10px;">
                <span style="color: #0066cc;">📱 Category • 🌐 P2P Network</span>
                <span style="background: linear-gradient(45deg, #28a745, #20c997); color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold;">+0.00100000 PYC per click</span>
            </div>
        </div>
        """

    def load_wallet(self):
        """Load or create wallet"""
        if not self.blockchain:
            self.log_message("Error: Cannot load wallet - blockchain not initialized")
            return
        
        try:
            if os.path.exists("wallet.json"):
                with open("wallet.json", "r") as f:
                    wallet_data = json.load(f)
                
                self.wallet = Wallet(
                    self.blockchain,
                    private_key=wallet_data["private_key"],
                    public_key=wallet_data["public_key"]
                )
                
                self.update_wallet_display()
                self.log_message("Wallet loaded successfully")
            else:
                self.create_new_wallet()
                
        except Exception as e:
            self.log_message(f"Error loading wallet: {str(e)}")
            self.create_new_wallet()
    
    def create_new_wallet(self):
        """Create a new wallet"""
        if not self.blockchain:
            self.log_message("Error: Cannot create wallet - blockchain not initialized")
            return
        
        try:
            self.wallet = Wallet(self.blockchain)
            self.save_wallet()
            self.update_wallet_display()
            self.log_message("New wallet created successfully")
        except Exception as e:
            self.log_message(f"Error creating wallet: {str(e)}")
            QMessageBox.critical(self, "Wallet Error", f"Failed to create wallet: {str(e)}")
            return
        
        # Auto-register with database after wallet is created/loaded
        if self.wallet and hasattr(self.wallet, 'address'):
            try:
                username = f"user_{self.wallet.address[:8]}"
                self.db_registration = DatabaseAutoRegistration(
                    username=username,
                    wallet_address=self.wallet.address,
                    client_name=f"PythonCoin Wallet - {username}",
                    port=8082
                )
                
                # Register in background thread
                registration_thread = threading.Thread(
                    target=lambda: self.db_registration.register_client(self.wallet, self.blockchain),
                    daemon=True
                )
                registration_thread.start()
                
                self.log_message("🔄 Database auto-registration initiated...")
                
            except Exception as e:
                self.log_message(f"❌ Database registration error: {str(e)}")
            
            except Exception as e:
                self.log_message(f"Error creating wallet: {str(e)}")
                QMessageBox.critical(self, "Wallet Error", f"Failed to create wallet: {str(e)}")
    
    def save_wallet(self):
        """Save wallet to file"""
        if not self.wallet:
            return
        
        try:
            wallet_data = {
                "private_key": self.wallet.private_key,
                "public_key": self.wallet.public_key,
                "address": self.wallet.address
            }
            
            with open("wallet.json", "w") as f:
                json.dump(wallet_data, f)
            
            self.log_message("Wallet saved successfully")
            
        except Exception as e:
            self.log_message(f"Error saving wallet: {str(e)}")
    
    def init_p2p_components(self):
        """Initialize P2P components after wallet is loaded"""
        if not self.wallet:
            return
        
        try:
            # Initialize P2P manager
            self.p2p_manager = CryptoP2PManager(
                self.client_id, self.port, self.blockchain, self.wallet
            )
            
            # Connect signals
            self.p2p_manager.peerDiscovered.connect(self.on_peer_discovered)
            self.p2p_manager.peerConnected.connect(self.on_peer_connected)
            self.p2p_manager.peerDisconnected.connect(self.on_peer_disconnected)
            self.p2p_manager.adsReceived.connect(self.on_ads_received)
            self.p2p_manager.statusUpdate.connect(self.on_status_update)
            self.p2p_manager.clickReceived.connect(self.on_click_received)
            self.p2p_manager.paymentSent.connect(self.on_payment_sent)
            self.p2p_manager.genesisReady.connect(self.on_genesis_ready)
            
            self.log_message("P2P components initialized")
            
        except Exception as e:
            self.log_message(f"Error initializing P2P components: {str(e)}")
    
    # ============================================================================
    # UI Update Functions (Enhanced)
    # ============================================================================
    
    def original_update_ui(self):
        """Update all UI components - fixed version"""
        try:
            if self.wallet:
                self.update_wallet_display()
                self.update_dashboard()
                self.update_transactions()
                self.update_network_display()
                if hasattr(self, 'update_ad_network_stats'):
                    self.update_ad_network_stats()
        except Exception as e:
            self.log_message(f"Original UI update error: {str(e)}")


    def update_ui(self):
        """Update UI - safe version without recursion"""
        try:
            # Prevent recursion by using a flag
            if hasattr(self, '_updating_ui') and self._updating_ui:
                return
            
            self._updating_ui = True
            
            if self.wallet:
                self.update_wallet_display()
                self.update_dashboard()
                # Update other components less frequently
                if not hasattr(self, '_last_full_update') or (datetime.now().timestamp() - self._last_full_update) > 10:
                    self.update_transactions()
                    self.update_network_display()
                    if hasattr(self, 'update_ad_network_stats'):
                        self.update_ad_network_stats()
                    self._last_full_update = datetime.now().timestamp()
            
        except Exception as e:
            self.log_message(f"UI update error: {str(e)}")
        finally:
            self._updating_ui = False

    
    def init_database(self):
        """Initialize database connection and setup client registration"""
        try:
            self.db_connected = self.db_manager.connect()
            
            if self.db_connected:
                self.log_message("✅ Database connected successfully")
                
                # Schedule client registration after wallet is loaded
                QTimer.singleShot(5000, self.delayed_database_registration)
                
                # Schedule periodic cleanup
                QTimer.singleShot(10000, self.setup_database_maintenance)
                
            else:
                self.log_message("❌ Database connection failed - will retry in 30 seconds")
                # Retry connection after 30 seconds
                QTimer.singleShot(30000, self.init_database)
                
        except Exception as e:
            self.log_message(f"❌ Database initialization error: {str(e)}")
            self.db_connected = False
            # Retry after 30 seconds
            QTimer.singleShot(30000, self.init_database)
    
    def delayed_database_registration(self):
        """Delayed database registration after wallet is ready"""
        try:
            if self.wallet and self.db_connected:
                self.log_message("📋 Performing delayed database registration...")
                success = self.register_client_in_database()
                if success:
                    self.start_database_sync()
                else:
                    # Retry registration in 15 seconds
                    QTimer.singleShot(15000, self.delayed_database_registration)
            else:
                # Wallet not ready yet, try again in 5 seconds
                QTimer.singleShot(5000, self.delayed_database_registration)
                
        except Exception as e:
            self.log_message(f"❌ Delayed registration error: {str(e)}")
    
    def setup_database_maintenance(self):
        """Setup periodic database maintenance tasks"""
        try:
            if not hasattr(self, 'db_maintenance_timer'):
                self.db_maintenance_timer = QTimer()
                self.db_maintenance_timer.timeout.connect(self.perform_database_maintenance)
                self.db_maintenance_timer.start(300000)  # Every 5 minutes
                self.log_message("✅ Database maintenance timer started (5 minute intervals)")
            
        except Exception as e:
            self.log_message(f"❌ Error setting up maintenance: {str(e)}")
    
    def perform_database_maintenance(self):
        """Perform periodic database maintenance"""
        try:
            if not self.db_connected:
                return
            
            # Update client status
            self.update_client_in_database()
            
            # Clean up old sessions
            cleanup_query = """
                UPDATE developer_sessions 
                SET status = 'inactive'
                WHERE last_activity < DATE_SUB(NOW(), INTERVAL 2 HOUR)
                AND status = 'active'
                AND client_id = %s
            """
            
            self.db_manager.execute_query(cleanup_query, (self.client_id,))
            
            # Log maintenance completion
            self.log_message("🧹 Database maintenance completed")
            
        except Exception as e:
            self.log_message(f"❌ Database maintenance error: {str(e)}")
    def populate_client_data(self):
        """Populate client data in database on startup"""
        try:
            if not self.db_connected or not self.wallet:
                return
            
            # Register this client
            client_data = {
                'client_id': self.client_id,
                'name': f'PythonCoin Wallet - {self.wallet.address[:8]}...' if self.wallet else 'PythonCoin Wallet',
                'host': '127.0.0.1',
                'port': self.port,
                'username': f'user_{self.wallet.address[:8]}' if self.wallet else 'unknown',
                'wallet_address': self.wallet.address if self.wallet else '',
                'version': '2.1.0',
                'capabilities': ['ad_serving', 'payments', 'p2p', 'notifications'],
                'metadata': {
                    'start_time': datetime.now().isoformat(),
                    'python_version': sys.version,
                    'platform': os.name
                },
                'ad_count': len(self.ads)
            }
            
            success = self.db_manager.register_client(client_data)
            if success:
                self.log_message(f"✅ Registered client in database: {self.client_id}")
            
            # Populate initial ads if any
            for ad in self.ads:
                self.db_manager.create_ad(ad.to_dict() if hasattr(ad, 'to_dict') else ad.__dict__)
                
        except Exception as e:
            self.log_message(f"Error populating client data: {str(e)}")
    
    def update_database_on_ad_creation(self, ad):
        """Update database when new ad is created"""
        try:
            if not self.db_connected:
                return
            
            # Convert AdContent to dict if needed
            if hasattr(ad, 'to_dict'):
                ad_data = ad.to_dict()
            else:
                ad_data = ad.__dict__ if hasattr(ad, '__dict__') else ad
            
            # Create ad in database
            success = self.db_manager.create_ad(ad_data)
            if success:
                self.log_message(f"✅ Ad saved to database: {ad_data.get('title', 'Unknown')}")
                
                # Create notification
                self.db_manager.create_notification({
                    'type': 'new_ad_created',
                    'title': 'New Advertisement',
                    'message': f'New ad created: {ad_data.get("title", "Unknown")}',
                    'metadata': {'ad_id': ad_data.get('id', ''), 'category': ad_data.get('category', '')}
                })
            
        except Exception as e:
            self.log_message(f"Error updating database on ad creation: {str(e)}")
    
    def update_database_on_click(self, click_data):
        """Update database when ad is clicked"""
        try:
            if not self.db_connected:
                return
            
            success = self.db_manager.record_ad_click(click_data)
            if success:
                self.log_message(f"✅ Click recorded in database: {click_data.get('ad_id', 'Unknown')}")
            
        except Exception as e:
            self.log_message(f"Error recording click in database: {str(e)}")


    def update_wallet_display(self):
        """Update wallet display with enhanced balance checking"""
        if not self.wallet or not self.blockchain:
            # Set default values when wallet/blockchain not ready
            if hasattr(self, 'address_label'):
                self.address_label.setText("Address: Loading...")
            if hasattr(self, 'balance_label'):
                self.balance_label.setText("Balance: Loading...")
            if hasattr(self, 'genesis_status_label'):
                self.genesis_status_label.setText("Genesis: Initializing...")
            return
        
        # Update header
        self.address_label.setText(f"Address: {self.wallet.address}")
        
        # Get balance with error handling
        try:
            # Use corrected balance calculation
            try:
                balance = self.override_wallet_get_balance()
            except AttributeError:
                balance = self.wallet.get_balance() if hasattr(self.wallet, "get_balance") else 0.0
            self.balance_label.setText(f"Balance: {balance:.8f} PYC")
            
            # If balance is 0 but we should have mining rewards, debug it
            if balance == 0 and len(self.blockchain.chain) > 1:
                self.log_message("⚠️ Balance is 0 but blockchain has blocks - debugging...")
                # Trigger debug but don't block UI
                QTimer.singleShot(1000, self.debug_balance_calculation)
                
        except Exception as e:
            self.log_message(f"❌ Error getting balance: {str(e)}")
            self.balance_label.setText("Balance: Error")
    def update_dashboard(self):
        """Update dashboard statistics"""
        if not self.wallet:
            return
        
        # Genesis status
        if self.blockchain.genesis_complete:
            self.genesis_info_label.setText("Genesis block created and distributed successfully! ✓")
            genesis_addresses = self.blockchain.genesis_addresses
            self.genesis_participants_label.setText(f"Participants: {len(genesis_addresses)} wallets received initial coins")
        else:
            self.genesis_info_label.setText("Coordinating with peers for initial coin distribution...")
            
        # Wallet stats - Enhanced balance display
        try:
            # Use corrected balance calculation
            try:
                balance = self.override_wallet_get_balance()
            except AttributeError:
                balance = self.wallet.get_balance() if hasattr(self.wallet, "get_balance") else 0.0
            self.dashboard_balance.setText(f"{balance:.8f} PYC")
            
            # Also update the main balance label if it exists
            if hasattr(self, 'balance_label'):
                self.balance_label.setText(f"Balance: {balance:.8f} PYC")
                
        except Exception as e:
            self.log_message(f"❌ Dashboard balance error: {str(e)}")
            self.dashboard_balance.setText("Error calculating balance")
        
        # Calculate pending balance
        pending = sum(self.calculate_transaction_amount(tx) 
                     for tx in self.blockchain.pending_transactions)
        self.pending_balance.setText(f"Pending: {pending:.8f} PYC")
        
        # Transaction count
        tx_history = self.wallet.get_transaction_history()
        self.total_transactions.setText(f"Total Transactions: {len(tx_history)}")
        
        # Network stats
        connected_peers = len([p for p in self.peers.values() if p.status == 'connected'])
        self.connected_peers.setText(f"Connected Peers: {connected_peers}")
        
        self.blockchain_height_dash.setText(f"Blockchain Height: {len(self.blockchain.chain)}")
        
        if self.p2p_manager and self.p2p_manager.running:
            self.network_status_dash.setText("P2P Status: Online")
        else:
            self.network_status_dash.setText("P2P Status: Offline")
        
        # Mining stats
        self.blocks_mined_label.setText(f"Blocks Mined: {self.stats['blocks_mined']}")
        
        if self.blockchain.chain:
            last_block = self.blockchain.chain[-1]
            self.mining_difficulty.setText(f"Difficulty: {last_block.difficulty}")
        
        # Header quick stats
        self.peers_status.setText(f"Peers: {connected_peers} connected")
        self.blockchain_status.setText(f"Blockchain: {len(self.blockchain.chain)} blocks")
        
        # Update recent activity
        self.update_recent_activity()
    
    def update_recent_activity(self):
        """Update recent activity table"""
        self.activity_table.setRowCount(0)
        
        # Combine different types of activities
        activities = []
        
        # Add recent transactions
        if self.wallet:
            recent_txs = self.wallet.get_transaction_history()[-10:]
            for tx in recent_txs:
                amount = self.calculate_transaction_amount(tx)
                activities.append({
                    'time': datetime.fromtimestamp(tx.timestamp),
                    'type': f"💰 {tx.tx_type.title()}",
                    'details': f"{'Sent' if amount < 0 else 'Received'} transaction",
                    'amount': f"{abs(amount):.6f} PYC"
                })
        
        # Add mining events
        for i, block in enumerate(self.blockchain.chain[-5:]):  # Last 5 blocks
            if any(tx.tx_type == "coinbase" and any(out.address == self.wallet.address for out in tx.outputs) 
                   for tx in block.transactions):
                activities.append({
                    'time': datetime.fromtimestamp(block.timestamp),
                    'type': "⛏️ Mining",
                    'details': f"Block {block.index} mined",
                    'amount': "+50.0 PYC"
                })
        
        # Sort by time (newest first)
        activities.sort(key=lambda x: x['time'], reverse=True)
        
        # Add to table
        for i, activity in enumerate(activities[:20]):  # Show last 20 activities
            self.activity_table.insertRow(i)
            
            time_item = QTableWidgetItem(activity['time'].strftime("%H:%M:%S"))
            self.activity_table.setItem(i, 0, time_item)
            
            type_item = QTableWidgetItem(activity['type'])
            self.activity_table.setItem(i, 1, type_item)
            
            details_item = QTableWidgetItem(activity['details'])
            self.activity_table.setItem(i, 2, details_item)
            
            amount_item = QTableWidgetItem(activity['amount'])
            self.activity_table.setItem(i, 3, amount_item)
    
    def update_transactions(self):
        """Update transaction history"""
        if not self.wallet:
            return
        
        transactions = self.wallet.get_transaction_history()
        transactions.sort(key=lambda tx: tx.timestamp, reverse=True)
        
        self.tx_table.setRowCount(0)
        
        for i, tx in enumerate(transactions):
            self.tx_table.insertRow(i)
            
            # Time
            time_str = datetime.fromtimestamp(tx.timestamp).strftime("%Y-%m-%d %H:%M")
            time_item = QTableWidgetItem(time_str)
            self.tx_table.setItem(i, 0, time_item)
            
            # Type
            type_item = QTableWidgetItem(tx.tx_type.title())
            self.tx_table.setItem(i, 1, type_item)
            
            # From/To
            if tx.tx_type == "coinbase":
                from_to = f"Mining Reward → You"
            elif tx.tx_type == "genesis":
                from_to = f"Genesis Distribution → You"
            elif tx.sender == self.wallet.public_key:
                recipient = tx.outputs[0].address if tx.outputs else "N/A"
                from_to = f"You → {recipient[:8]}..."
            else:
                sender_addr = CryptoUtils.pubkey_to_address(tx.sender)
                from_to = f"{sender_addr[:8]}... → You"
            
            from_to_item = QTableWidgetItem(from_to)
            self.tx_table.setItem(i, 2, from_to_item)
            
            # Amount
            amount = self.calculate_transaction_amount(tx)
            amount_item = QTableWidgetItem(f"{amount:.8f} PYC")
            if amount < 0:
                amount_item.setForeground(QColor(220, 53, 69))  # Red for outgoing
            else:
                amount_item.setForeground(QColor(40, 167, 69))  # Green for incoming
            self.tx_table.setItem(i, 3, amount_item)
            
            # Status
            status = "Confirmed" if any(tx in block.transactions for block in self.blockchain.chain) else "Pending"
            status_item = QTableWidgetItem(status)
            self.tx_table.setItem(i, 4, status_item)
            
            # TX ID
            tx_id_item = QTableWidgetItem(tx.tx_id[:16] + "...")
            self.tx_table.setItem(i, 5, tx_id_item)
    
    def update_network_display(self):
        """Update network and peers display"""
        # Update peers table
        self.peers_table.setRowCount(len(self.peers))
        
        for row, (peer_id, peer) in enumerate(self.peers.items()):
            self.peers_table.setItem(row, 0, QTableWidgetItem(peer_id[:8] + "..."))
            self.peers_table.setItem(row, 1, QTableWidgetItem(f"{peer.host}:{peer.port}"))
            self.peers_table.setItem(row, 2, QTableWidgetItem(peer.status))
            self.peers_table.setItem(row, 3, QTableWidgetItem(peer.wallet_address[:8] + "..." if peer.wallet_address else "N/A"))
            self.peers_table.setItem(row, 4, QTableWidgetItem(peer.last_seen))
        
        # Update network status
        if self.p2p_manager and self.p2p_manager.running:
            self.network_status.setText("Status: Online")
            self.start_network_btn.setEnabled(False)
            self.stop_network_btn.setEnabled(True)
        else:
            self.network_status.setText("Status: Offline")
            self.start_network_btn.setEnabled(True)
            self.stop_network_btn.setEnabled(False)
        
        # Update blockchain info
        if hasattr(self, 'blockchain_height_label'):
            self.blockchain_height_label.setText(str(len(self.blockchain.chain)))
        
        if hasattr(self, 'blockchain_difficulty'):
            if self.blockchain.chain:
                difficulty = self.blockchain.chain[-1].difficulty
                self.blockchain_difficulty.setText(str(difficulty))
        
        if hasattr(self, 'pending_transactions'):
            self.pending_transactions.setText(str(len(self.blockchain.pending_transactions)))
        
        if hasattr(self, 'genesis_status_detail'):
            if self.blockchain.genesis_complete:
                self.genesis_status_detail.setText("Complete ✓")
            else:
                self.genesis_status_detail.setText("Coordinating...")
        
        # Update mining genesis status
        if hasattr(self, 'genesis_mining_status'):
            if self.blockchain.genesis_complete:
                self.genesis_mining_status.setText("Genesis: Ready ✓")
            else:
                self.genesis_mining_status.setText("Genesis: Waiting...")
    
    # ============================================================================
    # Transaction Functions (Enhanced)
    # ============================================================================
    
    def calculate_transaction_amount(self, tx):
        """Calculate net amount for transaction"""
        if not self.wallet:
            return 0
        
        if tx.tx_type in ["coinbase", "genesis"]:
            for output in tx.outputs:
                if output.address == self.wallet.address:
                    return output.amount
            return 0
        
        if tx.tx_type in ["data", "dsa_verification"]:
            return 0
        
        sender_addr = CryptoUtils.pubkey_to_address(tx.sender)
        if sender_addr == self.wallet.address:
            # Outgoing transaction
            total_out = sum(output.amount for output in tx.outputs 
                           if output.address != self.wallet.address)
            return -total_out
        else:
            # Incoming transaction
            total_in = sum(output.amount for output in tx.outputs 
                          if output.address == self.wallet.address)
            return total_in
    
    def set_max_amount(self):
        """Set maximum available amount"""
        if not self.wallet:
            return
        
        # Use corrected balance calculation
            try:
                balance = self.override_wallet_get_balance()
            except AttributeError:
                balance = self.wallet.get_balance() if hasattr(self.wallet, "get_balance") else 0.0
        max_amount = max(0, balance - 0.0001)  # Leave small amount for fees
        self.amount_input.setValue(max_amount)
    
    def send_transaction(self):
        """Send a transaction"""
        if not self.wallet:
            QMessageBox.warning(self, "Transaction Error", "No wallet loaded")
            return
        
        if not self.blockchain.genesis_complete:
            QMessageBox.warning(self, "Transaction Error", "Please wait for genesis block to complete")
            return
        
        recipient = self.recipient_input.text().strip()
        amount = self.amount_input.value()
        
        if not recipient:
            QMessageBox.warning(self, "Transaction Error", "Please enter recipient address")
            return
        
        if amount <= 0:
            QMessageBox.warning(self, "Transaction Error", "Amount must be greater than zero")
            return
        
        # Use corrected balance calculation
            try:
                balance = self.override_wallet_get_balance()
            except AttributeError:
                balance = self.wallet.get_balance() if hasattr(self.wallet, "get_balance") else 0.0
        if amount > balance:
            QMessageBox.warning(self, "Transaction Error", 
                               f"Insufficient funds. Available: {balance:.8f} PYC")
            return
        
        try:
            tx = self.wallet.send(recipient, amount)
            if tx:
                self.log_message(f"Transaction sent: {tx.tx_id}")
                QMessageBox.information(self, "Transaction Sent", 
                                       f"Transaction sent successfully!\nTX ID: {tx.tx_id}")
                
                # Immediately commit the transaction to blockchain
                self.on_blockchain_changed("transaction_sent")
                
                # Clear inputs
                self.recipient_input.clear()
                self.amount_input.setValue(0)
                
                # Update stats
                self.stats['payments_sent'] += 1
                
                # Update UI
                self.original_update_ui()
                
                # Save blockchain after transaction
                self.save_blockchain()
            else:
                QMessageBox.warning(self, "Transaction Error", "Failed to create transaction")
                
        except Exception as e:
            self.log_message(f"Transaction error: {str(e)}")
            QMessageBox.critical(self, "Transaction Error", f"Error: {str(e)}")
    
    def show_transaction_details(self, item):
        """Show detailed transaction information (same as before)"""
        row = item.row()
        
        # Get transaction ID from table
        tx_id_item = self.tx_table.item(row, 5)
        if not tx_id_item:
            return
        
        tx_id_partial = tx_id_item.text().replace("...", "")
        
        # Find full transaction
        tx = None
        for transaction in self.wallet.get_transaction_history():
            if transaction.tx_id.startswith(tx_id_partial):
                tx = transaction
                break
        
        if not tx:
            return
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Transaction Details")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Transaction details
        details = QTextEdit()
        details.setReadOnly(True)
        
        details_text = f"""
<h3>Transaction Details</h3>
<p><b>Transaction ID:</b> {tx.tx_id}</p>
<p><b>Type:</b> {tx.tx_type.title()}</p>
<p><b>Timestamp:</b> {datetime.fromtimestamp(tx.timestamp).strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><b>Amount:</b> {self.calculate_transaction_amount(tx):.8f} PYC</p>
        """
        
        if tx.tx_type not in ["coinbase", "genesis"]:
            sender_addr = CryptoUtils.pubkey_to_address(tx.sender)
            details_text += f"<p><b>Sender:</b> {sender_addr}</p>"
        
        if tx.outputs:
            details_text += "<p><b>Recipients:</b></p><ul>"
            for output in tx.outputs:
                details_text += f"<li>{output.address}: {output.amount:.8f} PYC</li>"
            details_text += "</ul>"
        
        details.setHtml(details_text)
        layout.addWidget(details)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def export_transactions(self):
        """Export transaction history (same as before)"""
        if not self.wallet:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Transactions", 
            f"pythoncoin_transactions_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            transactions = self.wallet.get_transaction_history()
            
            with open(filename, 'w') as f:
                f.write("Date,Time,Type,From,To,Amount,Status,TX_ID\n")
                
                for tx in transactions:
                    dt = datetime.fromtimestamp(tx.timestamp)
                    date_str = dt.strftime('%Y-%m-%d')
                    time_str = dt.strftime('%H:%M:%S')
                    
                    if tx.tx_type in ["coinbase", "genesis"]:
                        from_addr = f"{tx.tx_type.title()} Distribution"
                        to_addr = self.wallet.address
                    elif tx.sender == self.wallet.public_key:
                        from_addr = self.wallet.address
                        to_addr = tx.outputs[0].address if tx.outputs else "N/A"
                    else:
                        from_addr = CryptoUtils.pubkey_to_address(tx.sender)
                        to_addr = self.wallet.address
                    
                    amount = self.calculate_transaction_amount(tx)
                    status = "Confirmed" if any(tx in block.transactions for block in self.blockchain.chain) else "Pending"
                    
                    f.write(f"{date_str},{time_str},{tx.tx_type},{from_addr},{to_addr},{amount:.8f},{status},{tx.tx_id}\n")
            
            self.log_message(f"Transactions exported to {filename}")
            QMessageBox.information(self, "Export Complete", f"Exported to {filename}")
            
        except Exception as e:
            self.log_message(f"Export error: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
    
    # ============================================================================
    # P2P Ad Network Functions (Enhanced)
    # ============================================================================
    
    def start_ad_network(self):
        """Start P2P ad network"""
        if not self.wallet:
            QMessageBox.warning(self, "Network Error", "No wallet loaded")
            return
        
        try:
            if self.p2p_manager and not self.p2p_manager.running:
                self.p2p_manager.start()
                self.log_message("P2P Ad Network started")
            
        except Exception as e:
            self.log_message(f"Error starting ad network: {str(e)}")
            QMessageBox.critical(self, "Network Error", f"Failed to start: {str(e)}")
    
    def stop_ad_network(self):
        """Stop P2P ad network"""
        try:
            if self.p2p_manager:
                self.p2p_manager.stop()
                self.log_message("P2P Ad Network stopped")
            
        except Exception as e:
            self.log_message(f"Error stopping ad network: {str(e)}")
    
    # ============================================================================
    # Mining Functions (Enhanced)
    # ============================================================================
    
    def toggle_mining(self):
        """Start or stop mining"""
        if not self.wallet:
            QMessageBox.warning(self, "Mining Error", "No wallet loaded")
            return
        
        if not self.blockchain.genesis_complete:
            QMessageBox.warning(self, "Mining Error", "Please wait for genesis block coordination to complete")
            return
        
        if self.mining_thread and self.mining_thread.isRunning():
            # Stop mining
            self.mining_thread.stop()
            self.mining_thread.wait()
            self.mining_thread = None
            
            self.mining_status.setText("Status: Not mining")
            self.mining_status_label.setText("Mining: Stopped")
            self.start_mining_button.setEnabled(True)
            self.stop_mining_button.setEnabled(False)
            
            self.log_message("Mining stopped")
        else:
            # Start mining
            mining_address = self.wallet.address
            threads = int(self.mining_threads.currentText().split()[0])
            
            try:
                self.mining_thread = CryptoMiningThread(
                    blockchain=self.blockchain,
                    wallet=self.wallet,
                    threads=threads
                )
                
                # Connect signals
                self.mining_thread.status_update.connect(self.on_mining_status_update)
                self.mining_thread.hashrate_update.connect(self.on_mining_hashrate_update)
                self.mining_thread.new_block.connect(self.on_new_block_mined)
                self.mining_thread.payment_processed.connect(self.on_payment_sent)
                
                # Start thread
                self.mining_thread.start()
                
                self.mining_status.setText("Status: Mining in progress")
                self.mining_status_label.setText("Mining: Active")
                self.start_mining_button.setEnabled(False)
                self.stop_mining_button.setEnabled(True)
                
                self.log_message(f"Mining started with {threads} threads")
                
            except Exception as e:
                self.log_message(f"Error starting mining: {str(e)}")
                QMessageBox.critical(self, "Mining Error", f"Failed to start mining: {str(e)}")
    
    # ============================================================================
    # Network Functions (Enhanced)
    # ============================================================================
    
    
    
    def start_enhanced_node_server(self):
        """Start enhanced node server with payment request handling"""
        try:
            if self.node:
                return
            
            host = "0.0.0.0"  # Listen on all interfaces
            port = 5000
            
            if hasattr(self, 'node_host') and self.node_host:
                host_text = self.node_host.text().strip()
                if host_text:
                    host = host_text
            
            if hasattr(self, 'node_port') and self.node_port:
                try:
                    port = self.get_safe_port_from_ui(self.node_port, 5000)
                except:
                    try:
                        port_value = self.node_port.value() if hasattr(self.node_port, 'value') else 5000
                        port = int(port_value)
                        if port < 1024 or port > 65535:
                            port = 5000
                    except:
                        port = 5000
            
            self.log_message(f"🚀 Starting enhanced node server on {host}:{port}")
            
            # Create enhanced node with payment request handling
            self.node = EnhancedPythonCoinNode(
                host=host, 
                port=port, 
                blockchain=self.blockchain, 
                wallet=self.wallet,
                main_wallet_instance=self
            )
            
            # Start node in thread
            threading.Thread(target=self.node.start, daemon=True).start()
            
            if hasattr(self, 'node_status'):
                self.node_status.setText(f"Status: Enhanced node running on {host}:{port}")
            if hasattr(self, 'start_node_button'):
                self.start_node_button.setEnabled(False)
            if hasattr(self, 'stop_node_button'):
                self.stop_node_button.setEnabled(True)
            
            self.log_message(f"✅ Enhanced node server started with payment request handling")
            
        except Exception as e:
            self.log_message(f"❌ Error starting enhanced node: {str(e)}")
            QMessageBox.critical(self, "Node Error", f"Failed to start enhanced node: {str(e)}")
    def stop_node(self):
        """Stop blockchain node"""
        if self.node:
            try:
                # Stop node
                self.node.stop()
                self.node = None
                
                self.node_status.setText("Status: Node not running")
                self.start_node_button.setEnabled(True)
                self.stop_node_button.setEnabled(False)
                
                self.log_message("Blockchain node stopped")
                
            except Exception as e:
                self.log_message(f"Error stopping node: {str(e)}")
    # ============================================================================
    # Ad Creation Support Methods
    # ============================================================================
    
    def preview_ad(self):
        """Enhanced preview using storage manager templates with live updates"""
        if not hasattr(self, 'ad_title_input') or not hasattr(self, 'ad_storage'):
            return
        
        try:
            title = self.ad_title_input.text().strip() or "Your Amazing Ad Title Here"
            description = self.ad_description_input.toPlainText().strip() or "Your compelling ad description will appear here. Make it engaging and informative to attract more clicks!"
            category = self.ad_category_combo.currentText() if hasattr(self, 'ad_category_combo') else "technology"
            payout = self.ad_payout_input.value() if hasattr(self, 'ad_payout_input') else 0.00100000
            click_url = self.ad_click_url_input.text().strip() if hasattr(self, 'ad_click_url_input') else "https://example.com"
            
            # Truncate for preview
            if len(title) > 50:
                title = title[:50] + "..."
            if len(description) > 150:
                description = description[:150] + "..."
            
            # Create preview metadata
            preview_metadata = {
                'id': 'preview_' + str(int(datetime.now().timestamp())),
                'title': title,
                'description': description,
                'category': category,
                'click_url': click_url if click_url.startswith(('http://', 'https://')) else f"https://{click_url}",
                'payout_rate': payout,
                'image_url': getattr(self, 'current_ad_image', ''),
                'advertiser_address': self.wallet.address if self.wallet else 'preview_address'
            }
            
            # Generate enhanced HTML preview
            preview_html = self.ad_storage.generate_html_ad(preview_metadata)
            
            # Add preview-specific styling
            preview_css = """
            <style>
                body { 
                    background: #f8f9fa; 
                    padding: 20px; 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                }
                .preview-banner {
                    background: linear-gradient(45deg, #17a2b8, #007bff);
                    color: white;
                    padding: 10px 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    text-align: center;
                    font-weight: bold;
                    animation: pulse 2s infinite;
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.8; }
                }
                .preview-info {
                    background: white;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 15px;
                    margin-top: 20px;
                    font-size: 14px;
                }
                .preview-stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-top: 15px;
                }
                .stat-item {
                    background: #f8f9fa;
                    padding: 10px;
                    border-radius: 6px;
                    text-align: center;
                }
                .stat-value {
                    font-size: 18px;
                    font-weight: bold;
                    color: #0066cc;
                }
                .stat-label {
                    font-size: 12px;
                    color: #6c757d;
                    margin-top: 4px;
                }
            </style>
            """
            
            preview_banner = """
            <div class="preview-banner">
                🎯 LIVE PREVIEW - This is how your ad will appear to users
            </div>
            """
            
            preview_info = f"""
            <div class="preview-info">
                <strong>📊 Preview Information</strong>
                <div class="preview-stats">
                    <div class="stat-item">
                        <div class="stat-value">{len(title)}</div>
                        <div class="stat-label">Title Characters</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{len(description)}</div>
                        <div class="stat-label">Description Characters</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{payout:.6f}</div>
                        <div class="stat-label">PYC Per Click</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{category.title()}</div>
                        <div class="stat-label">Category</div>
                    </div>
                </div>
                <p style="margin-top: 15px; color: #6c757d; font-size: 13px;">
                    💡 Tip: Keep titles under 50 characters and descriptions under 150 characters for best display.
                </p>
            </div>
            """
            
            # Combine all elements
            full_preview = preview_css + preview_banner + preview_html + preview_info
            
            if hasattr(self, 'ad_preview_area'):
                self.ad_preview_area.setHtml(full_preview)
            
        except Exception as e:
            self.log_message(f"❌ Error generating preview: {str(e)}")
            # Fallback to simple preview
            if hasattr(self, 'ad_preview_area'):
                self.ad_preview_area.setHtml(self.get_default_preview_html())

    def upload_ad_image(self):
        """Upload image for advertisement"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Ad Image", "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.webp);;All Files (*)"
        )
        
        if file_path:
            self.current_ad_image = file_path
            filename = os.path.basename(file_path)
            self.image_path_label.setText(f"Selected: {filename}")
            self.image_path_label.setStyleSheet("color: #28a745; font-weight: bold;")
            
            # Show image preview
            try:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(150, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.image_preview_label.setPixmap(scaled_pixmap)
                    self.image_preview_label.setText("")
                else:
                    self.image_preview_label.setText("Invalid Image")
            except Exception as e:
                self.image_preview_label.setText("Preview Error")
                logger.warning(f"Image preview error: {e}")
    
    def create_advertisement(self):
        """Enhanced advertisement creation with HTML/SVG storage and validation"""
        if not self.wallet:
            QMessageBox.warning(self, "Ad Creation Error", "No wallet loaded")
            return
        
        title = self.ad_title_input.text().strip()
        description = self.ad_description_input.toPlainText().strip()
        click_url = self.ad_click_url_input.text().strip()
        category = self.ad_category_combo.currentText()
        payout_rate = self.ad_payout_input.value()
        daily_budget = self.daily_budget_input.value()
        max_clicks = self.max_clicks_input.value()
        
        # Enhanced validation
        validation_errors = []
        
        if not title:
            validation_errors.append("Title is required")
        elif len(title) < 5:
            validation_errors.append("Title must be at least 5 characters")
        elif len(title) > 100:
            validation_errors.append("Title must be less than 100 characters")
        
        if not description:
            validation_errors.append("Description is required")
        elif len(description) < 20:
            validation_errors.append("Description must be at least 20 characters")
        elif len(description) > 500:
            validation_errors.append("Description must be less than 500 characters")
        
        if not click_url:
            click_url = 'https://example.com'
        elif not click_url.startswith(('http://', 'https://')):
            click_url = 'https://' + click_url
        
        if payout_rate <= 0:
            validation_errors.append("Payout rate must be greater than 0")
        elif payout_rate > 1.0:
            validation_errors.append("Payout rate cannot exceed 1.0 PYC")
        
        if daily_budget <= 0:
            validation_errors.append("Daily budget must be greater than 0")
        
        if validation_errors:
            QMessageBox.warning(self, "Validation Errors", "\n".join(validation_errors))
            return
        
        # Check balance
        try:
            balance = self.get_current_balance()
        except Exception as e:
            self.log_message(f"Error getting balance: {str(e)}")
            balance = 0.0
        
        if balance < daily_budget:
            QMessageBox.warning(self, "Insufficient Funds", 
                               f"You need at least {daily_budget:.8f} PYC for one day of advertising.\n"
                               f"Current balance: {balance:.8f} PYC")
            return
        
        try:
            # Show progress dialog
            progress = QProgressDialog("Creating advertisement...", "Cancel", 0, 4, self)
            progress.setWindowTitle("Creating Advertisement")
            progress.setModal(True)
            progress.show()
            QApplication.processEvents()
            
            # Step 1: Generate ad ID and data
            progress.setValue(1)
            progress.setLabelText("Generating advertisement data...")
            QApplication.processEvents()
            
            ad_id = str(uuid.uuid4())
            
            # Get targeting options
            interests = [i.strip() for i in self.target_interests.text().split(',') if i.strip()]
            targeting = {
                'interests': interests,
                'geographic': self.target_geo.currentText(),
                'budget_daily': daily_budget,
                'max_clicks_daily': max_clicks,
                'min_age': 18,
                'max_age': 65
            }
            
            # Step 2: Prepare ad data
            progress.setValue(2)
            progress.setLabelText("Preparing advertisement files...")
            QApplication.processEvents()
            
            ad_data = {
                'id': ad_id,
                'title': title,
                'description': description,
                'image_url': getattr(self, 'current_ad_image', ''),
                'click_url': click_url,
                'category': category,
                'targeting': targeting,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=30)).isoformat(),
                'peer_source': self.client_id,
                'payout_rate': payout_rate,
                'advertiser_address': self.wallet.address
            }
            
            # Step 3: Save to storage (both HTML and SVG)
            progress.setValue(3)
            progress.setLabelText("Saving advertisement files...")
            QApplication.processEvents()
            
            html_result = self.ad_storage.save_ad(ad_data, 'html')
            svg_result = self.ad_storage.save_ad(ad_data, 'svg')
            
            if not html_result['success']:
                progress.close()
                QMessageBox.critical(self, "Storage Error", 
                                   f"Failed to save HTML version: {html_result.get('error', 'Unknown error')}")
                return
            
            if not svg_result['success']:
                progress.close()
                QMessageBox.critical(self, "Storage Error", 
                                   f"Failed to save SVG version: {svg_result.get('error', 'Unknown error')}")
                return
            
            # Step 4: Create AdContent object and update UI
            progress.setValue(4)
            progress.setLabelText("Finalizing advertisement...")
            QApplication.processEvents()
            
            ad = AdContent(
                id=ad_id,
                title=title,
                description=description,
                image_url=ad_data.get('image_url', ''),
                click_url=click_url,
                category=category,
                targeting=targeting,
                created_at=ad_data['created_at'],
                expires_at=ad_data['expires_at'],
                peer_source=self.client_id,
                payout_rate=payout_rate,
                advertiser_address=self.wallet.address
            )
            
            # Add to local ads
            self.ads.append(ad)
            
            # Update database if connected
            if self.db_connected:
                try:
                    self.update_database_on_ad_creation(ad)
                except Exception as e:
                    self.log_message(f"Database update error: {str(e)}")
            
            # Broadcast to P2P network if connected
            if self.p2p_manager and self.p2p_manager.running:
                try:
                    self.broadcast_new_ad(ad)
                except Exception as e:
                    self.log_message(f"P2P broadcast error: {str(e)}")
            
            # Update UI
            self.update_my_ads_table()
            self.clear_ad_form()
            
            progress.close()
            
            # Show success dialog with detailed info
            success_msg = f"""Advertisement '{title}' created successfully!

📄 Formats Created:
   • HTML: {html_result['file_path']}
   • SVG: {svg_result['file_path']}

💰 Configuration:
   • Payout: {payout_rate:.8f} PYC per click
   • Daily Budget: {daily_budget:.8f} PYC
   • Max Clicks: {max_clicks:,}
   • Category: {category}

🌐 Network Status:
   • Ad ID: {ad_id[:16]}...
   • P2P Network: {'Online' if self.p2p_manager and self.p2p_manager.running else 'Offline'}
   • Database: {'Connected' if self.db_connected else 'Offline'}

Your advertisement is now live and ready to earn PYC!"""
            
            QMessageBox.information(self, "Advertisement Created", success_msg)
            
            self.log_message(f"✅ Created advertisement: {title} (ID: {ad_id[:8]}...)")
            self.log_message(f"📁 HTML: {html_result['file_path']}")
            self.log_message(f"📁 SVG: {svg_result['file_path']}")
            
            self.stats['ads_served'] += 1
            
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            self.log_message(f"❌ Error creating advertisement: {str(e)}")
            QMessageBox.critical(self, "Creation Error", f"Failed to create advertisement: {str(e)}")

    def original_create_advertisement(self):
        """Create and publish advertisement to P2P network"""
        if not self.wallet:
            QMessageBox.warning(self, "Ad Creation Error", "No wallet loaded")
            return
        
        title = self.ad_title_input.text().strip()
        description = self.ad_description_input.toPlainText().strip()
        click_url = self.ad_click_url_input.text().strip()
        category = self.ad_category_combo.currentText()
        payout_rate = self.ad_payout_input.value()
        daily_budget = self.daily_budget_input.value()
        max_clicks = self.max_clicks_input.value()
        
        # Validation
        if not title or not description:
            QMessageBox.warning(self, "Validation Error", "Please fill in title and description")
            return
        
        if len(title) < 5:
            QMessageBox.warning(self, "Validation Error", "Title must be at least 5 characters")
            return
        
        if len(description) < 20:
            QMessageBox.warning(self, "Validation Error", "Description must be at least 20 characters")
            return
        
        if not click_url.startswith(('http://', 'https://')):
            click_url = 'http://' + click_url if click_url else 'https://example.com'
        
        # Check if advertiser has enough balance for at least one day of ads
        try:
            # Try multiple methods to get balance with fallbacks
            balance = 0.0
            
            # Method 1: Try override method if it exists
            if hasattr(self, 'override_wallet_get_balance'):
                try:
                    balance = self.override_wallet_get_balance()
                except Exception as e:
                    self.log_message(f"Override balance method failed: {str(e)}")
                    balance = 0.0
            
            # Method 2: Try wallet get_balance if override failed
            if balance == 0.0 and hasattr(self.wallet, 'get_balance'):
                try:
                    balance = self.wallet.get_balance()
                except Exception as e:
                    self.log_message(f"Wallet balance method failed: {str(e)}")
                    balance = 0.0
            
            # Method 3: Try blockchain get_balance as final fallback
            if balance == 0.0 and hasattr(self.blockchain, 'get_balance') and self.wallet:
                try:
                    balance = self.blockchain.get_balance(self.wallet.address)
                except Exception as e:
                    self.log_message(f"Blockchain balance method failed: {str(e)}")
                    balance = 0.0
            
            self.log_message(f"Current balance: {balance:.8f} PYC")
            
        except Exception as e:
            self.log_message(f"Error getting balance: {str(e)}")
            balance = 0.0
        
        # Check if sufficient funds available
        if balance < daily_budget:
            QMessageBox.warning(self, "Insufficient Funds", 
                               f"You need at least {daily_budget:.8f} PYC for one day of advertising.\n"
                               f"Current balance: {balance:.8f} PYC")
            return
        
        try:
            # Create ad object
            ad_id = str(uuid.uuid4())
            
            # Get image URL (in real implementation, upload to IPFS or similar)
            image_url = ""
            if hasattr(self, 'current_ad_image'):
                image_url = f"file://{self.current_ad_image}"  # Local file for demo
            
            # Get targeting options
            interests = [i.strip() for i in self.target_interests.text().split(',') if i.strip()]
            targeting = {
                'interests': interests,
                'geographic': self.target_geo.currentText(),
                'budget_daily': daily_budget,
                'max_clicks_daily': max_clicks
            }
            
            ad = AdContent(
                id=ad_id,
                title=title,
                description=description,
                image_url=image_url,
                click_url=click_url,
                category=category,
                targeting=targeting,
                created_at=datetime.now().isoformat(),
                expires_at=(datetime.now() + timedelta(days=30)).isoformat(),
                peer_source=self.client_id,
                payout_rate=payout_rate,
                advertiser_address=self.wallet.address
            )
            
            # Add to local ads
            self.ads.append(ad)
            
            # Update database
            self.update_database_on_ad_creation(ad)
            
            # Broadcast to P2P network if connected
            if self.p2p_manager and self.p2p_manager.running:
                self.broadcast_new_ad(ad)
            
            # Update my ads table
            self.update_my_ads_table()
            
            # Clear form
            self.clear_ad_form()
            
            QMessageBox.information(self, "Success", 
                                   f"Advertisement '{title}' created successfully!\n\n"
                                   f"• Payout: {payout_rate:.8f} PYC per click\n"
                                   f"• Daily Budget: {daily_budget:.8f} PYC\n"
                                   f"• Max Clicks: {max_clicks:,}\n\n"
                                   f"Your ad is now live on the P2P network!")
            
            self.log_message(f"Created new advertisement: {title}")
            
            # Update stats
            self.stats['ads_served'] += 1
            
        except Exception as e:
            self.log_message(f"Error creating advertisement: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to create advertisement: {str(e)}")
    def clear_ad_form(self):
        """Clear the ad creation form"""
        self.ad_title_input.clear()
        self.ad_description_input.clear()
        self.ad_click_url_input.clear()
        self.target_interests.clear()
        self.ad_payout_input.setValue(0.00100000)
        self.daily_budget_input.setValue(1.0)
        self.max_clicks_input.setValue(1000)
        self.image_path_label.setText("No image selected")
        self.image_path_label.setStyleSheet("color: #666; font-style: italic;")
        self.image_preview_label.clear()
        self.image_preview_label.setText("Image Preview")
        if hasattr(self, 'current_ad_image'):
            delattr(self, 'current_ad_image')
        self.ad_preview_area.setHtml(self.get_default_preview_html())
    
    def broadcast_new_ad(self, ad):
        """Broadcast new ad to P2P network"""
        if not self.p2p_manager or not self.p2p_manager.running:
            return
        
        broadcast_message = {
            'type': 'new_ad_broadcast',
            'ad_data': ad.to_dict(),
            'broadcaster': self.client_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to all connected peers
        for peer_id, sock in self.p2p_manager.peer_sockets.items():
            try:
                self.p2p_manager._send_message(sock, broadcast_message)
            except Exception as e:
                logger.error(f"Failed to broadcast ad to peer {peer_id}: {e}")
    
    def update_my_ads_table(self):
        """Update my advertisements table"""
        if not hasattr(self, 'my_ads_table'):
            return
        
        my_ads = [ad for ad in self.ads if ad.advertiser_address == self.wallet.address]
        
        self.my_ads_table.setRowCount(len(my_ads))
        
        for row, ad in enumerate(my_ads):
            # Title
            title_item = QTableWidgetItem(ad.title)
            title_item.setToolTip(ad.description)
            self.my_ads_table.setItem(row, 0, title_item)
            
            # Category
            self.my_ads_table.setItem(row, 1, QTableWidgetItem(ad.category.title()))
            
            # Payout
            payout_item = QTableWidgetItem(f"{ad.payout_rate:.8f}")
            payout_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.my_ads_table.setItem(row, 2, payout_item)
            
            # Count clicks and calculate spent
            ad_clicks = len([c for c in self.click_events if c.ad_id == ad.id])
            spent = ad_clicks * ad.payout_rate
            
            clicks_item = QTableWidgetItem(str(ad_clicks))
            clicks_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.my_ads_table.setItem(row, 3, clicks_item)
            
            spent_item = QTableWidgetItem(f"{spent:.8f}")
            spent_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.my_ads_table.setItem(row, 4, spent_item)
            
            # Status
            status = "Active" if datetime.now().isoformat() < ad.expires_at else "Expired"
            status_item = QTableWidgetItem(status)
            if status == "Active":
                status_item.setForeground(QColor(40, 167, 69))  # Green
            else:
                status_item.setForeground(QColor(220, 53, 69))  # Red
            self.my_ads_table.setItem(row, 5, status_item)
            
            # Actions (simple text for now)
            actions_item = QTableWidgetItem("📊 View Stats")
            self.my_ads_table.setItem(row, 6, actions_item)
    
    def update_ad_network_stats(self):
        """Update ad network statistics display"""
        if not hasattr(self, 'ad_stats_layout'):
            return
        
        # Clear existing widgets
        for i in reversed(range(self.ad_stats_layout.count())): 
            self.ad_stats_layout.itemAt(i).widget().setParent(None)
        
        # Calculate stats
        my_ads = [ad for ad in self.ads if ad.advertiser_address == self.wallet.address]
        total_clicks = len([c for c in self.click_events if any(c.ad_id == ad.id for ad in my_ads)])
        total_spent = sum(c.payout_amount for c in self.click_events if any(c.ad_id == ad.id for ad in my_ads))
        avg_cpc = total_spent / max(1, total_clicks)
        
        # Create stats labels
        stats = [
            f"📊 My Active Ads: {len(my_ads)}",
            f"👆 Total Clicks: {total_clicks:,}",
            f"💸 Total Spent: {total_spent:.8f} PYC",
            f"📈 Average CPC: {avg_cpc:.8f} PYC",
            f"🌐 Network Ads: {len(self.ads)}",
            f"👥 Connected Peers: {len([p for p in self.peers.values() if p.status == 'connected'])}"
        ]
        
        for stat in stats:
            label = QLabel(stat)
            label.setStyleSheet("color: #333; font-size: 12px; padding: 2px;")
            self.ad_stats_layout.addWidget(label)
    
    def edit_advertisement(self):
        """Edit selected advertisement"""
        current_row = self.my_ads_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select an advertisement to edit")
            return
        
        my_ads = [ad for ad in self.ads if ad.advertiser_address == self.wallet.address]
        if current_row < len(my_ads):
            ad = my_ads[current_row]
            
            # Populate form with existing data
            self.ad_title_input.setText(ad.title)
            self.ad_description_input.setPlainText(ad.description)
            self.ad_click_url_input.setText(ad.click_url)
            self.ad_payout_input.setValue(ad.payout_rate)
            
            # Set category
            category_index = self.ad_category_combo.findText(ad.category)
            if category_index >= 0:
                self.ad_category_combo.setCurrentIndex(category_index)
            
            # Set targeting
            interests = ad.targeting.get('interests', [])
            self.target_interests.setText(', '.join(interests))
            
            self.preview_ad()
    
    def pause_advertisement(self):
        """Pause/resume selected advertisement"""
        current_row = self.my_ads_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select an advertisement")
            return
        
        QMessageBox.information(self, "Ad Paused", "Advertisement has been paused(Feature coming soon)")
    
    def delete_advertisement(self):
        """Delete selected advertisement"""
        current_row = self.my_ads_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select an advertisement to delete")
            return
        
        my_ads = [ad for ad in self.ads if ad.advertiser_address == self.wallet.address]
        if current_row < len(my_ads):
            ad_to_remove = my_ads[current_row]
            
            reply = QMessageBox.question(self, "Confirm Delete", 
                                       f"Are you sure you want to delete '{ad_to_remove.title}'?"
                                       f"This action cannot be undone.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.ads.remove(ad_to_remove)
                self.update_my_ads_table()
                QMessageBox.information(self, "Ad Deleted", "Advertisement has been deleted")
                self.log_message(f"Deleted advertisement: {ad_to_remove.title}")
    # ============================================================================
    # Blockchain Persistence Methods
    # ============================================================================
    
    def save_blockchain(self):
        """Save blockchain to file"""
        try:
            # Get difficulty from last block or use default
            difficulty = 2  # Default difficulty
            if self.blockchain.chain:
                last_block = self.blockchain.chain[-1]
                if hasattr(last_block, 'difficulty'):
                    difficulty = last_block.difficulty
            
            # Get mining reward - use default if not available
            mining_reward = 50  # Default mining reward
            if hasattr(self.blockchain, 'mining_reward'):
                mining_reward = self.blockchain.mining_reward
            
            blockchain_data = {
                'chain': [block.to_dict() for block in self.blockchain.chain],
                'pending_transactions': [tx.to_dict() for tx in self.blockchain.pending_transactions],
                'genesis_complete': getattr(self.blockchain, 'genesis_complete', False),
                'genesis_addresses': getattr(self.blockchain, 'genesis_addresses', []),
                'difficulty': difficulty,
                'mining_reward': mining_reward,
                'saved_timestamp': time.time(),
                'saved_datetime': datetime.now().isoformat()
            }
            
            with open("blockchain.json", "w") as f:
                json.dump(blockchain_data, f, indent=2)
            
            self.log_message("Blockchain saved successfully")
            
        except Exception as e:
            self.log_message(f"Error saving blockchain: {str(e)}")
            logger.error(f"Blockchain save error: {str(e)}")
    
    def load_blockchain(self):
        """Load blockchain from file"""
        try:
            if not os.path.exists("blockchain.json"):
                self.log_message("No saved blockchain found - creating new blockchain")
                return False
            
            with open("blockchain.json", "r") as f:
                blockchain_data = json.load(f)
            
            # Reconstruct blockchain
            self.blockchain = Blockchain()
            
            # Load basic properties safely
            self.blockchain.genesis_complete = blockchain_data.get('genesis_complete', False)
            self.blockchain.genesis_addresses = blockchain_data.get('genesis_addresses', [])
            
            # Only set difficulty and mining_reward if the blockchain supports them
            if hasattr(self.blockchain, 'difficulty'):
                self.blockchain.difficulty = blockchain_data.get('difficulty', 2)
            if hasattr(self.blockchain, 'mining_reward'):
                self.blockchain.mining_reward = blockchain_data.get('mining_reward', 50)
            
            # Reconstruct blocks
            chain_data = blockchain_data.get('chain', [])
            self.blockchain.chain = []
            
            for block_data in chain_data:
                # Reconstruct transactions for this block
                transactions = []
                for tx_data in block_data.get('transactions', []):
                    tx = self.reconstruct_transaction(tx_data)
                    if tx:
                        transactions.append(tx)
                
                # Create block object
                from pythoncoin import Block
                block = Block(
                    index=block_data['index'],
                    timestamp=block_data['timestamp'],
                    transactions=transactions,
                    previous_hash=block_data['previous_hash']
                )
                
                # Set additional block properties
                block.hash = block_data['hash']
                block.nonce = block_data['nonce']
                
                # Only set difficulty if the block supports it
                if hasattr(block, 'difficulty'):
                    block.difficulty = block_data.get('difficulty', 2)
                
                self.blockchain.chain.append(block)
            
            # Reconstruct pending transactions
            pending_data = blockchain_data.get('pending_transactions', [])
            self.blockchain.pending_transactions = []
            
            for tx_data in pending_data:
                tx = self.reconstruct_transaction(tx_data)
                if tx:
                    self.blockchain.pending_transactions.append(tx)
            
            saved_datetime = blockchain_data.get('saved_datetime', 'Unknown')
            chain_length = len(self.blockchain.chain)
            pending_count = len(self.blockchain.pending_transactions)
            
            self.log_message(f"Blockchain loaded: {chain_length} blocks, {pending_count} pending transactions")
            self.log_message(f"Last saved: {saved_datetime}")
            
            return True
            
            # Verify balance after loading
            QTimer.singleShot(2000, self.verify_wallet_balance_after_load)
            
            # Verify balance after loading
            QTimer.singleShot(2000, self.verify_wallet_balance_after_load)
            
        except Exception as e:
            self.log_message(f"Error loading blockchain: {str(e)}")
            logger.error(f"Blockchain load error: {str(e)}")
            # Create new blockchain on load failure
            self.blockchain = Blockchain()
            return False
    
    def reconstruct_transaction(self, tx_data):
        """Reconstruct a transaction object from saved data"""
        try:
            from pythoncoin import Transaction, TransactionInput, TransactionOutput, DataTransaction, DSAVerificationTransaction
            
            tx_type = tx_data.get('tx_type', 'regular')
            
            if tx_type == 'data':
                # Reconstruct DataTransaction
                tx = DataTransaction(
                    sender=tx_data['sender'],
                    data_content=tx_data.get('data_content', ''),
                    private_key=None  # Don't need private key for reconstruction
                )
                tx.tx_id = tx_data['tx_id']
                tx.timestamp = tx_data['timestamp']
                tx.signature = tx_data.get('signature', '')
                return tx
                
            elif tx_type == 'dsa_verification':
                # Reconstruct DSAVerificationTransaction
                tx = DSAVerificationTransaction(
                    sender=tx_data['sender'],
                    message=tx_data.get('message', ''),
                    private_key=None  # Don't need private key for reconstruction
                )
                tx.tx_id = tx_data['tx_id']
                tx.timestamp = tx_data['timestamp']
                tx.signature = tx_data.get('signature', '')
                return tx
                
            else:
                # Reconstruct regular Transaction (including coinbase and genesis)
                # Reconstruct inputs
                inputs = []
                for input_data in tx_data.get('inputs', []):
                    tx_input = TransactionInput(
                        tx_id=input_data['tx_id'],
                        output_index=input_data['output_index'],
                        signature=input_data.get('signature', '')
                    )
                    inputs.append(tx_input)
                
                # Reconstruct outputs - CRITICAL for balance calculation
                outputs = []
                for output_data in tx_data.get('outputs', []):
                    tx_output = TransactionOutput(
                        address=output_data['address'],
                        amount=float(output_data['amount'])  # Ensure float conversion
                    )
                    outputs.append(tx_output)
                
                # Create transaction
                tx = Transaction(
                    sender=tx_data.get('sender', ''),
                    inputs=inputs,
                    outputs=outputs
                )
                
                # Set all transaction properties
                tx.tx_id = tx_data['tx_id']
                tx.timestamp = tx_data['timestamp']
                tx.tx_type = tx_data.get('tx_type', 'regular')
                tx.signature = tx_data.get('signature', '')
                
                # Log reconstruction for debugging
                if tx.tx_type in ['coinbase', 'genesis']:
                    total_output = sum(output.amount for output in outputs)
                    logger.info(f"Reconstructed {tx.tx_type} transaction: {total_output} PYC total output")
                
                return tx
                
        except Exception as e:
            logger.error(f"Error reconstructing transaction: {str(e)}")
            logger.error(f"Transaction data: {tx_data}")
            return None
    def auto_save_blockchain(self):
        """Automatically save blockchain periodically"""
        if hasattr(self, 'blockchain') and self.blockchain:
            self.save_blockchain()
    
    def setup_auto_save_timer(self):
        """Setup automatic blockchain saving every 30 seconds"""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_blockchain)
        self.auto_save_timer.start(30000)  # 30 seconds
        self.log_message("Auto-save enabled: blockchain will be saved every 30 seconds")
    def delayed_initial_update(self):
        """Delayed initial UI update after all components are ready"""
        try:
            if self.wallet and self.blockchain:
                self.original_update_ui()
                self.log_message("Wallet and blockchain ready - UI updated")
                
                # Run comprehensive balance check on startup
                QTimer.singleShot(2000, self.debug_balance_calculation)
            else:
                self.log_message("Waiting for wallet/blockchain initialization...")
                # Try again in another second
                QTimer.singleShot(1000, self.delayed_initial_update)
        except Exception as e:
            self.log_message(f"Delayed update error: {str(e)}")
    # ============================================================================
    # Balance Verification and Debugging Methods
    # ============================================================================
    
    def verify_wallet_balance_after_load(self):
        """Verify and debug wallet balance after blockchain load"""
        if not self.wallet or not self.blockchain:
            return
        
        try:
            self.log_message("=== WALLET BALANCE VERIFICATION ===")
            self.log_message(f"Wallet Address: {self.wallet.address}")
            self.log_message(f"Blockchain Height: {len(self.blockchain.chain)}")
            
            # Debug balance calculation
            # Use corrected balance calculation
            try:
                balance = self.override_wallet_get_balance()
            except AttributeError:
                balance = self.wallet.get_balance() if hasattr(self.wallet, "get_balance") else 0.0
            self.log_message(f"Calculated Balance: {balance:.8f} PYC")
            
            # Manual balance verification
            manual_balance = self.calculate_manual_balance()
            self.log_message(f"Manual Balance Check: {manual_balance:.8f} PYC")
            
            if abs(balance - manual_balance) > 0.00000001:
                self.log_message("⚠️ WARNING: Balance mismatch detected!")
            else:
                self.log_message("✅ Balance verification passed")
            
            # Count transactions involving this wallet
            tx_count = self.count_wallet_transactions()
            self.log_message(f"Transactions involving wallet: {tx_count}")
            
            # Check for mining rewards
            mining_rewards = self.calculate_mining_rewards()
            self.log_message(f"Mining rewards earned: {mining_rewards:.8f} PYC")
            
            self.log_message("=== END VERIFICATION ===")
            
        except Exception as e:
            self.log_message(f"Balance verification error: {str(e)}")
    
    def calculate_manual_balance(self):
        """Manually calculate balance by examining all blockchain transactions"""
        if not self.wallet or not self.blockchain:
            return 0.0
        
        balance = 0.0
        wallet_address = self.wallet.address
        
        try:
            # Go through every block and every transaction
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    # Check if this transaction involves our wallet
                    
                    # For coinbase and genesis transactions (mining rewards, initial distribution)
                    if tx.tx_type in ['coinbase', 'genesis']:
                        for output in tx.outputs:
                            if output.address == wallet_address:
                                balance += output.amount
                                self.log_message(f"  +{output.amount:.8f} PYC from {tx.tx_type} (block {block.index})")
                    
                    # For regular transactions
                    elif tx.tx_type == 'regular':
                        # Check if we're the sender (subtract outputs to others)
                        sender_address = CryptoUtils.pubkey_to_address(tx.sender) if tx.sender else None
                        if sender_address == wallet_address:
                            for output in tx.outputs:
                                if output.address != wallet_address:
                                    balance -= output.amount
                                    self.log_message(f"  -{output.amount:.8f} PYC sent to {output.address[:8]}...")
                        
                        # Check if we're receiving (add outputs to us)
                        for output in tx.outputs:
                            if output.address == wallet_address:
                                balance += output.amount
                                self.log_message(f"  +{output.amount:.8f} PYC received from transaction")
            
            return balance
            
        except Exception as e:
            self.log_message(f"Manual balance calculation error: {str(e)}")
            return 0.0
    
    def count_wallet_transactions(self):
        """Count transactions involving this wallet"""
        if not self.wallet or not self.blockchain:
            return 0
        
        count = 0
        wallet_address = self.wallet.address
        
        try:
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    involved = False
                    
                    # Check if we're in outputs
                    for output in tx.outputs:
                        if output.address == wallet_address:
                            involved = True
                            break
                    
                    # Check if we're the sender
                    if not involved and tx.sender:
                        sender_address = CryptoUtils.pubkey_to_address(tx.sender)
                        if sender_address == wallet_address:
                            involved = True
                    
                    if involved:
                        count += 1
            
            return count
            
        except Exception as e:
            self.log_message(f"Transaction count error: {str(e)}")
            return 0
    
    def calculate_mining_rewards(self):
        """Calculate total mining rewards earned by this wallet"""
        if not self.wallet or not self.blockchain:
            return 0.0
        
        rewards = 0.0
        wallet_address = self.wallet.address
        
        try:
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    if tx.tx_type == 'coinbase':
                        for output in tx.outputs:
                            if output.address == wallet_address:
                                rewards += output.amount
            
            return rewards
            
        except Exception as e:
            self.log_message(f"Mining rewards calculation error: {str(e)}")
            return 0.0
    
    def fix_missing_mining_rewards(self):
        """Fix missing mining rewards by checking for unrewarded blocks"""
        if not self.wallet or not self.blockchain:
            return
        
        try:
            self.log_message("🔍 Checking for missing mining rewards...")
            
            missing_rewards = 0
            for block in self.blockchain.chain:
                # Check if block has coinbase transaction
                has_coinbase = any(tx.tx_type == 'coinbase' for tx in block.transactions)
                
                if not has_coinbase and block.index > 0:  # Skip genesis block
                    self.log_message(f"⚠️ Block {block.index} missing coinbase transaction")
                    missing_rewards += 1
            
            if missing_rewards > 0:
                self.log_message(f"Found {missing_rewards} blocks without mining rewards")
                self.log_message("Note: This might be why your balance is low")
            else:
                self.log_message("✅ All blocks have proper coinbase transactions")
                
        except Exception as e:
            self.log_message(f"Missing rewards check error: {str(e)}")
    def save_wallet_state(self):
        """Save additional wallet state information"""
        if not self.wallet:
            return
        
        try:
            # Calculate and save current balance
            current_balance = 0.0
            
            try:
                # Try override method first
                if hasattr(self, 'override_wallet_get_balance'):
                    current_balance = self.override_wallet_get_balance()
                else:
                    # Fallback to standard wallet method
                    current_balance = self.wallet.get_balance() if hasattr(self.wallet, "get_balance") else 0.0
            except AttributeError:
                # Final fallback if methods don't exist
                current_balance = self.wallet.get_balance() if hasattr(self.wallet, "get_balance") else 0.0
            except Exception as e:
                self.log_message(f"Error calculating balance for state save: {str(e)}")
                current_balance = 0.0
            
            wallet_state = {
                'address': self.wallet.address,
                'private_key': self.wallet.private_key,
                'public_key': self.wallet.public_key,
                'last_known_balance': current_balance,
                'last_updated': datetime.now().isoformat(),
                'blockchain_height_at_save': len(self.blockchain.chain) if self.blockchain else 0
            }
            
            with open("wallet_state.json", "w") as f:
                json.dump(wallet_state, f, indent=2)
            
            self.log_message(f"Wallet state saved - Balance: {current_balance:.8f} PYC")
            
        except Exception as e:
            self.log_message(f"Error saving wallet state: {str(e)}")
    def load_wallet_state(self):
        """Load and verify wallet state"""
        try:
            if os.path.exists("wallet_state.json"):
                with open("wallet_state.json", "r") as f:
                    wallet_state = json.load(f)
                
                last_balance = wallet_state.get('last_known_balance', 0)
                last_height = wallet_state.get('blockchain_height_at_save', 0)
                current_height = len(self.blockchain.chain) if self.blockchain else 0
                
                self.log_message(f"Last known balance: {last_balance:.8f} PYC (at height {last_height})")
                self.log_message(f"Current blockchain height: {current_height}")
                
                if current_height > last_height:
                    self.log_message(f"Blockchain grew by {current_height - last_height} blocks since last save")
                
        except Exception as e:
            self.log_message(f"Error loading wallet state: {str(e)}")
    # ============================================================================
    # Balance Verification and Debugging Methods
    # ============================================================================
    
    def commit_blockchain_immediately(self, reason="network_update"):
        """Immediately save blockchain when it changes from network activity"""
        try:
            # Save blockchain
            self.save_blockchain()
            
            # Also save wallet state
            if hasattr(self, 'save_wallet_state'):
                self.save_wallet_state()
            
            # Log the commit
            chain_height = len(self.blockchain.chain) if self.blockchain else 0
            pending_count = len(self.blockchain.pending_transactions) if self.blockchain else 0
            
            self.log_message(f"🔄 Blockchain committed: {reason} (Height: {chain_height}, Pending: {pending_count})")
            
        except Exception as e:
            self.log_message(f"❌ Failed to commit blockchain: {str(e)}")
            logger.error(f"Blockchain commit error: {str(e)}")
    
    def on_blockchain_changed(self, reason="unknown"):
        """Called whenever the blockchain state changes"""
        # Immediate save when blockchain changes
        self.commit_blockchain_immediately(reason)
        
        # Update UI to reflect changes
        if hasattr(self, 'update_ui'):
            self.original_update_ui()
    
    def add_transaction_to_blockchain(self, transaction):
        """Add transaction and immediately commit"""
        try:
            if self.blockchain and transaction:
                # Add to pending transactions
                if transaction not in self.blockchain.pending_transactions:
                    self.blockchain.pending_transactions.append(transaction)
                    self.log_message(f"📥 Added transaction to pending pool: {transaction.tx_id[:16]}...")
                    
                    # Immediate commit
                    self.on_blockchain_changed("new_transaction_received")
                    return True
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error adding transaction: {str(e)}")
            return False
    
    def add_block_to_blockchain(self, block):
        """Add block and immediately commit"""
        try:
            if self.blockchain and block:
                # Validate block before adding
                if self.validate_received_block(block):
                    self.blockchain.chain.append(block)
                    
                    # Remove transactions from pending that are now in the block
                    for tx in block.transactions:
                        if tx in self.blockchain.pending_transactions:
                            self.blockchain.pending_transactions.remove(tx)
                    
                    self.log_message(f"📦 Added block to blockchain: Height {block.index}, Hash {block.hash[:16]}...")
                    
                    # Immediate commit
                    self.on_blockchain_changed("new_block_received")
                    return True
                else:
                    self.log_message(f"❌ Invalid block rejected: {block.hash[:16]}...")
                    return False
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error adding block: {str(e)}")
            return False
    
    def validate_received_block(self, block):
        """Basic validation for received blocks"""
        try:
            # Basic checks
            if not block or not hasattr(block, 'hash') or not hasattr(block, 'index'):
                return False
            
            # Check if block already exists
            for existing_block in self.blockchain.chain:
                if existing_block.hash == block.hash:
                    self.log_message(f"⚠️ Block already exists: {block.hash[:16]}...")
                    return False
            
            # Check if block index is sequential
            expected_index = len(self.blockchain.chain)
            if block.index != expected_index:
                self.log_message(f"⚠️ Block index mismatch: expected {expected_index}, got {block.index}")
                return False
            
            # Check previous hash
            if len(self.blockchain.chain) > 0:
                last_block = self.blockchain.chain[-1]
                if block.previous_hash != last_block.hash:
                    self.log_message(f"⚠️ Previous hash mismatch in block {block.index}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Block validation error: {str(e)}")
            return False
    def enhance_node_server_for_immediate_commit(self):
        """Note: Node server should call wallet commit methods when blockchain changes"""
        # When node server receives new blocks or transactions, it should call:
        # - self.add_block_to_blockchain(block) for new blocks
        # - self.add_transaction_to_blockchain(tx) for new transactions
        # This ensures immediate persistence of network-received data
        pass
    def safe_add_transaction(self, transaction):
        """Safely add transaction with immediate commit"""
        try:
            result = self.blockchain.add_transaction(transaction)
            if result:
                self.on_blockchain_changed("transaction_added")
            return result
        except Exception as e:
            self.log_message(f"❌ Error adding transaction: {str(e)}")
            return False
    
    def safe_mine_block(self, mining_address):
        """Safely mine block with immediate commit"""
        try:
            block = self.blockchain.mine_pending_transactions(mining_address)
            if block:
                self.on_blockchain_changed("block_mined")
            return block
        except Exception as e:
            self.log_message(f"❌ Error mining block: {str(e)}")
            return None
    # ============================================================================
    # Comprehensive Balance Debugging Methods
    # ============================================================================
        
    def debug_balance_calculation(self):
        """Comprehensive balance debugging with detailed logging"""
        if not self.wallet or not self.blockchain:
            self.log_message("❌ Cannot debug balance - wallet or blockchain missing")
            return
        
        try:
            self.log_message("🔍 ===== COMPREHENSIVE BALANCE DEBUG =====")
            self.log_message(f"Wallet Address: {self.wallet.address}")
            self.log_message(f"Blockchain Height: {len(self.blockchain.chain)} blocks")
            self.log_message(f"Pending Transactions: {len(self.blockchain.pending_transactions)}")
            
            # Check wallet's calculated balance using corrected balance calculation
            wallet_balance = 0.0
            try:
                if hasattr(self, 'override_wallet_get_balance'):
                    wallet_balance = self.override_wallet_get_balance()
                    self.log_message(f"Override wallet balance: {wallet_balance:.8f} PYC")
                else:
                    wallet_balance = self.wallet.get_balance() if hasattr(self.wallet, "get_balance") else 0.0
                    self.log_message(f"Wallet.get_balance(): {wallet_balance:.8f} PYC")
            except Exception as e:
                self.log_message(f"❌ Wallet balance calculation failed: {str(e)}")
                wallet_balance = 0.0
            
            # Manual balance calculation
            manual_balance = 0.0
            try:
                manual_balance = self.calculate_balance_manually()
                self.log_message(f"Manual calculation: {manual_balance:.8f} PYC")
            except Exception as e:
                self.log_message(f"❌ Manual balance calculation failed: {str(e)}")
            
            # Check coinbase transactions specifically
            coinbase_rewards = 0.0
            try:
                coinbase_rewards = self.check_coinbase_transactions()
                self.log_message(f"Coinbase rewards found: {coinbase_rewards:.8f} PYC")
            except Exception as e:
                self.log_message(f"❌ Coinbase check failed: {str(e)}")
            
            # Check each block for mining rewards
            try:
                self.audit_mining_rewards()
            except Exception as e:
                self.log_message(f"❌ Mining rewards audit failed: {str(e)}")
            
            # Check blockchain get_balance method directly
            blockchain_balance = 0.0
            try:
                blockchain_balance = self.blockchain.get_balance(self.wallet.address)
                self.log_message(f"Blockchain.get_balance(): {blockchain_balance:.8f} PYC")
            except Exception as e:
                self.log_message(f"❌ Blockchain.get_balance() failed: {str(e)}")
            
            # Summary and comparison
            self.log_message("📊 BALANCE COMPARISON SUMMARY:")
            self.log_message(f"  Wallet Balance:     {wallet_balance:.8f} PYC")
            self.log_message(f"  Manual Balance:     {manual_balance:.8f} PYC")
            self.log_message(f"  Blockchain Balance: {blockchain_balance:.8f} PYC")
            self.log_message(f"  Coinbase Rewards:   {coinbase_rewards:.8f} PYC")
            
            # Check for discrepancies
            if abs(wallet_balance - manual_balance) > 0.00000001:
                self.log_message("⚠️ WARNING: Balance calculation mismatch detected!")
                self.log_message(f"Difference (Wallet vs Manual): {abs(wallet_balance - manual_balance):.8f} PYC")
            else:
                self.log_message("✅ Wallet and manual balance calculations match")
            
            if abs(wallet_balance - blockchain_balance) > 0.00000001:
                self.log_message("⚠️ WARNING: Wallet vs Blockchain balance mismatch!")
                self.log_message(f"Difference (Wallet vs Blockchain): {abs(wallet_balance - blockchain_balance):.8f} PYC")
            else:
                self.log_message("✅ Wallet and blockchain balance calculations match")
            
            self.log_message("🔍 ===== END BALANCE DEBUG =====")
            
        except Exception as e:
            self.log_message(f"❌ Balance debug error: {str(e)}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
    
    def calculate_balance_manually(self):
        """Calculate balance by manually examining every transaction"""
        balance = 0.0
        wallet_address = self.wallet.address
        
        try:
            self.log_message(f"📊 Manual balance calculation for: {wallet_address}")
            
            for block_idx, block in enumerate(self.blockchain.chain):
                block_rewards = 0.0
                self.log_message(f"  📦 Block {block_idx}: {len(block.transactions)} transactions")
                
                for tx_idx, tx in enumerate(block.transactions):
                    tx_effect = 0.0
                    
                    # Check transaction type
                    tx_type = getattr(tx, 'tx_type', 'unknown')
                    self.log_message(f"    💰 TX {tx_idx}: Type='{tx_type}', ID={getattr(tx, 'tx_id', 'NO_ID')[:16]}...")
                    
                    # Handle coinbase transactions (mining rewards) - ENHANCED
                    if tx_type == 'coinbase':
                        for output_idx, output in enumerate(tx.outputs):
                            self.log_message(f"      🎯 Coinbase Output {output_idx}: {output.address[:8]}... = {output.amount:.8f} PYC")
                            if output.address == wallet_address:
                                tx_effect += output.amount
                                block_rewards += output.amount
                                self.log_message(f"      ✅ MINING REWARD: +{output.amount:.8f} PYC")
                        
                        # Ensure coinbase transaction is properly marked
                        if tx_effect > 0:
                            self.log_message(f"      💎 Total coinbase reward this tx: {tx_effect:.8f} PYC")
                    
                    # Handle genesis transactions
                    elif tx_type == 'genesis':
                        for output_idx, output in enumerate(tx.outputs):
                            self.log_message(f"      🎯 Genesis Output {output_idx}: {output.address[:8]}... = {output.amount:.8f} PYC")
                            if output.address == wallet_address:
                                tx_effect += output.amount
                                self.log_message(f"      ✅ GENESIS REWARD: +{output.amount:.8f} PYC")
                    
                    # Handle regular transactions
                    elif tx_type == 'regular':
                        # Check if we sent this transaction
                        sender_address = None
                        if hasattr(tx, 'sender') and tx.sender:
                            try:
                                sender_address = CryptoUtils.pubkey_to_address(tx.sender)
                            except:
                                sender_address = None
                        
                        if sender_address == wallet_address:
                            # We sent this transaction - subtract outputs to others
                            for output in tx.outputs:
                                if output.address != wallet_address:
                                    tx_effect -= output.amount
                                    self.log_message(f"      ❌ SENT: -{output.amount:.8f} PYC to {output.address[:8]}...")
                        
                        # Check if we received coins
                        for output in tx.outputs:
                            if output.address == wallet_address:
                                tx_effect += output.amount
                                self.log_message(f"      ✅ RECEIVED: +{output.amount:.8f} PYC")
                    
                    balance += tx_effect
                    if tx_effect != 0:
                        self.log_message(f"    📊 Transaction effect: {tx_effect:+.8f} PYC (Running total: {balance:.8f} PYC)")
                
                if block_rewards > 0:
                    self.log_message(f"  ⛏️ Block {block_idx} total rewards: {block_rewards:.8f} PYC")
            
            self.log_message(f"📊 Final manual balance: {balance:.8f} PYC")
            return balance
            
        except Exception as e:
            self.log_message(f"❌ Manual balance calculation error: {str(e)}")
            self.log_message(f"Traceback: {traceback.format_exc()}")
            return 0.0
    
    def check_coinbase_transactions(self):
        """Specifically check coinbase transactions"""
        total_rewards = 0.0
        wallet_address = self.wallet.address
        
        try:
            self.log_message("🔍 Checking coinbase transactions...")
            
            coinbase_count = 0
            for block_idx, block in enumerate(self.blockchain.chain):
                block_coinbase = 0
                
                for tx in block.transactions:
                    if getattr(tx, 'tx_type', '') == 'coinbase':
                        block_coinbase += 1
                        coinbase_count += 1
                        
                        self.log_message(f"  📦 Block {block_idx} coinbase:")
                        for output in tx.outputs:
                            self.log_message(f"    💰 {output.address[:8]}... = {output.amount:.8f} PYC")
                            if output.address == wallet_address:
                                total_rewards += output.amount
                                self.log_message(f"    ✅ OUR REWARD: {output.amount:.8f} PYC")
                
                if block_coinbase == 0 and block_idx > 0:  # Skip genesis block
                    self.log_message(f"  ⚠️ Block {block_idx} has NO coinbase transaction!")
            
            self.log_message(f"🔍 Total coinbase transactions: {coinbase_count}")
            self.log_message(f"🔍 Total our rewards: {total_rewards:.8f} PYC")
            
            return total_rewards
            
        except Exception as e:
            self.log_message(f"❌ Coinbase check error: {str(e)}")
            return 0.0
    
    def audit_mining_rewards(self):
        """Audit each block to see if it has proper mining rewards"""
        try:
            self.log_message("⛏️ Auditing mining rewards per block...")
            
            for block_idx, block in enumerate(self.blockchain.chain):
                if block_idx == 0:
                    self.log_message(f"  📦 Block 0 (Genesis): Skipping mining reward check")
                    continue
                
                # Check if block has coinbase transaction
                coinbase_txs = [tx for tx in block.transactions if getattr(tx, 'tx_type', '') == 'coinbase']
                
                if not coinbase_txs:
                    self.log_message(f"  ❌ Block {block_idx}: NO COINBASE TRANSACTION!")
                elif len(coinbase_txs) > 1:
                    self.log_message(f"  ⚠️ Block {block_idx}: Multiple coinbase transactions ({len(coinbase_txs)})")
                else:
                    coinbase_tx = coinbase_txs[0]
                    total_reward = sum(output.amount for output in coinbase_tx.outputs)
                    self.log_message(f"  ✅ Block {block_idx}: Coinbase reward = {total_reward:.8f} PYC")
                    
                    # Check if any reward goes to our address
                    our_reward = sum(output.amount for output in coinbase_tx.outputs 
                                   if output.address == self.wallet.address)
                    if our_reward > 0:
                        self.log_message(f"    🎯 Our share: {our_reward:.8f} PYC")
            
        except Exception as e:
            self.log_message(f"❌ Mining audit error: {str(e)}")
    
    def fix_missing_coinbase_transactions(self):
        """Attempt to fix blocks that are missing coinbase transactions"""
        try:
            self.log_message("🔧 Checking for blocks missing coinbase transactions...")
            
            fixed_count = 0
            for block_idx, block in enumerate(self.blockchain.chain):
                if block_idx == 0:  # Skip genesis block
                    continue
                
                # Check if block has coinbase transaction
                has_coinbase = any(getattr(tx, 'tx_type', '') == 'coinbase' for tx in block.transactions)
                
                if not has_coinbase:
                    self.log_message(f"🔧 Fixing Block {block_idx}: Adding missing coinbase transaction")
                    
                    # Create a coinbase transaction for this block
                    
                    coinbase_tx = Transaction(
                        sender="",  # Coinbase has no sender
                        inputs=[],  # Coinbase has no inputs
                        outputs=[TransactionOutput(address=self.wallet.address, amount=50.0)]
                    )
                    coinbase_tx.tx_type = 'coinbase'
                    coinbase_tx.timestamp = block.timestamp
                    coinbase_tx.tx_id = f"coinbase_{block_idx}_{int(block.timestamp)}"
                    
                    # Add to the beginning of the block's transactions
                    block.transactions.insert(0, coinbase_tx)
                    fixed_count += 1
                    
                    self.log_message(f"✅ Added coinbase transaction to block {block_idx}")
            
            if fixed_count > 0:
                self.log_message(f"🔧 Fixed {fixed_count} blocks with missing coinbase transactions")
                # Save the blockchain after fixing
                self.save_blockchain()
                return True
            else:
                self.log_message("✅ All blocks have proper coinbase transactions")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error fixing coinbase transactions: {str(e)}")
            return False
    def verify_blockchain_coinbase_integrity(self):
        """Verify that all mined blocks have proper coinbase transactions"""
        try:
            self.log_message("🔍 Verifying blockchain coinbase integrity...")
            
            problems = []
            total_expected_rewards = 0
            total_actual_rewards = 0
            
            for block_idx, block in enumerate(self.blockchain.chain):
                if block_idx == 0:  # Skip genesis block
                    continue
                
                expected_reward = 50.0  # Standard mining reward
                total_expected_rewards += expected_reward
                
                # Check if block has coinbase transaction
                coinbase_txs = [tx for tx in block.transactions if getattr(tx, 'tx_type', '') == 'coinbase']
                
                if not coinbase_txs:
                    problems.append(f"Block {block_idx}: Missing coinbase transaction")
                elif len(coinbase_txs) > 1:
                    problems.append(f"Block {block_idx}: Multiple coinbase transactions")
                else:
                    coinbase_tx = coinbase_txs[0]
                    
                    # Check if first transaction
                    if block.transactions[0] != coinbase_tx:
                        problems.append(f"Block {block_idx}: Coinbase not first transaction")
                    
                    # Check reward amount
                    our_reward = sum(output.amount for output in coinbase_tx.outputs 
                                   if output.address == self.wallet.address)
                    total_actual_rewards += our_reward
                    
                    if our_reward != expected_reward:
                        problems.append(f"Block {block_idx}: Expected {expected_reward} PYC, got {our_reward} PYC")
            
            # Report results
            self.log_message(f"Expected total rewards: {total_expected_rewards:.8f} PYC")
            self.log_message(f"Actual total rewards: {total_actual_rewards:.8f} PYC")
            
            if problems:
                self.log_message(f"❌ Found {len(problems)} coinbase problems:")
                for problem in problems[:10]:  # Show first 10 problems
                    self.log_message(f"  • {problem}")
                if len(problems) > 10:
                    self.log_message(f"  ... and {len(problems) - 10} more problems")
                return False
            else:
                self.log_message("✅ All blocks have proper coinbase transactions")
                return True
                
        except Exception as e:
            self.log_message(f"❌ Coinbase verification error: {str(e)}")
            return False
    
    def repair_all_missing_coinbase_transactions(self):
        """Repair all blocks missing coinbase transactions"""
        try:
            self.log_message("🔧 Repairing all missing coinbase transactions...")
            
            repaired_count = 0
            for block_idx, block in enumerate(self.blockchain.chain):
                if block_idx == 0:  # Skip genesis block
                    continue
                
                # Check if block has coinbase transaction
                has_coinbase = any(getattr(tx, 'tx_type', '') == 'coinbase' for tx in block.transactions)
                
                if not has_coinbase:
                    # Create and add coinbase transaction
                    
                    coinbase_tx = Transaction(
                        sender="",
                        inputs=[],
                        outputs=[TransactionOutput(address=self.wallet.address, amount=50.0)]
                    )
                    coinbase_tx.tx_type = 'coinbase'
                    coinbase_tx.timestamp = block.timestamp
                    coinbase_tx.tx_id = f"coinbase_repair_{block_idx}_{int(block.timestamp)}"
                    coinbase_tx.signature = ""
                    
                    # Insert at beginning of block
                    block.transactions.insert(0, coinbase_tx)
                    repaired_count += 1
                    
                    self.log_message(f"🔧 Repaired block {block_idx}: Added coinbase transaction")
            
            if repaired_count > 0:
                self.log_message(f"✅ Repaired {repaired_count} blocks")
                # Save blockchain after repairs
                self.save_blockchain()
                # Update UI
                self.original_update_ui()
                return True
            else:
                self.log_message("✅ No repairs needed")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Repair error: {str(e)}")
            return False
    def get_balance_from_blockchain_proof(self, address):
        """Get balance by validating the entire blockchain as proof of funds"""
        try:
            self.log_message(f"🔍 Calculating balance from blockchain proof for: {address[:8]}...")
            
            balance = 0.0
            unspent_outputs = {}  # Track unspent transaction outputs (UTXO)
            
            # Go through every block in chronological order
            for block_idx, block in enumerate(self.blockchain.chain):
                self.log_message(f"📦 Processing block {block_idx} with {len(block.transactions)} transactions...")
                
                # Process every transaction in the block
                for tx_idx, tx in enumerate(block.transactions):
                    tx_type = getattr(tx, 'tx_type', 'regular')
                    tx_id = getattr(tx, 'tx_id', f'tx_{block_idx}_{tx_idx}')
                    
                    # Handle coinbase transactions (mining rewards)
                    if tx_type == 'coinbase':
                        self.log_message(f"  💰 Processing coinbase transaction: {tx_id}")
                        for output_idx, output in enumerate(tx.outputs):
                            if output.address == address:
                                utxo_key = f"{tx_id}:{output_idx}"
                                unspent_outputs[utxo_key] = output.amount
                                balance += output.amount
                                self.log_message(f"    ✅ Added UTXO: {utxo_key} = {output.amount:.8f} PYC")
                    
                    # Handle genesis transactions  
                    elif tx_type == 'genesis':
                        self.log_message(f"  🌱 Processing genesis transaction: {tx_id}")
                        for output_idx, output in enumerate(tx.outputs):
                            if output.address == address:
                                utxo_key = f"{tx_id}:{output_idx}"
                                unspent_outputs[utxo_key] = output.amount
                                balance += output.amount
                                self.log_message(f"    ✅ Added genesis UTXO: {utxo_key} = {output.amount:.8f} PYC")
                    
                    # Handle regular transactions
                    elif tx_type == 'regular':
                        self.log_message(f"  📝 Processing regular transaction: {tx_id}")
                        
                        # Check if this transaction spends any of our UTXOs (inputs)
                        for tx_input in tx.inputs:
                            utxo_key = f"{tx_input.tx_id}:{tx_input.output_index}"
                            if utxo_key in unspent_outputs:
                                spent_amount = unspent_outputs[utxo_key]
                                del unspent_outputs[utxo_key]
                                balance -= spent_amount
                                self.log_message(f"    ❌ Spent UTXO: {utxo_key} = -{spent_amount:.8f} PYC")
                        
                        # Check if this transaction creates new UTXOs for us (outputs)
                        for output_idx, output in enumerate(tx.outputs):
                            if output.address == address:
                                utxo_key = f"{tx_id}:{output_idx}"
                                unspent_outputs[utxo_key] = output.amount
                                balance += output.amount
                                self.log_message(f"    ✅ Added UTXO: {utxo_key} = {output.amount:.8f} PYC")
            
            # Final validation
            utxo_total = sum(unspent_outputs.values())
            self.log_message(f"🔍 Final validation:")
            self.log_message(f"  Balance calculated: {balance:.8f} PYC")
            self.log_message(f"  UTXO total: {utxo_total:.8f} PYC")
            self.log_message(f"  Unspent outputs count: {len(unspent_outputs)}")
            
            if abs(balance - utxo_total) > 0.00000001:
                self.log_message("⚠️ WARNING: Balance and UTXO total don't match!")
            
            return balance
            
        except Exception as e:
            self.log_message(f"❌ Error calculating balance from blockchain proof: {str(e)}")
            self.log_message(f"Traceback: {traceback.format_exc()}")
            return 0.0
    
    def override_wallet_get_balance(self):
        """Override wallet get_balance to use the corrected blockchain method"""
        try:
            # Temporarily override the wallet's get_balance method
            if self.wallet and self.blockchain:
                # Use our corrected balance calculation
                corrected_balance = self.get_balance_from_blockchain_proof(self.wallet.address)
                
                # Also check what the original blockchain method returns
                try:
                    original_balance = self.blockchain.get_balance(self.wallet.address)
                    self.log_message(f"Original blockchain.get_balance(): {original_balance:.8f} PYC")
                    self.log_message(f"Corrected calculation: {corrected_balance:.8f} PYC")
                except Exception as e:
                    self.log_message(f"Original blockchain.get_balance() failed: {str(e)}")
                
                return corrected_balance
            return 0.0
            
        except Exception as e:
            self.log_message(f"❌ Error in override_wallet_get_balance: {str(e)}")
            return 0.0
    def debug_blockchain_validation_issues(self):
        """Debug why blockchain.get_balance() is failing"""
        try:
            self.log_message("🔍 ===== BLOCKCHAIN VALIDATION DEBUG =====")
            
            if not self.wallet or not self.blockchain:
                self.log_message("❌ Wallet or blockchain not available")
                return
            
            address = self.wallet.address
            self.log_message(f"Debugging balance for address: {address}")
            
            # Test the original blockchain get_balance method
            try:
                original_balance = self.blockchain.get_balance(address)
                self.log_message(f"Original blockchain.get_balance(): {original_balance:.8f} PYC")
            except Exception as e:
                self.log_message(f"❌ Original blockchain.get_balance() failed: {str(e)}")
                self.log_message("This is the root cause of the problem!")
            
            # Test our corrected method
            try:
                corrected_balance = self.get_balance_from_blockchain_proof(address)
                self.log_message(f"Corrected balance calculation: {corrected_balance:.8f} PYC")
            except Exception as e:
                self.log_message(f"❌ Corrected method failed: {str(e)}")
            
            # Check if blockchain class has the get_balance method
            if hasattr(self.blockchain, 'get_balance'):
                self.log_message("✅ Blockchain has get_balance method")
                
                # Try to inspect the method
                import inspect
                try:
                    source = inspect.getsource(self.blockchain.get_balance)
                    self.log_message("Original get_balance method source:")
                    for line_num, line in enumerate(source.split('')[:10], 1):
                        self.log_message(f"  {line_num}: {line}")
                except:
                    self.log_message("Could not inspect get_balance method source")
            else:
                self.log_message("❌ Blockchain does NOT have get_balance method!")
            
            # Check what's actually in the blockchain
            self.log_message(f"Blockchain chain length: {len(self.blockchain.chain)}")
            self.log_message(f"Pending transactions: {len(self.blockchain.pending_transactions)}")
            
            # Check first few blocks for coinbase transactions
            for i, block in enumerate(self.blockchain.chain[:5]):
                coinbase_count = sum(1 for tx in block.transactions if getattr(tx, 'tx_type', '') == 'coinbase')
                self.log_message(f"Block {i}: {len(block.transactions)} transactions, {coinbase_count} coinbase")
            
            self.log_message("🔍 ===== END BLOCKCHAIN VALIDATION DEBUG =====")
            
        except Exception as e:
            self.log_message(f"❌ Blockchain validation debug error: {str(e)}")
            self.log_message(f"Traceback: {traceback.format_exc()}")
    def compare_balance_calculation_methods(self):
        """Compare different balance calculation methods to find the issue"""
        try:
            if not self.wallet or not self.blockchain:
                self.log_message("❌ Cannot compare - wallet or blockchain missing")
                return
            
            address = self.wallet.address
            self.log_message("⚖️ ===== BALANCE CALCULATION COMPARISON =====")
            self.log_message(f"Address: {address}")
            
            # Method 1: Original wallet.get_balance()
            try:
                wallet_balance = self.wallet.get_balance()
                self.log_message(f"Method 1 - wallet.get_balance(): {wallet_balance:.8f} PYC")
            except Exception as e:
                self.log_message(f"Method 1 FAILED: {str(e)}")
                wallet_balance = None
            
            # Method 2: Original blockchain.get_balance()
            try:
                blockchain_balance = self.blockchain.get_balance(address)
                self.log_message(f"Method 2 - blockchain.get_balance(): {blockchain_balance:.8f} PYC")
            except Exception as e:
                self.log_message(f"Method 2 FAILED: {str(e)}")
                blockchain_balance = None
            
            # Method 3: Our manual calculation
            try:
                manual_balance = self.calculate_balance_manually()
                self.log_message(f"Method 3 - manual calculation: {manual_balance:.8f} PYC")
            except Exception as e:
                self.log_message(f"Method 3 FAILED: {str(e)}")
                manual_balance = None
            
            # Method 4: Our corrected blockchain proof method
            try:
                proof_balance = self.get_balance_from_blockchain_proof(address)
                self.log_message(f"Method 4 - blockchain proof: {proof_balance:.8f} PYC")
            except Exception as e:
                self.log_message(f"Method 4 FAILED: {str(e)}")
                proof_balance = None
            
            # Analysis
            methods = [
                ("wallet.get_balance()", wallet_balance),
                ("blockchain.get_balance()", blockchain_balance), 
                ("manual calculation", manual_balance),
                ("blockchain proof", proof_balance)
            ]
            
            working_methods = [(name, balance) for name, balance in methods if balance is not None]
            
            if len(working_methods) > 1:
                # Check if methods agree
                first_balance = working_methods[0][1]
                all_agree = all(abs(balance - first_balance) < 0.00000001 for _, balance in working_methods)
                
                if all_agree:
                    self.log_message(f"✅ All working methods agree: {first_balance:.8f} PYC")
                else:
                    self.log_message("❌ Methods disagree:")
                    for name, balance in working_methods:
                        self.log_message(f"  {name}: {balance:.8f} PYC")
            
            # Recommendation
            if blockchain_balance is None:
                self.log_message("🔧 RECOMMENDATION: blockchain.get_balance() is broken!")
                self.log_message("   Solution: Use corrected blockchain proof method")
            elif wallet_balance != manual_balance:
                self.log_message("🔧 RECOMMENDATION: wallet.get_balance() has issues!")
                self.log_message("   Solution: Fix wallet balance calculation")
            
            self.log_message("⚖️ ===== END BALANCE COMPARISON =====")
            
        except Exception as e:
            self.log_message(f"❌ Balance comparison error: {str(e)}")
    def create_developer_portal_tab(self):
        """Create developer portal integration tab"""
        portal_widget = QWidget()
        portal_layout = QVBoxLayout()
        portal_widget.setLayout(portal_layout)
        
        # Portal server status
        server_group = QGroupBox("🌐 Developer Portal Server")
        server_layout = QVBoxLayout()
        
        self.portal_status = QLabel("Status: Offline")
        self.portal_status.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        server_layout.addWidget(self.portal_status)
        
        # Server controls
        server_controls = QHBoxLayout()
        
        self.start_portal_btn = QPushButton("🚀 Start Portal Server")
        self.start_portal_btn.clicked.connect(self.start_portal_server)
        server_controls.addWidget(self.start_portal_btn)
        
        self.stop_portal_btn = QPushButton("⏹️ Stop Portal Server")
        self.stop_portal_btn.clicked.connect(self.stop_portal_server)
        self.stop_portal_btn.setEnabled(False)
        server_controls.addWidget(self.stop_portal_btn)
        
        test_portal_btn = QPushButton("🔧 Test Server")
        test_portal_btn.clicked.connect(self.test_portal_server)
        server_controls.addWidget(test_portal_btn)
        
        server_layout.addLayout(server_controls)
        server_group.setLayout(server_layout)
        portal_layout.addWidget(server_group)
        
        # Developer registration
        dev_group = QGroupBox("👥 Registered Developers")
        dev_layout = QVBoxLayout()
        
        self.developers_table = QTableWidget()
        self.developers_table.setColumnCount(4)
        self.developers_table.setHorizontalHeaderLabels(["Developer", "Address", "Clicks", "Earnings"])
        
        dev_header = self.developers_table.horizontalHeader()
        dev_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        dev_layout.addWidget(self.developers_table)
        dev_group.setLayout(dev_layout)
        portal_layout.addWidget(dev_group)
        
        # Portal statistics
        stats_group = QGroupBox("📊 Portal Statistics")
        stats_layout = QFormLayout()
        
        self.total_developers_label = QLabel("0")
        stats_layout.addRow("Total Developers:", self.total_developers_label)
        
        self.total_clicks_label = QLabel("0")
        stats_layout.addRow("Total Clicks:", self.total_clicks_label)
        
        self.total_payments_label = QLabel("0.00000000 PYC")
        stats_layout.addRow("Total Payments:", self.total_payments_label)
        
        stats_group.setLayout(stats_layout)
        portal_layout.addWidget(stats_group)
        
        self.tab_widget.addTab(portal_widget, "🌐 Developer Portal")
















    
    # ============================================================================
    # Signal Handlers (Enhanced)
    # ============================================================================
    
    def on_peer_discovered(self, peer_id: str, host: str, port: int):
        """Handle peer discovered"""
        self.log_message(f"Discovered peer: {peer_id} at {host}:{port}")
        
        # Update peer info in our local dict
        if peer_id not in self.peers:
            self.peers[peer_id] = PeerInfo(
                peer_id=peer_id,
                host=host,
                port=port,
                status='discovered',
                last_seen=datetime.now().isoformat(),
                ad_count=0,
                capabilities=[]
            )
    
    def on_peer_connected(self, peer_id: str):
        """Handle peer connected"""
        self.log_message(f"Connected to peer: {peer_id}")
        if peer_id in self.peers:
            self.peers[peer_id].status = 'connected'
    
    def on_peer_disconnected(self, peer_id: str):
        """Handle peer disconnected"""
        self.log_message(f"Disconnected from peer: {peer_id}")
        if peer_id in self.peers:
            self.peers[peer_id].status = 'disconnected'
    
    def on_ads_received(self, ads_data: List):
        """Handle ads received from peers"""
        new_ads = []
        for ad_data in ads_data:
            ad = AdContent(
                id=ad_data.get('id', str(uuid.uuid4())),
                title=ad_data.get('title', 'Unknown Ad'),
                description=ad_data.get('description', ''),
                image_url=ad_data.get('image_url', ''),
                click_url=ad_data.get('click_url', ''),
                category=ad_data.get('category', 'general'),
                targeting=ad_data.get('targeting', {}),
                created_at=ad_data.get('created_at', datetime.now().isoformat()),
                expires_at=ad_data.get('expires_at', (datetime.now() + timedelta(days=7)).isoformat()),
                peer_source=ad_data.get('peer_source', 'unknown'),
                payout_rate=ad_data.get('payout_rate', 0.001),
                advertiser_address=ad_data.get('advertiser_address', '')
            )
            
            # Only add if not already cached
            if not any(existing.id == ad.id for existing in self.ads):
                self.ads.append(ad)
                new_ads.append(ad)
        
        if new_ads:
            self.log_message(f"Received {len(new_ads)} new ads from P2P network")
            
            # Commit any blockchain changes from ad processing
            if new_ads:
                self.on_blockchain_changed("new_ads_received")
    
    def on_status_update(self, status: str):
        """Handle status updates"""
        self.log_message(status)
    
    def on_click_received(self, click_event: ClickEvent):
        """Handle click event received"""
        self.click_events.append(click_event)
            
            # Update database
        self.update_database_on_click(click_event.__dict__ if hasattr(click_event, '__dict__') else {})
        self.log_message(f"Click received: {click_event.ad_id} -> {click_event.payout_amount} PYC")
            
            # Commit blockchain after click event processing
        self.on_blockchain_changed("click_event_processed")
    
    def on_payment_sent(self, address: str, amount: float):
        """Handle payment sent confirmation"""
        self.stats['payments_sent'] += 1
        self.stats['revenue_generated'] += amount
        self.log_message(f"Payment sent: {amount:.6f} PYC to {address[:8]}...")
            
            # Commit blockchain after payment
        self.on_blockchain_changed("payment_sent")
    
    def on_genesis_ready(self, genesis_addresses: List[str]):
        """Handle genesis block ready signal"""
        self.log_message(f"Genesis block created with {len(genesis_addresses)} participants")
        
        # Update UI to reflect genesis completion
        if hasattr(self, 'genesis_participants_label'):
            self.genesis_participants_label.setText(f"Participants: {len(genesis_addresses)} wallets")
        
        # Show notification
        QMessageBox.information(self, "Genesis Block Created", 
                               f"Genesis block successfully created!\n\n"
                               f"Participants: {len(genesis_addresses)}\n"
                               f"Initial distribution completed.\n\n"
                               f"You can now start mining and sending transactions.")
    
    def on_mining_status_update(self, status: str):
        """Handle mining status updates"""
        self.mining_log.append(f"{datetime.now().strftime('%H:%M:%S')} - {status}")
        self.mining_log.ensureCursorVisible()
    
    def on_mining_hashrate_update(self, hashrate: float):
        """Handle mining hashrate updates"""
        self.mining_hashrate.setText(f"Hash Rate: {hashrate:.2f} H/s")
        if hasattr(self, 'mining_hashrate_label'):
            self.mining_hashrate_label.setText(f"Hash Rate: {hashrate:.2f} H/s")
    
    def on_new_block_mined(self, block):
        """Handle new block mined"""
        self.stats['blocks_mined'] += 1
        if hasattr(self, 'blocks_mined_count'):
            self.blocks_mined_count.setText(f"Blocks Mined: {self.stats['blocks_mined']}")
        
        # Update mining rewards
        mining_rewards = 0
        for blk in self.blockchain.chain:
            for tx in blk.transactions:
                if tx.tx_type == "coinbase":
                    for output in tx.outputs:
                        if output.address == self.wallet.address:
                            mining_rewards += output.amount
        
        if hasattr(self, 'mining_rewards'):
            self.mining_rewards.setText(f"Mining Rewards: {mining_rewards:.8f} PYC")
        
        self.log_message(f"Block mined! Height: {block.index}, Hash: {block.hash[:16]}...")
        
        # Immediate balance verification after mining
        try:
            new_# Use corrected balance calculation
            try:
                balance = self.override_wallet_get_balance()
            except AttributeError:
                balance = self.wallet.get_balance() if hasattr(self.wallet, "get_balance") else 0.0
            self.log_message(f"💰 Balance after mining: {new_balance:.8f} PYC")
            
            # If balance is still 0, there's a problem with coinbase transaction
            if new_balance == 0:
                self.log_message("❌ WARNING: Balance is 0 after mining - coinbase issue!")
                # Debug the balance immediately
                QTimer.singleShot(500, self.debug_balance_calculation)
            
        except Exception as e:
            self.log_message(f"❌ Error checking balance after mining: {str(e)}")
    
    # ============================================================================
    # Utility Functions (Enhanced)
    # ============================================================================
    
    def generate_qr_code(self, data):
        """Generate QR code for wallet address"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=3,
                border=2,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to QPixmap
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            qpm = QPixmap()
            qpm.loadFromData(QByteArray(buffer.getvalue()))
            
            self.qr_label.setPixmap(qpm)
            
        except Exception as e:
            self.log_message(f"QR code generation error: {e}")
    
    def copy_address_to_clipboard(self):
        """Copy wallet address to clipboard"""
        if self.wallet:
            QApplication.clipboard().setText(self.wallet.address)
            self.statusBar.showMessage("Address copied to clipboard", 3000)
        
    def log_message(self, message: str):
        """Log message to console and status bar"""
        logger.info(message)
        
        # Only try to update status bar if UI is initialized
        if hasattr(self, 'statusBar') and hasattr(self.statusBar, 'showMessage'):
            try:
                self.statusBar.showMessage(message, 5000)
            except AttributeError:
                # Fallback if status bar isn't properly initialized yet
                pass
        
        # Also log to network log if available
        if hasattr(self, 'network_log') and hasattr(self.network_log, 'append'):
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.network_log.append(f"[{timestamp}] {message}")
                self.network_log.ensureCursorVisible()
            except:
                pass
    def import_wallet(self):
        """Import wallet from private key (same as before)"""
        private_key, ok = QInputDialog.getText(
            self, "Import Wallet", "Enter your private key (hex format):",
            QLineEdit.EchoMode.Normal
        )
        
        if not ok or not private_key:
            return
        
        try:
            # Recreate public key from private key
            import ecdsa
            priv_key_bytes = bytes.fromhex(private_key)
            signing_key = ecdsa.SigningKey.from_string(priv_key_bytes, curve=ecdsa.SECP256k1)
            public_key = signing_key.get_verifying_key().to_string().hex()
            
            # Create wallet
            self.wallet = Wallet(
                self.blockchain,
                private_key=private_key,
                public_key=public_key
            )
            
            self.save_wallet()
            self.init_p2p_components()
            self.update_wallet_display()
            
            QMessageBox.information(self, "Import Successful", 
                                   f"Wallet imported: {self.wallet.address}")
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import wallet: {str(e)}")
    
    def export_wallet(self):
        """Export wallet private key (same as before)"""
        if not self.wallet:
            QMessageBox.warning(self, "Export Error", "No wallet loaded")
            return
        
        reply = QMessageBox.warning(
            self, "Security Warning",
            "WARNING: Your private key gives complete control over your funds.\n"
            "Never share it with anyone and store it securely.\n\n"
            "Are you sure you want to display your private key?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            dialog = QDialog(self)
            dialog.setWindowTitle("Your Private Key")
            dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout()
            
            warning = QLabel("⚠️ Keep this private key secure! Anyone with this key can steal your funds.")
            warning.setStyleSheet("color: red; font-weight: bold; padding: 10px; border: 2px solid red; border-radius: 6px;")
            warning.setWordWrap(True)
            layout.addWidget(warning)
            
            key_display = QTextEdit()
            key_display.setPlainText(self.wallet.private_key)
            key_display.setReadOnly(True)
            key_display.setMaximumHeight(100)
            layout.addWidget(key_display)
            
            button_layout = QHBoxLayout()
            
            copy_btn = QPushButton("📋 Copy to Clipboard")
            copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.wallet.private_key))
            button_layout.addWidget(copy_btn)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            dialog.exec()
    
    def backup_all_data(self):
        """Backup all wallet and network data"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Backup All Data", 
            f"pythoncoin_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        
        if not filename:
            return
        
        try:
            backup_data = {
                'wallet': {
                    'private_key': self.wallet.private_key if self.wallet else '',
                    'public_key': self.wallet.public_key if self.wallet else '',
                    'address': self.wallet.address if self.wallet else ''
                },
                'blockchain': {
                    'chain': [block.to_dict() for block in self.blockchain.chain],
                    'pending_transactions': [tx.to_dict() for tx in self.blockchain.pending_transactions],
                    'genesis_complete': self.blockchain.genesis_complete,
                    'genesis_addresses': self.blockchain.genesis_addresses
                },
                'ad_network': {
                    'client_id': self.client_id,
                    'ads': [ad.to_dict() for ad in self.ads],
                    'click_events': [asdict(click) for click in self.click_events],
                    'stats': self.stats
                },
                'backup_timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            QMessageBox.information(self, "Backup Complete", f"Data backed up to {filename}")
            self.log_message(f"Full backup created: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Failed to create backup: {str(e)}")
    
    def show_about(self):
        """Show enhanced about dialog"""
        about_text = f"""
        <h2>🚀 PythonCoin P2P Ad Network Wallet (Enhanced)</h2>
        <p><b>Version:</b> 2.0.0</p>
        <p><b>Client ID:</b> {self.client_id}</p>
        
        <h3>🏗️ Genesis Block Features:</h3>
        <ul>
            <li>Automatic peer discovery and coordination</li>
            <li>Fair initial coin distribution to all connected peers</li>
            <li>Synchronized blockchain initialization</li>
            <li>Proper UTXO management from genesis</li>
        </ul>
        
        <h3>💰 Cryptocurrency Features:</h3>
        <ul>
            <li>Send and receive PythonCoin (PYC)</li>
            <li>Mine blocks to earn rewards (50 PYC per block)</li>
            <li>Full blockchain node capabilities</li>
            <li>Secure wallet with private key management</li>
            <li>Dynamic difficulty adjustment</li>
        </ul>
        
        <h3>🌐 P2P Network Features:</h3>
        <ul>
            <li>Decentralized peer discovery</li>
            <li>Real-time blockchain synchronization</li>
            <li>Genesis coordination protocol</li>
            <li>Automatic cryptocurrency payments for ad clicks</li>
        </ul>
        
        <h3>🔧 Technical Improvements:</h3>
        <ul>
            <li>Enhanced UTXO validation</li>
            <li>Better transaction verification</li>
            <li>Improved mining algorithm</li>
            <li>Comprehensive error handling</li>
            <li>Real-time UI updates</li>
        </ul>
        
        <p><b>Created with Python, PyQt5, and enhanced PythonCoin blockchain technology.</b></p>
        """
        
        QMessageBox.about(self, "About Enhanced PythonCoin Wallet", about_text)
    # Developer Portal Server Methods
    
    def start_portal_server(self):
        """Start the enhanced developer portal server with state checking"""
        if not self.wallet:
            QMessageBox.warning(self, "Portal Error", "No wallet loaded")
            return
        
        # Check if server is actually running
        if not self.check_portal_server_state():
            self.log_message("🔧 Portal server state was incorrect, proceeding with startup...")
        elif self.portal_server and self.portal_server.isRunning():
            self.log_message("⚠️ Portal server is already running")
            # Test the existing connection
            self.test_portal_connection()
            return
        
        try:
            # Force stop any existing server first
            self.force_stop_portal_server()
            
            # Get and validate port
            server_port = 8082
            try:
                if hasattr(self, 'validate_port'):
                    server_port = self.validate_port(self.port if hasattr(self, 'port') else 8082, 8082)
                else:
                    server_port = int(self.port) if hasattr(self, 'port') else 8082
                        
            except Exception as e:
                self.log_message(f"⚠️ Port validation failed: {str(e)}, using 8082")
                server_port = 8082
            
            self.log_message(f"🚀 Creating portal server on port {server_port}...")
            
            # Create new portal server
            self.portal_server = EnhancedDeveloperPortalServer(
                wallet=self.wallet, 
                blockchain=self.blockchain, 
                port=server_port
            )
            
            # Pass database manager and wallet instance
            if hasattr(self, 'db_manager') and self.db_manager:
                self.portal_server.db_manager = self.db_manager
                self.portal_server.wallet_instance = self
            
            # Connect signals
            self.portal_server.status_update.connect(self.on_portal_status_update)
            self.portal_server.click_received.connect(self.on_portal_click_received)
            self.portal_server.developer_registered.connect(self.on_developer_registered)
            if hasattr(self.portal_server, 'client_notification'):
                self.portal_server.client_notification.connect(self.on_client_notification)
            
            # Start the server
            self.log_message("🔄 Starting portal server thread...")
            self.portal_server.start()
            
            # Update UI state
            self.portal_enabled = True
            if hasattr(self, 'portal_status'):
                self.portal_status.setText(f"Status: Starting on port {server_port}...")
            if hasattr(self, 'start_portal_btn'):
                self.start_portal_btn.setEnabled(False)
            if hasattr(self, 'stop_portal_btn'):
                self.stop_portal_btn.setEnabled(True)
            
            self.log_message(f"✅ Portal server startup initiated on port {server_port}")
            
            # Test connection after startup
            QTimer.singleShot(4000, self.test_portal_connection)
            
        except Exception as e:
            self.log_message(f"❌ Error starting portal server: {str(e)}")
            import traceback
            self.log_message(f"Stack trace: {traceback.format_exc()}")
            
            QMessageBox.critical(self, "Portal Error", 
                               f"Failed to start server: {str(e)}"
                               f"Check the console for detailed error information.")
            
            # Reset state on failure
            self.force_stop_portal_server()

    def stop_portal_server(self):
        """Stop the developer portal server"""
        try:
            
            if self.portal_server and hasattr(self.portal_server, 'stop'):
                self.portal_server.stop()
                self.portal_server.wait(3000)  # Wait up to 3 seconds
                self.portal_server = None
            elif self.portal_server:
                # Fallback for servers without proper stop method
                try:
                    self.portal_server.running = False
                    if hasattr(self.portal_server, 'terminate'):
                        self.portal_server.terminate()
                    self.portal_server = None
                except:
                    pass

        except Exception as e:
            self.log_message(f"Error stopping portal server: {str(e)}")
    
    def test_portal_server(self):
        """Test the portal server connection"""
        try:
            import urllib.request
            
            if not self.portal_enabled:
                QMessageBox.warning(self, "Test Error", "Portal server is not running")
                return
            
            url = "http://127.0.0.1:8082/client_info"
            
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read().decode())
            
            if data.get('success'):
                client_info = data.get('client', {})
                
                QMessageBox.information(self, "Portal Test Success", 
                                       f"✅ Portal server is working!"
                                       f"Client Name: {client_info.get('name', 'Unknown')}"
                                       f"Available Ads: {client_info.get('ad_count', 0)}")
                
                self.log_message("Portal server test successful")
            else:
                QMessageBox.warning(self, "Test Failed", "Portal server returned error")
                
        except Exception as e:
            QMessageBox.critical(self, "Test Error", f"Portal test failed: {str(e)}")
    
    def on_portal_status_update(self, status):
        """Handle portal server status updates with database integration"""
        self.log_message(f"🌐 Portal: {status}")
        
        if "server started" in status.lower() or "✅" in status:
            if hasattr(self, 'portal_status'):
                self.portal_status.setText("Status: Online ✅")
        elif "error" in status.lower() or "❌" in status:
            if hasattr(self, 'portal_status'):
                self.portal_status.setText("Status: Error ❌")
        
        # Update database with server status
        if self.db_connected and "started successfully" in status.lower():
            self.update_client_in_database()
    
    def on_client_notification(self, notification_data):
        """Handle client notifications from portal server"""
        try:
            notification_type = notification_data.get('type', 'general')
            message = notification_data.get('message', '')
            
            self.log_message(f"📢 Portal notification: {message}")
            
            # Store notification in database
            if self.db_connected:
                self.create_system_notification(notification_type, message)
                
        except Exception as e:
            self.log_message(f"❌ Error handling notification: {str(e)}")
    
    def on_portal_click_received(self, click_data):
        """Handle ad click from portal with enhanced database tracking"""
        try:
            developer = click_data.get('developer', 'Unknown')
            amount = click_data.get('amount', 0)
            ad_id = click_data.get('ad_id', '')
            
            self.log_message(f"💰 Portal click: {amount:.6f} PYC -> {developer}")
            
            # Record in database if connected
            if self.db_connected and ad_id:
                click_record = {
                    'ad_id': ad_id,
                    'client_id': self.client_id,
                    'zone': click_data.get('zone', 'default'),
                    'payout_amount': amount,
                    'ip_address': click_data.get('ip_address', '127.0.0.1'),
                    'user_agent': click_data.get('user_agent', ''),
                    'metadata': {
                        'developer': developer,
                        'timestamp': datetime.now().isoformat(),
                        'payment_address': self.wallet.address if self.wallet else '',
                        'client_balance_before': self.get_current_balance()
                    }
                }
                
                try:
                    self.db_manager.record_ad_click(click_record)
                    self.log_message("✅ Click recorded in database")
                except Exception as e:
                    self.log_message(f"❌ Error recording click: {str(e)}")
            
            # Update stats and save blockchain
            self.stats['clicks'] = self.stats.get('clicks', 0) + 1
            self.stats['revenue_generated'] = self.stats.get('revenue_generated', 0.0) + amount
            
            if hasattr(self, 'save_blockchain'):
                self.save_blockchain()
            
            # Update database after click
            self.update_client_in_database()
                
        except Exception as e:
            self.log_message(f"❌ Error handling portal click: {str(e)}")
    def on_portal_click_received(self, click_data):
        """Handle ad click from portal"""
        developer = click_data.get('developer', 'Unknown')
        amount = click_data.get('amount', 0)
        
        self.log_message(f"💰 Portal click: {amount:.6f} PYC -> {developer}")
        self.update_portal_stats()
        
        if hasattr(self, 'save_blockchain'):
            self.save_blockchain()
    
    def on_developer_registered(self, developer, address):
        """Handle developer registration"""
        self.log_message(f"👤 Developer registered: {developer} -> {address[:8]}...")
        self.update_developers_table()
    
    def update_developers_table(self):
        """Update the developers table display"""
        if not hasattr(self, 'developers_table') or not self.portal_server:
            return
        
        developers = getattr(self.portal_server, 'registered_developers', {})
        payments = getattr(self.portal_server, 'click_payments', [])
        
        self.developers_table.setRowCount(len(developers))
        
        for row, (developer, address) in enumerate(developers.items()):
            self.developers_table.setItem(row, 0, QTableWidgetItem(developer))
            self.developers_table.setItem(row, 1, QTableWidgetItem(f"{address[:8]}..."))
            
            dev_clicks = len([p for p in payments if p.get('developer') == developer])
            self.developers_table.setItem(row, 2, QTableWidgetItem(str(dev_clicks)))
            
            dev_earnings = sum(p.get('amount', 0) for p in payments if p.get('developer') == developer)
            self.developers_table.setItem(row, 3, QTableWidgetItem(f"{dev_earnings:.8f} PYC"))(p.get('amount', 0) for p in payments if p.get('developer') == developer)
            self.developers_table.setItem(row, 3, QTableWidgetItem(f"{dev_earnings:.8f} PYC"))
    
    def update_portal_stats(self):
        """Update portal statistics display"""
        if not hasattr(self, 'total_developers_label') or not self.portal_server:
            return
        
        developers = getattr(self.portal_server, 'registered_developers', {})
        payments = getattr(self.portal_server, 'click_payments', [])
        
        self.total_developers_label.setText(str(len(developers)))
        self.total_clicks_label.setText(str(len(payments)))
        
        total_paid = sum(p.get('amount', 0) for p in payments)
        self.total_payments_label.setText(f"{total_paid:.8f} PYC")


    

    # Emergency patch methods
    def setup_optimized_timers(self):
        """Emergency patch - basic timer setup"""
        try:
            # Keep existing update timer but with longer interval
            if hasattr(self, "update_timer"):
                self.update_timer.stop()
                self.update_timer.start(5000)  # 5 seconds
        except Exception as e:
            self.log_message(f"Timer setup error: {str(e)}")

    def optimized_update_ui(self):
        """Emergency patch - basic UI update"""
        try:
            if hasattr(self, "original_update_ui"):
                self.original_update_ui()
            else:
                self.update_wallet_display()
        except Exception as e:
            self.log_message(f"UI update error: {str(e)}")

    
    def test_portal_connection(self):
        """Test portal connection with multiple retry attempts"""
        try:
            if not self.portal_server:
                self.log_message("⚠️ No portal server instance to test")
                return False
            
            # Wait for server to be ready
            max_wait = 10  # seconds
            wait_count = 0
            
            while wait_count < max_wait:
                if getattr(self.portal_server, 'server_started', False):
                    break
                time.sleep(1)
                wait_count += 1
            
            if not getattr(self.portal_server, 'server_started', False):
                self.log_message("⚠️ Server did not start within timeout period")
                return False
            
            # Get the actual port
            actual_port = getattr(self.portal_server, 'actual_port', 8082)
            self.log_message(f"🔍 Testing portal connection on port {actual_port}")
            
            # Try multiple connection attempts
            for attempt in range(3):
                try:
                    import urllib.request
                    import time
                    
                    if attempt > 0:
                        time.sleep(2)  # Wait before retry
                    
                    test_url = f"http://127.0.0.1:{actual_port}/test"
                    
                    req = urllib.request.Request(test_url)
                    req.add_header('User-Agent', 'PythonCoin-Wallet-Test')
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode())
                        if data.get('success'):
                            self.log_message(f"✅ Portal server test successful on port {actual_port} (attempt {attempt + 1})")
                            
                            if hasattr(self, 'portal_status'):
                                self.portal_status.setText(f"Status: Online ✅ (Port {actual_port})")
                            
                            # Now that server is confirmed working, register in database
                            QTimer.singleShot(1000, self.register_client_in_database)
                            
                            # Start database sync
                            QTimer.singleShot(2000, self.start_database_sync)
                            
                            # Open portal in browser
                            try:
                                import webbrowser
                                webbrowser.open(f"http://127.0.0.1:{actual_port}/portal")
                                self.log_message(f"🌐 Opened portal in browser: http://127.0.0.1:{actual_port}/portal")
                            except:
                                self.log_message(f"💡 Portal available at: http://127.0.0.1:{actual_port}/portal")
                            
                            return True
                        else:
                            self.log_message(f"⚠️ Server responded but returned error (attempt {attempt + 1})")
                            
                except Exception as e:
                    self.log_message(f"⚠️ Connection attempt {attempt + 1} failed: {str(e)}")
                    if attempt == 2:  # Last attempt
                        self.log_message("❌ All connection attempts failed")
                        if hasattr(self, 'portal_status'):
                            self.portal_status.setText(f"Status: Connection Failed ❌")
            
            return False
                    
        except Exception as e:
            self.log_message(f"⚠️ Portal connection test error: {str(e)}")
            return False
    def get_local_ip(self):
        """Get local IP address for client registration"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"
    
    def register_client_in_database(self):
        """Register this client in the database with complete information - ENHANCED"""
        try:
            if not self.db_connected:
                # Try to reconnect to database
                self.db_connected = self.db_manager.connect()
                if not self.db_connected:
                    self.log_message("❌ Cannot register client - database not connected")
                    return False
            
            if not self.wallet:
                self.log_message("⚠️ Cannot register client - wallet not loaded")
                return False
            
            self.log_message("📝 Registering client in database...")
            
            # Get current balance safely
            current_balance = 0.0
            try:
                if hasattr(self, 'override_wallet_get_balance'):
                    current_balance = self.override_wallet_get_balance()
                elif hasattr(self.wallet, 'get_balance'):
                    current_balance = self.wallet.get_balance()
            except Exception as e:
                self.log_message(f"⚠️ Could not get balance: {str(e)}")
            
            # Get server port
            server_port = self.port
            if self.portal_server and hasattr(self.portal_server, 'actual_port'):
                server_port = self.portal_server.actual_port
            
            # Comprehensive client information
            client_data = {
                'client_id': self.client_id,
                'name': f'PythonCoin Wallet - {self.wallet.address[:8]}...',
                'host': self.get_local_ip(),
                'port': server_port,
                'username': f'user_{self.wallet.address[:8]}',
                'wallet_address': self.wallet.address,
                'version': '2.1.0',
                'capabilities': ['ad_serving', 'payments', 'p2p', 'mining', 'blockchain'],
                'metadata': {
                    'start_time': datetime.now().isoformat(),
                    'python_version': sys.version,
                    'platform': os.name,
                    'blockchain_height': len(self.blockchain.chain) if self.blockchain else 0,
                    'wallet_balance': current_balance,
                    'mining_status': 'active' if (self.mining_thread and self.mining_thread.isRunning()) else 'inactive',
                    'server_status': 'online' if self.portal_enabled else 'offline',
                    'last_balance_update': datetime.now().isoformat(),
                    'payment_address': self.wallet.address,
                    'client_type': 'desktop_wallet'
                },
                'ad_count': len(self.ads)
            }
            
            # Register in database
            success = self.db_manager.register_client(client_data)
            
            if success:
                self.log_message(f"✅ Client registered in database: {self.client_id}")
                self.log_message(f"💰 Payment address: {self.wallet.address}")
                self.log_message(f"💎 Current balance: {current_balance:.8f} PYC")
                
                # Create startup notification
                self.create_system_notification("client_startup", 
                    f"PythonCoin client {self.client_id} started successfully with {current_balance:.6f} PYC")
                
                return True
            else:
                self.log_message("❌ Failed to register client in database")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error registering client: {str(e)}")
            import traceback
            self.log_message(f"Stack trace: {traceback.format_exc()}")
            return False
    
    def start_database_sync(self):
        """Start periodic database synchronization"""
        try:
            if not hasattr(self, 'db_sync_timer'):
                self.db_sync_timer = QTimer()
                self.db_sync_timer.timeout.connect(self.update_client_in_database)
                self.db_sync_timer.start(15000)  # Update every 15 seconds
                self.log_message("✅ Database sync timer started (15 second intervals)")
            
        except Exception as e:
            self.log_message(f"❌ Error starting database sync: {str(e)}")
    
    def update_client_in_database(self):
        """Update client information in database - ENHANCED"""
        try:
            if not self.db_connected or not self.wallet:
                return
            
            # Get current balance
            current_balance = 0.0
            try:
                if hasattr(self, 'override_wallet_get_balance'):
                    current_balance = self.override_wallet_get_balance()
                elif hasattr(self.wallet, 'get_balance'):
                    current_balance = self.wallet.get_balance()
            except:
                pass
            
            # Get server port
            server_port = self.port
            if self.portal_server and hasattr(self.portal_server, 'actual_port'):
                server_port = self.portal_server.actual_port
            
            # Updated metadata with payment tracking
            updated_metadata = {
                'last_update': datetime.now().isoformat(),
                'blockchain_height': len(self.blockchain.chain) if self.blockchain else 0,
                'wallet_balance': current_balance,
                'mining_status': 'active' if (self.mining_thread and self.mining_thread.isRunning()) else 'inactive',
                'server_status': 'online' if self.portal_enabled else 'offline',
                'connected_peers': len([p for p in self.peers.values() if p.status == 'connected']),
                'ads_served': self.stats.get('ads_served', 0),
                'total_clicks': len(self.click_events),
                'total_payments': self.stats.get('payments_sent', 0),
                'revenue_generated': self.stats.get('revenue_generated', 0.0),
                'uptime_seconds': int(time.time() - self.stats.get('uptime_start', time.time())),
                'payment_address': self.wallet.address,
                'server_port': server_port,
                'last_balance_update': datetime.now().isoformat()
            }
            
            # Update in database
            query = """
                UPDATE p2p_clients 
                SET metadata = %s, ad_count = %s, last_seen = CURRENT_TIMESTAMP,
                    status = 'online', wallet_address = %s, port = %s
                WHERE client_id = %s
            """
            
            success = self.db_manager.execute_query(query, (
                json.dumps(updated_metadata),
                len(self.ads),
                self.wallet.address,
                server_port,
                self.client_id
            ))
            
            if success:
                # Only log every 5th update to avoid spam
                if not hasattr(self, '_db_update_count'):
                    self._db_update_count = 0
                self._db_update_count += 1
                
                if self._db_update_count % 5 == 0:
                    self.log_message(f"✅ Database updated (#{self._db_update_count}) - Balance: {current_balance:.6f} PYC")
            
        except Exception as e:
            self.log_message(f"❌ Error updating client in database: {str(e)}")
    
    def create_system_notification(self, notification_type, message, priority='normal'):
        """Create system notification in database"""
        try:
            if not self.db_connected:
                return
            
            notification_data = {
                'type': notification_type,
                'title': f'Client {self.client_id[:8]}',
                'message': message,
                'recipient_type': 'system',
                'metadata': {
                    'client_id': self.client_id,
                    'wallet_address': self.wallet.address if self.wallet else '',
                    'timestamp': datetime.now().isoformat(),
                    'balance': self.get_current_balance() if hasattr(self, 'get_current_balance') else 0.0
                },
                'priority': priority
            }
            
            self.db_manager.create_notification(notification_data)
            
        except Exception as e:
            self.log_message(f"❌ Error creating notification: {str(e)}")
    
    def get_current_balance(self):
        """Get current wallet balance safely"""
        try:
            if not self.wallet:
                return 0.0
            
            if hasattr(self, 'override_wallet_get_balance'):
                return self.override_wallet_get_balance()
            elif hasattr(self.wallet, 'get_balance'):
                return self.wallet.get_balance()
            else:
                return 0.0
                
        except Exception as e:
            return 0.0
    
    def check_portal_server_state(self):
        """Check and fix portal server state issues"""
        try:
            # Reset portal state if server is not actually running
            if hasattr(self, 'portal_server'):
                if self.portal_server is None or not self.portal_server.isRunning():
                    self.portal_enabled = False
                    if hasattr(self, 'portal_status'):
                        self.portal_status.setText("Status: Offline")
                    if hasattr(self, 'start_portal_btn'):
                        self.start_portal_btn.setEnabled(True)
                    if hasattr(self, 'stop_portal_btn'):
                        self.stop_portal_btn.setEnabled(False)
                    self.log_message("🔧 Fixed portal server state - was marked as running but wasn't")
                    return False
                else:
                    return True
            else:
                self.portal_enabled = False
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error checking portal state: {str(e)}")
            return False
    
    def force_stop_portal_server(self):
        """Force stop portal server and reset state"""
        try:
            self.log_message("🛑 Force stopping portal server...")
            
            if hasattr(self, 'portal_server') and self.portal_server:
                try:
                    self.portal_server.running = False
                    if self.portal_server.isRunning():
                        self.portal_server.terminate()
                        self.portal_server.wait(3000)
                except:
                    pass
                self.portal_server = None
            
            # Reset state
            self.portal_enabled = False
            if hasattr(self, 'portal_status'):
                self.portal_status.setText("Status: Offline")
            if hasattr(self, 'start_portal_btn'):
                self.start_portal_btn.setEnabled(True)
            if hasattr(self, 'stop_portal_btn'):
                self.stop_portal_btn.setEnabled(False)
            
            self.log_message("✅ Portal server force stopped and state reset")
            
        except Exception as e:
            self.log_message(f"❌ Error force stopping portal: {str(e)}")


    def export_advertisement(self, ad_id=None):
        """Export advertisement as standalone HTML file"""
        try:
            if not ad_id:
                if not self.ads:
                    QMessageBox.information(self, "No Ads", "No advertisements available to export")
                    return
                
                ad_titles = [f"{ad.title} ({ad.id[:8]}...)" for ad in self.ads]
                ad_title, ok = QInputDialog.getItem(
                    self, "Export Advertisement", "Select advertisement to export:",
                    ad_titles, 0, False
                )
                
                if not ok:
                    return
                
                # Extract ad_id from selection
                ad_id = ad_title.split('(')[1].split(')')[0].replace('...', '')
                
                # Find full ad_id
                for ad in self.ads:
                    if ad.id.startswith(ad_id):
                        ad_id = ad.id
                        break
            
            # Choose export location
            export_path, _ = QFileDialog.getSaveFileName(
                self, "Export Advertisement", 
                f"pythoncoin_ad_{ad_id[:8]}.html",
                "HTML Files (*.html);;SVG Files (*.svg);;All Files (*)"
            )
            
            if export_path:
                # Determine format from extension
                format_type = 'svg' if export_path.endswith('.svg') else 'html'
                
                # Find the ad file
                ad_file = self.ad_storage.base_dir / "active" / f"{ad_id}_{format_type}.{format_type}"
                
                if ad_file.exists():
                    shutil.copy2(ad_file, export_path)
                    QMessageBox.information(self, "Export Successful", 
                                           f"Advertisement exported to:{export_path}")
                    self.log_message(f"✅ Exported ad {ad_id[:8]}... to {export_path}")
                else:
                    QMessageBox.critical(self, "Export Failed", f"Advertisement file not found:{ad_file}")
            
        except Exception as e:
            self.log_message(f"❌ Error exporting advertisement: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"Export failed: {str(e)}")
    
    def show_ad_storage_stats(self):
        """Show detailed advertisement storage statistics"""
        try:
            stats = self.ad_storage.get_storage_stats()
            
            # Calculate additional metrics
            total_clicks = sum(getattr(ad, 'click_count', 0) for ad in self.ads)
            total_impressions = sum(getattr(ad, 'impression_count', 0) for ad in self.ads)
            avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            
            stats_text = f"""📊 Advertisement Storage Statistics

📁 Storage Information:
   • Location: {stats.get('base_directory', 'Unknown')}
   • Total Size: {stats.get('storage_size_mb', 0):.2f} MB
   • Files Stored: HTML, SVG, JSON metadata, images

📈 Advertisement Counts:
   • Active Ads: {stats.get('active_ads', 0)}
   • Archived Ads: {stats.get('inactive_ads', 0)}
   • Total Created: {stats.get('total_ads', 0)}

📊 Performance Metrics:
   • Total Clicks: {total_clicks:,}
   • Total Impressions: {total_impressions:,}
   • Average CTR: {avg_ctr:.2f}%
   • Revenue Generated: {sum(getattr(ad, 'revenue_generated', 0) for ad in self.ads):.6f} PYC

🔧 Available Actions:
   • Export ads as standalone files
   • Archive old advertisements  
   • Clean up unused assets
   • View detailed analytics

💡 Storage is automatically managed with periodic cleanup."""
            
            # Create dialog with action buttons
            dialog = QDialog(self)
            dialog.setWindowTitle("Storage Statistics")
            dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout()
            
            # Stats text
            stats_label = QLabel(stats_text)
            stats_label.setWordWrap(True)
            stats_label.setStyleSheet("font-family: monospace; font-size: 11px; padding: 15px;")
            layout.addWidget(stats_label)
            
            # Action buttons
            button_layout = QHBoxLayout()
            
            export_btn = QPushButton("📤 Export Ad")
            export_btn.clicked.connect(lambda: [dialog.accept(), self.export_advertisement()])
            button_layout.addWidget(export_btn)
            
            cleanup_btn = QPushButton("🧹 Cleanup")
            cleanup_btn.clicked.connect(lambda: [dialog.accept(), self.cleanup_ad_storage()])
            button_layout.addWidget(cleanup_btn)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            self.log_message(f"❌ Error getting storage stats: {str(e)}")
            QMessageBox.critical(self, "Stats Error", f"Failed to get statistics: {str(e)}")
    
    def cleanup_ad_storage(self):
        """Clean up old and unused advertisement files"""
        try:
            reply = QMessageBox.question(
                self, "Cleanup Storage",
                "This will:"
                "• Archive ads older than 30 days"
                "• Remove orphaned image files"
                "• Optimize storage structure"
                "• Clear temporary files"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                cleaned_count = 0
                archived_count = 0
                
                # Archive old ads
                cutoff_date = datetime.now() - timedelta(days=30)
                
                for ad in self.ads[:]:  # Copy to avoid modification during iteration
                    try:
                        created_date = datetime.fromisoformat(ad.created_at.replace('Z', '+00:00'))
                        if created_date < cutoff_date:
                            # Move to inactive
                            active_meta = self.ad_storage.base_dir / "active" / f"{ad.id}_meta.json"
                            inactive_meta = self.ad_storage.base_dir / "inactive" / f"{ad.id}_meta.json"
                            
                            if active_meta.exists():
                                shutil.move(str(active_meta), str(inactive_meta))
                                
                                # Move ad files too
                                for ext in ['html', 'svg']:
                                    active_file = self.ad_storage.base_dir / "active" / f"{ad.id}_{ext}.{ext}"
                                    inactive_file = self.ad_storage.base_dir / "inactive" / f"{ad.id}_{ext}.{ext}"
                                    if active_file.exists():
                                        shutil.move(str(active_file), str(inactive_file))
                                
                                self.ads.remove(ad)
                                archived_count += 1
                    except Exception as e:
                        self.log_message(f"Error archiving ad {ad.id}: {e}")
                        continue
                
                # Clean up orphaned files
                assets_dir = self.ad_storage.base_dir / "assets" / "images"
                if assets_dir.exists():
                    valid_ad_ids = {ad.id for ad in self.ads}
                    
                    for image_file in assets_dir.glob("*"):
                        try:
                            ad_id = image_file.stem
                            if ad_id not in valid_ad_ids:
                                image_file.unlink()
                                cleaned_count += 1
                        except:
                            pass
                
                # Update UI
                if hasattr(self, 'update_my_ads_table'):
                    self.update_my_ads_table()
                
                QMessageBox.information(self, "Cleanup Complete", 
                                       f"Storage cleanup completed!"
                                       f"• Archived {archived_count} old advertisements"
                                       f"• Cleaned {cleaned_count} orphaned files"
                                       f"• Storage optimized")
                
                self.log_message(f"✅ Storage cleanup: {archived_count} archived, {cleaned_count} cleaned")
                
        except Exception as e:
            self.log_message(f"❌ Error during cleanup: {str(e)}")
            QMessageBox.critical(self, "Cleanup Error", f"Cleanup failed: {str(e)}")
    
    def handle_ad_click_with_storage(self, ad_id, developer_address="", zone="default"):
        """Enhanced ad click handler with storage statistics"""
        try:
            # Update storage stats
            self.ad_storage.update_ad_stats(ad_id, clicks=1)
            
            # Update in-memory stats
            self.stats['clicks'] += 1
            
            # Find and update the ad object
            for ad in self.ads:
                if ad.id == ad_id:
                    if not hasattr(ad, 'click_count'):
                        ad.click_count = 0
                    ad.click_count += 1
                    
                    # Calculate revenue
                    revenue = ad.payout_rate
                    if not hasattr(ad, 'revenue_generated'):
                        ad.revenue_generated = 0
                    ad.revenue_generated += revenue
                    
                    break
            
            # Create click event
            click_event = ClickEvent(
                ad_id=ad_id,
                user_id=f"user_{int(datetime.now().timestamp())}",
                developer_address=developer_address or self.wallet.address,
                advertiser_address=self.wallet.address,
                payout_amount=getattr(ad, 'payout_rate', 0.001),
                timestamp=datetime.now().isoformat()
            )
            
            self.click_events.append(click_event)
            
            # Update database if connected
            if self.db_connected:
                try:
                    self.update_database_on_click(click_event.__dict__)
                except Exception as e:
                    self.log_message(f"Database click update error: {str(e)}")
            
            # Update UI
            if hasattr(self, 'update_my_ads_table'):
                self.update_my_ads_table()
            
            self.log_message(f"💰 Ad click recorded: {ad_id[:8]}... (+{getattr(ad, 'payout_rate', 0.001):.6f} PYC)")
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error handling ad click: {str(e)}")
            return False
    def initialize_enhanced_ad_system(self):
        """Initialize the enhanced ad system that fetches real ads"""
        try:
            self.log_message("🔄 Initializing enhanced ad system...")
            
            if not hasattr(self, 'ad_fetcher'):
                self.ad_fetcher = EnhancedAdFetcher(self)
            
            if not hasattr(self, 'dev_registration'):
                self.dev_registration = EnhancedDeveloperRegistration(self)
            
            self.replace_placeholder_ad_methods()
            
            initial_ads = self.ad_fetcher.get_real_ads(limit=50)
            self.log_message(f"✅ Enhanced ad system initialized with {len(initial_ads)} real ads")
            
            if hasattr(self, 'update_my_ads_table'):
                self.update_my_ads_table()
            
            self.start_developer_cleanup_timer()
            
        except Exception as e:
            self.log_message(f"❌ Error initializing enhanced ad system: {str(e)}")
    
    def replace_placeholder_ad_methods(self):
        """Replace placeholder ad generation with real ad fetching"""
        def enhanced_get_available_ads(self, category=None, limit=10):
            """Enhanced method to get real ads instead of placeholders"""
            if hasattr(self, 'ad_fetcher'):
                return self.ad_fetcher.get_real_ads(category, limit)
            return []
        
        self.get_available_ads = enhanced_get_available_ads.__get__(self, type(self))
    
    def update_developers_table_enhanced(self):
        """Enhanced update of developers table with online status"""
        try:
            if not hasattr(self, 'developers_table') or not hasattr(self, 'dev_registration'):
                return
            
            developers = self.dev_registration.registered_developers
            online_devs = self.dev_registration.online_developers
            
            self.developers_table.setRowCount(len(developers))
            
            if self.developers_table.columnCount() < 5:
                self.developers_table.setColumnCount(5)
                self.developers_table.setHorizontalHeaderLabels([
                    "Developer", "Address", "Status", "Clicks", "Earnings"
                ])
            
            for row, (developer, info) in enumerate(developers.items()):
                self.developers_table.setItem(row, 0, QTableWidgetItem(developer))
                
                address = info['wallet_address']
                self.developers_table.setItem(row, 1, QTableWidgetItem(f"{address[:8]}..."))
                
                if developer in online_devs:
                    status_item = QTableWidgetItem("🟢 Online")
                    status_item.setForeground(QColor(40, 167, 69))
                else:
                    status_item = QTableWidgetItem("🔴 Offline")
                    status_item.setForeground(QColor(220, 53, 69))
                self.developers_table.setItem(row, 2, status_item)
                
                clicks = info.get('total_clicks', 0)
                self.developers_table.setItem(row, 3, QTableWidgetItem(str(clicks)))
                
                earnings = info.get('total_earnings', 0.0)
                self.developers_table.setItem(row, 4, QTableWidgetItem(f"{earnings:.8f} PYC"))
            
            self.update_portal_stats_enhanced()
            
        except Exception as e:
            self.log_message(f"❌ Error updating developers table: {str(e)}")
    
    def update_portal_stats_enhanced(self):
        """Update portal statistics with enhanced info"""
        try:
            if not hasattr(self, 'dev_registration'):
                return
            
            total_devs = len(self.dev_registration.registered_developers)
            online_devs = len(self.dev_registration.online_developers)
            total_clicks = sum(info.get('total_clicks', 0) 
                             for info in self.dev_registration.registered_developers.values())
            total_earnings = sum(info.get('total_earnings', 0.0) 
                               for info in self.dev_registration.registered_developers.values())
            
            if hasattr(self, 'total_developers_label'):
                self.total_developers_label.setText(f"{total_devs} ({online_devs} online)")
            
            if hasattr(self, 'total_clicks_label'):
                self.total_clicks_label.setText(str(total_clicks))
            
            if hasattr(self, 'total_payments_label'):
                self.total_payments_label.setText(f"{total_earnings:.8f} PYC")
                
        except Exception as e:
            self.log_message(f"❌ Error updating portal stats: {str(e)}")
    
    def start_developer_cleanup_timer(self):
        """Start timer to clean up offline developers"""
        try:
            if not hasattr(self, 'dev_cleanup_timer'):
                self.dev_cleanup_timer = QTimer()
                self.dev_cleanup_timer.timeout.connect(self.cleanup_offline_developers)
                self.dev_cleanup_timer.start(60000)
                self.log_message("✅ Developer cleanup timer started")
        except Exception as e:
            self.log_message(f"❌ Error starting cleanup timer: {str(e)}")
    
    def cleanup_offline_developers(self):
        """Clean up offline developers"""
        try:
            if hasattr(self, 'dev_registration'):
                self.dev_registration.cleanup_offline_developers()
        except Exception as e:
            self.log_message(f"❌ Error in cleanup: {str(e)}")
    
    def on_enhanced_developer_registered(self, developer, address, session_info=None):
        """Handle enhanced developer registration"""
        try:
            if hasattr(self, 'dev_registration'):
                self.dev_registration.register_developer(developer, address, session_info)
            
            if hasattr(self, 'on_developer_registered'):
                self.on_developer_registered(developer, address)
        except Exception as e:
            self.log_message(f"❌ Error handling developer registration: {str(e)}")
    
    def on_enhanced_portal_click_received(self, click_data):
        """Handle enhanced ad click with developer tracking"""
        try:
            developer = click_data.get('developer', 'Unknown')
            amount = click_data.get('amount', 0)
            
            if hasattr(self, 'dev_registration'):
                self.dev_registration.update_developer_activity(developer)
                self.dev_registration.record_developer_click(developer, amount)
            
            if hasattr(self, 'on_portal_click_received'):
                self.on_portal_click_received(click_data)
        except Exception as e:
            self.log_message(f"❌ Error handling enhanced click: {str(e)}")


    def closeEvent(self, event):
        """Handle application close"""
        try:
            # Stop all threads and connections
            if self.mining_thread and self.mining_thread.isRunning():
                self.mining_thread.stop()
                self.mining_thread.wait()
            
            if self.p2p_manager and self.p2p_manager.running:
                self.p2p_manager.stop()
            
            if self.node:
                self.node.stop()
            
            # Save blockchain and wallet
            if self.blockchain:
                self.save_blockchain()
            if self.wallet:
                self.save_wallet()
            
            # Stop portal server if running
            if hasattr(self, 'portal_server') and self.portal_server:
                self.stop_portal_server()
        
            event.accept()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            event.accept()
    def create_transaction_queue_tab(self):
        """Create transaction queue management tab for automatic payments"""
        queue_widget = QWidget()
        queue_layout = QVBoxLayout()
        queue_widget.setLayout(queue_layout)
        
        # Transaction Queue Status
        status_group = QGroupBox("💰 Automatic Payment System")
        status_layout = QVBoxLayout()
        
        self.payment_system_status = QLabel("Status: Ready for incoming requests")
        self.payment_system_status.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        status_layout.addWidget(self.payment_system_status)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.enable_auto_payments_btn = QPushButton("🔴 Enable Auto-Payments")
        self.enable_auto_payments_btn.clicked.connect(self.toggle_auto_payments)
        self.enable_auto_payments_btn.setStyleSheet("background-color: #28a745;")
        controls_layout.addWidget(self.enable_auto_payments_btn)
        
        self.clear_queue_btn = QPushButton("🗑️ Clear Queue")
        self.clear_queue_btn.clicked.connect(self.clear_transaction_queue)
        controls_layout.addWidget(self.clear_queue_btn)
        
        refresh_queue_btn = QPushButton("🔄 Refresh")
        refresh_queue_btn.clicked.connect(self.update_transaction_queue_display)
        controls_layout.addWidget(refresh_queue_btn)
        
        status_layout.addLayout(controls_layout)
        status_group.setLayout(status_layout)
        queue_layout.addWidget(status_group)
        
        # Pending Transactions Queue
        pending_group = QGroupBox("📋 Pending Payment Requests")
        pending_layout = QVBoxLayout()
        
        # Transaction queue table
        self.transaction_queue_table = QTableWidget()
        self.transaction_queue_table.setColumnCount(6)
        self.transaction_queue_table.setHorizontalHeaderLabels([
            "Time", "From", "To", "Amount", "Status", "Select"
        ])
        
        queue_header = self.transaction_queue_table.horizontalHeader()
        queue_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        pending_layout.addWidget(self.transaction_queue_table)
        
        # Batch processing controls
        batch_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("☑️ Select All")
        self.select_all_btn.clicked.connect(self.select_all_transactions)
        batch_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("◻️ Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all_transactions)
        batch_layout.addWidget(self.deselect_all_btn)
        
        batch_layout.addStretch()
        
        # Submit button
        self.submit_selected_btn = QPushButton("💸 Submit Selected Payments")
        self.submit_selected_btn.clicked.connect(self.submit_selected_transactions)
        self.submit_selected_btn.setStyleSheet("background-color: #007bff; font-size: 16px; padding: 12px;")
        self.submit_selected_btn.setMinimumHeight(50)
        batch_layout.addWidget(self.submit_selected_btn)
        
        pending_layout.addLayout(batch_layout)
        pending_group.setLayout(pending_layout)
        queue_layout.addWidget(pending_group)
        
        # Auto-payment settings
        settings_group = QGroupBox("⚙️ Auto-Payment Settings")
        settings_layout = QFormLayout()
        
        self.auto_approve_limit = QDoubleSpinBox()
        self.auto_approve_limit.setDecimals(8)
        self.auto_approve_limit.setRange(0, 1000)
        self.auto_approve_limit.setValue(0.1)  # Auto-approve payments under 0.1 PYC
        settings_layout.addRow("Auto-approve limit (PYC):", self.auto_approve_limit)
        
        self.require_confirmation = QCheckBox("Require confirmation for large payments")
        self.require_confirmation.setChecked(True)
        settings_layout.addRow("", self.require_confirmation)
        
        settings_group.setLayout(settings_layout)
        queue_layout.addWidget(settings_group)
        
        # Initialize transaction queue system
        self.transaction_queue = []
        self.auto_payments_enabled = False
        
        # Start transaction queue monitoring
        self.setup_transaction_queue_monitoring()
        
        self.tab_widget.addTab(queue_widget, "💰 Payments")
    
    def setup_transaction_queue_monitoring(self):
        """Setup monitoring for incoming transaction requests"""
        try:
            # Timer to check for new transaction requests
            self.transaction_monitor_timer = QTimer()
            self.transaction_monitor_timer.timeout.connect(self.check_incoming_transactions)
            self.transaction_monitor_timer.start(2000)  # Check every 2 seconds
            
            self.log_message("✅ Transaction queue monitoring started")
            
        except Exception as e:
            self.log_message(f"❌ Error setting up transaction monitoring: {str(e)}")
    
    def check_incoming_transactions(self):
        """Check for incoming transaction requests through the node server"""
        try:
            # Check if node is running and has pending requests
            if hasattr(self, 'node') and self.node:
                # Look for incoming transaction requests in node's pending queue
                if hasattr(self.node, 'pending_payment_requests'):
                    new_requests = getattr(self.node, 'pending_payment_requests', [])
                    
                    for request in new_requests:
                        self.add_transaction_to_queue(request)
                    
                    # Clear processed requests
                    if new_requests:
                        self.node.pending_payment_requests = []
                        self.update_transaction_queue_display()
                        
                        if self.auto_payments_enabled:
                            self.process_auto_payments()
            
        except Exception as e:
            pass  # Silent fail for monitoring
    
    def add_transaction_to_queue(self, request):
        """Add a transaction request to the queue"""
        try:
            transaction_data = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'from_address': request.get('from', 'Unknown'),
                'to_address': request.get('to', ''),
                'amount': float(request.get('amount', 0)),
                'message': request.get('message', ''),
                'status': 'pending',
                'selected': False,
                'auto_eligible': float(request.get('amount', 0)) <= self.auto_approve_limit.value()
            }
            
            # Add to queue if not duplicate
            if not any(t['from_address'] == transaction_data['from_address'] and 
                      t['to_address'] == transaction_data['to_address'] and
                      t['amount'] == transaction_data['amount'] and
                      t['status'] == 'pending'
                      for t in self.transaction_queue):
                self.transaction_queue.append(transaction_data)
                self.log_message(f"📨 New payment request: {transaction_data['amount']:.6f} PYC from {transaction_data['from_address'][:8]}...")
                
                # Show notification
                if hasattr(self, 'statusBar'):
                    self.statusBar.showMessage(f"New payment request: {transaction_data['amount']:.6f} PYC", 5000)
                
                return True
            
        except Exception as e:
            self.log_message(f"❌ Error adding transaction to queue: {str(e)}")
            
        return False
    
    def update_transaction_queue_display(self):
        """Update the transaction queue display table"""
        try:
            if not hasattr(self, 'transaction_queue_table'):
                return
            
            # Clear existing rows
            self.transaction_queue_table.setRowCount(0)
            
            # Add pending transactions
            pending_transactions = [t for t in self.transaction_queue if t['status'] == 'pending']
            self.transaction_queue_table.setRowCount(len(pending_transactions))
            
            for row, transaction in enumerate(pending_transactions):
                # Time
                time_str = datetime.fromisoformat(transaction['timestamp']).strftime("%H:%M:%S")
                time_item = QTableWidgetItem(time_str)
                self.transaction_queue_table.setItem(row, 0, time_item)
                
                # From
                from_item = QTableWidgetItem(f"{transaction['from_address'][:8]}...")
                self.transaction_queue_table.setItem(row, 1, from_item)
                
                # To
                to_item = QTableWidgetItem(f"{transaction['to_address'][:8]}...")
                self.transaction_queue_table.setItem(row, 2, to_item)
                
                # Amount
                amount_item = QTableWidgetItem(f"{transaction['amount']:.8f} PYC")
                if transaction['auto_eligible']:
                    amount_item.setForeground(QColor(40, 167, 69))  # Green for auto-eligible
                else:
                    amount_item.setForeground(QColor(220, 53, 69))  # Red for manual approval
                self.transaction_queue_table.setItem(row, 3, amount_item)
                
                # Status
                status_text = "✅ Auto-eligible" if transaction['auto_eligible'] else "⚠️ Manual approval"
                status_item = QTableWidgetItem(status_text)
                self.transaction_queue_table.setItem(row, 4, status_item)
                
                # Select checkbox
                select_checkbox = QCheckBox()
                select_checkbox.setChecked(transaction['selected'])
                select_checkbox.stateChanged.connect(
                    lambda state, t_id=transaction['id']: self.update_transaction_selection(t_id, state == 2)
                )
                self.transaction_queue_table.setCellWidget(row, 5, select_checkbox)
            
            # Update status
            if hasattr(self, 'payment_system_status'):
                pending_count = len(pending_transactions)
                selected_count = len([t for t in pending_transactions if t['selected']])
                auto_eligible_count = len([t for t in pending_transactions if t['auto_eligible']])
                
                status_text = f"Status: {pending_count} pending ({selected_count} selected, {auto_eligible_count} auto-eligible)"
                self.payment_system_status.setText(status_text)
            
        except Exception as e:
            self.log_message(f"❌ Error updating queue display: {str(e)}")
    
    def toggle_auto_payments(self):
        """Toggle automatic payments on/off"""
        try:
            self.auto_payments_enabled = not self.auto_payments_enabled
            
            if self.auto_payments_enabled:
                self.enable_auto_payments_btn.setText("🟢 Auto-Payments ON")
                self.enable_auto_payments_btn.setStyleSheet("background-color: #28a745;")
                self.log_message("✅ Automatic payments enabled")
                
                # Process any eligible transactions immediately
                self.process_auto_payments()
            else:
                self.enable_auto_payments_btn.setText("🔴 Auto-Payments OFF")
                self.enable_auto_payments_btn.setStyleSheet("background-color: #dc3545;")
                self.log_message("⏸️ Automatic payments disabled")
                
        except Exception as e:
            self.log_message(f"❌ Error toggling auto-payments: {str(e)}")
    
    def process_auto_payments(self):
        """Process payments that are eligible for automatic approval"""
        try:
            if not self.auto_payments_enabled:
                return
            
            auto_processed = 0
            for transaction in self.transaction_queue:
                if (transaction['status'] == 'pending' and 
                    transaction['auto_eligible'] and 
                    transaction['amount'] <= self.auto_approve_limit.value()):
                    
                    # Process the payment
                    success = self.execute_transaction_payment(transaction)
                    if success:
                        transaction['status'] = 'completed_auto'
                        auto_processed += 1
            
            if auto_processed > 0:
                self.log_message(f"🤖 Auto-processed {auto_processed} payments")
                self.update_transaction_queue_display()
                
        except Exception as e:
            self.log_message(f"❌ Error in auto-payment processing: {str(e)}")
    
    def select_all_transactions(self):
        """Select all pending transactions"""
        try:
            for transaction in self.transaction_queue:
                if transaction['status'] == 'pending':
                    transaction['selected'] = True
            
            self.update_transaction_queue_display()
            
        except Exception as e:
            self.log_message(f"❌ Error selecting all transactions: {str(e)}")
    
    def deselect_all_transactions(self):
        """Deselect all transactions"""
        try:
            for transaction in self.transaction_queue:
                transaction['selected'] = False
            
            self.update_transaction_queue_display()
            
        except Exception as e:
            self.log_message(f"❌ Error deselecting transactions: {str(e)}")
    
    def update_transaction_selection(self, transaction_id, selected):
        """Update selection state of a specific transaction"""
        try:
            for transaction in self.transaction_queue:
                if transaction['id'] == transaction_id:
                    transaction['selected'] = selected
                    break
                    
        except Exception as e:
            self.log_message(f"❌ Error updating selection: {str(e)}")
    
    def submit_selected_transactions(self):
        """Submit all selected transactions for payment"""
        try:
            selected_transactions = [t for t in self.transaction_queue 
                                   if t['selected'] and t['status'] == 'pending']
            
            if not selected_transactions:
                QMessageBox.warning(self, "No Selection", "Please select transactions to process")
                return
            
            # Calculate total amount
            total_amount = sum(t['amount'] for t in selected_transactions)
            
            # Check balance
            current_balance = self.get_current_balance()
            
            if total_amount > current_balance:
                QMessageBox.warning(self, "Insufficient Funds", 
                                   f"Total amount: {total_amount:.8f} PYC"
                                   f"Available balance: {current_balance:.8f} PYC")
                return
            
            # Confirm submission
            reply = QMessageBox.question(self, "Confirm Payments", 
                                       f"Submit {len(selected_transactions)} payments for a total of {total_amount:.8f} PYC?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                # Process each selected transaction
                successful_payments = 0
                failed_payments = 0
                
                for transaction in selected_transactions:
                    success = self.execute_transaction_payment(transaction)
                    if success:
                        transaction['status'] = 'completed_manual'
                        successful_payments += 1
                    else:
                        transaction['status'] = 'failed'
                        failed_payments += 1
                
                # Show results
                QMessageBox.information(self, "Payment Results", 
                                       f"Payment processing complete:"
                                       f"✅ Successful: {successful_payments}"
                                       f"❌ Failed: {failed_payments}")
                
                self.log_message(f"💸 Batch payment complete: {successful_payments} successful, {failed_payments} failed")
                self.update_transaction_queue_display()
                
        except Exception as e:
            self.log_message(f"❌ Error submitting transactions: {str(e)}")
            QMessageBox.critical(self, "Payment Error", f"Error processing payments: {str(e)}")
    
    def execute_transaction_payment(self, transaction):
        """Execute a single transaction payment"""
        try:
            if not self.wallet or not self.blockchain:
                return False
            
            # Create and send transaction
            tx = self.wallet.send(transaction['to_address'], transaction['amount'])
            
            if tx:
                self.log_message(f"💰 Payment sent: {transaction['amount']:.6f} PYC to {transaction['to_address'][:8]}...")
                
                # Update stats
                self.stats['payments_sent'] = self.stats.get('payments_sent', 0) + 1
                
                # Save blockchain state
                if hasattr(self, 'save_blockchain'):
                    self.save_blockchain()
                
                return True
            else:
                self.log_message(f"❌ Payment failed: {transaction['amount']:.6f} PYC to {transaction['to_address'][:8]}...")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Transaction execution error: {str(e)}")
            return False
    
    def clear_transaction_queue(self):
        """Clear completed/failed transactions from queue"""
        try:
            original_count = len(self.transaction_queue)
            
            # Keep only pending transactions
            self.transaction_queue = [t for t in self.transaction_queue if t['status'] == 'pending']
            
            cleared_count = original_count - len(self.transaction_queue)
            
            if cleared_count > 0:
                self.log_message(f"🗑️ Cleared {cleared_count} completed transactions from queue")
                self.update_transaction_queue_display()
            else:
                QMessageBox.information(self, "Queue Clean", "No completed transactions to clear")
                
        except Exception as e:
            self.log_message(f"❌ Error clearing queue: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            event.accept()


    def get_local_ip(self):
        """Get local IP address for client registration"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"

    def register_client_in_database(self):
        """Register this client in the database with complete information"""
        try:
            if not self.db_connected or not self.wallet:
                self.log_message("⚠️ Cannot register client - database or wallet not ready")
                return False
            
            # Gather comprehensive client information
            client_data = {
                'client_id': self.client_id,
                'name': f'PythonCoin Wallet - {self.wallet.address[:8]}...',
                'host': self.get_local_ip(),
                'port': self.port,
                'username': f'user_{self.wallet.address[:8]}',
                'wallet_address': self.wallet.address,
                'version': '2.1.0',
                'capabilities': ['ad_serving', 'payments', 'p2p', 'mining', 'blockchain'],
                'metadata': {
                    'start_time': datetime.now().isoformat(),
                    'python_version': sys.version,
                    'platform': os.name,
                    'blockchain_height': len(self.blockchain.chain) if self.blockchain else 0,
                    'wallet_balance': self.get_current_balance(),
                    'mining_status': 'active' if (self.mining_thread and self.mining_thread.isRunning()) else 'inactive',
                    'server_status': 'online' if self.portal_enabled else 'offline'
                },
                'ad_count': len(self.ads)
            }
            
            # Register client in database
            success = self.db_manager.register_client(client_data)
            
            if success:
                self.log_message(f"✅ Client registered in database: {self.client_id}")
                
                # Also populate initial ads if any exist
                self.sync_ads_to_database()
                
                # Create startup notification
                self.create_system_notification("client_startup", 
                    f"PythonCoin client {self.client_id} started successfully")
                
                return True
            else:
                self.log_message("❌ Failed to register client in database")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error registering client: {str(e)}")
            return False

    def sync_ads_to_database(self):
        """Sync all current ads to database"""
        try:
            if not self.db_connected:
                return
            
            synced_count = 0
            for ad in self.ads:
                ad_data = ad.to_dict() if hasattr(ad, 'to_dict') else ad.__dict__
                
                # Ensure required fields
                ad_data['client_id'] = self.client_id
                ad_data['peer_source'] = self.client_id
                
                if self.db_manager.create_ad(ad_data):
                    synced_count += 1
            
            if synced_count > 0:
                self.log_message(f"✅ Synced {synced_count} ads to database")
                
        except Exception as e:
            self.log_message(f"❌ Error syncing ads: {str(e)}")

    def update_client_status_in_database(self):
        """Update client status and metadata in database"""
        try:
            if not self.db_connected:
                return
            
            # Update client metadata
            updated_metadata = {
                'last_update': datetime.now().isoformat(),
                'blockchain_height': len(self.blockchain.chain) if self.blockchain else 0,
                'wallet_balance': self.get_current_balance(),
                'mining_status': 'active' if (self.mining_thread and self.mining_thread.isRunning()) else 'inactive',
                'server_status': 'online' if self.portal_enabled else 'offline',
                'connected_peers': len([p for p in self.peers.values() if p.status == 'connected']),
                'ads_served': self.stats.get('ads_served', 0),
                'total_clicks': len(self.click_events),
                'uptime_seconds': int(time.time() - self.stats.get('uptime_start', time.time()))
            }
            
            # Update in database
            query = """
                UPDATE p2p_clients 
                SET metadata = %s, ad_count = %s, last_seen = CURRENT_TIMESTAMP,
                    status = 'online'
                WHERE client_id = %s
            """
            
            success = self.db_manager.execute_query(query, (
                json.dumps(updated_metadata),
                len(self.ads),
                self.client_id
            ))
            
            if success:
                self.log_message(f"✅ Updated client status in database")
            
        except Exception as e:
            self.log_message(f"❌ Error updating client status: {str(e)}")

    def record_developer_session(self, developer_address, session_data):
        """Record developer session in database"""
        try:
            if not self.db_connected:
                return False
            
            query = """
                INSERT INTO developer_sessions 
                (client_id, developer_address, session_start, session_data, status)
                VALUES (%s, %s, CURRENT_TIMESTAMP, %s, 'active')
                ON DUPLICATE KEY UPDATE
                session_data = VALUES(session_data),
                last_activity = CURRENT_TIMESTAMP,
                status = 'active'
            """
            
            session_json = json.dumps({
                'user_agent': session_data.get('user_agent', ''),
                'ip_address': session_data.get('ip_address', ''),
                'capabilities': session_data.get('capabilities', []),
                'preferences': session_data.get('preferences', {}),
                'js_file_generated': session_data.get('js_file', ''),
                'ads_requested': session_data.get('ads_requested', [])
            })
            
            success = self.db_manager.execute_query(query, (
                self.client_id,
                developer_address,
                session_json
            ))
            
            if success:
                self.log_message(f"✅ Recorded developer session: {developer_address[:8]}...")
                return True
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error recording developer session: {str(e)}")
            return False

    def record_ad_impression(self, ad_id, developer_address, impression_data):
        """Record ad impression in database"""
        try:
            if not self.db_connected:
                return False
            
            query = """
                INSERT INTO ad_impressions 
                (ad_id, client_id, developer_address, impression_time, impression_data)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)
            """
            
            impression_json = json.dumps({
                'user_agent': impression_data.get('user_agent', ''),
                'ip_address': impression_data.get('ip_address', ''),
                'zone': impression_data.get('zone', 'default'),
                'viewport_size': impression_data.get('viewport_size', ''),
                'referrer': impression_data.get('referrer', ''),
                'session_id': impression_data.get('session_id', '')
            })
            
            success = self.db_manager.execute_query(query, (
                ad_id,
                self.client_id,
                developer_address,
                impression_json
            ))
            
            if success:
                self.stats['impressions'] = self.stats.get('impressions', 0) + 1
                self.log_message(f"✅ Recorded ad impression: {ad_id}")
                return True
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error recording impression: {str(e)}")
            return False

    def setup_database_update_timer(self):
        """Setup timer for periodic database updates"""
        try:
            self.db_update_timer = QTimer()
            self.db_update_timer.timeout.connect(self.periodic_database_update)
            self.db_update_timer.start(30000)  # Update every 30 seconds
            self.log_message("✅ Database update timer started (30 second intervals)")
            
        except Exception as e:
            self.log_message(f"❌ Error setting up database timer: {str(e)}")

    def periodic_database_update(self):
        """Perform periodic database updates"""
        try:
            if not self.db_connected:
                return
            
            # Update client status
            self.update_client_status_in_database()
            
            # Update peer information if we have discovered peers
            self.sync_peers_to_database()
            
            # Clean up old sessions
            self.cleanup_old_sessions()
            
        except Exception as e:
            self.log_message(f"❌ Periodic database update error: {str(e)}")

    def sync_peers_to_database(self):
        """Sync discovered peers to database"""
        try:
            if not self.db_connected:
                return
            
            synced_count = 0
            for peer_id, peer in self.peers.items():
                if peer_id == self.client_id:  # Skip ourselves
                    continue
                
                peer_data = {
                    'client_id': peer_id,
                    'name': f'Peer - {peer_id[:8]}...',
                    'host': peer.host,
                    'port': peer.port,
                    'username': f'peer_{peer_id[:8]}',
                    'wallet_address': peer.wallet_address,
                    'version': '2.1.0',
                    'capabilities': peer.capabilities,
                    'metadata': {
                        'discovered_by': self.client_id,
                        'discovery_time': peer.last_seen,
                        'peer_status': peer.status
                    },
                    'ad_count': peer.ad_count
                }
                
                if self.db_manager.register_client(peer_data):
                    synced_count += 1
            
            if synced_count > 0:
                self.log_message(f"✅ Synced {synced_count} peers to database")
                
        except Exception as e:
            self.log_message(f"❌ Error syncing peers: {str(e)}")

    def cleanup_old_sessions(self):
        """Clean up old developer sessions"""
        try:
            if not self.db_connected:
                return
            
            # Mark sessions as inactive if no activity for 1 hour
            query = """
                UPDATE developer_sessions 
                SET status = 'inactive'
                WHERE last_activity < DATE_SUB(NOW(), INTERVAL 1 HOUR)
                AND status = 'active'
            """
            
            self.db_manager.execute_query(query)
            
        except Exception as e:
            self.log_message(f"❌ Error cleaning up sessions: {str(e)}")

    def create_system_notification(self, notification_type, message, priority='normal'):
        """Create system notification in database"""
        try:
            if not self.db_connected:
                return
            
            notification_data = {
                'type': notification_type,
                'title': f'Client {self.client_id[:8]}',
                'message': message,
                'recipient_type': 'system',
                'metadata': {
                    'client_id': self.client_id,
                    'wallet_address': self.wallet.address if self.wallet else '',
                    'timestamp': datetime.now().isoformat()
                },
                'priority': priority
            }
            
            self.db_manager.create_notification(notification_data)
            
        except Exception as e:
            self.log_message(f"❌ Error creating notification: {str(e)}")

    def get_current_balance(self):
        """Get current wallet balance safely"""
        try:
            if not self.wallet:
                return 0.0
            
            if hasattr(self, 'override_wallet_get_balance'):
                return self.override_wallet_get_balance()
            elif hasattr(self.wallet, 'get_balance'):
                return self.wallet.get_balance()
            else:
                return 0.0
                
        except Exception as e:
            return 0.0



        
    def start_portal_server(self):
        """Start the working developer portal server"""
        if not self.wallet:
            QMessageBox.warning(self, "Portal Error", "No wallet loaded")
            return
        
        if hasattr(self, 'portal_server') and self.portal_server and self.portal_server.running:
            self.log_message("⚠️ Portal server is already running")
            return
        
        try:
            self.log_message("🚀 Starting working portal server...")
            
            # Create the working server
            self.portal_server = WorkingDeveloperPortalServer(
                host='0.0.0.0',  # Listen on all interfaces
                port=8082,
                wallet=self.wallet,
                blockchain=self.blockchain,
                db_manager=getattr(self, 'db_manager', None)
            )
            
            # Start the server
            if self.portal_server.start():
                self.portal_enabled = True
                
                # Update UI
                if hasattr(self, 'portal_status'):
                    self.portal_status.setText("Status: Online ✅")
                if hasattr(self, 'start_portal_btn'):
                    self.start_portal_btn.setEnabled(False)
                if hasattr(self, 'stop_portal_btn'):
                    self.stop_portal_btn.setEnabled(True)
                
                self.log_message("✅ Working portal server started successfully on port 8082")
                
                # Test the connection
                QTimer.singleShot(2000, self.test_portal_connection_working)
            else:
                self.log_message("❌ Failed to start working portal server")
                
        except Exception as e:
            self.log_message(f"❌ Error starting working portal server: {str(e)}")
            import traceback
            self.log_message(f"Stack trace: {traceback.format_exc()}")

    def stop_portal_server(self):
        """Stop the working developer portal server"""
        try:
            if hasattr(self, 'portal_server') and self.portal_server:
                self.portal_server.stop()
                self.portal_server = None
            
            self.portal_enabled = False
            
            # Update UI
            if hasattr(self, 'portal_status'):
                self.portal_status.setText("Status: Offline")
            if hasattr(self, 'start_portal_btn'):
                self.start_portal_btn.setEnabled(True)
            if hasattr(self, 'stop_portal_btn'):
                self.stop_portal_btn.setEnabled(False)
            
            self.log_message("✅ Portal server stopped")
            
        except Exception as e:
            self.log_message(f"❌ Error stopping portal server: {str(e)}")

    def test_portal_connection_working(self):
        """Test the working portal connection"""
        try:
            import urllib.request
            
            test_url = "http://127.0.0.1:8082/test"
            
            with urllib.request.urlopen(test_url, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get('success'):
                    self.log_message("✅ Working portal server test successful!")
                    
                    # Try the registration endpoint too
                    self.test_registration_endpoint()
                else:
                    self.log_message("⚠️ Portal server responded but returned error")
                    
        except Exception as e:
            self.log_message(f"❌ Portal connection test failed: {str(e)}")

    def test_registration_endpoint(self):
        """Test the registration endpoint specifically"""
        try:
            import urllib.request
            
            test_data = {
                'developer': 'test_developer',
                'pythoncoin_address': '1TestAddress123456789'
            }
            
            req = urllib.request.Request(
                'http://127.0.0.1:8082/register_developer',
                data=json.dumps(test_data).encode(),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get('success'):
                    self.log_message("✅ Registration endpoint test successful!")
                else:
                    self.log_message(f"⚠️ Registration test failed: {data.get('error', 'Unknown error')}")
                    
        except Exception as e:
            self.log_message(f"❌ Registration endpoint test failed: {str(e)}")

    def on_enhanced_portal_click_received(self, click_data):
        """Handle enhanced ad click from portal with database integration"""
        try:
            developer = click_data.get('developer', 'Unknown')
            amount = click_data.get('amount', 0)
            ad_id = click_data.get('ad_id', '')
            developer_address = click_data.get('pythoncoin_address', '')
            
            self.log_message(f"💰 Portal click: {amount:.6f} PYC -> {developer}")
            
            # Record click in database if connected
            if self.db_connected and ad_id and developer_address:
                click_record = {
                    'ad_id': ad_id,
                    'client_id': self.client_id,
                    'zone': click_data.get('zone', 'default'),
                    'payout_amount': amount,
                    'ip_address': click_data.get('ip_address', '127.0.0.1'),
                    'user_agent': click_data.get('user_agent', ''),
                    'metadata': {
                        'developer': developer,
                        'timestamp': datetime.now().isoformat(),
                        'session_id': click_data.get('session_id', ''),
                        'referrer': click_data.get('referrer', '')
                    }
                }
                
                self.db_manager.record_ad_click(click_record)
                self.log_message(f"✅ Click recorded in database")
            
            # Update portal stats
            self.update_portal_stats()
            
            # Save blockchain state
            if hasattr(self, 'save_blockchain'):
                self.save_blockchain()
                
        except Exception as e:
            self.log_message(f"❌ Error handling portal click: {str(e)}")

    def on_client_notification(self, notification_data):
        """Handle client notifications from portal server"""
        try:
            notification_type = notification_data.get('type', 'general')
            message = notification_data.get('message', '')
            
            self.log_message(f"📢 Portal notification: {message}")
            
            # Store notification in database if connected
            if self.db_connected:
                self.create_system_notification(notification_type, message)
                
        except Exception as e:
            self.log_message(f"❌ Error handling notification: {str(e)}")



    def original_create_advertisement(self):
        """Create and publish advertisement to P2P network with database integration"""
        if not self.wallet:
            QMessageBox.warning(self, "Ad Creation Error", "No wallet loaded")
            return
        
        title = self.ad_title_input.text().strip()
        description = self.ad_description_input.toPlainText().strip()
        click_url = self.ad_click_url_input.text().strip()
        category = self.ad_category_combo.currentText()
        payout_rate = self.ad_payout_input.value()
        daily_budget = self.daily_budget_input.value()
        max_clicks = self.max_clicks_input.value()
        
        # Validation
        if not title or not description:
            QMessageBox.warning(self, "Validation Error", "Please fill in title and description")
            return
        
        if len(title) < 5:
            QMessageBox.warning(self, "Validation Error", "Title must be at least 5 characters")
            return
        
        if len(description) < 20:
            QMessageBox.warning(self, "Validation Error", "Description must be at least 20 characters")
            return
        
        if not click_url.startswith(('http://', 'https://')):
            click_url = 'http://' + click_url if click_url else 'https://example.com'
        
        # Check balance
        try:
            balance = self.get_current_balance()
        except Exception as e:
            self.log_message(f"Error getting balance: {str(e)}")
            balance = 0.0
        
        if balance < daily_budget:
            QMessageBox.warning(self, "Insufficient Funds", 
                                f"You need at least {daily_budget:.8f} PYC for one day of advertising."
                               f"Current balance: {balance:.8f} PYC")
            return
        
        try:
            # Create ad object
            ad_id = str(uuid.uuid4())
            
            # Get image URL
            image_url = ""
            if hasattr(self, 'current_ad_image'):
                image_url = f"file://{self.current_ad_image}"
            
            # Get targeting options
            interests = [i.strip() for i in self.target_interests.text().split(',') if i.strip()]
            targeting = {
                'interests': interests,
                'geographic': self.target_geo.currentText(),
                'budget_daily': daily_budget,
                'max_clicks_daily': max_clicks
            }
            
            ad = AdContent(
                id=ad_id,
                title=title,
                description=description,
                image_url=image_url,
                click_url=click_url,
                category=category,
                targeting=targeting,
                created_at=datetime.now().isoformat(),
                expires_at=(datetime.now() + timedelta(days=30)).isoformat(),
                peer_source=self.client_id,
                payout_rate=payout_rate,
                advertiser_address=self.wallet.address
            )
            
            # Add to local ads
            self.ads.append(ad)
            
            # ENHANCED: Save to database immediately
            if self.db_connected:
                ad_data = ad.to_dict()
                ad_data['client_id'] = self.client_id
                ad_data['peer_source'] = self.client_id
                
                success = self.db_manager.create_ad(ad_data)
                if success:
                    self.log_message(f"✅ Ad saved to database: {title}")
                    
                    # Create notification about new ad
                    self.create_system_notification("ad_created", 
                        f"New advertisement created: {title} ({payout_rate:.6f} PYC/click)")
                    
                    # Update client ad count
                    self.update_client_status_in_database()
                else:
                    self.log_message(f"❌ Failed to save ad to database")
            
            # Broadcast to P2P network if connected
            if self.p2p_manager and self.p2p_manager.running:
                self.broadcast_new_ad(ad)
            
            # Notify portal server if running
            if self.portal_server and self.portal_server.running:
                notification_data = {
                    'ad_data': ad.to_dict(),
                    'advertiser_address': self.wallet.address
                }
                try:
                    self.portal_server.handle_notify_ad_created(notification_data)
                except Exception as e:
                    self.log_message(f"Portal notification error: {str(e)}")
            
            # Update UI
            self.update_my_ads_table()
            self.clear_ad_form()
            
            QMessageBox.information(self, "Success", 
                                   f"Advertisement '{title}' created successfully!"
                                   f"• Payout: {payout_rate:.8f} PYC per click"
                                   f"• Daily Budget: {daily_budget:.8f} PYC"
                                   f"• Max Clicks: {max_clicks:,}"
                                   f"Your ad is now live on the P2P network!")
            
            self.log_message(f"✅ Created new advertisement: {title}")
            self.stats['ads_served'] += 1
            
        except Exception as e:
            self.log_message(f"❌ Error creating advertisement: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to create advertisement: {str(e)}")


# ============================================================================
# Enhanced Genesis Coordination Script
# ============================================================================

    def run_genesis_coordination():
        """
        Standalone function to coordinate genesis block creation among multiple clients.
        This can be run before starting the main wallet application.
        """
        print("=== PythonCoin Genesis Coordination ===")
        
        # Discover peers on the network
        discovered_peers = []
        
        print("Discovering peers for genesis coordination...")
        
        # UDP broadcast to find other clients
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(2.0)
        
        try:
            # Broadcast discovery message
            discovery_msg = {
                'type': 'genesis_discovery',
                'timestamp': time.time(),
                'requesting_genesis': True
            }
            
            data = json.dumps(discovery_msg).encode()
            sock.sendto(data, ('255.255.255.255', 8083))  # Different port for genesis coordination
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < 10:  # 10 second discovery window
                try:
                    response_data, addr = sock.recvfrom(1024)
                    response = json.loads(response_data.decode())
                    
                    if response.get('type') == 'genesis_response':
                        peer_info = {
                            'host': addr[0],
                            'wallet_address': response.get('wallet_address', ''),
                            'timestamp': response.get('timestamp', time.time())
                        }
                        discovered_peers.append(peer_info)
                        print(f"Found peer: {addr[0]} with wallet {peer_info['wallet_address'][:8]}...")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Discovery error: {e}")
                    
        except Exception as e:
            print(f"Genesis coordination error: {e}")
        finally:
            sock.close()
        
        print(f"Discovery complete. Found {len(discovered_peers)} peers.")
        
        if len(discovered_peers) > 0:
            print("Genesis block will be created with fair distribution to all participants.")
            return [peer['wallet_address'] for peer in discovered_peers if peer['wallet_address']]
        else:
            print("No peers found. Genesis block will be created for single wallet.")
            return []

# ============================================================================
# Main Application Entry Point (Enhanced)
# ============================================================================


    # ============================================================================
    # Performance Optimizations to Prevent Freezing
    # ============================================================================
    
    def _delayed_ui_update(self):
        """Delayed UI update handler"""
        self._ui_update_pending = False
        self._perform_ui_update()
        self._last_ui_update = time.time()
    
    def _perform_ui_update(self):
        """Actually perform UI updates"""
        if self.wallet:
            self.update_wallet_display()
            self.update_dashboard()
            # Only update transactions occasionally
            if hasattr(self, '_last_tx_update'):
                if time.time() - self._last_tx_update > 10:  # Every 10 seconds
                    self.update_transactions()
                    self._last_tx_update = time.time()
            else:
                self._last_tx_update = time.time()
                self.update_transactions()
    
    def optimized_save_blockchain(self):
        """Optimized blockchain saving to prevent freezing"""
        try:
            # Don't save too frequently
            if not hasattr(self, '_last_blockchain_save'):
                self._last_blockchain_save = 0
            
            current_time = time.time()
            if current_time - self._last_blockchain_save < 10:  # Minimum 10 seconds between saves
                return
            
            self._last_blockchain_save = current_time
            
            # Run save in background thread
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
    def save_worker():
                try:
                    self.save_blockchain()
                except Exception as e:
                    self.log_message(f"Background save error: {str(e)}")
            
                    threading.Thread(target=save_worker, daemon=True).start()
            
                except Exception as e:
                    self.log_message(f"Optimized save error: {str(e)}")
            
    def optimized_balance_calculation(self):
        """Optimized balance calculation with caching"""
        try:
            # Cache balance calculation results
            if not hasattr(self, '_cached_balance') or not hasattr(self, '_balance_cache_time'):
                self._cached_balance = 0.0
                self._balance_cache_time = 0
            
            current_time = time.time()
            
            # Cache balance for 5 seconds to prevent frequent recalculation
            if current_time - self._balance_cache_time < 5.0:
                return self._cached_balance
            
            # Calculate balance (use fastest method available)
            try:
                if hasattr(self.wallet, 'get_balance'):
                    balance = self.wallet.get_balance()
                elif hasattr(self.blockchain, 'get_balance') and self.wallet:
                    balance = self.blockchain.get_balance(self.wallet.address)
                else:
                    balance = 0.0
                
                self._cached_balance = balance
                self._balance_cache_time = current_time
                return balance
                
            except Exception as e:
                self.log_message(f"Balance calculation error: {str(e)}")
                return self._cached_balance  # Return cached value on error
                
        except Exception as e:
            self.log_message(f"Optimized balance error: {str(e)}")
            return 0.0
    
    def update_critical_info(self):
        """Update only critical information frequently"""
        try:
            # Only update essential info that users need to see immediately
            if self.wallet and hasattr(self, 'balance_label'):
                balance = self.optimized_balance_calculation()
                self.balance_label.setText(f"Balance: {balance:.8f} PYC")
            
            # Update mining status if mining
            if hasattr(self, 'mining_thread') and self.mining_thread and self.mining_thread.isRunning():
                if hasattr(self, 'mining_status_label'):
                    self.mining_status_label.setText("Mining: Active")
            
        except Exception as e:
            pass  # Silent fail for critical updates
    
    def optimized_create_advertisement(self):
        """Optimized advertisement creation to prevent freezing"""
        if not self.wallet:
            QMessageBox.warning(self, "Ad Creation Error", "No wallet loaded")
            return
        
        title = self.ad_title_input.text().strip()
        description = self.ad_description_input.toPlainText().strip()
        click_url = self.ad_click_url_input.text().strip()
        category = self.ad_category_combo.currentText()
        payout_rate = self.ad_payout_input.value()
        daily_budget = self.daily_budget_input.value()
        max_clicks = self.max_clicks_input.value()
        
        # Validation
        if not title or not description:
            QMessageBox.warning(self, "Validation Error", "Please fill in title and description")
            return
        
        if len(title) < 5:
            QMessageBox.warning(self, "Validation Error", "Title must be at least 5 characters")
            return
        
        if len(description) < 20:
            QMessageBox.warning(self, "Validation Error", "Description must be at least 20 characters")
            return
        
        if not click_url.startswith(('http://', 'https://')):
            click_url = 'http://' + click_url if click_url else 'https://example.com'
        
        # Use optimized balance calculation
        try:
            balance = self.optimized_balance_calculation()
        except Exception as e:
            self.log_message(f"Error getting balance: {str(e)}")
            balance = 0.0
        
        if balance < daily_budget:
            QMessageBox.warning(self, "Insufficient Funds", 
                               f"You need at least {daily_budget:.8f} PYC for one day of advertising."
                               f"Current balance: {balance:.8f} PYC")
            return
        
        # Create advertisement in background to prevent UI freezing
    def create_ad_worker():
            try:
                # Create ad object
                ad_id = str(uuid.uuid4())
                
                # Get image URL
                image_url = ""
                if hasattr(self, 'current_ad_image'):
                    image_url = f"file://{self.current_ad_image}"
                
                # Get targeting options
                interests = [i.strip() for i in self.target_interests.text().split(',') if i.strip()]
                targeting = {
                    'interests': interests,
                    'geographic': self.target_geo.currentText(),
                    'budget_daily': daily_budget,
                    'max_clicks_daily': max_clicks
                }
                
                ad = AdContent(
                    id=ad_id,
                    title=title,
                    description=description,
                    image_url=image_url,
                    click_url=click_url,
                    category=category,
                    targeting=targeting,
                    created_at=datetime.now().isoformat(),
                    expires_at=(datetime.now() + timedelta(days=30)).isoformat(),
                    peer_source=self.client_id,
                    payout_rate=payout_rate,
                    advertiser_address=self.wallet.address
                )
                
                # Add to local ads
                self.ads.append(ad)
            
            # Update database
                self.update_database_on_ad_creation(ad)
                
                # Notify network in background
                if self.portal_server and self.portal_server.running:
                    try:
                        notification_data = {
                            'ad_data': ad.to_dict(),
                            'advertiser_address': self.wallet.address
                        }
                        self.portal_server.handle_notify_ad_created(notification_data)
                    except Exception as e:
                        self.log_message(f"Notification error: {str(e)}")
                
                # Update UI in main thread
                QTimer.singleShot(0, lambda: self._finish_ad_creation(ad))
                
            except Exception as e:
                QTimer.singleShot(0, lambda: self._handle_ad_creation_error(str(e)))
        
        # Show progress and start background work
                self.show_ad_creation_progress()
                threading.Thread(target=create_ad_worker, daemon=True).start()
            
    def show_ad_creation_progress(self):
        """Show progress while creating ad"""
        if hasattr(self, 'ad_creation_progress'):
            return  # Already showing
        
        self.ad_creation_progress = QMessageBox(self)
        self.ad_creation_progress.setWindowTitle("Creating Advertisement")
        self.ad_creation_progress.setText("Creating your advertisement...\n\nThis may take a few moments.")
        self.ad_creation_progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        self.ad_creation_progress.show()
    
    def _finish_ad_creation(self, ad):
        """Finish ad creation in main thread"""
        try:
            # Close progress dialog
            if hasattr(self, 'ad_creation_progress'):
                self.ad_creation_progress.close()
                delattr(self, 'ad_creation_progress')
            
            # Update UI
            self.update_my_ads_table()
            self.clear_ad_form()
            
            QMessageBox.information(self, "Success", 
                                   f"Advertisement '{ad.title}' created successfully!\n"
                                   f"• Payout: {ad.payout_rate:.8f} PYC per click\n"
                                   f"• Daily Budget: {ad.targeting.get('budget_daily', 0):.8f} PYC\n"
                                   f"Your ad is now live on the P2P network!")
            
            self.log_message(f"Created new advertisement: {ad.title}")
            self.stats['ads_served'] += 1
            
        except Exception as e:
            self.log_message(f"Error finishing ad creation: {str(e)}")
    
    def _handle_ad_creation_error(self, error_msg):
        """Handle ad creation error in main thread"""
        if hasattr(self, 'ad_creation_progress'):
            self.ad_creation_progress.close()
            delattr(self, 'ad_creation_progress')
        
        self.log_message(f"Error creating advertisement: {error_msg}")
        QMessageBox.critical(self, "Error", f"Failed to create advertisement: {error_msg}")



class EnhancedPythonCoinNode:
    """Enhanced PythonCoin node with payment request handling"""
    
    def __init__(self, host="0.0.0.0", port=5000, blockchain=None, wallet=None, main_wallet_instance=None):
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.wallet = wallet
        self.main_wallet = main_wallet_instance
        self.running = False
        self.server = None
        self.pending_payment_requests = []
        
    def start(self):
        """Start the enhanced node server"""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import json
            import urllib.parse
            
            self.running = True
            
            class EnhancedNodeHandler(BaseHTTPRequestHandler):
                def log_message(self, format, *args):
                    # Custom logging
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[Node {timestamp}] {format % args}")
                
                def do_OPTIONS(self):
                    """Handle CORS preflight requests"""
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()
                
                def do_GET(self):
                    """Handle GET requests"""
                    try:
                        parsed_path = urllib.parse.urlparse(self.path)
                        path = parsed_path.path
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        
                        if path == '/status':
                            response = {
                                'success': True,
                                'status': 'Enhanced PythonCoin Node Active',
                                'blockchain_height': len(self.server.blockchain.chain) if self.server.blockchain else 0,
                                'pending_transactions': len(self.server.blockchain.pending_transactions) if self.server.blockchain else 0,
                                'pending_payment_requests': len(self.server.pending_payment_requests),
                                'wallet_address': self.server.wallet.address if self.server.wallet else None,
                                'timestamp': datetime.now().isoformat()
                            }
                        elif path == '/blockchain':
                            # Return blockchain info
                            response = {
                                'success': True,
                                'height': len(self.server.blockchain.chain) if self.server.blockchain else 0,
                                'latest_block': self.server.blockchain.chain[-1].to_dict() if self.server.blockchain and self.server.blockchain.chain else None
                            }
                        elif path == '/pending_requests':
                            # Return pending payment requests
                            response = {
                                'success': True,
                                'pending_requests': self.server.pending_payment_requests,
                                'count': len(self.server.pending_payment_requests)
                            }
                        else:
                            response = {
                                'success': False,
                                'error': 'Unknown endpoint',
                                'available_endpoints': ['/status', '/blockchain', '/pending_requests', '/payment_request']
                            }
                        
                        self.wfile.write(json.dumps(response).encode())
                        
                    except Exception as e:
                        error_response = {'success': False, 'error': str(e)}
                        self.wfile.write(json.dumps(error_response).encode())
                
                def do_POST(self):
                    """Handle POST requests including payment requests"""
                    try:
                        content_length = int(self.headers.get('Content-Length', 0))
                        post_data = self.rfile.read(content_length)
                        
                        parsed_path = urllib.parse.urlparse(self.path)
                        path = parsed_path.path
                        
                        # Parse JSON data
                        try:
                            data = json.loads(post_data.decode('utf-8')) if post_data else {}
                        except json.JSONDecodeError:
                            data = {}
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        
                        if path == '/payment_request':
                            # Handle payment request
                            response = self.server.handle_payment_request(data)
                        elif path == '/transaction':
                            # Handle transaction submission
                            response = self.server.handle_transaction_submission(data)
                        elif path == '/sync':
                            # Handle blockchain sync
                            response = self.server.handle_blockchain_sync(data)
                        else:
                            response = {
                                'success': False,
                                'error': f'Unknown POST endpoint: {path}',
                                'available_endpoints': ['/payment_request', '/transaction', '/sync']
                            }
                        
                        self.wfile.write(json.dumps(response).encode())
                        
                    except Exception as e:
                        error_response = {'success': False, 'error': str(e)}
                        self.wfile.write(json.dumps(error_response).encode())
            
            # Create and configure server
            self.server = HTTPServer((self.host, self.port), EnhancedNodeHandler)
            self.server.blockchain = self.blockchain
            self.server.wallet = self.wallet
            self.server.main_wallet = self.main_wallet
            self.server.pending_payment_requests = self.pending_payment_requests
            self.server.handle_payment_request = self.handle_payment_request
            self.server.handle_transaction_submission = self.handle_transaction_submission
            self.server.handle_blockchain_sync = self.handle_blockchain_sync
            
            print(f"[Node] Enhanced PythonCoin node starting on {self.host}:{self.port}")
            
            # Serve requests
            while self.running:
                try:
                    self.server.handle_request()
                except Exception as e:
                    if self.running:
                        print(f"[Node] Request handling error: {e}")
                    break
                    
        except Exception as e:
            print(f"[Node] Enhanced node startup error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.server:
                self.server.server_close()
            print(f"[Node] Enhanced node stopped")
    
    def handle_payment_request(self, data):
        """Handle incoming payment request"""
        try:
            # Validate payment request data
            required_fields = ['from', 'to', 'amount']
            for field in required_fields:
                if field not in data:
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Create payment request
            payment_request = {
                'id': str(uuid.uuid4()),
                'from': data['from'],
                'to': data['to'],
                'amount': float(data['amount']),
                'message': data.get('message', ''),
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            # Add to pending requests
            self.pending_payment_requests.append(payment_request)
            
            print(f"[Node] New payment request: {payment_request['amount']} PYC from {payment_request['from'][:8]}...")
            
            # Notify main wallet if available
            if self.main_wallet and hasattr(self.main_wallet, 'add_transaction_to_queue'):
                self.main_wallet.add_transaction_to_queue(payment_request)
            
            return {
                'success': True,
                'message': 'Payment request received',
                'request_id': payment_request['id'],
                'status': 'pending'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_transaction_submission(self, data):
        """Handle transaction submission"""
        try:
            # Validate transaction data
            if not all(key in data for key in ['to', 'amount']):
                return {'success': False, 'error': 'Missing required transaction fields'}
            
            to_address = data['to']
            amount = float(data['amount'])
            
            # Check if we have a wallet to send from
            if not self.wallet:
                return {'success': False, 'error': 'No wallet available for transaction'}
            
            # Attempt to create and send transaction
            tx = self.wallet.send(to_address, amount)
            
            if tx:
                return {
                    'success': True,
                    'message': 'Transaction submitted successfully',
                    'tx_id': tx.tx_id,
                    'amount': amount,
                    'to': to_address
                }
            else:
                return {'success': False, 'error': 'Failed to create transaction'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_blockchain_sync(self, data):
        """Handle blockchain synchronization request"""
        try:
            if not self.blockchain:
                return {'success': False, 'error': 'No blockchain available'}
            
            # Return current blockchain state
            return {
                'success': True,
                'blockchain_height': len(self.blockchain.chain),
                'latest_hash': self.blockchain.chain[-1].hash if self.blockchain.chain else None,
                'pending_transactions': len(self.blockchain.pending_transactions)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop(self):
        """Stop the enhanced node server"""
        self.running = False
        if self.server:
            self.server.server_close()

def main():
    """Enhanced main application entry point with genesis coordination"""
    app = QApplication(sys.argv)
    app.setApplicationName("PythonCoin P2P Ad Network Wallet (Enhanced)")
    app.setApplicationVersion("2.0")
    
    # Create splash screen
    pixmap = QPixmap(400, 300)
    pixmap.fill(Qt.GlobalColor.white)
    splash = QSplashScreen(pixmap)
    splash.show()
    
    # Update splash with progress
    def update_splash(message):
        splash.showMessage(f"Loading PythonCoin Wallet...\n{message}", 
                          Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        app.processEvents()
    
    try:
        update_splash("Initializing blockchain...")
        
        # Check if user wants to participate in genesis coordination
        if len(sys.argv) > 1 and sys.argv[1] == "--genesis-coord":
            update_splash("Coordinating genesis block with peers...")
            genesis_addresses = run_genesis_coordination()
            
            if genesis_addresses:
                print(f"Genesis coordination complete with {len(genesis_addresses)} participants")
            else:
                print("No peers found for genesis coordination")
        
        update_splash("Creating wallet interface...")
        
        # Create main window
        main_window = UnifiedPythonCoinWallet()
        
        update_splash("Starting P2P discovery...")
        
        # Auto-start P2P network for genesis coordination
        main_window.start_ad_network()
        
        # Auto-start portal server
        try:
            main_window.start_portal_server()
        except Exception as e:
            print(f"Portal server auto-start failed: {e}")
        main_window.start_portal_server()
        # Close splash and show main window
        splash.finish(main_window)
        main_window.show()
        
        # Show initial instructions
        if not main_window.blockchain.genesis_complete:
            QMessageBox.information(
                main_window, 
                "Welcome to PythonCoin!", 
                "🏗️ Genesis Block Coordination\n\n"
                "Your wallet is now discovering peers for initial coin distribution.\n"
                "The genesis block will be created automatically when:\n\n"
                "• Other wallets are found on the network, OR\n"
                "• 30 seconds have passed (single-wallet mode)\n\n"
                "You can start mining once the genesis block is complete!"
            )
        
        # Start the application
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(None, "Startup Error", f"Failed to start application: {str(e)}")
        logger.error(f"Application startup error: {e}")
        traceback.print_exc()
        sys.exit(1)
class SimplePortalServer(QThread):
    """Simplified, reliable portal server for debugging"""
    
    status_update = pyqtSignal(str)
    developer_registered = pyqtSignal(str, str)
    
    def __init__(self, wallet, blockchain, port=8082):
        super().__init__()
        self.wallet = wallet
        self.blockchain = blockchain
        self.port = port
        self.running = False
        self.httpd = None
        self.registered_developers = {}
        
    def run(self):
        """Run the simple server"""
        self.running = True
        self.status_update.emit("🔄 Starting simple HTTP server...")
        
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import json
            
            class SimpleHandler(BaseHTTPRequestHandler):
                def log_message(self, format, *args):
                    # Custom logging to see all requests
                    timestamp = time.strftime("%H:%M:%S", time.localtime())
                    print(f"[{timestamp}] {format % args}")
                
                def do_OPTIONS(self):
                    """Handle CORS preflight requests"""
                    print(f"[{time.strftime('%H:%M:%S')}] OPTIONS request to {self.path}")
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                    self.end_headers()
                
                def do_GET(self):
                    """Handle GET requests"""
                    print(f"[{time.strftime('%H:%M:%S')}] GET request to {self.path}")
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    if self.path == '/test' or self.path == '/':
                        response = {
                            'success': True,
                            'message': 'Simple portal server is working!',
                            'timestamp': time.time(),
                            'path': self.path
                        }
                    else:
                        response = {
                            'success': False,
                            'error': f'Unknown GET path: {self.path}',
                            'available_paths': ['/test', '/', '/register_developer']
                        }
                    
                    self.wfile.write(json.dumps(response).encode())
                
                def do_POST(self):
                    """Handle POST requests with detailed logging"""
                    print(f"[{time.strftime('%H:%M:%S')}] POST request to {self.path}")
                    
                    # Read the request body
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    
                    print(f"[{time.strftime('%H:%M:%S')}] POST body length: {content_length}")
                    print(f"[{time.strftime('%H:%M:%S')}] POST body: {post_data}")
                    print(f"[{time.strftime('%H:%M:%S')}] Headers: {dict(self.headers)}")
                    
                    # Parse JSON data
                    try:
                        data = json.loads(post_data.decode('utf-8')) if post_data else {}
                        print(f"[{time.strftime('%H:%M:%S')}] Parsed JSON: {data}")
                    except Exception as e:
                        print(f"[{time.strftime('%H:%M:%S')}] JSON parse error: {e}")
                        data = {}
                    
                    # Send response
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    if self.path == '/register_developer':
                        # Handle developer registration
                        developer = data.get('developer', data.get('developer_name', data.get('username', '')))
                        address = data.get('pythoncoin_address', data.get('wallet_address', data.get('developer_address', '')))
                        
                        print(f"[{time.strftime('%H:%M:%S')}] Registration attempt: {developer} -> {address}")
                        
                        if developer and address:
                            # Store registration (simple version)
                            server_instance = self.server  # Access the server instance
                            if hasattr(server_instance, 'registered_developers'):
                                server_instance.registered_developers[developer] = address
                            
                            response = {
                                'success': True,
                                'message': 'Developer registered successfully',
                                'developer': developer,
                                'address': address,
                                'timestamp': time.time()
                            }
                            print(f"[{time.strftime('%H:%M:%S')}] ✅ Registration successful")
                        else:
                            response = {
                                'success': False,
                                'error': 'Missing developer name or address',
                                'received_data': data
                            }
                            print(f"[{time.strftime('%H:%M:%S')}] ❌ Registration failed - missing data")
                    else:
                        response = {
                            'success': False,
                            'error': f'Unknown POST path: {self.path}',
                            'received_data': data
                        }
                        print(f"[{time.strftime('%H:%M:%S')}] ❌ Unknown POST path")
                    
                    self.wfile.write(json.dumps(response).encode())
            
            # Create and start server
            print(f"[{time.strftime('%H:%M:%S')}] Creating HTTPServer on 0.0.0.0:{self.port}")
            self.httpd = HTTPServer(('0.0.0.0', self.port), SimpleHandler)  # Listen on all interfaces
            self.httpd.registered_developers = self.registered_developers  # Store reference
            
            print(f"[{time.strftime('%H:%M:%S')}] ✅ Server created successfully")
            self.status_update.emit(f"✅ Simple server started on 0.0.0.0:{self.port}")
            
            # Serve requests
            print(f"[{time.strftime('%H:%M:%S')}] Starting to serve requests...")
            while self.running:
                try:
                    self.httpd.handle_request()
                except Exception as e:
                    if self.running:
                        print(f"[{time.strftime('%H:%M:%S')}] Request handling error: {e}")
                        self.status_update.emit(f"Request error: {str(e)}")
                    break
                    
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Server startup error: {e}")
            import traceback
            traceback.print_exc()
            self.status_update.emit(f"❌ Server startup failed: {str(e)}")
        finally:
            if self.httpd:
                self.httpd.server_close()
            self.status_update.emit("🛑 Simple server stopped")
            print(f"[{time.strftime('%H:%M:%S')}] Server stopped")
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.httpd:
            self.httpd.server_close()
if __name__ == "__main__":
    main()