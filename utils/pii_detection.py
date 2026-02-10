import re
from typing import Dict, List, Any, Optional

def identify_pii_in_text(text: str, region: str = "Netherlands") -> List[Dict[str, Any]]:
    """
    Identify PII in text using regular expressions.
    
    Args:
        text: The text to scan for PII
        region: The region for which to apply PII detection rules
        
    Returns:
        List of dictionaries containing PII information
    """
    pii_items = []
    
    # Email addresses
    pii_items.extend(_find_emails(text))
    
    # Phone numbers
    pii_items.extend(_find_phone_numbers(text))
    
    # Addresses
    pii_items.extend(_find_addresses(text))
    
    # Names
    pii_items.extend(_find_names(text))
    
    # Credit card numbers
    pii_items.extend(_find_credit_cards(text))
    
    # IP addresses
    pii_items.extend(_find_ip_addresses(text))
    
    # Dates of birth
    pii_items.extend(_find_dates_of_birth(text))
    
    # Netherlands-specific identifiers with ML-enhanced context
    if region == "Netherlands":
        pii_items.extend(_find_bsn_numbers(text))
        pii_items.extend(_find_kvk_numbers(text))
        pii_items.extend(_find_dutch_phone_numbers(text))
        pii_items.extend(_find_dutch_addresses(text))
        pii_items.extend(_find_dutch_government_ids(text))
        pii_items.extend(_find_dutch_business_identifiers(text))
        pii_items.extend(_find_dutch_health_insurance(text))
        pii_items.extend(_find_dutch_bank_codes(text))
        pii_items.extend(_find_dutch_regional_identifiers(text))
        pii_items.extend(_find_dutch_educational_identifiers(text))
        pii_items.extend(_find_dutch_municipal_services(text))
        
        # Apply ML-enhanced context analysis for Netherlands
        pii_items = _enhance_dutch_context_analysis(pii_items, text)
    
    # Passport numbers
    pii_items.extend(_find_passport_numbers(text))
    
    # Financial data
    pii_items.extend(_find_financial_data(text))
    
    # Medical data
    pii_items.extend(_find_medical_data(text))
    
    # Usernames and passwords
    pii_items.extend(_find_credentials(text))
    
    # Personal Access Tokens and API Keys
    pii_items.extend(_find_personal_access_tokens(text))
    
    return pii_items

def _find_emails(text: str) -> List[Dict[str, Any]]:
    """Find email addresses in text."""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.finditer(pattern, text)
    
    found = []
    for match in matches:
        found.append({
            'type': 'Email',
            'value': match.group(0)
        })
    
    return found

def _find_phone_numbers(text: str) -> List[Dict[str, Any]]:
    """Find phone numbers in text."""
    # International format
    pattern1 = r'\+\d{1,3}[-.\s]?(\d{1,3}[-.\s]?)?\d{3,}[-.\s]?\d{3,}'
    
    # National format
    pattern2 = r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    
    # European format
    pattern3 = r'\b\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,4}\b'
    
    patterns = [pattern1, pattern2, pattern3]
    found = []
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            found.append({
                'type': 'Phone',
                'value': match.group(0)
            })
    
    return found

