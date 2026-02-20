"""
Enterprise UI Components for DataGuardian Pro
Enhanced authentication, RBAC controls, and enterprise connector interfaces
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from services.enterprise_auth import (
    EnterpriseAuth, EnterpriseRole, Permission, UserProfile,
    get_enterprise_auth
)
from services.salesforce_connector import create_salesforce_connector
from services.sap_connector import create_sap_connector
import json

def show_enterprise_login():
    """Display enterprise login options (SSO/SAML/Local)"""
    st.title("🔐 Enterprise Login")
    
    auth_method = st.selectbox(
        "Authentication Method",
        ["Local Account", "SAML SSO", "OpenID Connect", "Microsoft Azure AD"],
        key="auth_method"
    )
    
    if auth_method == "Local Account":
        show_local_login()
    elif auth_method == "SAML SSO":
        show_saml_login()
    elif auth_method == "OpenID Connect":
        show_oidc_login()
    elif auth_method == "Microsoft Azure AD":
        show_azure_ad_login()

def show_local_login():
    """Show local authentication form"""
    with st.form("local_login"):
        st.subheader("Local Account Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if username and password:
                # Simulate local authentication
                user_profile = UserProfile(
                    user_id=username,
                    email=f"{username}@company.com",
                    name=username.title(),
                    roles=[EnterpriseRole.ADMIN],
                    permissions=[],
                    organization="Local Company",
                    department="IT",
                    country="NL",
                    session_id="local_session",
                    auth_method="local"
                )
                
                enterprise_auth = get_enterprise_auth()
                user_profile.permissions = enterprise_auth._get_permissions_for_roles(user_profile.roles)
                
                st.session_state['enterprise_user_profile'] = user_profile
                st.session_state['authenticated'] = True
                st.success("Login successful!")
                st.rerun()

def show_saml_login():
    """Show SAML SSO login"""
    st.subheader("SAML Single Sign-On")
    st.info("Configure SAML settings in your environment variables:")
    st.code("""
SAML_ENTITY_ID=https://dataguardian.nl
SAML_SSO_URL=https://your-idp.com/sso
SAML_X509_CERT=your_certificate
SAML_PRIVATE_KEY=your_private_key
    """)
    
    if st.button("Login with SAML", type="primary"):
        enterprise_auth = get_enterprise_auth()
        if enterprise_auth.saml_config:
            redirect_url = enterprise_auth.generate_saml_auth_request()
            st.markdown(f"[Redirect to IdP]({redirect_url})")
        else:
            st.error("SAML not configured. Please set environment variables.")

def show_oidc_login():
    """Show OpenID Connect login"""
    st.subheader("OpenID Connect")
    st.info("Configure OIDC settings in your environment variables:")
    st.code("""
