"""
Scanner Interface Management Module
Extracted from app.py to improve modularity while preserving exact UI behavior
Contains the comprehensive scanner interface from lines 1580-6600
"""
import streamlit as st
import os
import uuid
import logging
from datetime import datetime
from io import BytesIO
import base64

from services.auth import require_permission, has_permission
from services.code_scanner import CodeScanner
from services.blob_scanner import BlobScanner
from services.website_scanner import WebsiteScanner
from services.ai_model_scanner import AIModelScanner
# Enhanced SOC2 scanner will be imported when needed
from utils.gdpr_rules import REGIONS
from utils.i18n import get_text
from utils.async_scan_manager import submit_async_scan

# Enterprise integration - non-breaking import
try:
    from utils.event_bus import EventType, publish_event
    from components.enterprise_actions import show_enterprise_actions, show_quick_enterprise_sidebar
    ENTERPRISE_EVENTS_AVAILABLE = True
except ImportError:
    ENTERPRISE_EVENTS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Define translation function
def _(key, default=None):
    return get_text(key, default)

def render_scanner_interface():
    """
    Main scanner interface - extracted from app.py lines 1580-6600
    Preserves exact UI behavior and structure
    """
    st.title(_("scan.new_scan_title"))
    
    # Show enterprise quick actions in sidebar if available
    if ENTERPRISE_EVENTS_AVAILABLE:
        show_quick_enterprise_sidebar()
    
    # Check if user has permission to create scans
    if not require_permission('scan:create'):
        st.warning(_("permission.no_scan_create"))
        st.info(_("permission.requires_scan_create"))
        st.stop()
    
    # Scan configuration form - expanded with all scanner types
    scan_type_options = [
        _("scan.code"), 
        _("scan.document"),  # Blob Scan
        _("scan.image"), 
        _("scan.database"),
        _("scan.api"),
        _("scan.website"),
        _("scan.manual_upload"),
        _("scan.dpia"),      # Data Protection Impact Assessment
        _("scan.sustainability"),
        _("scan.ai_model"),
        _("scan.soc2")
    ]
    
    # Add premium tag to premium features
    if not has_permission('scan:premium'):
        scan_type_options_with_labels = []
        premium_scans = [_("scan.image"), _("scan.api"), _("scan.sustainability"), _("scan.ai_model"), _("scan.soc2"), _("scan.dpia")]
        
        for option in scan_type_options:
            if option in premium_scans:
                scan_type_options_with_labels.append(f"{option} 💎")
            else:
                scan_type_options_with_labels.append(option)
                
        scan_type = st.selectbox(_("scan.select_type"), scan_type_options_with_labels)
        # Remove the premium tag for processing
        scan_type = scan_type.replace(" 💎", "")
        
        # Show premium feature message if needed
        if scan_type in premium_scans:
            st.warning(_("scan.premium_warning"))
            with st.expander(_("scan.premium_details_title")):
                st.markdown(_("scan.premium_details_description"))
                if st.button(_("scan.view_upgrade_options")):
                    st.session_state.selected_nav = _("nav.membership")
                    # Note: st.rerun() removed from button click to avoid no-op warning
                    # The app will automatically rerun due to session state changes
    else:
        scan_type = st.selectbox(_("scan.select_type"), scan_type_options)
    
    region = st.selectbox(_("scan.select_region"), list(REGIONS.keys()))
    
    # Additional configurations - customized for each scan type
    with st.expander(_("scan.advanced_configuration")):
        # Route to specific scanner configuration
        if scan_type == _("scan.code"):
            render_code_scanner_config()
        elif scan_type == _("scan.document"):
            render_document_scanner_config()
        elif scan_type == _("scan.image"):
            render_image_scanner_config()
        elif scan_type == _("scan.database"):
            render_database_scanner_config()
        elif scan_type == _("scan.api"):
            render_api_scanner_config()
        elif scan_type == _("scan.website"):
            render_website_scanner_config()
        elif scan_type == _("scan.dpia"):
            render_dpia_scanner_config()
        elif scan_type == _("scan.sustainability"):
            render_sustainability_scanner_config()
        elif scan_type == _("scan.ai_model"):
            render_ai_model_scanner_config()
        elif scan_type == _("scan.soc2"):
            render_soc2_scanner_config()
        else:
            render_manual_upload_config()
    
    # Store scan type in session state for submission
    st.session_state['scan_type'] = scan_type
    st.session_state['region'] = region

