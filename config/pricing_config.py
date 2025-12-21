"""
DataGuardian Pro Pricing Configuration
Flexible pricing system supporting multiple tiers and regions
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class PricingTier(Enum):
    """Pricing tier levels"""
    STARTUP = "startup"
    PROFESSIONAL = "professional"
    GROWTH = "growth" 
    SCALE = "scale"
    SALESFORCE_PREMIUM = "salesforce_premium"  # NEW: Premium Salesforce CRM tier
    SAP_ENTERPRISE = "sap_enterprise"          # NEW: Premium SAP ERP tier
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"

class BillingCycle(Enum):
    """Billing cycle options"""
    MONTHLY = "monthly"
    ANNUAL = "annual"
    ONE_TIME = "one_time"

class PricingConfig:
    """Centralized pricing configuration with flexible updates"""
    
    def __init__(self, region: str = "Netherlands"):
        self.region = region
        self.currency = "EUR"
        self.pricing_data = self._load_pricing_configuration()
        self.features_matrix = self._load_features_matrix()
        self.discounts = self._load_discount_rules()
    
    def _load_pricing_configuration(self) -> Dict[str, Any]:
        """Load current pricing configuration - easily updatable"""
        return {
            "version": "3.0",  # Updated for premium connector pricing
            "last_updated": "2025-09-15", 
            "effective_date": "2025-09-15",  # Premium connector launch
            
            "tiers": {
                PricingTier.STARTUP.value: {
                    "name": "Startup Essential",
                    "description": "Complete GDPR + AI Act compliance for growing startups - 90% cost savings vs OneTrust + 30-day money-back guarantee",
                    "target_employees": "1-25",
                    "target_revenue": "< €1M",
                    "monthly_price": 59,  # Optimized for SME market
                    "annual_price": 590,  # 2 months free incentive
                    "setup_fee": 0,
                    "max_scans_monthly": 200,  
                    "max_data_sources": 20,    
                    "support_level": "priority_email_chat",
                    "sla_hours": 24,
                    "guaranteed_savings": 18000,  
                    "includes_ai_act": True,
                    "netherlands_specialization": True,
                    "free_trial_days": 14,
                    "money_back_guarantee": 30,
                    "onboarding_included": True
                },
                
                PricingTier.PROFESSIONAL.value: {
                    "name": "Professional Plus",
                    "description": "Advanced scanning + compliance automation - Perfect bridge to enterprise features",
                    "target_employees": "15-50",
                    "target_revenue": "€500K - €5M",
                    "monthly_price": 99,  # Strategic gap-filling price
                    "annual_price": 990,  # 2 months free
                    "setup_fee": 0,
                    "max_scans_monthly": 350,
                    "max_data_sources": 35,
                    "support_level": "priority_email_phone",
                    "sla_hours": 16,
                    "guaranteed_savings": 25000,
                    "enterprise_connectors": "basic",  # Limited connectors
                    "ai_act_compliance": True,
                    "compliance_certificates": True,
                    "success_manager": "monthly_email_check_in",
                    "automated_reporting": True,
                    "compliance_dashboard": "advanced"
                },
                
                PricingTier.GROWTH.value: {
                    "name": "Growth Professional",
                    "description": "Enterprise-grade compliance automation + quarterly business reviews - 91% cost savings vs OneTrust (€1,790 vs €19,500)",
                    "target_employees": "25-100", 
                    "target_revenue": "€1M - €10M",
                    "monthly_price": 179,  # Strategic increase for better margins
                    "annual_price": 1790,  # Proportional with 2 months free
                    "setup_fee": 0,
                    "max_scans_monthly": 750,  # Premium unlimited-like experience
                    "max_data_sources": 75,    # Enhanced capacity
                    "support_level": "priority_phone_chat",
                    "sla_hours": 8,   # Further improved
                    "most_popular": True,
                    "guaranteed_savings": 55000,  # Increased value proposition
                    "enterprise_connectors": True,
                    "ai_act_compliance": True,
                    "compliance_certificates": True,
                    "success_manager": "bi_weekly_check_in",
                    "quarterly_business_reviews": True,
                    "compliance_health_score": True,
                    "risk_monitoring_alerts": True
                },
                
                PricingTier.SCALE.value: {
                    "name": "Scale Professional",
                    "description": "Enterprise automation + dedicated support team - 83% cost savings vs OneTrust (€4,990 vs €29,000)",
                    "target_employees": "100-500",
                    "target_revenue": "€10M - €50M", 
                    "monthly_price": 499,  # Premium positioning for maximum value
                    "annual_price": 4990,  # 2 months free
                    "setup_fee": 0,  # Removed to reduce friction
                    "max_scans_monthly": "unlimited",
                    "max_data_sources": "unlimited",
                    "support_level": "dedicated_team_24_7",
                    "sla_hours": 2,   # Premium support
                    "includes_onboarding": True,
                    "guaranteed_savings": 150000,  # Enhanced value
                    "api_access": True,
                    "white_label_option": True,
                    "custom_workflows": True,
                    "success_manager": "weekly_check_in",
                    "dedicated_compliance_team": True,
                    "monthly_compliance_reports": True,
                    "regulatory_change_monitoring": True,
                    "priority_feature_development": True
                },
                
                PricingTier.SALESFORCE_PREMIUM.value: {
                    "name": "Salesforce Premium",
                    "description": "Enterprise CRM compliance with Netherlands BSN/KvK specialization - 82% cost savings vs OneTrust + Salesforce modules (€6,990 vs €38,000)",
                    "target_employees": "50-250",
                    "target_revenue": "€5M - €25M", 
                    "monthly_price": 699,  # Premium Salesforce integration pricing
                    "annual_price": 6990,  # 2 months free
                    "setup_fee": 0,
                    "max_scans_monthly": "unlimited",
                    "max_data_sources": "unlimited",
                    "support_level": "dedicated_team_priority",
                    "sla_hours": 4,   
                    "includes_onboarding": True,
                    "guaranteed_savings": 250000,  # Enhanced savings with CRM integration
                    "salesforce_crm_connector": True,     # Premium feature
                    "netherlands_bsn_advanced": True,     # Advanced BSN detection in CRM
                    "kvk_enterprise_validation": True,    # Enterprise KvK validation
                    "crm_data_mapping": True,             # Advanced CRM field mapping
                    "api_access": True,
                    "custom_workflows": True,
                    "success_manager": "bi_weekly_check_in",
                    "dedicated_compliance_team": True,
                    "monthly_compliance_reports": True,
                    "regulatory_change_monitoring": True,
                    "priority_feature_development": True
                },
                
                PricingTier.SAP_ENTERPRISE.value: {
                    "name": "SAP Enterprise",
                    "description": "Complete SAP ERP compliance with HR/Finance BSN scanning - 75% cost savings vs SAP GRC + OneTrust (€9,990 vs €42,000)",
                    "target_employees": "100-500+",
                    "target_revenue": "€10M - €100M", 
                    "monthly_price": 999,  # Premium SAP integration pricing
                    "annual_price": 9990,  # 2 months free
                    "setup_fee": 0,
                    "max_scans_monthly": "unlimited",
                    "max_data_sources": "unlimited",
                    "support_level": "dedicated_team_24_7",
                    "sla_hours": 2,   # Premium SAP support
                    "includes_onboarding": True,
                    "guaranteed_savings": 400000,  # Maximum ERP compliance savings
                    "sap_erp_connector": True,          # Premium SAP integration
                    "sap_hr_module": True,             # PA0002 Personal Data scanning
                    "sap_finance_module": True,        # KNA1/LFA1 business partner data
                    "netherlands_bsn_advanced": True,  # Advanced BSN detection in ERP
                    "kvk_enterprise_validation": True, # Enterprise KvK validation
                    "erp_data_governance": True,       # Advanced ERP data governance
                    "sap_custom_fields": True,         # Custom SAP field scanning
                    "api_access": True,
                    "custom_integrations": True,
                    "white_label_option": True,
                    "success_manager": "weekly_check_in",
                    "dedicated_compliance_team": True,
                    "monthly_compliance_reports": True,
                    "regulatory_change_monitoring": True,
                    "priority_feature_development": True,
                    "sap_consulting_hours": 20         # SAP-specific compliance consulting
                },
                
                PricingTier.ENTERPRISE.value: {
                    "name": "Enterprise Ultimate + Premium Connectors",
                    "description": "Complete platform + Salesforce & SAP integration - 78% cost savings vs OneTrust Enterprise + modules (€13,990 vs €65,000)",
                    "target_employees": "200+",
                    "target_revenue": "€25M+", 
                    "monthly_price": 1399,  # Premium pricing with Salesforce + SAP value
                    "annual_price": 13990,  # 2 months free
                    "setup_fee": 0,  # Executive-level service includes setup
                    "max_scans_monthly": "unlimited",
                    "max_data_sources": "unlimited", 
                    "support_level": "executive_partnership_24_7",
                    "sla_hours": 1,  # Ultra-premium response
                    "includes_onboarding": True,
                    "custom_integrations": True,
                    "guaranteed_savings": 500000,  # Enhanced with premium connectors
                    "salesforce_crm_connector": True,  # NEW: Premium Salesforce CRM integration
                    "sap_erp_connector": True,        # NEW: Premium SAP ERP integration  
                    "dutch_banking_connector": True,  # NEW: PSD2 banking integration
                    "netherlands_bsn_advanced": True, # NEW: Advanced BSN validation & compliance
                    "kvk_enterprise_validation": True, # NEW: Enterprise KvK number validation
                    "dedicated_success_team": True,
                    "monthly_executive_reviews": True,
                    "legal_consultation_hours": 40,  
                    "priority_feature_requests": True,
                    "source_code_escrow": True,
                    "strategic_compliance_consulting": True,
                    "regulatory_representation": True,
                    "custom_training_programs": True
                },
                
                PricingTier.GOVERNMENT.value: {
                    "name": "Government & Enterprise License",
                    "description": "On-premises deployment for government and large enterprises",
                    "target_employees": "Any",
                    "target_revenue": "Any",
                    "monthly_price": 0,  # One-time license
                    "license_price": 15000,
                    "annual_maintenance": 2500,
                    "billing_cycle": BillingCycle.ONE_TIME.value,
                    "deployment": "on_premises",
                    "max_scans_monthly": "unlimited",
                    "max_data_sources": "unlimited",
                    "source_code_access": True,
                    "custom_development": True,
                    "support_level": "enterprise",
                    "sla_hours": 2
                }
            }
        }
    
    def _load_features_matrix(self) -> Dict[str, Dict[str, List[str]]]:
        """Define features available per tier"""
        return {
            "core_features": {
                "basic_pii_scanning": [PricingTier.STARTUP.value, PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "gdpr_compliance_reports": [PricingTier.STARTUP.value, PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "netherlands_bsn_detection": [PricingTier.STARTUP.value, PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "multi_language_support": [PricingTier.STARTUP.value, PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value]
            },
            
            "advanced_scanners": {
                "enterprise_connectors": [PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "microsoft365_integration": [PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value], 
                "exact_online_connector": [PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "google_workspace_integration": [PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "salesforce_crm_connector": [PricingTier.SALESFORCE_PREMIUM.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],  # NEW: Premium Salesforce CRM
                "sap_erp_connector": [PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],  # NEW: Premium SAP ERP
                "dutch_banking_connector": [PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],  # NEW: PSD2 Banking
                "netherlands_bsn_advanced": [PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],  # NEW: Advanced BSN
                "kvk_enterprise_validation": [PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],  # NEW: Enterprise KvK
                "ai_model_scanning": [PricingTier.STARTUP.value, PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "audio_video_deepfake_detection": [PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "advanced_ai_analysis": [PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "netherlands_bsn_detection": [PricingTier.STARTUP.value, PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "automated_reporting": [PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value]
            },
            
            "compliance_features": {
                "compliance_certificates": [PricingTier.STARTUP.value, PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "dpia_automation": [PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "eu_ai_act_compliance": [PricingTier.STARTUP.value, PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "cost_savings_calculator": [PricingTier.STARTUP.value, PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "guaranteed_savings": [PricingTier.STARTUP.value, PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "netherlands_uavg_specialization": [PricingTier.STARTUP.value, PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "risk_monitoring_alerts": [PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value]
            },
            
            "enterprise_features": {
                "api_access": [PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "white_label_deployment": [PricingTier.SCALE.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "custom_integrations": [PricingTier.SCALE.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "custom_workflows": [PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],  # NEW: Custom workflow automation
                "crm_data_mapping": [PricingTier.SALESFORCE_PREMIUM.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],  # NEW: Advanced CRM field mapping
                "erp_data_governance": [PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],  # NEW: ERP data governance
                "sap_consulting_hours": [PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],  # NEW: SAP-specific consulting
                "dedicated_support": [PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "success_manager": [PricingTier.PROFESSIONAL.value, PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "on_premises_deployment": [PricingTier.GOVERNMENT.value],
                "source_code_access": [PricingTier.GOVERNMENT.value],
                "legal_consultation": [PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "quarterly_business_reviews": [PricingTier.GROWTH.value, PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value],
                "regulatory_change_monitoring": [PricingTier.SCALE.value, PricingTier.SALESFORCE_PREMIUM.value, PricingTier.SAP_ENTERPRISE.value, PricingTier.ENTERPRISE.value, PricingTier.GOVERNMENT.value]
            }
        }
    
    def _load_discount_rules(self) -> Dict[str, Any]:
        """Define discount rules and promotional offers"""
        return {
            "annual_discount": {
                "description": "2 months free on annual billing",
                "discount_months": 2,
                "min_tier": PricingTier.STARTUP.value
            },
            
            "volume_discounts": {
                "multi_year": {
                    "2_year": 0.10,  # 10% discount
                    "3_year": 0.15,  # 15% discount
                },
                "multiple_licenses": {
                    "3-5_licenses": 0.05,   # 5% discount
                    "6-10_licenses": 0.10,  # 10% discount
                    "11+_licenses": 0.15    # 15% discount
                }
            },
            
            "promotional": {
                "early_adopter": {
                    "discount": 0.25,  # Increased to 25% off first year
                    "valid_until": "2025-12-31",
                    "description": "Early adopter discount - Limited time"
                },
                "exact_online_users": {
                    "discount": 0.20,  # Increased to 20% off
                    "description": "Exact Online customer special pricing",
                    "verification_required": True
                },
                "annual_upgrade": {
                    "discount": 0.30,  # 30% off first year when upgrading to annual
                    "description": "Upgrade to annual billing - Maximum savings",
                    "min_tier": PricingTier.PROFESSIONAL.value
                },
                "netherlands_business": {
                    "discount": 0.15,  # 15% off for Netherlands KvK registered businesses
                    "description": "Netherlands business discount",
                    "verification_required": True
                }
            }
        }
    
    def get_tier_pricing(self, tier: PricingTier, billing_cycle: BillingCycle = BillingCycle.MONTHLY) -> Dict[str, Any]:
        """Get pricing for specific tier and billing cycle"""
        tier_data = self.pricing_data["tiers"].get(tier.value)
        if not tier_data:
            raise ValueError(f"Invalid pricing tier: {tier.value}")
        
        pricing = {
            "tier": tier.value,
            "name": tier_data["name"],
            "description": tier_data["description"],
            "billing_cycle": billing_cycle.value,
            "currency": self.currency
        }
        
        if billing_cycle == BillingCycle.MONTHLY:
            pricing["price"] = tier_data["monthly_price"]
            pricing["billing_frequency"] = "monthly"
        elif billing_cycle == BillingCycle.ANNUAL:
            # Handle Government tier which uses license_price instead of annual_price
            if tier == PricingTier.GOVERNMENT:
                pricing["price"] = tier_data.get("license_price", 15000)
                pricing["billing_frequency"] = "one_time"
                pricing["maintenance_fee"] = tier_data.get("annual_maintenance", 2500)
            else:
                pricing["price"] = tier_data["annual_price"]
                pricing["billing_frequency"] = "annual"
                pricing["savings"] = (tier_data["monthly_price"] * 12) - tier_data["annual_price"]
                pricing["discount_percentage"] = round((pricing["savings"] / (tier_data["monthly_price"] * 12)) * 100)
        elif billing_cycle == BillingCycle.ONE_TIME and tier == PricingTier.GOVERNMENT:
            pricing["price"] = tier_data["license_price"]
            pricing["maintenance_fee"] = tier_data["annual_maintenance"]
            pricing["billing_frequency"] = "one_time"
        
        return pricing
    
    def get_features_for_tier(self, tier: PricingTier) -> List[str]:
        """Get list of features available for specific tier"""
        available_features = []
        
        for category, features in self.features_matrix.items():
            for feature, tiers in features.items():
                if isinstance(tiers, list) and tier.value in tiers:
                    available_features.append(feature)
        
        return available_features
    
    def calculate_pricing_with_discounts(self, tier: PricingTier, billing_cycle: BillingCycle, 
                                       discount_code: Optional[str] = None,
                                       quantity: int = 1) -> Dict[str, Any]:
        """Calculate final pricing with applicable discounts"""
        
        base_pricing = self.get_tier_pricing(tier, billing_cycle)
        base_price = base_pricing["price"]
        
        discounts_applied = []
        total_discount = 0
        
        # Volume discount
        if quantity > 1:
            volume_rules = self.discounts["volume_discounts"]["multiple_licenses"]
            if quantity >= 11:
                discount = volume_rules["11+_licenses"]
                discounts_applied.append(f"Volume discount (11+ licenses): {discount*100}%")
                total_discount += discount
            elif quantity >= 6:
                discount = volume_rules["6-10_licenses"] 
                discounts_applied.append(f"Volume discount (6-10 licenses): {discount*100}%")
                total_discount += discount
            elif quantity >= 3:
                discount = volume_rules["3-5_licenses"]
                discounts_applied.append(f"Volume discount (3-5 licenses): {discount*100}%")
                total_discount += discount
        
        # Promotional discount
        if discount_code:
            promo = self.discounts["promotional"].get(discount_code)
            if promo:
                # Check validity
                if "valid_until" in promo:
                    valid_until = datetime.strptime(promo["valid_until"], "%Y-%m-%d")
                    if datetime.now() <= valid_until:
                        total_discount += promo["discount"]
                        discounts_applied.append(f"{promo['description']}: {promo['discount']*100}%")
                else:
                    total_discount += promo["discount"]
                    discounts_applied.append(f"{promo['description']}: {promo['discount']*100}%")
        
        # Cap total discount at 40%
        total_discount = min(total_discount, 0.40)
        
        final_price = base_price * (1 - total_discount) * quantity
        discount_amount = (base_price * quantity) - final_price
        
        return {
            **base_pricing,
            "quantity": quantity,
            "base_total": base_price * quantity,
            "discount_percentage": round(total_discount * 100, 1),
            "discount_amount": round(discount_amount, 2),
            "final_price": round(final_price, 2),
            "discounts_applied": discounts_applied,
            "per_unit_price": round(final_price / quantity, 2)
        }
    
    def get_competitive_comparison(self, tier: PricingTier) -> Dict[str, Any]:
        """Get competitive pricing comparison"""
        tier_data = self.pricing_data["tiers"].get(tier.value)
        
        competitor_costs = {
            PricingTier.STARTUP.value: {"onetrust": 6000, "privacera": 4500, "basic_tools": 3000},
            PricingTier.PROFESSIONAL.value: {"onetrust_pro": 12000, "bigid_essentials": 9500, "mid_tools": 8000},
            PricingTier.GROWTH.value: {"onetrust": 19500, "bigid_starter": 15000, "mid_tier": 12000},
            PricingTier.SCALE.value: {"onetrust": 29000, "bigid": 45000, "varonis": 38000},
            PricingTier.SALESFORCE_PREMIUM.value: {"onetrust_salesforce": 38000, "salesforce_shield": 25000, "crm_compliance_stack": 42000},
            PricingTier.SAP_ENTERPRISE.value: {"sap_grc": 42000, "onetrust_sap": 50000, "erp_compliance_suite": 65000},
            PricingTier.ENTERPRISE.value: {"onetrust_enterprise": 65000, "bigid_full_stack": 85000, "varonis_enterprise": 75000},
            PricingTier.GOVERNMENT.value: {"enterprise_deployment": 180000, "government_suite": 200000}
        }
        
        our_price = tier_data.get("annual_price", tier_data.get("license_price", 0))
        competitors = competitor_costs.get(tier.value, {})
        
        comparisons = []
        for competitor, cost in competitors.items():
            savings = cost - our_price
            percentage = round((savings / cost) * 100, 1)
            comparisons.append({
                "competitor": competitor.replace("_", " ").title(),
                "competitor_cost": cost,
                "our_price": our_price,
                "savings": savings,
                "savings_percentage": percentage
            })
        
        return {
            "tier": tier.value,
            "our_annual_price": our_price,
            "comparisons": comparisons
        }
    
    def update_pricing(self, updates: Dict[str, Any]) -> bool:
        """Update pricing configuration (for admin use)"""
        try:
            # Update version and timestamp
            self.pricing_data["version"] = str(float(self.pricing_data["version"]) + 0.1)
            self.pricing_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
            
            # Apply updates
            if "tiers" in updates:
                for tier_name, tier_updates in updates["tiers"].items():
                    if tier_name in self.pricing_data["tiers"]:
                        self.pricing_data["tiers"][tier_name].update(tier_updates)
            
            if "discounts" in updates:
                self.discounts.update(updates["discounts"])
            
            return True
        except Exception as e:
            print(f"Error updating pricing: {e}")
            return False

# Global pricing instance
_pricing_config = None

def get_pricing_config(region: str = "Netherlands") -> PricingConfig:
    """Get global pricing configuration instance"""
    global _pricing_config
    if _pricing_config is None or _pricing_config.region != region:
        _pricing_config = PricingConfig(region)
    return _pricing_config

# Convenience functions for common operations
def get_all_tiers() -> List[Dict[str, Any]]:
    """Get all pricing tiers including new premium connectors"""
    config = get_pricing_config()
    return [config.get_tier_pricing(tier) for tier in PricingTier if tier != PricingTier.GOVERNMENT]

def get_tier_features(tier_name: str) -> List[str]:
    """Get features for tier by name"""
    config = get_pricing_config()
    tier = PricingTier(tier_name)
    return config.get_features_for_tier(tier)

def calculate_savings_vs_competitors(tier_name: str) -> Dict[str, Any]:
    """Calculate savings vs competitors for tier"""
    config = get_pricing_config() 
    tier = PricingTier(tier_name)
    return config.get_competitive_comparison(tier)