OIDC_CLIENT_ID=your_client_id
OIDC_CLIENT_SECRET=your_client_secret
OIDC_DISCOVERY_URL=https://your-provider.com/.well-known/openid_configuration
    """)
    
    if st.button("Login with OIDC", type="primary"):
        enterprise_auth = get_enterprise_auth()
        if enterprise_auth.oidc_config:
            auth_url = enterprise_auth.initiate_oidc_flow()
            st.markdown(f"[Redirect to Provider]({auth_url})")
        else:
            st.error("OIDC not configured. Please set environment variables.")

def show_azure_ad_login():
    """Show Azure AD login"""
    st.subheader("Microsoft Azure AD")
    st.info("Azure AD integration provides seamless SSO for Office 365 users")
    
    col1, col2 = st.columns(2)
    with col1:
        tenant_id = st.text_input("Tenant ID", placeholder="your-tenant-id")
    with col2:
        client_id = st.text_input("Application ID", placeholder="your-app-id")
    
    if st.button("Login with Azure AD", type="primary"):
        if tenant_id and client_id:
            st.success("Azure AD authentication would redirect here")
            # In production, redirect to Azure AD
        else:
            st.error("Please provide Tenant ID and Application ID")

def show_rbac_management():
    """Display RBAC management interface"""
    if not check_permission(Permission.USER_VIEW):
        st.error("Access denied. Insufficient permissions.")
        return
    
    st.title("👥 Role-Based Access Control")
    
    tab1, tab2, tab3 = st.tabs(["Users", "Roles", "Permissions"])
    
    with tab1:
        show_user_management()
    
    with tab2:
        show_role_management()
    
    with tab3:
        show_permission_matrix()

def show_user_management():
    """Show user management interface"""
    st.subheader("User Management")
    
    # User list
    users = get_sample_users()  # In production, fetch from database
    
    for user in users:
        with st.expander(f"{user['name']} ({user['email']})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Department:** {user['department']}")
                st.write(f"**Organization:** {user['organization']}")
            
            with col2:
                current_roles = user.get('roles', [])
                new_roles = st.multiselect(
                    "Roles",
                    [role.value for role in EnterpriseRole],
                    default=current_roles,
                    key=f"roles_{user['id']}"
                )
            
            with col3:
                if st.button("Update User", key=f"update_{user['id']}"):
                    st.success(f"Updated roles for {user['name']}")
                
                if check_permission(Permission.USER_DELETE):
                    if st.button("Delete User", key=f"delete_{user['id']}", type="secondary"):
                        st.warning(f"User {user['name']} would be deleted")

def show_role_management():
    """Show role management interface"""
    st.subheader("Role Management")
    
    enterprise_auth = get_enterprise_auth()
    
    for role in EnterpriseRole:
        with st.expander(f"{role.value.replace('_', ' ').title()} Role"):
            permissions = enterprise_auth.role_permissions.get(role, [])
            
            st.write(f"**Permissions ({len(permissions)}):**")
            for perm in permissions[:5]:  # Show first 5
                st.write(f"• {perm.value}")
            
            if len(permissions) > 5:
                st.write(f"... and {len(permissions) - 5} more")
            
            if check_permission(Permission.ADMIN_SETTINGS):
                if st.button(f"Edit {role.value}", key=f"edit_role_{role.value}"):
                    st.info("Role editing interface would open here")

def show_permission_matrix():
    """Show permission matrix"""
    st.subheader("Permission Matrix")
    
    enterprise_auth = get_enterprise_auth()
    
    # Create permission matrix
    matrix_data = []
    all_permissions = list(Permission)
    
    for role in EnterpriseRole:
        row = {"Role": role.value.replace('_', ' ').title()}
        role_permissions = enterprise_auth.role_permissions.get(role, [])
        
        for perm in all_permissions:
            row[perm.value] = "✅" if perm in role_permissions else "❌"
        
        matrix_data.append(row)
    
    if st.checkbox("Show detailed permission matrix"):
        st.dataframe(matrix_data, width="stretch")

def show_enterprise_connectors():
    """Display enterprise connector management"""
    if not check_permission(Permission.DATA_SOURCE_CONNECT):
        st.error("Access denied. Insufficient permissions.")
        return
    
    st.title("🔗 Enterprise Connectors")
    
    tab1, tab2, tab3 = st.tabs(["Salesforce", "SAP", "Connection Status"])
    
    with tab1:
        show_salesforce_connector()
    
    with tab2:
        show_sap_connector()
    
    with tab3:
        show_connector_status()

def show_salesforce_connector():
    """Salesforce connector configuration"""
    st.subheader("Salesforce Integration")
    
    with st.form("salesforce_config"):
        st.write("**Authentication Settings**")
        
        col1, col2 = st.columns(2)
        with col1:
            client_id = st.text_input("Consumer Key", type="password")
            username = st.text_input("Username")
            sandbox = st.checkbox("Sandbox Environment")
        
        with col2:
            client_secret = st.text_input("Consumer Secret", type="password")
            password = st.text_input("Password", type="password")
            security_token = st.text_input("Security Token", type="password")
        
        if st.form_submit_button("Test Connection"):
            if client_id and client_secret and username and password and security_token:
                try:
                    connector = create_salesforce_connector(
                        client_id, client_secret, username, password, security_token, sandbox
                    )
                    
                    if connector.authenticate():
                        st.success("✅ Salesforce connection successful!")
                        
                        # Show available objects
                        objects = connector.get_sobjects()
                        st.write(f"Found {len(objects)} queryable objects")
                        
                        # Store connector in session for scanning
                        st.session_state['salesforce_connector'] = connector
                    else:
                        st.error("❌ Salesforce connection failed")
                        
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
            else:
                st.error("Please fill in all required fields")

def show_sap_connector():
    """SAP connector configuration"""
    st.subheader("SAP Integration")
    
    with st.form("sap_config"):
        st.write("**SAP System Settings**")
        
        col1, col2 = st.columns(2)
        with col1:
            host = st.text_input("SAP Host")
            client = st.text_input("Client (Mandant)")
            username = st.text_input("Username")
        
        with col2:
            port = st.number_input("Port", value=8000, min_value=1, max_value=65535)
            system_id = st.text_input("System ID (SID)")
            password = st.text_input("Password", type="password")
        
        protocol = st.selectbox("Protocol", ["https", "http"])
        
        if st.form_submit_button("Test Connection"):
            if host and client and username and password:
                try:
                    connector = create_sap_connector(
                        host, port, client, username, password, system_id, protocol
                    )
                    
                    if connector.authenticate():
                        st.success("✅ SAP connection successful!")
                        
                        # Show available tables
                        tables = connector.get_data_dictionary_tables()
                        st.write(f"Found {len(tables)} data dictionary tables")
                        
                        # Store connector in session for scanning
                        st.session_state['sap_connector'] = connector
                    else:
                        st.error("❌ SAP connection failed")
                        
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
            else:
                st.error("Please fill in all required fields")

def show_connector_status():
    """Show status of all enterprise connectors"""
    st.subheader("Connector Status")
    
    connectors = {
        "Salesforce": st.session_state.get('salesforce_connector'),
        "SAP": st.session_state.get('sap_connector'),
        "Microsoft 365": st.session_state.get('microsoft365_connector'),
        "Google Workspace": st.session_state.get('google_workspace_connector'),
        "Exact Online": st.session_state.get('exact_online_connector')
    }
    
    for name, connector in connectors.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{name}**")
        
        with col2:
            if connector:
                st.success("✅ Connected")
            else:
                st.error("❌ Disconnected")
        
        with col3:
            if connector:
                if st.button(f"Test {name}", key=f"test_{name.lower()}"):
                    st.info(f"Testing {name} connection...")

def check_permission(permission: Permission) -> bool:
    """Check if current user has permission"""
    user_profile = st.session_state.get('enterprise_user_profile')
    if not user_profile:
        return False
    
    enterprise_auth = get_enterprise_auth()
    return enterprise_auth.has_permission(user_profile, permission)

def get_sample_users() -> List[Dict[str, Any]]:
    """Get sample users for demonstration"""
    return [
        {
            'id': '1',
            'name': 'Jan de Vries',
            'email': 'jan.devries@company.nl',
            'department': 'Compliance',
            'organization': 'Acme Corp',
            'roles': ['compliance_manager', 'privacy_officer']
        },
        {
            'id': '2',
            'name': 'Maria Jansen',
            'email': 'maria.jansen@company.nl',
            'department': 'IT Security',
            'organization': 'Acme Corp',
            'roles': ['security_analyst']
        },
        {
            'id': '3',
            'name': 'Pieter van Berg',
            'email': 'pieter.vanberg@company.nl',
            'department': 'Audit',
            'organization': 'Acme Corp',
            'roles': ['auditor']
        }
    ]

def show_enterprise_sidebar():
    """Show enterprise-specific sidebar content"""
    user_profile = st.session_state.get('enterprise_user_profile')
    
    if user_profile:
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 User Profile")
            st.write(f"**Name:** {user_profile.name}")
            st.write(f"**Email:** {user_profile.email}")
            st.write(f"**Role:** {', '.join([role.value for role in user_profile.roles])}")
            st.write(f"**Auth:** {user_profile.auth_method.upper()}")
            
            if check_permission(Permission.ADMIN_SETTINGS):
                if st.button("⚙️ Admin Panel"):
                    st.session_state['show_admin'] = True
                    st.rerun()
            
            if check_permission(Permission.USER_VIEW):
                if st.button("👥 User Management"):
                    st.session_state['show_rbac'] = True
                    st.rerun()
            
            if check_permission(Permission.DATA_SOURCE_CONNECT):
                if st.button("🔗 Enterprise Connectors"):
                    st.session_state['show_connectors'] = True
                    st.rerun()
            
            if st.button("🚪 Logout"):
                for key in ['enterprise_user_profile', 'authenticated', 'show_admin', 'show_rbac', 'show_connectors']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()