def render_code_scanner_config():
    """Unified code scanner configuration with intelligent scanning options"""
    st.subheader(_("scan.code_configuration", "GDPR Code Scanner Configuration"))
    
    # Use session state to remember the selection
    if 'repo_source' not in st.session_state:
        st.session_state.repo_source = _("scan.upload_files")
    
    # Create the radio button and update session state
    repo_source = st.radio(
        _("scan.repository_details"), 
        [_("scan.upload_files"), _("scan.repository_url")], 
        index=0 if st.session_state.repo_source == _("scan.upload_files") else 1,
        key="repo_source_radio"
    )
    
    # Update session state
    st.session_state.repo_source = repo_source
    
    if repo_source == _("scan.upload_files"):
        # File upload option
        st.write("📁 " + _("scan.upload_code_files", "Upload Code Files"))
        uploaded_files = st.file_uploader(
            _("scan.drag_files"),
            accept_multiple_files=True,
            type=['py', 'js', 'java', 'cpp', 'c', 'cs', 'php', 'rb', 'go', 'rs', 'ts', 'jsx', 'tsx', 'yaml', 'yml', 'json', 'xml', 'tf', 'tfvars', 'sh', 'ps1', 'sql', 'env'],
            key="code_files"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} files uploaded")
            for file in uploaded_files:
                st.write(f"📄 {file.name}")
    
    else:
        # Repository URL option
        st.write("🔗 " + _("scan.repository_url_option", "Repository URL"))
        repo_url = st.text_input(
            _("scan.repo_url"), 
            placeholder="https://github.com/username/repository",
            key="repo_url"
        )
        repo_branch = st.text_input(
            _("scan.repo_branch"), 
            value="main",
            key="repo_branch"
        )
        repo_token = st.text_input(
            _("scan.repo_token"), 
            type="password",
            help=_("scan.repo_token_help"),
            key="repo_token"
        )
    
    # Advanced intelligent scanning options
    with st.expander(_("scan.advanced_options", "Advanced Scanning Options")):
        st.write("🧠 " + _("scan.intelligent_options", "Intelligent Scanning Configuration"))
        
        col1, col2 = st.columns(2)
        with col1:
            scan_mode = st.selectbox(
                _("scan.mode", "Scan Mode"),
                ["fast", "smart", "deep", "sampling"],
                index=1,  # Default to smart
                key="scan_mode",
                help=_("scan.mode_help", "Smart mode adapts to repository size automatically")
            )
            
            use_entropy = st.checkbox(
                _("scan.entropy_analysis", "Entropy Analysis"), 
                value=True,
                key="use_entropy",
                help=_("scan.entropy_help", "Use entropy analysis for better secret detection")
            )
            
            include_comments = st.checkbox(
                _("scan.include_comments", "Include Comments"), 
                value=True,
                key="include_comments",
                help=_("scan.comments_help", "Scan code comments for sensitive information")
            )
        
        with col2:
            use_git_metadata = st.checkbox(
                _("scan.git_metadata", "Git Metadata Collection"), 
                value=False,
                key="use_git_metadata", 
                help=_("scan.git_help", "Collect Git blame and commit information")
            )
            
            detect_secrets = st.checkbox(
                _("scan.detect_secrets", "Secret Detection"), 
                value=True,
                key="detect_secrets",
                help=_("scan.secrets_help", "Detect API keys, tokens, and credentials")
            )
            
            timeout = st.number_input(
                _("scan.timeout_seconds", "Timeout (seconds)"), 
                value=60, 
                min_value=10, 
                max_value=3600,
                key="scan_timeout",
                help=_("scan.timeout_help", "Maximum scan duration before timeout")
            )
        
        # File filtering options
        st.write("📁 " + _("scan.file_options", "File Processing Options"))
        col3, col4 = st.columns(2)
        with col3:
            max_files = st.number_input(
                _("scan.max_files", "Max Files to Scan"), 
                value=200, 
                min_value=10, 
                max_value=1000,
                key="max_files",
                help=_("scan.max_files_help", "Maximum number of files to process")
            )
        with col4:
            priority_extensions = st.multiselect(
                _("scan.priority_extensions", "Priority Extensions"),
                ['.py', '.js', '.java', '.php', '.cs', '.go', '.rs', '.env', '.config'],
                default=['.env', '.config'],
                key="priority_extensions",
                help=_("scan.priority_help", "File types to scan with high priority")
            )

def render_document_scanner_config():
    """Document scanner configuration - extracted from app.py lines 2000-2500"""
    st.subheader("Document Scanner Configuration")
    
    uploaded_files = st.file_uploader(
        _("scan.upload_documents", "Upload Documents"),
        accept_multiple_files=True,
        type=['pdf', 'docx', 'txt', 'md', 'rtf'],
        key="document_files"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} documents uploaded")
        for file in uploaded_files:
            st.write(f"📄 {file.name} ({file.size} bytes)")

def render_image_scanner_config():
    """Image scanner configuration - extracted from app.py lines 2500-3000"""
    st.subheader("Image Scanner Configuration (Premium)")
    
    if not has_permission('scan:premium'):
        st.warning(_("scan.premium_required", "Premium subscription required for image scanning"))
        return
    
    uploaded_images = st.file_uploader(
        _("scan.upload_images", "Upload Images"),
        accept_multiple_files=True,
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'],
        key="image_files"
    )
    
    if uploaded_images:
        st.success(f"✅ {len(uploaded_images)} images uploaded")
        for image in uploaded_images:
            st.write(f"🖼️ {image.name} ({image.size} bytes)")