def _find_addresses(text: str) -> List[Dict[str, Any]]:
    """Find addresses in text."""
    # Simple address pattern for demonstration (would need more complex patterns in production)
    patterns = [
        # Street address with number
        r'\b\d{1,5}\s[A-Za-z0-9\s]{1,50}(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b',
        
        # European-style address
        r'\b[A-Za-z0-9\s]{1,50}(straat|laan|weg|plein|straße|straße|rue)\s\d{1,5}\b',
        
        # Postal codes
        r'\b\d{5}(-\d{4})?\b',  # US ZIP
        r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b',  # UK Postcode
        r'\b\d{4}\s?(?!KB|MB|GB|TB|PB|HZ)[A-Z]{2}\b'  # Dutch Postcode (excluding unit suffixes)
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            found.append({
                'type': 'Address',
                'value': match.group(0)
            })
    
    return found

def _find_names(text: str) -> List[Dict[str, Any]]:
    """Find names in text (simplified approach for demonstration)."""
    # This is a simplified approach and would need more sophisticated NLP in production
    # Looking for title + capitalized words
    pattern = r'\b(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s[A-Z][a-z]+(\s[A-Z][a-z]+)?\b'
    
    # Also look for common name patterns
    pattern2 = r'\b[A-Z][a-z]+\s(van|de|der|den|von|du|di|le|la|los)\s[A-Z][a-z]+\b'
    
    found = []
    for p in [pattern, pattern2]:
        matches = re.finditer(p, text)
        for match in matches:
            found.append({
                'type': 'Name',
                'value': match.group(0)
            })
    
    return found

def _find_credit_cards(text: str) -> List[Dict[str, Any]]:
    """Find credit card numbers in text."""
    # Match common credit card formats
    patterns = [
        # Visa
        r'\b4[0-9]{12}(?:[0-9]{3})?\b',
        
        # Mastercard
        r'\b5[1-5][0-9]{14}\b',
        
        # Amex
        r'\b3[47][0-9]{13}\b',
        
        # Discover
        r'\b6(?:011|5[0-9]{2})[0-9]{12}\b',
        
        # With spaces or dashes
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            value = match.group(0)
            # Mask most digits for security
            masked = value[:4] + '*' * (len(value) - 8) + value[-4:]
            found.append({
                'type': 'Credit Card',
                'value': masked
            })
    
    return found

def _find_ip_addresses(text: str) -> List[Dict[str, Any]]:
    """Find IP addresses in text."""
    # IPv4
    pattern1 = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    
    # IPv6 (simplified)
    pattern2 = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    
    found = []
    for pattern in [pattern1, pattern2]:
        matches = re.finditer(pattern, text)
        for match in matches:
            found.append({
                'type': 'IP Address',
                'value': match.group(0)
            })
    
    return found

def _find_dates_of_birth(text: str) -> List[Dict[str, Any]]:
    """Find dates of birth in text."""
    # Look for date patterns with context that suggests a birth date
    patterns = [
        # DOB explicit mention
        r'\b(?:DOB|Date\sof\sBirth|Birth\sDate|Born\son)[:=\s-]+([0-9]{1,2}[-/\.][0-9]{1,2}[-/\.][0-9]{2,4})\b',
        
        # Common date formats (with context check)
        r'\bborn\s+(?:on\s+)?([0-9]{1,2}[-/\.][0-9]{1,2}[-/\.][0-9]{2,4})\b',
        r'\bbirth(?:date|day)?\s*(?::|is|on)?\s*([0-9]{1,2}[-/\.][0-9]{1,2}[-/\.][0-9]{2,4})\b'
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Use the captured group if available, otherwise the whole match
            value = match.group(1) if match.lastindex else match.group(0)
            found.append({
                'type': 'Date of Birth',
                'value': value
            })
    
    return found

def _find_bsn_numbers(text: str) -> List[Dict[str, Any]]:
    """Find Dutch BSN numbers in text."""
    # BSN is a 9-digit number that passes the "11 test"
    # For simplicity, we'll just look for 9-digit numbers mentioned near the term "BSN"
    pattern = r'\b(?:BSN|Burgerservicenummer)(?:[:\s-]+)?(\d{9})\b'
    
    # Also look for 9-digit numbers with dashes or spaces
    pattern2 = r'\b\d{3}[-\s]\d{3}[-\s]\d{3}\b'
    
    found = []
    
    # Check for explicit BSN mentions
    matches = re.finditer(pattern, text, re.IGNORECASE)
    for match in matches:
        bsn = match.group(1) if match.lastindex else match.group(0)
        # Remove non-digits
        bsn = re.sub(r'\D', '', bsn)
        found.append({
            'type': 'BSN',
            'value': bsn
        })
    
    # Check for potential BSN patterns
    matches = re.finditer(pattern2, text)
    for match in matches:
        bsn = re.sub(r'\D', '', match.group(0))
        if _is_valid_bsn(bsn):
            found.append({
                'type': 'BSN',
                'value': bsn
            })
    
    return found

def _is_valid_bsn(bsn: str) -> bool:
    """
    Check if a number passes the BSN validation ("11 test").
    
    Official Dutch BSN 11-proef algorithm:
    checksum = (digit_0 × 9) + (digit_1 × 8) + (digit_2 × 7) + (digit_3 × 6) + 
               (digit_4 × 5) + (digit_5 × 4) + (digit_6 × 3) + (digit_7 × 2) - 
               (digit_8 × 1)
    
    BSN is valid if: checksum mod 11 == 0
    
    Example: 111222333
    = (1×9) + (1×8) + (1×7) + (2×6) + (2×5) + (2×4) + (3×3) + (3×2) - (3×1)
    = 9 + 8 + 7 + 12 + 10 + 8 + 9 + 6 - 3
    = 66 mod 11 = 0 ✓ VALID
    """
    if not bsn.isdigit() or len(bsn) != 9:
        return False
    
    # Apply the official Dutch "11 test" for BSN
    total = 0
    for i in range(9):
        if i == 8:
            # Last digit is SUBTRACTED with factor 1
            total -= int(bsn[i]) * 1
        else:
            # First 8 digits use factors 9, 8, 7, 6, 5, 4, 3, 2
            total += int(bsn[i]) * (9 - i)
    
    return total % 11 == 0

def _find_passport_numbers(text: str) -> List[Dict[str, Any]]:
    """Find passport numbers in text."""
    # Different passport formats for different countries
    patterns = [
        # Generic passport number mention
        r'\bpassport(?:\s+number)?(?:[:\s#]+)([A-Z0-9]{6,12})\b',
        
        # Dutch passport
        r'\b[A-Z]{2}[0-9]{6}\b',
        
        # Various formats
        r'\b[A-Z]{1,2}[0-9]{6,8}\b'
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Use the captured group if available, otherwise the whole match
            value = match.group(1) if match.lastindex else match.group(0)
            found.append({
                'type': 'Passport Number',
                'value': value
            })
    
    return found

def _find_financial_data(text: str) -> List[Dict[str, Any]]:
    """Find financial data in text."""
    # Bank account numbers
    patterns = [
        # IBAN
        r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}(?:[A-Z0-9]{0,16})?\b',
        
        # Bank account mentions
        r'\baccount(?:\s+number)?(?:[:\s#]+)([0-9]{6,12})\b',
        
        # Dutch bank account
        r'\bNL\d{2}\s?[A-Z]{4}\s?\d{4}\s?\d{4}\s?\d{2}\b'
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Use the captured group if available, otherwise the whole match
            value = match.group(1) if match.lastindex else match.group(0)
            found.append({
                'type': 'Financial Data',
                'value': value
            })
    
    return found

def _find_medical_data(text: str) -> List[Dict[str, Any]]:
    """Find medical data in text."""
    # Medical terms and contexts
    medical_contexts = [
        r'\b(?:patient|medical|health|diagnosis|treatment|medication|prescription|symptom|disease|doctor|hospital|clinic)\b',
        r'\b(?:MRI|CT scan|X-ray|blood test|examination|surgery|condition|admitted|discharged)\b'
    ]
    
    found = []
    for pattern in medical_contexts:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Get a context snippet around the match
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]
            
            found.append({
                'type': 'Medical Data',
                'value': match.group(0),
                'context': '...' + context + '...'
            })
    
    return found

def _find_credentials(text: str) -> List[Dict[str, Any]]:
    """Find usernames and passwords in text."""
    patterns = [
        # Username
        r'\busername(?:[:\s]+)([A-Za-z0-9_-]{3,20})\b',
        
        # Username/Password pair
        r'\busername(?:[:\s]+)([A-Za-z0-9_-]{3,20})(?:[,\s]+)password(?:[:\s]+)([^\s,;]{6,20})\b',
        
        # Common login patterns
        r'\blogin(?:[:\s]+)([A-Za-z0-9_-]{3,20})\b',
        r'\buser(?:[:\s]+)([A-Za-z0-9_-]{3,20})\b',
        
        # Expanded credential patterns for vulnerable applications
        r'\b(username|user|login|user_id|userid|user_name)\s*[=:]\s*["\']([^"\']{3,30})["\']',
        r'\b(password|passwd|pwd|pass|secret|api_key|apikey|token|access_key)\s*[=:]\s*["\']([^"\']{3,30})["\']',
        
        # Hard-coded credentials in code
        r'\blogin\s*\(["\']([^"\']{3,30})["\'],\s*["\']([^"\']{3,30})["\']\)',
        r'\bauth\w*\s*\(["\']([^"\']{3,30})["\'],\s*["\']([^"\']{3,30})["\']\)',
        
        # Database connection strings with credentials
        r'(?i)(mongodb|mysql|postgresql|jdbc|sqlserver|oracle|redis)(://|:|@)([^\s;,]*:[^\s;,]*@)([a-zA-Z0-9.-]+)',
        
        # Environment variables or config with credentials
        r'(?i)(APP|API|DB|ENV|CONFIG)_?(SECRET|KEY|TOKEN|PASS|PASSWORD|USER|USERNAME)\s*[=:]\s*["\']([^"\']{3,30})["\']',
        
        # Credentials in JSON/dict format
        r'["\'](?:user|username|login)["\'][\s:]+["\']([^"\']{3,30})["\']',
        r'["\'](?:pass|password|secret|token|key)["\'][\s:]+["\']([^"\']{3,30})["\']',
        
        # Intentional vulnerable patterns
        r'(?i)(test|demo|example|sample|dummy|default)_(user|password|secret|key)',
        r'(?i)(root|admin|administrator|superuser|superadmin|dba|sa)[.](password|pwd|pass)',
        r'hardcoded[_\s]*(password|credential|secret|key|token)',
        
        # Framework-specific patterns (Flask, Django, etc.)
        r'(?i)app\.config\[["\']SECRET_KEY["\']\]\s*=\s*["\']([^"\']{3,})["\']',
        r'(?i)SECRET_KEY\s*=\s*["\']([^"\']{3,})["\']',
        r'(?i)SQLALCHEMY_DATABASE_URI\s*=\s*["\']([^"\']{3,})["\']',
        
        # URL with credentials embedded
        r'(https?|ftp)://([^:]+):([^@]+)@[^/\s]+',
        
        # Common credential variables in vulnerable applications
        r'(?i)var\s+(api_key|apikey|key|token|secret|password)\s*=\s*["\']([^"\']{8,})["\']',
        r'(?i)const\s+(api_key|apikey|key|token|secret|password)\s*=\s*["\']([^"\']{8,})["\']',
        
        # Security implementation patterns
        r'plain[_\s]*text[_\s]*(password|credential)',
        r'unencrypted[_\s]*(password|credential)'
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                if match.lastindex == 2:  # Username/password pair
                    found.append({
                        'type': 'Username',
                        'value': match.group(1)
                    })
                    found.append({
                        'type': 'Password',
                        'value': '*******'  # Mask password
                    })
                else:
                    # Just credential or full match
                    if "password" in match.group(0).lower() or "secret" in match.group(0).lower() or "key" in match.group(0).lower():
                        found.append({
                            'type': 'Credentials',
                            'value': match.group(0)
                        })
                    else:
                        value = match.group(1) if match.lastindex else match.group(0)
                        found.append({
                            'type': 'Credentials',
                            'value': value
                        })
            except Exception:
                # Fallback if regex groups don't match expectations
                found.append({
                    'type': 'Credentials',
                    'value': match.group(0)
                })
    
    return found

def _find_personal_access_tokens(text: str) -> List[Dict[str, Any]]:
    """Find Personal Access Tokens and API keys in text."""
    patterns = [
        # GitHub Personal Access Tokens (flexible length 36-40 chars)
        r'\bghp_[a-zA-Z0-9]{36,40}\b',  # GitHub PAT (classic)
        r'\bgho_[a-zA-Z0-9]{36,40}\b',  # GitHub OAuth token
        r'\bghu_[a-zA-Z0-9]{36,40}\b',  # GitHub user token
        r'\bghs_[a-zA-Z0-9]{36,40}\b',  # GitHub server token
        r'\bghr_[a-zA-Z0-9]{36,40}\b',  # GitHub refresh token
        
        # GitLab Personal Access Tokens
        r'\bglpat-[a-zA-Z0-9_-]{20}\b',  # GitLab PAT
        r'\bgldt-[a-zA-Z0-9_-]{20}\b',   # GitLab deploy token
        r'\bglft-[a-zA-Z0-9_-]{20}\b',   # GitLab feed token
        
        # Azure DevOps Personal Access Tokens
        r'\b[a-zA-Z0-9]{52}\b',  # Azure DevOps PAT (52 chars base64)
        
        # Generic API keys and tokens
        r'\bapi[_-]?key[:\s=]*["\']?([a-zA-Z0-9_-]{20,})["\']?\b',
        r'\baccess[_-]?token[:\s=]*["\']?([a-zA-Z0-9_.-]{20,})["\']?\b',
        r'\bbearer[_\s]+([a-zA-Z0-9_.-]{20,})\b',
        r'\btoken[:\s=]*["\']?([a-zA-Z0-9_.-]{20,})["\']?\b',
        
        # AWS Access Keys
        r'\bAKIA[0-9A-Z]{16}\b',  # AWS Access Key ID
        r'\b[a-zA-Z0-9+/]{40}\b', # AWS Secret Access Key
        
        # Azure keys
        r'\b[a-zA-Z0-9+/]{44}==\b',  # Azure storage key
        
        # Common secret patterns
        r'\bsecret[_-]?key[:\s=]*["\']?([a-zA-Z0-9_.-]{16,})["\']?\b',
        r'\bprivate[_-]?key[:\s=]*["\']?([a-zA-Z0-9_.-]{20,})["\']?\b',
        
        # Slack tokens
        r'\bxoxb-[0-9]+-[0-9]+-[0-9a-zA-Z]{24}\b',  # Slack bot token
        r'\bxoxa-[0-9]+-[0-9]+-[0-9a-zA-Z]{24}\b',  # Slack access token
        r'\bxoxp-[0-9]+-[0-9]+-[0-9a-zA-Z]{24}\b',  # Slack user token
        
        # Discord tokens
        r'\b[MN][A-Za-z\d]{23}\.[A-Za-z\d]{6}\.[A-Za-z\d\-_]{27}\b',  # Discord bot token
        
        # Generic patterns for various platforms
        r'\b[a-zA-Z0-9]{32}\b',   # 32-char hex tokens
        r'\b[a-zA-Z0-9]{40}\b',   # 40-char tokens (common for SHA1-based)
        r'\b[a-zA-Z0-9+/]{64}={0,2}\b',  # Base64 64-char tokens
        
        # JWT tokens
        r'\beyJ[a-zA-Z0-9+/]+=*\.[a-zA-Z0-9+/]+=*\.[a-zA-Z0-9+/\-_]+=*\b',
        
        # Environment variable patterns for tokens
        r'\b[A-Z_]+TOKEN[:\s=]*["\']?([a-zA-Z0-9_.-]{16,})["\']?\b',
        r'\b[A-Z_]+KEY[:\s=]*["\']?([a-zA-Z0-9_.-]{16,})["\']?\b',
        r'\b[A-Z_]+SECRET[:\s=]*["\']?([a-zA-Z0-9_.-]{16,})["\']?\b',
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            token_value = match.group(1) if match.lastindex else match.group(0)
            
            # Determine token type based on pattern
            token_type = "Personal Access Token"
            risk_level = "Critical"
            description = "Personal Access Token or API key detected"
            
            if "ghp_" in token_value or "gho_" in token_value or "ghu_" in token_value:
                token_type = "GitHub Personal Access Token"
                description = "GitHub Personal Access Token - grants access to repositories and user data"
            elif "glpat-" in token_value or "gldt-" in token_value:
                token_type = "GitLab Personal Access Token"
                description = "GitLab Personal Access Token - grants access to GitLab repositories and APIs"
            elif "AKIA" in token_value:
                token_type = "AWS Access Key"
                description = "AWS Access Key ID - grants access to AWS services"
            elif "xoxb-" in token_value or "xoxa-" in token_value or "xoxp-" in token_value:
                token_type = "Slack Token"
                description = "Slack API token - grants access to Slack workspace"
            elif "eyJ" in token_value:
                token_type = "JWT Token"
                description = "JSON Web Token - may contain sensitive authentication data"
            elif len(token_value) == 52 and token_value.isalnum():
                token_type = "Azure DevOps PAT"
                description = "Azure DevOps Personal Access Token - grants access to Azure DevOps services"
            
            # Mask the token value for security
            masked_value = token_value[:8] + "..." + token_value[-4:] if len(token_value) > 12 else "*" * len(token_value)
            
            found.append({
                'type': token_type,
                'value': masked_value,
                'risk_level': risk_level,
                'description': description,
                'gdpr_article': 'Article 32 - Security of processing',
                'recommendation': 'Immediately revoke this token and rotate credentials. Review access logs for unauthorized usage.'
            })
    
    return found


def _find_kvk_numbers(text: str) -> List[Dict[str, Any]]:
    """Find Dutch Chamber of Commerce (KvK) numbers in text."""
    # KvK numbers are 8 digits, often mentioned with "KvK" or "Chamber of Commerce"
    patterns = [
        r'\b(?:KvK|kvk|K\.v\.K\.|Chamber\s+of\s+Commerce|Kamer\s+van\s+Koophandel)(?:[:\s#-]+)?(\d{8})\b',
        r'\bKvK[\s-]*nummer[\s:]*(\d{8})\b',
        r'\bHandelsregisternummer[\s:]*(\d{8})\b',
        # Standalone 8-digit numbers that could be KvK
        r'\b\d{8}\b'  # This will need context validation
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            kvk = match.group(1) if match.lastindex else match.group(0)
            kvk = re.sub(r'\D', '', kvk)
            
            # Validate 8-digit format and reasonable number range
            if len(kvk) == 8 and kvk.isdigit() and int(kvk) >= 10000000:
                found.append({
                    'type': 'KvK Number',
                    'value': kvk,
                    'description': 'Dutch Chamber of Commerce number'
                })
    
    return found


def _find_dutch_phone_numbers(text: str) -> List[Dict[str, Any]]:
    """Find Netherlands-specific phone numbers."""
    patterns = [
        # Netherlands international format
        r'\+31[-\s]?(?:6[-\s]?\d{8}|\d{1,3}[-\s]?\d{3}[-\s]?\d{4})',
        
        # Mobile numbers (06 prefix)
        r'\b06[-\s]?\d{4}[-\s]?\d{4}\b',
        r'\b06[-\s]?\d{8}\b',
        
        # Landline numbers (2-5 digit area codes)
        r'\b0(?:10|13|15|18|20|23|24|26|30|33|35|36|38|40|43|45|46|48|50|53|55|58|70|71|72|73|74|75|76|77|78|79)[-\s]?\d{3,4}[-\s]?\d{4}\b',
        
        # Service numbers
        r'\b0800[-\s]?\d{4}[-\s]?\d{3}\b',  # Free phone
        r'\b0900[-\s]?\d{4}[-\s]?\d{3}\b',  # Premium rate
        r'\b088[-\s]?\d{3}[-\s]?\d{4}\b',   # Non-geographic
        
        # Emergency and special services
        r'\b11[0-9]\b',  # Emergency services (112, 116, etc.)
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            found.append({
                'type': 'Dutch Phone Number',
                'value': match.group(0),
                'description': 'Netherlands phone number'
            })
    
    return found


def _find_dutch_addresses(text: str) -> List[Dict[str, Any]]:
    """Find comprehensive Dutch address components."""
    patterns = [
        # Dutch postcode (4 digits + 2 letters), excluding unit suffixes (KB, MB, GB, TB, PB, HZ)
        r'\b\d{4}\s?(?!KB|MB|GB|TB|PB|HZ)[A-Z]{2}\b',
        
        # Street names with house numbers
        r'\b[A-Za-z\s-]+(?:straat|laan|weg|plein|kade|gracht|steeg|pad|park|hof|singel|boulevard|avenue)[\s]*\d+[a-zA-Z]?\b',
        
        # House number with toevoeging (addition)
        r'\b\d{1,5}[a-zA-Z]?(?:[-\s]+(?:bis|ter|quater|A|B|C|D|I|II|III|IV))?\b',
        
        # Dutch city names (common ones)
        r'\b(?:Amsterdam|Rotterdam|Den\s+Haag|Utrecht|Eindhoven|Tilburg|Groningen|Almere|Breda|Nijmegen|Enschede|Haarlem|Arnhem|Zaanstad|Amersfoort|Apeldoorn|Hoofddorp|Maastricht|Leiden|Dordrecht|Zoetermeer|Zwolle|Deventer|Delft|Alkmaar|Leeuwarden|Sittard)\b',
        
        # Province names
        r'\b(?:Noord-Holland|Zuid-Holland|Utrecht|Gelderland|Overijssel|Flevoland|Noord-Brabant|Zeeland|Limburg|Friesland|Drenthe|Groningen)\b',
        
        # PO Box (Postbus)
        r'\bPostbus\s+\d{1,6}\b',
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            found.append({
                'type': 'Dutch Address Component',
                'value': match.group(0),
                'description': 'Netherlands address information'
            })
    
    return found


def _find_dutch_government_ids(text: str) -> List[Dict[str, Any]]:
    """Find comprehensive Dutch government-issued identification numbers."""
    patterns = [
        # Dutch passport (2 letters + 7 digits)
        r'\b[A-Z]{2}\d{7}\b',
        
        # Dutch driving license (10 digits)
        r'\b(?:rijbewijs|driving\s+license|driver\'s\s+license)(?:[:\s#-]+)?(\d{10})\b',
        
        # Dutch ID card number
        r'\b(?:identiteitskaart|ID\s+card|identity\s+card)(?:[:\s#-]+)?([A-Z]{2}\d{6}[A-Z]\d)\b',
        
        # Dutch vehicle license plate (all formats)
        r'\b(?:\d{2}[-\s]?[A-Z]{2}[-\s]?\d{2}|\d{1}[-\s]?[A-Z]{3}[-\s]?\d{2}|[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z]{2})\b',
        
        # Municipality codes (CBS codes) - 342 Dutch municipalities
        r'\bGM\d{4}\b',
        
        # Province codes (12 Dutch provinces)  
        r'\bPV\d{2}\b',
        
        # Water authority codes (21 water boards)
        r'\bWS\d{3}\b',
        
        # Security region codes (25 regions)
        r'\bVR\d{2}\b',
        
        # Court district codes
        r'\bRECHT\d{3}\b',
        
        # Police region codes
        r'\bPOL\d{3}\b',
        
        # Fire department codes
        r'\bBRAND\d{3}\b',
        
        # Ambulance service codes
        r'\bAMBU\d{3}\b',
        
        # Educational institution codes (BRIN)
        r'\bBRIN\d{2}[A-Z]{2}\b',
        
        # Higher education program codes (CROHO)
        r'\bCROHO\d{5}\b',
        
        # Professional certification numbers
        r'\bVCA\d{8}\b',     # Safety certification
        r'\bNVCB\d{6}\b',    # Construction certification  
        r'\bSCC\d{7}\b',     # Safety certificate contractors
        
        # Social security numbers
        r'\bAOW\d{9}\b',     # State pension number
        r'\bWW\d{8}\b',      # Unemployment benefits
        r'\bWAO\d{8}\b',     # Disability benefits
        r'\bWIA\d{8}\b',     # Work and Income Act
        r'\bZVW\d{9}\b',     # Health Insurance Law
        r'\bWLZ\d{8}\b',     # Long-term Care Act
        
        # Immigration and residence
        r'\bV\d{7}\b',       # V-number (alien registration)
        r'\bVAR\d{6}\b',     # Residence document number
        r'\bTVV\d{8}\b',     # Temporary residence permit
        r'\bVVR\d{8}\b',     # Return visa number
        
        # Court and legal identifiers
        r'\bLJN[A-Z]{2}\d{4}\b',  # Legal case numbers
        r'\bECLI:NL:[A-Z]{2,4}:\d{4}:\d+\b',  # European case law identifier
        r'\bPARKET\d{6}\b',  # Public prosecutor number
        
        # Professional licenses
        r'\bADV\d{6}\b',     # Lawyer license (Advocaat)
        r'\bNOT\d{6}\b',     # Notary license
        r'\bDEUR\d{6}\b',    # Bailiff license (Deurwaarder)
        r'\bCURATOR\d{6}\b', # Bankruptcy trustee
        
        # Healthcare professional IDs
        r'\bBIG\d{8}\b',     # Healthcare professional registration
        r'\bUZI\d{8}\b',     # Healthcare professional card
        r'\bAGB\d{8}\b',     # Healthcare provider codes
        r'\bGGZ\d{6}\b',     # Mental health registration
        r'\bZORG\d{8}\b',    # Care provider registration
        
        # Environment and permits
        r'\bWM\d{8}\b',      # Waste management permit
        r'\bWVO\d{7}\b',     # Water pollution permit
        r'\bWET\d{6}\b',     # Environmental permit
        r'\bEMISSIE\d{8}\b', # Emission permit
        r'\bNATUUR\d{6}\b',  # Nature permit
        
        # Energy sector identifiers
        r'\bEAN\d{18}\b',    # Energy connection code
        r'\bGTS\d{8}\b',     # Gas transport services
        r'\bTSO\d{6}\b',     # Transmission system operator
        r'\bDSO\d{6}\b',     # Distribution system operator
        r'\bENERGIE\d{8}\b', # Energy permit
        
        # Telecommunications
        r'\bACM\d{6}\b',     # Consumer and market authority
        r'\bTELECOM\d{8}\b', # Telecom permit
        r'\bFREQ\d{6}\b',    # Frequency allocation
        
        # Agriculture and food safety
        r'\bGGN\d{13}\b',    # GlobalGAP number
        r'\bNEVA\d{6}\b',    # Food safety inspection
        r'\bDIER\d{8}\b',    # Animal identification
        r'\bVEE\d{6}\b',     # Livestock registration
        r'\bLANDB\d{8}\b',   # Agricultural permit
        
        # Cultural heritage
        r'\bRCE\d{7}\b',     # Cultural heritage agency
        r'\bMONU\d{6}\b',    # Monument registration
        r'\bARCHEO\d{6}\b',  # Archeological permit
        
        # Transport and infrastructure
        r'\bCEMT\d{6}\b',    # Transport permit
        r'\bNIWO\d{8}\b',    # Road transport organization
        r'\bTLN\d{7}\b',     # Transport and logistics Nederland
        r'\bVOGELS\d{6}\b',  # Aviation permit
        r'\bWATER\d{8}\b',   # Waterway permit
        
        # Housing and construction
        r'\bBAG\d{16}\b',    # Address registration (BAG-ID)
        r'\bWOZ\d{12}\b',    # Property valuation number
        r'\bBOUW\d{8}\b',    # Building permit
        r'\bPLAN\d{6}\b',    # Zoning plan number
        
        # Financial supervision
        r'\bWFT\d{8}\b',     # Financial Supervision Act license
        r'\bDNB\d{6}\b',     # Central bank registration
        r'\bAFM\d{8}\b',     # Financial Markets Authority
        r'\bPENSIOEN\d{8}\b', # Pension fund registration
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = match.group(1) if match.lastindex else match.group(0)
            
            # Determine specific ID type for better classification
            id_type = "Dutch Government ID"
            description = "Netherlands government identification"
            risk_level = "Medium"
            
            if "BSN" in pattern or "Burgerservice" in pattern:
                id_type = "BSN Number"
                description = "Dutch Citizen Service Number"
                risk_level = "High"
            elif "rijbewijs" in pattern or "driving" in pattern:
                id_type = "Driver's License"
                description = "Netherlands driving license number"
            elif "identiteitskaart" in pattern or "ID" in pattern:
                id_type = "National ID Card"
                description = "Dutch identity card number"
                risk_level = "High"
            elif "GM" in value:
                id_type = "Municipality Code"
                description = "Dutch municipality identifier"
            elif "V" in value and len(value) == 8:
                id_type = "Alien Number"
                description = "Immigration registration number (V-number)"
                risk_level = "High"
            elif "BIG" in value:
                id_type = "Healthcare Professional ID"
                description = "Dutch healthcare professional registration"
                risk_level = "High"
            elif "AOW" in value or "WW" in value or "WIA" in value:
                id_type = "Social Security Number"
                description = "Dutch social benefits identifier"
                risk_level = "High"
            elif "BAG" in value:
                id_type = "Address Registration ID"
                description = "Dutch address database identifier"
            elif "WOZ" in value:
                id_type = "Property Valuation ID"
                description = "Netherlands property tax identifier"
            
            found.append({
                'type': id_type,
                'value': value,
                'description': description,
                'risk_level': risk_level
            })
    
    return found


def _find_dutch_business_identifiers(text: str) -> List[Dict[str, Any]]:
    """Find comprehensive Dutch business and commercial identifiers."""
    patterns = [
        # Dutch VAT number (BTW-nummer) - comprehensive patterns
        r'\b(?:BTW|VAT)[-\s]*(?:nummer|number)?[\s:]*NL\d{9}B\d{2}\b',
        r'\bNL\d{9}B\d{2}\b',  # Direct VAT format
        r'\b(?:Omzetbelasting|Sales\s+tax)[-\s]*(?:nummer|number)?[\s:]*NL\d{9}B\d{2}\b',
        
        # RSIN (Rechtspersonen Samenwerkingsverbanden Informatie Nummer)
        r'\b(?:RSIN|rechtspersonen)(?:[:\s#-]+)?(\d{9})\b',
        r'\bRechtspersonen\s+nummer[\s:]*(\d{9})\b',
        
        # Chamber of Commerce (KvK) extended patterns
        r'\bKvK[-\s]*nummer[\s:]*(\d{8})\b',
        r'\bHandelsregister[-\s]*nummer[\s:]*(\d{8})\b',
        r'\bChamber\s+of\s+Commerce[\s:#]*(\d{8})\b',
        r'\bKamer\s+van\s+Koophandel[\s:#]*(\d{8})\b',
        r'\bCOC[-\s]*number[\s:]*(\d{8})\b',
        
        # Corporate entity identifiers
        r'\bBV[-\s]*nummer[\s:]*(\d{8})\b',      # Private limited company
        r'\bNV[-\s]*nummer[\s:]*(\d{8})\b',      # Public limited company
        r'\bEENMANSZAAK[-\s]*nummer[\s:]*(\d{8})\b',  # Sole proprietorship
        r'\bVOF[-\s]*nummer[\s:]*(\d{8})\b',     # General partnership
        r'\bCV[-\s]*nummer[\s:]*(\d{8})\b',      # Limited partnership
        r'\bMAATSCHAP[-\s]*nummer[\s:]*(\d{8})\b', # Professional partnership
        r'\bSTICHTING[-\s]*nummer[\s:]*(\d{8})\b', # Foundation
        r'\bVERENIGING[-\s]*nummer[\s:]*(\d{8})\b', # Association
        r'\bCOOPERATIE[-\s]*nummer[\s:]*(\d{8})\b', # Cooperative
        
        # IBAN with all Dutch bank codes
        r'\bNL\d{2}[A-Z]{4}\d{10}\b',
        r'\bIBAN[\s:]*NL\d{2}[A-Z]{4}\d{10}\b',
        
        # Dutch bank account numbers (legacy format)
        r'\b\d{1,7}\.\d{2}\.\d{3}\b',  # Old format: 1234567.12.345
        r'\bRekeningnummer[\s:]*\d{1,7}\.\d{2}\.\d{3}\b',
        
        # Industry classification codes
        r'\bSBI[-\s]*code[\s:]*(\d{5})\b',       # Standard Business Industry
        r'\bNACE[-\s]*code[\s:]*(\d{4}\.\d{2})\b', # European industry classification
        r'\bIsic[-\s]*code[\s:]*(\d{4})\b',      # International Standard Industrial Classification
        
        # Professional services registrations
        r'\bNOVA[-\s]*nummer[\s:]*(\d{6})\b',    # Dutch Bar Association (lawyers)
        r'\bNRO[-\s]*nummer[\s:]*(\d{7})\b',     # Public accountant registration
        r'\bNIVRA[-\s]*nummer[\s:]*(\d{6})\b',   # Accountant association
        r'\bREA[-\s]*nummer[\s:]*(\d{8})\b',     # Tax advisor registration
        r'\bNOB[-\s]*nummer[\s:]*(\d{6})\b',     # Notary association
        
        # Financial licenses and permits
        r'\bAFM[-\s]*vergunning[\s:]*(\d{8})\b', # Financial Markets Authority license
        r'\bDNB[-\s]*vergunning[\s:]*(\d{8})\b', # Dutch National Bank license
        r'\bWFT[-\s]*vergunning[\s:]*(\d{8})\b', # Financial Supervision Act license
        r'\bPENSIOEN[-\s]*nummer[\s:]*(\d{8})\b', # Pension fund registration
        r'\bVEROPS[-\s]*nummer[\s:]*(\d{6})\b',  # Insurance intermediary
        
        # Construction and building licenses
        r'\bBRL[-\s]*certificaat[\s:]*(\d{6})\b', # Building regulation certificate
        r'\bKVK[-\s]*bouw[\s:]*(\d{8})\b',       # Construction company registration
        r'\bSNEL[-\s]*certificaat[\s:]*(\d{7})\b', # Construction certification
        r'\bBOUW[-\s]*vergunning[\s:]*(\d{8})\b', # Building permit
        r'\bVCA[-\s]*certificaat[\s:]*(\d{8})\b', # Safety certification
        
        # Transport and logistics
        r'\bCEMT[-\s]*vergunning[\s:]*(\d{6})\b', # European transport permit
        r'\bNIWO[-\s]*nummer[\s:]*(\d{8})\b',    # Road transport organization
        r'\bTLN[-\s]*nummer[\s:]*(\d{7})\b',     # Transport and logistics Nederland
        r'\bVERVOER[-\s]*vergunning[\s:]*(\d{8})\b', # Transport permit
        r'\bTAXI[-\s]*vergunning[\s:]*(\d{6})\b', # Taxi permit
        
        # Healthcare and medical
        r'\bAGB[-\s]*code[\s:]*(\d{8})\b',       # Healthcare provider code
        r'\bUZI[-\s]*nummer[\s:]*(\d{8})\b',     # Healthcare professional card
        r'\bBIG[-\s]*nummer[\s:]*(\d{8})\b',     # Healthcare professional registration
        r'\bGGZ[-\s]*nummer[\s:]*(\d{6})\b',     # Mental health care registration
        r'\bZORG[-\s]*nummer[\s:]*(\d{8})\b',    # Care provider registration
        r'\bFARMA[-\s]*nummer[\s:]*(\d{6})\b',   # Pharmacy registration
        
        # Agriculture and food safety
        r'\bKDV[-\s]*nummer[\s:]*(\d{6})\b',     # Animal health service
        r'\bGGN[-\s]*nummer[\s:]*(\d{13})\b',    # GlobalGAP number
        r'\bNEVA[-\s]*nummer[\s:]*(\d{8})\b',    # Food safety authority
        r'\bBIO[-\s]*certificaat[\s:]*(\d{6})\b', # Organic certification
        r'\bHACCP[-\s]*certificaat[\s:]*(\d{8})\b', # Food safety certification
        
        # Environmental and energy permits
        r'\bETS[-\s]*nummer[\s:]*(\d{8})\b',     # Emission trading system
        r'\bEMISSIE[-\s]*vergunning[\s:]*(\d{8})\b', # Emission permit
        r'\bAFVAL[-\s]*vergunning[\s:]*(\d{8})\b', # Waste management permit
        r'\bENERGIE[-\s]*vergunning[\s:]*(\d{8})\b', # Energy permit
        r'\bMILIEU[-\s]*vergunning[\s:]*(\d{8})\b', # Environmental permit
        
        # Telecommunications and digital
        r'\bACM[-\s]*vergunning[\s:]*(\d{8})\b', # Consumer and market authority telecom
        r'\bTELECOM[-\s]*vergunning[\s:]*(\d{8})\b', # Telecommunications permit
        r'\bFREQUENTIE[-\s]*vergunning[\s:]*(\d{6})\b', # Frequency allocation
        r'\bINTERNET[-\s]*provider[\s:]*(\d{6})\b', # Internet service provider
        
        # Customs and international trade
        r'\bEORI[-\s]*nummer[\s:]*([A-Z]{2}\d{12})\b', # Economic Operator Registration
        r'\bAEO[-\s]*certificaat[\s:]*(\d{8})\b',   # Authorized Economic Operator
        r'\bINTRAST[-\s]*nummer[\s:]*(\d{8})\b',    # Intrastat declaration number
        r'\bDOUANE[-\s]*nummer[\s:]*(\d{8})\b',     # Customs registration
        
        # Intellectual property
        r'\bBIE[-\s]*nummer[\s:]*(\d{8})\b',        # Patent office registration (Benelux)
        r'\bMERK[-\s]*nummer[\s:]*(\d{6})\b',       # Trademark registration
        r'\bOCTROOI[-\s]*nummer[\s:]*(\d{8})\b',    # Patent number
        r'\bAUTEURS[-\s]*recht[\s:]*(\d{6})\b',     # Copyright registration
        
        # Social enterprises and charities
        r'\bANBI[-\s]*nummer[\s:]*(\d{8})\b',       # Public benefit organization
        r'\bSBBI[-\s]*nummer[\s:]*(\d{8})\b',       # Social benefit organization  
        r'\bCBF[-\s]*keur[\s:]*(\d{6})\b',          # Charity certification
        r'\bGOEDE[-\s]*doelen[\s:]*(\d{6})\b',      # Charitable organization
        
        # Employee and HR identifiers
        r'\b(?:personeelsnummer|employee\s+number|medewerker\s+nummer)(?:[:\s#-]+)?(\d{4,8})\b',
        r'\b(?:loonnummer|salary\s+number)(?:[:\s#-]+)?(\d{4,8})\b',
        r'\b(?:contractnummer|contract\s+number)(?:[:\s#-]+)?([A-Z0-9]{6,12})\b',
        r'\bWERKNEMER[-\s]*nummer[\s:]*(\d{6,8})\b',
        r'\bBANK[-\s]*machtiging[\s:]*([A-Z0-9]{8,15})\b', # Direct debit authorization
        
        # Project and tender identifiers
        r'\bAANBESTEDING[-\s]*nummer[\s:]*([A-Z0-9]{8,12})\b', # Tender number
        r'\bPROJECT[-\s]*nummer[\s:]*([A-Z0-9]{6,10})\b',      # Project number
        r'\bOFFERTE[-\s]*nummer[\s:]*([A-Z0-9]{6,12})\b',      # Quote number
        r'\bFACTUUR[-\s]*nummer[\s:]*([A-Z0-9]{6,12})\b',      # Invoice number
        
        # Quality and compliance certifications
        r'\bISO[-\s]*certificaat[\s:]*(\d{4,5})\b',    # ISO certification
        r'\bKWALITEIT[-\s]*certificaat[\s:]*(\d{6})\b', # Quality certificate
        r'\bVEILIGHEID[-\s]*certificaat[\s:]*(\d{8})\b', # Safety certificate
        r'\bMVO[-\s]*certificaat[\s:]*(\d{6})\b',      # CSR certificate
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = match.group(1) if match.lastindex else match.group(0)
            
            # Determine business identifier type for precise classification
            business_type = "Dutch Business Identifier"
            description = "Netherlands business identification"
            risk_level = "Medium"
            
            if "BTW" in match.group(0) or "VAT" in match.group(0) or ("NL" in value and "B" in value):
                business_type = "VAT Number"
                description = "Netherlands tax identification number"
                risk_level = "High"
            elif "RSIN" in match.group(0):
                business_type = "RSIN Number"
                description = "Legal Entity Identification Number"
                risk_level = "High"
            elif "KvK" in match.group(0) or "Handelsregister" in match.group(0) or "Chamber" in match.group(0):
                business_type = "Chamber of Commerce Number"
                description = "Official Dutch business registration"
                risk_level = "High"
            elif "IBAN" in match.group(0) or (len(value) == 18 and value.startswith("NL")):
                business_type = "Dutch IBAN"
                description = "Netherlands bank account number"
                risk_level = "High"
            elif "BV" in match.group(0) or "NV" in match.group(0) or "EENMANSZAAK" in match.group(0):
                business_type = "Corporate Entity Number"
                description = "Dutch corporation identifier"
                risk_level = "High"
            elif "AFM" in match.group(0) or "DNB" in match.group(0) or "WFT" in match.group(0):
                business_type = "Financial License"
                description = "Financial services authorization"
                risk_level = "High"
            elif "AGB" in match.group(0) or "BIG" in match.group(0) or "UZI" in match.group(0):
                business_type = "Healthcare Provider ID"
                description = "Healthcare professional registration"
                risk_level = "High"
            elif "NOVA" in match.group(0) or "NRO" in match.group(0) or "REA" in match.group(0):
                business_type = "Professional License"
                description = "Professional services registration"
                risk_level = "High"
            elif "SBI" in match.group(0) or "NACE" in match.group(0):
                business_type = "Industry Code"
                description = "Business industry classification"
            elif "EORI" in match.group(0):
                business_type = "EU Trade Number"
                description = "European customs identifier"
                risk_level = "High"
            elif "ANBI" in match.group(0) or "CBF" in match.group(0):
                business_type = "Charity Registration"
                description = "Non-profit organization identifier"
            elif "personeelsnummer" in match.group(0) or "employee" in match.group(0):
                business_type = "Employee Number"
                description = "Staff identification number"
                risk_level = "High"
            elif "loonnummer" in match.group(0) or "salary" in match.group(0):
                business_type = "Payroll Number"
                description = "Salary administration identifier"
                risk_level = "High"
            
            found.append({
                'type': business_type,
                'value': value,
                'description': description,
                'risk_level': risk_level
            })
    
    return found


def _find_dutch_health_insurance(text: str) -> List[Dict[str, Any]]:
    """Find Dutch health insurance related identifiers."""
    patterns = [
        # Health insurance number
        r'\b(?:zorgverzekeringsnummer|health\s+insurance\s+number)(?:[:\s#-]+)?(\d{8,10})\b',
        
        # AGB code (healthcare provider code)
        r'\b(?:AGB|agb)[-\s]*(?:code|nummer)?[\s:]*(\d{8})\b',
        
        # UZI number (healthcare professional ID)
        r'\b(?:UZI|uzi)[-\s]*(?:nummer|number)?[\s:]*(\d{8})\b',
        
        # DBC code (diagnosis treatment combination)
        r'\b(?:DBC|dbc)[-\s]*(?:code|nummer)?[\s:]*(\d{6})\b',
        
        # Dutch medical record number
        r'\b(?:dossier|medical\s+record)(?:[:\s#-]+)?(\d{6,10})\b',
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = match.group(1) if match.lastindex else match.group(0)
            found.append({
                'type': 'Dutch Health Insurance ID',
                'value': value,
                'description': 'Netherlands health insurance identifier'
            })
    
    return found


def _find_dutch_bank_codes(text: str) -> List[Dict[str, Any]]:
    """Find Dutch bank-specific codes and identifiers."""
    found = []

    bic_pattern = r'\b(?:ABNA|INGB|RABO|BUNQ|TRIO|KABA|BNPA|DEUT)NL2[A-Z0-9]\b'
    for match in re.finditer(bic_pattern, text):
        found.append({
            'type': 'Dutch Bank Code',
            'value': match.group(0),
            'description': 'Netherlands BIC/SWIFT code'
        })

    tx_pattern = r'\b(?:transactie|transaction)[\s:=#-]+(\d[A-Z0-9]{12,15})\b'
    for match in re.finditer(tx_pattern, text, re.IGNORECASE):
        value = match.group(1)
        if sum(c.isdigit() for c in value) >= 6:
            found.append({
                'type': 'Dutch Bank Code',
                'value': value,
                'description': 'Netherlands transaction reference'
            })

    ideal_pattern = r'\b(?:iDEAL|ideal)[\s:=#-]+(\d[A-Z0-9]{15})\b'
    for match in re.finditer(ideal_pattern, text, re.IGNORECASE):
        value = match.group(1)
        if sum(c.isdigit() for c in value) >= 8:
            found.append({
                'type': 'Dutch Bank Code',
                'value': value,
                'description': 'iDEAL transaction ID'
            })

    mandate_pattern = r'\b(?:incassomachtiging)[\s:=#-]+([A-Z0-9]{8,15})\b'
    for match in re.finditer(mandate_pattern, text, re.IGNORECASE):
        found.append({
            'type': 'Dutch Bank Code',
            'value': match.group(1),
            'description': 'Netherlands direct debit mandate'
        })

    return found


def _find_dutch_regional_identifiers(text: str) -> List[Dict[str, Any]]:
    """Find Dutch regional and provincial identifiers."""
    patterns = [
        # Provincial identifiers
        r'\bNOORD[-\s]*HOLLAND[-\s]*(\d{4,8})\b',    # North Holland
        r'\bZUID[-\s]*HOLLAND[-\s]*(\d{4,8})\b',     # South Holland  
        r'\bUTRECHT[-\s]*(\d{4,8})\b',              # Utrecht province
        r'\bGELDERLAND[-\s]*(\d{4,8})\b',           # Gelderland
        r'\bOVERIJSSEL[-\s]*(\d{4,8})\b',           # Overijssel
        r'\bFLEVOLAND[-\s]*(\d{4,8})\b',            # Flevoland
        r'\bNOORD[-\s]*BRABANT[-\s]*(\d{4,8})\b',    # North Brabant
        r'\bZEELAND[-\s]*(\d{4,8})\b',              # Zeeland
        r'\bLIMBURG[-\s]*(\d{4,8})\b',              # Limburg
        r'\bFRIESLAND[-\s]*(\d{4,8})\b',            # Friesland
        r'\bDRENTHE[-\s]*(\d{4,8})\b',              # Drenthe
        r'\bGRONINGEN[-\s]*(\d{4,8})\b',            # Groningen
        
        # Regional service identifiers
        r'\bGGD[-\s]*(\d{4,6})\b',                  # Regional health service
        r'\bWATERSCHAP[-\s]*(\d{4,6})\b',           # Water board
        r'\bVEILIGHEIDSREGIO[-\s]*(\d{2,3})\b',     # Safety region
        r'\bRPA[-\s]*(\d{4,6})\b',                  # Regional police authority
        
        # Municipal service codes
        r'\bGEMEENTE[-\s]*(\d{4,8})\b',             # Municipality code
        r'\bBURGER[-\s]*service[-\s]*(\d{4,8})\b',   # Citizen service number
        r'\bWONING[-\s]*(\d{6,10})\b',              # Housing identifier
        r'\bUITKERING[-\s]*(\d{6,10})\b',           # Social benefit number
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = match.group(1) if match.lastindex else match.group(0)
            
            # Determine regional identifier type
            region_type = "Dutch Regional Identifier"
            description = "Netherlands regional service identifier"
            
            if "GEMEENTE" in match.group(0):
                region_type = "Municipality Code"
                description = "Dutch municipality service identifier"
            elif "WATERSCHAP" in match.group(0):
                region_type = "Water Board ID"
                description = "Dutch water management authority"
            elif "GGD" in match.group(0):
                region_type = "Health Service ID"
                description = "Regional health authority identifier"
            
            found.append({
                'type': region_type,
                'value': value,
                'description': description,
                'risk_level': 'Medium'
            })
    
    return found


def _find_dutch_educational_identifiers(text: str) -> List[Dict[str, Any]]:
    """Find Dutch educational system identifiers."""
    patterns = [
        # Student identification
        r'\bSTUDENT[-\s]*nummer[-\s]*(\d{6,10})\b',   # Student number
        r'\bONDERWIJS[-\s]*nummer[-\s]*(\d{8,12})\b', # Education number
        r'\bDUO[-\s]*nummer[-\s]*(\d{8,10})\b',       # Education service number
        
        # Educational certificates
        r'\bDIPLOMA[-\s]*nummer[-\s]*([A-Z0-9]{8,12})\b', # Diploma number
        r'\bCERTIFICAT[-\s]*nummer[-\s]*([A-Z0-9]{6,10})\b', # Certificate number
        r'\bEXAMEN[-\s]*nummer[-\s]*(\d{6,10})\b',     # Exam number
        
        # Student financial aid
        r'\bSTUDIE[-\s]*financiering[-\s]*(\d{8,10})\b', # Student finance
        r'\bBEURS[-\s]*nummer[-\s]*(\d{6,10})\b',      # Grant/scholarship number
        r'\bLEENING[-\s]*nummer[-\s]*(\d{8,12})\b',    # Student loan number
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = match.group(1) if match.lastindex else match.group(0)
            
            edu_type = "Dutch Educational ID"
            description = "Netherlands education system identifier"
            risk_level = "Medium"
            
            if "STUDENT" in match.group(0):
                edu_type = "Student Number"
                description = "Dutch student identification number"
                risk_level = "High"
            elif "FINANCIERING" in match.group(0) or "BEURS" in match.group(0):
                edu_type = "Student Finance ID"
                description = "Dutch student financial aid identifier"
                risk_level = "High"
            
            found.append({
                'type': edu_type,
                'value': value,
                'description': description,
                'risk_level': risk_level
            })
    
    return found


def _find_dutch_municipal_services(text: str) -> List[Dict[str, Any]]:
    """Find Dutch municipal and local government service identifiers."""
    patterns = [
        # Citizen services
        r'\bBURGER[-\s]*zaken[-\s]*(\d{6,10})\b',     # Citizen affairs
        r'\bPASSPOORT[-\s]*aanvraag[-\s]*(\d{8,12})\b', # Passport application
        r'\bUTTREKSEL[-\s]*BRP[-\s]*(\d{8,12})\b',    # Personal records extract
        
        # Municipal permits and licenses
        r'\bBOUW[-\s]*vergunning[-\s]*(\d{6,10})\b',  # Building permit
        r'\bEVENEMENT[-\s]*vergunning[-\s]*(\d{6,10})\b', # Event permit
        r'\bHORECA[-\s]*vergunning[-\s]*(\d{6,10})\b', # Hospitality license
        
        # Municipal taxation
        r'\bOZB[-\s]*nummer[-\s]*(\d{8,12})\b',       # Property tax (OZB)
        r'\bRIOOL[-\s]*heffing[-\s]*(\d{6,10})\b',    # Sewerage charge
        r'\bAFVAL[-\s]*heffing[-\s]*(\d{6,10})\b',    # Waste collection charge
        
        # Municipal registrations
        r'\bVERHUIZING[-\s]*(\d{8,12})\b',            # Change of address
        r'\bGEBOORTE[-\s]*akte[-\s]*(\d{6,10})\b',    # Birth certificate
        r'\bHUWELIJK[-\s]*akte[-\s]*(\d{6,10})\b',    # Marriage certificate
    ]
    
    found = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = match.group(1) if match.lastindex else match.group(0)
            
            service_type = "Dutch Municipal Service ID"
            description = "Netherlands municipal service identifier"
            risk_level = "Medium"
            
            if "BURGER" in match.group(0) or "PASPOORT" in match.group(0):
                service_type = "Citizen Service ID"
                description = "Dutch citizen service identifier"
                risk_level = "High"
            elif "AKTE" in match.group(0):
                service_type = "Civil Registry Document"
                description = "Dutch civil registration identifier"
                risk_level = "High"
            
            found.append({
                'type': service_type,
                'value': value,
                'description': description,
                'risk_level': risk_level
            })
    
    return found


def _enhance_dutch_context_analysis(pii_items: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
    """Apply ML-enhanced context analysis for Dutch PII detection."""
    
    # Dutch legal context keywords for enhanced risk assessment
    high_risk_contexts = [
        'patiënt', 'klant', 'burger', 'persoonlijk', 'vertrouwelijk',
        'geheim', 'privé', 'medisch', 'financieel', 'juridisch'
    ]
    
    # Dutch GDPR-specific terms
    gdpr_contexts = [
        'AVG', 'UAVG', 'privacyverklaring', 'toestemming', 'verwerkingsovereenkomst',
        'privacy by design', 'privacy by default', 'persoonsgegevens'
    ]
    
    enhanced_items = []
    text_lower = text.lower()
    
    for item in pii_items:
        # Create enhanced copy of the item
        enhanced_item = item.copy()
        
        # Get surrounding context (100 characters before and after)
        item_value = str(item.get('value', ''))
        if item_value in text:
            start_pos = text.find(item_value)
            context_start = max(0, start_pos - 100)
            context_end = min(len(text), start_pos + len(item_value) + 100)
            context = text[context_start:context_end].lower()
            
            # Analyze context for risk enhancement
            original_risk = item.get('risk_level', 'Medium')
            
            # Check for high-risk context
            if any(keyword in context for keyword in high_risk_contexts):
                if original_risk == 'Medium':
                    enhanced_item['risk_level'] = 'High'
                enhanced_item['context_enhancement'] = 'High-risk context detected'
            
            # Check for GDPR-specific context
            if any(keyword in context for keyword in gdpr_contexts):
                enhanced_item['gdpr_context'] = True
                enhanced_item['compliance_note'] = 'GDPR/UAVG context detected - requires special handling'
            
            # Netherlands-specific enhancements
            if item.get('type') == 'BSN':
                if any(term in context for term in ['patiënt', 'medisch', 'ziekenhuis']):
                    enhanced_item['special_category'] = 'Medical context - Article 9 GDPR/UAVG'
                    enhanced_item['risk_level'] = 'Critical'
        
        enhanced_items.append(enhanced_item)
    
    return enhanced_items
