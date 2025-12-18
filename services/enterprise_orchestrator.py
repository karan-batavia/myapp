"""
Enterprise Orchestrator

Coordinates enterprise features using event-driven architecture.
Integrates DSAR, RoPA, Consent Management, Vendor Risk, and other enterprise features
without modifying core scanner functionality.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import streamlit as st

from utils.event_bus import get_event_bus, EventType, Event, publish_event
from services.dsar_automation import DSARAutomation
from services.ropa_data_inventory import RopaDataInventory
from services.consent_management_platform import ConsentManagementPlatform
from services.vendor_risk_management import VendorRiskManagement
from services.enterprise_connector_hardening import EnterpriseConnectorHardening
from services.enterprise_ticketing_integrations import EnterpriseTicketingIntegrations
from services.soc2_audit_readiness import SOC2AuditReadiness
from services.enterprise_listeners import initialize_enterprise_listeners, get_enterprise_listener

logger = logging.getLogger("services.enterprise_orchestrator")

class EnterpriseOrchestrator:
    """
    Orchestrates enterprise features using event-driven integration
    
    Maintains separation between core functionality and enterprise features
    while providing seamless integration through events.
    """
    
    def __init__(self, use_redis: bool = True):
        self.event_bus = get_event_bus(use_redis)
        self.listeners_registered = False
        
        # Initialize enterprise services
        self.dsar_service = DSARAutomation()
        self.ropa_service = RopaDataInventory()
        self.consent_service = ConsentManagementPlatform()
        self.vendor_service = VendorRiskManagement()
        self.connector_service = EnterpriseConnectorHardening()
        self.ticketing_service = EnterpriseTicketingIntegrations()
        self.soc2_service = SOC2AuditReadiness()
        
        # Track listener IDs for cleanup
        self._listener_ids: List[str] = []
        
        logger.info("EnterpriseOrchestrator: Initialized enterprise services")
    
    def register_listeners(self) -> None:
        """Register event listeners for enterprise integration"""
        if self.listeners_registered:
            return
            
        try:
            # Get enterprise listener instance for delegation (no auto-registration)
            self.enterprise_listener = get_enterprise_listener()
            logger.info("Initialized enterprise listener for delegation")
            
            # Register orchestrator as coordinator (delegates to enterprise listener)
            # Core scanning events
            self._listener_ids.append(
                self.event_bus.subscribe(EventType.SCAN_STARTED, self._on_scan_started)
            )
            self._listener_ids.append(
                self.event_bus.subscribe(EventType.SCAN_COMPLETED, self._on_scan_completed)
            )
            self._listener_ids.append(
                self.event_bus.subscribe(EventType.FINDING_DETECTED, self._on_finding_detected)
            )
            self._listener_ids.append(
                self.event_bus.subscribe(EventType.CRITICAL_ISSUE_FOUND, self._on_critical_issue)
            )
            
            # DSAR events
            self._listener_ids.append(
                self.event_bus.subscribe(EventType.DSAR_REQUEST_SUBMITTED, self._on_dsar_submitted)
            )
            
            # Consent events
            self._listener_ids.append(
                self.event_bus.subscribe(EventType.CONSENT_UPDATED, self._on_consent_updated)
            )
            
            # Vendor risk events
            self._listener_ids.append(
                self.event_bus.subscribe(EventType.VENDOR_RISK_ALERT, self._on_vendor_alert)
            )
            
            # SOC2 evidence events
            self._listener_ids.append(
                self.event_bus.subscribe(EventType.COMPLIANCE_EVIDENCE_ADDED, self._on_evidence_added)
            )
            
            self.listeners_registered = True
            logger.info(f"EnterpriseOrchestrator: Registered {len(self._listener_ids)} event listeners")
            
        except Exception as e:
            logger.error(f"EnterpriseOrchestrator: Failed to register listeners: {e}")
    
    def unregister_listeners(self) -> None:
        """Unregister all event listeners"""
        for event_type in EventType:
            for listener_id in self._listener_ids:
                self.event_bus.unsubscribe(event_type, listener_id)
        
        self._listener_ids.clear()
        self.listeners_registered = False
        logger.info("EnterpriseOrchestrator: Unregistered all listeners")
    
    def _on_scan_started(self, event: Event) -> None:
        """Handle scan started events"""
        try:
            data = event.data
            scan_type = data.get('scanner_type', 'unknown')
            region = data.get('region', 'Unknown')
            
            # Prepare RoPA entry for new scan
            if hasattr(self.ropa_service, 'prepare_scan_entry'):
                self.ropa_service.prepare_scan_entry({
                    'scan_id': event.event_id,
                    'scan_type': scan_type,
                    'region': region,
                    'user_id': event.user_id,
                    'timestamp': event.timestamp.isoformat()
                })
            
            # Initialize SOC2 evidence collection
            if hasattr(self.soc2_service, 'start_evidence_collection'):
                self.soc2_service.start_evidence_collection({
                    'scan_id': event.event_id,
                    'scan_type': scan_type,
                    'user_id': event.user_id
                })
            
            logger.debug(f"EnterpriseOrchestrator: Processed scan start for {scan_type}")
            
        except Exception as e:
            logger.error(f"EnterpriseOrchestrator: Error handling scan started: {e}")
    
    def _on_scan_completed(self, event: Event) -> None:
        """Handle scan completed events - delegate to enterprise listener"""
        try:
            logger.debug(f"EnterpriseOrchestrator: Delegating scan completion to enterprise listener")
            
            # Delegate to enterprise listener for evidence capture
            if hasattr(self, 'enterprise_listener'):
                self.enterprise_listener._handle_scan_completion(event)
            
            logger.debug(f"EnterpriseOrchestrator: Scan completion delegation complete")
            
        except Exception as e:
            logger.error(f"EnterpriseOrchestrator: Error delegating scan completion: {e}")
    
    def _on_finding_detected(self, event: Event) -> None:
        """Handle individual finding detection events"""
        try:
            data = event.data
            finding_type = data.get('type', 'Unknown')
            risk_level = data.get('risk_level', 'Low')
            location = data.get('location', 'Unknown')
            
            # Add to RoPA data inventory if PII-related
            if 'pii' in finding_type.lower() or 'personal' in finding_type.lower():
                if hasattr(self.ropa_service, 'add_data_finding'):
                    self.ropa_service.add_data_finding({
                        'scan_id': event.event_id,
                        'finding_type': finding_type,
                        'location': location,
                        'risk_level': risk_level,
                        'detected_at': event.timestamp.isoformat()
                    })
            
            # Track for SOC2 evidence if security-related
            if risk_level in ['Critical', 'High']:
                if hasattr(self.soc2_service, 'add_security_finding'):
                    self.soc2_service.add_security_finding({
                        'scan_id': event.event_id,
                        'finding_type': finding_type,
                        'risk_level': risk_level,
                        'location': location
                    })
            
            logger.debug(f"EnterpriseOrchestrator: Processed {risk_level} finding: {finding_type}")
            
        except Exception as e:
            logger.error(f"EnterpriseOrchestrator: Error handling finding detected: {e}")
    
    def _on_critical_issue(self, event: Event) -> None:
        """Handle critical issues - delegate to enterprise listener"""
        try:
            logger.info(f"EnterpriseOrchestrator: Delegating critical issue to enterprise listener")
            
            # Delegate to enterprise listener for ticket creation and evidence
            if hasattr(self, 'enterprise_listener'):
                self.enterprise_listener._handle_critical_issue(event)
            
            logger.info("EnterpriseOrchestrator: Critical issue delegation complete")
            
        except Exception as e:
            logger.error(f"EnterpriseOrchestrator: Error handling critical issue: {e}")
    
    def _on_dsar_submitted(self, event: Event) -> None:
        """Handle DSAR request submissions"""
        try:
            # Process DSAR automation workflow
            if hasattr(self.dsar_service, 'process_request'):
                self.dsar_service.process_request(event.data)
            
            # Create SOC2 audit evidence
            if hasattr(self.soc2_service, 'add_dsar_evidence'):
                self.soc2_service.add_dsar_evidence({
                    'request_id': event.event_id,
                    'submitted_by': event.user_id,
                    'submitted_at': event.timestamp.isoformat()
                })
            
            logger.info(f"EnterpriseOrchestrator: Processed DSAR request {event.event_id}")
            
        except Exception as e:
            logger.error(f"EnterpriseOrchestrator: Error handling DSAR submission: {e}")
    
    def _on_consent_updated(self, event: Event) -> None:
        """Handle consent updates"""
        try:
            # Update consent management platform
            if hasattr(self.consent_service, 'update_consent'):
                self.consent_service.update_consent(event.data)
            
            # Track for SOC2 evidence
            if hasattr(self.soc2_service, 'add_consent_evidence'):
                self.soc2_service.add_consent_evidence({
                    'user_id': event.user_id,
                    'consent_changes': event.data,
                    'updated_at': event.timestamp.isoformat()
                })
            
            logger.debug(f"EnterpriseOrchestrator: Processed consent update for {event.user_id}")
            
        except Exception as e:
            logger.error(f"EnterpriseOrchestrator: Error handling consent update: {e}")
    
    def _on_vendor_alert(self, event: Event) -> None:
        """Handle vendor risk alerts"""
        try:
            # Create ticket for vendor issues
            self._auto_create_ticket(event, {
                'category': 'Vendor Risk',
                'priority': 'High',
                'vendor_related': True
            })
            
            # Process through vendor risk management
            if hasattr(self.vendor_service, 'handle_alert'):
                self.vendor_service.handle_alert(event.data)
            
            logger.info(f"EnterpriseOrchestrator: Processed vendor alert")
            
        except Exception as e:
            logger.error(f"EnterpriseOrchestrator: Error handling vendor alert: {e}")
    
    def _on_evidence_added(self, event: Event) -> None:
        """Handle compliance evidence additions"""
        try:
            # Store in SOC2 audit system
            if hasattr(self.soc2_service, 'store_evidence'):
                self.soc2_service.store_evidence(event.data)
            
            logger.debug(f"EnterpriseOrchestrator: Stored compliance evidence")
            
        except Exception as e:
            logger.error(f"EnterpriseOrchestrator: Error handling evidence addition: {e}")
    
    def _auto_create_ticket(self, event: Event, context: Dict[str, Any]) -> None:
        """Auto-create tickets for high-priority issues"""
        try:
            if hasattr(self.ticketing_service, 'create_auto_ticket'):
                ticket_data = {
                    'source_event_id': event.event_id,
                    'user_id': event.user_id,
                    'session_id': event.session_id,
                    'created_at': event.timestamp.isoformat(),
                    'context': context,
                    'event_data': event.data
                }
                
                self.ticketing_service.create_auto_ticket(ticket_data)
                logger.info(f"EnterpriseOrchestrator: Auto-created ticket for event {event.event_id}")
            
        except Exception as e:
            logger.error(f"EnterpriseOrchestrator: Failed to auto-create ticket: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status and health"""
        return {
            'listeners_registered': self.listeners_registered,
            'listener_count': len(self._listener_ids),
            'event_bus_stats': self.event_bus.get_all_listener_counts(),
            'services_status': {
                'dsar': bool(self.dsar_service),
                'ropa': bool(self.ropa_service),
                'consent': bool(self.consent_service),
                'vendor': bool(self.vendor_service),
                'connectors': bool(self.connector_service),
                'ticketing': bool(self.ticketing_service),
                'soc2': bool(self.soc2_service)
            }
        }

