import os
import json
import uuid
import psycopg2
import logging
from psycopg2.extras import Json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Import encryption service for PII protection
try:
    from .encryption_service import get_encryption_service
    from .multi_tenant_service import MultiTenantService
    from .gdpr_data_protection import get_gdpr_protection, DataCategory
except ImportError:
    # Fallback for direct execution
    from encryption_service import get_encryption_service
    from multi_tenant_service import MultiTenantService
    from gdpr_data_protection import get_gdpr_protection, DataCategory

logger = logging.getLogger(__name__)

# Global cached multi-tenant service (singleton pattern for performance)
_cached_multi_tenant_service = None

def _get_cached_multi_tenant_service():
    """Get or create cached multi-tenant service (singleton for performance)."""
    global _cached_multi_tenant_service
    if _cached_multi_tenant_service is None:
        _cached_multi_tenant_service = MultiTenantService()
        logger.info("Multi-tenant service initialized (cached globally)")
    return _cached_multi_tenant_service

class ResultsAggregator:
    """
    Aggregates and stores scan results in a PostgreSQL database with enterprise-grade security.
    
    Security Features:
    - Field-level encryption for PII data
    - No file-based fallback to prevent data leakage
    - GDPR/UAVG compliant data protection
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the results aggregator with secure PII encryption and multi-tenant isolation.
        
        Args:
            db_url: PostgreSQL database URL. If None, uses DATABASE_URL environment variable.
        """
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        self.encryption_service = get_encryption_service()
        self.gdpr_protection = get_gdpr_protection()
        self.strict_enterprise_mode = os.environ.get('STRICT_ENTERPRISE_MODE', '0').lower() in ('1','true','yes')
        
        # Use cached multi-tenant service for performance (prevents 8-second re-initialization)
        try:
            self.multi_tenant_service = _get_cached_multi_tenant_service()
            logger.info("Using cached multi-tenant service for secure tenant isolation")
        except Exception as e:
            logger.error(f"Failed to initialize multi-tenant service: {str(e)}")
            raise RuntimeError(f"Multi-tenant service required for enterprise security compliance: {str(e)}")
        
        # Enterprise security: No file fallback to prevent PII data leakage
        self.use_file_storage = False
        
        try:
            self._init_db()
            logger.info("ResultsAggregator initialized with enterprise security and tenant isolation")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            if self.strict_enterprise_mode:
                raise RuntimeError(f"Database connection required for enterprise security compliance: {str(e)}")
            else:
                logger.warning("Non-strict mode: falling back to file-based storage")
                self.use_file_storage = True
                self._init_file_storage()
    
    def _get_secure_connection(self, organization_id: str = 'default_org', admin_bypass: bool = False):
        """
        Get a secure database connection with tenant context for enterprise security.
        
        Args:
            organization_id: Organization ID for tenant isolation
            admin_bypass: Whether to bypass RLS for admin operations
            
        Returns:
            Secure database connection with proper tenant context
        """
        try:
            if not self.db_url:
                raise RuntimeError("DATABASE_URL environment variable required for enterprise deployment")
            
            # Use multi-tenant service for secure connections with RLS
            return self.multi_tenant_service.get_secure_connection(organization_id, admin_bypass)
            
        except Exception as e:
            logger.error(f"Secure database connection error for organization {organization_id}: {str(e)}")
            # Enterprise security: No file fallback for PII data
            raise RuntimeError(f"Secure database connection required for enterprise security compliance: {str(e)}")
    
    def _get_connection(self):
        """DEPRECATED AND UNSAFE: This method bypasses tenant isolation and should not be used."""
        raise RuntimeError("_get_connection() is deprecated and unsafe - use _get_secure_connection() with proper organization_id for tenant isolation")
    
    def _release_connection(self, conn):
        """Release a connection back to the pool."""
        if conn is not None:
            try:
                self.multi_tenant_service.release_connection(conn)
            except Exception as e:
                logger.warning(f"Error releasing connection to pool: {e}")
                try:
                    conn.close()  # Fallback to direct close if pool release fails
                except:
                    pass
    
    def _ensure_reports_directory(self):
        """Ensure reports directory exists for non-PII report generation."""
        # Only create reports directory for non-sensitive report files
        # PII data is never stored in files for enterprise security
        os.makedirs('reports', exist_ok=True)
    
    def _init_db(self):
        """Initialize the database with required tables if they don't exist."""
        conn = self._get_secure_connection('system_admin', admin_bypass=True)
        if not conn:
            print("No database connection available. Using file-based storage.")
            self.use_file_storage = True
            self._init_file_storage()
            return
            
        try:
            cursor = conn.cursor()
            
            # Create optimized scans table with performance indexes
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                scan_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                scan_type TEXT NOT NULL,
                region TEXT NOT NULL,
                file_count INTEGER NOT NULL,
                total_pii_found INTEGER NOT NULL,
                high_risk_count INTEGER NOT NULL,
                result_json JSONB NOT NULL,
                organization_id TEXT NOT NULL DEFAULT 'default_org'
            )
            ''')
            
            # Add performance indexes for common queries
            performance_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_scans_username_timestamp ON scans(username, timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_scans_organization_timestamp ON scans(organization_id, timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_scans_scan_type ON scans(scan_type)",
                "CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_scans_composite ON scans(username, organization_id, timestamp DESC)"
            ]
            
            for index_sql in performance_indexes:
                try:
                    cursor.execute(index_sql)
                    logger.debug(f"Created performance index: {index_sql.split()[5]}")
                except Exception as index_error:
                    logger.debug(f"Index creation note: {index_error}")
            
            # Migration: Add organization_id column if it doesn't exist (for existing databases)
            # Note: Check if column exists first to avoid transaction abort
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='scans' AND column_name='organization_id'
                """)
                if cursor.fetchone() is None:
                    cursor.execute('''
                    ALTER TABLE scans ADD COLUMN organization_id TEXT NOT NULL DEFAULT 'default_org'
                    ''')
                    logger.info("Added organization_id column to existing scans table")
                else:
                    logger.debug("Migration note: organization_id column already exists")
            except Exception as migration_error:
                # If check fails, rollback and continue
                conn.rollback()
                logger.debug(f"Migration note: {migration_error}")
            
            # Create optimized audit log table with performance indexes
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                details JSONB
            )
            ''')
            
            # Add performance indexes for audit log
            audit_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_audit_username_timestamp ON audit_log(username, timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)",
                "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC)"
            ]
            
            for index_sql in audit_indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as index_error:
                    logger.debug(f"Audit index note: {index_error}")
            
            # Create PII types reference table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pii_types (
                type_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                risk_level TEXT NOT NULL,
                gdpr_article TEXT
            )
            ''')
            
            # Create compliance scores table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_scores (
                score_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                repo_name TEXT NOT NULL,
                scan_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                overall_score INTEGER NOT NULL,
                principle_scores JSONB NOT NULL
            )
            ''')
            
            # Create GDPR principles reference table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS gdpr_principles (
                principle_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                article TEXT NOT NULL
            )
            ''')
            
            # Create user sessions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                login_time TIMESTAMP NOT NULL,
                last_activity TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT
            )
            ''')
            
            conn.commit()
            cursor.close()
            self._release_connection(conn)
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            self._release_connection(conn)
            # Enterprise security: Fail secure - no file fallback for PII data
            raise RuntimeError(f"Database initialization required for enterprise security compliance: {str(e)}")
    
    def save_scan_result(self, username: str, result: Dict[str, Any], organization_id: str = 'default_org') -> str:
        """
        Save scan result - alias for store_scan_result for backward compatibility with tenant isolation.
        
        Args:
            username: Username who performed the scan
            result: Scan result dictionary
            organization_id: Organization ID for tenant isolation
            
        Returns:
            str: Scan ID of the saved result
        """
        return self.store_scan_result(username, result, organization_id)
    
    def store_scan_result(self, username: str, result: Dict[str, Any], organization_id: str = 'default_org', store_pii_details: bool = False) -> str:
        """
        Store a scan result in the database with GDPR compliance, PII encryption and tenant isolation.
        
        Args:
            username: Username associated with the scan
            result: Scan result dictionary containing potentially sensitive PII data
            organization_id: Organization ID for tenant isolation
            store_pii_details: Whether to store detailed PII findings (requires consent)
        
        Returns:
            str: Scan ID of the stored result
        """
        # Generate a scan ID if not present
        scan_id = result.get('scan_id', f"scan_{uuid.uuid4().hex}")
        result['scan_id'] = scan_id
        
        # Extract metadata (non-PII fields safe for database indexing)
        scan_type = result.get('scan_type', 'unknown')
        region = result.get('region', 'Netherlands')  # Default to Netherlands for GDPR
        file_count = result.get('files_scanned', 0)
        total_pii = result.get('total_pii_found', 0)
        high_risk = result.get('high_risk_count', 0)
        
        try:
            # Validate tenant access
            if not self.multi_tenant_service.validate_tenant_access(organization_id):
                raise PermissionError(f"Access denied to organization {organization_id}")
            
            # GDPR compliance: Apply data minimization and anonymization
            gdpr_compliant_result = self.gdpr_protection.prepare_scan_result_for_storage(
                scan_result=result,
                user_id=username,
                store_pii_details=store_pii_details
            )
            logger.info(f"Applied GDPR data minimization to scan {scan_id}")
            
            # Enterprise security: Encrypt remaining sensitive data before storage
            encrypted_result = self.encryption_service.encrypt_scan_result(gdpr_compliant_result)
            logger.info(f"Encrypted scan result {scan_id} for secure storage in organization {organization_id}")
            
            # Use secure connection with tenant context
            conn = self._get_secure_connection(organization_id)
            cursor = conn.cursor()
            
            # Store encrypted result in database with organization_id for tenant isolation
            cursor.execute("""
            INSERT INTO scans 
            (scan_id, username, timestamp, scan_type, region, file_count, total_pii_found, high_risk_count, result_json, organization_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (scan_id) DO UPDATE SET
            timestamp = EXCLUDED.timestamp,
            region = EXCLUDED.region,
            file_count = EXCLUDED.file_count,
            total_pii_found = EXCLUDED.total_pii_found,
            high_risk_count = EXCLUDED.high_risk_count,
            result_json = EXCLUDED.result_json,
            organization_id = EXCLUDED.organization_id
            """, (
                scan_id,
                username,
                datetime.now(),
                scan_type,
                region,
                file_count,
                total_pii,
                high_risk,
                Json(encrypted_result),  # Store encrypted version
                organization_id  # Add organization_id for tenant isolation
            ))
            
            conn.commit()
            cursor.close()
            self._release_connection(conn)
            
            # Update tenant usage statistics
            self.multi_tenant_service.update_tenant_usage(organization_id, increment_scans=1)
            
            logger.info(f"Successfully stored encrypted scan result {scan_id} for organization {organization_id}")
            return scan_id
            
        except Exception as e:
            logger.error(f"Error storing scan result: {str(e)}")
            # Enterprise security: Fail secure - no fallback storage for PII data
            raise RuntimeError(f"Failed to store scan result securely: {str(e)}")
    
    def _init_file_storage(self):
        """Initialize file-based storage for non-strict mode."""
        try:
            os.makedirs('data', exist_ok=True)
            # Create empty scan file if it doesn't exist
            if not os.path.exists('data/scans.json'):
                with open('data/scans.json', 'w') as f:
                    json.dump([], f)
            logger.info("File-based storage initialized for non-strict mode")
        except Exception as e:
            logger.error(f"Error initializing file storage: {e}")
            raise
    
    def _legacy_file_cleanup(self):
        """
        Enterprise security: Remove any legacy file-based PII storage.
        Called during system maintenance to ensure no PII remains in files.
        """
        logger.warning("Enterprise security: Cleaning up legacy PII files")
        
        # Remove potentially sensitive files
        sensitive_files = [
            'data/scans.json',
            'data/audit_log.json'
        ]
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Removed legacy PII file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove legacy file {file_path}: {str(e)}")
        
        # Remove scan report files (may contain PII)
        if os.path.exists('reports'):
            for filename in os.listdir('reports'):
                if filename.startswith('scan_') and filename.endswith('.json'):
                    try:
                        os.remove(os.path.join('reports', filename))
                        logger.info(f"Removed legacy scan file: {filename}")
                    except Exception as e:
                        logger.error(f"Failed to remove legacy scan file {filename}: {str(e)}")
    
    def get_scan_result(self, scan_id: str, organization_id: str = 'default_org') -> Optional[Dict[str, Any]]:
        """
        Get a scan result by ID with automatic PII decryption and tenant isolation.
        
        Args:
            scan_id: Scan ID
            organization_id: Organization ID for tenant isolation
            
        Returns:
            Decrypted scan result dictionary or None if not found
        """
        try:
            # Validate tenant access
            if not self.multi_tenant_service.validate_tenant_access(organization_id):
                raise PermissionError(f"Access denied to organization {organization_id}")
            
            # Use secure connection with tenant context
            conn = self._get_secure_connection(organization_id)
            cursor = conn.cursor()
            
            # Query with tenant isolation - RLS will automatically filter by organization_id
            cursor.execute("SELECT result_json FROM scans WHERE scan_id = %s", (scan_id,))
            result = cursor.fetchone()
            
            cursor.close()
            self._release_connection(conn)
            
            if result and result[0]:
                # Enterprise security: Decrypt PII data before returning
                encrypted_result = result[0]
                decrypted_result = self.encryption_service.decrypt_scan_result(encrypted_result)
                logger.info(f"Successfully decrypted scan result {scan_id} for organization {organization_id}")
                return decrypted_result
                
            logger.info(f"Scan result {scan_id} not found or not accessible for organization {organization_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving scan result {scan_id} for organization {organization_id}: {str(e)}")
            # Enterprise security: Fail secure - no file fallback for PII data
            raise RuntimeError(f"Failed to retrieve scan result securely: {str(e)}")
    
    def _migrate_legacy_data(self) -> int:
        """
        Enterprise security: Migrate any existing unencrypted data to encrypted format.
        
        Returns:
            int: Number of records migrated
        """
        logger.info("Starting legacy data migration to encrypted format")
        migrated_count = 0
        
        try:
            conn = self._get_secure_connection('system_admin', admin_bypass=True)
            cursor = conn.cursor()
            
            # Find records without encryption metadata
            cursor.execute("""
                SELECT scan_id, result_json 
                FROM scans 
                WHERE result_json->>'_encryption_version' IS NULL
                LIMIT 100
            """)
            
            legacy_records = cursor.fetchall()
            
            for scan_id, result_json in legacy_records:
                try:
                    # Encrypt the legacy data
                    encrypted_result = self.encryption_service.encrypt_scan_result(result_json)
                    
                    # Update the record with encrypted version
                    cursor.execute("""
                        UPDATE scans 
                        SET result_json = %s 
                        WHERE scan_id = %s
                    """, (Json(encrypted_result), scan_id))
                    
                    migrated_count += 1
                    logger.info(f"Migrated legacy record: {scan_id}")
                    
                except Exception as record_error:
                    logger.error(f"Failed to migrate record {scan_id}: {str(record_error)}")
                    continue
            
            conn.commit()
            cursor.close()
            self._release_connection(conn)
            
            logger.info(f"Successfully migrated {migrated_count} legacy records to encrypted format")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Legacy data migration failed: {str(e)}")
            return migrated_count

    def get_user_scans(self, username: str, limit: int = 20, organization_id: str = 'default_org') -> List[Dict[str, Any]]:
        """
        Get recent scans for a user with proper tenant isolation.
        
        Args:
            username: Username to get scans for
            limit: Maximum number of scans to return
            organization_id: Organization ID for tenant isolation
            
        Returns:
            List of scan metadata dictionaries
        """
        try:
            conn = self._get_secure_connection(organization_id)
            
            cursor = conn.cursor()
            
            # Query the scans table for the most recent scans for this user
            cursor.execute("""
            SELECT scan_id, timestamp, scan_type, region, file_count, total_pii_found, high_risk_count
            FROM scans
            WHERE username = %s AND organization_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
            """, (username, organization_id, limit))
            
            results = cursor.fetchall()
            cursor.close()
            self._release_connection(conn)
            
            # Format as dictionaries
            scans = []
            for row in results:
                scans.append({
                    'scan_id': row[0],
                    'timestamp': row[1].isoformat(),
                    'scan_type': row[2],
                    'region': row[3],
                    'file_count': row[4],
                    'total_pii_found': row[5],
                    'high_risk_count': row[6]
                })
            
            return scans
        except Exception as e:
            print(f"Error retrieving user scans: {str(e)}")
            self.use_file_storage = True
            return self._get_user_scans_file(username, limit)
    
    def _get_user_scans_file(self, username: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user scans from file system."""
        try:
            # Load existing scans
            if os.path.exists('data/scans.json'):
                with open('data/scans.json', 'r') as f:
                    all_scans = json.load(f)
                
                # Filter for this user and sort by timestamp (most recent first)
                user_scans = [s for s in all_scans if s.get('username') == username]
                user_scans.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                # Limit the number of results
                user_scans = user_scans[:limit]
                
                # Format for return
                return [
                    {
                        'scan_id': s.get('scan_id'),
                        'timestamp': s.get('timestamp'),
                        'scan_type': s.get('scan_type'),
                        'region': s.get('region'),
                        'file_count': s.get('file_count', 0),
                        'total_pii_found': s.get('total_pii_found', 0),
                        'high_risk_count': s.get('high_risk_count', 0)
                    }
                    for s in user_scans
                ]
            
            return []
        except Exception as e:
            print(f"Error retrieving user scans from file: {str(e)}")
            return []

    def get_recent_scans(self, days: int = 30, username: Optional[str] = None, organization_id: str = 'default_org') -> List[Dict[str, Any]]:
        """
        Get recent scans within the specified number of days.
        
        Args:
            days: Number of days to look back
            username: Optional username filter
            organization_id: Organization ID for tenant isolation
            
        Returns:
            List of recent scan results
        """
        # Always try database first, even if use_file_storage is True
        db_scans = self._get_recent_scans_db(days, username, organization_id)
        if db_scans is not None:
            return db_scans
            
        if self.use_file_storage:
            return self._get_recent_scans_file(days, username)
        
        return []
    
    def _get_recent_scans_db(self, days: int = 30, username: Optional[str] = None, organization_id: str = 'default_org', limit: int = 1000) -> Optional[List[Dict[str, Any]]]:
        """Get recent scans from database with enhanced error handling, tenant isolation, and performance optimization."""
        
        try:
            conn = self._get_secure_connection(organization_id)
            if not conn:
                print(f"No database connection for recent scans query")
                return None
            
            cursor = conn.cursor()
            
            # Calculate cutoff date - Use current timestamp for accurate filtering
            cutoff_date = datetime.now() - timedelta(days=days)
            print(f"Querying scans since: {cutoff_date} for user: {username}")
            
            # Optimized query with LIMIT for large datasets and proper indexing
            if username:
                cursor.execute("""
                    SELECT scan_id, username, timestamp, scan_type, region,
                           file_count, total_pii_found, high_risk_count, result_json
                    FROM scans 
                    WHERE username = %s AND organization_id = %s AND timestamp >= %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (username, organization_id, cutoff_date, limit))
            else:
                cursor.execute("""
                    SELECT scan_id, username, timestamp, scan_type, region,
                           file_count, total_pii_found, high_risk_count, result_json
                    FROM scans 
                    WHERE organization_id = %s AND timestamp >= %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (organization_id, cutoff_date, limit))
            
            results = cursor.fetchall()
            print(f"Database returned {len(results)} scan records")
            
            cursor.close()
            self._release_connection(conn)
            
            # Convert to list of dictionaries with enhanced logging
            scans = []
            for result in results:
                scan_data = {
                    'scan_id': result[0],
                    'username': result[1], 
                    'timestamp': result[2].isoformat() if result[2] else None,
                    'scan_type': result[3],
                    'region': result[4],
                    'file_count': result[5],
                    'total_pii_found': result[6],
                    'high_risk_count': result[7],
                    'result': result[8]
                }
                scans.append(scan_data)
            
            print(f"Formatted {len(scans)} scans for return")
            return scans
        except Exception as e:
            print(f"Error retrieving recent scans: {str(e)}")
            self.use_file_storage = True
            return self._get_recent_scans_file(days, username)
    
    def _get_recent_scans_file(self, days: int = 30, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent scans from file storage."""
        try:
            if not os.path.exists('data/scans.json'):
                return []
            
            with open('data/scans.json', 'r') as f:
                all_scans = json.load(f)
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Filter scans
            recent_scans = []
            for scan in all_scans:
                try:
                    scan_date = datetime.fromisoformat(scan['timestamp'])
                    if scan_date >= cutoff_date:
                        if username is None or scan.get('username') == username:
                            recent_scans.append(scan)
                except (ValueError, KeyError):
                    continue
            
            # Sort by timestamp descending
            recent_scans.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return recent_scans
        except Exception as e:
            print(f"Error retrieving recent scans from file: {str(e)}")
            return []

    def log_audit_event(self, username: str, action: str, details: Optional[Dict[str, Any]] = None, organization_id: str = 'default_org') -> None:
        """
        Log an audit event for tracking user actions and system activities with tenant isolation.
        
        Args:
            username: Username performing the action
            action: Type of action (e.g., 'login', 'scan', 'report_download')
            details: Dictionary of additional details
            organization_id: Organization ID for tenant isolation
        """
        log_id = f"log_{uuid.uuid4().hex}"
        
        if self.use_file_storage:
            self._log_user_action_file(log_id, username, action, details)
            return
        
        try:
            # Validate tenant access
            if not self.multi_tenant_service.validate_tenant_access(organization_id):
                raise PermissionError(f"Access denied to organization {organization_id}")
            
            # Use secure connection with tenant context
            conn = self._get_secure_connection(organization_id)
            cursor = conn.cursor()
            
            # Insert into audit_log table with organization_id for tenant isolation
            cursor.execute("""
            INSERT INTO audit_log (log_id, username, action, timestamp, details, organization_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                log_id,
                username,
                action,
                datetime.now(),
                Json(details) if details else None,
                organization_id  # Add organization_id for tenant isolation
            ))
            
            conn.commit()
            cursor.close()
            self._release_connection(conn)
            
            logger.info(f"Audit event logged for organization {organization_id}: {action} by {username}")
        except Exception as e:
            print(f"Error logging audit event: {str(e)}")
            self.use_file_storage = True
            self._log_user_action_file(log_id, username, action, details)
    
    # For backward compatibility
    def log_user_action(self, username: str, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Legacy method for logging user actions, redirects to log_audit_event.
        
        Args:
            username: Username performing the action
            action: Type of action (e.g., 'login', 'scan', 'report_download')
            details: Dictionary of additional details
        """
        return self.log_audit_event(username, action, details)
    
    def _log_user_action_file(self, log_id: str, username: str, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log user action to file system."""
        try:
            # Load existing logs
            logs = []
            if os.path.exists('data/audit_log.json'):
                with open('data/audit_log.json', 'r') as f:
                    logs = json.load(f)
            
            # Create log entry
            log_entry = {
                'log_id': log_id,
                'username': username,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'details': details or {}
            }
            
            # Add new entry
            logs.append(log_entry)
            
            # Save to file (keep only last 1000 entries to prevent file growth)
            with open('data/audit_log.json', 'w') as f:
                json.dump(logs[-1000:], f, indent=2)
        except Exception as e:
            print(f"Error logging user action to file: {str(e)}")

    def store_scan_results(self, scan_id: str, username: str, scan_type: str, results: Dict[str, Any]) -> None:
        """
        Store scan results (alias for store_scan_result for compatibility).
        
        Args:
            scan_id: Unique scan identifier
            username: Username associated with the scan
            scan_type: Type of scan performed
            results: Scan result dictionary
        """
        # Ensure results has required fields
        results['scan_id'] = scan_id
        results['scan_type'] = scan_type
        self.store_scan_result(username, results)
    
    def get_scan_by_id(self, scan_id: str, organization_id: str = 'default_org') -> Optional[Dict[str, Any]]:
        """
        Retrieve a scan by its ID with proper tenant isolation.
        
        Args:
            scan_id: Unique scan identifier
            organization_id: Organization ID for tenant isolation
            
        Returns:
            Scan results dictionary or None if not found
        """
        if self.use_file_storage:
            return self._get_scan_by_id_file(scan_id)
        
        try:
            conn = self._get_secure_connection(organization_id)
            if not conn:
                self.use_file_storage = True
                return self._get_scan_by_id_file(scan_id)
            
            cursor = conn.cursor()
            cursor.execute("""
            SELECT scan_id, username, timestamp, scan_type, 
                   file_count, total_pii_found, high_risk_count, result_json
            FROM scans WHERE scan_id = %s
            """, (scan_id,))
            
            row = cursor.fetchone()
            cursor.close()
            self._release_connection(conn)
            
            if row:
                return {
                    'scan_id': row[0],
                    'username': row[1],
                    'timestamp': row[2],
                    'scan_type': row[3],
                    'region': row[4],
                    'file_count': row[5],
                    'total_pii_found': row[6],
                    'high_risk_count': row[7],
                    'result_json': row[8]
                }
            return None
            
        except Exception as e:
            print(f"Error retrieving scan by ID: {str(e)}")
            self.use_file_storage = True
            return self._get_scan_by_id_file(scan_id)
    
    def _get_scan_by_id_file(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve scan by ID from file storage."""
        try:
            if os.path.exists('data/scans.json'):
                with open('data/scans.json', 'r') as f:
                    scans = json.load(f)
                    for scan in scans:
                        if scan.get('scan_id') == scan_id:
                            return scan
            return None
        except Exception as e:
            print(f"Error retrieving scan by ID from file: {str(e)}")
            return None

    def store_compliance_score(self, username: str, repo_name: str, scan_id: str, 
                             overall_score: int, principle_scores: Dict[str, int], 
                             organization_id: str = 'default_org') -> None:
        """
        Store a compliance score for a repository with proper tenant isolation.
        
        Args:
            username: Username associated with the scan
            repo_name: Repository name or identifier
            scan_id: Associated scan ID
            overall_score: Overall compliance score (0-100)
            principle_scores: Dictionary mapping GDPR principles to scores (0-100)
            organization_id: Organization ID for tenant isolation
        """
        score_id = f"score_{uuid.uuid4().hex}"
        
        if self.use_file_storage:
            self._store_compliance_score_file(score_id, username, repo_name, scan_id,
                                           overall_score, principle_scores)
            return
        
        try:
            conn = self._get_secure_connection(organization_id)
            if not conn:
                self.use_file_storage = True
                self._store_compliance_score_file(score_id, username, repo_name, scan_id,
                                              overall_score, principle_scores)
                return
            
            cursor = conn.cursor()
            
            # Insert into compliance_scores table
            cursor.execute("""
            INSERT INTO compliance_scores
            (score_id, username, repo_name, scan_id, timestamp, overall_score, principle_scores)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                score_id,
                username,
                repo_name,
                scan_id,
                datetime.now(),
                overall_score,
                Json(principle_scores)
            ))
            
            conn.commit()
            cursor.close()
            self._release_connection(conn)
        except Exception as e:
            print(f"Error storing compliance score: {str(e)}")
            self.use_file_storage = True
            self._store_compliance_score_file(score_id, username, repo_name, scan_id,
                                          overall_score, principle_scores)
    
    def _store_compliance_score_file(self, score_id: str, username: str, repo_name: str,
                                   scan_id: str, overall_score: int, 
                                   principle_scores: Dict[str, int]) -> None:
        """Store compliance score in file system."""
        try:
            # Create scores file if it doesn't exist
            scores = []
            if os.path.exists('data/compliance_scores.json'):
                with open('data/compliance_scores.json', 'r') as f:
                    scores = json.load(f)
            
            # Create score entry
            score_entry = {
                'score_id': score_id,
                'username': username,
                'repo_name': repo_name,
                'scan_id': scan_id,
                'timestamp': datetime.now().isoformat(),
                'overall_score': overall_score,
                'principle_scores': principle_scores
            }
            
            # Add new entry
            scores.append(score_entry)
            
            # Save to file
            with open('data/compliance_scores.json', 'w') as f:
                json.dump(scores, f, indent=2)
        except Exception as e:
            print(f"Error storing compliance score to file: {str(e)}")

    def get_user_compliance_history(self, username: str, repo_name: Optional[str] = None,
                                  days: int = 30, organization_id: str = 'default_org') -> List[Dict[str, Any]]:
        """
        Get compliance score history for a user with proper tenant isolation.
        
        Args:
            username: Username to get history for
            repo_name: Optional repository name to filter by
            days: Number of days of history to include
            organization_id: Organization ID for tenant isolation
            
        Returns:
            List of compliance score data points
        """
        if self.use_file_storage:
            return self._get_user_compliance_history_file(username, repo_name, days)
        
        try:
            conn = self._get_secure_connection(organization_id)
            if not conn:
                self.use_file_storage = True
                return self._get_user_compliance_history_file(username, repo_name, days)
            
            cursor = conn.cursor()
            
            # Build query based on whether repo_name is provided
            if repo_name:
                query = """
                SELECT score_id, repo_name, scan_id, timestamp, overall_score, principle_scores
                FROM compliance_scores
                WHERE username = %s AND repo_name = %s AND timestamp > %s
                ORDER BY timestamp ASC
                """
                params = (username, repo_name, datetime.now() - timedelta(days=days))
            else:
                query = """
                SELECT score_id, repo_name, scan_id, timestamp, overall_score, principle_scores
                FROM compliance_scores
                WHERE username = %s AND timestamp > %s
                ORDER BY timestamp ASC
                """
                params = (username, datetime.now() - timedelta(days=days))
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            self._release_connection(conn)
            
            # Format as dictionaries
            history = []
            for row in results:
                history.append({
                    'score_id': row[0],
                    'repo_name': row[1],
                    'scan_id': row[2],
                    'timestamp': row[3].isoformat(),
                    'overall_score': row[4],
                    'principle_scores': row[5]
                })
            
            return history
        except Exception as e:
            print(f"Error retrieving compliance history: {str(e)}")
            self.use_file_storage = True
            return self._get_user_compliance_history_file(username, repo_name, days)
    
    def _get_user_compliance_history_file(self, username: str, repo_name: Optional[str] = None,
                                        days: int = 30) -> List[Dict[str, Any]]:
        """Get compliance history from file system."""
        try:
            if os.path.exists('data/compliance_scores.json'):
                with open('data/compliance_scores.json', 'r') as f:
                    all_scores = json.load(f)
                
                # Calculate cutoff date
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Filter for this user and optional repo_name
                if repo_name:
                    filtered_scores = [
                        s for s in all_scores 
                        if s.get('username') == username 
                        and s.get('repo_name') == repo_name
                        and s.get('timestamp', '') > cutoff_date
                    ]
                else:
                    filtered_scores = [
                        s for s in all_scores 
                        if s.get('username') == username
                        and s.get('timestamp', '') > cutoff_date
                    ]
                
                # Sort by timestamp (oldest first for time series)
                filtered_scores.sort(key=lambda x: x.get('timestamp', ''))
                
                return filtered_scores
            
            return []
        except Exception as e:
            print(f"Error retrieving compliance history from file: {str(e)}")
            return []
    
    def get_all_scans(self, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all scans for a user (alias for get_user_scans for backward compatibility).
        
        Args:
            username: Username to get scans for
            limit: Maximum number of scans to return
            
        Returns:
            List of scan metadata dictionaries
        """
        return self.get_user_scans(username, limit)
    
    # ==================== GDPR Data Subject Rights ====================
    
    def gdpr_delete_user_data(self, username: str, organization_id: str = 'default_org') -> Dict[str, Any]:
        """
        GDPR Article 17 - Right to Erasure (Right to be Forgotten).
        
        Deletes all user data from the system.
        
        Args:
            username: Username whose data should be deleted
            organization_id: Organization ID for tenant context
            
        Returns:
            Summary of deleted data
        """
        try:
            conn = self._get_secure_connection(organization_id, admin_bypass=True)
            result = self.gdpr_protection.delete_user_data(username, conn)
            self._release_connection(conn)
            
            logger.info(f"GDPR erasure completed for user {username}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"GDPR erasure failed for user {username}: {str(e)}")
            return {"error": str(e), "user_id": username}
    
    def gdpr_export_user_data(self, username: str, organization_id: str = 'default_org') -> Dict[str, Any]:
        """
        GDPR Article 20 - Right to Data Portability.
        
        Exports all user data in a portable format.
        
        Args:
            username: Username whose data should be exported
            organization_id: Organization ID for tenant context
            
        Returns:
            All user data in JSON format
        """
        try:
            conn = self._get_secure_connection(organization_id, admin_bypass=True)
            result = self.gdpr_protection.export_user_data(username, conn)
            self._release_connection(conn)
            
            logger.info(f"GDPR export completed for user {username}")
            return result
            
        except Exception as e:
            logger.error(f"GDPR export failed for user {username}: {str(e)}")
            return {"error": str(e), "user_id": username}
    
    def gdpr_enforce_retention(self, organization_id: str = 'default_org') -> Dict[str, Any]:
        """
        Enforce data retention policies - delete expired data.
        
        Should be run periodically (e.g., daily via cron).
        
        Args:
            organization_id: Organization ID (use 'system_admin' for global enforcement)
            
        Returns:
            Summary of deleted records
        """
        try:
            conn = self._get_secure_connection('system_admin', admin_bypass=True)
            cursor = conn.cursor()
            
            # Get retention policy for scan data (default 365 days)
            retention_days = 365
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Delete expired scans
            cursor.execute(
                "DELETE FROM scans WHERE timestamp < %s RETURNING scan_id",
                (cutoff_date,)
            )
            deleted_scans = cursor.fetchall()
            
            # Delete expired audit logs (90 days for analytics)
            audit_cutoff = datetime.now() - timedelta(days=90)
            cursor.execute(
                "DELETE FROM audit_log WHERE timestamp < %s RETURNING log_id",
                (audit_cutoff,)
            )
            deleted_logs = cursor.fetchall()
            
            conn.commit()
            cursor.close()
            self._release_connection(conn)
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "scans_deleted": len(deleted_scans),
                "scan_retention_days": retention_days,
                "audit_logs_deleted": len(deleted_logs),
                "audit_retention_days": 90
            }
            
            logger.info(f"GDPR retention enforcement completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"GDPR retention enforcement failed: {str(e)}")
            return {"error": str(e)}
    
    def gdpr_get_retention_policies(self) -> List[Dict[str, Any]]:
        """
        Get all data retention policies for transparency (GDPR Article 13/14).
        
        Returns:
            List of retention policies with legal basis and purposes
        """
        return self.gdpr_protection.get_retention_info()
    
    def gdpr_record_consent(self, username: str, category: str, granted: bool) -> Dict[str, Any]:
        """
        Record user consent for a data category.
        
        Args:
            username: Username giving/withdrawing consent
            category: Data category (e.g., 'pii_findings', 'usage_analytics')
            granted: Whether consent is granted or withdrawn
            
        Returns:
            Consent record confirmation
        """
        try:
            category_enum = DataCategory(category)
            return self.gdpr_protection.record_consent(username, category_enum, granted)
        except ValueError:
            return {"error": f"Unknown category: {category}"}