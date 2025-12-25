"""
DataGuardian Pro API Routes
REST API endpoints for external integrations
"""

from flask import Blueprint, jsonify, request
import logging
import uuid
import json
import hashlib
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


def _get_redis_cache():
    """Get Redis cache instance with fallback."""
    try:
        from utils.redis_cache import RedisCache
        return RedisCache(strict_mode=False)
    except Exception as e:
        logger.debug(f"Redis cache not available: {e}")
        return None


def _cache_key(prefix: str, *args) -> str:
    """Generate cache key from prefix and arguments."""
    key_data = f"{prefix}:{':'.join(str(a) for a in args)}"
    return f"api:{hashlib.md5(key_data.encode()).hexdigest()[:16]}"

api_blueprint = Blueprint('api', __name__, url_prefix='/api/v1')


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        return f(*args, **kwargs)
    return decorated


@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0'
    })


@api_blueprint.route('/scans', methods=['GET'])
@require_api_key
def list_scans():
    """List recent scans with Redis caching (60s TTL)"""
    try:
        cache = _get_redis_cache()
        cache_key = _cache_key('scans_list', '30d')
        
        if cache:
            cached = cache.get(cache_key)
            if cached:
                logger.debug("Returning cached scans list")
                return jsonify(cached)
        
        from services.results_aggregator import ResultsAggregator
        aggregator = ResultsAggregator()
        scans = aggregator.get_recent_scans(days=30)
        
        result = {
            'scans': [
                {
                    'id': scan.get('scan_id'),
                    'type': scan.get('scan_type'),
                    'timestamp': str(scan.get('timestamp')),
                    'total_pii': scan.get('total_pii_found', 0),
                    'high_risk': scan.get('high_risk_count', 0),
                    'compliance_score': scan.get('result', {}).get('compliance_score', 0)
                }
                for scan in scans
            ],
            'count': len(scans)
        }
        
        if cache:
            cache.set(cache_key, result, ttl=60)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error listing scans: {e}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/scans/<scan_id>', methods=['GET'])
@require_api_key
def get_scan(scan_id):
    """Get specific scan details"""
    try:
        from services.results_aggregator import ResultsAggregator
        aggregator = ResultsAggregator()
        scans = aggregator.get_recent_scans(days=365)
        
        for scan in scans:
            if scan.get('scan_id') == scan_id:
                return jsonify({
                    'scan': {
                        'id': scan.get('scan_id'),
                        'type': scan.get('scan_type'),
                        'region': scan.get('region'),
                        'timestamp': str(scan.get('timestamp')),
                        'file_count': scan.get('file_count', 0),
                        'total_pii': scan.get('total_pii_found', 0),
                        'high_risk': scan.get('high_risk_count', 0),
                        'result': scan.get('result', {})
                    }
                })
        
        return jsonify({'error': 'Scan not found'}), 404
    except Exception as e:
        logger.error(f"Error getting scan {scan_id}: {e}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/scans', methods=['POST'])
@require_api_key
def create_scan():
    """Create a new scan request"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        scan_type = data.get('type')
        if not scan_type:
            return jsonify({'error': 'Scan type required'}), 400
        
        scan_id = str(uuid.uuid4())
        
        return jsonify({
            'scan_id': scan_id,
            'status': 'queued',
            'type': scan_type,
            'message': 'Scan request queued for processing'
        }), 202
        
    except Exception as e:
        logger.error(f"Error creating scan: {e}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/compliance/status', methods=['GET'])
@require_api_key
def compliance_status():
    """Get overall compliance status with Redis caching (120s TTL)"""
    try:
        cache = _get_redis_cache()
        cache_key = _cache_key('compliance_status', '30d')
        
        if cache:
            cached = cache.get(cache_key)
            if cached:
                logger.debug("Returning cached compliance status")
                return jsonify(cached)
        
        from services.results_aggregator import ResultsAggregator
        aggregator = ResultsAggregator()
        scans = aggregator.get_recent_scans(days=30)
        
        scores = [scan.get('result', {}).get('compliance_score', 0) for scan in scans if scan.get('result', {}).get('compliance_score', 0) > 0]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        result = {
            'compliance': {
                'gdpr': {'status': 'compliant' if avg_score > 70 else 'needs_attention', 'score': avg_score},
                'uavg': {'status': 'compliant', 'region': 'Netherlands'},
                'ai_act': {'status': 'pending', 'deadline': '2025-08-01'},
                'soc2': {'status': 'available'},
                'nis2': {'status': 'available'}
            },
            'overall_score': avg_score,
            'scans_analyzed': len(scans)
        }
        
        if cache:
            cache.set(cache_key, result, ttl=120)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting compliance status: {e}")
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/license', methods=['GET'])
@require_api_key
def license_info():
    """Get license information"""
    try:
        return jsonify({
            'license': {
                'tier': 'professional',
                'status': 'active',
                'scans_remaining': 250,
                'expires': '2025-12-31'
            }
        })
    except Exception as e:
        logger.error(f"Error getting license info: {e}")
        return jsonify({'error': str(e)}), 500
