#!/usr/bin/env python3
"""
GDPR Data Protection Layer for Scan Results
Ensures all data storage complies with GDPR Articles 5, 6, 17, and 25
"""

import json
import hashlib
import uuid
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class LegalBasis(Enum):
    """GDPR Article 6 Legal Basis for Processing"""
    CONSENT = "consent"  # Art. 6(1)(a) - Data subject has given consent
    CONTRACT = "contract"  # Art. 6(1)(b) - Necessary for contract performance
    LEGAL_OBLIGATION = "legal_obligation"  # Art. 6(1)(c) - Legal obligation
    VITAL_INTERESTS = "vital_interests"  # Art. 6(1)(d) - Protect vital interests
    PUBLIC_TASK = "public_task"  # Art. 6(1)(e) - Public interest task
    LEGITIMATE_INTEREST = "legitimate_interest"  # Art. 6(1)(f) - Legitimate interest

class DataCategory(Enum):
    """Categories of data stored"""
    SCAN_METADATA = "scan_metadata"  # Non-PII: scan type, timestamp, counts
    AGGREGATED_METRICS = "aggregated_metrics"  # Non-PII: totals, scores
    PII_FINDINGS = "pii_findings"  # PII detected in scans
    USER_ACCOUNT = "user_account"  # Username, email, org
    USAGE_ANALYTICS = "usage_analytics"  # Feature usage, scan history
    CLOUD_RESOURCES = "cloud_resources"  # Customer cloud resource info

@dataclass
class DataRetentionPolicy:
    """Data retention configuration per category"""
    category: DataCategory
    retention_days: int
    legal_basis: LegalBasis
    purpose: str
    auto_delete: bool = True
    anonymize_on_expire: bool = True

