"""
DataGuardian Pro Scanner Job Queue
Async job queue for scanner execution using Redis for scalability.
Enables background processing with progress tracking and bounded memory usage.
"""

import json
import logging
import os
import time
import uuid
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import queue

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Scanner job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ScannerJob:
    """Represents a scanner job in the queue."""
    job_id: str
    scanner_type: str
    user_id: str
    tenant_id: Optional[str]
    input_data: Dict[str, Any]
    status: JobStatus
    progress: int
    progress_message: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    priority: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScannerJob':
        """Create from dictionary."""
        data['status'] = JobStatus(data['status'])
        return cls(**data)


class ScannerQueue:
    """
    Redis-backed scanner job queue for async processing.
    Provides progress tracking, job prioritization, and bounded execution.
    """
    
    QUEUE_KEY = "dataguardian:scanner:queue"
    JOBS_KEY = "dataguardian:scanner:jobs"
    PROGRESS_KEY = "dataguardian:scanner:progress"
    RESULTS_KEY = "dataguardian:scanner:results"
    
    JOB_TIMEOUT_SECONDS = 480
    MAX_CONCURRENT_JOBS = 8
    RESULT_TTL_SECONDS = 3600
    
    def __init__(self):
        self.redis_client = None
        self._local_queue = queue.PriorityQueue()
        self._local_jobs: Dict[str, ScannerJob] = {}
        self._workers: List[threading.Thread] = []
        self._shutdown = False
        self._scanner_registry: Dict[str, Callable] = {}
        self._connect_redis()
    
    def _connect_redis(self):
        """Connect to Redis for distributed queue."""
        try:
            import redis
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.redis_client.ping()
            logger.info("Scanner queue connected to Redis")
        except Exception as e:
            logger.warning(f"Redis unavailable for scanner queue, using local queue: {e}")
            self.redis_client = None
    
    def register_scanner(self, scanner_type: str, scanner_func: Callable):
        """Register a scanner function for a scanner type."""
        self._scanner_registry[scanner_type] = scanner_func
        logger.debug(f"Registered scanner: {scanner_type}")
    
    def enqueue(
        self,
        scanner_type: str,
        user_id: str,
        input_data: Dict[str, Any],
        tenant_id: Optional[str] = None,
        priority: int = 5
    ) -> str:
        """
        Add a scanner job to the queue.
        
        Args:
            scanner_type: Type of scanner to run
            user_id: User requesting the scan
            input_data: Input data for the scanner
            tenant_id: Optional tenant ID for multi-tenant
            priority: Job priority (1=highest, 10=lowest)
        
        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        
        job = ScannerJob(
            job_id=job_id,
            scanner_type=scanner_type,
            user_id=user_id,
            tenant_id=tenant_id,
            input_data=input_data,
            status=JobStatus.PENDING,
            progress=0,
            progress_message="Queued",
            result=None,
            error=None,
            created_at=datetime.utcnow().isoformat(),
            started_at=None,
            completed_at=None,
            priority=priority
        )
        
        if self.redis_client:
            self._redis_enqueue(job)
        else:
            self._local_enqueue(job)
        
        logger.info(f"Enqueued scanner job {job_id} for {scanner_type}")
        return job_id
    
    def _redis_enqueue(self, job: ScannerJob):
        """Enqueue job in Redis."""
        try:
            job_data = json.dumps(job.to_dict())
            pipe = self.redis_client.pipeline()
            pipe.hset(self.JOBS_KEY, job.job_id, job_data)
            pipe.zadd(self.QUEUE_KEY, {job.job_id: job.priority})
            pipe.execute()
        except Exception as e:
            logger.error(f"Redis enqueue failed: {e}")
            self._local_enqueue(job)
    
    def _local_enqueue(self, job: ScannerJob):
        """Enqueue job in local queue."""
        self._local_jobs[job.job_id] = job
        self._local_queue.put((job.priority, job.created_at, job.job_id))
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status and progress."""
        if self.redis_client:
            try:
                job_data = self.redis_client.hget(self.JOBS_KEY, job_id)
                if job_data:
                    return json.loads(job_data)
            except Exception as e:
                logger.error(f"Redis get_job_status failed: {e}")
        
        if job_id in self._local_jobs:
            return self._local_jobs[job_id].to_dict()
        
        return None
    
    def update_progress(self, job_id: str, progress: int, message: str = ""):
        """Update job progress (0-100)."""
        if self.redis_client:
            try:
                job_data = self.redis_client.hget(self.JOBS_KEY, job_id)
                if job_data:
                    job = json.loads(job_data)
                    job['progress'] = min(100, max(0, progress))
                    job['progress_message'] = message
                    self.redis_client.hset(self.JOBS_KEY, job_id, json.dumps(job))
                    return
            except Exception as e:
                logger.error(f"Redis update_progress failed: {e}")
        
        if job_id in self._local_jobs:
            self._local_jobs[job_id].progress = min(100, max(0, progress))
            self._local_jobs[job_id].progress_message = message
    
    def complete_job(self, job_id: str, result: Dict[str, Any]):
        """Mark job as completed with result."""
        completed_at = datetime.utcnow().isoformat()
        
        if self.redis_client:
            try:
                job_data = self.redis_client.hget(self.JOBS_KEY, job_id)
                if job_data:
                    job = json.loads(job_data)
                    job['status'] = JobStatus.COMPLETED.value
                    job['progress'] = 100
                    job['progress_message'] = "Completed"
                    job['result'] = result
                    job['completed_at'] = completed_at
                    
                    pipe = self.redis_client.pipeline()
                    pipe.hset(self.JOBS_KEY, job_id, json.dumps(job))
                    pipe.setex(f"{self.RESULTS_KEY}:{job_id}", self.RESULT_TTL_SECONDS, json.dumps(result))
                    pipe.zrem(self.QUEUE_KEY, job_id)
                    pipe.execute()
                    return
            except Exception as e:
                logger.error(f"Redis complete_job failed: {e}")
        
        if job_id in self._local_jobs:
            job = self._local_jobs[job_id]
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.progress_message = "Completed"
            job.result = result
            job.completed_at = completed_at
    
    def fail_job(self, job_id: str, error: str):
        """Mark job as failed with error."""
        completed_at = datetime.utcnow().isoformat()
        
        if self.redis_client:
            try:
                job_data = self.redis_client.hget(self.JOBS_KEY, job_id)
                if job_data:
                    job = json.loads(job_data)
                    job['status'] = JobStatus.FAILED.value
                    job['progress_message'] = "Failed"
                    job['error'] = error
                    job['completed_at'] = completed_at
                    
                    pipe = self.redis_client.pipeline()
                    pipe.hset(self.JOBS_KEY, job_id, json.dumps(job))
                    pipe.zrem(self.QUEUE_KEY, job_id)
                    pipe.execute()
                    return
            except Exception as e:
                logger.error(f"Redis fail_job failed: {e}")
        
        if job_id in self._local_jobs:
            job = self._local_jobs[job_id]
            job.status = JobStatus.FAILED
            job.progress_message = "Failed"
            job.error = error
            job.completed_at = completed_at
    
    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job result if completed."""
        if self.redis_client:
            try:
                result = self.redis_client.get(f"{self.RESULTS_KEY}:{job_id}")
                if result:
                    return json.loads(result)
                
                job_data = self.redis_client.hget(self.JOBS_KEY, job_id)
                if job_data:
                    job = json.loads(job_data)
                    if job.get('result'):
                        return job['result']
            except Exception as e:
                logger.error(f"Redis get_result failed: {e}")
        
        if job_id in self._local_jobs:
            return self._local_jobs[job_id].result
        
        return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        stats = {
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'redis_connected': self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                stats['pending'] = self.redis_client.zcard(self.QUEUE_KEY)
                all_jobs = self.redis_client.hgetall(self.JOBS_KEY)
                for job_data in all_jobs.values():
                    job = json.loads(job_data)
                    status = job.get('status', '')
                    if status == 'running':
                        stats['running'] += 1
                    elif status == 'completed':
                        stats['completed'] += 1
                    elif status == 'failed':
                        stats['failed'] += 1
            except Exception as e:
                logger.error(f"Redis get_queue_stats failed: {e}")
        else:
            stats['pending'] = self._local_queue.qsize()
            for job in self._local_jobs.values():
                if job.status == JobStatus.RUNNING:
                    stats['running'] += 1
                elif job.status == JobStatus.COMPLETED:
                    stats['completed'] += 1
                elif job.status == JobStatus.FAILED:
                    stats['failed'] += 1
        
        return stats
    
    def process_job_sync(self, job_id: str) -> Dict[str, Any]:
        """
        Process a job synchronously (for immediate execution).
        Used when async processing is not required.
        """
        job_data = self.get_job_status(job_id)
        if not job_data:
            raise ValueError(f"Job {job_id} not found")
        
        scanner_type = job_data['scanner_type']
        input_data = job_data['input_data']
        
        self.update_progress(job_id, 10, "Starting scan...")
        
        if scanner_type in self._scanner_registry:
            try:
                self.update_progress(job_id, 30, "Processing...")
                
                scanner_func = self._scanner_registry[scanner_type]
                result = scanner_func(
                    input_data,
                    progress_callback=lambda p, m: self.update_progress(job_id, 30 + int(p * 0.6), m)
                )
                
                self.update_progress(job_id, 95, "Finalizing...")
                self.complete_job(job_id, result)
                
                return result
                
            except Exception as e:
                logger.error(f"Scanner job {job_id} failed: {e}")
                self.fail_job(job_id, str(e))
                raise
        else:
            error = f"Unknown scanner type: {scanner_type}"
            self.fail_job(job_id, error)
            raise ValueError(error)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed/failed jobs."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        cutoff_iso = cutoff.isoformat()
        
        if self.redis_client:
            try:
                all_jobs = self.redis_client.hgetall(self.JOBS_KEY)
                for job_id, job_data in all_jobs.items():
                    job = json.loads(job_data)
                    if job.get('completed_at') and job['completed_at'] < cutoff_iso:
                        self.redis_client.hdel(self.JOBS_KEY, job_id)
                        self.redis_client.delete(f"{self.RESULTS_KEY}:{job_id}")
            except Exception as e:
                logger.error(f"Redis cleanup failed: {e}")
        else:
            to_remove = []
            for job_id, job in self._local_jobs.items():
                if job.completed_at and job.completed_at < cutoff_iso:
                    to_remove.append(job_id)
            for job_id in to_remove:
                del self._local_jobs[job_id]


_scanner_queue = None

def get_scanner_queue() -> ScannerQueue:
    """Get singleton scanner queue instance."""
    global _scanner_queue
    if _scanner_queue is None:
        _scanner_queue = ScannerQueue()
    return _scanner_queue
