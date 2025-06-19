<?php
/**
 * PythonCoin Developer Dashboard (Complete PHP Version with Storage Integration)
 * Full-featured developer portal for PythonCoin P2P Ad Network
 * NOW SUPPORTS: ads_storage/active folder with SVG/HTML/JSON ad trios
 * Uses the same 'adnetwrk' database as the Python Qt client
 * VERSION 2.2.0 - Enhanced Storage Integration
 */

session_start();

// Configuration - Enhanced for new ad structure
define('PYTHONCOIN_SERVER_URL', 'http://secupgrade.com:8082');
define('DASHBOARD_VERSION', '2.2.0');
define('REFRESH_INTERVAL', 30);

// Database configuration - Same as Python Qt client
$db_config = [
    'host' => 'localhost',
    'database' => 'adnetwrk',
    'username' => 'root',
    'password' => ''
];

// NEW: Function to scan ads_storage/active folder for ad trios
function scanActiveAdsStorage() {
    // Try multiple possible paths for the ads_storage directory
    $possiblePaths = [
        realpath(dirname(__FILE__) . '/../livepy/pythoncoin/ads_storage/active'),
        realpath(dirname(__FILE__) . '/../../pythoncoin/ads_storage/active'),
        realpath(dirname(__FILE__) . '/ads_storage/active'),
        realpath('./ads_storage/active'),
        realpath('../ads_storage/active'),
        realpath('/livepy/pythoncoin/ads_storage/active'),
        realpath($_SERVER['DOCUMENT_ROOT'] . '/../livepy/pythoncoin/ads_storage/active'),
        realpath($_SERVER['DOCUMENT_ROOT'] . '/livepy/pythoncoin/ads_storage/active')
    ];
    
    $adsPath = null;
    foreach ($possiblePaths as $path) {
        if ($path && is_dir($path)) {
            $adsPath = $path;
            error_log("Found ads storage at: $adsPath");
            break;
        }
    }
    
    if (!$adsPath) {
        error_log("Ads storage path not found. Tried: " . implode(', ', array_filter($possiblePaths)));
        return [];
    }
    
    $ads = [];
    $files = scandir($adsPath);
    
    if (!$files) {
        error_log("Could not scan ads storage directory: $adsPath");
        return [];
    }
    
    // Group files by ad ID
    $adGroups = [];
    foreach ($files as $file) {
        if ($file === '.' || $file === '..') continue;
        
        // Extract ad ID from filename (everything before the last underscore and extension)
        if (preg_match('/^(.+)_(svg|html|meta)\.(svg|html|json)$/', $file, $matches)) {
            $adId = $matches[1];
            $fileType = $matches[2];
            
            if (!isset($adGroups[$adId])) {
                $adGroups[$adId] = [];
            }
            
            $adGroups[$adId][$fileType] = $file;
        }
    }
    
    // Process complete ad trios
    foreach ($adGroups as $adId => $files) {
        if (isset($files['svg']) && isset($files['html']) && isset($files['meta'])) {
            $metaFile = $adsPath . '/' . $files['meta'];
            
            if (file_exists($metaFile)) {
                $metaContent = file_get_contents($metaFile);
                $metadata = json_decode($metaContent, true);
                
                if ($metadata && is_array($metadata)) {
                    // Check if ad is still active and not expired
                    $expiresAt = $metadata['expires_at'] ?? null;
                    $status = $metadata['status'] ?? 'active';
                    
                    if ($status === 'active' && (!$expiresAt || strtotime($expiresAt) > time())) {
                        $ads[] = [
                            'id' => $adId,
                            'ad_id' => $adId,
                            'title' => $metadata['title'] ?? 'Untitled Ad',
                            'description' => $metadata['description'] ?? '',
                            'category' => $metadata['category'] ?? 'general',
                            'payout_amount' => $metadata['payout_rate'] ?? 0.001,
                            'payout' => $metadata['payout_rate'] ?? 0.001,
                            'click_url' => $metadata['click_url'] ?? '',
                            'target_url' => $metadata['click_url'] ?? '',
                            'advertiser_address' => $metadata['advertiser_address'] ?? '',
                            'targeting' => $metadata['targeting'] ?? [],
                            'created_at' => $metadata['created_at'] ?? date('Y-m-d H:i:s'),
                            'expires_at' => $metadata['expires_at'] ?? null,
                            'click_count' => $metadata['click_count'] ?? 0,
                            'impression_count' => $metadata['impression_count'] ?? 0,
                            'files' => [
                                'svg' => $files['svg'],
                                'html' => $files['html'],
                                'meta' => $files['meta']
                            ],
                            'file_path' => $adsPath,
                            'svg_url' => "?ajax=serve_ad_svg&ad_id=" . urlencode($adId),
                            'html_url' => "?ajax=serve_ad_html&ad_id=" . urlencode($adId),
                            'client_id' => 'local_storage',
                            'client_host' => '127.0.0.1',
                            'client_port' => '8082',
                            'source' => 'ads_storage'
                        ];
                    }
                }
            }
        }
    }
    
    error_log("Scanned ads storage: found " . count($ads) . " active ads");
    return $ads;
}

// NEW: Function to serve ad content from storage
function serveAdContent($adId, $contentType = 'svg') {
    // Try multiple possible paths for the ads_storage directory
    $possiblePaths = [
        realpath(dirname(__FILE__) . '/../livepy/pythoncoin/ads_storage/active'),
        realpath(dirname(__FILE__) . '/../../pythoncoin/ads_storage/active'),
        realpath(dirname(__FILE__) . '/ads_storage/active'),
        realpath('./ads_storage/active'),
        realpath('../ads_storage/active'),
        realpath('/livepy/pythoncoin/ads_storage/active'),
        realpath($_SERVER['DOCUMENT_ROOT'] . '/../livepy/pythoncoin/ads_storage/active'),
        realpath($_SERVER['DOCUMENT_ROOT'] . '/livepy/pythoncoin/ads_storage/active')
    ];
    
    $adsPath = null;
    foreach ($possiblePaths as $path) {
        if ($path && is_dir($path)) {
            $adsPath = $path;
            break;
        }
    }
    
    if (!$adsPath) {
        error_log("Could not find ads storage path for serving ad: $adId");
        return null;
    }
    
    $extension = $contentType === 'html' ? 'html' : 'svg';
    $fileName = $adId . '_' . $contentType . '.' . $extension;
    $filePath = $adsPath . '/' . $fileName;
    
    if (file_exists($filePath)) {
        return file_get_contents($filePath);
    }
    
    error_log("Ad file not found: $filePath");
    return null;
}

// Database connection
function getDatabase() {
    global $db_config;
    try {
        $pdo = new PDO(
            "mysql:host={$db_config['host']};dbname={$db_config['database']};charset=utf8mb4",
            $db_config['username'],
            $db_config['password'],
            [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
            ]
        );
        return $pdo;
    } catch (PDOException $e) {
        error_log("Database connection error: " . $e->getMessage());
        return null;
    }
}

// Initialize database tables if they don't exist
function initializeTables() {
    $pdo = getDatabase();
    if (!$pdo) return false;
    
    try {
        // Create developers table if not exists
        $pdo->exec("CREATE TABLE IF NOT EXISTS developers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            pythoncoin_address VARCHAR(100) NOT NULL,
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL,
            total_clicks INT DEFAULT 0,
            total_earned DECIMAL(16,8) DEFAULT 0.00000000,
            is_active BOOLEAN DEFAULT TRUE
        )");
        
        // Create developer_sessions table
        $pdo->exec("CREATE TABLE IF NOT EXISTS developer_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            developer_id INT,
            session_token VARCHAR(255),
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(45),
            user_agent TEXT,
            FOREIGN KEY (developer_id) REFERENCES developers(id)
        )");
        
        // Create ad_clicks table
        $pdo->exec("CREATE TABLE IF NOT EXISTS ad_clicks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            developer_id INT,
            ad_id VARCHAR(100),
            client_id VARCHAR(100),
            zone VARCHAR(100),
            payout_amount DECIMAL(16,8),
            click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(45),
            user_agent TEXT,
            processed BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (developer_id) REFERENCES developers(id)
        )");
        
        // Create developer_embeds table
        $pdo->exec("CREATE TABLE IF NOT EXISTS developer_embeds (
            id INT AUTO_INCREMENT PRIMARY KEY,
            developer_id INT,
            embed_name VARCHAR(100),
            zone_id VARCHAR(100),
            width VARCHAR(20),
            height VARCHAR(20),
            rotation_interval INT DEFAULT 30,
            selected_clients JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            total_impressions INT DEFAULT 0,
            total_clicks INT DEFAULT 0,
            FOREIGN KEY (developer_id) REFERENCES developers(id)
        )");
        
        // Enhanced ads_cache table to support the new structure
        $pdo->exec("CREATE TABLE IF NOT EXISTS ads_cache (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ad_id VARCHAR(100) UNIQUE,
            client_id VARCHAR(100),
            title VARCHAR(255),
            description TEXT,
            category VARCHAR(100),
            payout_amount DECIMAL(16,8),
            svg_url TEXT,
            html_url TEXT,
            target_url TEXT,
            advertiser_address VARCHAR(100),
            file_path TEXT,
            has_html_wrapper BOOLEAN DEFAULT FALSE,
            targeting_data JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            click_count INT DEFAULT 0,
            impression_count INT DEFAULT 0,
            INDEX(client_id),
            INDEX(category),
            INDEX(expires_at)
        )");
        
        // Create p2p_clients table if it doesn't exist (used by scan_network fallback)
        $pdo->exec("CREATE TABLE IF NOT EXISTS p2p_clients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            client_id VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(255),
            host VARCHAR(255),
            port VARCHAR(10),
            status VARCHAR(50),
            ad_count INT DEFAULT 0,
            peers INT DEFAULT 0,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )");

        return true;
    } catch (PDOException $e) {
        error_log("Database initialization error: " . $e->getMessage());
        return false;
    }
}

// Initialize tables
initializeTables();

// Helper Functions
class PythonCoinAPI {
    private $serverUrl;
    
    public function __construct($serverUrl = PYTHONCOIN_SERVER_URL) {
        $this->serverUrl = $serverUrl;
    }
    
    public function makeRequest($endpoint, $data = null, $method = 'GET') {
        $url = $this->serverUrl . $endpoint;
        $ch = curl_init();
        
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'User-Agent: PythonCoin-Dashboard/2.2.0'
        ]);
        
        if ($method === 'POST' && $data) {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode === 200 && $response) {
            return json_decode($response, true);
        }
        
        return ['success' => false, 'error' => 'Connection failed', 'http_code' => $httpCode];
    }
    
    // All API methods
    public function getClientInfo() { return $this->makeRequest('/client_info'); }
    public function discoverClients() { return $this->makeRequest('/discover_clients'); }
    public function getActiveClients() { return $this->makeRequest('/active_clients'); }
    public function getStats() { return $this->makeRequest('/stats'); }
    public function getNotifications() { return $this->makeRequest('/notifications'); }
    public function getAds() { return $this->makeRequest('/ads'); }
    public function getAdSvg($adId) { return $this->makeRequest('/ad/' . urlencode($adId) . '.svg'); }
    public function getAdsForDeveloper($developerAddress) { 
        return $this->makeRequest('/ads?developer=' . urlencode($developerAddress)); 
    }
    
    public function selectClient($developerAddress, $clientId, $categories = []) {
        return $this->makeRequest('/select_client', [
            'developer_address' => $developerAddress,
            'client_id' => $clientId,
            'categories' => $categories
        ], 'POST');
    }
    
    public function generateCustomJS($developerAddress, $preferences = []) {
        return $this->makeRequest('/generate_custom_js', [
            'developer_address' => $developerAddress,
            'client_preferences' => $preferences
        ], 'POST');
    }
    
    public function registerDeveloper($developer, $address) {
        return $this->makeRequest('/register_developer', [
            'developer' => $developer,
            'pythoncoin_address' => $address
        ], 'POST');
    }
    
    public function recordClick($adId, $clientId, $developerAddress, $zone) {
        return $this->makeRequest('/record_click', [
            'ad_id' => $adId,
            'client_id' => $clientId,
            'developer_address' => $developerAddress,
            'zone' => $zone
        ], 'POST');
    }
}

// Database functions (keep existing ones)
function getDeveloperByUsername($username) {
    $pdo = getDatabase();
    if (!$pdo) return null;
    
    $stmt = $pdo->prepare("SELECT * FROM developers WHERE username = ?");
    $stmt->execute([$username]);
    return $stmt->fetch();
}

function createDeveloper($username, $password, $pythoncoinAddress, $email = null) {
    $pdo = getDatabase();
    if (!$pdo) return false;
    
    $passwordHash = password_hash($password, PASSWORD_DEFAULT);
    
    try {
        $stmt = $pdo->prepare("INSERT INTO developers (username, password_hash, pythoncoin_address, email) VALUES (?, ?, ?, ?)");
        return $stmt->execute([$username, $passwordHash, $pythoncoinAddress, $email]);
    } catch (PDOException $e) {
        error_log("Developer creation error: " . $e->getMessage());
        return false;
    }
}

function updateDeveloperLogin($developerId) {
    $pdo = getDatabase();
    if (!$pdo) return false;
    
    $stmt = $pdo->prepare("UPDATE developers SET last_login = CURRENT_TIMESTAMP WHERE id = ?");
    return $stmt->execute([$developerId]);
}

