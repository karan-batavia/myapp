"""
DataGuardian Pro Streaming File Processor
Bounded memory file processing for large audio/video files.
Prevents OOM by streaming chunks instead of loading entire files into RAM.
"""

import logging
import os
import tempfile
import hashlib
from typing import Generator, Tuple, Optional, Callable, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FileChunk:
    """Represents a chunk of file data."""
    data: bytes
    offset: int
    size: int
    is_last: bool

class StreamingFileProcessor:
    """
    Process large files in bounded memory chunks.
    Prevents OOM errors when processing large audio/video files.
    """
    
    DEFAULT_CHUNK_SIZE = 10 * 1024 * 1024
    MAX_MEMORY_LIMIT = 100 * 1024 * 1024
    
    def __init__(self, chunk_size: int = None, max_memory: int = None):
        self.chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self.max_memory = max_memory or self.MAX_MEMORY_LIMIT
    
    def stream_file(self, file_path: str) -> Generator[FileChunk, None, None]:
        """
        Stream a file in chunks.
        
        Args:
            file_path: Path to the file
            
        Yields:
            FileChunk objects with bounded memory usage
        """
        file_size = os.path.getsize(file_path)
        offset = 0
        
        with open(file_path, 'rb') as f:
            while True:
                chunk_data = f.read(self.chunk_size)
                if not chunk_data:
                    break
                
                chunk_size = len(chunk_data)
                is_last = (offset + chunk_size) >= file_size
                
                yield FileChunk(
                    data=chunk_data,
                    offset=offset,
                    size=chunk_size,
                    is_last=is_last
                )
                
                offset += chunk_size
    
    def calculate_hash_streaming(self, file_path: str, algorithm: str = 'sha256') -> str:
        """Calculate file hash using streaming to avoid memory issues."""
        hasher = hashlib.new(algorithm)
        
        for chunk in self.stream_file(file_path):
            hasher.update(chunk.data)
        
        return hasher.hexdigest()
    
    def process_with_callback(
        self, 
        file_path: str, 
        processor: Callable[[FileChunk], Any],
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> list:
        """
        Process file chunks with a callback function.
        
        Args:
            file_path: Path to the file
            processor: Function to process each chunk
            progress_callback: Optional (progress_percent, message) callback
            
        Returns:
            List of results from processor
        """
        file_size = os.path.getsize(file_path)
        results = []
        processed = 0
        
        for chunk in self.stream_file(file_path):
            try:
                result = processor(chunk)
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.error(f"Chunk processing error at offset {chunk.offset}: {e}")
            
            processed += chunk.size
            
            if progress_callback:
                progress = int((processed / file_size) * 100)
                progress_callback(progress, f"Processed {processed}/{file_size} bytes")
        
        return results
    
    def extract_sample(
        self, 
        file_path: str, 
        sample_size: int = None,
        sample_positions: list = None
    ) -> bytes:
        """
        Extract representative samples from file for analysis.
        More memory-efficient than loading entire file.
        
        Args:
            file_path: Path to the file
            sample_size: Size of each sample (default: 1MB)
            sample_positions: List of positions to sample from (default: start, middle, end)
            
        Returns:
            Concatenated sample bytes
        """
        sample_size = sample_size or (1 * 1024 * 1024)
        file_size = os.path.getsize(file_path)
        
        if file_size <= sample_size * 3:
            with open(file_path, 'rb') as f:
                return f.read()
        
        if sample_positions is None:
            sample_positions = [
                0,
                (file_size // 2) - (sample_size // 2),
                max(0, file_size - sample_size)
            ]
        
        samples = []
        with open(file_path, 'rb') as f:
            for pos in sample_positions:
                f.seek(pos)
                samples.append(f.read(sample_size))
        
        return b''.join(samples)
    
    def get_file_info(self, file_path: str) -> dict:
        """Get file information without loading into memory."""
        stat = os.stat(file_path)
        return {
            'path': file_path,
            'size': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'modified': stat.st_mtime,
            'is_large': stat.st_size > self.max_memory
        }


class BoundedMediaAnalyzer:
    """
    Memory-bounded media file analyzer.
    Analyzes audio/video files without loading entirely into RAM.
    """
    
    VIDEO_SAMPLE_FRAMES = 30
    AUDIO_SAMPLE_SECONDS = 10
    
    def __init__(self, max_memory_mb: int = 100):
        self.max_memory = max_memory_mb * 1024 * 1024
        self.processor = StreamingFileProcessor(max_memory=self.max_memory)
    
    def analyze_video_bounded(
        self, 
        file_path: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> dict:
        """
        Analyze video file with bounded memory usage.
        Samples frames instead of loading entire video.
        """
        try:
            import cv2
        except ImportError:
            return {'error': 'OpenCV not available', 'frames_analyzed': 0}
        
        results = {
            'frames_analyzed': 0,
            'frame_samples': [],
            'consistency_issues': [],
            'face_detections': []
        }
        
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return {'error': 'Could not open video file'}
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            results['total_frames'] = total_frames
            results['fps'] = fps
            results['duration_seconds'] = duration
            
            if total_frames <= self.VIDEO_SAMPLE_FRAMES:
                sample_indices = range(total_frames)
            else:
                step = total_frames // self.VIDEO_SAMPLE_FRAMES
                sample_indices = [i * step for i in range(self.VIDEO_SAMPLE_FRAMES)]
            
            prev_frame = None
            for i, frame_idx in enumerate(sample_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                frame_info = {
                    'index': frame_idx,
                    'shape': frame.shape,
                    'mean_intensity': float(frame.mean())
                }
                
                if prev_frame is not None:
                    diff = cv2.absdiff(frame, prev_frame)
                    frame_info['diff_from_prev'] = float(diff.mean())
                    
                    if frame_info['diff_from_prev'] > 100:
                        results['consistency_issues'].append({
                            'type': 'large_frame_jump',
                            'frame': frame_idx,
                            'diff': frame_info['diff_from_prev']
                        })
                
                results['frame_samples'].append(frame_info)
                results['frames_analyzed'] += 1
                prev_frame = frame.copy()
                
                if progress_callback:
                    progress = int((i / len(sample_indices)) * 100)
                    progress_callback(progress, f"Analyzed frame {i+1}/{len(sample_indices)}")
                
                del frame
            
            cap.release()
            
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"Video analysis error: {e}")
        
        return results
    
    def analyze_audio_bounded(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> dict:
        """
        Analyze audio file with bounded memory usage.
        Samples segments instead of loading entire audio.
        """
        results = {
            'samples_analyzed': 0,
            'spectral_samples': [],
            'anomalies': []
        }
        
        try:
            file_size = os.path.getsize(file_path)
            sample_data = self.processor.extract_sample(file_path)
            
            results['file_size'] = file_size
            results['sample_size'] = len(sample_data)
            results['samples_analyzed'] = 3
            
            if progress_callback:
                progress_callback(50, "Analyzing audio samples...")
            
            try:
                import numpy as np
                samples = np.frombuffer(sample_data[:min(len(sample_data), 44100*4)], dtype=np.int16)
                if len(samples) > 0:
                    results['peak_amplitude'] = float(np.max(np.abs(samples)))
                    results['mean_amplitude'] = float(np.mean(np.abs(samples)))
                    results['std_amplitude'] = float(np.std(samples))
            except Exception as e:
                logger.debug(f"Numpy analysis failed: {e}")
            
            if progress_callback:
                progress_callback(100, "Audio analysis complete")
                
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"Audio analysis error: {e}")
        
        return results


_streaming_processor = None

def get_streaming_processor(chunk_size: int = None) -> StreamingFileProcessor:
    """Get singleton streaming file processor."""
    global _streaming_processor
    if _streaming_processor is None:
        _streaming_processor = StreamingFileProcessor(chunk_size=chunk_size)
    return _streaming_processor


def get_bounded_analyzer(max_memory_mb: int = 100) -> BoundedMediaAnalyzer:
    """Get bounded media analyzer instance."""
    return BoundedMediaAnalyzer(max_memory_mb=max_memory_mb)
