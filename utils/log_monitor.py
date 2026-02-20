#!/usr/bin/env python3
"""
DataGuardian Pro - Log Monitoring and Analysis Utilities
Real-time log analysis and monitoring for all services
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import streamlit as st

class LogAnalyzer:
    """Analyze and monitor DataGuardian Pro logs"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
    
    def get_recent_logs(self, category: str = None, hours: int = 24, level: str = None) -> List[Dict[str, Any]]:
        """Get recent log entries with filtering"""
        entries = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Determine which log files to read
        if category:
            log_files = [self.logs_dir / f"dataguardian_{category}.log"]
        else:
            log_files = list(self.logs_dir.glob("dataguardian_*.log"))
        
        for log_file in log_files:
            if log_file.exists():
                entries.extend(self._parse_log_file(log_file, cutoff_time, level))
        
        # Sort by timestamp descending
        entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return entries
    
    def _parse_log_file(self, log_file: Path, cutoff_time: datetime, level_filter: str = None) -> List[Dict[str, Any]]:
        """Parse a single log file"""
        entries = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        
                        # Parse timestamp
                        timestamp_str = entry.get('timestamp', '')
                        if timestamp_str:
                            log_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            if log_time.replace(tzinfo=None) < cutoff_time:
                                continue
                        
                        # Filter by level if specified
                        if level_filter and entry.get('level', '').upper() != level_filter.upper():
                            continue
                        
                        entries.append(entry)
                        
                    except json.JSONDecodeError:
                        # Handle non-JSON log lines (legacy format)
                        continue
                        
        except Exception as e:
            st.error(f"Error reading log file {log_file}: {e}")
        
        return entries
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of errors in the specified time period"""
        error_logs = self.get_recent_logs(hours=hours, level='ERROR')
        critical_logs = self.get_recent_logs(hours=hours, level='CRITICAL')
        
        all_errors = error_logs + critical_logs
        
        # Categorize errors
        error_categories = defaultdict(list)
        scanner_errors = defaultdict(int)
        module_errors = Counter()
        
        for error in all_errors:
            category = error.get('category', 'unknown')
            error_categories[category].append(error)
            
            if error.get('scanner_type'):
                scanner_errors[error['scanner_type']] += 1
            
            module_errors[error.get('module', 'unknown')] += 1
        
        return {
            'total_errors': len(all_errors),
            'error_categories': dict(error_categories),
            'scanner_errors': dict(scanner_errors),
            'module_errors': dict(module_errors),
            'recent_errors': all_errors[:10]  # Last 10 errors
        }
    
    def get_scanner_performance(self, hours: int = 24) -> Dict[str, Any]:
        """Get scanner performance metrics"""
        scanner_logs = self.get_recent_logs(category='scanner', hours=hours)
        
        performance_data = defaultdict(lambda: {
            'total_scans': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'avg_execution_time': 0,
            'total_execution_time': 0,
            'total_findings': 0
        })
        
        for log in scanner_logs:
            scanner_type = log.get('scanner_type')
            if not scanner_type:
                continue
            
            data = performance_data[scanner_type]
            
            if 'Scan completed' in log.get('message', ''):
                data['successful_scans'] += 1
                data['total_scans'] += 1
                
                exec_time = log.get('execution_time', 0)
                data['total_execution_time'] += exec_time
                
                results_count = log.get('results_count', 0)
                data['total_findings'] += results_count
                
            elif 'Scan failed' in log.get('message', ''):
                data['failed_scans'] += 1
                data['total_scans'] += 1
        
        # Calculate averages
        for scanner, data in performance_data.items():
            if data['successful_scans'] > 0:
                data['avg_execution_time'] = data['total_execution_time'] / data['successful_scans']
                data['success_rate'] = (data['successful_scans'] / data['total_scans']) * 100
            else:
                data['success_rate'] = 0
        
        return dict(performance_data)
    
    def get_security_events(self, hours: int = 24) -> Dict[str, Any]:
        """Get security-related events"""
        security_logs = self.get_recent_logs(category='security', hours=hours)
        
        login_attempts = {'successful': 0, 'failed': 0}
        unauthorized_attempts = []
        
        for log in security_logs:
            if log.get('login_success'):
                login_attempts['successful'] += 1
            elif log.get('login_failure'):
                login_attempts['failed'] += 1
            elif log.get('unauthorized_access'):
                unauthorized_attempts.append(log)
        
        return {
            'login_attempts': login_attempts,
            'unauthorized_attempts': unauthorized_attempts,
            'total_security_events': len(security_logs)
        }
    
    def search_logs(self, query: str, category: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Search logs for specific content"""
        logs = self.get_recent_logs(category=category, hours=hours)
        
        matching_logs = []
        query_lower = query.lower()
        
        for log in logs:
            # Search in message
            if query_lower in log.get('message', '').lower():
                matching_logs.append(log)
                continue
            
            # Search in other fields
            for key, value in log.items():
                if isinstance(value, str) and query_lower in value.lower():
                    matching_logs.append(log)
                    break
        
        return matching_logs