def render_database_scanner_config():
    """Database scanner configuration - extracted from app.py lines 3000-3500"""
    st.subheader("Database Scanner Configuration")
    
    # Connection method selection
    connection_method = st.radio(
        _("scan.connection_method", "Connection Method") + " ℹ️",
        ["Individual Parameters", "Connection String (Cloud)"],
        key="db_connection_method",
        help=_("scan.connection_method_help", "Use individual parameters for standard databases or connection string for cloud databases (Azure, AWS RDS, Google Cloud SQL)")
    )
    
    if connection_method == "Individual Parameters":
        # Database type selection
        db_type = st.selectbox(
            _("scan.database_type", "Database Type"),
            ["PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis"],
            key="db_type"
        )
        
        # Host and Port in columns with helpful info
        col1, col2 = st.columns([3, 1])
        with col1:
            db_host = st.text_input(
                _("scan.db_host", "Host") + " ℹ️",
                value="localhost",
                key="db_host",
                placeholder="localhost or 192.168.1.100 or db.example.com",
                help=_("scan.db_host_help", 
                       "⚠️ For LOCAL databases: use 'localhost'\n"
                       "⚠️ For REMOTE/NETWORK databases: use IP address (e.g., 192.168.1.100) or hostname (e.g., db.example.com)\n"
                       "⚠️ Ensure port 5432 (PostgreSQL) or 3306 (MySQL) is open and reachable")
            )
        with col2:
            default_port = 5432 if st.session_state.get("db_type") == "PostgreSQL" else 3306
            db_port = st.number_input(
                _("scan.db_port", "Port"),
                value=default_port,
                key="db_port",
                min_value=1,
                max_value=65535
            )
        
        # Show network connectivity warning for remote hosts
        if db_host and db_host not in ["localhost", "127.0.0.1", "::1"]:
            st.info(
                f"🌐 **Remote Database Detected**\n\n"
                f"Make sure:\n"
                f"- ✅ Host `{db_host}` is reachable from this scanner\n"
                f"- ✅ Port `{db_port}` is open in firewall\n"
                f"- ✅ Database allows remote connections\n"
                f"- ✅ User has proper access permissions"
            )
        
        # Database credentials
        db_name = st.text_input(_("scan.db_name", "Database Name"), key="db_name")
        
        col_user, col_pass = st.columns(2)
        with col_user:
            db_user = st.text_input(_("scan.db_user", "Username"), key="db_user")
        with col_pass:
            db_password = st.text_input(_("scan.db_password", "Password"), type="password", key="db_password")
        
        # SSL/TLS configuration for cloud databases
        with st.expander("🔒 SSL/TLS Configuration (Cloud Databases)"):
            st.caption("Enable SSL/TLS for secure connections to cloud databases (Azure, AWS RDS, Google Cloud SQL)")
            ssl_enabled = st.checkbox(_("scan.ssl_enabled", "Enable SSL/TLS"), key="db_ssl_enabled")
            if ssl_enabled:
                ssl_mode = st.selectbox(
                    _("scan.ssl_mode", "SSL Mode"),
                    ["require", "verify-ca", "verify-full"],
                    key="db_ssl_mode",
                    help="require: Encrypt connection | verify-ca: Verify CA certificate | verify-full: Verify hostname"
                )
    
    else:
        # Connection String method (for cloud databases)
        st.info(
            "📋 **Connection String Format Examples:**\n\n"
            "**PostgreSQL:**\n"
            "`postgresql://user:password@host:5432/database?sslmode=require`\n\n"
            "**MySQL:**\n"
            "`mysql://user:password@host:3306/database`\n\n"
            "**Azure:**\n"
            "`Server=host;Port=5432;Database=dbname;Uid=user;Pwd=password;SslMode=Required;`"
        )
        
        connection_string = st.text_area(
            _("scan.connection_string", "Connection String"),
            key="db_connection_string",
            height=100,
            placeholder="postgresql://user:password@hostname:5432/database?sslmode=require"
        )

def render_api_scanner_config():
    """API scanner configuration - extracted from app.py lines 3500-4000"""
    st.subheader("API Scanner Configuration (Premium)")
    
    if not has_permission('scan:premium'):
        st.warning(_("scan.premium_required", "Premium subscription required for API scanning"))
        return
    
    api_url = st.text_input(
        _("scan.api_url", "API Base URL"),
        placeholder="https://api.example.com",
        key="api_url"
    )
    
    api_auth_type = st.selectbox(
        _("scan.api_auth_type", "Authentication Type"),
        ["None", "API Key", "Bearer Token", "Basic Auth"],
        key="api_auth_type"
    )
    
    if api_auth_type != "None":
        api_auth_value = st.text_input(
            _("scan.api_auth_value", "Authentication Value"),
            type="password",
            key="api_auth_value"
        )

