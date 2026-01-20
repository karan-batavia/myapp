"""
Database Service for DataGuardian Pro
Handles payment records, subscription management, and analytics storage
"""

import os
import logging

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("database_service")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import json
from contextlib import contextmanager



class DatabaseService:
    """Professional database service for payment and subscription management"""
    
    def __init__(self):
        # Database configuration
        self.database_url = os.getenv('DATABASE_URL')
        self.connection_pool = None
        
        if not self.database_url:
            logger.warning("DATABASE_URL not configured - database features disabled")
            self.enabled = False
        else:
            self.enabled = True
            self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database tables if they don't exist"""
        if not self.enabled:
            return
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create payment records table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS payment_records (
                            id SERIAL PRIMARY KEY,
                            session_id VARCHAR(255) UNIQUE NOT NULL,
                            customer_email VARCHAR(255) NOT NULL,
                            amount DECIMAL(10,2) NOT NULL,
                            currency VARCHAR(3) DEFAULT 'EUR',
                            scan_type VARCHAR(100) NOT NULL,
                            country_code VARCHAR(2) DEFAULT 'NL',
                            payment_method VARCHAR(50),
                            status VARCHAR(50) NOT NULL,
                            metadata JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create subscription records table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS subscription_records (
                            id SERIAL PRIMARY KEY,
                            subscription_id VARCHAR(255) UNIQUE NOT NULL,
                            customer_id VARCHAR(255) NOT NULL,
                            customer_email VARCHAR(255) NOT NULL,
                            plan_name VARCHAR(100) NOT NULL,
                            status VARCHAR(50) NOT NULL,
                            amount DECIMAL(10,2) NOT NULL,
                            currency VARCHAR(3) DEFAULT 'EUR',
                            billing_interval VARCHAR(20) DEFAULT 'month',
                            current_period_start TIMESTAMP,
                            current_period_end TIMESTAMP,
                            cancel_at_period_end BOOLEAN DEFAULT FALSE,
                            metadata JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create invoice records table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS invoice_records (
                            id SERIAL PRIMARY KEY,
                            invoice_number VARCHAR(50) UNIQUE NOT NULL,
                            customer_email VARCHAR(255) NOT NULL,
                            customer_name VARCHAR(255),
                            customer_address TEXT,
                            amount_subtotal DECIMAL(10,2) NOT NULL,
                            amount_tax DECIMAL(10,2) NOT NULL,
                            amount_total DECIMAL(10,2) NOT NULL,
                            currency VARCHAR(3) DEFAULT 'EUR',
                            tax_rate DECIMAL(5,4),
                            country_code VARCHAR(2) DEFAULT 'NL',
                            description TEXT,
                            payment_status VARCHAR(50) DEFAULT 'paid',
                            pdf_generated BOOLEAN DEFAULT FALSE,
                            metadata JSONB,
                            issue_date DATE DEFAULT CURRENT_DATE,
                            due_date DATE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create analytics events table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS analytics_events (
                            id SERIAL PRIMARY KEY,
                            event_type VARCHAR(100) NOT NULL,
                            user_id VARCHAR(255),
                            session_id VARCHAR(255),
                            event_data JSONB,
                            ip_address INET,
                            user_agent TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create certificate records table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS certificate_records (
                            id SERIAL PRIMARY KEY,
                            certificate_id VARCHAR(255) UNIQUE NOT NULL,
                            customer_email VARCHAR(255) NOT NULL,
                            certificate_type VARCHAR(100) NOT NULL,
                            organization_name VARCHAR(255),
                            amount_paid DECIMAL(10,2),
                            currency VARCHAR(3) DEFAULT 'EUR',
                            status VARCHAR(50) DEFAULT 'issued',
                            issue_date DATE DEFAULT CURRENT_DATE,
                            expiry_date DATE,
                            pdf_generated BOOLEAN DEFAULT FALSE,
                            metadata JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes for better performance
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_payment_records_email 
                        ON payment_records(customer_email)
                    """)
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_payment_records_status 
                        ON payment_records(status)
                    """)
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_subscription_records_customer 
                        ON subscription_records(customer_id)
                    """)
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_analytics_events_type 
                        ON analytics_events(event_type)
                    """)
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_analytics_events_created 
                        ON analytics_events(created_at)
                    """)
                    
                conn.commit()
                logger.info("Database tables initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        if not self.enabled:
            raise ValueError("Database not configured")
        
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def store_payment_record(self, payment_record: Dict[str, Any]) -> bool:
        """Store payment record in database"""
        if not self.enabled:
            logger.warning("Database not configured - payment record not stored")
            return False
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO payment_records 
                        (session_id, customer_email, amount, currency, scan_type, 
                         country_code, payment_method, status, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (session_id) 
                        DO UPDATE SET 
                            status = EXCLUDED.status,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        payment_record['session_id'],
                        payment_record['customer_email'],
                        payment_record['amount'],
                        payment_record.get('currency', 'EUR'),
                        payment_record['scan_type'],
                        payment_record.get('country_code', 'NL'),
                        payment_record.get('payment_method'),
                        payment_record['status'],
                        json.dumps(payment_record.get('metadata', {}))
                    ))
                conn.commit()
                logger.info(f"Payment record stored: {payment_record['session_id']}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store payment record: {str(e)}")
            return False
    
    def get_payment_record(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve payment record by session ID"""
        if not self.enabled:
            return None
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM payment_records WHERE session_id = %s
                    """, (session_id,))
                    
                    record = cursor.fetchone()
                    return dict(record) if record else None
                    
        except Exception as e:
            logger.error(f"Failed to retrieve payment record: {str(e)}")
            return None
    
    def store_subscription_record(self, subscription: Dict[str, Any]) -> bool:
        """Store subscription record in database"""
        if not self.enabled:
            return False
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO subscription_records 
                        (subscription_id, customer_id, customer_email, plan_name, status,
                         amount, currency, billing_interval, current_period_start,
                         current_period_end, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (subscription_id)
                        DO UPDATE SET
                            status = EXCLUDED.status,
                            amount = EXCLUDED.amount,
                            current_period_start = EXCLUDED.current_period_start,
                            current_period_end = EXCLUDED.current_period_end,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        subscription['id'],
                        subscription['customer'],
                        subscription.get('customer_email', ''),
                        subscription.get('plan_name', ''),
                        subscription['status'],
                        subscription.get('amount', 0) / 100,  # Convert from cents
                        subscription.get('currency', 'eur').upper(),
                        subscription.get('interval', 'month'),
                        datetime.fromtimestamp(subscription.get('current_period_start', 0)),
                        datetime.fromtimestamp(subscription.get('current_period_end', 0)),
                        json.dumps(subscription.get('metadata', {}))
                    ))
                conn.commit()
                logger.info(f"Subscription record stored: {subscription['id']}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store subscription record: {str(e)}")
            return False
    
    def get_subscription_by_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get active subscription for customer"""
        if not self.enabled:
            return None
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM subscription_records 
                        WHERE customer_id = %s AND status = 'active'
                        ORDER BY created_at DESC LIMIT 1
                    """, (customer_id,))
                    
                    record = cursor.fetchone()
                    return dict(record) if record else None
                    
        except Exception as e:
            logger.error(f"Failed to retrieve subscription: {str(e)}")
            return None
    
    def store_invoice_record(self, invoice_data: Dict[str, Any]) -> bool:
        """Store invoice record in database"""
        if not self.enabled:
            return False
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO invoice_records 
                        (invoice_number, customer_email, customer_name, customer_address,
                         amount_subtotal, amount_tax, amount_total, currency, tax_rate,
                         country_code, description, payment_status, issue_date, due_date, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        invoice_data['invoice_number'],
                        invoice_data['customer_email'],
                        invoice_data.get('customer_name'),
                        invoice_data.get('customer_address'),
                        invoice_data['amount_subtotal'],
                        invoice_data['amount_tax'],
                        invoice_data['amount_total'],
                        invoice_data.get('currency', 'EUR'),
                        invoice_data.get('tax_rate'),
                        invoice_data.get('country_code', 'NL'),
                        invoice_data.get('description'),
                        invoice_data.get('payment_status', 'paid'),
                        invoice_data.get('issue_date', datetime.now().date()),
                        invoice_data.get('due_date'),
                        json.dumps(invoice_data.get('metadata', {}))
                    ))
                conn.commit()
                logger.info(f"Invoice record stored: {invoice_data['invoice_number']}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store invoice record: {str(e)}")
            return False
    
    def track_analytics_event(self, event_type: str, user_id: Optional[str] = None, 
                            session_id: Optional[str] = None, event_data: Optional[Dict[str, Any]] = None,
                            ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """Track analytics event"""
        if not self.enabled:
            return False
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO analytics_events 
                        (event_type, user_id, session_id, event_data, ip_address, user_agent)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        event_type,
                        user_id,
                        session_id,
                        json.dumps(event_data) if event_data else None,
                        ip_address,
                        user_agent
                    ))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to track analytics event: {str(e)}")
            return False
    
    def get_payment_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get payment analytics for the last N days"""
        if not self.enabled:
            return {}
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    start_date = datetime.now() - timedelta(days=days)
                    
                    # Total revenue
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_payments,
                            SUM(amount) as total_revenue,
                            AVG(amount) as average_payment,
                            COUNT(DISTINCT customer_email) as unique_customers
                        FROM payment_records 
                        WHERE created_at >= %s AND status = 'completed'
                    """, (start_date,))
                    totals = cursor.fetchone()
                    
                    # Revenue by scan type
                    cursor.execute("""
                        SELECT 
                            scan_type,
                            COUNT(*) as count,
                            SUM(amount) as revenue
                        FROM payment_records 
                        WHERE created_at >= %s AND status = 'completed'
                        GROUP BY scan_type
                        ORDER BY revenue DESC
                    """, (start_date,))
                    by_scan_type = cursor.fetchall()
                    
                    # Revenue by country
                    cursor.execute("""
                        SELECT 
                            country_code,
                            COUNT(*) as count,
                            SUM(amount) as revenue
                        FROM payment_records 
                        WHERE created_at >= %s AND status = 'completed'
                        GROUP BY country_code
                        ORDER BY revenue DESC
                    """, (start_date,))
                    by_country = cursor.fetchall()
                    
                    return {
                        'period_days': days,
                        'totals': dict(totals) if totals else {},
                        'by_scan_type': [dict(row) for row in by_scan_type],
                        'by_country': [dict(row) for row in by_country]
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get payment analytics: {str(e)}")
            return {}
    
    def get_subscription_analytics(self) -> Dict[str, Any]:
        """Get subscription analytics"""
        if not self.enabled:
            return {}
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    # Active subscriptions
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as active_subscriptions,
                            SUM(amount) as monthly_recurring_revenue,
                            COUNT(DISTINCT customer_email) as unique_subscribers
                        FROM subscription_records 
                        WHERE status = 'active'
                    """)
                    active_stats = cursor.fetchone()
                    
                    # Subscriptions by plan
                    cursor.execute("""
                        SELECT 
                            plan_name,
                            COUNT(*) as count,
                            SUM(amount) as revenue
                        FROM subscription_records 
                        WHERE status = 'active'
                        GROUP BY plan_name
                        ORDER BY revenue DESC
                    """)
                    by_plan = cursor.fetchall()
                    
                    return {
                        'active_stats': dict(active_stats) if active_stats else {},
                        'by_plan': [dict(row) for row in by_plan]
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get subscription analytics: {str(e)}")
            return {}
    
    def store_certificate_record(self, certificate_data: Dict[str, Any]) -> bool:
        """Store certificate generation record"""
        if not self.enabled:
            return False
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO certificate_records 
                        (certificate_id, customer_email, certificate_type, organization_name,
                         amount_paid, currency, status, issue_date, expiry_date, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        certificate_data['certificate_id'],
                        certificate_data['customer_email'],
                        certificate_data['certificate_type'],
                        certificate_data.get('organization_name'),
                        certificate_data.get('amount_paid', 0),
                        certificate_data.get('currency', 'EUR'),
                        certificate_data.get('status', 'issued'),
                        certificate_data.get('issue_date', datetime.now().date()),
                        certificate_data.get('expiry_date'),
                        json.dumps(certificate_data.get('metadata', {}))
                    ))
                conn.commit()
                logger.info(f"Certificate record stored: {certificate_data['certificate_id']}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store certificate record: {str(e)}")
            return False
    
    def update_payment_status(self, session_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update payment status"""
        if not self.enabled:
            return False
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    metadata_update = {'error_message': error_message} if error_message else {}
                    cursor.execute("""
                        UPDATE payment_records 
                        SET status = %s, 
                            metadata = metadata || %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE session_id = %s
                    """, (status, json.dumps(metadata_update), session_id))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to update payment status: {str(e)}")
            return False
    
    def get_customer_payment_history(self, customer_email: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get payment history for customer"""
        if not self.enabled:
            return []
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM payment_records 
                        WHERE customer_email = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (customer_email, limit))
                    
                    records = cursor.fetchall()
                    return [dict(record) for record in records]
                    
        except Exception as e:
            logger.error(f"Failed to get customer payment history: {str(e)}")
            return []
    
    def get_subscription_by_customer_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription record by customer ID"""
        if not self.enabled:
            return None
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM subscription_records 
                        WHERE customer_id = %s 
                        AND status IN ('active', 'trialing', 'past_due', 'payment_failed')
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """, (customer_id,))
                    
                    record = cursor.fetchone()
                    return dict(record) if record else None
                    
        except Exception as e:
            logger.error(f"Failed to get subscription by customer ID: {str(e)}")
            return None
    
    def update_subscription_record(self, subscription_id: str, update_data: Dict[str, Any]) -> bool:
        """Update subscription record"""
        if not self.enabled:
            return False
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE subscription_records 
                        SET status = %s,
                            metadata = metadata || %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE subscription_id = %s
                    """, (
                        update_data.get('status'),
                        json.dumps(update_data.get('metadata', {})),
                        subscription_id
                    ))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update subscription record: {str(e)}")
            return False

    def update_user_license_tier(self, user_id: str, tier: str, subscription_id: Optional[str] = None) -> bool:
        """Update user's license tier in platform_users table by user_id"""
        if not self.enabled:
            return False
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Update the user's license tier and subscription info
                    cursor.execute("""
                        UPDATE platform_users 
                        SET license_tier = %s,
                            metadata = COALESCE(metadata, '{}'::jsonb) || %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        tier,
                        json.dumps({
                            'subscription_id': subscription_id,
                            'tier_updated_at': datetime.now().isoformat()
                        }),
                        int(user_id)
                    ))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"User {user_id} license tier updated to {tier}")
                    return True
                else:
                    logger.warning(f"No user found with id {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update user license tier: {str(e)}")
            return False
    
    def update_user_license_tier_by_email(self, email: str, tier: str, subscription_id: Optional[str] = None) -> bool:
        """Update user's license tier in platform_users table by email"""
        if not self.enabled:
            return False
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Update the user's license tier and subscription info by email
                    cursor.execute("""
                        UPDATE platform_users 
                        SET license_tier = %s,
                            metadata = COALESCE(metadata, '{}'::jsonb) || %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE email = %s
                    """, (
                        tier,
                        json.dumps({
                            'subscription_id': subscription_id,
                            'tier_updated_at': datetime.now().isoformat()
                        }),
                        email
                    ))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"User {email} license tier updated to {tier}")
                    return True
                else:
                    logger.warning(f"No user found with email {email}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update user license tier by email: {str(e)}")
            return False

# Global database service instance
database_service = DatabaseService()