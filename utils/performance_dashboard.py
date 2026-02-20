"""
Performance Dashboard for DataGuardian Pro
Modern, professional real-time monitoring and optimization insights
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any, List
import logging
import os

from utils.database_optimizer import get_optimized_db
from utils.redis_cache import get_cache, get_performance_cache
from utils.session_optimizer import get_session_optimizer
from utils.code_profiler import get_profiler

logger = logging.getLogger(__name__)

class PerformanceDashboard:
    """Modern Performance monitoring dashboard"""
    
    def __init__(self):
        self.db_optimizer = get_optimized_db()
        self.redis_cache = get_cache()
        self.performance_cache = get_performance_cache()
        self.session_optimizer = get_session_optimizer()
        self.profiler = get_profiler()
    
    def render_dashboard(self):
        """Render the complete modern performance dashboard"""
        
        # Custom CSS for professional styling
        st.markdown("""
        <style>
        .perf-header {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            color: white;
        }
        .perf-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 600;
        }
        .perf-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
            font-size: 1rem;
        }
        .metric-card {
            background: white;
            padding: 1.2rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #1e3a5f;
            margin-bottom: 1rem;
        }
        .status-good { border-left-color: #10b981 !important; }
        .status-warning { border-left-color: #f59e0b !important; }
        .status-critical { border-left-color: #ef4444 !important; }
        .section-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1e3a5f;
            margin: 1.5rem 0 1rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="perf-header">
            <h1>📊 Performance Dashboard</h1>
            <p>Real-time system monitoring and optimization insights</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Last updated timestamp
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Performance summary cards
        self._render_summary_cards()
        
        st.markdown("---")
        
        # Main content in two columns
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_system_health()
        
        with col2:
            self._render_cache_metrics()
        
        st.markdown("---")
        
        # Detailed analysis tabs
        self._render_detailed_analysis()
    
    def _render_summary_cards(self):
        """Render modern performance summary cards"""
        try:
            db_stats = {'pool_stats': {'avg_query_time': 0, 'total_queries': 0}}
            cache_stats = {'hit_rate': 0, 'total_keys': 0, 'connected': False}
            session_stats = {'active_sessions': 0, 'peak_concurrent': 0, 'system_resources': {'memory_percent': 0, 'cpu_percent': 0}}
            
            try:
                db_stats = self.db_optimizer.get_performance_stats()
            except Exception:
                pass
            
            try:
                cache_stats = self.redis_cache.get_stats()
            except Exception:
                pass
            
            try:
                session_stats = self.session_optimizer.get_session_stats()
            except Exception:
                pass
            
            # Calculate health scores
            memory_pct = session_stats.get('system_resources', {}).get('memory_percent', 0)
            cpu_pct = session_stats.get('system_resources', {}).get('cpu_percent', 0)
            cache_hit = cache_stats.get('hit_rate', 0) * 100
            avg_query = db_stats['pool_stats'].get('avg_query_time', 0)
            
            # Overall health calculation
            health_score = 100
            if memory_pct > 80: health_score -= 20
            if cpu_pct > 80: health_score -= 20
            if cache_hit < 50: health_score -= 15
            if avg_query > 1: health_score -= 15
            health_score = max(0, health_score)
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                health_color = "🟢" if health_score >= 80 else "🟡" if health_score >= 50 else "🔴"
                st.metric(
                    f"{health_color} System Health",
                    f"{health_score}%",
                    "Healthy" if health_score >= 80 else "Needs Attention"
                )
            
            with col2:
                db_status = "🟢" if avg_query < 0.5 else "🟡" if avg_query < 1 else "🔴"
                st.metric(
                    f"{db_status} Database",
                    f"{avg_query:.3f}s",
                    f"{db_stats['pool_stats'].get('total_queries', 0)} queries"
                )
            
            with col3:
                cache_status = "🟢" if cache_hit >= 70 else "🟡" if cache_hit >= 40 else "🔴"
                st.metric(
                    f"{cache_status} Cache Rate",
                    f"{cache_hit:.1f}%",
                    f"{cache_stats.get('total_keys', 0)} keys"
                )
            
            with col4:
                mem_status = "🟢" if memory_pct < 70 else "🟡" if memory_pct < 85 else "🔴"
                st.metric(
                    f"{mem_status} Memory",
                    f"{memory_pct:.1f}%",
                    "Normal" if memory_pct < 70 else "High"
                )
            
            with col5:
                cpu_status = "🟢" if cpu_pct < 70 else "🟡" if cpu_pct < 85 else "🔴"
                st.metric(
                    f"{cpu_status} CPU",
                    f"{cpu_pct:.1f}%",
                    f"{session_stats.get('active_sessions', 0)} sessions"
                )
                
        except Exception as e:
            st.error(f"Error loading metrics: {e}")
    
    def _render_system_health(self):
        """Render system health with modern gauges"""
        st.markdown('<p class="section-title">💻 System Resources</p>', unsafe_allow_html=True)
        
        try:
            session_stats = {'system_resources': {'memory_percent': 0, 'cpu_percent': 0}}
            
            try:
                session_stats = self.session_optimizer.get_session_stats()
            except Exception:
                pass
            
            system_resources = session_stats.get('system_resources', {})
            memory_pct = system_resources.get('memory_percent', 0)
            cpu_pct = system_resources.get('cpu_percent', 0)
            
            # Combined gauge chart
            fig = go.Figure()
            
            # Memory gauge
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=memory_pct,
                title={'text': "Memory", 'font': {'size': 14}},
                domain={'x': [0, 0.45], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1},
                    'bar': {'color': "#3b82f6"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "#e5e7eb",
                    'steps': [
                        {'range': [0, 50], 'color': '#dcfce7'},
                        {'range': [50, 80], 'color': '#fef3c7'},
                        {'range': [80, 100], 'color': '#fee2e2'}
                    ],
                    'threshold': {
                        'line': {'color': "#ef4444", 'width': 3},
                        'thickness': 0.75,
                        'value': 85
                    }
                }
            ))
            
            # CPU gauge
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=cpu_pct,
                title={'text': "CPU", 'font': {'size': 14}},
                domain={'x': [0.55, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1},
                    'bar': {'color': "#10b981"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "#e5e7eb",
                    'steps': [
                        {'range': [0, 50], 'color': '#dcfce7'},
                        {'range': [50, 80], 'color': '#fef3c7'},
                        {'range': [80, 100], 'color': '#fee2e2'}
                    ],
                    'threshold': {
                        'line': {'color': "#ef4444", 'width': 3},
                        'thickness': 0.75,
                        'value': 85
                    }
                }
            ))
            
            fig.update_layout(
                height=250,
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                font={'color': '#374151'}
            )
            
            st.plotly_chart(fig, width="stretch")
            
            # Session metrics
            st.markdown('<p class="section-title">👥 Active Sessions</p>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Active", session_stats.get('active_sessions', 0))
            with col2:
                st.metric("Peak", session_stats.get('peak_concurrent', 0))
            with col3:
                avg_duration = session_stats.get('session_duration_avg', 0) / 60
                st.metric("Avg Duration", f"{avg_duration:.1f}m")
            
        except Exception as e:
            st.error(f"Error loading system health: {e}")
    
    def _render_cache_metrics(self):
        """Render cache performance metrics"""
        st.markdown('<p class="section-title">⚡ Cache Performance</p>', unsafe_allow_html=True)
        
        try:
            cache_stats = {'hit_rate': 0, 'connected': False, 'total_keys': 0, 'memory_used': 'N/A', 'hits': 0, 'misses': 0}
            
            try:
                cache_stats = self.redis_cache.get_stats()
            except Exception:
                pass
            
            hit_rate = cache_stats.get('hit_rate', 0) * 100
            
            # Modern donut chart
            fig = go.Figure(data=[go.Pie(
                labels=['Hits', 'Misses'],
                values=[hit_rate, 100-hit_rate],
                hole=0.7,
                marker_colors=['#10b981', '#e5e7eb'],
                textinfo='none',
                hoverinfo='label+percent'
            )])
            
            fig.update_layout(
                height=200,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
                annotations=[dict(
                    text=f'{hit_rate:.0f}%',
                    x=0.5, y=0.5,
                    font_size=28,
                    font_color='#1e3a5f',
                    showarrow=False
                )]
            )
            
            st.plotly_chart(fig, width="stretch")
            
            # Cache stats grid
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Status", "🟢 Connected" if cache_stats.get('connected') else "🔴 Offline")
                st.metric("Hits", f"{cache_stats.get('hits', 0):,}")
            with col2:
                st.metric("Keys", f"{cache_stats.get('total_keys', 0):,}")
                st.metric("Misses", f"{cache_stats.get('misses', 0):,}")
            
            # Database quick stats
            st.markdown('<p class="section-title">🗄️ Database</p>', unsafe_allow_html=True)
            
            try:
                db_stats = self.db_optimizer.get_performance_stats()
                pool_stats = db_stats.get('pool_stats', {})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Queries", f"{pool_stats.get('total_queries', 0):,}")
                    st.metric("Slow Queries", pool_stats.get('slow_queries', 0))
                with col2:
                    st.metric("Avg Time", f"{pool_stats.get('avg_query_time', 0):.3f}s")
                    st.metric("Cache Hits", pool_stats.get('cache_hits', 0))
            except Exception:
                st.info("Database stats loading...")
            
        except Exception as e:
            st.error(f"Error loading cache metrics: {e}")
    
    def _render_detailed_analysis(self):
        """Render detailed analysis section"""
        st.markdown('<p class="section-title">📈 Detailed Analysis</p>', unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔧 Functions",
            "🔍 Queries", 
            "⚠️ Bottlenecks",
            "💡 Recommendations"
        ])
        
        with tab1:
            self._render_function_performance()
        
        with tab2:
            self._render_query_analysis()
        
        with tab3:
            self._render_bottleneck_analysis()
        
        with tab4:
            self._render_recommendations()
    
    def _render_function_performance(self):
        """Render function performance with modern styling"""
        try:
            profiler_report = self.profiler.get_performance_report()
            slow_functions = profiler_report.get('top_slow_functions', [])
            
            if slow_functions:
                df = pd.DataFrame(slow_functions)
                
                # Modern bar chart
                fig = px.bar(
                    df, 
                    x='name', 
                    y='avg_time',
                    color='avg_time',
                    color_continuous_scale=['#10b981', '#f59e0b', '#ef4444'],
                    labels={'name': 'Function', 'avg_time': 'Avg Time (s)'}
                )
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=80),
                    xaxis_tickangle=-45,
                    showlegend=False,
                    coloraxis_showscale=False
                )
                
                st.plotly_chart(fig, width="stretch")
                
                # Data table
                with st.expander("View Details"):
                    st.dataframe(df, width="stretch", hide_index=True)
            else:
                st.success("✅ No slow functions detected")
                
        except Exception as e:
            st.info("Function profiling data will appear after more usage")
    
    def _render_query_analysis(self):
        """Render query analysis with modern styling"""
        try:
            profiler_report = self.profiler.get_performance_report()
            slow_queries = profiler_report.get('slow_queries', [])
            
            if slow_queries:
                for i, query in enumerate(slow_queries[:5], 1):
                    exec_time = query.get('execution_time', 0)
                    status = "🟢" if exec_time < 0.5 else "🟡" if exec_time < 1 else "🔴"
                    
                    with st.expander(f"{status} Query {i} - {exec_time:.3f}s"):
                        st.code(query.get('query', 'N/A'), language='sql')
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Function:** `{query.get('function', 'Unknown')}`")
                        with col2:
                            st.write(f"**Time:** {query.get('timestamp', 'N/A')}")
            else:
                st.success("✅ No slow queries detected")
                
        except Exception as e:
            st.info("Query analysis data will appear after more database activity")
    
    def _render_bottleneck_analysis(self):
        """Render bottleneck analysis with modern styling"""
        try:
            profiler_report = self.profiler.get_performance_report()
            bottlenecks = profiler_report.get('bottlenecks', [])
            
            if bottlenecks:
                df = pd.DataFrame(bottlenecks)
                
                # Scatter plot
                fig = px.scatter(
                    df, 
                    x='occurrences', 
                    y='avg_time',
                    size='avg_time',
                    color='function',
                    labels={'occurrences': 'Frequency', 'avg_time': 'Avg Time (s)'}
                )
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                
                st.plotly_chart(fig, width="stretch")
                
                with st.expander("View Details"):
                    st.dataframe(df, width="stretch", hide_index=True)
            else:
                st.success("✅ No performance bottlenecks detected")
                
        except Exception as e:
            st.info("Bottleneck data will appear after more system activity")
    
    def _render_recommendations(self):
        """Render recommendations with modern styling"""
        try:
            suggestions = self.profiler.get_optimization_suggestions()
            profiler_report = self.profiler.get_performance_report()
            recommendations = profiler_report.get('recommendations', [])
            
            has_content = False
            
            # High priority
            high_priority = [s for s in suggestions if s.get('priority') == 'high']
            if high_priority:
                has_content = True
                st.error("🚨 **High Priority Issues**")
                for rec in high_priority:
                    st.markdown(f"""
                    <div style="background: #fef2f2; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid #ef4444;">
                        <strong>{rec.get('type', '').replace('_', ' ').title()}</strong><br>
                        {rec.get('issue', '')}<br>
                        <em>💡 {rec.get('suggestion', '')}</em>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Medium priority
            medium_priority = [s for s in suggestions if s.get('priority') == 'medium']
            if medium_priority:
                has_content = True
                st.warning("⚠️ **Medium Priority Issues**")
                for rec in medium_priority:
                    st.markdown(f"""
                    <div style="background: #fffbeb; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid #f59e0b;">
                        <strong>{rec.get('type', '').replace('_', ' ').title()}</strong><br>
                        {rec.get('issue', '')}<br>
                        <em>💡 {rec.get('suggestion', '')}</em>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Recent recommendations
            if recommendations:
                has_content = True
                with st.expander("📋 Recent Recommendations"):
                    for rec in recommendations[-5:]:
                        st.write(f"**{rec.get('category', '').replace('_', ' ').title()}:** {rec.get('issue', '')}")
                        st.write(f"💡 {rec.get('suggestion', '')}")
                        st.caption(f"🕒 {rec.get('timestamp', '')}")
                        st.markdown("---")
            
            if not has_content:
                st.success("🎉 **System performing optimally!**")
                st.write("No optimization recommendations at this time.")
                
        except Exception as e:
            st.info("Recommendations will appear based on system analysis")


def render_performance_dashboard():
    """Render the modern performance dashboard"""
    dashboard = PerformanceDashboard()
    dashboard.render_dashboard()