def render_website_scanner_config():
    """Website scanner configuration - extracted from app.py lines 4000-4500"""
    st.subheader("Website Scanner Configuration")
    
    website_url = st.text_input(
        _("scan.website_url", "Website URL"),
        placeholder="https://example.com",
        key="website_url"
    )
    
    scan_depth = st.slider(
        _("scan.scan_depth", "Scan Depth"),
        min_value=1,
        max_value=5,
        value=2,
        help=_("scan.scan_depth_help", "Number of levels to crawl"),
        key="scan_depth"
    )
    
    include_external = st.checkbox(
        _("scan.include_external", "Include External Links"),
        value=False,
        key="include_external"
    )

def render_dpia_scanner_config():
    """DPIA scanner configuration - extracted from app.py lines 4500-5000"""
    st.subheader("DPIA Scanner Configuration (Premium)")
    
    if not has_permission('scan:premium'):
        st.warning(_("scan.premium_required", "Premium subscription required for DPIA scanning"))
        return
    
    dpia_source = st.radio(
        _("scan.dpia_source", "Data Source"),
        [_("scan.dpia_upload_files", "Upload Files"), _("scan.dpia_github_repo", "GitHub Repository")],
        key="dpia_source"
    )
    
    if dpia_source == _("scan.dpia_upload_files"):
        uploaded_files = st.file_uploader(
            _("scan.upload_files"),
            accept_multiple_files=True,
            type=['py', 'js', 'java', 'json', 'xml', 'yaml'],
            key="dpia_files"
        )
    else:
        repo_url = st.text_input(
            _("scan.dpia_repo_url", "Repository URL"),
            key="dpia_repo_url"
        )

def render_sustainability_scanner_config():
    """Sustainability scanner configuration - extracted from app.py lines 5000-5500"""
    st.subheader("Sustainability Scanner Configuration (Premium)")
    
    if not has_permission('scan:premium'):
        st.warning(_("scan.premium_required", "Premium subscription required for sustainability scanning"))
        return
    
    sustainability_scope = st.multiselect(
        _("scan.sustainability_scope", "Sustainability Scope"),
        ["Energy Usage", "Carbon Footprint", "Resource Efficiency", "Green Computing"],
        default=["Energy Usage"],
        key="sustainability_scope"
    )

def render_ai_model_scanner_config():
    """AI Model scanner configuration - extracted from app.py lines 5500-6000"""
    st.subheader("AI Model Scanner Configuration (Premium)")
    
    if not has_permission('scan:premium'):
        st.warning(_("scan.premium_required", "Premium subscription required for AI model scanning"))
        return
    
    model_type = st.selectbox(
        _("scan.ai_model_type", "Model Type"),
        ["Machine Learning Model", "Deep Learning Model", "Natural Language Processing", "Computer Vision"],
        key="ai_model_type"
    )
    
    model_file = st.file_uploader(
        _("scan.upload_model", "Upload Model File"),
        type=['pkl', 'joblib', 'h5', 'pb', 'onnx'],
        key="ai_model_file"
    )

def render_soc2_scanner_config():
    """SOC2 scanner configuration - extracted from app.py lines 6000-6500"""
    st.subheader("SOC2 Scanner Configuration (Premium)")
    
    if not has_permission('scan:premium'):
        st.warning(_("scan.premium_required", "Premium subscription required for SOC2 scanning"))
        return
    
    soc2_repo_url = st.text_input(
        _("scan.soc2_repo_url", "Repository URL"),
        placeholder="https://github.com/username/repository",
        key="soc2_repo_url"
    )
    
    soc2_criteria = st.multiselect(
        _("scan.soc2_criteria", "SOC2 Criteria"),
        ["Security", "Availability", "Processing Integrity", "Confidentiality", "Privacy"],
        default=["Security"],
        key="soc2_criteria"
    )

def render_manual_upload_config():
    """Manual upload configuration - fallback option"""
    st.subheader("Manual Upload Configuration")
    
    uploaded_files = st.file_uploader(
        _("scan.upload_any_files", "Upload Any Files"),
        accept_multiple_files=True,
        key="manual_files"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} files uploaded")

def render_scan_submission():
    """Render scan submission button and handle actual scanning execution"""
    st.markdown("---")
    
    # Scan submission with real execution
    if st.button(_("scan.start_scan", "🚀 Start Scan"), type="primary", use_container_width=True):
        scan_type = st.session_state.get('scan_type')
        region = st.session_state.get('region', 'Netherlands')
        username = st.session_state.get('username', 'anonymous')
        
        # Route to appropriate scanner based on scan type
        if scan_type == _("scan.code"):
            execute_code_scan(region, username)
        elif scan_type == _("scan.document"):
            execute_document_scan(region, username)
        elif scan_type == _("scan.image"):
            execute_image_scan(region, username)
        elif scan_type == _("scan.database"):
            execute_database_scan(region, username)
        elif scan_type == _("scan.api"):
            execute_api_scan(region, username)
        elif scan_type == _("scan.website"):
            execute_website_scan(region, username)
        elif scan_type == _("scan.dpia"):
            execute_dpia_scan(region, username)
        elif scan_type == _("scan.sustainability"):
            execute_sustainability_scan(region, username)
        elif scan_type == _("scan.ai_model"):
            execute_ai_model_scan(region, username)
        elif scan_type == _("scan.soc2"):
            execute_soc2_scan(region, username)
        else:
            execute_manual_upload_scan(region, username)

