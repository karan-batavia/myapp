"""
Visitor Analytics Dashboard for DataGuardian Pro
Real-time display of visitor tracking, login attempts, and user registrations

GDPR-Compliant Display:
- No personal data shown
- Anonymized metrics only
- Compliance with GDPR Article 5 (data minimization)
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.visitor_tracker import get_visitor_tracker, VisitorEventType
from typing import Dict, Any

def safe_plotly_chart(fig, use_container_width=True, fallback_data=None, fallback_title=""):
    """Safely render Plotly chart with fallback to table on error"""
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        st.plotly_chart(fig, use_container_width=use_container_width)
    except Exception as e:
        if fallback_data:
            st.caption(f"📊 {fallback_title}")
            st.dataframe(pd.DataFrame(fallback_data), use_container_width=True)
        else:
            st.warning(f"Chart unavailable: {str(e)[:50]}")

def render_visitor_analytics_dashboard():
    """
    Render visitor analytics dashboard
    
    Metrics displayed:
    - Total unique visitors (last 7/30 days)
    - Login attempts (success/failure)
    - User registrations (success/failure)
    - Top pages visited
    - Traffic sources (referrers)
    - Geographic distribution (countries)
    """
    
    st.markdown("## 📊 Visitor Analytics Dashboard")
    st.markdown("*GDPR-compliant tracking with IP anonymization*")
    
    # Time period selector
    col1, col2 = st.columns([3, 1])
    with col2:
        period = st.selectbox(
            "Period",
            options=[7, 14, 30, 90],
            format_func=lambda x: f"Last {x} days",
            key="analytics_period"
        )
    
    # Get analytics data
    tracker = get_visitor_tracker()
    analytics = tracker.get_analytics(days=period)
    
    # Key metrics row
    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Unique Visitors",
            value=analytics['total_visitors'],
            help="Unique sessions (no personal data tracked)"
        )
    
    with col2:
        st.metric(
            label="Page Views",
            value=analytics['total_pageviews']
        )
    
    with col3:
        login_total = analytics['login_success'] + analytics['login_failure']
        login_rate = (analytics['login_success'] / login_total * 100) if login_total > 0 else 0
        st.metric(
            label="Login Success Rate",
            value=f"{login_rate:.1f}%",
            delta=f"{analytics['login_success']}/{login_total}"
        )
    
    with col4:
        reg_total = analytics['registration_success'] + analytics['registration_failure']
        reg_rate = (analytics['registration_success'] / reg_total * 100) if reg_total > 0 else 0
        st.metric(
            label="Registration Success Rate",
            value=f"{reg_rate:.1f}%",
            delta=f"{analytics['registration_success']}/{reg_total}"
        )
    
    # Detailed metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔐 Authentication Events")
        
        # Login attempts breakdown
        login_data = {
            'Status': ['Success', 'Failure'],
            'Count': [analytics['login_success'], analytics['login_failure']]
        }
        
        try:
            import plotly.express as px
            fig_login = px.pie(
                login_data,
                values='Count',
                names='Status',
                title=f"Login Attempts ({login_total} total)",
                color='Status',
                color_discrete_map={'Success': '#00D26A', 'Failure': '#FF4B4B'}
            )
            fig_login.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_login, use_container_width=True)
        except Exception:
            st.caption(f"Login Attempts ({login_total} total)")
            st.dataframe(pd.DataFrame(login_data), use_container_width=True, hide_index=True)
        
        # Registration attempts breakdown
        st.markdown("### 👥 User Registrations")
        reg_data = {
            'Status': ['Success', 'Failure'],
            'Count': [analytics['registration_success'], analytics['registration_failure']]
        }
        
        try:
            import plotly.express as px
            fig_reg = px.pie(
                reg_data,
                values='Count',
                names='Status',
                title=f"Registration Attempts ({reg_total} total)",
                color='Status',
                color_discrete_map={'Success': '#00D26A', 'Failure': '#FF4B4B'}
            )
            fig_reg.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_reg, use_container_width=True)
        except Exception:
            st.caption(f"Registration Attempts ({reg_total} total)")
            st.dataframe(pd.DataFrame(reg_data), use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### 📄 Top Pages Visited")
        
        if analytics['top_pages']:
            pages_df = {
                'Page': [p['page_path'] for p in analytics['top_pages'][:10]],
                'Views': [p['views'] for p in analytics['top_pages'][:10]]
            }
            
            try:
                import plotly.express as px
                fig_pages = px.bar(
                    pages_df,
                    x='Views',
                    y='Page',
                    orientation='h',
                    title="Most Visited Pages"
                )
                fig_pages.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_pages, use_container_width=True)
            except Exception:
                st.dataframe(pd.DataFrame(pages_df), use_container_width=True, hide_index=True)
        else:
            st.info("No page view data available yet")
        
        st.markdown("### 🔗 Traffic Sources")
        
        if analytics['top_referrers']:
            referrers_df = {
                'Source': [r['referrer'] for r in analytics['top_referrers'][:10]],
                'Visits': [r['visits'] for r in analytics['top_referrers'][:10]]
            }
            
            try:
                import plotly.express as px
                fig_refs = px.bar(
                    referrers_df,
                    x='Visits',
                    y='Source',
                    orientation='h',
                    title="Top Referrers"
                )
                fig_refs.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_refs, use_container_width=True)
            except Exception:
                st.dataframe(pd.DataFrame(referrers_df), use_container_width=True, hide_index=True)
        else:
            st.info("No referrer data available yet")
    
    # Geographic distribution
    if analytics['countries']:
        st.markdown("### 🌍 Geographic Distribution")
        
        # Country code to full name and flag mapping
        country_names = {
            'NL': ('🇳🇱', 'Netherlands'),
            'DE': ('🇩🇪', 'Germany'),
            'BE': ('🇧🇪', 'Belgium'),
            'FR': ('🇫🇷', 'France'),
            'GB': ('🇬🇧', 'United Kingdom'),
            'US': ('🇺🇸', 'United States'),
            'ES': ('🇪🇸', 'Spain'),
            'IT': ('🇮🇹', 'Italy'),
            'PL': ('🇵🇱', 'Poland'),
            'AT': ('🇦🇹', 'Austria'),
            'CH': ('🇨🇭', 'Switzerland'),
            'SE': ('🇸🇪', 'Sweden'),
            'NO': ('🇳🇴', 'Norway'),
            'DK': ('🇩🇰', 'Denmark'),
            'FI': ('🇫🇮', 'Finland'),
            'IE': ('🇮🇪', 'Ireland'),
            'PT': ('🇵🇹', 'Portugal'),
            'LU': ('🇱🇺', 'Luxembourg'),
            'CZ': ('🇨🇿', 'Czech Republic'),
            'GR': ('🇬🇷', 'Greece'),
            'RO': ('🇷🇴', 'Romania'),
            'HU': ('🇭🇺', 'Hungary'),
            'IN': ('🇮🇳', 'India'),
            'CN': ('🇨🇳', 'China'),
            'JP': ('🇯🇵', 'Japan'),
            'AU': ('🇦🇺', 'Australia'),
            'CA': ('🇨🇦', 'Canada'),
            'BR': ('🇧🇷', 'Brazil'),
            'RU': ('🇷🇺', 'Russia'),
            'ZA': ('🇿🇦', 'South Africa'),
        }
        
        def get_country_display(code):
            if code in country_names:
                flag, name = country_names[code]
                return f"{flag} {name}"
            return f"🌐 {code}"
        
        countries_display = [get_country_display(c['country']) for c in analytics['countries']]
        
        countries_df = {
            'Country': countries_display,
            'Visitors': [c['visitors'] for c in analytics['countries']]
        }
        
        # Display as clean table with country names and flags
        df = pd.DataFrame(countries_df)
        df = df.sort_values('Visitors', ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Visitor Sessions section
    st.markdown("### 👤 Visitor Sessions")
    st.caption("Who visited which pages (anonymized, GDPR-compliant)")
    
    sessions = tracker.get_visitor_sessions(days=period, limit=50)
    
    if sessions:
        sessions_data = []
        for session in sessions:
            user_display = 'Anonymous Visitor'
            if session.get('user_id'):
                user_display = f"User-{session['user_id'][:8]}"
            if session.get('logged_in'):
                user_display += " 🔐"
            
            pages = session.get('pages_visited', [])
            if pages:
                pages_str = ', '.join([p for p in pages if p][:5])
                if len(pages) > 5:
                    pages_str += f" (+{len(pages)-5} more)"
            else:
                pages_str = "N/A"
            
            session_start = session.get('session_start')
            if hasattr(session_start, 'strftime'):
                start_str = session_start.strftime('%Y-%m-%d %H:%M')
            else:
                start_str = str(session_start)[:16] if session_start else 'N/A'
            
            sessions_data.append({
                'Session Start': start_str,
                'Visitor': user_display,
                'Pages Viewed': session.get('page_views', 0),
                'Pages Visited': pages_str,
                'Total Actions': session.get('total_events', 0)
            })
        
        st.dataframe(sessions_data, use_container_width=True)
    else:
        st.info("No visitor session data available yet")
    
    # Recent Events section
    st.markdown("### 📋 Recent Events")
    
    recent_events = tracker.get_recent_events(limit=30, days=period)
    
    if recent_events:
        events_data = []
        for event in recent_events:
            user_display = 'Anonymous'
            if event.get('user_id'):
                user_display = f"User-{event['user_id'][:8]}"
            
            timestamp = event.get('timestamp')
            if hasattr(timestamp, 'strftime'):
                time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_str = str(timestamp)[:19] if timestamp else 'N/A'
            
            event_type = event.get('event_type', 'unknown')
            event_display = event_type.replace('_', ' ').title()
            
            events_data.append({
                'Time': time_str,
                'Event': event_display,
                'Page': event.get('page_path', '/'),
                'Visitor': user_display,
                'Status': '✅ Success' if event.get('success', True) else '❌ Failed'
            })
        
        st.dataframe(events_data, use_container_width=True)
    else:
        st.info("No recent events recorded yet")
    
    # GDPR compliance notice
    st.markdown("---")
    st.markdown("""
    **🔒 Privacy & GDPR Compliance:**
    - ✅ IP addresses anonymized (hashed)
    - ✅ No cookies stored
    - ✅ No personal data tracked
    - ✅ 90-day data retention
    - ✅ GDPR Articles 5, 17, 32 compliant
    """)
    
    # Data cleanup button (admin only)
    if st.session_state.get('user_role') == 'admin':
        st.markdown("### 🗑️ Data Management")
        if st.button("Clean Up Old Events (>90 days)", type="secondary"):
            tracker.cleanup_old_events(retention_days=90)
            st.success("✅ Old events cleaned up per GDPR data retention policy")
            st.rerun()