function getDeveloperStats($developerId) {
    $pdo = getDatabase();
    if (!$pdo) return ['clicks' => 0, 'earned' => 0, 'embeds' => 0];
    
    try {
        $stmt = $pdo->prepare("
            SELECT 
                COALESCE(SUM(total_clicks), 0) as total_clicks,
                COALESCE(SUM(total_earned), 0) as total_earned,
                (SELECT COUNT(*) FROM developer_embeds WHERE developer_id = ? AND is_active = 1) as active_embeds
            FROM developers WHERE id = ?
        ");
        $stmt->execute([$developerId, $developerId]);
        return $stmt->fetch() ?: ['total_clicks' => 0, 'total_earned' => 0, 'active_embeds' => 0];
    } catch (PDOException $e) {
        error_log("Get developer stats error: " . $e->getMessage());
        return ['total_clicks' => 0, 'total_earned' => 0, 'active_embeds' => 0];
    }
}

function recordAdClick($developerId, $adId, $clientId, $zone, $payoutAmount) {
    $pdo = getDatabase();
    if (!$pdo) return false;
    
    try {
        $stmt = $pdo->prepare("
            INSERT INTO ad_clicks (developer_id, ad_id, client_id, zone, payout_amount, ip_address, user_agent) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ");
        return $stmt->execute([
            $developerId, $adId, $clientId, $zone, $payoutAmount,
            $_SERVER['REMOTE_ADDR'] ?? '', $_SERVER['HTTP_USER_AGENT'] ?? ''
        ]);
    } catch (PDOException $e) {
        error_log("Record ad click error: " . $e->getMessage());
        return false;
    }
}

function cacheAdsFromClient($clientId, $ads) {
    $pdo = getDatabase();
    if (!$pdo) return false;
    
    try {
        // Clear old ads from this client
        $stmt = $pdo->prepare("DELETE FROM ads_cache WHERE client_id = ?");
        $stmt->execute([$clientId]);
        
        // Insert new ads
        foreach ($ads as $ad) {
            $stmt = $pdo->prepare("
                INSERT INTO ads_cache (ad_id, client_id, title, description, category, payout_amount, svg_url, target_url, expires_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, DATE_ADD(NOW(), INTERVAL 1 HOUR))
            ");
            $stmt->execute([
                $ad['id'] ?? uniqid(),
                $clientId,
                $ad['title'] ?? 'Untitled Ad',
                $ad['description'] ?? '',
                $ad['category'] ?? 'general',
                $ad['payout'] ?? ($ad['payout_amount'] ?? 0.001), // Use payout_amount if payout is missing
                $ad['svg_url'] ?? '',
                $ad['target_url'] ?? ''
            ]);
        }
        return true;
    } catch (PDOException $e) {
        error_log("Cache ads error: " . $e->getMessage());
        return false;
    }
}

function getCachedAds($limit = 50) {
    $pdo = getDatabase();
    if (!$pdo) return [];
    
    try {
        $stmt = $pdo->prepare("
            SELECT * FROM ads_cache 
            WHERE is_active = 1 AND expires_at > NOW() 
            ORDER BY created_at DESC 
            LIMIT ?
        ");
        $stmt->execute([$limit]);
        return $stmt->fetchAll();
    } catch (PDOException $e) {
        error_log("Get cached ads error: " . $e->getMessage());
        return [];
    }
}

// Enhanced function that combines storage ads with network ads
function getEnhancedNetworkSampleAds() {
    $baseProxyUrl = '?ajax=proxy_svg&client_host=127.0.0.1&client_port=8082&ad_id=';
    return [
        [
            'id' => 'network_ad_001',
            'ad_id' => 'network_ad_001',
            'client_id' => 'pyc_client_001',
            'title' => 'PythonCoin Wallet Pro',
            'description' => 'Advanced cryptocurrency wallet with P2P advertising features',
            'category' => 'cryptocurrency',
            'payout' => 0.005,
            'payout_amount' => 0.005,
            'svg_url' => $baseProxyUrl . 'network_ad_001',
            'target_url' => 'https://pythoncoin.org',
            'created_at' => date('Y-m-d H:i:s'),
            'client_host' => '127.0.0.1',
            'client_port' => '8082',
            'source' => 'network_sample'
        ],
        [
            'id' => 'network_ad_002',
            'ad_id' => 'network_ad_002',
            'client_id' => 'pyc_client_001',
            'title' => 'P2P Ad Network Integration',
            'description' => 'Learn how to integrate P2P advertising into your applications',
            'category' => 'education',
            'payout' => 0.003,
            'payout_amount' => 0.003,
            'svg_url' => $baseProxyUrl . 'network_ad_002',
            'target_url' => 'https://docs.pythoncoin.org',
            'created_at' => date('Y-m-d H:i:s'),
            'client_host' => '127.0.0.1',
            'client_port' => '8082',
            'source' => 'network_sample'
        ],
        [
            'id' => 'network_ad_003',
            'ad_id' => 'network_ad_003',
            'client_id' => 'pyc_client_001',
            'title' => 'Decentralized Advertising Platform',
            'description' => 'Next-generation advertising platform built on blockchain technology',
            'category' => 'technology',
            'payout' => 0.002,
            'payout_amount' => 0.002,
            'svg_url' => $baseProxyUrl . 'network_ad_003',
            'target_url' => 'https://pythoncoin.org/advertising',
            'created_at' => date('Y-m-d H:i:s'),
            'client_host' => '127.0.0.1',
            'client_port' => '8082',
            'source' => 'network_sample'
        ]
    ];
}

function getAdsFromSelectedClients($selectedClientIds = []) {
    $allAds = [];
    
    // Always include storage ads first
    $storageAds = scanActiveAdsStorage();
    $allAds = array_merge($allAds, $storageAds);
    
    if (empty($selectedClientIds)) {
        // Fallback to sample ads if no clients selected
        $sampleAds = getEnhancedNetworkSampleAds();
        return array_merge($allAds, $sampleAds);
    }
    
    foreach ($selectedClientIds as $clientData) {
        $host = $clientData['host'] ?? '127.0.0.1';
        $port = $clientData['port'] ?? '8082';
        $clientId = $clientData['client_id'] ?? 'unknown';
        
        // Try to get ads from this client
        $adsUrl = "http://{$host}:{$port}/ads";
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $adsUrl);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 3);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Accept: application/json']);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode === 200 && $response) {
            $decoded = json_decode($response, true);
            if ($decoded && isset($decoded['ads']) && is_array($decoded['ads'])) {
                foreach ($decoded['ads'] as $ad) {
                    $ad['client_host'] = $host;
                    $ad['client_port'] = $port;
                    $ad['source_client'] = $clientId;
                    $ad['svg_url'] = "?ajax=proxy_svg&client_host={$host}&client_port={$port}&ad_id=" . urlencode($ad['id'] ?? uniqid('ad_'));
                    $allAds[] = $ad;
                }
            }
        }
    }
    
    // If no network ads from real clients, add sample ads
    if (count($allAds) === count($storageAds)) {
        $sampleAds = getEnhancedNetworkSampleAds();
        $allAds = array_merge($allAds, $sampleAds);
    }
    
    return $allAds;
}

// HTTP Response Parser - Auto-added by Master Patcher
function parseHttpResponse($response) {
    if (strpos($response, "HTTP/") === 0) {
        $parts = explode("\r\n\r\n", $response, 2);
        if (count($parts) >= 2) {
            $headers = $parts[0];
            $body = $parts[1];
            preg_match('/HTTP\/\d\.\d\s+(\d+)/', $headers, $matches);
            $statusCode = isset($matches[1]) ? intval($matches[1]) : 500;
            return [
                'status_code' => $statusCode,
                'headers' => $headers,
                'body' => $body,
                'success' => $statusCode >= 200 && $statusCode < 300
            ];
        }
    }
    return [
        'status_code' => 200,
        'headers' => '',
        'body' => $response,
        'success' => true
    ];
}

// ENHANCED HELPER FUNCTIONS - Auto-injected by PythonCoin Patcher
function discoverClientEndpoints($host, $port) {
    $endpointsToTest = ['/', '/status', '/info', '/client_info', '/ads', '/register', '/register_js', '/register_developer', '/register_client'];
    $workingEndpoints = [];
    $clientBaseUrl = "http://{$host}:{$port}";
    
    foreach ($endpointsToTest as $endpoint) {
        $url = $clientBaseUrl . $endpoint;
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 1);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 1);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode === 200 && $response) {
            $workingEndpoints[] = [
                'endpoint' => $endpoint,
                'http_code' => $httpCode,
                'is_json' => json_decode($response, true) !== null
            ];
        }
    }
    
    return [
        'client_url' => $clientBaseUrl,
        'working_endpoints' => $workingEndpoints,
        'total_working' => count($workingEndpoints)
    ];
}

function generateFallbackSVG($adId, $message = 'PythonCoin Ad') {
    $cleanAdId = htmlspecialchars($adId);
    $cleanMessage = htmlspecialchars($message);
    
    return '<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#0066cc;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#004499;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect width="100%" height="100%" fill="url(#grad1)" rx="10"/>
    <text x="200" y="100" font-family="Arial, sans-serif" font-size="28" fill="white" text-anchor="middle" font-weight="bold">🌐 PythonCoin</text>
    <text x="200" y="130" font-family="Arial, sans-serif" font-size="18" fill="white" text-anchor="middle">P2P Advertising Network</text>
    <text x="200" y="160" font-family="Arial, sans-serif" font-size="14" fill="#ccddff" text-anchor="middle">' . $cleanMessage . '</text>
    <text x="200" y="190" font-family="Arial, sans-serif" font-size="12" fill="#ccddff" text-anchor="middle">Ad ID: ' . $cleanAdId . '</text>
    <text x="200" y="220" font-family="Arial, sans-serif" font-size="10" fill="rgba(255,255,255,0.8)" text-anchor="middle">Fallback Mode - Check PyQt Client Connection</text>
    <rect x="10" y="10" width="380" height="280" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2" rx="8"/>
    <circle cx="50" cy="50" r="8" fill="rgba(255,255,255,0.6)">
        <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite"/>
    </circle>
</svg>';
}

// Initialize API
$api = new PythonCoinAPI();

