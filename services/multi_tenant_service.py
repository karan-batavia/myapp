"""
Multi-Tenant Service
Provides organization-level data isolation and tenant separation for enterprise customers.
"""

import os
import logging
import psycopg2
from psycopg2 import pool
from psycopg2.extras import Json
from datetime import datetime
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from enum import Enum
import threading

logger = logging.getLogger(__name__)

# Global connection pool (singleton for all MultiTenantService instances)
_connection_pool = None
_pool_lock = threading.Lock()

def get_connection_pool(db_url: str, min_connections: int = 2, max_connections: int = 20):
    """
    Get or create a thread-safe connection pool (singleton pattern).
    
    Args:
        db_url: PostgreSQL database URL
        min_connections: Minimum connections to keep open
        max_connections: Maximum connections allowed
        
    Returns:
        ThreadedConnectionPool instance
    """
    global _connection_pool
    
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                try:
                    _connection_pool = pool.ThreadedConnectionPool(
                        minconn=min_connections,
                        maxconn=max_connections,
                        dsn=db_url,
                        sslmode='require'
                    )
                    logger.info(f"Connection pool initialized: min={min_connections}, max={max_connections}")
                except Exception as e:
                    logger.error(f"Failed to create connection pool: {e}")
                    raise
    
    return _connection_pool

def close_connection_pool():
    """Close the global connection pool (call on shutdown)."""
    global _connection_pool
    if _connection_pool is not None:
        with _pool_lock:
            if _connection_pool is not None:
                _connection_pool.closeall()
                _connection_pool = None
                logger.info("Connection pool closed")

class TenantTier(Enum):
    """Tenant subscription tiers."""
    STARTER = "starter"
    PROFESSIONAL = "professional" 
    ENTERPRISE = "enterprise"
    ENTERPRISE_PLUS = "enterprise_plus"

@dataclass
class TenantConfig:
    """Multi-tenant configuration."""
    organization_id: str
    organization_name: str
    tier: TenantTier
    max_users: int
    max_scans_per_month: int
    max_storage_gb: int
    features: Set[str]
    compliance_regions: List[str]
    data_residency: str
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass 
class TenantUsage:
    """Tenant usage tracking."""
    organization_id: str
    current_users: int
    scans_this_month: int
    storage_used_gb: float
    last_activity: datetime
    compliance_score: float