class LogDashboard:
    """Streamlit dashboard for log monitoring"""
    
    def __init__(self):
        self.analyzer = LogAnalyzer()
    
    def show_dashboard(self):
        """Display log monitoring dashboard"""
        st.header("📊 DataGuardian Pro - Log Monitoring Dashboard")
        
        # Time range selector
        col1, col2 = st.columns(2)
        with col1:
            hours = st.selectbox("Time Range", [1, 6, 12, 24, 48, 168], index=3, format_func=lambda x: f"Last {x} hours")
        with col2:
            auto_refresh = st.checkbox("Auto Refresh (30s)", value=False)
        
        if auto_refresh:
            st.rerun()
        
        # Refresh button
        if st.button("🔄 Refresh Now"):
            st.rerun()
        
        # Error Summary
        st.subheader("🚨 Error Summary")
        error_summary = self.analyzer.get_error_summary(hours)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Errors", error_summary['total_errors'])
        with col2:
            st.metric("Scanner Errors", sum(error_summary['scanner_errors'].values()))
        with col3:
            st.metric("Critical Issues", len([e for e in error_summary['recent_errors'] if e.get('level') == 'CRITICAL']))
        
        if error_summary['recent_errors']:
            with st.expander("Recent Errors", expanded=True):
                for error in error_summary['recent_errors'][:5]:
                    timestamp = error.get('timestamp', 'Unknown')
                    level = error.get('level', 'Unknown')
                    message = error.get('message', 'No message')
                    module = error.get('module', 'Unknown')
                    
                    st.error(f"**{timestamp}** [{level}] {module}: {message}")
        
        # Scanner Performance
        st.subheader("🔍 Scanner Performance")
        scanner_perf = self.analyzer.get_scanner_performance(hours)
        
        if scanner_perf:
            perf_data = []
            for scanner, data in scanner_perf.items():
                perf_data.append({
                    'Scanner': scanner,
                    'Total Scans': data['total_scans'],
                    'Success Rate': f"{data['success_rate']:.1f}%",
                    'Avg Time': f"{data['avg_execution_time']:.2f}s",
                    'Total Findings': data['total_findings']
                })
            
            st.dataframe(perf_data, width="stretch")
        else:
            st.info("No scanner performance data available for the selected time range.")
        
        # Security Events
        st.subheader("🛡️ Security Events")
        security_events = self.analyzer.get_security_events(hours)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Successful Logins", security_events['login_attempts']['successful'])
        with col2:
            st.metric("Failed Logins", security_events['login_attempts']['failed'])
        with col3:
            st.metric("Unauthorized Attempts", len(security_events['unauthorized_attempts']))
        
        # Log Search
        st.subheader("🔍 Log Search")
        col1, col2 = st.columns(2)
        with col1:
            search_query = st.text_input("Search Query", placeholder="Enter search term...")
        with col2:
            search_category = st.selectbox("Category", ["All", "scanner", "license", "security", "performance"])
        
        if search_query:
            category = None if search_category == "All" else search_category
            search_results = self.analyzer.search_logs(search_query, category, hours)
            
            st.write(f"Found {len(search_results)} matching log entries:")
            
            for result in search_results[:20]:  # Limit to 20 results
                timestamp = result.get('timestamp', 'Unknown')
                level = result.get('level', 'INFO')
                message = result.get('message', 'No message')
                
                if level == 'ERROR':
                    st.error(f"**{timestamp}**: {message}")
                elif level == 'WARNING':
                    st.warning(f"**{timestamp}**: {message}")
                else:
                    st.info(f"**{timestamp}**: {message}")

def show_log_dashboard():
    """Show the log monitoring dashboard"""
    dashboard = LogDashboard()
    dashboard.show_dashboard()

if __name__ == "__main__":
    # CLI usage
    analyzer = LogAnalyzer()
    
    print("=== DataGuardian Pro Log Summary ===")
    
    # Error summary
    error_summary = analyzer.get_error_summary()
    print(f"Total Errors (24h): {error_summary['total_errors']}")
    
    # Scanner performance
    scanner_perf = analyzer.get_scanner_performance()
    print(f"Scanner Types Active: {len(scanner_perf)}")
    
    # Security events
    security_events = analyzer.get_security_events()
    print(f"Login Attempts: {security_events['login_attempts']['successful']} successful, {security_events['login_attempts']['failed']} failed")