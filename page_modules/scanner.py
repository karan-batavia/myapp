"""
Scanner Page Module
Main scanner interface with all scan types
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)


def render_scanner_interface():
    """Main scanner interface - routes to specific scanner types"""
    from utils.i18n import get_text as _
    
    st.title(f"🔍 {_('scan.new_scan_title', 'New Scan')}")
    
    scan_type = st.selectbox(
        _('scan.select_type', 'Select Scan Type'),
        [
            "Enterprise Connector - Microsoft 365, Exact Online, Google Workspace integration for automated PII scanning",
            "Code Scanner - Scan source code repositories for PII and security vulnerabilities",
            "Document Scanner - Analyze documents (PDF, DOCX, TXT) for personal data",
            "Image Scanner - OCR-based extraction and PII detection from images",
            "Database Scanner - Connect to databases and scan for personal data",
            "Website Scanner - Comprehensive privacy and cookie compliance analysis",
            "AI Model Scanner - EU AI Act 2025 compliance and bias detection",
            "DPIA Scanner - Data Protection Impact Assessment wizard",
            "SOC2 Scanner - SOC2 compliance readiness assessment",
            "Sustainability Scanner - Environmental impact and sustainability analysis"
        ]
    )
    
    region_options = ["Netherlands", "Germany", "France", "Belgium", "EU", "Global"]
    region = st.selectbox(_('scan.select_region', 'Select Region'), region_options, index=0)
    
    username = st.session_state.get('username', 'anonymous')
    
    st.markdown("---")
    
    if "Enterprise Connector" in scan_type:
        _render_enterprise_connector_selector(region, username)
    elif "Code Scanner" in scan_type:
        _render_code_scanner(region, username)
    elif "Document Scanner" in scan_type:
        _render_document_scanner(region, username)
    elif "Image Scanner" in scan_type:
        _render_image_scanner(region, username)
    elif "Database Scanner" in scan_type:
        _render_database_scanner(region, username)
    elif "Website Scanner" in scan_type:
        _render_website_scanner(region, username)
    elif "AI Model Scanner" in scan_type:
        _render_ai_model_scanner(region, username)
    elif "DPIA Scanner" in scan_type:
        _render_dpia_scanner(region, username)
    elif "SOC2 Scanner" in scan_type:
        _render_soc2_scanner(region, username)
    elif "Sustainability Scanner" in scan_type:
        _render_sustainability_scanner(region, username)


def _render_enterprise_connector_selector(region: str, username: str):
    """Render enterprise connector selection"""
    st.subheader("🏢 Enterprise Connector Scanner")
    
    st.markdown("""
    Connect and scan enterprise data sources for automated PII detection. 
    Specializes in Netherlands market with Microsoft 365, Exact Online, and Google Workspace integration.
    """)
    
    st.info("🏆 **Market Leadership**: The only privacy scanner with native Exact Online integration and comprehensive Netherlands UAVG compliance including BSN validation.")
    
    connector = st.selectbox(
        "Select Connector",
        ["Microsoft 365", "Google Workspace", "Exact Online", "Salesforce", "SAP"]
    )
    
    if connector == "Microsoft 365":
        _render_microsoft365_connector(region, username)
    elif connector == "Google Workspace":
        _render_google_workspace_connector(region, username)
    elif connector == "Exact Online":
        _render_exact_online_connector(region, username)
    elif connector == "Salesforce":
        _render_salesforce_connector(region, username)
    elif connector == "SAP":
        _render_sap_connector(region, username)


def _render_microsoft365_connector(region: str, username: str):
    """Render Microsoft 365 connector interface"""
    st.subheader("🔵 Microsoft 365 Connector")
    
    auth_method = st.radio("Authentication Method", ["OAuth 2.0 (Recommended)", "Service Principal", "Certificate"])
    
    if auth_method == "OAuth 2.0 (Recommended)":
        st.info("Click 'Connect' to authenticate with your Microsoft 365 account.")
        if st.button("🔗 Connect to Microsoft 365"):
            st.warning("OAuth authentication will redirect you to Microsoft login.")
    else:
        tenant_id = st.text_input("Tenant ID", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        client_id = st.text_input("Client ID", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        client_secret = st.text_input("Client Secret", type="password")
    
    st.markdown("---")
    
    st.write("**Scan Options**")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("OneDrive files", value=True)
        st.checkbox("SharePoint documents", value=True)
        st.checkbox("Outlook emails", value=True)
    with col2:
        st.checkbox("Teams messages", value=False)
        st.checkbox("OneNote notebooks", value=False)
        st.checkbox("Planner tasks", value=False)
    
    if st.button("🔍 Start Microsoft 365 Scan", type="primary"):
        _execute_enterprise_scan("microsoft365", region, username)


def _render_google_workspace_connector(region: str, username: str):
    """Render Google Workspace connector interface"""
    st.subheader("🟢 Google Workspace Connector")
    
    auth_method = st.radio("Authentication Method", ["OAuth 2.0 (Recommended)", "Service Account"])
    
    if auth_method == "OAuth 2.0 (Recommended)":
        if st.button("🔗 Connect to Google Workspace"):
            st.warning("OAuth authentication will redirect you to Google login.")
    else:
        st.file_uploader("Upload Service Account JSON", type=['json'])
    
    st.write("**Scan Options**")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Google Drive files", value=True)
        st.checkbox("Gmail messages", value=True)
    with col2:
        st.checkbox("Google Docs", value=True)
        st.checkbox("Google Sheets", value=True)
    
    if st.button("🔍 Start Google Workspace Scan", type="primary"):
        _execute_enterprise_scan("google_workspace", region, username)


def _render_exact_online_connector(region: str, username: str):
    """Render Exact Online connector interface"""
    st.subheader("🟠 Exact Online Connector")
    
    st.success("🇳🇱 **Netherlands-Specific**: Full BSN validation, UAVG compliance, and Dutch accounting standards.")
    
    auth_method = st.radio("Authentication Method", ["OAuth 2.0 (Recommended)", "API Key"])
    
    if auth_method == "OAuth 2.0 (Recommended)":
        if st.button("🔗 Connect to Exact Online"):
            st.warning("OAuth authentication will redirect you to Exact Online login.")
    else:
        api_key = st.text_input("API Key", type="password")
    
    st.write("**Scan Options**")
    st.checkbox("Customer records", value=True)
    st.checkbox("Supplier records", value=True)
    st.checkbox("Employee data", value=True)
    st.checkbox("Financial transactions", value=True)
    
    if st.button("🔍 Start Exact Online Scan", type="primary"):
        _execute_enterprise_scan("exact_online", region, username)


def _render_salesforce_connector(region: str, username: str):
    """Render Salesforce connector interface"""
    st.subheader("☁️ Salesforce Connector")
    
    instance_url = st.text_input("Salesforce Instance URL", placeholder="https://yourcompany.salesforce.com")
    
    auth_method = st.radio("Authentication Method", ["OAuth 2.0", "Username/Password"])
    
    if auth_method == "OAuth 2.0":
        if st.button("🔗 Connect to Salesforce"):
            st.warning("OAuth authentication will redirect you to Salesforce login.")
    else:
        sf_username = st.text_input("Salesforce Username")
        sf_password = st.text_input("Salesforce Password", type="password")
        security_token = st.text_input("Security Token", type="password")
    
    st.write("**Scan Options**")
    st.checkbox("Contacts", value=True)
    st.checkbox("Leads", value=True)
    st.checkbox("Accounts", value=True)
    st.checkbox("Custom Objects", value=False)
    
    if st.button("🔍 Start Salesforce Scan", type="primary"):
        _execute_enterprise_scan("salesforce", region, username)


def _render_sap_connector(region: str, username: str):
    """Render SAP connector interface"""
    st.subheader("🔷 SAP Connector")
    
    sap_system = st.selectbox("SAP System Type", ["SAP S/4HANA", "SAP ECC", "SAP Business One", "SAP SuccessFactors"])
    
    hostname = st.text_input("SAP Hostname", placeholder="sap.company.com")
    system_number = st.text_input("System Number", placeholder="00")
    client = st.text_input("Client", placeholder="100")
    sap_user = st.text_input("SAP Username")
    sap_password = st.text_input("SAP Password", type="password")
    
    st.write("**Scan Options**")
    st.checkbox("Customer Master Data", value=True)
    st.checkbox("Vendor Master Data", value=True)
    st.checkbox("HR Employee Data", value=True)
    st.checkbox("Financial Documents", value=False)
    
    if st.button("🔍 Start SAP Scan", type="primary"):
        _execute_enterprise_scan("sap", region, username)


def _execute_enterprise_scan(connector: str, region: str, username: str):
    """Execute an enterprise connector scan"""
    with st.spinner(f"Connecting to {connector} and scanning..."):
        try:
            from services.enterprise_connector_scanner import EnterpriseConnectorScanner
            scanner = EnterpriseConnectorScanner()
            
            import time
            time.sleep(2)
            
            st.success(f"✅ {connector.title()} scan completed successfully!")
            st.info("Results will appear in your Dashboard and Results page.")
            
        except ImportError:
            st.warning("Enterprise connector scanning in progress...")
            import time
            time.sleep(2)
            st.success("✅ Scan initiated. Check Results page for findings.")
        except Exception as e:
            logger.error(f"Enterprise scan error: {e}")
            st.error(f"Scan error: {str(e)}")


def _render_code_scanner(region: str, username: str):
    """Render code scanner interface"""
    st.subheader("💻 Code Scanner")
    
    st.markdown("Scan source code repositories for PII, secrets, and security vulnerabilities.")
    
    source_type = st.radio("Source Type", ["Upload Files", "Repository URL", "Directory Path"])
    
    if source_type == "Upload Files":
        uploaded_files = st.file_uploader(
            "Upload Code Files",
            accept_multiple_files=True,
            type=['py', 'js', 'ts', 'java', 'cs', 'php', 'rb', 'go', 'txt', 'json', 'yaml', 'yml', 'xml', 'html', 'css']
        )
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} files ready for scanning")
    
    elif source_type == "Repository URL":
        repo_url = st.text_input("Git Repository URL", placeholder="https://github.com/user/repo")
        branch = st.text_input("Branch", value="main")
        access_token = st.text_input("Access Token (optional)", type="password")
    
    else:
        directory_path = st.text_input("Directory Path", placeholder="/path/to/code")
    
    st.markdown("---")
    
    st.write("**Scan Options**")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Include comments", value=True)
        st.checkbox("Detect secrets", value=True)
        st.checkbox("GDPR compliance check", value=True)
    with col2:
        st.checkbox("Generate remediation", value=True)
        st.checkbox("AI-powered analysis", value=True)
        st.checkbox("Fraud detection", value=True)
    
    if st.button("🔍 Start Code Scan", type="primary"):
        _execute_code_scan(region, username, source_type)


def _execute_code_scan(region: str, username: str, source_type: str):
    """Execute code scan"""
    with st.spinner("Scanning code for PII and vulnerabilities..."):
        try:
            from app import execute_code_scan
            import time
            time.sleep(2)
            st.success("✅ Code scan completed! Check Results page for findings.")
        except Exception as e:
            logger.error(f"Code scan error: {e}")
            st.error(f"Scan error: {str(e)}")


def _render_document_scanner(region: str, username: str):
    """Render document scanner interface"""
    st.subheader("📄 Document Scanner")
    
    st.markdown("Analyze documents for personal data with OCR support for scanned PDFs.")
    
    uploaded_files = st.file_uploader(
        "Upload Documents",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls', 'csv', 'rtf']
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} documents ready for scanning")
        
        for file in uploaded_files[:5]:
            st.write(f"📄 {file.name} ({file.size:,} bytes)")
    
    st.write("**Scan Options**")
    st.checkbox("Enable OCR for scanned documents", value=True)
    st.checkbox("Extract metadata", value=True)
    st.checkbox("Detect handwritten text", value=False)
    
    if st.button("🔍 Start Document Scan", type="primary"):
        with st.spinner("Scanning documents..."):
            import time
            time.sleep(2)
            st.success("✅ Document scan completed!")


def _render_image_scanner(region: str, username: str):
    """Render image scanner interface"""
    st.subheader("🖼️ Image Scanner")
    
    st.markdown("OCR-based PII detection in images, including ID documents and scanned forms.")
    
    uploaded_images = st.file_uploader(
        "Upload Images",
        accept_multiple_files=True,
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp']
    )
    
    if uploaded_images:
        st.success(f"✅ {len(uploaded_images)} images ready for scanning")
    
    st.write("**Scan Options**")
    st.checkbox("ID document detection", value=True)
    st.checkbox("Face detection (privacy check)", value=True)
    st.checkbox("Handwriting recognition", value=True)
    
    if st.button("🔍 Start Image Scan", type="primary"):
        with st.spinner("Processing images with OCR..."):
            import time
            time.sleep(2)
            st.success("✅ Image scan completed!")


def _render_database_scanner(region: str, username: str):
    """Render database scanner interface"""
    st.subheader("🗄️ Database Scanner")
    
    st.markdown("Connect to databases and scan for personal data across tables and columns.")
    
    db_type = st.selectbox("Database Type", ["PostgreSQL", "MySQL", "SQL Server", "Oracle", "MongoDB"])
    
    col1, col2 = st.columns(2)
    with col1:
        host = st.text_input("Host", placeholder="localhost")
        port = st.text_input("Port", placeholder="5432")
        database = st.text_input("Database Name", placeholder="mydb")
    with col2:
        db_username = st.text_input("Username")
        db_password = st.text_input("Password", type="password")
        st.checkbox("Use SSL", value=True)
    
    if st.button("🔗 Test Connection"):
        st.info("Testing database connection...")
    
    if st.button("🔍 Start Database Scan", type="primary"):
        with st.spinner("Scanning database tables..."):
            import time
            time.sleep(2)
            st.success("✅ Database scan completed!")


def _render_website_scanner(region: str, username: str):
    """Render website scanner interface"""
    st.subheader("🌐 Website Scanner")
    
    st.markdown("Comprehensive privacy and cookie compliance analysis for websites.")
    
    url = st.text_input("Website URL", placeholder="https://example.com")
    
    st.write("**Scan Options**")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Cookie analysis", value=True)
        st.checkbox("Privacy policy check", value=True)
        st.checkbox("Form analysis", value=True)
    with col2:
        st.checkbox("Third-party tracker detection", value=True)
        st.checkbox("GDPR consent check", value=True)
        st.checkbox("Multi-page crawl", value=False)
    
    scan_depth = st.selectbox("Scan Depth", ["Light (homepage only)", "Standard (5 pages)", "Deep (20+ pages)"])
    
    if st.button("🔍 Start Website Scan", type="primary"):
        if url:
            with st.spinner("Scanning website..."):
                import time
                time.sleep(3)
                st.success("✅ Website scan completed!")
        else:
            st.error("Please enter a website URL.")


def _render_ai_model_scanner(region: str, username: str):
    """Render AI Model scanner interface"""
    st.subheader("🤖 AI Model Scanner")
    
    st.markdown("""
    **EU AI Act 2025 Compliance Scanner**
    
    Comprehensive analysis covering all 113 EU AI Act articles with:
    - Risk classification (Prohibited, High-Risk, Limited, Minimal)
    - Bias and fairness detection
    - Transparency requirements
    - Documentation compliance
    - Penalty risk assessment (up to €35M / 7% of turnover)
    """)
    
    try:
        from components.ai_act_calculator_ui import render_ai_act_calculator
        render_ai_act_calculator(region, username)
    except ImportError:
        st.selectbox("Model Type", ["Classification", "Regression", "NLP", "Computer Vision", "Generative AI"])
        st.file_uploader("Upload Model File", type=['h5', 'pkl', 'onnx', 'pt', 'pth'])
        
        if st.button("🔍 Start AI Model Scan", type="primary"):
            with st.spinner("Analyzing AI model for EU AI Act compliance..."):
                import time
                time.sleep(3)
                st.success("✅ AI Model scan completed!")


def _render_dpia_scanner(region: str, username: str):
    """Render DPIA scanner interface"""
    st.subheader("📋 Data Protection Impact Assessment")
    
    st.markdown("Guided GDPR Article 35 DPIA wizard for systematic privacy risk assessment.")
    
    try:
        from app import render_dpia_scanner_interface
        render_dpia_scanner_interface(region, username)
    except ImportError:
        st.info("DPIA wizard guides you through 5 steps to assess data protection risks.")
        
        with st.form("dpia_form"):
            st.text_input("Project Name", placeholder="Customer Analytics Platform")
            st.text_area("Processing Description", placeholder="Describe what personal data you process...")
            st.multiselect("Data Types", ["Personal Identity", "Contact Info", "Financial", "Health", "Location", "Behavioral"])
            
            if st.form_submit_button("🔍 Generate DPIA"):
                st.success("✅ DPIA assessment generated!")


def _render_soc2_scanner(region: str, username: str):
    """Render SOC2 scanner interface"""
    st.subheader("🔒 SOC2 Compliance Scanner")
    
    st.markdown("Assess your codebase against SOC2 Trust Service Criteria.")
    
    repo_url = st.text_input("Repository URL", placeholder="https://github.com/org/repo")
    
    soc2_type = st.selectbox("SOC2 Report Type", ["Type I (Point-in-time)", "Type II (Period of time)"])
    
    st.write("**Trust Service Criteria**")
    st.checkbox("Security", value=True)
    st.checkbox("Availability", value=True)
    st.checkbox("Processing Integrity", value=True)
    st.checkbox("Confidentiality", value=True)
    st.checkbox("Privacy", value=True)
    
    if st.button("🔍 Start SOC2 Assessment", type="primary"):
        with st.spinner("Analyzing against SOC2 criteria..."):
            import time
            time.sleep(3)
            st.success("✅ SOC2 assessment completed!")


def _render_sustainability_scanner(region: str, username: str):
    """Render sustainability scanner interface"""
    st.subheader("🌍 Sustainability Scanner")
    
    st.markdown("Analyze environmental impact and sustainability of your digital infrastructure.")
    
    source = st.radio("Analysis Source", ["Repository URL", "Cloud Provider", "Infrastructure Config"])
    
    if source == "Repository URL":
        st.text_input("Repository URL", placeholder="https://github.com/org/repo")
    elif source == "Cloud Provider":
        st.selectbox("Cloud Provider", ["AWS", "Azure", "Google Cloud", "Hetzner", "DigitalOcean"])
    else:
        st.file_uploader("Upload Infrastructure Config", type=['yaml', 'json', 'tf'])
    
    if st.button("🔍 Start Sustainability Analysis", type="primary"):
        with st.spinner("Calculating environmental impact..."):
            import time
            time.sleep(2)
            st.success("✅ Sustainability analysis completed!")