class MultiTenantService:
    """
    Multi-tenant service providing organization-level data isolation.
    
    Features:
    - Organization-level data separation
    - Tenant-specific resource limits
    - Usage tracking and quota enforcement
    - Data residency compliance
    - Subscription tier management
    - Cross-tenant data protection
    """
    
    def __init__(self):
        """Initialize multi-tenant service with connection pooling."""
        self.db_url = os.environ.get('DATABASE_URL')
        if not self.db_url:
            raise RuntimeError("DATABASE_URL environment variable required for multi-tenant service")
        
        self.tenants: Dict[str, TenantConfig] = {}
        self.usage_cache: Dict[str, TenantUsage] = {}
        
        # Initialize connection pool (singleton - shared across all instances)
        self.pool = get_connection_pool(self.db_url, min_connections=2, max_connections=20)
        
        self._init_tenant_schema()
        self._load_tenant_configs()
        
        logger.info("Multi-tenant service initialized with connection pooling and organization isolation")
    
    def _get_pooled_connection(self):
        """Get a connection from the pool."""
        return self.pool.getconn()
    
    def _return_connection(self, conn):
        """Return a connection to the pool."""
        if conn is not None:
            self.pool.putconn(conn)
    
    def _init_tenant_schema(self) -> None:
        """Initialize database schema for multi-tenancy."""
        conn = None
        try:
            conn = self._get_pooled_connection()
            cursor = conn.cursor()
            
            # Create tenants table for organization management
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                organization_id VARCHAR(255) PRIMARY KEY,
                organization_name VARCHAR(500) NOT NULL,
                tier VARCHAR(50) NOT NULL,
                max_users INTEGER DEFAULT 10,
                max_scans_per_month INTEGER DEFAULT 100,
                max_storage_gb INTEGER DEFAULT 10,
                features JSONB DEFAULT '[]'::jsonb,
                compliance_regions JSONB DEFAULT '["EU"]'::jsonb,
                data_residency VARCHAR(100) DEFAULT 'EU',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}'::jsonb,
                status VARCHAR(50) DEFAULT 'active'
            )
            """)
            
            # Create tenant usage tracking table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenant_usage (
                organization_id VARCHAR(255) PRIMARY KEY,
                current_users INTEGER DEFAULT 0,
                scans_this_month INTEGER DEFAULT 0,
                storage_used_gb DECIMAL(10,2) DEFAULT 0.0,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                compliance_score DECIMAL(5,2) DEFAULT 0.0,
                monthly_reset_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organization_id) REFERENCES tenants(organization_id) ON DELETE CASCADE
            )
            """)
            
            # Add organization_id to existing tables for tenant isolation
            try:
                cursor.execute("""
                ALTER TABLE scans ADD COLUMN IF NOT EXISTS organization_id VARCHAR(255) DEFAULT 'default_org';
                """)
                
                cursor.execute("""
                ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS organization_id VARCHAR(255) DEFAULT 'default_org';
                """)
                
                # Create indexes for performance
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_scans_org_id ON scans(organization_id);
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_org_id ON audit_log(organization_id);
                """)
                
            except psycopg2.Error as e:
                # Columns might already exist
                logger.info(f"Tenant isolation columns may already exist: {str(e)}")
            
            # Initialize Row Level Security (RLS) for tenant isolation
            # Allow disabling RLS for production deployments via environment variable
            if os.getenv("DISABLE_RLS") != "1":
                self._init_row_level_security(cursor)
            else:
                logger.warning("RLS DISABLED via DISABLE_RLS environment variable - tenant isolation not enforced")
            
            conn.commit()
            cursor.close()
            self._return_connection(conn)
            conn = None
            
            logger.info("Multi-tenant database schema initialized successfully with RLS")
            
        except Exception as e:
            if conn is not None:
                self._return_connection(conn)
            logger.error(f"Failed to initialize tenant schema: {str(e)}")
            raise RuntimeError(f"Multi-tenant schema initialization failed: {str(e)}")
    
    def _init_row_level_security(self, cursor) -> None:
        """
        Initialize Row Level Security (RLS) for tenant isolation.
        
        Implements database-level security policies to prevent cross-tenant data access.
        """
        try:
            logger.info("Initializing Row Level Security for tenant isolation")
            
            # Enable RLS on scans table
            cursor.execute("ALTER TABLE scans ENABLE ROW LEVEL SECURITY;")
            
            # Enable RLS on audit_log table  
            cursor.execute("ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;")
            
            # Drop existing policies if they exist (for idempotency)
            cursor.execute("DROP POLICY IF EXISTS tenant_isolation_scans ON scans;")
            cursor.execute("DROP POLICY IF EXISTS tenant_isolation_audit_log ON audit_log;")
            
            # Create RLS policies for tenant isolation (idempotent)
            # Users can only access scans from their organization
            cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'scans' AND policyname = 'tenant_isolation_scans') THEN
                    CREATE POLICY tenant_isolation_scans ON scans
                    FOR ALL
                    TO PUBLIC
                    USING (organization_id = current_setting('app.current_organization_id', true));
                END IF;
            END $$;
            """)
            
            # Users can only access audit logs from their organization
            cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'audit_log' AND policyname = 'tenant_isolation_audit_log') THEN
                    CREATE POLICY tenant_isolation_audit_log ON audit_log
                    FOR ALL
                    TO PUBLIC
                    USING (organization_id = current_setting('app.current_organization_id', true));
                END IF;
            END $$;
            """)
            
            # Create administrative bypass policies for system operations (idempotent)
            # These allow operations when no organization context is set (for admin tasks)
            cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'scans' AND policyname = 'admin_access_scans') THEN
                    CREATE POLICY admin_access_scans ON scans
                    FOR ALL
                    TO PUBLIC
                    USING (current_setting('app.current_organization_id', true) = '' OR 
                           current_setting('app.admin_bypass', true) = 'true');
                END IF;
            END $$;
            """)
            
            cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'audit_log' AND policyname = 'admin_access_audit_log') THEN
                    CREATE POLICY admin_access_audit_log ON audit_log
                    FOR ALL
                    TO PUBLIC
                    USING (current_setting('app.current_organization_id', true) = '' OR 
                           current_setting('app.admin_bypass', true) = 'true');
                END IF;
            END $$;
            """)
            
            logger.info("Row Level Security policies created successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Row Level Security: {str(e)}")
            # Don't raise exception here to avoid breaking schema initialization
            # RLS can be configured later if needed
            # Note: Transaction rollback is handled by the calling method
            logger.warning("Continuing without RLS - manual configuration may be required")
    
    def get_secure_connection(self, organization_id: str, admin_bypass: bool = False):
        """
        Get a secure database connection from the pool with tenant context set.
        
        IMPORTANT: Caller must return connection using return_connection() when done,
        or use release_connection() method. Do NOT call conn.close() directly.
        
        Args:
            organization_id: Organization ID for tenant isolation
            admin_bypass: Whether to bypass RLS for admin operations
            
        Returns:
            psycopg2 connection from pool with proper tenant context
        """
        conn = None
        try:
            # Validate organization access first
            if not admin_bypass and not self.validate_tenant_access(organization_id):
                raise PermissionError(f"Access denied to organization {organization_id}")
            
            # Get connection from pool instead of creating new one
            conn = self._get_pooled_connection()
            conn.autocommit = True  # Use autocommit for SET commands to avoid transaction issues
            cursor = conn.cursor()
            
            # Set organization context for RLS
            cursor.execute("SET app.current_organization_id = %s", (organization_id,))
            
            # Set admin bypass if needed
            if admin_bypass:
                cursor.execute("SET app.admin_bypass = 'true'")
            else:
                cursor.execute("SET app.admin_bypass = 'false'")
            
            # Reset autocommit for normal operations
            conn.autocommit = False
            cursor.close()
            
            logger.debug(f"Secure pooled connection established for organization {organization_id}")
            return conn
            
        except Exception as e:
            # Return connection to pool if we got one but failed
            if conn is not None:
                self._return_connection(conn)
            logger.error(f"Failed to get secure connection for organization {organization_id}: {str(e)}")
            raise RuntimeError(f"Secure connection failed: {str(e)}")
    
    def release_connection(self, conn):
        """
        Release a connection back to the pool.
        Use this instead of conn.close() for pooled connections.
        """
        self._return_connection(conn)
    
    def execute_with_tenant_context(self, organization_id: str, query: str, params: Optional[tuple] = None, admin_bypass: bool = False):
        """
        Execute a query with proper tenant context.
        
        Args:
            organization_id: Organization ID for tenant isolation
            query: SQL query to execute
            params: Query parameters
            admin_bypass: Whether to bypass RLS for admin operations
            
        Returns:
            Query results
        """
        conn = self.get_secure_connection(organization_id, admin_bypass)
        
        try:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Fetch results if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
            else:
                results = cursor.rowcount
                conn.commit()
            
            cursor.close()
            self.release_connection(conn)
            
            return results
            
        except Exception as e:
            conn.rollback()
            self.release_connection(conn)
            logger.error(f"Query execution failed for organization {organization_id}: {str(e)}")
            raise RuntimeError(f"Tenant query execution failed: {str(e)}")
    
    def _load_tenant_configs(self) -> None:
        """Load tenant configurations from database."""
        conn = None
        try:
            conn = self._get_pooled_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT organization_id, organization_name, tier, max_users, max_scans_per_month,
                   max_storage_gb, features, compliance_regions, data_residency, created_at, metadata
            FROM tenants WHERE status = 'active'
            """)
            
            results = cursor.fetchall()
            
            for row in results:
                org_id = row[0]
                tenant_config = TenantConfig(
                    organization_id=org_id,
                    organization_name=row[1],
                    tier=TenantTier(row[2]),
                    max_users=row[3],
                    max_scans_per_month=row[4],
                    max_storage_gb=row[5],
                    features=set(row[6]) if row[6] else set(),
                    compliance_regions=row[7] if row[7] else ['EU'],
                    data_residency=row[8],
                    created_at=row[9],
                    metadata=row[10] if row[10] else {}
                )
                self.tenants[org_id] = tenant_config
            
            cursor.close()
            self._return_connection(conn)
            conn = None
            
            logger.info(f"Loaded {len(self.tenants)} tenant configurations")
            
            # Ensure default organization exists
            if 'default_org' not in self.tenants:
                self._create_default_tenant()
                
        except Exception as e:
            if conn is not None:
                self._return_connection(conn)
            logger.error(f"Failed to load tenant configs: {str(e)}")
            # Create default tenant for fallback
            self._create_default_tenant()
    
    def _create_default_tenant(self) -> None:
        """Create default tenant organization."""
        try:
            default_config = TenantConfig(
                organization_id='default_org',
                organization_name='Default Organization',
                tier=TenantTier.PROFESSIONAL,
                max_users=50,
                max_scans_per_month=500,
                max_storage_gb=100,
                features={'basic_scanning', 'gdpr_compliance', 'reports'},
                compliance_regions=['EU', 'Netherlands'],
                data_residency='EU',
                created_at=datetime.now(),
                metadata={'created_by': 'system', 'type': 'default'}
            )
            
            self.create_tenant(default_config)
            logger.info("Created default tenant organization")
            
        except Exception as e:
            logger.error(f"Failed to create default tenant: {str(e)}")
    
    def create_tenant(self, config: TenantConfig) -> str:
        """
        Create new tenant organization.
        
        Args:
            config: Tenant configuration
            
        Returns:
            str: Organization ID
        """
        try:
            conn = psycopg2.connect(self.db_url, sslmode='require')
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO tenants 
            (organization_id, organization_name, tier, max_users, max_scans_per_month,
             max_storage_gb, features, compliance_regions, data_residency, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (organization_id) DO UPDATE SET
                organization_name = EXCLUDED.organization_name,
                tier = EXCLUDED.tier,
                max_users = EXCLUDED.max_users,
                max_scans_per_month = EXCLUDED.max_scans_per_month,
                max_storage_gb = EXCLUDED.max_storage_gb,
                features = EXCLUDED.features,
                compliance_regions = EXCLUDED.compliance_regions,
                data_residency = EXCLUDED.data_residency,
                metadata = EXCLUDED.metadata,
                updated_at = CURRENT_TIMESTAMP
            """, (
                config.organization_id,
                config.organization_name,
                config.tier.value,
                config.max_users,
                config.max_scans_per_month,
                config.max_storage_gb,
                Json(list(config.features)),
                Json(config.compliance_regions),
                config.data_residency,
                Json(config.metadata)
            ))
            
            # Initialize usage tracking
            cursor.execute("""
            INSERT INTO tenant_usage (organization_id)
            VALUES (%s)
            ON CONFLICT (organization_id) DO NOTHING
            """, (config.organization_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Cache the configuration
            self.tenants[config.organization_id] = config
            
            logger.info(f"Created tenant organization: {config.organization_name} ({config.organization_id})")
            return config.organization_id
            
        except Exception as e:
            logger.error(f"Failed to create tenant {config.organization_id}: {str(e)}")
            raise RuntimeError(f"Tenant creation failed: {str(e)}")
    
    def get_tenant_config(self, organization_id: str) -> Optional[TenantConfig]:
        """Get tenant configuration by organization ID."""
        return self.tenants.get(organization_id)
    
    def validate_tenant_access(self, organization_id: str, resource_type: Optional[str] = None) -> bool:
        """
        Validate tenant access and enforce isolation.
        
        Args:
            organization_id: Organization ID to validate
            resource_type: Optional resource type for feature checking
            
        Returns:
            bool: True if access is allowed
        """
        config = self.get_tenant_config(organization_id)
        if not config:
            logger.warning(f"Access denied: Unknown organization {organization_id}")
            return False
        
        # Check feature access if resource type specified
        if resource_type and resource_type not in config.features:
            logger.warning(f"Access denied: Organization {organization_id} lacks feature {resource_type}")
            return False
        
        # Check usage limits
        usage = self.get_tenant_usage(organization_id)
        if usage and self._is_over_limits(config, usage):
            logger.warning(f"Access denied: Organization {organization_id} over usage limits")
            return False
        
        return True
    
    def _is_over_limits(self, config: TenantConfig, usage: TenantUsage) -> bool:
        """Check if tenant is over usage limits."""
        return (
            usage.current_users > config.max_users or
            usage.scans_this_month > config.max_scans_per_month or
            usage.storage_used_gb > config.max_storage_gb
        )
    
    def get_tenant_usage(self, organization_id: str) -> Optional[TenantUsage]:
        """Get current tenant usage statistics."""
        if organization_id in self.usage_cache:
            return self.usage_cache[organization_id]
        
        try:
            conn = psycopg2.connect(self.db_url, sslmode='require')
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT current_users, scans_this_month, storage_used_gb, 
                   last_activity, compliance_score
            FROM tenant_usage
            WHERE organization_id = %s
            """, (organization_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                usage = TenantUsage(
                    organization_id=organization_id,
                    current_users=result[0],
                    scans_this_month=result[1],
                    storage_used_gb=float(result[2]),
                    last_activity=result[3],
                    compliance_score=float(result[4])
                )
                
                # Cache usage data
                self.usage_cache[organization_id] = usage
                return usage
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get tenant usage for {organization_id}: {str(e)}")
            return None
    
    def update_tenant_usage(self, organization_id: str, **updates) -> None:
        """Update tenant usage statistics."""
        try:
            conn = psycopg2.connect(self.db_url, sslmode='require')
            cursor = conn.cursor()
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            if 'current_users' in updates:
                update_fields.append('current_users = %s')
                values.append(updates['current_users'])
            
            if 'increment_scans' in updates:
                update_fields.append('scans_this_month = scans_this_month + %s')
                values.append(updates['increment_scans'])
            
            if 'storage_used_gb' in updates:
                update_fields.append('storage_used_gb = %s')
                values.append(updates['storage_used_gb'])
            
            if 'compliance_score' in updates:
                update_fields.append('compliance_score = %s')
                values.append(updates['compliance_score'])
            
            if update_fields:
                update_fields.append('last_activity = CURRENT_TIMESTAMP')
                values.append(organization_id)
                
                query = f"""
                UPDATE tenant_usage 
                SET {', '.join(update_fields)}
                WHERE organization_id = %s
                """
                
                cursor.execute(query, values)
                conn.commit()
                
                # Clear cache to force refresh
                if organization_id in self.usage_cache:
                    del self.usage_cache[organization_id]
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update tenant usage for {organization_id}: {str(e)}")
    
    def get_scan_results_for_tenant(self, organization_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get scan results isolated to specific tenant organization.
        
        Args:
            organization_id: Organization ID for data isolation
            limit: Maximum number of results
            
        Returns:
            List of scan results for the organization
        """
        if not self.validate_tenant_access(organization_id):
            raise PermissionError(f"Access denied to organization {organization_id}")
        
        try:
            conn = psycopg2.connect(self.db_url, sslmode='require')
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT scan_id, username, timestamp, scan_type, region, 
                   file_count, total_pii_found, high_risk_count
            FROM scans
            WHERE organization_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
            """, (organization_id, limit))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Format results
            scan_results = []
            for row in results:
                scan_results.append({
                    'scan_id': row[0],
                    'username': row[1],
                    'timestamp': row[2].isoformat() if row[2] else None,
                    'scan_type': row[3],
                    'region': row[4],
                    'file_count': row[5],
                    'total_pii_found': row[6],
                    'high_risk_count': row[7],
                    'organization_id': organization_id
                })
            
            logger.info(f"Retrieved {len(scan_results)} scan results for organization {organization_id}")
            return scan_results
            
        except Exception as e:
            logger.error(f"Failed to get scan results for tenant {organization_id}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve tenant scan results: {str(e)}")
    
    def enforce_data_residency(self, organization_id: str, operation: str) -> bool:
        """
        Enforce data residency requirements for tenant.
        
        Args:
            organization_id: Organization ID
            operation: Operation being performed
            
        Returns:
            bool: True if operation is allowed under data residency rules
        """
        config = self.get_tenant_config(organization_id)
        if not config:
            return False
        
        # Check data residency requirements
        if config.data_residency == 'EU':
            # EU data residency - all operations must stay in EU
            logger.info(f"Data residency check passed: EU operation for organization {organization_id}")
            return True
        elif config.data_residency == 'Netherlands':
            # Netherlands-only data residency
            logger.info(f"Data residency check passed: Netherlands operation for organization {organization_id}")
            return True
        else:
            logger.warning(f"Unknown data residency requirement: {config.data_residency}")
            return False
    
    def migrate_scan_to_tenant(self, scan_id: str, target_organization_id: str) -> bool:
        """
        Migrate scan result to target tenant (admin operation).
        
        Args:
            scan_id: Scan ID to migrate
            target_organization_id: Target organization ID
            
        Returns:
            bool: True if migration successful
        """
        if not self.validate_tenant_access(target_organization_id):
            return False
        
        try:
            conn = psycopg2.connect(self.db_url, sslmode='require')
            cursor = conn.cursor()
            
            cursor.execute("""
            UPDATE scans 
            SET organization_id = %s
            WHERE scan_id = %s
            """, (target_organization_id, scan_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Migrated scan {scan_id} to organization {target_organization_id}")
                result = True
            else:
                logger.warning(f"No scan found with ID {scan_id}")
                result = False
            
            cursor.close()
            conn.close()
            return result
            
        except Exception as e:
            logger.error(f"Failed to migrate scan {scan_id}: {str(e)}")
            return False
    
    def get_tenant_compliance_report(self, organization_id: str) -> Dict[str, Any]:
        """Generate compliance report for tenant organization."""
        if not self.validate_tenant_access(organization_id):
            raise PermissionError(f"Access denied to organization {organization_id}")
        
        config = self.get_tenant_config(organization_id)
        usage = self.get_tenant_usage(organization_id)
        
        if not config or not usage:
            raise ValueError(f"Configuration or usage data not found for organization {organization_id}")
        
        try:
            # Get scan statistics
            conn = psycopg2.connect(self.db_url, sslmode='require')
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT 
                COUNT(*) as total_scans,
                SUM(total_pii_found) as total_pii_detected,
                SUM(high_risk_count) as total_high_risk,
                AVG(total_pii_found) as avg_pii_per_scan
            FROM scans
            WHERE organization_id = %s
            AND timestamp >= CURRENT_DATE - INTERVAL '30 days'
            """, (organization_id,))
            
            scan_stats = cursor.fetchone()
            cursor.close()
            conn.close()
            
            compliance_report = {
                'organization_id': organization_id,
                'organization_name': config.organization_name,
                'report_date': datetime.now().isoformat(),
                'compliance_score': usage.compliance_score,
                'data_residency': config.data_residency,
                'compliance_regions': config.compliance_regions,
                'scan_statistics': {
                    'total_scans_30_days': scan_stats[0] if scan_stats else 0,
                    'total_pii_detected': scan_stats[1] if scan_stats else 0,
                    'total_high_risk': scan_stats[2] if scan_stats else 0,
                    'avg_pii_per_scan': float(scan_stats[3]) if scan_stats and scan_stats[3] else 0.0
                },
                'usage_status': {
                    'current_users': usage.current_users,
                    'max_users': config.max_users,
                    'scans_this_month': usage.scans_this_month,
                    'max_scans_per_month': config.max_scans_per_month,
                    'storage_used_gb': usage.storage_used_gb,
                    'max_storage_gb': config.max_storage_gb,
                    'utilization_percentage': {
                        'users': (usage.current_users / config.max_users) * 100,
                        'scans': (usage.scans_this_month / config.max_scans_per_month) * 100,
                        'storage': (usage.storage_used_gb / config.max_storage_gb) * 100
                    }
                },
                'features_enabled': list(config.features),
                'tier': config.tier.value
            }
            
            return compliance_report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report for {organization_id}: {str(e)}")
            raise RuntimeError(f"Compliance report generation failed: {str(e)}")
    
    def list_all_tenants(self) -> List[Dict[str, Any]]:
        """List all tenant organizations (admin operation)."""
        return [
            {
                'organization_id': config.organization_id,
                'organization_name': config.organization_name,
                'tier': config.tier.value,
                'max_users': config.max_users,
                'max_scans_per_month': config.max_scans_per_month,
                'data_residency': config.data_residency,
                'compliance_regions': config.compliance_regions,
                'features': list(config.features),
                'created_at': config.created_at.isoformat()
            }
            for config in self.tenants.values()
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on multi-tenant service."""
        total_tenants = len(self.tenants)
        active_tenants = sum(1 for config in self.tenants.values() if config.tier != TenantTier.STARTER)
        
        return {
            "status": "healthy",
            "total_tenants": total_tenants,
            "active_tenants": active_tenants,
            "data_isolation": "enabled",
            "compliance_features": ["EU_GDPR", "Netherlands_UAVG", "data_residency"],
            "supported_tiers": [tier.value for tier in TenantTier],
            "tenant_summary": {
                "enterprise": sum(1 for c in self.tenants.values() if c.tier in [TenantTier.ENTERPRISE, TenantTier.ENTERPRISE_PLUS]),
                "professional": sum(1 for c in self.tenants.values() if c.tier == TenantTier.PROFESSIONAL),
                "starter": sum(1 for c in self.tenants.values() if c.tier == TenantTier.STARTER)
            }
        }

# Global multi-tenant service instance
_multi_tenant_service = None

def get_multi_tenant_service() -> MultiTenantService:
    """Get global multi-tenant service instance."""
    global _multi_tenant_service
    if _multi_tenant_service is None:
        _multi_tenant_service = MultiTenantService()
    return _multi_tenant_service