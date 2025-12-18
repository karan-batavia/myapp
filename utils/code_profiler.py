"""
Code Profiler for DataGuardian Pro
Identifies performance bottlenecks and provides optimization recommendations
"""

import time
import functools
import logging

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("code_profiler")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)
import traceback
import sys
import threading
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
import psutil
import os
from collections import defaultdict, deque
import json



class PerformanceProfiler:
    """Performance profiler for identifying bottlenecks"""
    
    def __init__(self):
        self.function_stats = defaultdict(lambda: {
            'call_count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'recent_calls': deque(maxlen=100),
            'errors': 0
        })
        
        self.system_stats = {
            'memory_usage': deque(maxlen=1000),
            'cpu_usage': deque(maxlen=1000),
            'disk_io': deque(maxlen=1000),
            'network_io': deque(maxlen=1000)
        }
        
        self.slow_queries = deque(maxlen=500)
        self.bottlenecks = []
        self.recommendations = []
        
        self.profiling_enabled = True
        self.slow_threshold = 1.0  # seconds
        self.memory_threshold = 80  # percent
        self.cpu_threshold = 80  # percent
        
        # Start system monitoring
        self.start_system_monitoring()
    
    def track_activity(self, session_id: str, activity: str, data: dict = None):
        """Track user activity"""
        try:
            # Basic activity tracking
            logger.info(f"Activity tracked: {session_id} - {activity}")
        except Exception as e:
            logger.error(f"Error tracking activity: {e}")
    
    def start_system_monitoring(self):
        """Start background system monitoring"""
        def monitor_system():
            while self.profiling_enabled:
                try:
                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.system_stats['memory_usage'].append({
                        'timestamp': datetime.now().isoformat(),
                        'percent': memory.percent,
                        'available_mb': memory.available / 1024 / 1024,
                        'used_mb': memory.used / 1024 / 1024
                    })
                    
                    # CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.system_stats['cpu_usage'].append({
                        'timestamp': datetime.now().isoformat(),
                        'percent': cpu_percent,
                        'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                    })
                    
                    # Disk I/O
                    disk_io = psutil.disk_io_counters()
                    if disk_io:
                        self.system_stats['disk_io'].append({
                            'timestamp': datetime.now().isoformat(),
                            'read_mb': disk_io.read_bytes / 1024 / 1024,
                            'write_mb': disk_io.write_bytes / 1024 / 1024,
                            'read_count': disk_io.read_count,
                            'write_count': disk_io.write_count
                        })
                    
                    # Network I/O
                    net_io = psutil.net_io_counters()
                    if net_io:
                        self.system_stats['network_io'].append({
                            'timestamp': datetime.now().isoformat(),
                            'sent_mb': net_io.bytes_sent / 1024 / 1024,
                            'recv_mb': net_io.bytes_recv / 1024 / 1024,
                            'packets_sent': net_io.packets_sent,
                            'packets_recv': net_io.packets_recv
                        })
                    
                    # Check for performance issues
                    self._check_performance_issues()
                    
                    time.sleep(5)  # Monitor every 5 seconds
                    
                except Exception as e:
                    logger.error(f"System monitoring error: {e}")
                    time.sleep(10)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
        logger.info("System monitoring started")
    
    def profile_function(self, func_name: str = None):
        """Decorator to profile function performance"""
        def decorator(func: Callable) -> Callable:
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.profiling_enabled:
                    return func(*args, **kwargs)
                
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                
                # Get stats reference early so it's available in exception handler
                stats = self.function_stats[name]
                
                try:
                    result = func(*args, **kwargs)
                    
                    execution_time = time.time() - start_time
                    memory_used = psutil.Process().memory_info().rss - start_memory
                    
                    # Update statistics
                    stats['call_count'] += 1
                    stats['total_time'] += execution_time
                    stats['avg_time'] = stats['total_time'] / stats['call_count']
                    stats['min_time'] = min(stats['min_time'], execution_time)
                    stats['max_time'] = max(stats['max_time'], execution_time)
                    
                    # Store recent call data
                    stats['recent_calls'].append({
                        'timestamp': datetime.now().isoformat(),
                        'execution_time': execution_time,
                        'memory_used': memory_used,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    })
                    
                    # Check for slow execution
                    if execution_time > self.slow_threshold:
                        self._record_slow_function(name, execution_time, args, kwargs)
                    
                    return result
                    
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"Error in profiled function {name}: {e}")
                    raise
            
            return wrapper
        return decorator
    
    def profile_database_query(self, query: str, params: tuple = None):
        """Profile database query performance"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.profiling_enabled:
                    return func(*args, **kwargs)
                
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Record query performance
                    if execution_time > 0.5:  # Slow query threshold
                        self.slow_queries.append({
                            'timestamp': datetime.now().isoformat(),
                            'query': query[:200] + '...' if len(query) > 200 else query,
                            'execution_time': execution_time,
                            'params': str(params) if params else None,
                            'function': func.__name__
                        })
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Database query error: {e}")
                    raise
            
            return wrapper
        return decorator
    
    def _record_slow_function(self, name: str, execution_time: float, args: tuple, kwargs: dict):
        """Record slow function execution"""
        slow_record = {
            'timestamp': datetime.now().isoformat(),
            'function': name,
            'execution_time': execution_time,
            'args_count': len(args),
            'kwargs_count': len(kwargs),
            'stack_trace': traceback.format_stack()[-5:]  # Last 5 stack frames
        }
        
        # Add to bottlenecks if not already present
        if not any(b['function'] == name for b in self.bottlenecks):
            self.bottlenecks.append({
                'function': name,
                'avg_time': execution_time,
                'occurrences': 1,
                'first_seen': datetime.now().isoformat()
            })
        else:
            # Update existing bottleneck
            for bottleneck in self.bottlenecks:
                if bottleneck['function'] == name:
                    bottleneck['occurrences'] += 1
                    bottleneck['avg_time'] = (bottleneck['avg_time'] + execution_time) / 2
                    break
    
    def _check_performance_issues(self):
        """Check for performance issues and generate recommendations"""
        if not self.system_stats['memory_usage'] or not self.system_stats['cpu_usage']:
            return
        
        # Check memory usage
        latest_memory = self.system_stats['memory_usage'][-1]
        if latest_memory['percent'] > self.memory_threshold:
            self._add_recommendation(
                'high_memory',
                f"High memory usage: {latest_memory['percent']:.1f}%",
                "Consider implementing caching or optimizing data structures"
            )
        
        # Check CPU usage
        latest_cpu = self.system_stats['cpu_usage'][-1]
        if latest_cpu['percent'] > self.cpu_threshold:
            self._add_recommendation(
                'high_cpu',
                f"High CPU usage: {latest_cpu['percent']:.1f}%",
                "Consider optimizing algorithms or adding async processing"
            )
        
        # Check for frequent slow functions
        slow_functions = [name for name, stats in self.function_stats.items() 
                         if stats['avg_time'] > self.slow_threshold and stats['call_count'] > 10]
        
        for func_name in slow_functions:
            self._add_recommendation(
                'slow_function',
                f"Slow function: {func_name}",
                f"Average execution time: {self.function_stats[func_name]['avg_time']:.2f}s"
            )
    
    def _add_recommendation(self, category: str, issue: str, suggestion: str):
        """Add performance recommendation"""
        recommendation = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'issue': issue,
            'suggestion': suggestion
        }
        
        # Avoid duplicate recommendations
        if not any(r['category'] == category and r['issue'] == issue for r in self.recommendations):
            self.recommendations.append(recommendation)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        # Calculate top slow functions
        slow_functions = sorted(
            [(name, stats) for name, stats in self.function_stats.items()],
            key=lambda x: x[1]['avg_time'],
            reverse=True
        )[:10]
        
        # Memory usage trends
        memory_trend = 'stable'
        if len(self.system_stats['memory_usage']) > 10:
            recent_memory = [m['percent'] for m in list(self.system_stats['memory_usage'])[-10:]]
            if recent_memory[-1] > recent_memory[0] * 1.2:
                memory_trend = 'increasing'
            elif recent_memory[-1] < recent_memory[0] * 0.8:
                memory_trend = 'decreasing'
        
        # CPU usage trends
        cpu_trend = 'stable'
        if len(self.system_stats['cpu_usage']) > 10:
            recent_cpu = [c['percent'] for c in list(self.system_stats['cpu_usage'])[-10:]]
            if recent_cpu[-1] > recent_cpu[0] * 1.2:
                cpu_trend = 'increasing'
            elif recent_cpu[-1] < recent_cpu[0] * 0.8:
                cpu_trend = 'decreasing'
        
        return {
            'summary': {
                'total_functions_profiled': len(self.function_stats),
                'total_function_calls': sum(stats['call_count'] for stats in self.function_stats.values()),
                'slow_queries_count': len(self.slow_queries),
                'bottlenecks_count': len(self.bottlenecks),
                'recommendations_count': len(self.recommendations)
            },
            'system_performance': {
                'memory_trend': memory_trend,
                'cpu_trend': cpu_trend,
                'current_memory_percent': self.system_stats['memory_usage'][-1]['percent'] if self.system_stats['memory_usage'] else 0,
                'current_cpu_percent': self.system_stats['cpu_usage'][-1]['percent'] if self.system_stats['cpu_usage'] else 0
            },
            'top_slow_functions': [
                {
                    'name': name,
                    'avg_time': stats['avg_time'],
                    'call_count': stats['call_count'],
                    'total_time': stats['total_time'],
                    'max_time': stats['max_time']
                }
                for name, stats in slow_functions
            ],
            'slow_queries': list(self.slow_queries)[-10:],  # Last 10 slow queries
            'bottlenecks': self.bottlenecks,
            'recommendations': self.recommendations[-10:],  # Last 10 recommendations
            'detailed_stats': {
                name: {
                    'call_count': stats['call_count'],
                    'avg_time': stats['avg_time'],
                    'total_time': stats['total_time'],
                    'min_time': stats['min_time'] if stats['min_time'] != float('inf') else 0,
                    'max_time': stats['max_time'],
                    'errors': stats['errors']
                }
                for name, stats in self.function_stats.items()
            }
        }
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get specific optimization suggestions"""
        suggestions = []
        
        # Analyze function performance
        for name, stats in self.function_stats.items():
            if stats['avg_time'] > 2.0 and stats['call_count'] > 5:
                suggestions.append({
                    'type': 'function_optimization',
                    'priority': 'high',
                    'function': name,
                    'issue': f"Function takes {stats['avg_time']:.2f}s on average",
                    'suggestion': "Consider caching results, optimizing algorithms, or implementing async processing"
                })
        
        # Analyze memory usage
        if self.system_stats['memory_usage']:
            avg_memory = sum(m['percent'] for m in self.system_stats['memory_usage']) / len(self.system_stats['memory_usage'])
            if avg_memory > 70:
                suggestions.append({
                    'type': 'memory_optimization',
                    'priority': 'medium',
                    'issue': f"Average memory usage: {avg_memory:.1f}%",
                    'suggestion': "Implement object pooling, optimize data structures, or add garbage collection"
                })
        
        # Analyze database queries
        if len(self.slow_queries) > 10:
            suggestions.append({
                'type': 'database_optimization',
                'priority': 'high',
                'issue': f"{len(self.slow_queries)} slow queries detected",
                'suggestion': "Add database indexes, optimize queries, or implement query caching"
            })
        
        return suggestions
    
    def export_profile_data(self, filename: str):
        """Export profiling data to JSON file"""
        try:
            profile_data = {
                'timestamp': datetime.now().isoformat(),
                'performance_report': self.get_performance_report(),
                'optimization_suggestions': self.get_optimization_suggestions()
            }
            
            with open(filename, 'w') as f:
                json.dump(profile_data, f, indent=2, default=str)
            
            logger.info(f"Profile data exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting profile data: {e}")
    
    def reset_stats(self):
        """Reset all profiling statistics"""
        self.function_stats.clear()
        self.slow_queries.clear()
        self.bottlenecks.clear()
        self.recommendations.clear()
        
        for stat_list in self.system_stats.values():
            stat_list.clear()
        
        logger.info("Profiling statistics reset")
    
    def disable_profiling(self):
        """Disable profiling"""
        self.profiling_enabled = False
        logger.info("Profiling disabled")
    
    def enable_profiling(self):
        """Enable profiling"""
        self.profiling_enabled = True
        logger.info("Profiling enabled")

# Global profiler instance
profiler = PerformanceProfiler()

def get_profiler():
    """Get the global profiler instance"""
    return profiler

def profile_function(func_name: str = None):
    """Decorator to profile function performance"""
    return profiler.profile_function(func_name)

def profile_database_query(query: str, params: tuple = None):
    """Decorator to profile database query performance"""
    return profiler.profile_database_query(query, params)

# Performance monitoring context manager
class PerformanceMonitor:
    """Context manager for monitoring code blocks"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.start_memory = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        memory_used = psutil.Process().memory_info().rss - self.start_memory
        
        logger.info(f"Performance Monitor [{self.name}]: {execution_time:.3f}s, Memory: {memory_used/1024/1024:.1f}MB")
        
        if execution_time > 1.0:
            profiler._record_slow_function(self.name, execution_time, (), {})

def monitor_performance(name: str):
    """Context manager for performance monitoring"""
    return PerformanceMonitor(name)