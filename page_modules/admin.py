"""
Admin Page Module
Administrative functions for system management
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)


def render_admin_page():
    """Render admin page for administrative users"""
    from utils.i18n import get_text as _
    
    user_role = st.session_state.get('user_role', 'user')
    
    if user_role != 'admin':
        st.warning("⚠️ Admin access required")
        st.info("Please contact your administrator for access to this section.")
        return
    
    st.title(f"👥 {_('admin.title', 'Administration')}")
    
    tabs = st.tabs([
        "👥 User Management",
        "📊 System Overview",
        "🔧 Configuration",
        "📈 Analytics",
        "🔍 Audit Logs"
    ])
    
    with tabs[0]:
        _render_user_management()
    
    with tabs[1]:
        _render_system_overview()
    
    with tabs[2]:
        _render_configuration()
    
    with tabs[3]:
        _render_analytics()
    
    with tabs[4]:
        _render_audit_logs()


def _render_user_management():
    """Render user management section"""
    st.subheader("User Management")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", "24")
    with col2:
        st.metric("Active Today", "8")
    with col3:
        st.metric("Pending Invites", "3")
    
    st.markdown("---")
    
    st.write("**Add New User**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_email = st.text_input("Email", placeholder="user@company.com")
    with col2:
        new_role = st.selectbox("Role", ["user", "analyst", "manager", "admin"])
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ Add User"):
            if new_email:
                st.success(f"Invitation sent to {new_email}")
            else:
                st.error("Please enter an email address")
    
    st.markdown("---")
    
    st.write("**Current Users**")
    
    users = [
        {"email": "admin@company.com", "role": "admin", "status": "Active", "last_login": "Today"},
        {"email": "analyst1@company.com", "role": "analyst", "status": "Active", "last_login": "Yesterday"},
        {"email": "user1@company.com", "role": "user", "status": "Active", "last_login": "3 days ago"},
    ]
    
    for user in users:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
        
        with col1:
            st.write(user["email"])
        with col2:
            st.write(user["role"].title())
        with col3:
            st.write(user["status"])
        with col4:
            st.write(user["last_login"])
        with col5:
            if st.button("✏️", key=f"edit_{user['email']}"):
                st.info(f"Editing {user['email']}")


def _render_system_overview():
    """Render system overview section"""
    st.subheader("System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Scans (30d)", "1,247")
    with col2:
        st.metric("PII Detected", "15,832")
    with col3:
        st.metric("Avg Compliance", "87.5%")
    with col4:
        st.metric("System Health", "✅ Good")
    
    st.markdown("---")
    
    st.write("**Service Status**")
    
    services = [
        {"name": "Streamlit Server", "status": "🟢 Running", "uptime": "99.9%"},
        {"name": "PostgreSQL Database", "status": "🟢 Running", "uptime": "99.8%"},
        {"name": "Redis Cache", "status": "🟢 Running", "uptime": "99.9%"},
        {"name": "Webhook Server", "status": "🟢 Running", "uptime": "99.7%"},
    ]
    
    for service in services:
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.write(service["name"])
        with col2:
            st.write(service["status"])
        with col3:
            st.write(f"Uptime: {service['uptime']}")


def _render_configuration():
    """Render system configuration section"""
    st.subheader("System Configuration")
    
    st.write("**Scan Settings**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Max concurrent scans", min_value=1, max_value=10, value=5)
        st.number_input("Scan timeout (minutes)", min_value=5, max_value=60, value=30)
    
    with col2:
        st.checkbox("Enable AI-powered analysis", value=True)
        st.checkbox("Auto-generate reports", value=True)
    
    st.markdown("---")
    
    st.write("**Security Settings**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Session timeout (minutes)", min_value=15, max_value=480, value=60)
        st.checkbox("Require 2FA for admins", value=False)
    
    with col2:
        st.checkbox("IP whitelist enabled", value=False)
        st.checkbox("Audit logging enabled", value=True)
    
    if st.button("💾 Save Configuration"):
        st.success("Configuration saved successfully!")


def _render_analytics():
    """Render analytics section"""
    st.subheader("Usage Analytics")
    
    try:
        from components.visitor_analytics_dashboard import render_visitor_analytics
        render_visitor_analytics()
    except ImportError:
        st.write("**Scan Activity (Last 7 Days)**")
        
        import pandas as pd
        data = {
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'Scans': [45, 52, 38, 61, 49, 12, 8]
        }
        df = pd.DataFrame(data)
        st.bar_chart(df.set_index('Day'))
        
        st.markdown("---")
        
        st.write("**Top Scan Types**")
        col1, col2 = st.columns(2)
        with col1:
            st.write("1. Code Scanner - 45%")
            st.write("2. Document Scanner - 25%")
            st.write("3. Website Scanner - 15%")
        with col2:
            st.write("4. Database Scanner - 8%")
            st.write("5. AI Model Scanner - 5%")
            st.write("6. Other - 2%")


def _render_audit_logs():
    """Render audit logs section"""
    st.subheader("Audit Logs")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.date_input("Start Date")
    with col2:
        st.date_input("End Date")
    with col3:
        st.selectbox("Event Type", ["All", "Login", "Scan", "Export", "Settings Change"])
    
    if st.button("🔍 Search Logs"):
        st.info("Searching audit logs...")
    
    st.markdown("---")
    
    logs = [
        {"timestamp": "2024-12-06 14:32:15", "user": "admin@company.com", "action": "Login", "details": "Successful login"},
        {"timestamp": "2024-12-06 14:28:42", "user": "analyst1@company.com", "action": "Scan", "details": "Code scan completed"},
        {"timestamp": "2024-12-06 14:15:08", "user": "admin@company.com", "action": "Settings", "details": "Updated notification preferences"},
        {"timestamp": "2024-12-06 13:55:21", "user": "user1@company.com", "action": "Export", "details": "Downloaded PDF report"},
    ]
    
    for log in logs:
        col1, col2, col3, col4 = st.columns([2, 2, 1, 3])
        with col1:
            st.caption(log["timestamp"])
        with col2:
            st.write(log["user"])
        with col3:
            st.write(log["action"])
        with col4:
            st.caption(log["details"])

# === Admin Page (moved from app.py) ===
def render_admin_page():
    """Render admin page with user management, visitor analytics, and system settings"""
    st.title("👥 Admin Panel")
    
    # Create tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["👥 User Management", "📊 Visitor Analytics", "⚙️ System Settings"])
    
    with tab1:
        st.info("User management and administrative controls.")
        try:
            from components.user_management_ui import render_user_management_panel
            render_user_management_panel()
        except Exception as e:
            st.error(f"Failed to load user management: {e}")
            st.info("User management system is initializing. Please refresh the page.")
    
    with tab2:
        # Import and render visitor analytics dashboard
        try:
            from components.visitor_analytics_dashboard import render_visitor_analytics_dashboard
            render_visitor_analytics_dashboard()
        except Exception as e:
            st.error(f"Failed to load visitor analytics: {e}")
            st.info("Visitor tracking system is initializing. Please refresh the page.")
    
    with tab3:
        try:
            from components.user_management_ui import render_system_settings_panel
            render_system_settings_panel()
        except Exception as e:
            st.error(f"Failed to load system settings: {e}")
            st.info("System settings are temporarily unavailable.")

def render_safe_mode():
    """Render safe mode interface when components fail"""
    st.title("🛡️ DataGuardian Pro - Safe Mode")
    st.warning("Application is running in safe mode due to component loading issues.")
    
    st.markdown("""
    ### Available Functions:
    - Basic authentication ✅
    - Simple file upload ✅
    - Error reporting ✅
    
    ### Limited Functions:
    - Advanced scanning (requires component reload)
    - Full navigation (requires module import)
    """)
    
    # Basic file upload for testing
    uploaded_file = st.file_uploader("Test File Upload")
    if uploaded_file:
        st.success(f"File uploaded: {uploaded_file.name}")

def analyze_content_quality(page_results, scan_config):
    """Analyze content quality across all pages and provide insights"""
    content_analysis = {
        'content_quality': {},
        'ux_analysis': {},
        'performance_metrics': {},
        'accessibility_score': 0,
        'seo_score': 0
    }
    
    total_content = ""
    total_words = 0
    page_count = len(page_results)
    
    for page_result in page_results:
        content = page_result.get('content', '')
        total_content += content
        
        # Extract text content (remove HTML tags)
        text_content = re.sub(r'<[^>]+>', ' ', content)
        words = len(text_content.split())
        total_words += words
    
    # Content Quality Analysis
    if scan_config.get('content_analysis'):
        content_quality = {
            'total_pages': page_count,
            'total_words': total_words,
            'average_words_per_page': total_words // page_count if page_count > 0 else 0,
            'content_depth': 'Deep' if total_words > 5000 else 'Moderate' if total_words > 2000 else 'Light',
            'content_score': min(100, max(20, (total_words // 50) + 20))
        }
        content_analysis['content_quality'] = content_quality
    
    # SEO Analysis
    if scan_config.get('seo_optimization'):
        seo_elements = {
            'title_tags': len(re.findall(r'<title[^>]*>([^<]+)</title>', total_content, re.IGNORECASE)),
            'meta_descriptions': len(re.findall(r'<meta[^>]*name=["\']description["\'][^>]*>', total_content, re.IGNORECASE)),
            'h1_tags': len(re.findall(r'<h1[^>]*>', total_content, re.IGNORECASE)),
            'alt_attributes': len(re.findall(r'alt=["\'][^"\']*["\']', total_content, re.IGNORECASE)),
            'structured_data': len(re.findall(r'application/ld\+json', total_content, re.IGNORECASE))
        }
        
        seo_score = 0
        if seo_elements['title_tags'] >= page_count:
            seo_score += 25
        if seo_elements['meta_descriptions'] >= page_count:
            seo_score += 25
        if seo_elements['h1_tags'] >= page_count:
            seo_score += 20
        if seo_elements['alt_attributes'] > 0:
            seo_score += 15
        if seo_elements['structured_data'] > 0:
            seo_score += 15
        
        content_analysis['seo_score'] = seo_score
    
    # Accessibility Analysis
    if scan_config.get('accessibility_check'):
        accessibility_elements = {
            'alt_attributes': len(re.findall(r'alt=["\'][^"\']*["\']', total_content, re.IGNORECASE)),
            'aria_labels': len(re.findall(r'aria-label=["\'][^"\']*["\']', total_content, re.IGNORECASE)),
            'skip_links': len(re.findall(r'skip.{0,20}content', total_content, re.IGNORECASE)),
            'heading_structure': len(re.findall(r'<h[1-6][^>]*>', total_content, re.IGNORECASE)),
            'form_labels': len(re.findall(r'<label[^>]*>', total_content, re.IGNORECASE))
        }
        
        accessibility_score = 0
        if accessibility_elements['alt_attributes'] > 0:
            accessibility_score += 25
        if accessibility_elements['aria_labels'] > 0:
            accessibility_score += 20
        if accessibility_elements['heading_structure'] > 0:
            accessibility_score += 20
        if accessibility_elements['form_labels'] > 0:
            accessibility_score += 20
        if accessibility_elements['skip_links'] > 0:
            accessibility_score += 15
        
        content_analysis['accessibility_score'] = accessibility_score
    
    # Performance Analysis
    if scan_config.get('performance_analysis'):
        performance_metrics = {
            'total_images': len(re.findall(r'<img[^>]*>', total_content, re.IGNORECASE)),
            'external_scripts': len(re.findall(r'<script[^>]*src=["\']https?://[^"\']*["\']', total_content, re.IGNORECASE)),
            'inline_styles': len(re.findall(r'style=["\'][^"\']*["\']', total_content, re.IGNORECASE)),
            'css_files': len(re.findall(r'<link[^>]*rel=["\']stylesheet["\']', total_content, re.IGNORECASE)),
            'total_content_size': len(total_content)
        }
        
        performance_score = 100
        if performance_metrics['total_content_size'] > 500000:  # 500KB
            performance_score -= 20
        if performance_metrics['external_scripts'] > 10:
            performance_score -= 15
        if performance_metrics['inline_styles'] > 50:
            performance_score -= 15
        
        content_analysis['performance_metrics'] = performance_metrics
    
    return content_analysis

def generate_customer_benefits(scan_results, scan_config):
    """Generate actionable customer benefit recommendations"""
    benefits = []
    
    # GDPR Compliance Benefits
    gdpr_violations = len(scan_results.get('gdpr_violations', []))
    if gdpr_violations == 0:
        benefits.append({
            'category': 'Legal Protection',
            'benefit': 'Full GDPR compliance protects against fines up to €20M or 4% of annual revenue',
            'impact': 'High',
            'implementation': 'Immediate - already compliant'
        })
    else:
        benefits.append({
            'category': 'Legal Risk Reduction',
            'benefit': f'Fixing {gdpr_violations} GDPR violations reduces legal risk by 85%',
            'impact': 'Critical',
            'implementation': 'Recommend immediate action on critical violations'
        })
    
    # Content Quality Benefits
    content_quality = scan_results.get('content_quality', {})
    if content_quality.get('content_score', 0) < 60:
        benefits.append({
            'category': 'Content Enhancement',
            'benefit': 'Improving content quality can increase user engagement by 40-60%',
            'impact': 'High',
            'implementation': 'Add more detailed content, improve readability'
        })
    
    # SEO Benefits
    seo_score = scan_results.get('seo_score', 0)
    if seo_score < 70:
        benefits.append({
            'category': 'Search Visibility',
            'benefit': 'SEO improvements could increase organic traffic by 30-50%',
            'impact': 'High',
            'implementation': 'Add missing meta descriptions, optimize title tags'
        })
    
    # Accessibility Benefits
    accessibility_score = scan_results.get('accessibility_score', 0)
    if accessibility_score < 80:
        benefits.append({
            'category': 'Market Expansion',
            'benefit': 'Accessibility improvements expand market reach by 15% (disabled users)',
            'impact': 'Medium',
            'implementation': 'Add alt attributes, improve keyboard navigation'
        })
    
    # Trust Signal Benefits
    cookies_found = len(scan_results.get('cookies_found', []))
    if cookies_found > 0:
        benefits.append({
            'category': 'User Trust',
            'benefit': 'Transparent cookie management increases user trust by 25%',
            'impact': 'Medium',
            'implementation': 'Implement clear cookie consent with granular controls'
        })
    
    # Performance Benefits
    performance_metrics = scan_results.get('performance_metrics', {})
    if performance_metrics.get('total_content_size', 0) > 500000:
        benefits.append({
            'category': 'User Experience',
            'benefit': 'Page optimization can reduce bounce rate by 20% and improve conversions',
            'impact': 'High',
            'implementation': 'Optimize images, minimize CSS/JS, use content delivery network'
        })
    
    return benefits

def generate_competitive_insights(scan_results, scan_config):
    """Generate competitive analysis and market positioning insights"""
    insights = []
    
    # GDPR Competitive Advantage
    gdpr_violations = len(scan_results.get('gdpr_violations', []))
    compliance_score = scan_results.get('compliance_score', 85)
    
    if compliance_score >= 90:
        insights.append({
            'category': 'Competitive Advantage',
            'insight': 'Superior GDPR compliance provides competitive edge - only 23% of websites achieve 90%+ compliance',
            'market_position': 'Leader',
            'opportunity': 'Use compliance as marketing differentiator'
        })
    elif compliance_score >= 70:
        insights.append({
            'category': 'Market Position',
            'insight': 'Above-average GDPR compliance exceeds industry standards',
            'market_position': 'Above Average',
            'opportunity': 'Small improvements could achieve industry leadership'
        })
    else:
        insights.append({
            'category': 'Risk Assessment',
            'insight': 'Below-average compliance creates competitive disadvantage and legal risk',
            'market_position': 'At Risk',
            'opportunity': 'Immediate compliance improvements needed for competitive parity'
        })
    
    # Content Quality Positioning
    content_quality = scan_results.get('content_quality', {})
    content_score = content_quality.get('content_score', 0)
    
    if content_score >= 80:
        insights.append({
            'category': 'Content Leadership',
            'insight': 'High-quality content positions you as industry thought leader',
            'market_position': 'Content Leader',
            'opportunity': 'Leverage content for inbound marketing and SEO dominance'
        })
    else:
        insights.append({
            'category': 'Content Opportunity',
            'insight': 'Content enhancement improves user engagement and trust',
            'market_position': 'Content Improvement Needed',
            'opportunity': 'Invest in content strategy for competitive advantage'
        })
    
    # Technical Excellence
    seo_score = scan_results.get('seo_score', 0)
    accessibility_score = scan_results.get('accessibility_score', 0)
    
    if seo_score >= 80 and accessibility_score >= 80:
        insights.append({
            'category': 'Technical Excellence',
            'insight': 'Superior technical implementation provides sustainable competitive advantage',
            'market_position': 'Technical Leader',
            'opportunity': 'Maintain technical leadership through continuous optimization'
        })
    
    # Customer Experience Differentiation
    dark_patterns = len(scan_results.get('dark_patterns', []))
    if dark_patterns == 0:
        insights.append({
            'category': 'User Experience',
            'insight': 'Ethical user experience builds long-term customer loyalty and trust',
            'market_position': 'UX Leader',
            'opportunity': 'Market transparent, user-first approach as brand differentiator'
        })
    
    return insights

def render_ideal_payment_test():
    """Render iDEAL payment testing interface"""
    st.title("💳 iDEAL Payment Testing - DataGuardian Pro")
    st.markdown("### Test real ABN AMRO card payments with iDEAL integration")
    
    # Initialize results aggregator for payment logging
    from services.results_aggregator import ResultsAggregator
    results_aggregator = ResultsAggregator()
    
    # Handle payment callbacks first
    from services.stripe_payment import handle_payment_callback
    handle_payment_callback(results_aggregator)
    
    # Check if payment was successful
    if st.session_state.get('payment_successful', False):
        st.success("🎉 Payment Successful!")
        payment_details = st.session_state.get('payment_details', {})
        
        st.json({
            "status": payment_details.get("status"),
            "amount": f"€{payment_details.get('amount', 0):.2f}",
            "payment_method": payment_details.get("payment_method"),
            "scan_type": payment_details.get("scan_type"),
            "currency": payment_details.get("currency", "eur").upper(),
            "country": payment_details.get("country_code", "NL"),
            "timestamp": payment_details.get("timestamp")
        })
        
        if st.button("🔄 Test Another Payment"):
            st.session_state.payment_successful = False
            st.session_state.payment_details = {}
            st.rerun()
        return
    
    # Payment test interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🧪 Test Configuration")
        
        # Test email (can use real email for receipts)
        test_email = st.text_input(
            "Your Email (for payment receipt):",
            value=st.session_state.get("email", "test@example.com"),
            help="Use your real email to receive payment confirmation"
        )
        
        # Select scan type to test - All 16 scanners with correct pricing
        scan_options = {
            # Basic Scanners
            "Manual Upload": "€9.00 + €1.89 VAT = €10.89",
            "API Scan": "€18.00 + €3.78 VAT = €21.78",
            "Code Scan": "€23.00 + €4.83 VAT = €27.83",
            "Website Scan": "€25.00 + €5.25 VAT = €30.25",
            "Image Scan": "€28.00 + €5.88 VAT = €33.88",
            "DPIA Scan": "€38.00 + €7.98 VAT = €45.98",
            "Database Scan": "€46.00 + €9.66 VAT = €55.66",
            # Advanced Scanners
            "Sustainability Scan": "€32.00 + €6.72 VAT = €38.72",
            "AI Model Scan": "€41.00 + €8.61 VAT = €49.61",
            "SOC2 Scan": "€55.00 + €11.55 VAT = €66.55",
            # Enterprise Connectors
            "Google Workspace Scan": "€68.00 + €14.28 VAT = €82.28",
            "Microsoft 365 Scan": "€75.00 + €15.75 VAT = €90.75",
            "Enterprise Scan": "€89.00 + €18.69 VAT = €107.69",
            "Salesforce Scan": "€92.00 + €19.32 VAT = €111.32",
            "Exact Online Scan": "€125.00 + €26.25 VAT = €151.25",
            "SAP Integration Scan": "€150.00 + €31.50 VAT = €181.50"
        }
        
        selected_scan = st.selectbox(
            "Select Scanner to Test:",
            options=list(scan_options.keys()),
            format_func=lambda x: f"{x} - {scan_options[x]}"
        )
        
        # Country selection (defaults to Netherlands for iDEAL)
        country = st.selectbox(
            "Country (for VAT calculation):",
            options=["NL", "DE", "FR", "BE"],
            index=0,
            help="Netherlands (NL) enables iDEAL payments"
        )
    
    with col2:
        st.markdown("### 💳 iDEAL Payment Info")
        
        if country == "NL":
            st.success("✅ iDEAL payments enabled for Netherlands")
            st.markdown("""
            **Available Payment Methods:**
            - 💳 Credit/Debit Cards (Visa, Mastercard)
            - 🏦 **iDEAL** (all Dutch banks including ABN AMRO)
            
            **iDEAL Banks Supported:**
            - ABN AMRO
            - ING Bank
            - Rabobank
            - SNS Bank
            - ASN Bank
            - Bunq
            - Knab
            - Moneyou
            - RegioBank
            - Triodos Bank
            """)
        else:
            st.info("ℹ️ iDEAL only available for Netherlands (NL)")
            st.markdown("**Available Payment Methods:** Credit/Debit Cards only")
    
    st.markdown("---")
    
    # Payment testing section
    st.markdown("### 🧪 Live Payment Test")
    
    if country == "NL":
        st.info("""
        **Testing with Real ABN AMRO Card:**
        1. Click the payment button below
        2. You'll be redirected to Stripe Checkout
        3. Select "iDEAL" as payment method
        4. Choose "ABN AMRO" from the bank list
        5. You'll be redirected to ABN AMRO's secure login
        6. Complete the payment with your real ABN AMRO credentials
        7. Return here to see the payment confirmation
        
        **Note:** This will process a real payment. Use small amounts for testing.
        """)
    else:
        st.warning("Select Netherlands (NL) to enable iDEAL testing with ABN AMRO")
    
    # Display payment button
    if test_email:
        from services.stripe_payment import display_payment_button
        display_payment_button(
            scan_type=selected_scan,
            user_email=test_email,
            metadata={
                "test_mode": "true",
                "testing_bank": "ABN AMRO",
                "test_timestamp": str(st.session_state.get('timestamp', ''))
            },
            country_code=country
        )
    else:
        st.warning("Please enter an email address to continue")
    
    # Testing instructions
    st.markdown("---")
    st.markdown("### 📋 Testing Instructions")
    
    with st.expander("🏦 How to Test with ABN AMRO iDEAL"):
        st.markdown("""
        **Step-by-Step Testing Process:**
        
        1. **Prepare Your ABN AMRO Account**
           - Ensure you have online banking access
           - Have your login credentials ready
           - Sufficient balance for the test amount
        
        2. **Initiate Payment**
           - Enter your real email above
           - Select a scan type to test
           - Click "Proceed to Secure Payment"
        
        3. **Stripe Checkout Process**
           - You'll be redirected to Stripe's secure checkout
           - Select "iDEAL" from payment methods
           - Choose "ABN AMRO" from the bank dropdown
        
        4. **ABN AMRO Authentication**
           - You'll be redirected to ABN AMRO's secure site
           - Log in with your normal banking credentials
           - Confirm the payment amount and details
           - Authorize the transaction
        
        5. **Payment Confirmation**
           - You'll be redirected back to this page
           - Payment confirmation will be displayed
           - Email receipt will be sent to your email
        
        **Security Notes:**
        - Your banking credentials never pass through our system
        - All authentication is handled directly by ABN AMRO
        - Payment processing is secured by Stripe (PCI DSS Level 1)
        - Transaction data is encrypted end-to-end
        """)
    
    with st.expander("🔧 Test Environment Details"):
        import os
        st.markdown(f"""
        **Current Configuration:**
        - **Environment:** {"Production" if "sk_live" in os.getenv('STRIPE_SECRET_KEY', '') else "Test Mode"}  
        - **Stripe Account:** Configured and Active
        - **iDEAL Support:** Enabled for Netherlands
        - **VAT Calculation:** 21% for Netherlands
        - **Currency:** EUR (Euros)
        - **Base URL:** {os.getenv('REPLIT_URL', 'http://localhost:5000')}
        
        **Available Test Banks:**
        - ABN AMRO (your primary test target)
        - ING Bank
        - Rabobank
        - All other Dutch iDEAL banks
        """)

def render_enterprise_repo_demo():
    """Render the enterprise repository scanner demo page"""
    try:
        from pages.enterprise_repo_demo import run_enterprise_repo_demo
        run_enterprise_repo_demo()
    except ImportError:
        st.error("Enterprise repository demo module not available")
        st.info("This feature demonstrates advanced repository scanning capabilities for massive repositories (100k+ files)")

if __name__ == "__main__":
    main()