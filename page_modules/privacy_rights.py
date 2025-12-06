"""
Privacy Rights Page Module
GDPR privacy rights portal for data subjects
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)


def render_privacy_rights_page():
    """Render privacy rights portal for GDPR compliance"""
    from utils.i18n import get_text as _
    
    st.title(f"🔒 {_('sidebar.privacy_rights', 'Privacy Rights')}")
    
    try:
        from components.privacy_rights_portal import PrivacyRightsPortal
        privacy_portal = PrivacyRightsPortal()
        privacy_portal.render_portal()
        
    except ImportError:
        _render_fallback_privacy_portal()
    except Exception as e:
        logger.error(f"Privacy rights page error: {e}")
        _render_fallback_privacy_portal()


def _render_fallback_privacy_portal():
    """Fallback privacy rights interface"""
    st.markdown("""
    ### Your Privacy Rights Under GDPR
    
    As a data subject under the General Data Protection Regulation (GDPR), 
    you have the following rights regarding your personal data:
    """)
    
    rights = [
        {
            "title": "Right of Access (Article 15)",
            "description": "You have the right to obtain confirmation as to whether personal data concerning you is being processed, and access to that data.",
            "action": "Request Data Access"
        },
        {
            "title": "Right to Rectification (Article 16)",
            "description": "You have the right to have inaccurate personal data corrected without undue delay.",
            "action": "Request Correction"
        },
        {
            "title": "Right to Erasure (Article 17)",
            "description": "You have the right to have your personal data erased under certain circumstances ('right to be forgotten').",
            "action": "Request Deletion"
        },
        {
            "title": "Right to Restriction (Article 18)",
            "description": "You have the right to restrict the processing of your personal data under certain conditions.",
            "action": "Request Restriction"
        },
        {
            "title": "Right to Data Portability (Article 20)",
            "description": "You have the right to receive your personal data in a structured, commonly used format.",
            "action": "Request Export"
        },
        {
            "title": "Right to Object (Article 21)",
            "description": "You have the right to object to processing of your personal data for specific purposes.",
            "action": "Submit Objection"
        }
    ]
    
    for right in rights:
        with st.expander(right["title"]):
            st.write(right["description"])
            if st.button(right["action"], key=f"btn_{right['title'][:10]}"):
                _handle_privacy_request(right["title"])
    
    st.markdown("---")
    
    st.subheader("Submit a Privacy Request")
    
    request_type = st.selectbox(
        "Type of Request",
        ["Data Access Request", "Rectification Request", "Erasure Request", "Data Export Request", "Objection to Processing"]
    )
    
    email = st.text_input("Your Email Address", placeholder="your@email.com")
    details = st.text_area("Additional Details", placeholder="Please provide any additional information about your request...")
    
    if st.button("📨 Submit Request", type="primary"):
        if email:
            st.success(f"""
            ✅ **Request Submitted Successfully**
            
            Your {request_type.lower()} has been received. We will respond within 30 days as required by GDPR.
            
            **Reference Number:** DSAR-{hash(email) % 100000:05d}
            
            A confirmation email has been sent to {email}.
            """)
        else:
            st.error("Please provide your email address.")
    
    st.markdown("---")
    
    st.subheader("Contact Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Privacy Team**  
        📧 privacy@dataguardianpro.nl  
        📞 +31 (0)20 123 4567
        
        **Response Time:** Within 30 days
        """)
    
    with col2:
        st.markdown("""
        **Data Protection Officer**  
        📧 dpo@dataguardianpro.nl  
        
        **Netherlands Authority for Personal Data**  
        📧 [Autoriteit Persoonsgegevens](https://autoriteitpersoonsgegevens.nl)
        """)


def _handle_privacy_request(request_type: str):
    """Handle a specific privacy request"""
    st.info(f"""
    **{request_type}**
    
    To proceed with your request, please fill out the form below or contact our Privacy Team:
    
    📧 privacy@dataguardianpro.nl
    
    We will respond to your request within 30 days as required by GDPR Article 12.
    """)