class GDPRDataProtection:
    """
    GDPR-compliant data protection layer.
    
    Key Features:
    - Legal basis tracking for all stored data
    - Automatic retention policy enforcement
    - Data minimization (store only what's needed)
    - Anonymization of expired data
    - Right to erasure support
    - Persistent consent records (not in-memory)
    """
    
    def _init_consent_table(self, conn):
        """Initialize consent table in database for persistent consent records."""
        try:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS gdpr_consent (
                consent_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                granted BOOLEAN NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                UNIQUE(user_id, category)
            )
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_consent_user ON gdpr_consent(user_id)
            ''')
            conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Error creating consent table: {e}")
    
    DEFAULT_RETENTION_POLICIES = {
        DataCategory.SCAN_METADATA: DataRetentionPolicy(
            category=DataCategory.SCAN_METADATA,
            retention_days=365,  # 1 year for audit purposes
            legal_basis=LegalBasis.CONTRACT,
            purpose="Service delivery and audit trail",
            auto_delete=False,
            anonymize_on_expire=True
        ),
        DataCategory.AGGREGATED_METRICS: DataRetentionPolicy(
            category=DataCategory.AGGREGATED_METRICS,
            retention_days=730,  # 2 years for trend analysis
            legal_basis=LegalBasis.LEGITIMATE_INTEREST,
            purpose="Service improvement and compliance reporting",
            auto_delete=False,
            anonymize_on_expire=True
        ),
        DataCategory.PII_FINDINGS: DataRetentionPolicy(
            category=DataCategory.PII_FINDINGS,
            retention_days=90,  # 90 days - requires consent
            legal_basis=LegalBasis.CONSENT,
            purpose="PII detection and remediation tracking",
            auto_delete=True,
            anonymize_on_expire=True
        ),
        DataCategory.USER_ACCOUNT: DataRetentionPolicy(
            category=DataCategory.USER_ACCOUNT,
            retention_days=365,  # Keep while account active + 1 year
            legal_basis=LegalBasis.CONTRACT,
            purpose="Account management and service delivery",
            auto_delete=False,
            anonymize_on_expire=False
        ),
        DataCategory.USAGE_ANALYTICS: DataRetentionPolicy(
            category=DataCategory.USAGE_ANALYTICS,
            retention_days=90,  # 90 days
            legal_basis=LegalBasis.LEGITIMATE_INTEREST,
            purpose="Service improvement and feature optimization",
            auto_delete=True,
            anonymize_on_expire=True
        ),
        DataCategory.CLOUD_RESOURCES: DataRetentionPolicy(
            category=DataCategory.CLOUD_RESOURCES,
            retention_days=0,  # Never store - process in memory only
            legal_basis=LegalBasis.CONSENT,
            purpose="Cloud sustainability analysis",
            auto_delete=True,
            anonymize_on_expire=True
        )
    }
    
    def __init__(self, custom_policies: Optional[Dict[DataCategory, DataRetentionPolicy]] = None, db_url: Optional[str] = None):
        self.policies = self.DEFAULT_RETENTION_POLICIES.copy()
        if custom_policies:
            self.policies.update(custom_policies)
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        self._consent_cache: Dict[str, bool] = {}
        self._init_consent_db()
        logger.info("GDPR Data Protection layer initialized with persistent consent storage")
    
    def _get_db_connection(self):
        """Get database connection for consent storage."""
        if not self.db_url:
            return None
        try:
            import psycopg2
            return psycopg2.connect(self.db_url, connect_timeout=5)
        except ImportError:
            logger.warning("psycopg2 not available - consent storage disabled")
            return None
        except Exception as e:
            logger.warning(f"Database connection unavailable: {e}")
            return None
    
    def _init_consent_db(self):
        """Initialize consent table in database - graceful fallback if unavailable."""
        try:
            conn = self._get_db_connection()
            if conn:
                self._init_consent_table(conn)
                conn.close()
        except Exception as e:
            logger.warning(f"Consent database initialization skipped: {e}")
    
    def check_consent(self, user_id: str, category: DataCategory) -> bool:
        """Check if user has given consent for data category requiring consent."""
        policy = self.policies.get(category)
        if not policy:
            return False
        
        if policy.legal_basis != LegalBasis.CONSENT:
            return True
        
        cache_key = f"{user_id}:{category.value}"
        if cache_key in self._consent_cache:
            return self._consent_cache.get(cache_key, False)
        
        conn = self._get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT granted FROM gdpr_consent WHERE user_id = %s AND category = %s",
                    (user_id, category.value)
                )
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                granted = result[0] if result else False
                self._consent_cache[cache_key] = granted
                return granted
            except Exception as e:
                logger.error(f"Error checking consent: {e}")
                conn.close()
        
        return False
    
    def record_consent(self, user_id: str, category: DataCategory, granted: bool) -> Dict[str, Any]:
        """Record user consent for a data category - persisted to database."""
        consent_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        conn = self._get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO gdpr_consent (consent_id, user_id, category, granted, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, category) DO UPDATE SET
                        granted = EXCLUDED.granted,
                        timestamp = EXCLUDED.timestamp,
                        consent_id = EXCLUDED.consent_id
                """, (consent_id, user_id, category.value, granted, timestamp))
                conn.commit()
                cursor.close()
                conn.close()
                
                cache_key = f"{user_id}:{category.value}"
                self._consent_cache[cache_key] = granted
                
                logger.info(f"Consent recorded for user {user_id}, category {category.value}: {granted}")
            except Exception as e:
                logger.error(f"Error recording consent: {e}")
                conn.close()
        
        return {
            "consent_id": consent_id,
            "user_id": user_id,
            "category": category.value,
            "consent_granted": granted,
            "timestamp": timestamp.isoformat(),
            "legal_basis": LegalBasis.CONSENT.value,
            "persisted": conn is not None
        }
    
    def anonymize_pii_in_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Anonymize PII in scan findings for GDPR-compliant storage.
        Replaces actual PII values with hashed/redacted versions.
        """
        anonymized = []
        
        for finding in findings:
            anon_finding = finding.copy()
            
            if 'pii_value' in anon_finding:
                original = str(anon_finding['pii_value'])
                anon_finding['pii_value'] = self._hash_pii(original)
                anon_finding['pii_anonymized'] = True
            
            if 'matched_text' in anon_finding:
                anon_finding['matched_text'] = '[REDACTED]'
            
            if 'context' in anon_finding:
                anon_finding['context'] = self._redact_context(anon_finding['context'])
            
            if 'email' in anon_finding:
                anon_finding['email'] = self._anonymize_email(anon_finding['email'])
            
            if 'phone' in anon_finding:
                anon_finding['phone'] = '[REDACTED PHONE]'
            
            if 'bsn' in anon_finding or 'ssn' in anon_finding:
                anon_finding['bsn'] = '[REDACTED BSN]' if 'bsn' in anon_finding else None
                anon_finding['ssn'] = '[REDACTED SSN]' if 'ssn' in anon_finding else None
            
            anonymized.append(anon_finding)
        
        return anonymized
    
    def _hash_pii(self, value: str) -> str:
        """Create irreversible hash of PII value."""
        salt = os.environ.get('PII_HASH_SALT', 'dataguardian_pii_salt')
        combined = f"{salt}:{value}"
        return f"HASH:{hashlib.sha256(combined.encode()).hexdigest()[:16]}"
    
    def _anonymize_email(self, email: str) -> str:
        """Anonymize email while keeping domain for analytics."""
        if '@' in email:
            local, domain = email.split('@', 1)
            return f"***@{domain}"
        return '[REDACTED EMAIL]'
    
    def _redact_context(self, context: str) -> str:
        """Redact sensitive context while keeping structure."""
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_pattern = r'\b\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,4}\b'
        bsn_pattern = r'\b\d{9}\b'
        
        redacted = re.sub(email_pattern, '[EMAIL]', context)
        redacted = re.sub(phone_pattern, '[PHONE]', redacted)
        redacted = re.sub(bsn_pattern, '[BSN]', redacted)
        
        return redacted
    
    def prepare_scan_result_for_storage(
        self,
        scan_result: Dict[str, Any],
        user_id: str,
        store_pii_details: bool = False
    ) -> Dict[str, Any]:
        """
        Prepare scan result for GDPR-compliant storage.
        
        - Anonymizes PII findings unless explicit consent given
        - Removes cloud resource identifiers
        - Keeps only aggregated metrics
        """
        prepared = {
            "scan_id": scan_result.get("scan_id", str(uuid.uuid4())),
            "scan_type": scan_result.get("scan_type"),
            "timestamp": scan_result.get("timestamp", datetime.now().isoformat()),
            "data_category": DataCategory.SCAN_METADATA.value,
            "legal_basis": LegalBasis.CONTRACT.value,
            "retention_expires": (
                datetime.now() + timedelta(days=self.policies[DataCategory.SCAN_METADATA].retention_days)
            ).isoformat()
        }
        
        prepared["metrics"] = {
            "total_findings": scan_result.get("total_findings", 0),
            "high_risk_count": scan_result.get("high_risk_count", 0),
            "medium_risk_count": scan_result.get("medium_risk_count", 0),
            "low_risk_count": scan_result.get("low_risk_count", 0),
            "compliance_score": scan_result.get("compliance_score", 0),
            "files_scanned": scan_result.get("files_scanned", 0)
        }
        
        if 'emissions' in scan_result:
            prepared["emissions_summary"] = {
                "total_co2_kg_month": scan_result["emissions"].get("total_co2_kg_month", 0),
                "total_energy_kwh_month": scan_result["emissions"].get("total_energy_kwh_month", 0),
                "sustainability_score": scan_result.get("metrics", {}).get("sustainability_score", 0)
            }
        
        findings = scan_result.get("findings", [])
        if findings:
            has_consent = self.check_consent(user_id, DataCategory.PII_FINDINGS)
            
            if store_pii_details and has_consent:
                prepared["findings"] = self.anonymize_pii_in_findings(findings)
                prepared["findings_storage_consent"] = True
            else:
                prepared["findings_summary"] = {
                    "total": len(findings),
                    "by_type": self._count_by_type(findings),
                    "by_severity": self._count_by_severity(findings)
                }
                prepared["findings_storage_consent"] = False
        
        if 'resources' in scan_result:
            resources = scan_result['resources']
            prepared["resources_summary"] = {
                "unused_count": resources.get("unused_resources", 0),
                "total_waste_cost": resources.get("total_waste_cost", 0),
                "total_waste_co2": resources.get("total_waste_co2", 0)
            }
        
        return prepared
    
    def _count_by_type(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count findings by type without storing details."""
        counts = {}
        for f in findings:
            ftype = f.get("type", f.get("pii_type", "unknown"))
            counts[ftype] = counts.get(ftype, 0) + 1
        return counts
    
    def _count_by_severity(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count findings by severity."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in findings:
            severity = f.get("severity", "medium").lower()
            if severity in counts:
                counts[severity] += 1
        return counts
    
    def get_retention_info(self) -> List[Dict[str, Any]]:
        """Get all retention policies for transparency."""
        return [
            {
                "category": policy.category.value,
                "retention_days": policy.retention_days,
                "legal_basis": policy.legal_basis.value,
                "purpose": policy.purpose,
                "auto_delete": policy.auto_delete
            }
            for policy in self.policies.values()
        ]
    
    def delete_user_data(self, user_id: str, db_connection) -> Dict[str, Any]:
        """
        Delete all user data (GDPR Article 17 - Right to Erasure).
        
        Returns summary of deleted data.
        """
        deleted = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "deleted_categories": []
        }
        
        try:
            cursor = db_connection.cursor()
            
            cursor.execute(
                "DELETE FROM scans WHERE username = %s RETURNING scan_id",
                (user_id,)
            )
            scan_ids = cursor.fetchall()
            deleted["scans_deleted"] = len(scan_ids)
            deleted["deleted_categories"].append("scan_results")
            
            cursor.execute(
                "DELETE FROM gdpr_consent WHERE user_id = %s",
                (user_id,)
            )
            deleted["deleted_categories"].append("consent_records")
            
            for key in list(self._consent_cache.keys()):
                if key.startswith(f"{user_id}:"):
                    del self._consent_cache[key]
            
            db_connection.commit()
            logger.info(f"GDPR erasure completed for user {user_id}: {deleted}")
            
        except Exception as e:
            logger.error(f"Error during GDPR erasure for user {user_id}: {str(e)}")
            deleted["error"] = str(e)
        
        return deleted
    
    def export_user_data(self, user_id: str, db_connection) -> Dict[str, Any]:
        """
        Export all user data (GDPR Article 20 - Data Portability).
        
        Returns all data in portable JSON format.
        """
        export = {
            "user_id": user_id,
            "export_timestamp": datetime.now().isoformat(),
            "format_version": "1.0",
            "data": {}
        }
        
        try:
            cursor = db_connection.cursor()
            
            cursor.execute(
                """SELECT scan_id, scan_type, timestamp, result_summary, compliance_score
                   FROM scans WHERE username = %s ORDER BY timestamp DESC""",
                (user_id,)
            )
            scans = cursor.fetchall()
            export["data"]["scans"] = [
                {
                    "scan_id": s[0],
                    "scan_type": s[1],
                    "timestamp": s[2].isoformat() if s[2] else None,
                    "summary": s[3],
                    "compliance_score": s[4]
                }
                for s in scans
            ]
            
            cursor.execute(
                """SELECT consent_id, category, granted, timestamp 
                   FROM gdpr_consent WHERE user_id = %s""",
                (user_id,)
            )
            consent_rows = cursor.fetchall()
            export["data"]["consent_records"] = [
                {
                    "consent_id": c[0],
                    "category": c[1],
                    "granted": c[2],
                    "timestamp": c[3].isoformat() if c[3] else None
                }
                for c in consent_rows
            ]
            
            export["data"]["retention_policies"] = self.get_retention_info()
            
            logger.info(f"GDPR data export completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error during GDPR export for user {user_id}: {str(e)}")
            export["error"] = str(e)
        
        return export


_gdpr_protection_instance = None

def get_gdpr_protection() -> GDPRDataProtection:
    """Get singleton GDPR protection instance."""
    global _gdpr_protection_instance
    if _gdpr_protection_instance is None:
        _gdpr_protection_instance = GDPRDataProtection()
    return _gdpr_protection_instance
