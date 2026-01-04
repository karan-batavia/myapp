"""
Scan Limit Manager
Manages daily scan limits and pricing adjustments for DataGuardian Pro users
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import streamlit as st
import logging

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("scan_limit_manager")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)




class ScanLimitManager:
    """Manages daily scan limits and user tier enforcement"""
    
    def __init__(self):
        self.daily_limits = {
            'trial': {
                'daily_scans': 1,  # 1 free scan per email address
                'scan_types': ['code', 'document', 'website', 'ai_model'],
                'features': ['basic_reports'],
                'price': 0,
                'is_lifetime_limit': True  # Trial has lifetime limit, not daily
            },
            'free': {
                'daily_scans': 1,  # 1 free scan per email address
                'scan_types': ['code', 'document'],
                'features': ['basic_reports'],
                'price': 0,
                'is_lifetime_limit': True
            },
            'premium': {
                'daily_scans': 20,
                'scan_types': ['code', 'document', 'image', 'website', 'database'],
                'features': ['basic_reports', 'pdf_reports', 'priority_support'],
                'price': 20.00,  # €20/month as requested
                'original_price': 29.99  # Show savings
            },
            'professional': {
                'daily_scans': 100,
                'scan_types': ['code', 'document', 'image', 'website', 'database', 'api', 'dpia'],
                'features': ['basic_reports', 'pdf_reports', 'html_reports', 'priority_support', 'ai_analysis'],
                'price': 79.99,
                'original_price': 79.99
            },
            'enterprise': {
                'daily_scans': 1000,
                'scan_types': ['all'],
                'features': ['all', 'dedicated_support', 'custom_integrations', 'compliance_certification'],
                'price': 199.99,
                'original_price': 199.99
            }
        }
        
        # Data file for tracking daily usage
        self.usage_file = 'data/daily_usage.json'
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.usage_file):
            with open(self.usage_file, 'w') as f:
                json.dump({}, f)
    
    def get_user_tier(self, username: str) -> str:
        """Get user's subscription tier from session or database"""
        # First check session state
        if 'license_tier' in st.session_state:
            return st.session_state.get('license_tier', 'free')
        
        # Legacy session key check
        user_tier = st.session_state.get(f'{username}_tier')
        if user_tier:
            return user_tier
        
        # Check database for user's tier
        try:
            import psycopg2
            db_url = os.environ.get('DATABASE_URL')
            if db_url:
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT license_tier, metadata FROM platform_users 
                    WHERE username = %s OR email = %s
                """, (username, username))
                row = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if row:
                    license_tier = row[0] or 'free'
                    return license_tier
        except Exception as e:
            logger.debug(f"Could not get user tier from database: {e}")
        
        return 'free'
    
    def set_user_tier(self, username: str, tier: str):
        """Set user's subscription tier"""
        st.session_state[f'{username}_tier'] = tier
        logger.info(f"User {username} tier set to {tier}")
    
    def get_daily_usage(self, username: str, date: str = None) -> Dict[str, int]:
        """Get daily usage for a user"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with open(self.usage_file, 'r') as f:
                usage_data = json.load(f)
            
            user_date_key = f"{username}_{date}"
            return usage_data.get(user_date_key, {})
        
        except Exception as e:
            logger.error(f"Error loading usage data: {e}")
            return {}
    
    def record_scan(self, username: str, scan_type: str) -> bool:
        """Record a scan and check if within limits"""
        date = datetime.now().strftime('%Y-%m-%d')
        user_tier = self.get_user_tier(username)
        
        # Check if scan is allowed
        if not self.can_perform_scan(username, scan_type):
            return False
        
        try:
            # Load current usage
            with open(self.usage_file, 'r') as f:
                usage_data = json.load(f)
            
            user_date_key = f"{username}_{date}"
            if user_date_key not in usage_data:
                usage_data[user_date_key] = {}
            
            # Increment scan count
            if scan_type not in usage_data[user_date_key]:
                usage_data[user_date_key][scan_type] = 0
            
            usage_data[user_date_key][scan_type] += 1
            usage_data[user_date_key]['total'] = usage_data[user_date_key].get('total', 0) + 1
            usage_data[user_date_key]['last_scan'] = datetime.now().isoformat()
            
            # Save updated usage
            with open(self.usage_file, 'w') as f:
                json.dump(usage_data, f, indent=2)
            
            logger.info(f"Recorded {scan_type} scan for {username} (tier: {user_tier})")
            return True
        
        except Exception as e:
            logger.error(f"Error recording scan: {e}")
            return False
    
    def can_perform_scan(self, username: str, scan_type: str) -> Tuple[bool, str]:
        """Check if user can perform a scan"""
        user_tier = self.get_user_tier(username)
        tier_info = self.daily_limits.get(user_tier, self.daily_limits['free'])
        
        # Check scan type permission
        allowed_types = tier_info['scan_types']
        if 'all' not in allowed_types and scan_type not in allowed_types:
            return False, f"Scan type '{scan_type}' not available in {user_tier} tier. Upgrade to access this feature."
        
        # Check daily limit
        daily_usage = self.get_daily_usage(username)
        total_scans = daily_usage.get('total', 0)
        daily_limit = tier_info['daily_scans']
        
        if total_scans >= daily_limit:
            return False, f"Daily scan limit reached ({total_scans}/{daily_limit}). Upgrade your plan or try again tomorrow."
        
        return True, f"Scan allowed ({total_scans + 1}/{daily_limit} daily scans)"
    
    def get_usage_summary(self, username: str) -> Dict[str, any]:
        """Get comprehensive usage summary for user"""
        user_tier = self.get_user_tier(username)
        tier_info = self.daily_limits.get(user_tier, self.daily_limits['free'])
        daily_usage = self.get_daily_usage(username)
        
        total_today = daily_usage.get('total', 0)
        daily_limit = tier_info['daily_scans']
        
        # Calculate usage by scan type
        scan_breakdown = {}
        for scan_type in tier_info['scan_types']:
            if scan_type != 'all':
                count = daily_usage.get(scan_type, 0)
                scan_breakdown[scan_type] = count
        
        return {
            'tier': user_tier,
            'tier_info': tier_info,
            'daily_usage': total_today,
            'daily_limit': daily_limit,
            'remaining_scans': max(0, daily_limit - total_today),
            'usage_percentage': (total_today / daily_limit * 100) if daily_limit > 0 else 0,
            'scan_breakdown': scan_breakdown,
            'last_scan': daily_usage.get('last_scan'),
            'features_available': tier_info['features']
        }
    
    def get_upgrade_recommendations(self, username: str) -> List[Dict[str, any]]:
        """Get upgrade recommendations based on usage patterns"""
        current_tier = self.get_user_tier(username)
        recommendations = []
        
        # Analyze usage pattern for last 7 days
        usage_pattern = self._analyze_usage_pattern(username)
        
        if current_tier == 'free':
            recommendations.append({
                'tier': 'premium',
                'reason': 'Access more scan types and increased daily limits',
                'benefits': ['20 daily scans', 'Database & Website scanning', 'PDF reports'],
                'price': self.daily_limits['premium']['price'],
                'savings': self.daily_limits['premium']['original_price'] - self.daily_limits['premium']['price']
            })
        
        elif current_tier == 'premium':
            if usage_pattern['avg_daily_scans'] > 15:
                recommendations.append({
                    'tier': 'professional',
                    'reason': 'High usage detected - get 5x more daily scans',
                    'benefits': ['100 daily scans', 'AI Analysis', 'DPIA scanner', 'HTML reports'],
                    'price': self.daily_limits['professional']['price']
                })
        
        elif current_tier == 'professional':
            if usage_pattern['avg_daily_scans'] > 75:
                recommendations.append({
                    'tier': 'enterprise',
                    'reason': 'Enterprise usage patterns detected',
                    'benefits': ['1000 daily scans', 'All features', 'Dedicated support'],
                    'price': self.daily_limits['enterprise']['price']
                })
        
        return recommendations
    
    def _analyze_usage_pattern(self, username: str) -> Dict[str, any]:
        """Analyze user's usage pattern over the last 7 days"""
        try:
            with open(self.usage_file, 'r') as f:
                usage_data = json.load(f)
            
            # Get last 7 days of usage
            total_scans = 0
            days_with_usage = 0
            scan_types_used = set()
            
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                user_date_key = f"{username}_{date}"
                
                if user_date_key in usage_data:
                    day_usage = usage_data[user_date_key]
                    daily_total = day_usage.get('total', 0)
                    
                    if daily_total > 0:
                        total_scans += daily_total
                        days_with_usage += 1
                        
                        # Track scan types
                        for scan_type, count in day_usage.items():
                            if scan_type not in ['total', 'last_scan'] and count > 0:
                                scan_types_used.add(scan_type)
            
            avg_daily_scans = total_scans / 7 if total_scans > 0 else 0
            
            return {
                'total_scans_7_days': total_scans,
                'avg_daily_scans': avg_daily_scans,
                'days_with_usage': days_with_usage,
                'scan_types_used': list(scan_types_used),
                'usage_frequency': days_with_usage / 7
            }
        
        except Exception as e:
            logger.error(f"Error analyzing usage pattern: {e}")
            return {
                'total_scans_7_days': 0,
                'avg_daily_scans': 0,
                'days_with_usage': 0,
                'scan_types_used': [],
                'usage_frequency': 0
            }
    
    def display_usage_dashboard(self, username: str):
        """Display usage dashboard in Streamlit"""
        summary = self.get_usage_summary(username)
        
        st.subheader(f"📊 Usage Dashboard - {summary['tier'].title()} Plan")
        
        # Usage metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Today's Scans", 
                summary['daily_usage'],
                delta=f"{summary['remaining_scans']} remaining"
            )
        
        with col2:
            st.metric(
                "Daily Limit", 
                summary['daily_limit'],
                delta=f"{summary['usage_percentage']:.1f}% used"
            )
        
        with col3:
            st.metric("Plan", summary['tier'].title())
        
        with col4:
            price = summary['tier_info']['price']
            if price > 0:
                st.metric("Monthly Cost", f"€{price:.2f}")
            else:
                st.metric("Monthly Cost", "Free")
        
        # Usage progress bar
        progress = min(summary['usage_percentage'] / 100, 1.0)
        st.progress(progress)
        
        if progress > 0.8:
            st.warning("⚠️ You're approaching your daily scan limit. Consider upgrading for more scans.")
        elif progress >= 1.0:
            st.error("❌ Daily scan limit reached. Upgrade your plan or try again tomorrow.")
        
        # Scan breakdown
        if summary['scan_breakdown']:
            st.subheader("📈 Today's Scan Breakdown")
            
            for scan_type, count in summary['scan_breakdown'].items():
                if count > 0:
                    st.write(f"• **{scan_type.title()}**: {count} scans")
        
        # Upgrade recommendations
        recommendations = self.get_upgrade_recommendations(username)
        if recommendations:
            st.subheader("💡 Upgrade Recommendations")
            
            for rec in recommendations:
                with st.expander(f"Upgrade to {rec['tier'].title()} Plan"):
                    st.write(f"**Reason**: {rec['reason']}")
                    st.write("**Benefits**:")
                    for benefit in rec['benefits']:
                        st.write(f"• {benefit}")
                    
                    price = rec['price']
                    st.write(f"**Price**: €{price:.2f}/month")
                    
                    if 'savings' in rec and rec['savings'] > 0:
                        st.success(f"💰 Save €{rec['savings']:.2f}/month with current promotion!")
                    
                    if st.button(f"Upgrade to {rec['tier'].title()}", key=f"upgrade_{rec['tier']}"):
                        st.info("Upgrade functionality will redirect to payment processing.")
    
    def reset_daily_usage(self, username: str, date: str = None):
        """Reset daily usage for testing purposes"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with open(self.usage_file, 'r') as f:
                usage_data = json.load(f)
            
            user_date_key = f"{username}_{date}"
            if user_date_key in usage_data:
                del usage_data[user_date_key]
            
            with open(self.usage_file, 'w') as f:
                json.dump(usage_data, f, indent=2)
            
            logger.info(f"Reset daily usage for {username} on {date}")
            return True
        
        except Exception as e:
            logger.error(f"Error resetting usage: {e}")
            return False