def execute_code_scan(region: str, username: str):
    """Execute intelligent code scanning with unified configuration"""
    try:
        # Get scan parameters from unified configuration
        repo_source = st.session_state.get('repo_source', _("scan.upload_files"))
        uploaded_files = st.session_state.get('code_files', [])
        repo_url = st.session_state.get('repo_url', '')
        
        # Advanced configuration parameters
        scan_mode = st.session_state.get('scan_mode', 'smart')
        use_entropy = st.session_state.get('use_entropy', True)
        include_comments = st.session_state.get('include_comments', True)
        use_git_metadata = st.session_state.get('use_git_metadata', False)
        detect_secrets = st.session_state.get('detect_secrets', True)
        timeout = st.session_state.get('scan_timeout', 60)
        max_files = st.session_state.get('max_files', 200)
        priority_extensions = st.session_state.get('priority_extensions', [])
        
        # Use intelligent scanner wrapper
        from components.intelligent_scanner_wrapper import IntelligentScannerWrapper
        wrapper = IntelligentScannerWrapper()
        
        # Execute intelligent scan based on source type
        if repo_source == _("scan.upload_files") and uploaded_files:
            scan_result = wrapper.execute_code_scan_intelligent(
                region=region,
                username=username,
                uploaded_files=uploaded_files,
                include_comments=include_comments,
                detect_secrets=detect_secrets,
                gdpr_compliance=True,
                scan_mode=scan_mode,
                use_entropy=use_entropy,
                use_git_metadata=use_git_metadata,
                timeout=timeout,
                max_files=max_files,
                priority_extensions=priority_extensions
            )
        elif repo_source == _("scan.repository_url") and repo_url:
            scan_result = wrapper.execute_code_scan_intelligent(
                region=region,
                username=username,
                repo_url=repo_url,
                include_comments=include_comments,
                detect_secrets=detect_secrets,
                gdpr_compliance=True,
                scan_mode=scan_mode,
                use_entropy=use_entropy,
                use_git_metadata=use_git_metadata,
                timeout=timeout,
                max_files=max_files,
                priority_extensions=priority_extensions
            )
        else:
            st.error("Please provide either files to upload or a repository URL to scan.")
            return
        
        # Store results for display
        if scan_result and isinstance(scan_result, dict):
            st.session_state['code_scan_results'] = scan_result
            st.session_state['code_scan_complete'] = True
            
            # Display intelligent scan results
            wrapper.display_intelligent_scan_results(scan_result)
            st.success("✅ Intelligent code scan completed successfully!")
        else:
            st.error("❌ Scan failed to produce results")
            
    except Exception as e:
        st.error(f"❌ Code scan failed: {str(e)}")
        import logging
        logging.error(f"Code scan error: {str(e)}", exc_info=True)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            
            if repo_source == _("scan.upload_files"):
                # Handle uploaded files
                uploaded_files = st.session_state.get('code_files', [])
                if not uploaded_files:
                    st.error("Please upload code files to scan.")
                    return
                
                status_text.text("Processing uploaded files...")
                progress_bar.progress(0.1)
                
                # Save uploaded files to temp directory
                for i, uploaded_file in enumerate(uploaded_files):
                    progress = 0.1 + (i / len(uploaded_files) * 0.3)  # 10% to 40%
                    progress_bar.progress(progress)
                    status_text.text(f"Processing file {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
                    
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    file_paths.append(file_path)
                
                # Scan each file using working implementation
                scanner = CodeScanner(
                    extensions=[".py", ".js", ".java", ".tf", ".yaml", ".yml"],
                    include_comments=True,
                    region=region,
                    use_entropy=True,
                    use_git_metadata=True,
                    include_article_refs=True
                )
                
                progress_bar.progress(0.5)
                status_text.text("Starting file analysis...")
                
                for i, file_path in enumerate(file_paths):
                    try:
                        progress = 0.5 + (i / len(file_paths) * 0.4)  # 50% to 90%
                        progress_bar.progress(progress)
                        status_text.text(f"Scanning file {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")
                        
                        # Use the working scanner method
                        result = scanner._scan_file_with_timeout(file_path)
                        if result:
                            scan_results.append(result)
                            
                    except Exception as e:
                        logger.error(f"Error scanning file {file_path}: {e}")
                        continue
                
            else:
                # Handle GitHub repository using working implementation
                repo_url = st.session_state.get('repo_url', '')
                if not repo_url:
                    st.error("Please enter a repository URL to scan.")
                    return
                
                branch_name = st.session_state.get('repo_branch', 'main')
                auth_token = st.session_state.get('repo_token', None)
                
                status_text.text(f"Starting repository scan: {repo_url}")
                progress_bar.progress(0.1)
                
                # Use working GitHub scanner
                from services.github_repo_scanner import scan_github_repo_for_code
                
                def repo_progress_callback(current, total, current_file):
                    progress = 0.1 + (current / total * 0.8)  # 10% to 90%
                    progress_bar.progress(min(progress, 0.9))
                    status_text.text(f"Scanning repository file {current}/{total}: {current_file}")
                
                # Execute repository scan
                repo_result = scan_github_repo_for_code(
                    repo_url=repo_url,
                    branch=branch_name,
                    token=auth_token,
                    progress_callback=repo_progress_callback
                )
                
                if repo_result.get('status') == 'error':
                    st.error(f"Repository scan failed: {repo_result.get('message', 'Unknown error')}")
                    return
                
                # Store repository scan results
                scan_results = [repo_result]
            
            # Complete progress
            progress_bar.progress(1.0)
            status_text.text("Scan completed!")
            
            # Process and store results using working format
            if scan_results:
                # Aggregate results in working format
                if repo_source == _("scan.upload_files"):
                    total_files = len(file_paths)
                    source_info = 'uploaded_files'
                else:
                    # For repository scans, get info from the first result
                    first_result = scan_results[0] if scan_results else {}
                    total_files = first_result.get('files_scanned', 0)
                    source_info = st.session_state.get('repo_url', 'repository')
                
                total_pii = sum(len(res.get('pii_found', [])) for res in scan_results)
                
                aggregated_results = {
                    'scan_id': str(uuid.uuid4()),
                    'scan_type': 'code',
                    'timestamp': datetime.now().isoformat(),
                    'region': region,
                    'files_scanned': total_files,
                    'total_pii_found': total_pii,
                    'scan_results': scan_results,
                    'source': source_info,
                    'status': 'completed'
                }
                
                # Store results for display
                st.session_state['code_scan_results'] = aggregated_results
                st.session_state['code_scan_complete'] = True
                st.session_state['last_scan_type'] = 'code'
                
                st.success(f"✅ Code scan completed! Found {total_pii} potential PII items in {total_files} files.")
                
                # Display results immediately
                display_code_scan_results(aggregated_results)
                
            else:
                st.warning("Scan completed but no results were generated.")
                
    except Exception as e:
        st.error(f"Code scan error: {str(e)}")
        logger.error(f"Code scan execution error: {e}")
        import traceback
        st.code(traceback.format_exc())

# These functions have been integrated into execute_code_scan() above

def display_code_scan_results(scan_results):
    """Display code scan results with download options - FIXED using working format"""
    st.subheader("📊 Code Scan Results")
    
    # Summary metrics using working result format
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        # Handle different scanner types with appropriate metrics
        scan_type = scan_results.get('scan_type', '')
        if 'api' in scan_type.lower() or scan_results.get('endpoints_scanned') is not None:
            st.metric("Endpoints Scanned", scan_results.get('endpoints_scanned', 0))
        else:
            st.metric("Files Scanned", scan_results.get('files_scanned', 0))
    with col2:
        st.metric("Total Findings", scan_results.get('total_findings', scan_results.get('total_pii_found', 0)))
    with col3:
        scan_type = scan_results.get('scan_type', 'code')
        st.metric("Scan Type", scan_type.title())
    with col4:
        region = scan_results.get('region', 'Unknown')
        st.metric("Region", region)
    
    # Display source information
    source = scan_results.get('source', 'Unknown')
    if source != 'uploaded_files':
        st.info(f"📂 **Source**: {source}")
    else:
        st.info(f"📁 **Source**: Uploaded Files")
    
    # Process findings from scan results
    all_findings = []
    individual_results = scan_results.get('scan_results', [])
    
    for result in individual_results:
        pii_found = result.get('pii_found', [])
        file_name = result.get('file_name', 'unknown_file')
        
        for pii_item in pii_found:
            # Adapt to working PII format
            finding = {
                'file': file_name,
                'type': pii_item.get('type', 'Unknown'),
                'value': pii_item.get('value', '[REDACTED]'),
                'location': pii_item.get('location', 'Unknown'),
                'risk_level': pii_item.get('risk_level', 'Medium'),
                'reason': pii_item.get('reason', 'No reason provided'),
                'severity': pii_item.get('risk_level', 'Medium')  # Map risk_level to severity
            }
            all_findings.append(finding)
    
    # Display findings
    if all_findings:
        st.subheader("🔍 Detailed Findings")
        
        # Group by risk level
        high_risk = [f for f in all_findings if f.get('risk_level') == 'High']
        medium_risk = [f for f in all_findings if f.get('risk_level') == 'Medium']
        low_risk = [f for f in all_findings if f.get('risk_level') == 'Low']
        
        # Display tabs for different risk levels
        tab1, tab2, tab3 = st.tabs([
            f"🔴 High Risk ({len(high_risk)})",
            f"🟡 Medium Risk ({len(medium_risk)})", 
            f"🟢 Low Risk ({len(low_risk)})"
        ])
        
        with tab1:
            display_findings_by_risk(high_risk, "High")
        with tab2:
            display_findings_by_risk(medium_risk, "Medium")
        with tab3:
            display_findings_by_risk(low_risk, "Low")
            
    else:
        st.success("✅ No PII or security issues found in the scanned code!")
    
    # Download options
    st.subheader("📥 Download Reports")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Download PDF Report", use_container_width=True):
            st.info("PDF report generation will be available in the next update.")
    
    with col2:
        if st.button("🌐 Download HTML Report", use_container_width=True):
            st.info("HTML report generation will be available in the next update.")

def display_findings_by_risk(findings, risk_level):
    """Display findings grouped by risk level"""
    if not findings:
        st.info(f"No {risk_level.lower()} risk findings detected.")
        return
    
    for i, finding in enumerate(findings):
        pii_type = finding.get('type', 'Unknown')
        file_name = finding.get('file', 'unknown_file')
        location = finding.get('location', 'Unknown location')
        value = finding.get('value', '[REDACTED]')
        reason = finding.get('reason', 'No reason provided')
        
        # Color coding
        color = "🔴" if risk_level == 'High' else "🟡" if risk_level == 'Medium' else "🟢"
        
        with st.expander(f"{color} {pii_type} found in {file_name}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**File**: `{file_name}`")
                st.write(f"**Location**: {location}")
                st.write(f"**Type**: {pii_type}")
                st.write(f"**Value**: {value}")
                st.write(f"**Reason**: {reason}")
                
            with col2:
                st.write(f"**Risk Level**: {risk_level}")
                
                # GDPR information
                if pii_type.upper() in ['EMAIL', 'PHONE', 'BSN', 'CREDIT_CARD']:
                    st.write("**GDPR Impact**: High")
                    st.write("**Action Required**: Review and secure")
                else:
                    st.write("**GDPR Impact**: Medium")
                    st.write("**Action Required**: Assess context")

# Placeholder functions for other scanners - to be implemented
def execute_document_scan(region: str, username: str):
    st.info("Document scanner execution will be implemented in the next phase.")

def execute_image_scan(region: str, username: str):
    st.info("Image scanner execution will be implemented in the next phase.")

def execute_database_scan(region: str, username: str):
    st.info("Database scanner execution will be implemented in the next phase.")

def execute_api_scan(region: str, username: str):
    st.info("API scanner execution will be implemented in the next phase.")

def execute_website_scan(region: str, username: str):
    st.info("Website scanner execution will be implemented in the next phase.")

def execute_dpia_scan(region: str, username: str):
    st.info("DPIA scanner execution will be implemented in the next phase.")

def execute_sustainability_scan(region: str, username: str):
    st.info("Sustainability scanner execution will be implemented in the next phase.")

def execute_manual_upload_scan(region: str, username: str):
    st.info("Manual upload scanner execution will be implemented in the next phase.")

def execute_ai_model_scan(region: str, username: str):
    """Execute AI model scanning with ML framework integration"""
    try:
        with st.status("Analyzing AI model...", expanded=True) as status:
            # Get uploaded model file
            model_file = st.session_state.get('ai_model_file')
            model_type = st.session_state.get('ai_model_type', 'Machine Learning Model')
            
            if not model_file:
                st.error("Please upload an AI model file to analyze.")
                return
                
            status.update(label="Loading AI model analysis framework...")
            
            # Create enhanced AI model scanner
            from services.ai_model_scanner import AIModelScanner
            
            # Initialize with ML framework support
            scanner = AIModelScanner()
            
            # Enhanced AI model analysis
            status.update(label="Analyzing model architecture and data...")
            results = scanner.scan_ai_model_enhanced(
                model_file=model_file,
                model_type=model_type,
                region=region,
                status=status
            )
            
            if results and results.get('status') != 'failed':
                st.session_state['ai_model_scan_results'] = results
                st.session_state['ai_model_scan_complete'] = True
                st.session_state['last_scan_type'] = 'ai_model'
                
                status.update(label="✅ AI model analysis completed!", state="complete")
                st.success("AI model analysis completed! View results below.")
                
                # Display results
                display_ai_model_scan_results(results)
            else:
                error_msg = results.get('error', 'Unknown error occurred') if results else 'Analysis failed'
                st.error(f"AI model analysis failed: {error_msg}")
                
    except Exception as e:
        st.error(f"AI model analysis error: {str(e)}")
        logger.error(f"AI model scan execution error: {e}")

def execute_soc2_scan(region: str, username: str):
    """Execute SOC2 compliance scanning with TSC mapping"""
    try:
        with st.status("Running SOC2 compliance analysis...", expanded=True) as status:
            # Get scan parameters
            repo_url = st.session_state.get('soc2_repo_url', '')
            soc2_criteria = st.session_state.get('soc2_criteria', ['Security'])
            
            if not repo_url:
                st.error("Please enter a repository URL for SOC2 analysis.")
                return
                
            status.update(label="Initializing SOC2 compliance framework...")
            
            # Create enhanced SOC2 scanner
            from services.enhanced_soc2_scanner import EnhancedSOC2Scanner
            
            # Initialize with TSC mapping
            scanner = EnhancedSOC2Scanner()
            
            # Enhanced SOC2 analysis
            status.update(label="Analyzing repository for SOC2 compliance...")
            results = scanner.scan_soc2_compliance_enhanced(
                repo_url=repo_url,
                criteria=soc2_criteria,
                region=region,
                status=status
            )
            
            if results and results.get('status') != 'failed':
                st.session_state['soc2_scan_results'] = results
                st.session_state['soc2_scan_complete'] = True
                st.session_state['last_scan_type'] = 'soc2'
                
                status.update(label="✅ SOC2 compliance analysis completed!", state="complete")
                st.success("SOC2 compliance analysis completed! View results below.")
                
                # Display results
                display_soc2_scan_results(results)
            else:
                error_msg = results.get('error', 'Unknown error occurred') if results else 'Analysis failed'
                st.error(f"SOC2 analysis failed: {error_msg}")
                
    except Exception as e:
        st.error(f"SOC2 analysis error: {str(e)}")
        logger.error(f"SOC2 scan execution error: {e}")

def display_ai_model_scan_results(scan_results):
    """Display AI model scan results"""
    st.subheader("🤖 AI Model Analysis Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Model Type", scan_results.get('model_type', 'Unknown'))
    with col2:
        bias_score = scan_results.get('bias_score', 0)
        st.metric("Bias Score", f"{bias_score:.2f}", delta_color="inverse")
    with col3:
        pii_score = scan_results.get('pii_presence_score', 0)
        st.metric("PII Risk", f"{pii_score:.2f}", delta_color="inverse")
    with col4:
        explainability = scan_results.get('explainability_score', 0)
        st.metric("Explainability", f"{explainability:.2f}")
    
    # Detailed analysis
    findings = scan_results.get('findings', [])
    if findings:
        st.subheader("🔍 Analysis Findings")
        for finding in findings:
            severity = finding.get('severity', 'Medium')
            color = "🔴" if severity == 'High' else "🟡" if severity == 'Medium' else "🟢"
            
            with st.expander(f"{color} {finding.get('category', 'Analysis')} - {finding.get('title', 'Finding')}"):
                st.write(f"**Category**: {finding.get('category', 'Unknown')}")
                st.write(f"**Severity**: {severity}")
                st.write(f"**Description**: {finding.get('description', 'No description')}")
                if finding.get('recommendation'):
                    st.write(f"**Recommendation**: {finding['recommendation']}")

def display_soc2_scan_results(scan_results):
    """Display SOC2 scan results"""
    st.subheader("🛡️ SOC2 Compliance Analysis Results")
    
    # TSC criteria overview
    criteria_results = scan_results.get('tsc_criteria', {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        total_checks = scan_results.get('total_checks', 0)
        st.metric("Total Checks", total_checks)
    with col2:
        passed_checks = scan_results.get('passed_checks', 0)
        st.metric("Passed", passed_checks, delta_color="normal")
    with col3:
        failed_checks = scan_results.get('failed_checks', 0)
        st.metric("Failed", failed_checks, delta_color="inverse")
    
    # TSC criteria breakdown
    if criteria_results:
        st.subheader("📋 TSC Criteria Analysis")
        
        for criterion, details in criteria_results.items():
            status = details.get('status', 'Unknown')
            color = "✅" if status == 'Pass' else "❌" if status == 'Fail' else "⚠️"
            
            with st.expander(f"{color} {criterion} - {status}"):
                st.write(f"**Status**: {status}")
                st.write(f"**Score**: {details.get('score', 0)}/100")
                
                violations = details.get('violations', [])
                if violations:
                    st.write("**Violations Found:**")
                    for violation in violations:
                        st.write(f"- {violation}")
                
                recommendations = details.get('recommendations', [])
                if recommendations:
                    st.write("**Recommendations:**")
                    for rec in recommendations:
                        st.write(f"- {rec}")
    
    # Overall findings
    findings = scan_results.get('findings', [])
    if findings:
        st.subheader("🔍 Detailed Findings")
        for finding in findings:
            severity = finding.get('risk_level', 'Medium')
            color = "🔴" if severity == 'High' else "🟡" if severity == 'Medium' else "🟢"
            
            with st.expander(f"{color} {finding.get('principle', 'SOC2')} - {finding.get('violation', 'Issue')}"):
                st.write(f"**Principle**: {finding.get('principle', 'Unknown')}")
                st.write(f"**Risk Level**: {severity}")
                st.write(f"**Violation**: {finding.get('violation', 'No description')}")
                st.write(f"**Scanner**: {finding.get('scanner', 'soc2-scanner')}")
                if finding.get('remediation_suggestion'):
                    st.write(f"**Remediation**: {finding['remediation_suggestion']}")