// Enhanced AJAX handling with new storage endpoints
if (isset($_GET['ajax'])) {
    // Default to JSON content type for AJAX responses, change if needed
    header('Content-Type: application/json');
    
    try {
        switch ($_GET['ajax']) {
            case 'serve_ad_svg':
                header('Content-Type: image/svg+xml');
                $adId = $_GET['ad_id'] ?? '';
                $svgContent = serveAdContent($adId, 'svg');
                
                if ($svgContent) {
                    echo $svgContent;
                } else {
                    echo generateFallbackSVG($adId, 'Ad Not Found in Storage');
                }
                exit;
                
            case 'serve_ad_html':
                header('Content-Type: text/html');
                $adId = $_GET['ad_id'] ?? '';
                $htmlContent = serveAdContent($adId, 'html');
                
                if ($htmlContent) {
                    echo $htmlContent;
                } else {
                    echo '<div style="text-align:center;padding:20px;color:#666;">Ad HTML not found for ID: ' . htmlspecialchars($adId) . '</div>';
                }
                exit;
                
            case 'scan_storage_ads':
                $storageAds = scanActiveAdsStorage();
                echo json_encode([
                    'success' => true,
                    'ads' => $storageAds,
                    'count' => count($storageAds),
                    'source' => 'ads_storage'
                ]);
                break;
                
            case 'discover_clients':
                $result = $api->discoverClients();
                if (!$result || !isset($result['success']) || !$result['success']) {
                    // Fallback to database clients if API is unavailable
                    $pdo = getDatabase();
                    if ($pdo) {
                        $stmt = $pdo->query("SELECT * FROM p2p_clients WHERE status = 'online' ORDER BY last_seen DESC");
                        $clients = $stmt->fetchAll();
                        $result = ['success' => true, 'clients' => $clients];
                    } else {
                        $result = ['success' => false, 'clients' => []];
                    }
                }
                echo json_encode($result);
                break;
                
            case 'select_client':
                $result = $api->selectClient(
                    $_POST['developer_address'] ?? '',
                    $_POST['client_id'] ?? '',
                    $_POST['categories'] ?? []
                );
                echo json_encode($result);
                break;
                
            case 'generate_custom_js':
                $result = $api->generateCustomJS(
                    $_POST['developer_address'] ?? '',
                    $_POST['preferences'] ?? []
                );
                echo json_encode($result);
                break;
                
            case 'register_developer':
                $result = $api->registerDeveloper(
                    $_POST['developer'] ?? '',
                    $_POST['address'] ?? ''
                );
                echo json_encode($result);
                break;
                
            case 'get_stats':
                $result = $api->getStats();
                if (!$result || !isset($result['success']) || !$result['success']) {
                    if (isset($_SESSION['developer'])) {
                        // Fallback to database stats
                        $developer = getDeveloperByUsername($_SESSION['developer']['username']);
                        if ($developer) {
                            $stats = getDeveloperStats($developer['id']);
                            $result = [
                                'success' => true,
                                'stats' => [
                                    'total_developers' => 1,
                                    'total_clicks' => $stats['total_clicks'],
                                    'total_payments' => $stats['total_earned'],
                                    'active_embeds' => $stats['active_embeds'],
                                    'server_status' => 'online'
                                ]
                            ];
                        } else {
                            $result = ['success' => false, 'error' => 'Developer not found'];
                        }
                    } else {
                        $result = ['success' => false, 'error' => 'Not logged in'];
                    }
                }
                echo json_encode($result);
                break;
                
            case 'get_notifications':
                echo json_encode($api->getNotifications());
                break;
                
            case 'get_ads':
                // Enhanced ads loading with storage integration
                $result = ['success' => false, 'ads' => []];
                
                if (isset($_SESSION['developer'])) {
                    $developer = getDeveloperByUsername($_SESSION['developer']['username']);
                    if ($developer) {
                        // Get ads from storage first
                        $storageAds = scanActiveAdsStorage();
                        
                        // Try to get ads from PyQt client
                        $apiResult = $api->getAdsForDeveloper($developer['pythoncoin_address']);
                        
                        if ($apiResult && isset($apiResult['success']) && $apiResult['success'] && isset($apiResult['ads'])) {
                            $allAds = array_merge($storageAds, $apiResult['ads']);
                            // Cache the network ads
                            if (!empty($apiResult['ads'])) {
                                foreach($apiResult['ads'] as &$ad_item) {
                                    $ad_item['client_host'] = $ad_item['client_host'] ?? '127.0.0.1';
                                    $ad_item['client_port'] = $ad_item['client_port'] ?? '8082';
                                }
                                cacheAdsFromClient('pyc_client_001', $apiResult['ads']);
                            }
                        } else {
                            // Fallback to cached ads
                            $cachedAds = getCachedAds();
                            if (!empty($cachedAds)) {
                                $allAds = array_merge($storageAds, $cachedAds);
                            } else {
                                // Use enhanced network sample ads as fallback
                                $sampleAds = getEnhancedNetworkSampleAds(); 
                                $allAds = array_merge($storageAds, $sampleAds);
                            }
                        }
                        
                        $result = [
                            'success' => true, 
                            'ads' => $allAds, 
                            'storage_count' => count($storageAds),
                            'total_count' => count($allAds),
                            'source' => 'combined'
                        ];
                    } else {
                        $result = ['success' => false, 'error' => 'Developer not found'];
                    }
                } else {
                    $result = ['success' => false, 'error' => 'Not logged in'];
                }
                
                echo json_encode($result);
                break;
                
            case 'test_connection':
                $result = $api->getClientInfo();
                echo json_encode($result);
                break;
                
            case 'heartbeat':
                if (isset($_SESSION['developer'])) {
                    $developer = getDeveloperByUsername($_SESSION['developer']['username']);
                    if ($developer) {
                        updateDeveloperLogin($developer['id']);
                    }
                }
                echo json_encode(['success' => true, 'timestamp' => time()]);
                break;
                
            case 'scan_network':
                // Enhanced network scanning
                $clients = [];
                $pdo = getDatabase();
                
                if ($pdo) {
                    $stmt = $pdo->query("SELECT * FROM p2p_clients WHERE last_seen > DATE_SUB(NOW(), INTERVAL 5 MINUTE) ORDER BY last_seen DESC");
                    $dbClients = $stmt->fetchAll();
                    
                    foreach ($dbClients as $client) {
                        $clients[] = [
                            'client_id' => $client['client_id'],
                            'name' => $client['name'],
                            'host' => $client['host'],
                            'port' => $client['port'],
                            'status' => $client['status'],
                            'ad_count' => $client['ad_count'] ?? 0,
                            'peers' => 0
                        ];
                    }
                }
                
                // If no clients in database, return empty result
                if (empty($clients)) {
                    $clients = [];
                }
                
                echo json_encode(['success' => true, 'clients' => $clients]);
                break;
                
            case 'record_click':
                if (isset($_SESSION['developer'])) {
                    $developer = getDeveloperByUsername($_SESSION['developer']['username']);
                    if ($developer) {
                        $adId = $_POST['ad_id'] ?? '';
                        $clientId = $_POST['client_id'] ?? '';
                        $zone = $_POST['zone'] ?? '';
                        $payoutAmount = floatval($_POST['payout_amount'] ?? 0.001);
                        
                        // Record click in local database
                        $success = recordAdClick($developer['id'], $adId, $clientId, $zone, $payoutAmount);
                        
                        if ($success) {
                            // Update developer totals
                            $pdo = getDatabase();
                            $stmt = $pdo->prepare("UPDATE developers SET total_clicks = total_clicks + 1, total_earned = total_earned + ? WHERE id = ?");
                            $stmt->execute([$payoutAmount, $developer['id']]);
                            
                            // Also try to record on PyQt client
                            $api->recordClick($adId, $clientId, $developer['pythoncoin_address'], $zone);
                        }
                        
                        echo json_encode(['success' => $success, 'amount' => $payoutAmount]);
                    } else {
                        echo json_encode(['success' => false, 'error' => 'Developer not found']);
                    }
                } else {
                    echo json_encode(['success' => false, 'error' => 'Not logged in']);
                }
                break;
                
            case 'proxy_register':
                $clientHost = $_POST['client_host'] ?? '';
                $clientPort = $_POST['client_port'] ?? '8082';
                $developerAddress = $_POST['developer_address'] ?? '';
                $developerName = $_POST['developer_name'] ?? '';
                $zone = $_POST['zone'] ?? '';
                
                if ($clientHost && $developerAddress) {
                    // First discover what endpoints work
                    $discoveryResult = discoverClientEndpoints($clientHost, $clientPort);
                    
                    if (empty($discoveryResult['working_endpoints'])) {
                        echo json_encode([
                            'success' => false, 
                            'error' => 'No working endpoints found on client',
                            'client_url' => "http://{$clientHost}:{$clientPort}",
                            'discovery' => $discoveryResult
                        ]);
                        break;
                    }
                    
                    // Try registration endpoints that were discovered to work
                    $registrationEndpoints = ['/register_developer', '/register', '/register_js', '/register_client'];
                    $workingEndpoints = array_column($discoveryResult['working_endpoints'], 'endpoint');
                    
                    $success = false;
                    $attempts = [];
                    
                    foreach ($registrationEndpoints as $endpoint) {
                        if (in_array($endpoint, $workingEndpoints)) {
                            $registerUrl = "http://{$clientHost}:{$clientPort}{$endpoint}";
                            $postData = json_encode([
                                'developer_address' => $developerAddress,
                                'developer_name' => $developerName,
                                'zone' => $zone,
                                'host' => $_SERVER['HTTP_HOST'] ?? '',
                                'timestamp' => time()
                            ]);
                            
                            $ch = curl_init();
                            curl_setopt($ch, CURLOPT_URL, $registerUrl);
                            curl_setopt($ch, CURLOPT_POST, true);
                            curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
                            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                            curl_setopt($ch, CURLOPT_TIMEOUT, 3);
                            curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
                            
                            $response = curl_exec($ch);
                            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
                            curl_close($ch);
                            
                            $attempts[] = ['endpoint' => $endpoint, 'http_code' => $httpCode, 'response' => $response];
                            
                            if ($httpCode === 200 && $response) {
                                $decoded = json_decode($response, true);
                                if ($decoded && isset($decoded['success']) && $decoded['success']) {
                                    echo json_encode(['success' => true, 'endpoint' => $endpoint, 'response' => $decoded]);
                                    $success = true;
                                    break;
                                }
                            }
                        }
                    }
                    
                    if (!$success) {
                        echo json_encode([
                            'success' => false, 
                            'error' => 'Registration failed on all attempted endpoints', 
                            'working_endpoints' => $workingEndpoints,
                            'attempts' => $attempts
                        ]);
                    }
                } else {
                    echo json_encode(['success' => false, 'error' => 'Missing required parameters']);
                }
                break;

            case 'proxy_ads': 
                $clientHost = $_POST['client_host'] ?? '';
                $clientPort = $_POST['client_port'] ?? '8082';
                $zone = $_POST['zone'] ?? '';
                $developerAddress = $_POST['developer_address'] ?? '';
                
                if ($clientHost) {
                    $adsUrl = "http://{$clientHost}:{$clientPort}/ads";
                    if ($zone || $developerAddress) {
                        $params = [];
                        if ($zone) $params['zone'] = $zone;
                        if ($developerAddress) $params['developer'] = $developerAddress;
                        $adsUrl .= '?' . http_build_query($params);
                    }
                    
                    $ch = curl_init();
                    curl_setopt($ch, CURLOPT_URL, $adsUrl);
                    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
                    curl_setopt($ch, CURLOPT_HTTPHEADER, [
                        'X-Developer-Address: ' . $developerAddress,
                        'X-Zone: ' . $zone,
                        'Accept: application/json'
                    ]);
                    
                    $response = curl_exec($ch);
                    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
                    curl_close($ch);
                    
                    if ($httpCode === 200 && $response) {
                        $decoded = json_decode($response, true);
                        if ($decoded !== null) {
                            echo json_encode($decoded);
                        } else {
                            echo json_encode([
                                'success' => false,
                                'error' => 'Client returned non-JSON response',
                                'fallback' => 'using_sample_ads',
                                'raw_response_snippet' => substr($response, 0, 200) 
                            ]);
                        }
                    } else {
                        echo json_encode([
                            'success' => false, 
                            'error' => 'HTTP request failed', 
                            'http_code' => $httpCode,
                            'fallback' => 'using_sample_ads'
                        ]);
                    }
                } else {
                    echo json_encode(['success' => false, 'error' => 'Missing client host']);
                }
                break;

            case 'proxy_svg':
                // Set content type for SVG directly here, as it's a proxy for an SVG file
                header('Content-Type: image/svg+xml');

                $clientHost = $_REQUEST['client_host'] ?? ''; 
                $clientPort = $_REQUEST['client_port'] ?? '8082';
                $adId = $_REQUEST['ad_id'] ?? '';
                
                if ($clientHost && $adId) {
                    $svgUrls = [
                        "http://{$clientHost}:{$clientPort}/ad/{$adId}.svg",
                        "http://{$clientHost}:{$clientPort}/svg/{$adId}",
                        "http://{$clientHost}:{$clientPort}/ads/{$adId}/svg"
                    ];
                    
                    $svgContent = null;
                    
                    foreach ($svgUrls as $svgUrl) {
                        $ch = curl_init();
                        curl_setopt($ch, CURLOPT_URL, $svgUrl);
                        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                        curl_setopt($ch, CURLOPT_TIMEOUT, 3);
                        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Accept: image/svg+xml,text/plain']);
                        
                        $response = curl_exec($ch);
                        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
                        curl_close($ch);
                        
                        // Check for SVG content in response
                        if ($httpCode === 200 && $response && (strpos($response, '<svg') !== false || strpos($response, '<?xml') !== false)) {
                            $svgContent = $response;
                            break;
                        }
                    }
                    
                    if ($svgContent) {
                        echo $svgContent;
                    } else {
                        echo generateFallbackSVG($adId ?? 'unknown', 'Client SVG Not Available');
                    }
                } else {
                    echo generateFallbackSVG($adId ?? 'unknown', 'Missing Parameters');
                }
                exit; 
            
            case 'record_view':
                if (isset($_SESSION['developer'])) {
                    $developer = getDeveloperByUsername($_SESSION['developer']['username']);
                    if ($developer) {
                        $adId = $_POST['ad_id'] ?? '';
                        $clientId = $_POST['client_id'] ?? '';
                        $zone = $_POST['zone'] ?? '';
                        $developerAddress = $_POST['developer_address'] ?? '';
                        
                        // Record view for analytics (no payout for views)
                        $pdo = getDatabase();
                        if ($pdo) {
                            $stmt = $pdo->prepare("
                                INSERT INTO ad_clicks (developer_id, ad_id, client_id, zone, payout_amount, ip_address, user_agent) 
                                VALUES (?, ?, ?, ?, 0, ?, ?)
                            ");
                            $stmt->execute([
                                $developer['id'], 
                                $adId . '_view', 
                                $clientId, 
                                $zone, 
                                $_SERVER['REMOTE_ADDR'] ?? '', 
                                $_SERVER['HTTP_USER_AGENT'] ?? ''
                            ]);
                        }
                        
                        echo json_encode(['success' => true, 'message' => 'View recorded']);
                    } else {
                        echo json_encode(['success' => false, 'error' => 'Developer not found']);
                    }
                } else {
                    echo json_encode(['success' => false, 'error' => 'Not logged in']);
                }
                break;
                
            case 'discover_endpoints':
                $clientHost = $_POST['client_host'] ?? '127.0.0.1';
                $clientPort = $_POST['client_port'] ?? '8082';
                
                $discoveryResult = discoverClientEndpoints($clientHost, $clientPort);
                echo json_encode([
                    'success' => true,
                    'client_url' => "http://{$clientHost}:{$clientPort}",
                    'working_endpoints' => $discoveryResult['working_endpoints'],
                    'total_working' => $discoveryResult['total_working']
                ]);
                break;
                
            case 'get_ads_from_selected':
                $selectedClients = json_decode($_POST['selected_clients'] ?? '[]', true);
                $ads = getAdsFromSelectedClients($selectedClients);
                
                echo json_encode([
                    'success' => true,
                    'ads' => $ads,
                    'source' => 'selected_clients',
                    'client_count' => count($selectedClients),
                    'ad_count' => count($ads)
                ]);
                break;
        
            default:
                echo json_encode(['success' => false, 'error' => 'Unknown action']);
        }
    } catch (Exception $e) {
        error_log("AJAX error: " . $e->getMessage());
        echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    exit;
}

// Handle authentication
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {
    switch ($_POST['action']) {
        case 'login':
            $username = trim($_POST['username'] ?? '');
            $password = $_POST['password'] ?? '';
            $pythoncoinAddress = trim($_POST['pythoncoin_address'] ?? '');
            
            if ($username && $password && $pythoncoinAddress) {
                $developer = getDeveloperByUsername($username);
                
                if ($developer && password_verify($password, $developer['password_hash'])) {
                    // Update PythonCoin address if different
                    if ($developer['pythoncoin_address'] !== $pythoncoinAddress) {
                        $pdo = getDatabase();
                        if ($pdo) {
                            $stmt = $pdo->prepare("UPDATE developers SET pythoncoin_address = ? WHERE id = ?");
                            $stmt->execute([$pythoncoinAddress, $developer['id']]);
                            $developer['pythoncoin_address'] = $pythoncoinAddress;
                        }
                    }
                    
                    $_SESSION['developer'] = [
                        'id' => $developer['id'],
                        'username' => $developer['username'],
                        'pythoncoin_address' => $developer['pythoncoin_address'],
                        'login_time' => time()
                    ];
                    
                    updateDeveloperLogin($developer['id']);
                    // Attempt to register with PyQt client via proxy on login
                    $api->registerDeveloper($username, $pythoncoinAddress); 
                    
                    header('Content-Type: application/json');
                    echo json_encode(['success' => true, 'message' => 'Login successful']);
                    exit;
                } else {
                    header('Content-Type: application/json');
                    echo json_encode(['success' => false, 'message' => 'Invalid credentials']);
                    exit;
                }
            }
            break;
            
        case 'register':
            $username = trim($_POST['username'] ?? '');
            $password = $_POST['password'] ?? '';
            $confirmPassword = $_POST['confirm_password'] ?? '';
            $pythoncoinAddress = trim($_POST['pythoncoin_address'] ?? '');
            $email = trim($_POST['email'] ?? '');
            
            if ($username && $password && $password === $confirmPassword && $pythoncoinAddress) {
                if (getDeveloperByUsername($username)) {
                    header('Content-Type: application/json');
                    echo json_encode(['success' => false, 'message' => 'Username already exists']);
                    exit;
                }
                
                if (createDeveloper($username, $password, $pythoncoinAddress, $email)) {
                    $developer = getDeveloperByUsername($username);
                    $_SESSION['developer'] = [
                        'id' => $developer['id'],
                        'username' => $developer['username'],
                        'pythoncoin_address' => $developer['pythoncoin_address'],
                        'login_time' => time()
                    ];
                    // Attempt to register with PyQt client via proxy on registration
                    $api->registerDeveloper($username, $pythoncoinAddress);
                    
                    header('Content-Type: application/json');
                    echo json_encode(['success' => true, 'message' => 'Registration successful']);
                    exit;
                } else {
                    header('Content-Type: application/json');
                    echo json_encode(['success' => false, 'message' => 'Registration failed']);
                    exit;
                }
            } else {
                header('Content-Type: application/json');
                echo json_encode(['success' => false, 'message' => 'Invalid registration data. Passwords might not match or fields are missing.']);
                exit;
            }
            break;
            
        case 'logout':
            session_destroy();
            header('Location: ' . $_SERVER['PHP_SELF']);
            exit;
    }
}

// Check if user is logged in
$isLoggedIn = isset($_SESSION['developer']);
$currentUser = $_SESSION['developer'] ?? null;

// Get current data if logged in
$clientInfo = null;
$stats = null;
$notifications = null;
$ads = null;
$developerStats = null;

if ($isLoggedIn) {
    $clientInfo = $api->getClientInfo();
    $stats = $api->getStats();
    $notifications = $api->getNotifications();
    
    // Try to get ads from storage first, then network
    $storageAds = scanActiveAdsStorage();
    $networkAds = $api->getAdsForDeveloper($currentUser['pythoncoin_address']);
    
    if ($networkAds && isset($networkAds['success']) && $networkAds['success'] && isset($networkAds['ads'])) {
        $allAds = array_merge($storageAds, $networkAds['ads']);
    } else {
        $cachedAds = getCachedAds();
        if (!empty($cachedAds)) {
            $allAds = array_merge($storageAds, $cachedAds);
        } else {
            $allAds = array_merge($storageAds, getEnhancedNetworkSampleAds());
        }
    }
    
    $ads = ['success' => true, 'ads' => $allAds];
    
    // Get developer stats from database
    $developer = getDeveloperByUsername($currentUser['username']);
    if ($developer) {
        $developerStats = getDeveloperStats($developer['id']);
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PythonCoin Developer Dashboard v2.2.0</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #0066cc;
            --primary-dark: #0056b3;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
            --info: #17a2b8;
            --dark: #343a40;
            --light: #f8f9fa;
            --border: #dee2e6;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
            --shadow-lg: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .header {
            background: rgba(255,255,255,0.95);
            padding: 15px 0;
            box-shadow: var(--shadow);
            backdrop-filter: blur(10px);
            <?php echo !$isLoggedIn ? 'display: none;' : ''; ?>
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }
        
        .logo {
            font-size: 1.8em;
            font-weight: bold;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .network-status {
            display: flex;
            align-items: center;
            gap: 15px;
            font-size: 0.9em;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .status-online { background: #d4edda; color: #155724; }
        .status-offline { background: #f8d7da; color: #721c24; }
        .status-connecting { background: #fff3cd; color: #856404; }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .developer-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .api-key-display {
            font-family: monospace;
            background: #f8f9fa;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid var(--border);
            font-size: 0.8em;
            max-width: 150px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .logout-btn {
            background: var(--danger);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: background-color 0.3s ease;
        }
        
        .logout-btn:hover {
            background: #c82333;
        }
        
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 20px;
        }
        
        .auth-container {
            max-width: 450px;
            margin: 100px auto;
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 40px;
            box-shadow: var(--shadow-lg);
            backdrop-filter: blur(10px);
            <?php echo $isLoggedIn ? 'display: none;' : ''; ?>
        }
        
        .auth-tabs {
            display: flex;
            margin-bottom: 30px;
            border-radius: 8px;
            overflow: hidden;
            background: var(--light);
        }
        
        .auth-tab {
            flex: 1;
            padding: 12px;
            text-align: center;
            cursor: pointer;
            background: var(--light);
            border: none;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .auth-tab.active {
            background: var(--primary);
            color: white;
        }
        
        .auth-form {
            display: none;
        }
        
        .auth-form.active {
            display: block;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #4a5568;
        }
        
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .submit-btn {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        
        .submit-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .dashboard {
            <?php echo !$isLoggedIn ? 'display: none;' : ''; ?>
        }
        
        .dashboard-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 2px solid var(--border);
            flex-wrap: wrap;
        }
        
        .dashboard-tab {
            padding: 12px 24px;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 500;
            color: #718096;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        
        .dashboard-tab.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .panel {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }
        
        .panel h2 {
            color: var(--primary);
            margin-bottom: 20px;
            font-size: 1.4em;
            border-bottom: 2px solid var(--border);
            padding-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .grid {
            display: grid;
            gap: 20px;
        }
        
        .grid-2 { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
        .grid-3 { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
        .grid-4 { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
        
        .stats-card {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stats-card:hover {
            transform: translateY(-3px);
        }
        
        .stats-number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
            position: relative;
            z-index: 1;
        }
        
        .stats-label {
            font-size: 0.9em;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }
        
        .btn {
            display: inline-block;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            text-decoration: none;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .btn-primary { background: var(--primary); color: white; }
        .btn-success { background: var(--success); color: white; }
        .btn-warning { background: var(--warning); color: white; }
        .btn-info { background: var(--info); color: white; }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .network-client {
            background: white;
            border: 2px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        
        .network-client:hover {
            border-color: var(--primary);
            box-shadow: var(--shadow);
        }
        
        .network-client.selected {
            border-color: var(--success);
            background: #f8fff9;
        }
        
        .client-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .client-info h3 {
            margin: 0 0 5px 0;
            color: var(--dark);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .client-meta {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }
        
        .client-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .stat-item {
            text-align: center;
            padding: 10px;
            background: var(--light);
            border-radius: 6px;
        }
        
        .stat-number {
            font-size: 1.2em;
            font-weight: bold;
            color: var(--primary);
        }
        
        .stat-label {
            font-size: 0.8em;
            color: #666;
        }
        
        .code-preview {
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
            margin: 15px 0;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
            position: relative;
        }
        
        .copy-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background: var(--success);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8em;
        }
        
        .embed-form {
            background: var(--light);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .ad-preview {
            border: 2px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            background: white;
        }
        
        .ad-item {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            border-bottom: 1px solid var(--border);
            transition: background-color 0.3s ease;
        }
        
        .ad-item:last-child {
            border-bottom: none;
        }
        
        .ad-item:hover {
            background-color: var(--light);
        }
        
        .ad-image {
            width: 80px;
            height: 60px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            color: white;
            font-weight: bold;
        }
        
        .ad-content {
            flex: 1;
        }
        
        .ad-title {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .ad-description {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 4px;
        }
        
        .ad-meta {
            font-size: 0.8em;
            color: #999;
        }
        
        .pythoncoin-address {
            font-family: monospace;
            background: #f8f9fa;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid var(--border);
            font-size: 0.9em;
            word-break: break-all;
        }
        
        .earnings-display {
            background: linear-gradient(135deg, var(--success) 0%, #20c997 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .earnings-amount {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }
        
        .server-connection {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 15px;
            background: var(--light);
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .connection-light {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .light-green { background: var(--success); }
        .light-red { background: var(--danger); }
        .light-yellow { background: var(--warning); }
        
        .real-time-log {
            background: #1a202c;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 8px;
            height: 300px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.85em;
            margin: 15px 0;
            display: flex;
            flex-direction: column-reverse;
        }
        
        .log-entry {
            margin-bottom: 5px;
            padding: 2px 0;
        }
        
        .log-timestamp {
            color: #a0aec0;
        }
        
        .log-info { color: #63b3ed; }
        .log-success { color: #68d391; }
        .log-warning { color: #faf089; }
        .log-error { color: #fc8181; }
        
        .selected-clients {
            min-height: 60px;
            border: 2px dashed var(--border);
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }
        
        .client-tag {
            background: var(--primary);
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .remove-client {
            background: rgba(255,255,255,0.3);
            border: none;
            color: white;
            border-radius: 50%;
            width: 18px;
            height: 18px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            font-weight: 500;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .network-notice {
            background: linear-gradient(135deg, #17a2b8, #138496);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            margin: 10px 0;
            font-size: 0.9em;
            text-align: center;
        }

        /* Enhanced styles for storage ad indicators */
        .storage-badge {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: bold;
            margin-left: 8px;
        }

        .network-badge {
            background: linear-gradient(45deg, #007bff, #0056b3);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: bold;
            margin-left: 8px;
        }
        
        @media (max-width: 768px) {
            .grid-2, .grid-3, .grid-4 {
                grid-template-columns: 1fr;
            }
            
            .header-content {
                flex-direction: column;
                gap: 15px;
            }
            
            .dashboard-tabs {
                overflow-x: auto;
                white-space: nowrap;
            }
            
            .form-row {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header" id="header">
        <div class="header-content">
            <div class="logo">
                🌐 PythonCoin P2P Ad Network v2.2.0
                <span style="font-size: 0.6em; color: #718096;">Storage Integration</span>
            </div>
            <div class="network-status">
                <div class="status-indicator" id="connectionStatus">
                    <div class="status-dot"></div>
                    <span id="statusText">Online</span>
                </div>
                <div class="server-connection">
                    <div class="connection-light light-green" id="serverLight"></div>
                    <span id="serverStatus">Central Server</span>
                </div>
            </div>
            <div class="developer-info">
                <span>Developer: <strong><?php echo htmlspecialchars($currentUser['username'] ?? ''); ?></strong></span>
                <div class="api-key-display" title="Your PythonCoin Address">
                    <?php echo htmlspecialchars(substr($currentUser['pythoncoin_address'] ?? '', 0, 12) . '...'); ?>
                </div>
                <div class="earnings-display" style="padding: 8px 12px; font-size: 0.9em;">
                    <?php echo number_format($developerStats['total_earned'] ?? 0, 8); ?> PYC
                </div>
                <form method="post" style="display: inline;">
                    <input type="hidden" name="action" value="logout">
                    <button type="submit" class="logout-btn">Logout</button>
                </form>
            </div>
        </div>
    </div>

    <!-- Authentication (keep existing) -->
    <div class="auth-container" id="authContainer">
        <div class="logo" style="text-align: center; margin-bottom: 30px;">
            🌐 PythonCoin P2P Ad Network<br>
            <small style="font-size: 0.6em; color: #718096;">Developer Integration Portal v2.2.0</small>
        </div>
        
        <div class="auth-tabs">
            <button class="auth-tab active" data-auth-tab="login">Login</button>
            <button class="auth-tab" data-auth-tab="register">Register</button>
        </div>
        
        <!-- Login Form -->
        <form class="auth-form active" id="loginForm">
            <div class="form-group">
                <label for="loginUsername">Username</label>
                <input type="text" id="loginUsername" name="username" required>
            </div>
            <div class="form-group">
                <label for="loginPassword">Password</label>
                <input type="password" id="loginPassword" name="password" required>
            </div>
            <div class="form-group">
                <label for="loginPyCoinAddress">PythonCoin Address</label>
                <input type="text" id="loginPyCoinAddress" name="pythoncoin_address" placeholder="Your PythonCoin wallet address" required>
                <small style="color: #666; font-size: 0.85em;">This address will receive earnings from ad clicks</small>
            </div>
            <input type="hidden" name="action" value="login">
            <button type="submit" class="submit-btn">Connect to Network</button>
        </form>
        
        <!-- Register Form -->
        <form class="auth-form" id="registerForm">
            <div class="form-group">
                <label for="registerUsername">Username</label>
                <input type="text" id="registerUsername" name="username" required>
            </div>
            <div class="form-group">
                <label for="registerPassword">Password</label>
                <input type="password" id="registerPassword" name="password" required minlength="6">
            </div>
            <div class="form-group">
                <label for="confirmPassword">Confirm Password</label>
                <input type="password" id="confirmPassword" name="confirm_password" required>
            </div>
            <div class="form-group">
                <label for="registerPyCoinAddress">PythonCoin Address</label>
                <input type="text" id="registerPyCoinAddress" name="pythoncoin_address" placeholder="Your PythonCoin wallet address" required>
                <small style="color: #666; font-size: 0.85em;">Generate a PythonCoin address from the wallet application</small>
            </div>
            <div class="form-group">
                <label for="registerEmail">Email (Optional)</label>
                <input type="email" id="registerEmail" name="email" placeholder="your@email.com">
            </div>
            <input type="hidden" name="action" value="register">
            <button type="submit" class="submit-btn">Join Network</button>
        </form>
        
        <div id="authMessage"></div>
    </div>

    <!-- Dashboard -->
    <div class="container dashboard" id="dashboard">
        <!-- Dashboard Tabs -->
        <div class="dashboard-tabs">
            <button class="dashboard-tab active" data-tab="overview">📊 Overview</button>
            <button class="dashboard-tab" data-tab="network">🌐 P2P Clients</button>
            <button class="dashboard-tab" data-tab="generator">🔗 JS Generator</button>
            <button class="dashboard-tab" data-tab="ads">📺 Live Ads</button>
        </div>

        <!-- Overview Tab -->
        <div class="tab-content active" id="overviewTab">
            <div class="grid grid-4">
                <div class="stats-card">
                    <div class="stats-number"><?php echo number_format($developerStats['total_clicks'] ?? 0); ?></div>
                    <div class="stats-label">Total Clicks</div>
                </div>
                <div class="stats-card" style="background: linear-gradient(135deg, var(--success) 0%, #20c997 100%);">
                    <div class="stats-number"><?php echo number_format($developerStats['total_earned'] ?? 0, 8); ?></div>
                    <div class="stats-label">PYC Earned</div>
                </div>
                <div class="stats-card" style="background: linear-gradient(135deg, var(--info) 0%, #138496 100%);">
                    <div class="stats-number"><?php echo $developerStats['active_embeds'] ?? 0; ?></div>
                    <div class="stats-label">Active Embeds</div>
                </div>
                <div class="stats-card" style="background: linear-gradient(135deg, var(--warning) 0%, #e0a800 100%);">
                    <div class="stats-number" id="connectedClients">0</div>
                    <div class="stats-label">Connected Clients</div>
                </div>
            </div>
            
            <div class="grid grid-2">
                <div class="panel">
                    <h2>🔄 Real-Time Activity</h2>
                    <div class="real-time-log" id="activityLog">
                        <div class="log-entry"><span class="log-timestamp">[<?php echo date('H:i:s'); ?>]</span> <span class="log-info">Portal v2.2.0 initialized with storage support</span></div>
                        <?php if ($isLoggedIn): ?>
                        <div class="log-entry"><span class="log-timestamp">[<?php echo date('H:i:s'); ?>]</span> <span class="log-success">Developer <?php echo htmlspecialchars($currentUser['username']); ?> connected</span></div>
                        <?php endif; ?>
                    </div>
                </div>
                
                <div class="panel">
                    <h2>⚡ Quick Actions</h2>
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        <button class="btn btn-primary" id="scanClientsBtn">🔍 Scan for P2P Clients</button>
                        <button class="btn btn-success" id="generateAdBtn">⚡ Generate Enhanced Ad Block</button>
                        <button class="btn btn-info" id="testConnectionBtn">🔧 Test Central Server</button>
                        <button class="btn btn-warning" id="scanStorageBtn">📂 Scan Storage Ads</button>
                        <button class="btn btn-warning" id="refreshDataBtn">🔄 Refresh All Data</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Network Tab (keep existing) -->
        <div class="tab-content" id="networkTab">
            <div class="panel">
                <h2>🌐 Discover P2P Ad Clients</h2>
                <p>Connect to active PythonCoin P2P ad clients to access their advertisement content.</p>
                
                <div style="margin: 20px 0;">
                    <button class="btn btn-primary" id="scanNetworkBtn">🔍 Scan Network</button>
                    <button class="btn btn-info" id="refreshClientsBtn">🔄 Refresh</button>
                    <button class="btn btn-success" id="connectSelectedBtn">🔗 Connect Selected</button>
                </div>
                
                <div id="clientsList">
                    <div style="text-align: center; padding: 40px; color: #666;">
                        <h3>Network Discovery</h3>
                        <p>Initiate scan to discover active P2P advertising clients</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Generator Tab (keep existing but will enhance) -->
        <div class="tab-content" id="generatorTab">
            <div class="panel">
                <h2>⚡ Enhanced JavaScript Ad Block Generator</h2>
                <p>Generate personalized ad blocks that serve content from storage and selected P2P clients.</p>
                
                <div class="network-notice">
                    ✨ <strong>NEW:</strong> Generated JavaScript now supports ads_storage/active folder with HTML/SVG/JSON ad trios for rich interactive advertisements.
                </div>
                
                <div class="selected-clients" id="selectedClientsDisplay">
                    <span style="color: #666; font-style: italic;">Select P2P clients from the Network tab</span>
                </div>
                
                <div class="embed-form">
                    <div class="form-row">
                        <div class="form-group">
                            <label for="embedZone">Zone Identifier</label>
                            <input type="text" id="embedZone" value="main-content" placeholder="e.g., sidebar, header">
                        </div>
                        <div class="form-group">
                            <label for="adRotation">Rotation Interval</label>
                            <select id="adRotation">
                                <option value="15">15 seconds</option>
                                <option value="30" selected>30 seconds</option>
                                <option value="60">1 minute</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="embedWidth">Width</label>
                            <input type="text" id="embedWidth" value="400px">
                        </div>
                        <div class="form-group">
                            <label for="embedHeight">Height</label>
                            <input type="text" id="embedHeight" value="300px">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>Your PythonCoin Address (for payments)</label>
                        <div class="pythoncoin-address" id="pythonCoinAddressDisplay">
                            <?php echo htmlspecialchars($currentUser['pythoncoin_address'] ?? 'Loading...'); ?>
                        </div>
                    </div>
                </div>
                
                <div style="margin: 20px 0;">
                    <button class="btn btn-success" id="generateBlockBtn">🚀 Generate Enhanced Ad Block</button>
                    <button class="btn btn-warning" id="downloadBlockBtn">💾 Download JS File</button>
                    <button class="btn btn-info" id="generateHtmlBtn">📄 Generate HTML Example</button>
                </div>
                
                <div id="generatedCodeSection" style="display: none;">
                    <h3 style="color: var(--primary); margin: 20px 0 10px 0;">Generated Enhanced Ad Block Code</h3>
                    <div class="code-preview" id="generatedCode">
                        <button class="copy-btn" onclick="copyToClipboard()">📋 Copy</button>
                        <div id="codeContent"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Enhanced Ads Tab -->
        <div class="tab-content" id="adsTab">
            <div class="panel">
                <h2>📺 Live Advertisement Feed (Storage + Network)</h2>
                <p>Browse available advertisements from ads_storage and connected P2P clients.</p>
                
                <div style="margin: 20px 0;">
                    <button class="btn btn-primary" id="refreshAdsBtn">🔄 Refresh All Ads</button>
                    <button class="btn btn-success" id="scanStorageAdsBtn">📂 Scan Storage Only</button>
                    <button class="btn btn-info" id="previewAdBlockBtn">👁️ Preview Ad Block</button>
                    <button class="btn btn-warning" id="validateConnectionsBtn">🔗 Validate Connections</button>
                </div>
                
                <div id="adStatusInfo"></div>
                
                <div class="ad-preview" id="adsList">
                    <?php if ($ads && isset($ads['ads']) && is_array($ads['ads'])): ?>
                        <?php foreach ($ads['ads'] as $ad): ?>
                        <div class="ad-item">
                            <div class="ad-image">
                                <?php if (isset($ad['source']) && $ad['source'] === 'ads_storage'): ?>
                                📂
                                <?php else: ?>
                                📺
                                <?php endif; ?>
                            </div>
                            <div class="ad-content">
                                <div class="ad-title">
                                    <?php echo htmlspecialchars($ad['title'] ?? 'Untitled Ad'); ?>
                                    <?php if (isset($ad['source']) && $ad['source'] === 'ads_storage'): ?>
                                        <span class="storage-badge">STORAGE</span>
                                    <?php else: ?>
                                        <span class="network-badge">NETWORK</span>
                                    <?php endif; ?>
                                </div>
                                <div class="ad-description"><?php echo htmlspecialchars($ad['description'] ?? 'No description'); ?></div>
                                <div class="ad-meta">
                                    <strong>Category:</strong> <?php echo htmlspecialchars($ad['category'] ?? 'general'); ?> | 
                                    <strong>Payout:</strong> <?php echo number_format($ad['payout_amount'] ?? $ad['payout'] ?? 0.001, 8); ?> PYC
                                    <?php if (isset($ad['client_id'])): ?>
                                     | <strong>Client:</strong> <?php echo htmlspecialchars($ad['client_id']); ?>
                                    <?php endif; ?>
                                    <?php if (isset($ad['html_url'])): ?>
                                     | <strong>Format:</strong> HTML + SVG
                                    <?php else: ?>
                                     | <strong>Format:</strong> SVG Only
                                    <?php endif; ?>
                                </div>
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 5px;">
                                <button class="btn btn-info" onclick="previewSingleAd('<?php echo htmlspecialchars($ad['id'] ?? $ad['ad_id'] ?? ''); ?>', '<?php echo htmlspecialchars($ad['source'] ?? 'network'); ?>')">👁️ Preview</button>
                                <button class="btn btn-success" onclick="simulateAdClick('<?php echo htmlspecialchars($ad['id'] ?? $ad['ad_id'] ?? ''); ?>', '<?php echo htmlspecialchars($ad['client_id'] ?? 'unknown'); ?>', <?php echo $ad['payout_amount'] ?? $ad['payout'] ?? 0.001; ?>)">🖱️ Test Click</button>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    <?php else: ?>
                    <div style="text-align: center; padding: 40px; color: #666;">
                        <h3>Advertisement Feed</h3>
                        <p>Refresh to load current advertisements from storage and connected networks</p>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </div>

    <!-- Test ad zone -->
    <div data-pyc-zone="main-content"></div>
    <script src='<?php echo htmlspecialchars($currentUser['pythoncoin_address'] ?? '1CZSeEzAyKcbR9fytcT1hTKnG7PpcBhXoi'); ?>_adblock.js'></script>
    
    <script>
        // Global application state
        var currentUser = <?php echo json_encode($currentUser); ?>;
        var selectedClients = [];
        var availableClients = [];
        var liveAds = <?php echo json_encode($ads['ads'] ?? []); ?>;
        var serverConfig = {
            mainApi: window.location.href,
            jsServer: 'http://secupgrade.com:8082'
        };
        
        // Initialize application
        document.addEventListener('DOMContentLoaded', function() {
            console.log('PythonCoin Developer Dashboard v2.2.0 - Storage Integration Loaded');
            
            // Setup event listeners for auth tabs
            var authTabs = document.querySelectorAll('.auth-tab');
            for (var i = 0; i < authTabs.length; i++) {
                authTabs[i].addEventListener('click', function(e) {
                    var tab = e.target.getAttribute('data-auth-tab');
                    if (tab) switchTab(tab);
                });
            }
            
            // Setup event listeners for auth forms
            var loginForm = document.getElementById('loginForm');
            var registerForm = document.getElementById('registerForm');
            
            if (loginForm) loginForm.addEventListener('submit', login);
            if (registerForm) registerForm.addEventListener('submit', register);
            
            // Setup event listeners for dashboard tabs
            var dashboardTabs = document.querySelectorAll('.dashboard-tab');
            for (var i = 0; i < dashboardTabs.length; i++) {
                dashboardTabs[i].addEventListener('click', function(e) {
                    var tab = e.target.getAttribute('data-tab');
                    if (tab) switchDashboardTab(tab);
                });
            }
            
            // Setup event listeners for quick action buttons
            var scanBtn = document.getElementById('scanClientsBtn');
            var generateBtn = document.getElementById('generateAdBtn');
            var testBtn = document.getElementById('testConnectionBtn');
            var scanStorageBtn = document.getElementById('scanStorageBtn');
            var refreshBtn = document.getElementById('refreshDataBtn');
            
            if (scanBtn) scanBtn.addEventListener('click', function() { switchDashboardTab('network'); });
            if (generateBtn) generateBtn.addEventListener('click', function() { switchDashboardTab('generator'); });
            if (testBtn) testBtn.addEventListener('click', testConnection);
            if (scanStorageBtn) scanStorageBtn.addEventListener('click', scanStorageAds);
            if (refreshBtn) refreshBtn.addEventListener('click', refreshAllData);
            
            // Network tab buttons
            var scanNetworkBtn = document.getElementById('scanNetworkBtn');
            var refreshClientsBtn = document.getElementById('refreshClientsBtn');
            var connectSelectedBtn = document.getElementById('connectSelectedBtn');
            
            if (scanNetworkBtn) scanNetworkBtn.addEventListener('click', scanForClients);
            if (refreshClientsBtn) refreshClientsBtn.addEventListener('click', refreshClients);
            if (connectSelectedBtn) connectSelectedBtn.addEventListener('click', connectToSelected);
            
            // Generator tab buttons
            var generateBlockBtn = document.getElementById('generateBlockBtn');
            var downloadBlockBtn = document.getElementById('downloadBlockBtn');
            var generateHtmlBtn = document.getElementById('generateHtmlBtn');
            
            if (generateBlockBtn) generateBlockBtn.addEventListener('click', generateAdBlock);
            if (downloadBlockBtn) downloadBlockBtn.addEventListener('click', downloadAdBlock);
            if (generateHtmlBtn) generateHtmlBtn.addEventListener('click', generateHTMLExample);
            
            // Enhanced Ads tab buttons
            var refreshAdsBtn = document.getElementById('refreshAdsBtn');
            var scanStorageAdsBtn = document.getElementById('scanStorageAdsBtn');
            var previewAdBlockBtn = document.getElementById('previewAdBlockBtn');
            var validateConnectionsBtn = document.getElementById('validateConnectionsBtn');
            
            if (refreshAdsBtn) refreshAdsBtn.addEventListener('click', refreshAds);
            if (scanStorageAdsBtn) scanStorageAdsBtn.addEventListener('click', scanStorageAds);
            if (previewAdBlockBtn) previewAdBlockBtn.addEventListener('click', previewAdBlock);
            if (validateConnectionsBtn) validateConnectionsBtn.addEventListener('click', validateNetworkConnections);
            
            <?php if ($isLoggedIn): ?>
            addLog('Developer <?php echo htmlspecialchars($currentUser['username']); ?> connected', 'success');
            addLog('Storage integration enabled - checking for ads_storage/active', 'info');
            connectToCentralServer();
            
            // Auto-scan storage on startup
            setTimeout(function() {
                scanStorageAds();
            }, 1000);
            
            // Auto-load ads on startup
            setTimeout(function() {
                loadLiveAds();
            }, 2000);
            <?php endif; ?>
        });
        
        // NEW: Storage-specific functions
        function scanStorageAds() {
            addLog('Scanning ads_storage/active folder for ad trios...', 'info');
            
            var scanBtn = document.getElementById('scanStorageBtn') || document.getElementById('scanStorageAdsBtn');
            if (scanBtn) {
                var originalText = scanBtn.textContent;
                scanBtn.textContent = '📂 Scanning...';
                scanBtn.disabled = true;
                
                var resetButton = function() {
                    scanBtn.textContent = originalText;
                    scanBtn.disabled = false;
                };
            }
            
            fetch('?ajax=scan_storage_ads')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success) {
                        addLog('Storage scan complete: Found ' + data.count + ' active ads in storage', 'success');
                        
                        // Update the ads list if we're on the ads tab
                        if (data.ads && data.ads.length > 0) {
                            // Store storage ads for display
                            var storageAds = data.ads;
                            addLog('Storage ads include: ' + storageAds.map(function(ad) { return ad.title; }).join(', '), 'info');
                            
                            // Refresh the full ads list
                            loadLiveAds();
                        } else {
                            addLog('No active ads found in storage directory', 'warning');
                        }
                    } else {
                        addLog('Storage scan failed: ' + (data.error || 'Unknown error'), 'error');
                    }
                })
                .catch(function(error) {
                    addLog('Storage scan error: ' + error.message, 'error');
                })
                .finally(function() {
                    if (scanBtn && resetButton) resetButton();
                });
        }
        
        // Enhanced preview function for storage ads
        function previewSingleAd(adId, source) {
            if (!adId) {
                alert('No ad ID provided for preview');
                return;
            }
            
            addLog('Previewing ad: ' + adId + ' from ' + (source || 'unknown'), 'info');
            
            var previewUrl;
            var title = 'Ad Preview - ' + adId;
            
            if (source === 'ads_storage') {
                // For storage ads, try HTML first, then fall back to SVG
                previewUrl = '?ajax=serve_ad_html&ad_id=' + encodeURIComponent(adId);
                title = 'Storage Ad Preview - ' + adId;
            } else {
                // For network ads, use the proxy
                previewUrl = '?ajax=serve_ad_svg&ad_id=' + encodeURIComponent(adId);
                title = 'Network Ad Preview - ' + adId;
            }
            
            var previewWindow = window.open('', '_blank', 'width=800,height=700,scrollbars=yes');
            if (previewWindow) {
                var doc = previewWindow.document;
                doc.open();
                doc.write('<!DOCTYPE html>');
                doc.write('<html><head><title>' + title + '</title></head>');
                doc.write('<body style="margin:0;font-family:Arial;">');
                doc.write('<div style="padding:30px;background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);color:white;text-align:center;">');
                doc.write('<h1 style="margin:0 0 20px 0;">🌐 PythonCoin Ad Preview</h1>');
                doc.write('<h2 style="margin:0 0 10px 0;">' + adId + '</h2>');
                doc.write('<p style="margin:0 0 20px 0;">Source: ' + (source === 'ads_storage' ? 'Local Storage' : 'P2P Network') + '</p>');
                doc.write('<div style="background:white;padding:20px;border-radius:15px;margin:20px auto;max-width:700px;">');
                
                if (source === 'ads_storage') {
                    // For storage ads, embed as iframe
                    doc.write('<iframe src="' + previewUrl + '" style="width:100%;height:500px;border:none;"></iframe>');
                } else {
                    // For network ads, embed SVG directly
                    doc.write('<iframe src="' + previewUrl + '" style="width:100%;height:400px;border:none;"></iframe>');
                }
                
                doc.write('</div>');
                doc.write('<p style="font-size:0.9em;opacity:0.9;">Enhanced preview with storage integration</p>');
                doc.write('<button onclick="window.close()" style="background:#0066cc;color:white;border:none;padding:12px 24px;border-radius:6px;cursor:pointer;">Close Preview</button>');
                doc.write('</div></body></html>');
                doc.close();
            } else {
                alert('Popup blocked. Please allow popups for this site to preview ads.');
            }
        }
        
        // Authentication Functions (keep existing)
        function switchTab(tab) {
            var tabs = document.querySelectorAll('.auth-tab');
            var forms = document.querySelectorAll('.auth-form');
            
            for (var i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }
            for (var i = 0; i < forms.length; i++) {
                forms[i].classList.remove('active');
            }
            
            var activeTab = document.querySelector('[data-auth-tab="' + tab + '"]');
            var activeForm = document.getElementById(tab + 'Form');
            
            if (activeTab) activeTab.classList.add('active');
            if (activeForm) activeForm.classList.add('active');
        }
        
        function login(event) {
            event.preventDefault();
            
            var formData = new FormData(event.target);
            var submitBtn = event.target.querySelector('.submit-btn');
            
            submitBtn.textContent = 'Connecting...';
            submitBtn.disabled = true;
            
            fetch(window.location.href, {
                method: 'POST',
                body: formData
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.success) {
                    showMessage('Login successful! Redirecting...', 'success');
                    setTimeout(function() { 
                        window.location.reload(); 
                    }, 1000);
                } else {
                    showMessage(data.message || 'Login failed', 'error');
                }
            })
            .catch(function(error) {
                showMessage('Connection error: ' + error.message, 'error');
            })
            .finally(function() {
                submitBtn.textContent = 'Connect to Network';
                submitBtn.disabled = false;
            });
        }
        
        function register(event) {
            event.preventDefault();
            
            var password = document.getElementById('registerPassword').value;
            var confirmPassword = document.getElementById('confirmPassword').value;
            
            if (password !== confirmPassword) {
                showMessage('Passwords do not match', 'error');
                return;
            }
            
            var formData = new FormData(event.target);
            var submitBtn = event.target.querySelector('.submit-btn');
            
            submitBtn.textContent = 'Creating Account...';
            submitBtn.disabled = true;
            
            fetch(window.location.href, {
                method: 'POST',
                body: formData
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.success) {
                    showMessage('Registration successful! Redirecting...', 'success');
                    setTimeout(function() { 
                        window.location.reload(); 
                    }, 1000);
                } else {
                    showMessage(data.message || 'Registration failed', 'error');
                }
            })
            .catch(function(error) {
                showMessage('Connection error: ' + error.message, 'error');
            })
            .finally(function() {
                submitBtn.textContent = 'Join Network';
                submitBtn.disabled = false;
            });
        }
        
        function connectToCentralServer() {
            updateServerStatus('connecting');
            
            fetch('?ajax=heartbeat')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success) {
                        updateServerStatus('online');
                        addLog('Connected to central server', 'success');
                    } else {
                        updateServerStatus('offline');
                        addLog('Central server connection failed', 'error');
                    }
                })
                .catch(function(error) {
                    updateServerStatus('offline');
                    addLog('Server connection error: ' + error.message, 'error');
                });
        }
        
        function updateServerStatus(status) {
            var statusEl = document.getElementById('connectionStatus');
            var lightEl = document.getElementById('serverLight');
            var statusTextEl = document.getElementById('statusText');
            var serverStatusEl = document.getElementById('serverStatus');
            
            if (statusEl) statusEl.className = 'status-indicator status-' + status;
            
            if (status === 'online') {
                if (lightEl) lightEl.className = 'connection-light light-green';
                if (statusTextEl) statusTextEl.textContent = 'Connected';
                if (serverStatusEl) serverStatusEl.textContent = 'Central Server Online';
            } else if (status === 'offline') {
                if (lightEl) lightEl.className = 'connection-light light-red';
                if (statusTextEl) statusTextEl.textContent = 'Offline';
                if (serverStatusEl) serverStatusEl.textContent = 'Central Server Offline';
            } else {
                if (lightEl) lightEl.className = 'connection-light light-yellow';
                if (statusTextEl) statusTextEl.textContent = 'Connecting...';
                if (serverStatusEl) serverStatusEl.textContent = 'Connecting to Server...';
            }
        }
        
        // Dashboard Tab Switching Function
        function switchDashboardTab(tabName) {
            // Remove active class from all dashboard tabs
            var dashboardTabs = document.querySelectorAll('.dashboard-tab');
            for (var i = 0; i < dashboardTabs.length; i++) {
                dashboardTabs[i].classList.remove('active');
            }
            
            // Remove active class from all tab content areas
            var tabContents = document.querySelectorAll('.tab-content');
            for (var i = 0; i < tabContents.length; i++) {
                tabContents[i].classList.remove('active');
            }
            
            // Add active class to the clicked tab
            var activeTab = document.querySelector('[data-tab="' + tabName + '"]');
            if (activeTab) {
                activeTab.classList.add('active');
            }
            
            // Add active class to the corresponding content area
            var activeContent = document.getElementById(tabName + 'Tab');
            if (activeContent) {
                activeContent.classList.add('active');
            }
            
            // Log the tab switch for debugging
            addLog('Switched to ' + tabName + ' tab', 'info');
            
            // Perform tab-specific initialization if needed
            switch(tabName) {
                case 'network':
                    // Auto-scan for clients when switching to network tab
                    if (availableClients.length === 0) {
                        setTimeout(function() {
                            scanForClients();
                        }, 500);
                    }
                    break;
                case 'ads':
                    // Refresh ads when switching to ads tab
                    if (liveAds.length === 0 || !activeContent.dataset.loaded) {
                        setTimeout(function() {
                            loadLiveAds();
                            activeContent.dataset.loaded = 'true';
                        }, 500);
                    }
                    break;
                case 'generator':
                    // Update selected clients display when switching to generator
                    updateSelectedClientsDisplay();
                    break;
            }
        }
        
        // Enhanced loadLiveAds function with storage support
        function loadLiveAds() {
            addLog('Loading advertisements from storage and network...', 'info');
            
            var statusDiv = document.getElementById('adStatusInfo');
            if (statusDiv) {
                statusDiv.innerHTML = '<div class="alert alert-warning">🔄 Loading from ads_storage and P2P network...</div>';
            }
            
            fetch('?ajax=get_ads')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success && data.ads) {
                        liveAds = data.ads;
                        displayLiveAds();
                        addLog('Loaded ' + data.total_count + ' ads (' + (data.storage_count || 0) + ' from storage)', 'success');
                        
                        if (statusDiv) {
                            var storageCount = data.storage_count || 0;
                            var networkCount = data.total_count - storageCount;
                            statusDiv.innerHTML = '<div class="alert alert-success">✅ Loaded ' + data.total_count + ' ads (' + storageCount + ' from storage, ' + networkCount + ' from network)</div>';
                        }
                    } else {
                        addLog('Failed to load advertisements', 'error');
                        if (statusDiv) {
                            statusDiv.innerHTML = '<div class="alert alert-error">❌ Failed to load advertisements</div>';
                        }
                    }
                })
                .catch(function(error) {
                    addLog('Error loading advertisements: ' + error.message, 'error');
                    if (statusDiv) {
                        statusDiv.innerHTML = '<div class="alert alert-error">❌ Network error loading advertisements</div>';
                    }
                });
        }
        
        function displayLiveAds() {
            var container = document.getElementById('adsList');
            
            if (liveAds.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;"><h3>No advertisements available</h3><p>Scan storage and connect to P2P clients to load advertisements</p></div>';
                return;
            }
            
            // Clear container first
            container.innerHTML = '';
            
            for (var i = 0; i < liveAds.length; i++) {
                var ad = liveAds[i];
                var adId = ad.id || ad.ad_id || 'ad_' + i;
                var clientId = ad.client_id || 'unknown';
                var payout = ad.payout_amount || ad.payout || 0.001;
                var source = ad.source || 'network';
                
                // Determine the preview URL based on source
                var previewUrl;
                if (source === 'ads_storage') {
                    previewUrl = ad.html_url || ad.svg_url || ('?ajax=serve_ad_svg&ad_id=' + encodeURIComponent(adId));
                } else {
                    var adHost = ad.client_host || 'secupgrade.com'; 
                    var adPort = ad.client_port || '8082';
                    previewUrl = '?ajax=proxy_svg&client_host=' + encodeURIComponent(adHost) + '&client_port=' + encodeURIComponent(adPort) + '&ad_id=' + encodeURIComponent(adId);
                }
                
                var title = (ad.title || 'Untitled Ad').replace(/['"]/g, '');
                
                // Create ad item element
                var adItem = document.createElement('div');
                adItem.className = 'ad-item';
                
                // Create preview container
                var previewContainer = document.createElement('div');
                previewContainer.className = 'ad-preview-container';
                previewContainer.style.cssText = 'width: 120px; height: 90px; border: 1px solid #ddd; border-radius: 6px; overflow: hidden;';
                
                var iframe = document.createElement('iframe');
                iframe.src = previewUrl;
                iframe.style.cssText = 'width: 100%; height: 100%; border: none; pointer-events: none;';
                previewContainer.appendChild(iframe);
                
                // Create content section
                var contentDiv = document.createElement('div');
                contentDiv.className = 'ad-content';
                
                var sourceBadge = '';
                if (source === 'ads_storage') {
                    sourceBadge = '<span class="storage-badge">STORAGE</span>';
                } else {
                    sourceBadge = '<span class="network-badge">NETWORK</span>';
                }
                
                var formatInfo = '';
                if (ad.html_url) {
                    formatInfo = ' | <strong>Format:</strong> HTML + SVG';
                } else {
                    formatInfo = ' | <strong>Format:</strong> SVG Only';
                }
                
                contentDiv.innerHTML = 
                    '<div class="ad-title">' + title + ' ' + sourceBadge + '</div>' +
                    '<div class="ad-description">' + (ad.description || 'No description available') + '</div>' +
                    '<div class="ad-meta">' +
                    '<strong>Category:</strong> ' + (ad.category || 'general') + ' | ' +
                    '<strong>Payout:</strong> ' + Number(payout).toFixed(8) + ' PYC' +
                    (clientId !== 'unknown' ? ' | <strong>Client:</strong> ' + clientId : '') +
                    formatInfo +
                    '</div>';
                
                // Create button container
                var buttonContainer = document.createElement('div');
                buttonContainer.style.cssText = 'display: flex; flex-direction: column; gap: 5px;';
                
                // Create preview button
                var previewBtn = document.createElement('button');
                previewBtn.className = 'btn btn-info';
                previewBtn.textContent = '👁️ Preview';
                previewBtn.onclick = (function(id, src) {
                    return function() { previewSingleAd(id, src); };
                })(adId, source);
                
                // Create click button
                var clickBtn = document.createElement('button');
                clickBtn.className = 'btn btn-success';
                clickBtn.textContent = '🖱️ Test Click';
                clickBtn.onclick = (function(id, cid, p) {
                    return function() { simulateAdClick(id, cid, p); };
                })(adId, clientId, payout);
                
                buttonContainer.appendChild(previewBtn);
                buttonContainer.appendChild(clickBtn);
                
                // Assemble the ad item
                adItem.appendChild(previewContainer);
                adItem.appendChild(contentDiv);
                adItem.appendChild(buttonContainer);
                
                // Add to container
                container.appendChild(adItem);
            }
        }
        
        function scanForClients() {
            addLog('Scanning network for P2P clients...', 'info');
            
            var scanBtn = document.getElementById('scanNetworkBtn') || document.getElementById('scanClientsBtn');
            
            if (scanBtn) {
                var originalText = scanBtn.textContent;
                scanBtn.textContent = '🔍 Scanning...';
                scanBtn.disabled = true;
                
                var resetButton = function() {
                    scanBtn.textContent = originalText;
                    scanBtn.disabled = false;
                };
            }
            
            fetch('?ajax=scan_network')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success) {
                        availableClients = data.clients || [];
                        displayNetworkClients();
                        addLog('Network scan complete: Found ' + availableClients.length + ' P2P clients', 'success');
                        updateConnectedClientsCount();
                    } else {
                        addLog('Network scan failed: ' + (data.message || data.error), 'error');
                    }
                })
                .catch(function(error) {
                    addLog('Scan error: ' + error.message, 'error');
                })
                .finally(function() {
                    if (scanBtn && resetButton) resetButton();
                });
        }
        
        function displayNetworkClients() {
            var container = document.getElementById('clientsList');
            
            if (availableClients.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;"><h3>No active P2P clients detected</h3><p>Ensure P2P advertising clients are running and accessible on port 8082</p></div>';
                return;
            }
            
            // Clear container first
            container.innerHTML = '';
            
            for (var i = 0; i < availableClients.length; i++) {
                var client = availableClients[i];
                var isSelected = selectedClients.some(function(c) { return c.client_id === client.client_id; });
                
                // Create client element
                var clientDiv = document.createElement('div');
                clientDiv.className = 'network-client' + (isSelected ? ' selected' : '');
                
                // Create header
                var headerDiv = document.createElement('div');
                headerDiv.className = 'client-header';
                
                var infoDiv = document.createElement('div');
                infoDiv.className = 'client-info';
                infoDiv.innerHTML = 
                    '<h3><span class="status-badge status-' + client.status + '">' + client.status + '</span> ' + client.name + '</h3>' +
                    '<div class="client-meta"><strong>Client ID:</strong> ' + client.client_id + ' | <strong>Address:</strong> ' + client.host + ':' + client.port + '</div>';
                
                var selectBtn = document.createElement('button');
                selectBtn.className = 'btn ' + (isSelected ? 'btn-success' : 'btn-primary');
                selectBtn.textContent = isSelected ? '✓ Selected' : 'Select';
                selectBtn.setAttribute('data-client-id', client.client_id);
                selectBtn.addEventListener('click', function() {
                    toggleClientSelection(this.getAttribute('data-client-id'));
                });
                
                headerDiv.appendChild(infoDiv);
                headerDiv.appendChild(selectBtn);
                
                // Create stats
                var statsDiv = document.createElement('div');
                statsDiv.className = 'client-stats';
                statsDiv.innerHTML = 
                    '<div class="stat-item"><div class="stat-number">' + (client.ad_count || 0) + '</div><div class="stat-label">Ads</div></div>' +
                    '<div class="stat-item"><div class="stat-number">' + (client.peers || 0) + '</div><div class="stat-label">Peers</div></div>';
                
                clientDiv.appendChild(headerDiv);
                clientDiv.appendChild(statsDiv);
                container.appendChild(clientDiv);
            }
        }
        
        function toggleClientSelection(clientId) {
            var client = availableClients.find(function(c) { return c.client_id === clientId; });
            if (!client || client.status === 'offline') return;
            
            var index = selectedClients.findIndex(function(c) { return c.client_id === clientId; });
            
            if (index > -1) {
                selectedClients.splice(index, 1);
                addLog('Removed ' + client.name + ' from selection', 'info');
            } else {
                selectedClients.push(client);
                addLog('Added ' + client.name + ' to selection', 'info');
            }
            
            displayNetworkClients();
            updateSelectedClientsDisplay();
            updateConnectedClientsCount();
        }
        
        function updateSelectedClientsDisplay() {
            var container = document.getElementById('selectedClientsDisplay');
            
            if (selectedClients.length === 0) {
                container.innerHTML = '<span style="color: #666; font-style: italic;">Select P2P clients from the Network tab (storage ads always included)</span>';
                return;
            }
            
            // Clear container first
            container.innerHTML = '';
            
            for (var i = 0; i < selectedClients.length; i++) {
                var client = selectedClients[i];
                
                var clientTag = document.createElement('div');
                clientTag.className = 'client-tag';
                clientTag.textContent = client.name + ' ';
                
                var removeBtn = document.createElement('button');
                removeBtn.className = 'remove-client';
                removeBtn.textContent = '×';
                removeBtn.setAttribute('data-client-id', client.client_id);
                removeBtn.addEventListener('click', function() {
                    removeClientSelection(this.getAttribute('data-client-id'));
                });
                
                clientTag.appendChild(removeBtn);
                container.appendChild(clientTag);
            }
            
            // Auto-refresh ads when selection changes
            setTimeout(function() {
                loadAdsFromSelectedClients();
            }, 500);
        }
        
        function removeClientSelection(clientId) {
            selectedClients = selectedClients.filter(function(c) { return c.client_id !== clientId; });
            updateSelectedClientsDisplay();
            displayNetworkClients();
            updateConnectedClientsCount();
        }
        
        function updateConnectedClientsCount() {
            var countEl = document.getElementById('connectedClients');
            if (countEl) {
                countEl.textContent = selectedClients.length;
            }
        }
        
        // Enhanced Ad Block Generation with Storage Support
        function generateAdBlock() {
            if (!currentUser || !currentUser.pythoncoin_address) {
                alert('User session invalid. Please refresh the page and log in again.');
                return;
            }
            
            var zone = document.getElementById('embedZone').value || 'main-content';
            var rotation = parseInt(document.getElementById('adRotation').value) || 30;
            var width = document.getElementById('embedWidth').value || '400px';
            var height = document.getElementById('embedHeight').value || '300px';
            
            addLog('Generating enhanced ad block with storage support for zone: ' + zone, 'info');
            
            try {
                var adBlockCode = generateEnhancedJavaScriptAdBlock({
                    zone: zone,
                    rotation: rotation,
                    width: width,
                    height: height,
                    pythonCoinAddress: currentUser.pythoncoin_address,
                    developer: currentUser.username,
                    selectedClients: selectedClients, 
                    serverConfig: serverConfig
                });
                
                document.getElementById('codeContent').textContent = adBlockCode;
                document.getElementById('generatedCodeSection').style.display = 'block';
                
                addLog('Enhanced ad block generated successfully with storage + P2P support', 'success');
            } catch (error) {
                addLog('Error generating ad block: ' + error.message, 'error');
                alert('Error generating ad block: ' + error.message);
            }
        }
        
        // Enhanced JavaScript Ad Block Generator with Storage Support
        function generateEnhancedJavaScriptAdBlock(config) {
            var clientsJson = JSON.stringify(config.selectedClients); 
            var timestamp = new Date().toISOString();
            var filename = config.pythonCoinAddress + '_adblock.js'; 
            
            var code = '';
            code += '// PythonCoin P2P Ad Network - Enhanced Ad Block v2.2.0 (Storage + Network)\n';
            code += '// Supports: ads_storage/active folder with SVG/HTML/JSON ad trios\n';
            code += '// Developer: ' + config.developer + '\n';
            code += '// PythonCoin Address: ' + config.pythonCoinAddress + '\n';
            code += '// Generated: ' + timestamp + '\n';
            code += '// Zone: ' + config.zone + '\n';
            code += '// File: ' + filename + '\n\n'; 
            
            code += '(function() {\n';
            code += '    "use strict";\n\n';
            
            code += '    var PYC_AD_CONFIG = {\n';
            code += '        zone: "' + config.zone + '",\n';
            code += '        rotation: ' + (config.rotation * 1000) + ',\n';
            code += '        width: "' + config.width + '",\n';
            code += '        height: "' + config.height + '",\n';
            code += '        developer: "' + config.developer + '",\n';
            code += '        pythonCoinAddress: "' + config.pythonCoinAddress + '",\n';
            code += '        centralServer: "' + config.serverConfig.mainApi + '",\n';
            code += '        clients: ' + clientsJson + ',\n';
            code += '        currentAdIndex: 0,\n';
            code += '        container: null,\n';
            code += '        rotationTimer: null,\n';
            code += '        totalClicks: 0,\n';
            code += '        totalEarned: 0,\n';
            code += '        lastError: null,\n';
            code += '        registrationAttempts: 0,\n';
            code += '        storageAdsLoaded: [],\n';
            code += '        lastAdSource: null,\n';
            code += '        preferStorageAds: true\n';
            code += '    };\n\n';
            
            code += '    function safeJsonParse(str) {\n';
            code += '        try {\n';
            code += '            return JSON.parse(str);\n';
            code += '        } catch (e) {\n';
            code += '            console.error("JSON parse error:", e.message);\n';
            code += '            return null;\n';
            code += '        }\n';
            code += '    }\n\n';
            
            code += '    function initializeAdBlock() {\n';
            code += '        console.log("PythonCoin Enhanced Ad Block v2.2.0 - Storage + Network Support");\n';
            code += '        var container = document.querySelector("[data-pyc-zone=\\"" + PYC_AD_CONFIG.zone + "\\"]");\n';
            code += '        if (!container) {\n';
            code += '            console.error("PYC Ad Zone not found:", PYC_AD_CONFIG.zone);\n';
            code += '            return;\n';
            code += '        }\n';
            code += '        PYC_AD_CONFIG.container = container;\n';
            code += '        setupContainerStyles();\n';
            code += '        showPlaceholder("Loading PythonCoin Ads...");\n';
            code += '        \n';
            code += '        // Load storage ads first, then register with clients\n';
            code += '        loadStorageAds();\n';
            code += '        registerWithPyQtClients();\n';
            code += '        \n';
            code += '        if (PYC_AD_CONFIG.rotation > 0) {\n';
            code += '            PYC_AD_CONFIG.rotationTimer = setInterval(function() {\n';
            code += '                // Alternate between storage and network ads\n';
            code += '                if (PYC_AD_CONFIG.lastAdSource === "storage") {\n';
            code += '                    loadNextAd();\n';
            code += '                } else {\n';
            code += '                    displayStorageAd();\n';
            code += '                }\n';
            code += '            }, PYC_AD_CONFIG.rotation);\n';
            code += '        }\n';
            code += '    }\n\n';
            
            code += '    function setupContainerStyles() {\n';
            code += '        var container = PYC_AD_CONFIG.container;\n';
            code += '        if (!container) return;\n';
            code += '        container.style.cssText = "width: " + PYC_AD_CONFIG.width + "; height: " + PYC_AD_CONFIG.height + "; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa; overflow: hidden; position: relative; font-family: Arial, sans-serif; display: flex; align-items: center; justify-content: center;";\n';
            code += '    }\n\n';
            
            code += '    function loadStorageAds() {\n';
            code += '        console.log("Loading ads from storage...");\n';
            code += '        \n';
            code += '        fetch(PYC_AD_CONFIG.centralServer + "?ajax=scan_storage_ads")\n';
            code += '            .then(function(response) { return response.json(); })\n';
            code += '            .then(function(data) {\n';
            code += '                if (data.success && data.ads && data.ads.length > 0) {\n';
            code += '                    PYC_AD_CONFIG.storageAdsLoaded = data.ads;\n';
            code += '                    console.log("Loaded " + data.ads.length + " ads from storage");\n';
            code += '                    displayStorageAd();\n';
            code += '                } else {\n';
            code += '                    console.log("No storage ads found, using network only");\n';
            code += '                    setTimeout(loadNextAd, 2000);\n';
            code += '                }\n';
            code += '            })\n';
            code += '            .catch(function(error) {\n';
            code += '                console.warn("Storage ads loading failed:", error);\n';
            code += '                setTimeout(loadNextAd, 2000);\n';
            code += '            });\n';
            code += '    }\n\n';
            
            code += '    function displayStorageAd() {\n';
code += '        if (PYC_AD_CONFIG.storageAdsLoaded.length === 0) {\n';
code += '            loadNextAd();\n';
code += '            return;\n';
code += '        }\n';
code += '        \n';
code += '        var randomAd = PYC_AD_CONFIG.storageAdsLoaded[Math.floor(Math.random() * PYC_AD_CONFIG.storageAdsLoaded.length)];\n';
code += '        PYC_AD_CONFIG.lastAdSource = "storage";\n';
code += '        \n';
code += '        console.log("Displaying storage ad (SVG only):", randomAd.id);\n';
code += '        \n';
code += '        // Always display as SVG - ignore HTML files\n';
code += '        displaySvgAd(randomAd, {client_id: "storage"});\n';
code += '    }\n\n';
            
            code += '    function displayHtmlAd(ad) {\n';
            code += '        console.log("Loading HTML ad with enhanced features...");\n';
            code += '        \n';
            code += '        fetch(ad.html_url)\n';
            code += '            .then(function(response) { return response.text(); })\n';
            code += '            .then(function(htmlContent) {\n';
            code += '                if (htmlContent && htmlContent.includes("<")) {\n';
            code += '                    // Create iframe for security and isolation\n';
            code += '                    var iframe = document.createElement("iframe");\n';
            code += '                    iframe.style.cssText = "width: 100%; height: 100%; border: none; overflow: hidden;";\n';
            code += '                    iframe.srcdoc = htmlContent;\n';
            code += '                    \n';
            code += '                    PYC_AD_CONFIG.container.innerHTML = "";\n';
            code += '                    PYC_AD_CONFIG.container.appendChild(iframe);\n';
            code += '                    \n';
            code += '                    // Add click handler for the entire container\n';
            code += '                    PYC_AD_CONFIG.container.style.cursor = "pointer";\n';
            code += '                    PYC_AD_CONFIG.container.onclick = function() {\n';
            code += '                        recordClick(ad.id, "storage", ad.payout_amount || 0.001);\n';
            code += '                        if (ad.target_url || ad.click_url) {\n';
            code += '                            window.open(ad.target_url || ad.click_url, "_blank");\n';
            code += '                        }\n';
            code += '                    };\n';
            code += '                    \n';
            code += '                    console.log("HTML ad displayed successfully");\n';
            code += '                } else {\n';
            code += '                    console.warn("Invalid HTML content, falling back to SVG");\n';
            code += '                    displaySvgAd(ad, {client_id: "storage"});\n';
            code += '                }\n';
            code += '            })\n';
            code += '            .catch(function(error) {\n';
            code += '                console.error("HTML ad loading error:", error);\n';
            code += '                displaySvgAd(ad, {client_id: "storage"});\n';
            code += '            });\n';
            code += '        \n';
            code += '        recordView(ad, {client_id: "storage"});\n';
            code += '    }\n\n';
            
            // Add the rest of the existing JavaScript functions with enhancements...
            code += '    function registerWithPyQtClients() {\n';
            code += '        if (PYC_AD_CONFIG.clients.length === 0) {\n';
            code += '            console.log("No P2P clients configured for registration.");\n';
            code += '            return;\n';
            code += '        }\n\n';
            
            code += '        PYC_AD_CONFIG.registrationAttempts++;\n';
            code += '        console.log("Registration attempt #" + PYC_AD_CONFIG.registrationAttempts + " with configured P2P clients...");\n\n';
            
            code += '        PYC_AD_CONFIG.clients.forEach(function(client) {\n';
            code += '            fetch(PYC_AD_CONFIG.centralServer + "?ajax=proxy_register", {\n';
            code += '                method: "POST",\n';
            code += '                headers: { "Content-Type": "application/x-www-form-urlencoded" },\n';
            code += '                body: "client_host=" + encodeURIComponent(client.host) + \n';
            code += '                      "&client_port=" + encodeURIComponent(client.port || "8082") + \n';
            code += '                      "&developer_address=" + encodeURIComponent(PYC_AD_CONFIG.pythonCoinAddress) + \n';
            code += '                      "&developer_name=" + encodeURIComponent(PYC_AD_CONFIG.developer) + \n';
            code += '                      "&zone=" + encodeURIComponent(PYC_AD_CONFIG.zone)\n';
            code += '            })\n';
            code += '            .then(function(response) { return response.text(); })\n';
            code += '            .then(function(text) {\n';
            code += '                var data = safeJsonParse(text);\n';
            code += '                if (data && data.success) {\n';
            code += '                    console.log("Successfully registered with " + (client.name || client.host));\n';
            code += '                } else {\n';
            code += '                    console.warn("Failed to register with " + (client.name || client.host));\n';
            code += '                }\n';
            code += '            })\n';
            code += '            .catch(function(e) { \n';
            code += '                console.error("Registration error with " + (client.name || client.host) + ":", e.message); \n';
            code += '            });\n';
            code += '        });\n';
            code += '    }\n\n';
            
            code += '    function loadNextAd() {\n';
            code += '        if (PYC_AD_CONFIG.clients.length === 0) {\n';
            code += '            showFallbackAd("No P2P clients configured");\n';
            code += '            return;\n';
            code += '        }\n\n';
            
            code += '        var client = PYC_AD_CONFIG.clients[PYC_AD_CONFIG.currentAdIndex % PYC_AD_CONFIG.clients.length];\n';
            code += '        PYC_AD_CONFIG.currentAdIndex++;\n';
            code += '        PYC_AD_CONFIG.lastAdSource = "network";\n';
            code += '        \n';
            code += '        console.log("Loading network ads from:", client.name || client.host);\n';
            code += '        \n';
            code += '        fetch(PYC_AD_CONFIG.centralServer + "?ajax=proxy_ads", {\n';
            code += '            method: "POST",\n';
            code += '            headers: { "Content-Type": "application/x-www-form-urlencoded" },\n';
            code += '            body: "client_host=" + encodeURIComponent(client.host) + \n';
            code += '                  "&client_port=" + encodeURIComponent(client.port || "8082") + \n';
            code += '                  "&zone=" + encodeURIComponent(PYC_AD_CONFIG.zone) + \n';
            code += '                  "&developer_address=" + encodeURIComponent(PYC_AD_CONFIG.pythonCoinAddress)\n';
            code += '        })\n';
            code += '        .then(function(response) { return response.text(); })\n';
            code += '        .then(function(text) {\n';
            code += '            var data = safeJsonParse(text);\n';
            code += '            \n';
            code += '            if (data && data.success && data.ads && data.ads.length > 0) {\n';
            code += '                var randomAd = data.ads[Math.floor(Math.random() * data.ads.length)];\n';
            code += '                displaySvgAd(randomAd, client);\n';
            code += '            } else {\n';
            code += '                console.warn("No network ads available, trying storage fallback");\n';
            code += '                if (PYC_AD_CONFIG.storageAdsLoaded.length > 0) {\n';
            code += '                    displayStorageAd();\n';
            code += '                } else {\n';
            code += '                    showFallbackAd("No ads available");\n';
            code += '                }\n';
            code += '            }\n';
            code += '        })\n';
            code += '        .catch(function(error) {\n';
            code += '            console.error("Network ad loading error:", error);\n';
            code += '            if (PYC_AD_CONFIG.storageAdsLoaded.length > 0) {\n';
            code += '                displayStorageAd();\n';
            code += '            } else {\n';
            code += '                showFallbackAd("Network Error");\n';
            code += '            }\n';
            code += '        });\n';
            code += '    }\n\n';
            
            code += '    function displaySvgAd(ad, client) {\n';
            code += '        var svgUrl;\n';
            code += '        if (client.client_id === "storage") {\n';
            code += '            svgUrl = ad.svg_url;\n';
            code += '        } else {\n';
            code += '            svgUrl = PYC_AD_CONFIG.centralServer + "?ajax=proxy_svg&client_host=" + encodeURIComponent(client.host || "127.0.0.1") + "&client_port=" + encodeURIComponent(client.port || "8082") + "&ad_id=" + encodeURIComponent(ad.id || ad.ad_id || "unknown");\n';
            code += '        }\n';
            code += '        \n';
            code += '        fetch(svgUrl)\n';
            code += '            .then(function(response) { return response.text(); })\n';
            code += '            .then(function(svgContent) {\n';
            code += '                if (svgContent && (svgContent.includes("<svg") || svgContent.includes("<?xml"))) {\n';
            code += '                    PYC_AD_CONFIG.container.innerHTML = svgContent;\n';
            code += '                    console.log("SVG ad displayed successfully");\n';
            code += '                    addClickHandler(ad, client);\n';
            code += '                } else {\n';
            code += '                    showFallbackAd("Invalid SVG content");\n';
            code += '                }\n';
            code += '            })\n';
            code += '            .catch(function(error) {\n';
            code += '                console.error("SVG loading error:", error);\n';
            code += '                showFallbackAd("SVG Load Error");\n';
            code += '            });\n';
            code += '        \n';
            code += '        recordView(ad, client);\n';
            code += '    }\n\n';
            
            code += '    function addClickHandler(ad, client) {\n';
            code += '        if (!PYC_AD_CONFIG.container) return;\n';
            code += '        PYC_AD_CONFIG.container.style.cursor = "pointer";\n';
            code += '        PYC_AD_CONFIG.container.onclick = function() {\n';
            code += '            recordClick(ad.id || ad.ad_id, client.client_id, ad.payout_amount || ad.payout || 0.001);\n';
            code += '            if (ad.target_url || ad.click_url) {\n';
            code += '                window.open(ad.target_url || ad.click_url, "_blank");\n';
            code += '            }\n';
            code += '        };\n';
            code += '    }\n\n';
            
            code += '    function showFallbackAd(message) {\n';
            code += '        if (!PYC_AD_CONFIG.container) return;\n';
            code += '        \n';
            code += '        var fallbackSvg = \'<svg width="100%" height="100%" viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">\';\n';
            code += '        fallbackSvg += \'<defs><linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">\';\n';
            code += '        fallbackSvg += \'<stop offset="0%" style="stop-color:#0066cc;stop-opacity:1" />\';\n';
            code += '        fallbackSvg += \'<stop offset="100%" style="stop-color:#004499;stop-opacity:1" />\';\n';
            code += '        fallbackSvg += \'</linearGradient></defs>\';\n';
            code += '        fallbackSvg += \'<rect width="100%" height="100%" fill="url(#grad1)" rx="10"/>\';\n';
            code += '        fallbackSvg += \'<text x="200" y="120" font-family="Arial" font-size="24" fill="white" text-anchor="middle" font-weight="bold">🌐 PythonCoin</text>\';\n';
            code += '        fallbackSvg += \'<text x="200" y="150" font-family="Arial" font-size="16" fill="white" text-anchor="middle">P2P Ad Network v2.2.0</text>\';\n';
            code += '        fallbackSvg += \'<text x="200" y="180" font-family="Arial" font-size="12" fill="#ccddff" text-anchor="middle">\' + (message || "Loading...") + \'</text>\';\n';
            code += '        fallbackSvg += \'<text x="200" y="220" font-family="Arial" font-size="10" fill="#ccddff" text-anchor="middle">Storage + Network Integration</text>\';\n';
            code += '        fallbackSvg += \'</svg>\';\n';
            code += '        \n';
            code += '        PYC_AD_CONFIG.container.innerHTML = fallbackSvg;\n';
            code += '        PYC_AD_CONFIG.container.style.cursor = "default";\n';
            code += '        PYC_AD_CONFIG.container.onclick = null;\n';
            code += '    }\n\n';
            
            code += '    function showPlaceholder(message) {\n';
            code += '        if (!PYC_AD_CONFIG.container) return;\n';
            code += '        PYC_AD_CONFIG.container.innerHTML = "<div style=\\"display:flex;align-items:center;justify-content:center;height:100%;color:#666;font-size:14px;text-align:center;\\">" + message + "</div>";\n';
            code += '    }\n\n';
            
            code += '    function recordView(ad, client) {\n';
            code += '        fetch(PYC_AD_CONFIG.centralServer + "?ajax=record_view", {\n';
            code += '            method: "POST",\n';
            code += '            headers: {"Content-Type": "application/x-www-form-urlencoded"},\n';
            code += '            body: "ad_id=" + encodeURIComponent(ad.id || ad.ad_id || "unknown") + \n';
            code += '                  "&client_id=" + encodeURIComponent(client.client_id || "unknown") + \n';
            code += '                  "&zone=" + encodeURIComponent(PYC_AD_CONFIG.zone) + \n';
            code += '                  "&developer_address=" + encodeURIComponent(PYC_AD_CONFIG.pythonCoinAddress)\n';
            code += '        }).catch(function(e) { console.warn("View record failed:", e.message); });\n';
            code += '    }\n\n';
            
            code += '    function recordClick(adId, clientId, payoutAmount) {\n';
            code += '        console.log("Ad clicked:", adId, "Payout:", payoutAmount);\n';
            code += '        PYC_AD_CONFIG.totalClicks++;\n';
            code += '        PYC_AD_CONFIG.totalEarned += payoutAmount;\n';
            code += '        \n';
            code += '        fetch(PYC_AD_CONFIG.centralServer + "?ajax=record_click", {\n';
            code += '            method: "POST",\n';
            code += '            headers: {"Content-Type": "application/x-www-form-urlencoded"},\n';
            code += '            body: "ad_id=" + encodeURIComponent(adId) + \n';
            code += '                  "&client_id=" + encodeURIComponent(clientId) + \n';
            code += '                  "&zone=" + encodeURIComponent(PYC_AD_CONFIG.zone) + \n';
            code += '                  "&payout_amount=" + payoutAmount\n';
            code += '        })\n';
            code += '        .then(function(response) { return response.text(); })\n';
            code += '        .then(function(text) {\n';
            code += '            var data = safeJsonParse(text);\n';
            code += '            if (data && data.success) {\n';
            code += '                console.log("Click tracked successfully. Total earned:", PYC_AD_CONFIG.totalEarned.toFixed(8), "PYC");\n';
            code += '            } else {\n';
            code += '                console.warn("Click tracking failed");\n';
            code += '            }\n';
            code += '        })\n';
            code += '        .catch(function(e) { console.error("Click tracking error:", e.message); });\n';
            code += '    }\n\n';
            
            code += '    // Global functions\n';
            code += '    window.recordClick = recordClick;\n\n';
            
            code += '    window.PYC_STATS = function() {\n';
            code += '        return {\n';
            code += '            totalClicks: PYC_AD_CONFIG.totalClicks,\n';
            code += '            totalEarned: PYC_AD_CONFIG.totalEarned,\n';
            code += '            developerAddress: PYC_AD_CONFIG.pythonCoinAddress,\n';
            code += '            connectedClients: PYC_AD_CONFIG.clients.length,\n';
            code += '            storageAdsCount: PYC_AD_CONFIG.storageAdsLoaded.length,\n';
            code += '            lastAdSource: PYC_AD_CONFIG.lastAdSource,\n';
            code += '            lastError: PYC_AD_CONFIG.lastError,\n';
            code += '            version: "2.2.0"\n';
            code += '        };\n';
            code += '    };\n\n';
            
            code += '    window.PYC_FORCE_RELOAD = function() {\n';
            code += '        console.log("Force reloading ads...");\n';
            code += '        if (PYC_AD_CONFIG.storageAdsLoaded.length > 0) {\n';
            code += '            displayStorageAd();\n';
            code += '        } else {\n';
            code += '            loadNextAd();\n';
            code += '        }\n';
            code += '    };\n\n';
            
            code += '    // Initialize when DOM is ready\n';
            code += '    if (document.readyState === "loading") {\n';
            code += '        document.addEventListener("DOMContentLoaded", initializeAdBlock);\n';
            code += '    } else {\n';
            code += '        initializeAdBlock();\n';
            code += '    }\n\n';
            
            code += '})();\n\n';
            code += '/* Enhanced Usage Instructions v2.2.0:\n';
            code += ' * 1. Save this file as: ' + filename + '\n';
            code += " * 2. Include in HTML: <script src='" + filename + "'><\\/script>\n";
            code += ' * 3. Add ad zone: <div data-pyc-zone="' + config.zone + '"></div>\n';
            code += ' * 4. Ads loaded from: ads_storage/active + P2P network\n';
            code += ' * 5. HTML ads supported with full interactivity\n';
            code += ' * 6. Payments sent to: ' + config.pythonCoinAddress + '\n';
            code += ' * 7. Debug: console.log(PYC_STATS()) - check version 2.2.0\n';
            code += ' * 8. Force reload: PYC_FORCE_RELOAD()\n';
            code += ' */';
            
            return code;
        }
        
        function generateHTMLExample() {
            if (!currentUser || !currentUser.pythoncoin_address) {
                alert('User session invalid. Please refresh the page and log in again.');
                return;
            }
            
            var zone = document.getElementById('embedZone').value || 'main-content';
            var width = document.getElementById('embedWidth').value || '400px';
            var height = document.getElementById('embedHeight').value || '300px';
            
            try {
                var jsFileName = currentUser.pythoncoin_address + '_adblock.js'; 
                
                var htmlContent = [];
                htmlContent.push('<!DOCTYPE html>');
                htmlContent.push('<html lang="en">');
                htmlContent.push('<head>');
                htmlContent.push('    <meta charset="UTF-8">');
                htmlContent.push('    <meta name="viewport" content="width=device-width, initial-scale=1.0">');
                htmlContent.push('    <title>PythonCoin Ad Integration Example v2.2.0</title>');
                htmlContent.push('</head>');
                htmlContent.push('<body>');
                htmlContent.push('    <h1>My Website with Enhanced Ads</h1>');
                htmlContent.push('    <p>Welcome to my website with PythonCoin P2P advertising (Storage + Network)!</p>');
                htmlContent.push('');
                htmlContent.push('    <!-- PythonCoin Enhanced Ad Zone -->');
                htmlContent.push('    <div data-pyc-zone="' + zone + '" style="width: ' + width + '; height: ' + height + '; margin: 20px auto; border: 2px dashed #0066cc; padding: 10px; background: #f9f9f9; text-align: center;">');
                htmlContent.push('        Loading PythonCoin Ads...');
                htmlContent.push('    </div>');
                htmlContent.push('');
                htmlContent.push('    <!-- Load Enhanced PythonCoin Ad Block -->');
                htmlContent.push('    <script src="' + jsFileName + '"><\\/script>');
                htmlContent.push('');
                htmlContent.push('    <!-- Optional: Check enhanced stats -->');
                htmlContent.push('    <script>');
                htmlContent.push('        setTimeout(function() {');
                htmlContent.push('            if (typeof PYC_STATS === "function") {');
                htmlContent.push('                console.log("PythonCoin Enhanced Ad Stats:", PYC_STATS());');
                htmlContent.push('            }');
                htmlContent.push('        }, 5000);');
                htmlContent.push('    <\script>');
                htmlContent.push('</body>');
                htmlContent.push('</html>');
                
                document.getElementById('codeContent').textContent = htmlContent.join('\n');
                document.getElementById('generatedCodeSection').style.display = 'block';
                
                addLog('Enhanced HTML example generated with storage + network support', 'success');
            } catch (error) {
                addLog('Error generating HTML example: ' + error.message, 'error');
                alert('Error generating HTML example: ' + error.message);
            }
        }
        
        function copyToClipboard() {
            var codeElement = document.getElementById('codeContent');
            if (!codeElement) {
                alert('No code element found');
                return;
            }
            
            var code = codeElement.textContent;
            if (!code || code.trim() === '') {
                alert('No code generated yet. Please generate an ad block first.');
                return;
            }
            
            if (navigator.clipboard) {
                navigator.clipboard.writeText(code).then(function() {
                    addLog('Enhanced code copied to clipboard', 'success');
                    alert('Enhanced code copied to clipboard!');
                }).catch(function(err) {
                    console.error('Failed to copy: ', err);
                    fallbackCopyToClipboard(code);
                });
            } else {
                fallbackCopyToClipboard(code);
            }
        }
        
        function fallbackCopyToClipboard(text) {
            var textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                var successful = document.execCommand('copy');
                if (successful) {
                    alert('Enhanced code copied to clipboard!');
                    addLog('Enhanced code copied (fallback method)', 'success');
                } else {
                    alert('Failed to copy code. Please copy manually.');
                }
            } catch (err) {
                alert('Failed to copy code. Please copy manually.');
            }
            document.body.removeChild(textArea);
        }
        
        function downloadAdBlock() {
            if (!currentUser || !currentUser.pythoncoin_address) {
                alert('User session invalid. Please refresh the page and log in again.');
                return;
            }
            
            var codeElement = document.getElementById('codeContent');
            if (!codeElement) {
                alert('No code element found');
                return;
            }
            
            var code = codeElement.textContent;
            if (!code || code.trim() === '') {
                alert('Generate enhanced ad block code first');
                return;
            }
            
            try {
                var filename = currentUser.pythoncoin_address + '_adblock.js'; 
                var blob = new Blob([code], { type: 'application/javascript' });
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                addLog('Enhanced ad block JavaScript downloaded: ' + filename, 'success');
            } catch (error) {
                addLog('Error downloading file: ' + error.message, 'error');
                alert('Error downloading file: ' + error.message);
            }
        }
        
        function simulateAdClick(adId, clientId, payoutAmount) {
            addLog('Processing ad click interaction...', 'info');
            
            fetch('?ajax=record_click', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: 'ad_id=' + encodeURIComponent(adId) + '&client_id=' + encodeURIComponent(clientId) + '&zone=preview&payout_amount=' + payoutAmount
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.success) {
                    addLog('Click recorded successfully! Earned: ' + Number(data.amount).toFixed(8) + ' PYC', 'success');
                    alert('Click processed successfully! You earned ' + Number(data.amount).toFixed(8) + ' PYC');
                    
                    // Update earnings display
                    setTimeout(function() {
                        location.reload();
                    }, 2000);
                } else {
                    addLog('Click processing failed: ' + data.error, 'error');
                    alert('Click processing failed: ' + data.error);
                }
            })
            .catch(function(error) {
                addLog('Click processing error: ' + error.message, 'error');
                alert('Click processing error: ' + error.message);
            });
        }
        
        function validateNetworkConnections() {
            addLog('Validating P2P network connections...', 'info');
            
            if (selectedClients.length === 0) {
                alert('No P2P clients selected. Storage ads will still work.');
                return;
            }
            
            var validConnections = 0;
            var totalClients = selectedClients.length;
            
            selectedClients.forEach(function(client, index) {
                fetch('http://' + client.host + ':' + client.port + '/ads')
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        validConnections++;
                        addLog('Connection validated: ' + client.name + ' (' + (data.ads ? data.ads.length : 0) + ' ads available)', 'success');
                        
                        if (validConnections === totalClients) {
                            addLog('Network validation complete: ' + validConnections + '/' + totalClients + ' connections active', 'success');
                            loadLiveAds();
                        }
                    })
                    .catch(function(error) {
                        addLog('Connection failed: ' + client.name + ' - ' + error.message, 'error');
                        
                        if (index === totalClients - 1) {
                            addLog('Network validation complete: ' + validConnections + '/' + totalClients + ' connections active', validConnections > 0 ? 'success' : 'error');
                        }
                    });
            });
        }
        
        function previewAdBlock() {
            var zone = document.getElementById('embedZone').value || 'main-content';
            var width = document.getElementById('embedWidth').value || '400px';
            var height = document.getElementById('embedHeight').value || '300px';
            
            var previewWindow = window.open('', '_blank', 'width=900,height=600,scrollbars=yes');
            if (previewWindow) {
                var doc = previewWindow.document;
                doc.open();
                doc.write('<!DOCTYPE html>');
                doc.write('<html><head><title>PythonCoin Enhanced Ad Block Preview v2.2.0</title></head>');
                doc.write('<body style="font-family:Arial;padding:20px;background:#f5f5f5;">');
                doc.write('<h1 style="text-align:center;color:#0066cc;">🌐 PythonCoin Enhanced Ad Block Preview</h1>');
                doc.write('<p style="text-align:center;color:#666;">Storage + Network Integration - Version 2.2.0</p>');
                doc.write('<div style="max-width:800px;margin:20px auto;padding:20px;background:white;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);">');
                doc.write('<h3>Sample Website Content</h3>');
                doc.write('<p>This is regular website content. Below is your enhanced PythonCoin ad zone:</p>');
                doc.write('<div data-pyc-zone="' + zone + '" style="width:' + width + ';height:' + height + ';margin:20px auto;border:2px dashed #0066cc;background:#f8f9fa;display:flex;align-items:center;justify-content:center;color:#666;font-size:18px;">Enhanced PythonCoin Ad Zone<br><small>(' + zone + ') - Storage + Network</small></div>');
                doc.write('<p>More website content would appear here...</p>');
                doc.write('<div style="text-align:center;margin-top:30px;"><button onclick="window.close()" style="background:#0066cc;color:white;border:none;padding:10px 20px;border-radius:5px;cursor:pointer;">Close Preview</button></div>');
                doc.write('</div></body></html>');
                doc.close();
                
                addLog('Opened enhanced ad block preview for zone: ' + zone, 'info');
            } else {
                alert('Popup blocked. Please allow popups for this site to preview ad blocks.');
            }
        }
        
        function testConnection() {
            addLog('Testing central server connection...', 'info');
            updateServerStatus('connecting');
            
            fetch('?ajax=test_connection')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success) {
                        updateServerStatus('online');
                        addLog('Central server connection successful', 'success');
                        alert('Connection test successful!\n\nServer Status: Online\nAPI Version: 2.2.0 - Storage Integration');
                    } else {
                        throw new Error(data.message || data.error || 'Unknown error');
                    }
                })
                .catch(function(error) {
                    updateServerStatus('offline');
                    addLog('Central server connection failed: ' + error.message, 'error');
                    alert('Connection test failed: ' + error.message);
                });
        }
        
        function refreshClients() {
            addLog('Refreshing P2P client list...', 'info');
            scanForClients();
        }
        
        function connectToSelected() {
            if (selectedClients.length === 0) {
                alert('No P2P clients selected. Storage ads will still work automatically.');
                return;
            }
            
            addLog('Connecting to ' + selectedClients.length + ' selected clients...', 'info');
            
            for (var i = 0; i < selectedClients.length; i++) {
                var client = selectedClients[i];
                addLog('Connected to ' + client.name + ' (' + client.client_id + ')', 'success');
            }
            
            alert('Successfully connected to ' + selectedClients.length + ' P2P clients!\n\nStorage ads are always included automatically.\n\nGenerate enhanced ad blocks in the JS Generator tab.');
        }
        
        function refreshAds() {
            addLog('Refreshing ads from storage and selected clients...', 'info');
            loadLiveAds();
        }
        
        function refreshAllData() {
            addLog('Refreshing all dashboard data (v2.2.0)...', 'info');
            
            connectToCentralServer();
            
            setTimeout(function() {
                scanStorageAds();
            }, 500);
            
            setTimeout(function() {
                scanForClients();
            }, 1000);
            
            setTimeout(function() {
                loadLiveAds();
            }, 2000);
            
            addLog('Enhanced data refresh completed', 'success');
        }
        
        function addLog(message, type) {
            var log = document.getElementById('activityLog');
            if (!log) return;
            
            var timestamp = new Date().toLocaleTimeString();
            var entry = document.createElement('div');
            entry.className = 'log-entry log-' + (type || 'info');
            entry.innerHTML = '<span class="log-timestamp">[' + timestamp + ']</span> <span>' + message + '</span>';
            
            log.appendChild(entry);
            
            while (log.children.length > 100) {
                log.removeChild(log.firstChild);
            }
            
            log.scrollTop = log.scrollHeight;
        }
        
        function showMessage(message, type) {
            var messageDiv = document.getElementById('authMessage');
            if (messageDiv) {
                messageDiv.innerHTML = '<div class="alert alert-' + type + '">' + message + '</div>';
                
                setTimeout(function() {
                    messageDiv.innerHTML = '';
                }, 5000);
            }
        }
        
        // Auto-refresh functionality
        setInterval(function() {
            if (currentUser) {
                fetch('?ajax=heartbeat').catch(function() {
                    // Silent fail for heartbeat
                });
            }
        }, 60000);
        
        // Auto-scan for storage and clients every 5 minutes
        setInterval(function() {
            if (currentUser) {
                scanStorageAds();
                if (availableClients.length === 0) {
                    scanForClients();
                }
            }
        }, 300000);
        
        console.log('PythonCoin P2P Ad Network Developer Portal v2.2.0 initialized successfully');
        console.log('Features: Storage Integration + P2P Network + Enhanced Ad Blocks');
        console.log('Current user:', currentUser);
    </script>
</body>
</html>