"""
Compliance Score Calculator - Centralized compliance scoring with configurable penalties
and audit trail for regulatory compliance across all scanner types.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ComplianceConfig:
    """Configuration for compliance score calculation by region/industry."""
    critical_penalty: int = 25  # Penalty per Critical finding
    high_penalty: int = 15      # Penalty per High finding  
    medium_penalty: int = 5     # Penalty per Medium/Other finding
    low_penalty: int = 2        # Penalty per Low finding
    region: str = "Netherlands"
    industry: Optional[str] = None
    regulatory_framework: str = "GDPR"

@dataclass
class ComplianceResult:
    """Result of compliance score calculation with audit details."""
    score: float
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    penalty_breakdown: Dict[str, int]
    calculation_timestamp: str
    config_used: ComplianceConfig
    scan_id: Optional[str] = None
    username: Optional[str] = None

class ComplianceCalculator:
    """
    Centralized compliance score calculator with configurable penalties,
    audit trail, and caching for enterprise compliance requirements.
    """
    
    def __init__(self, config: Optional[ComplianceConfig] = None):
        """Initialize calculator with optional custom configuration."""
        self.config = config or ComplianceConfig()
        self._cache = {}
        self._audit_trail = []
        
    def calculate_compliance_score(self, 
                                 findings: List[Dict[str, Any]], 
                                 scan_id: Optional[str] = None,
                                 username: Optional[str] = None,
                                 use_cache: bool = True) -> ComplianceResult:
        """
        Calculate compliance score with comprehensive audit trail.
        
        Args:
            findings: List of scan findings with severity information
            scan_id: Unique scan identifier for audit trail
            username: User performing the scan for audit trail
            use_cache: Whether to use cached results for identical findings
            
        Returns:
            ComplianceResult with score and detailed breakdown
        """
        # Generate cache key for identical findings
        cache_key = None
        if use_cache:
            cache_key = self._generate_cache_key(findings)
            if cache_key in self._cache:
                cached_result = self._cache[cache_key]
                logger.info(f"Compliance score retrieved from cache: {cached_result.score:.1f}%")
                return cached_result
        
        # Count findings by severity
        critical_findings = len([f for f in findings if f.get('severity') == 'Critical'])
        high_findings = len([f for f in findings if 
                           f.get('severity') == 'High' or f.get('privacy_risk') == 'High'])
        medium_findings = len([f for f in findings if f.get('severity') == 'Medium'])
        low_findings = len([f for f in findings if f.get('severity') == 'Low'])
        
        # Calculate remaining findings (those without explicit severity)
        categorized_findings = critical_findings + high_findings + medium_findings + low_findings
        other_findings = len(findings) - categorized_findings
        medium_findings += other_findings  # Treat uncategorized as medium
        
        # Calculate penalties
        penalty_breakdown = {
            'critical': critical_findings * self.config.critical_penalty,
            'high': high_findings * self.config.high_penalty,
            'medium': medium_findings * self.config.medium_penalty,
            'low': low_findings * self.config.low_penalty
        }
        
        total_penalty = sum(penalty_breakdown.values())
        compliance_score = max(0.0, 100.0 - total_penalty)
        
        # Create result with audit information
        result = ComplianceResult(
            score=compliance_score,
            total_findings=len(findings),
            critical_findings=critical_findings,
            high_findings=high_findings,
            medium_findings=medium_findings,
            low_findings=low_findings,
            penalty_breakdown=penalty_breakdown,
            calculation_timestamp=datetime.now().isoformat(),
            config_used=self.config,
            scan_id=scan_id,
            username=username
        )
        
        # Cache result and add to audit trail
        if use_cache and cache_key:
            self._cache[cache_key] = result
            
        self._audit_trail.append(result)
        
        # Log compliance calculation for audit
        logger.info(f"Compliance score calculated: {compliance_score:.1f}% "
                   f"(Critical: {critical_findings}, High: {high_findings}, "
                   f"Medium: {medium_findings}, Low: {low_findings}) "
                   f"for scan {scan_id or 'unknown'}")
        
        return result
    
    def get_compliance_status(self, score: float, total_findings: int = 0) -> str:
        """Get compliance status text based on score and findings."""
        # Cannot be "Excellent" if there are any findings
        if total_findings > 0:
            if score >= 85:
                return "Good"
            elif score >= 70:
                return "Acceptable"
            elif score >= 50:
                return "Needs Improvement"
            else:
                return "Critical"
        else:
            # No findings - score-based only
            if score >= 95:
                return "Excellent"
            elif score >= 85:
                return "Very Good"
            elif score >= 75:
                return "Good"
            elif score >= 50:
                return "Needs Improvement"
            else:
                return "Critical"
    
    def get_risk_level(self, score: float) -> str:
        """Get risk level based on compliance score."""
        if score >= 75:
            return "Low"
        elif score >= 50:
            return "Medium"
        else:
            return "High"
    
    def update_config(self, new_config: ComplianceConfig) -> None:
        """Update compliance configuration and clear cache."""
        self.config = new_config
        self._cache.clear()
        logger.info(f"Compliance configuration updated for {new_config.region}")
    
    def get_audit_trail(self, limit: Optional[int] = None) -> List[ComplianceResult]:
        """Get audit trail of compliance calculations."""
        if limit:
            return self._audit_trail[-limit:]
        return self._audit_trail.copy()
    
    def export_audit_trail(self, filepath: str) -> None:
        """Export audit trail to JSON file for regulatory compliance."""
        try:
            audit_data = [asdict(result) for result in self._audit_trail]
            with open(filepath, 'w') as f:
                json.dump(audit_data, f, indent=2, default=str)
            logger.info(f"Audit trail exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export audit trail: {e}")
    
    def clear_cache(self) -> None:
        """Clear compliance score cache."""
        self._cache.clear()
        logger.info("Compliance score cache cleared")
    
    def _generate_cache_key(self, findings: List[Dict[str, Any]]) -> str:
        """Generate cache key based on findings severity distribution."""
        severity_counts = {}
        for finding in findings:
            severity = finding.get('severity') or 'Medium'  # Handle None values
            privacy_risk = finding.get('privacy_risk') or ''  # Handle None values
            # Create composite key including privacy_risk for website scans
            key = f"{severity}_{privacy_risk}" if privacy_risk else severity
            severity_counts[key] = severity_counts.get(key, 0) + 1
        
        # Include config in cache key to invalidate on config changes
        config_key = f"{self.config.critical_penalty}_{self.config.high_penalty}_{self.config.medium_penalty}_{self.config.low_penalty}"
        return f"{json.dumps(severity_counts, sort_keys=True)}_{config_key}"

# Global instance for application use
default_calculator = ComplianceCalculator()

def calculate_compliance_score(findings: List[Dict[str, Any]], 
                             scan_id: Optional[str] = None,
                             username: Optional[str] = None) -> Tuple[float, ComplianceResult]:
    """
    Convenience function for quick compliance score calculation.
    
    Returns:
        Tuple of (score, full_result) for backward compatibility
    """
    result = default_calculator.calculate_compliance_score(findings, scan_id, username)
    return result.score, result

def get_compliance_status(score: float) -> str:
    """Get compliance status text."""
    return default_calculator.get_compliance_status(score)

def get_risk_level(score: float) -> str:
    """Get risk level text."""
    return default_calculator.get_risk_level(score)

# Regional compliance configurations
REGIONAL_CONFIGS = {
    "Netherlands": ComplianceConfig(
        critical_penalty=25,
        high_penalty=15,
        medium_penalty=5,
        low_penalty=2,
        region="Netherlands",
        regulatory_framework="GDPR/UAVG"
    ),
    "Germany": ComplianceConfig(
        critical_penalty=30,  # Stricter penalties
        high_penalty=18,
        medium_penalty=6,
        low_penalty=2,
        region="Germany",
        regulatory_framework="GDPR/BDSG"
    ),
    "France": ComplianceConfig(
        critical_penalty=25,
        high_penalty=15,
        medium_penalty=5,
        low_penalty=2,
        region="France",
        regulatory_framework="GDPR/CNIL"
    ),
    "Enterprise": ComplianceConfig(
        critical_penalty=35,  # Highest penalties for enterprise
        high_penalty=20,
        medium_penalty=8,
        low_penalty=3,
        region="Enterprise",
        regulatory_framework="Multi-Regional"
    )
}

def set_regional_config(region: str) -> None:
    """Set compliance configuration for specific region."""
    if region in REGIONAL_CONFIGS:
        default_calculator.update_config(REGIONAL_CONFIGS[region])
        logger.info(f"Compliance configuration set to {region}")
    else:
        logger.warning(f"Unknown region {region}, using default configuration")