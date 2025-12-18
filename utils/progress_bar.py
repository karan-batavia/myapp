"""
Simple Progress Bar Component

Provides a uniform, reusable progress bar for scanning operations
across the DataGuardian Pro platform.
"""

import streamlit as st
from typing import Optional, Callable
from dataclasses import dataclass
import time


@dataclass
class ProgressState:
    """Tracks progress state for scanning operations"""
    current: int = 0
    total: int = 100
    stage: str = "Initializing"
    current_item: str = ""
    
    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100)
    
    @property
    def fraction(self) -> float:
        if self.total == 0:
            return 0.0
        return min(1.0, self.current / self.total)


class SimpleProgressBar:
    """
    Simple, uniform progress bar for scanning operations.
    
    Usage:
        progress = SimpleProgressBar("Scanning Repository")
        progress.start(total_items=100)
        for i, item in enumerate(items):
            progress.update(i + 1, current_item=item.name)
            # do work
        progress.complete()
    """
    
    def __init__(self, title: str = "Processing", key: str = None):
        self.title = title
        self.key = key or f"progress_{id(self)}"
        self.state = ProgressState()
        self._container = None
        self._progress_bar = None
        self._status_text = None
        self._started = False
    
    def start(self, total: int = 100, stage: str = "Starting") -> None:
        """Initialize the progress bar with total items"""
        self.state = ProgressState(current=0, total=total, stage=stage)
        self._started = True
        
        self._container = st.container()
        with self._container:
            st.markdown(f"**{self.title}**")
            self._progress_bar = st.progress(0.0)
            self._status_text = st.empty()
            self._status_text.caption(f"🔄 {stage}...")
    
    def update(
        self, 
        current: int, 
        stage: Optional[str] = None, 
        current_item: Optional[str] = None
    ) -> None:
        """Update progress bar state"""
        if not self._started:
            return
            
        self.state.current = current
        if stage:
            self.state.stage = stage
        if current_item:
            self.state.current_item = current_item
        
        self._progress_bar.progress(self.state.fraction)
        
        status_parts = [f"🔄 {self.state.stage}"]
        status_parts.append(f"({self.state.current}/{self.state.total})")
        if current_item:
            display_item = current_item[:50] + "..." if len(current_item) > 50 else current_item
            status_parts.append(f"• {display_item}")
        
        self._status_text.caption(" ".join(status_parts))
    
    def complete(self, message: str = "Complete") -> None:
        """Mark progress as complete"""
        if not self._started:
            return
            
        self._progress_bar.progress(1.0)
        self._status_text.caption(f"✅ {message}")
        self._started = False
    
    def error(self, message: str = "Error occurred") -> None:
        """Mark progress as failed"""
        if not self._started:
            return
            
        self._status_text.caption(f"❌ {message}")
        self._started = False


def create_progress_callback(progress_bar: SimpleProgressBar, total: int):
    """
    Create a callback function for scanner integration.
    
    Returns a function that can be passed to scanners as status_callback.
    The callback parses status messages and updates the progress bar.
    """
    current = [0]
    
    def callback(status: str, increment: int = 0, current_file: str = None):
        if increment > 0:
            current[0] += increment
        
        stage = status
        if "Cloning" in status:
            stage = "Cloning repository"
            progress_bar.update(0, stage=stage)
        elif "Reading" in status:
            stage = "Reading files"
            progress_bar.update(0, stage=stage)
        elif "Scanning" in status:
            stage = "Scanning files"
            if current_file:
                progress_bar.update(current[0], stage=stage, current_item=current_file)
            else:
                progress_bar.update(current[0], stage=stage)
        elif "Analyzing" in status:
            stage = "Analyzing results"
            progress_bar.update(int(total * 0.9), stage=stage)
        elif "Calculating" in status:
            stage = "Calculating scores"
            progress_bar.update(int(total * 0.95), stage=stage)
        else:
            progress_bar.update(current[0], stage=status, current_item=current_file)
    
    return callback


class ScanProgressTracker:
    """
    Streamlit-integrated progress tracker for repository scanning.
    
    Provides uniform progress display across all scanner types.
    """
    
    def __init__(self, title: str = "Scanning"):
        self.title = title
        self.progress_bar = None
        self.status_placeholder = None
        self.stats_placeholder = None
        self.total_files = 0
        self.scanned_files = 0
        self.findings_count = 0
    
    def initialize(self, container=None):
        """Set up the progress display elements"""
        target = container or st
        
        with target:
            st.markdown(f"### {self.title}")
            self.progress_bar = st.progress(0.0)
            self.status_placeholder = st.empty()
            self.stats_placeholder = st.empty()
    
    def set_total(self, total: int):
        """Set total number of files to scan"""
        self.total_files = total
        self._update_display()
    
    def update(self, stage: str, current_file: str = None, findings: int = 0):
        """Update the progress display"""
        self.scanned_files += 1
        self.findings_count += findings
        self._update_display(stage, current_file)
    
    def _update_display(self, stage: str = "Initializing", current_file: str = None):
        """Refresh the display elements"""
        if self.total_files > 0:
            progress = min(1.0, self.scanned_files / self.total_files)
            self.progress_bar.progress(progress)
        
        status_text = f"🔄 {stage}"
        if current_file:
            display_file = current_file[:60] + "..." if len(current_file) > 60 else current_file
            status_text += f" • `{display_file}`"
        
        self.status_placeholder.markdown(status_text)
        
        if self.total_files > 0:
            self.stats_placeholder.caption(
                f"Files: {self.scanned_files}/{self.total_files} • "
                f"Findings: {self.findings_count} • "
                f"Progress: {int(progress * 100) if self.total_files > 0 else 0}%"
            )
    
    def complete(self, success: bool = True, message: str = None):
        """Mark scanning as complete"""
        self.progress_bar.progress(1.0)
        
        if success:
            final_msg = message or f"✅ Scan complete! Found {self.findings_count} findings in {self.scanned_files} files."
            self.status_placeholder.success(final_msg)
        else:
            final_msg = message or "❌ Scan failed"
            self.status_placeholder.error(final_msg)
        
        self.stats_placeholder.empty()
