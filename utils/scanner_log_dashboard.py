#!/usr/bin/env python3
"""
DataGuardian Pro - Scanner-Focused Log Dashboard
Redesigned UI for scanner logging analysis and monitoring
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import streamlit as st
try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    pd = None
    px = None
    go = None

class ScannerLogAnalyzer:
    """Specialized analyzer for scanner logs only"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        self.scanner_log_files = [
            "dataguardian_scanner.log",
            "ai_model_scanner.log",
            "repo_scan.log",
            "scan_extract.log"
        ]
    
    def get_scanner_logs(self, hours: int = 24, scanner_type: str = None, level: str = None) -> List[Dict[str, Any]]:
        """Get scanner-specific logs with filtering"""
        entries = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Check all .log files in the directory, not just the predefined ones
        for log_file_path in self.logs_dir.glob("*.log"):
            if log_file_path.exists():
                entries.extend(self._parse_scanner_log_file(log_file_path, cutoff_time, scanner_type, level))
        
        # Sort by timestamp descending
        entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return entries
    
    def _parse_scanner_log_file(self, log_file: Path, cutoff_time: datetime, 
                               scanner_filter: str = None, level_filter: str = None) -> List[Dict[str, Any]]:
        """Parse scanner log file with enhanced filtering"""
        entries = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # Try to parse as JSON first (new format)
                        entry = json.loads(line)
                        
                        # Only include scanner-related logs, but exclude profiler/performance logs
                        if entry.get('category') != 'scanner':
                            continue
                        
                        # Exclude performance monitoring and profiler logs
                        logger_name = entry.get('logger', '')
                        if 'profiler' in logger_name.lower() or 'performance' in entry.get('message', '').lower():
                            continue
                            
                    except json.JSONDecodeError:
                        # Handle old format logs (timestamp - logger - level - message)
                        # Example: "2025-05-13 16:10:12,963 - services.enhanced_ai_model_scanner - INFO - Starting scan"
                        if ' - ' in line and any(keyword in line.lower() for keyword in ['scanner', 'scan', 'model', 'pii', 'compliance']):
                            parts = line.split(' - ', 3)
                            if len(parts) >= 4:
                                timestamp_str = parts[0]
                                logger_name = parts[1]
                                level = parts[2]
                                message = parts[3]
                                
                                # Extract scanner type from logger name or message
                                scanner_type = 'unknown'
                                if 'ai_model' in logger_name.lower() or 'ai_model' in message.lower():
                                    scanner_type = 'ai_model_scanner'
                                elif 'code_scanner' in logger_name.lower() or 'code scan' in message.lower():
                                    scanner_type = 'code_scanner'
                                elif 'blob' in logger_name.lower() or 'blob' in message.lower():
                                    scanner_type = 'blob_scanner'
                                elif 'website' in logger_name.lower() or 'website' in message.lower():
                                    scanner_type = 'website_scanner'
                                elif 'database' in logger_name.lower() or 'database' in message.lower():
                                    scanner_type = 'db_scanner'
                                elif 'repo' in logger_name.lower() or 'repository' in message.lower():
                                    scanner_type = 'repo_scanner'
                                
                                # Skip profiler and performance monitoring logs
                                if 'profiler' in logger_name.lower() or 'performance' in message.lower():
                                    continue
                                
                                # Convert to standardized format
                                entry = {
                                    'timestamp': timestamp_str,
                                    'level': level,
                                    'category': 'scanner',
                                    'scanner_type': scanner_type,
                                    'message': message,
                                    'logger': logger_name
                                }
                            else:
                                continue
                        else:
                            continue
                    
                    # Parse timestamp (common for both JSON and legacy formats)
                    timestamp_str = entry.get('timestamp', '')
                    if timestamp_str:
                        try:
                            # Handle different timestamp formats
                            if 'T' in timestamp_str and ('Z' in timestamp_str or '+' in timestamp_str):
                                # ISO format: "2025-09-06T18:22:17.193090Z"
                                log_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            elif ',' in timestamp_str and '-' in timestamp_str:
                                # Old format: "2025-05-13 16:10:12,963"
                                log_time = datetime.strptime(timestamp_str.split(',')[0], '%Y-%m-%d %H:%M:%S')
                            else:
                                # Default parsing attempt
                                log_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            
                            if log_time.replace(tzinfo=None) < cutoff_time:
                                continue
                        except (ValueError, TypeError):
                            # Skip logs with unparseable timestamps
                            continue
                    
                    # Skip entries with unknown scanner type unless it's a legitimate scanner activity
                    scanner_type = entry.get('scanner_type', 'unknown')
                    if scanner_type == 'unknown':
                        # Only keep unknown types if they contain actual scanner keywords
                        message = entry.get('message', '').lower()
                        if not any(keyword in message for keyword in ['scan started', 'scan completed', 'scan failed', 'pii detected', 'compliance']):
                            continue
                    
                    # Filter by scanner type if specified
                    if scanner_filter and scanner_filter != "All":
                        if scanner_type.lower() != scanner_filter.lower():
                            continue
                    
                    # Filter by level if specified
                    if level_filter and level_filter != "All":
                        if entry.get('level', '').upper() != level_filter.upper():
                            continue
                    
                    entries.append(entry)
                        
        except Exception as e:
            st.error(f"Error reading scanner log file {log_file}: {e}")
        
        return entries
    
    def get_scanner_types(self) -> List[str]:
        """Get list of scanner types that actually have logs available"""
        scanner_types = set()
        
        # Check all .log files in the directory for scanner types
        for log_file_path in self.logs_dir.glob("*.log"):
            if log_file_path.exists():
                try:
                    with open(log_file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                entry = json.loads(line)
                                if entry.get('category') == 'scanner' and entry.get('scanner_type'):
                                    scanner_type = entry['scanner_type']
                                    # Only include valid scanner types, exclude 'unknown'
                                    if scanner_type != 'unknown':
                                        scanner_types.add(scanner_type)
                            except (json.JSONDecodeError, AttributeError):
                                continue
                except Exception:
                    continue
        
        return sorted(list(scanner_types))
    
    def get_scanner_activity_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get scanner activity summary with metrics"""
        logs = self.get_scanner_logs(hours=hours)
        
        scanner_stats = defaultdict(lambda: {
            'total_operations': 0,
            'successful_operations': 0,
            'errors': 0,
            'warnings': 0,
            'total_execution_time': 0,
            'memory_usage_total': 0,
            'operations_count': 0,
            'last_activity': None
        })
        
        total_operations = 0
        total_errors = 0
        activity_timeline = []
        
        for log in logs:
            scanner_type = log.get('scanner_type', 'unknown')
            stats = scanner_stats[scanner_type]
            level = log.get('level', 'INFO')
            
            total_operations += 1
            stats['total_operations'] += 1
            
            # Track activity timeline
            activity_timeline.append({
                'timestamp': log.get('timestamp'),
                'scanner': scanner_type,
                'level': level,
                'message': log.get('message', '')
            })
            
            # Count by level
            if level == 'ERROR':
                stats['errors'] += 1
                total_errors += 1
            elif level == 'WARNING':
                stats['warnings'] += 1
            elif level == 'INFO' and 'completed' in log.get('message', '').lower():
                stats['successful_operations'] += 1
            
            # Performance metrics
            exec_time = log.get('execution_time', 0)
            if exec_time > 0:
                stats['total_execution_time'] += exec_time
                stats['operations_count'] += 1
            
            memory_usage = log.get('memory_usage', 0)
            if memory_usage > 0:
                stats['memory_usage_total'] += memory_usage
            
            # Last activity
            if not stats['last_activity'] or log.get('timestamp', '') > stats['last_activity']:
                stats['last_activity'] = log.get('timestamp')
        
        # Calculate averages - ensure no division by zero
        for scanner, stats in scanner_stats.items():
            operations_count = stats.get('operations_count', 0) or 0
            total_ops = stats.get('total_operations', 0) or 0
            
            if operations_count > 0:
                stats['avg_execution_time'] = (stats.get('total_execution_time', 0) or 0) / operations_count
                stats['avg_memory_usage'] = (stats.get('memory_usage_total', 0) or 0) / operations_count
            else:
                stats['avg_execution_time'] = 0
                stats['avg_memory_usage'] = 0
            
            # Calculate success rate
            if total_ops > 0:
                stats['success_rate'] = ((stats.get('successful_operations', 0) or 0) / total_ops) * 100
            else:
                stats['success_rate'] = 0
        
        return {
            'scanner_stats': dict(scanner_stats),
            'total_operations': total_operations,
            'total_errors': total_errors,
            'activity_timeline': activity_timeline[-50:],  # Last 50 activities
            'active_scanners': len(scanner_stats)
        }

class ScannerLogDashboard:
    """Redesigned Streamlit dashboard for scanner logs"""
    
    def __init__(self):
        self.analyzer = ScannerLogAnalyzer()
    
    def show_dashboard(self):
        """Display redesigned scanner log dashboard"""
        st.title("🔍 Scanner Logs Dashboard")
        st.markdown("*Real-time monitoring and analysis of DataGuardian Pro scanner activities*")
        
        # Dashboard controls
        self._show_controls()
        
        # Get user selections
        hours = st.session_state.get('log_hours', 24)
        scanner_filter = st.session_state.get('log_scanner_filter', 'All')
        level_filter = st.session_state.get('log_level_filter', 'All')
        
        # Main dashboard sections
        self._show_overview_metrics(hours)
        self._show_scanner_performance(hours, scanner_filter)
        self._show_activity_timeline(hours, scanner_filter, level_filter)
        self._show_log_details(hours, scanner_filter, level_filter)
    
    def _show_controls(self):
        """Display dashboard controls"""
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                hours = st.selectbox(
                    "📅 Time Range", 
                    [1, 6, 12, 24, 48, 168], 
                    index=3, 
                    format_func=lambda x: f"Last {x} hours",
                    key='log_hours'
                )
            
            with col2:
                scanner_types = ["All"] + self.analyzer.get_scanner_types()
                scanner_filter = st.selectbox(
                    "🔍 Scanner Type", 
                    scanner_types,
                    key='log_scanner_filter'
                )
            
            with col3:
                level_filter = st.selectbox(
                    "📊 Log Level", 
                    ["All", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    key='log_level_filter'
                )
            
            with col4:
                if st.button("🔄 Refresh", width="stretch"):
                    st.rerun()
        
        st.divider()
    
    def _show_overview_metrics(self, hours: int):
        """Show overview metrics cards"""
        st.subheader("📊 Scanner Activity Overview")
        
        summary = self.analyzer.get_scanner_activity_summary(hours)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Operations", 
                summary['total_operations'],
                delta=None,
                help="Total scanner operations in the selected time period"
            )
        
        with col2:
            st.metric(
                "Active Scanners", 
                summary['active_scanners'],
                delta=None,
                help="Number of different scanner types that were active"
            )
        
        with col3:
            error_rate = (summary['total_errors'] / summary['total_operations'] * 100) if summary['total_operations'] > 0 else 0
            st.metric(
                "Error Rate", 
                f"{error_rate:.1f}%",
                delta=None,
                help="Percentage of operations that resulted in errors"
            )
        
        with col4:
            st.metric(
                "Total Errors", 
                summary['total_errors'],
                delta=None,
                help="Total number of error-level log entries"
            )
    
    def _show_scanner_performance(self, hours: int, scanner_filter: str):
        """Show scanner performance metrics"""
        st.subheader("⚡ Scanner Performance Metrics")
        
        summary = self.analyzer.get_scanner_activity_summary(hours)
        scanner_stats = summary['scanner_stats']
        
        if not scanner_stats:
            st.info("No scanner activity found for the selected time period.")
            return
        
        # Filter data if specific scanner selected
        if scanner_filter != "All":
            if scanner_filter in scanner_stats:
                scanner_stats = {scanner_filter: scanner_stats[scanner_filter]}
            else:
                st.warning(f"No data found for scanner: {scanner_filter}")
                return
        
        # Create performance dataframe
        perf_data = []
        for scanner, stats in scanner_stats.items():
            perf_data.append({
                'Scanner': scanner,
                'Operations': stats['total_operations'],
                'Success Rate': f"{stats['success_rate']:.1f}%",
                'Avg Exec Time': f"{stats['avg_execution_time']:.3f}s",
                'Avg Memory': f"{stats['avg_memory_usage']:.1f}MB",
                'Errors': stats['errors'],
                'Warnings': stats['warnings'],
                'Last Activity': stats['last_activity'][:19] if stats['last_activity'] else 'N/A'
            })
        
        if perf_data:
            if CHARTS_AVAILABLE and pd is not None:
                df = pd.DataFrame(perf_data)
                st.dataframe(
                    df, 
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Scanner": st.column_config.TextColumn("Scanner Type", width="medium"),
                        "Operations": st.column_config.NumberColumn("Total Ops", width="small"),
                        "Success Rate": st.column_config.TextColumn("Success %", width="small"),
                        "Avg Exec Time": st.column_config.TextColumn("Avg Time", width="small"),
                        "Avg Memory": st.column_config.TextColumn("Avg Memory", width="small"),
                        "Errors": st.column_config.NumberColumn("Errors", width="small"),
                        "Warnings": st.column_config.NumberColumn("Warnings", width="small"),
                        "Last Activity": st.column_config.TextColumn("Last Seen", width="medium")
                    }
                )
            else:
                # Fallback display without pandas
                for data in perf_data:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Scanner", data['Scanner'])
                    with col2:
                        st.metric("Operations", data['Operations'])
                    with col3:
                        st.metric("Success Rate", data['Success Rate'])
                    with col4:
                        st.metric("Errors", data['Errors'])
                    st.divider()
            
            # Performance charts
            if len(perf_data) > 1 and CHARTS_AVAILABLE and px is not None and 'df' in locals():
                col1, col2 = st.columns(2)
                
                with col1:
                    # Operations chart
                    fig_ops = px.bar(
                        df, 
                        x='Scanner', 
                        y='Operations',
                        title="Operations by Scanner",
                        color='Operations',
                        color_continuous_scale='Blues'
                    )
                    fig_ops.update_layout(height=400)
                    st.plotly_chart(fig_ops, width="stretch")
                
                with col2:
                    # Error rate chart
                    error_data = []
                    for scanner, stats in scanner_stats.items():
                        error_data.append({
                            'Scanner': scanner,
                            'Errors': stats['errors'],
                            'Warnings': stats['warnings'],
                            'Success': stats['successful_operations']
                        })
                    
                    if pd is not None:
                        error_df = pd.DataFrame(error_data)
                        fig_errors = px.bar(
                        error_df, 
                        x='Scanner', 
                        y=['Errors', 'Warnings', 'Success'],
                        title="Status Distribution by Scanner",
                        color_discrete_map={
                            'Errors': '#ff4444',
                            'Warnings': '#ffaa00', 
                            'Success': '#44ff44'
                        }
                        )
                        fig_errors.update_layout(height=400)
                        st.plotly_chart(fig_errors, width="stretch")
    
    def _show_activity_timeline(self, hours: int, scanner_filter: str, level_filter: str):
        """Show scanner activity timeline"""
        st.subheader("⏱️ Recent Activity Timeline")
        
        logs = self.analyzer.get_scanner_logs(hours, scanner_filter, level_filter)
        
        if not logs:
            st.info("No scanner activity found for the selected filters.")
            return
        
        # Show recent activities in an expandable section
        with st.expander(f"📋 Recent Activities ({len(logs)} entries)", expanded=True):
            for i, log in enumerate(logs[:20]):  # Show last 20 activities
                timestamp = log.get('timestamp', 'Unknown')[:19]
                level = log.get('level', 'INFO')
                scanner = log.get('scanner_type', 'unknown')
                message = log.get('message', 'No message')
                
                # Style based on log level
                if level == 'ERROR':
                    st.error(f"🔴 **{timestamp}** `{scanner}`: {message}")
                elif level == 'WARNING':
                    st.warning(f"🟡 **{timestamp}** `{scanner}`: {message}")
                elif level == 'CRITICAL':
                    st.error(f"🔥 **{timestamp}** `{scanner}`: {message}")
                else:
                    st.info(f"🟢 **{timestamp}** `{scanner}`: {message}")
    
    def _show_log_details(self, hours: int, scanner_filter: str, level_filter: str):
        """Show detailed log search and filter"""
        st.subheader("🔍 Detailed Log Search")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Search in log messages", 
                placeholder="Enter search term...",
                help="Search for specific terms in log messages"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            export_logs = st.button("📥 Export Logs", width="stretch")
        
        # Get filtered logs
        logs = self.analyzer.get_scanner_logs(hours, scanner_filter, level_filter)
        
        # Apply search filter
        if search_query:
            search_lower = search_query.lower()
            logs = [log for log in logs if search_lower in log.get('message', '').lower()]
        
        # Show results
        if logs:
            st.write(f"**Found {len(logs)} matching log entries:**")
            
            # Pagination
            page_size = 50
            total_pages = (len(logs) + page_size - 1) // page_size
            
            if total_pages > 1:
                page = st.number_input("Page", min_value=1, max_value=total_pages, value=1) - 1
                start_idx = page * page_size
                end_idx = min(start_idx + page_size, len(logs))
                page_logs = logs[start_idx:end_idx]
                st.caption(f"Showing {start_idx + 1}-{end_idx} of {len(logs)} entries")
            else:
                page_logs = logs[:page_size]
            
            # Display logs in a clean format
            for log in page_logs:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 4])
                    
                    with col1:
                        st.code(log.get('timestamp', 'Unknown')[:19])
                    
                    with col2:
                        level = log.get('level', 'INFO')
                        if level == 'ERROR':
                            st.error(level, icon="🔴")
                        elif level == 'WARNING':
                            st.warning(level, icon="🟡")
                        elif level == 'CRITICAL':
                            st.error(level, icon="🔥")
                        else:
                            st.success(level, icon="🟢")
                    
                    with col3:
                        scanner = log.get('scanner_type', 'unknown')
                        message = log.get('message', 'No message')
                        st.write(f"**{scanner}**: {message}")
                    
                    st.divider()
        
        # Export functionality
        if export_logs and logs:
            if CHARTS_AVAILABLE:
                export_data = []
                for log in logs:
                    export_data.append({
                        'Timestamp': log.get('timestamp', ''),
                        'Level': log.get('level', ''),
                        'Scanner': log.get('scanner_type', ''),
                        'Message': log.get('message', ''),
                        'Execution Time': log.get('execution_time', 0),
                        'Memory Usage': log.get('memory_usage', 0)
                    })
                
                df = pd.DataFrame(export_data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"scanner_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Export functionality requires pandas. Please install pandas to enable CSV export.")

def show_scanner_log_dashboard():
    """Show the redesigned scanner log dashboard"""
    dashboard = ScannerLogDashboard()
    dashboard.show_dashboard()

if __name__ == "__main__":
    show_scanner_log_dashboard()