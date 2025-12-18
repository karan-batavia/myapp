"""
Bot Protection Service for DataGuardian Pro
Comprehensive protection against automated account creation

Security measures:
1. Rate limiting per IP address
2. Honeypot field detection
3. Time-based submission check (too-fast detection)
4. Disposable email domain blocking
5. Simple math CAPTCHA challenge
"""

import os
import time
import random
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
import redis

logger = logging.getLogger(__name__)

DISPOSABLE_EMAIL_DOMAINS = {
    'tempmail.com', 'temp-mail.org', 'guerrillamail.com', 'mailinator.com',
    '10minutemail.com', 'throwaway.email', 'fakeinbox.com', 'trashmail.com',
    'getnada.com', 'tempail.com', 'dispostable.com', 'mailnesia.com',
    'tmpmail.org', 'dropmail.me', 'yopmail.com', 'moakt.com', 'tempr.email',
    'fakemailgenerator.com', 'emailondeck.com', 'emailtemporar.ro',
    'temp-mail.io', 'mohmal.com', 'tempmailo.com', 'emailfake.com',
    'maildrop.cc', 'inboxkitten.com', 'minuteinbox.com', 'sharklasers.com',
    'spam4.me', 'grr.la', 'guerrillamailblock.com', 'burnermail.io'
}

RATE_LIMIT_WINDOW = 3600
MAX_REGISTRATIONS_PER_IP = 5
MIN_FORM_COMPLETION_SECONDS = 3

class BotProtection:
    """Bot protection with Redis-backed rate limiting"""
    
    def __init__(self):
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed, using fallback: {e}")
            self.redis_client = None
    
    def _get_ip_hash(self, ip_address: str) -> str:
        """Hash IP for storage (GDPR-compliant)"""
        return hashlib.sha256(f"dgp_{ip_address}".encode()).hexdigest()[:16]
    
    def check_rate_limit(self, ip_address: str) -> Tuple[bool, str]:
        """
        Check if IP has exceeded registration rate limit
        Returns: (is_allowed, message)
        """
        if not ip_address or ip_address == 'unknown':
            return True, ""
        
        ip_hash = self._get_ip_hash(ip_address)
        key = f"reg_attempts:{ip_hash}"
        
        try:
            if self.redis_client:
                attempts = self.redis_client.get(key)
                attempts = int(attempts) if attempts else 0
                
                if attempts >= MAX_REGISTRATIONS_PER_IP:
                    return False, "Too many registration attempts. Please try again later."
                
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, RATE_LIMIT_WINDOW)
                pipe.execute()
                
            return True, ""
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, ""
    
    def check_honeypot(self, honeypot_value: str) -> Tuple[bool, str]:
        """
        Check honeypot field - should be empty for real users
        Returns: (is_allowed, message)
        """
        if honeypot_value and honeypot_value.strip():
            logger.warning(f"Honeypot triggered: {honeypot_value[:20]}")
            return False, "Registration failed. Please try again."
        return True, ""
    
    def check_submission_time(self, form_start_time: float) -> Tuple[bool, str]:
        """
        Check if form was completed too quickly (bot behavior)
        Returns: (is_allowed, message)
        """
        if not form_start_time:
            return True, ""
        
        elapsed = time.time() - form_start_time
        
        if elapsed < MIN_FORM_COMPLETION_SECONDS:
            logger.warning(f"Form completed too fast: {elapsed:.2f}s")
            return False, "Please take your time to fill out the form."
        
        return True, ""
    
    def check_email_domain(self, email: str) -> Tuple[bool, str]:
        """
        Check if email uses disposable email domain
        Returns: (is_allowed, message)
        """
        if not email or '@' not in email:
            return False, "Please enter a valid email address"
        
        domain = email.split('@')[1].lower()
        
        if domain in DISPOSABLE_EMAIL_DOMAINS:
            return False, "Temporary email addresses are not allowed. Please use your business email."
        
        if len(domain.split('.')) < 2:
            return False, "Please enter a valid email domain"
        
        return True, ""
    
    def generate_captcha(self) -> Tuple[str, int]:
        """
        Generate simple math CAPTCHA
        Returns: (question, answer)
        """
        num1 = random.randint(2, 15)
        num2 = random.randint(2, 10)
        operation = random.choice(['+', '-'])
        
        if operation == '+':
            answer = num1 + num2
            question = f"What is {num1} + {num2}?"
        else:
            if num1 < num2:
                num1, num2 = num2, num1
            answer = num1 - num2
            question = f"What is {num1} - {num2}?"
        
        return question, answer
    
    def verify_captcha(self, user_answer: str, correct_answer: int) -> Tuple[bool, str]:
        """
        Verify CAPTCHA answer
        Returns: (is_correct, message)
        """
        try:
            user_int = int(user_answer.strip())
            if user_int == correct_answer:
                return True, ""
            else:
                return False, "Incorrect answer. Please try again."
        except (ValueError, AttributeError):
            return False, "Please enter a valid number"
    
    def validate_registration(
        self,
        ip_address: str,
        email: str,
        honeypot_value: str,
        form_start_time: float,
        captcha_answer: str,
        correct_captcha: int
    ) -> Tuple[bool, str]:
        """
        Run all bot protection checks
        Returns: (is_allowed, error_message)
        """
        allowed, msg = self.check_rate_limit(ip_address)
        if not allowed:
            return False, msg
        
        allowed, msg = self.check_honeypot(honeypot_value)
        if not allowed:
            return False, msg
        
        allowed, msg = self.check_submission_time(form_start_time)
        if not allowed:
            return False, msg
        
        allowed, msg = self.check_email_domain(email)
        if not allowed:
            return False, msg
        
        allowed, msg = self.verify_captcha(captcha_answer, correct_captcha)
        if not allowed:
            return False, msg
        
        return True, ""
    
    def log_suspicious_activity(self, ip_address: str, reason: str, details: Dict[str, Any] = None):
        """Log suspicious registration activity"""
        ip_hash = self._get_ip_hash(ip_address) if ip_address else 'unknown'
        logger.warning(f"Suspicious registration: {reason} | IP: {ip_hash} | Details: {details}")
        
        if self.redis_client:
            try:
                key = f"suspicious:{ip_hash}"
                self.redis_client.lpush(key, f"{datetime.utcnow().isoformat()}:{reason}")
                self.redis_client.expire(key, 86400 * 7)
            except Exception:
                pass


_bot_protection = None

def get_bot_protection() -> BotProtection:
    """Get singleton bot protection instance"""
    global _bot_protection
    if _bot_protection is None:
        _bot_protection = BotProtection()
    return _bot_protection