# Global orchestrator instance
_orchestrator: Optional[EnterpriseOrchestrator] = None

def get_enterprise_orchestrator(use_redis: bool = True) -> EnterpriseOrchestrator:
    """
    Get or create the global enterprise orchestrator instance
    
    Args:
        use_redis: Enable Redis for distributed events (default: True for scaling)
        
    Returns:
        EnterpriseOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EnterpriseOrchestrator(use_redis=use_redis)
        _orchestrator.register_listeners()
        logger.info("EnterpriseOrchestrator: Initialized global orchestrator with Redis enabled")
    return _orchestrator

def initialize_enterprise_integration(use_redis: bool = True) -> None:
    """
    Initialize enterprise integration system
    
    Should be called once per process to register event listeners globally.
    Uses process-global singletons to prevent duplicate listeners in multi-session environment.
    
    Args:
        use_redis: Enable Redis pub/sub for scaling (default: True - required for production)
    """
    try:
        # Get or create process-global orchestrator (singleton pattern)
        orchestrator = get_enterprise_orchestrator(use_redis)
        logger.info("EnterpriseOrchestrator: Enterprise integration initialized successfully")
        
        # Return orchestrator instance without storing in session state
        # This ensures process-global operation across all sessions
        return orchestrator
            
    except Exception as e:
        logger.error(f"EnterpriseOrchestrator: Failed to initialize enterprise integration: {e}")
        return None

def publish_scan_event(event_type: EventType, user_id: str, session_id: str, 
                      data: Dict[str, Any]) -> None:
    """
    Convenience function to publish scanning events
    
    Args:
        event_type: Type of scan event
        user_id: User ID
        session_id: Session ID  
        data: Event data
    """
    try:
        publish_event(
            event_type=event_type,
            source="scanner",
            user_id=user_id,
            session_id=session_id,
            data=data
        )
    except Exception as e:
        logger.error(f"EnterpriseOrchestrator: Failed to publish scan event: {e}")