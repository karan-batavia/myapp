#!/usr/bin/env python3
"""
DataGuardian Pro - Standalone Scanner Worker
Connects to Redis queue and processes scanner jobs independently.
Run this on your VM alongside the main app, or on separate VMs for scaling.
"""

import os
import sys
import time
import json
import signal
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scanner_worker')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import redis
except ImportError:
    logger.error("Redis not installed. Run: pip install redis")
    sys.exit(1)


class ScannerWorker:
    """
    Standalone worker that pulls jobs from Redis queue and executes scanners.
    Can run on same VM or separate VMs for horizontal scaling.
    """
    
    QUEUE_KEY = "dataguardian:scanner:queue"
    JOBS_KEY = "dataguardian:scanner:jobs"
    PROGRESS_KEY = "dataguardian:scanner:progress"
    RESULTS_KEY = "dataguardian:scanner:results"
    
    def __init__(self, worker_id: str = None, redis_url: str = None):
        self.worker_id = worker_id or f"worker-{os.getpid()}"
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client = None
        self.running = False
        self.current_job = None
        
        self._connect_redis()
        
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _connect_redis(self):
        """Connect to Redis server."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=30
            )
            self.redis_client.ping()
            logger.info(f"Worker {self.worker_id} connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _handle_shutdown(self, signum, frame):
        """Graceful shutdown handler."""
        logger.info(f"Worker {self.worker_id} received shutdown signal")
        self.running = False
        
        if self.current_job:
            logger.info(f"Marking current job {self.current_job} as failed due to shutdown")
            self._update_job_status(self.current_job, 'failed', error='Worker shutdown')
    
    def _update_job_status(self, job_id: str, status: str, progress: int = None, 
                          result: dict = None, error: str = None):
        """Update job status in Redis."""
        try:
            job_data = self.redis_client.hget(self.JOBS_KEY, job_id)
            if job_data:
                job = json.loads(job_data)
                job['status'] = status
                if progress is not None:
                    job['progress'] = progress
                if result is not None:
                    job['result'] = result
                if error is not None:
                    job['error'] = error
                if status == 'completed' or status == 'failed':
                    job['completed_at'] = datetime.now().isoformat()
                
                self.redis_client.hset(self.JOBS_KEY, job_id, json.dumps(job))
                
                if result:
                    self.redis_client.setex(
                        f"{self.RESULTS_KEY}:{job_id}",
                        3600,
                        json.dumps(result)
                    )
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
    
    def _get_scanner(self, scanner_type: str):
        """Get scanner instance by type."""
        scanners = {
            'code': ('services.code_scanner', 'CodeScanner'),
            'blob': ('services.intelligent_blob_scanner', 'IntelligentBlobScanner'),
            'image': ('services.intelligent_image_scanner', 'IntelligentImageScanner'),
            'website': ('services.intelligent_website_scanner', 'IntelligentWebsiteScanner'),
            'database': ('services.intelligent_db_scanner', 'IntelligentDBScanner'),
            'audio_video': ('services.audio_video_scanner', 'AudioVideoScanner'),
            'ai_model': ('services.ai_model_scanner', 'AIModelScanner'),
            'soc2': ('services.enhanced_soc2_scanner', 'EnhancedSOC2Scanner'),
            'dpia': ('services.dpia_scanner', 'DPIAScanner'),
        }
        
        if scanner_type not in scanners:
            raise ValueError(f"Unknown scanner type: {scanner_type}")
        
        module_name, class_name = scanners[scanner_type]
        module = __import__(module_name, fromlist=[class_name])
        scanner_class = getattr(module, class_name)
        
        return scanner_class()
    
    def _execute_job(self, job_data: dict) -> dict:
        """Execute a scanner job."""
        job_id = job_data['job_id']
        scanner_type = job_data['scanner_type']
        input_data = job_data.get('input_data', {})
        
        logger.info(f"Executing job {job_id}: {scanner_type}")
        
        try:
            scanner = self._get_scanner(scanner_type)
            
            self._update_job_status(job_id, 'running', progress=10)
            
            if scanner_type == 'code':
                result = scanner.scan_directory(
                    input_data.get('directory', '.'),
                    max_files_to_scan=input_data.get('max_files', 500)
                )
            elif scanner_type == 'website':
                result = scanner.scan_website(input_data.get('url', ''))
            elif scanner_type == 'audio_video':
                result = scanner.scan_file(input_data.get('file_path', ''))
                result = result.__dict__ if hasattr(result, '__dict__') else result
            else:
                if hasattr(scanner, 'scan'):
                    result = scanner.scan(input_data)
                elif hasattr(scanner, 'scan_directory'):
                    result = scanner.scan_directory(input_data.get('path', '.'))
                else:
                    raise ValueError(f"Scanner {scanner_type} has no scan method")
            
            self._update_job_status(job_id, 'completed', progress=100, result=result)
            logger.info(f"Job {job_id} completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            self._update_job_status(job_id, 'failed', error=str(e))
            raise
    
    def run(self, max_jobs: int = None):
        """
        Main worker loop - pulls jobs from queue and executes them.
        
        Args:
            max_jobs: Maximum jobs to process before exiting (None = infinite)
        """
        self.running = True
        jobs_processed = 0
        
        logger.info(f"Worker {self.worker_id} started, waiting for jobs...")
        
        while self.running:
            try:
                job_data = self.redis_client.brpop(self.QUEUE_KEY, timeout=5)
                
                if job_data is None:
                    continue
                
                _, job_json = job_data
                job = json.loads(job_json)
                
                self.current_job = job['job_id']
                self._execute_job(job)
                self.current_job = None
                
                jobs_processed += 1
                
                if max_jobs and jobs_processed >= max_jobs:
                    logger.info(f"Worker completed {max_jobs} jobs, exiting")
                    break
                    
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(1)
        
        logger.info(f"Worker {self.worker_id} stopped after processing {jobs_processed} jobs")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='DataGuardian Pro Scanner Worker')
    parser.add_argument('--worker-id', help='Unique worker identifier')
    parser.add_argument('--redis-url', help='Redis connection URL')
    parser.add_argument('--max-jobs', type=int, help='Max jobs before exit')
    
    args = parser.parse_args()
    
    worker = ScannerWorker(
        worker_id=args.worker_id,
        redis_url=args.redis_url
    )
    
    worker.run(max_jobs=args.max_jobs)
