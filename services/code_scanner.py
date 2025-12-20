import os
import re
import json
import math
import time
import hashlib
import threading
import multiprocessing
import subprocess
import signal
import logging

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("code_scanner")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set, Callable, Union
from utils.pii_detection import identify_pii_in_text
from utils.gdpr_rules import get_region_rules, evaluate_risk_level

# Configure logging

# Import Netherlands-specific detection module
try:
    from utils.netherlands_gdpr import detect_nl_violations
except ImportError:
    # Fallback if module not available
    def detect_nl_violations(content):
        return []

# Custom exception classes for better error handling
class ScannerError(Exception):
    """Base exception for code scanner errors"""
    pass

class CheckpointError(ScannerError):
    """Exception raised when checkpoint operations fail"""
    pass

class FileProcessingError(ScannerError):
    """Exception raised when file processing fails"""
    pass

class TimeoutError(ScannerError):
    """Exception raised when scan timeout is exceeded"""
    pass

class PatternCompilationError(ScannerError):
    """Exception raised when regex pattern compilation fails"""
    pass

class InvalidConfigurationError(ScannerError):
    """Exception raised when scanner configuration is invalid"""
    pass

class CodeScanner:
    """
    An advanced scanner that detects PII, secrets, and sensitive information in code files.
    Supports multiple languages and regulatory frameworks.
    """
    
    def __init__(self, extensions: Optional[List[str]] = None, include_comments: bool = True, 
                 region: str = "Netherlands", use_entropy: bool = True, 
                 use_git_metadata: bool = False, include_article_refs: bool = True,
                 max_timeout: int = 3600, checkpoint_interval: int = 300):
        """
        Initialize the code scanner with advanced detection capabilities.
        
        Args:
            extensions: List of file extensions to scan (e.g., ['.py', '.js'])
            include_comments: Whether to include comments in the scan
            region: The region for which to apply GDPR rules
            use_entropy: Whether to use entropy analysis for secret detection
            use_git_metadata: Whether to collect Git metadata for findings
            include_article_refs: Whether to include regulatory article references
            max_timeout: Maximum runtime in seconds before timeout (default: 1 hour)
            checkpoint_interval: Interval in seconds for saving scan checkpoints (default: 5 minutes)
        """
        # Long-running scan settings
        self.max_timeout = max_timeout
        self.checkpoint_interval = checkpoint_interval
        self.start_time = None
        self.scan_checkpoint_data = {}
        self.is_running = False
        self.progress_callback = None
        # Support for multiple languages
        self.extensions = extensions or [
            # Core programming languages
            '.py', '.pyw', '.pyx', '.pyi',  # Python
            '.js', '.jsx', '.mjs',          # JavaScript
            '.ts', '.tsx',                  # TypeScript
            '.java', '.jsp', '.jav',        # Java
            '.php', '.phtml',               # PHP
            '.rb', '.rhtml', '.erb',        # Ruby
            '.cs', '.cshtml', '.csx',       # C#
            '.go',                          # Go
            '.rs',                          # Rust
            '.c', '.cpp', '.cc', '.h',      # C/C++
            '.kt', '.kts',                  # Kotlin
            '.swift',                       # Swift
            
            # Infrastructure as Code
            '.tf', '.tfvars',               # Terraform
            '.yml', '.yaml',                # YAML
            '.json',                        # JSON
            '.xml',                         # XML
            
            # Web
            '.html', '.htm', '.xhtml',      # HTML
            '.css', '.scss', '.sass',       # CSS
            
            # Other
            '.sql',                         # SQL
            '.sh', '.bash',                 # Bash
            '.ps1', '.psm1',                # PowerShell
            '.env',                         # Environment files
            '.properties', '.conf', '.ini', # Config files
            '.md', '.txt'                   # Documentation
        ]
        
        self.include_comments = include_comments
        self.region = region
        self.region_rules = get_region_rules(region)
        self.use_entropy = use_entropy
        self.use_git_metadata = use_git_metadata
        self.include_article_refs = include_article_refs
        
        # Enhanced regex patterns for secrets and PII detection by provider
        # Fixed to prevent ReDoS attacks by simplifying complex quantifiers
        self.secret_patterns = {
            # General API keys and tokens - simplified to prevent ReDoS
            'api_key': r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([A-Za-z0-9_-]{20,64})["\']?',
            'auth_token': r'(?i)(auth[_-]?token|oauth|bearer|jwt)\s*[=:]\s*["\']?([A-Za-z0-9_.-]{30,64})["\']?',
            'generic_secret': r'(?i)(secret|key|token)\s*[=:]\s*["\']?([A-Za-z0-9_.-]{16,64})["\']?',
            
            # AWS - simplified patterns
            'aws_access_key': r'(?i)(aws_access_key_id|access_key)\s*[=:]\s*["\']?([A-Za-z0-9/+=]{16,40})["\']?',
            'aws_key_id': r'\b(AKIA[0-9A-Z]{16})\b',
            'aws_secret': r'(?i)(aws_secret_access_key|secret_key)\s*[=:]\s*["\']?([A-Za-z0-9/+=]{40})["\']?',
            
            # Azure - fixed patterns
            'azure_key': r'(?i)(azure_key|azure_token|azure_secret)\s*[=:]\s*["\']?([A-Za-z0-9+/=]{44})["\']?',
            'azure_connection': r'(DefaultEndpointsProtocol=https[^;]+AccountKey=)([A-Za-z0-9+/=]{88})',
            'azure_storage': r'(BlobEndpoint|QueueEndpoint|TableEndpoint|FileEndpoint)=https://[a-z0-9]+\.(blob|queue|table|file)\.core\.windows\.net/',
            
            # Google Cloud - simplified
            'gcp_api_key': r'\b(AIza[0-9A-Za-z_-]{35})\b',
            'gcp_service_account': r'"type":\s*"service_account"[^}]+?"private_key":\s*"([^"]+)"',
            
            # Payment processors - fixed patterns
            'stripe_key': r'\b(sk_(?:live|test)_[a-zA-Z0-9]{24})\b',
            'stripe_public_key': r'\b(pk_(?:live|test)_[a-zA-Z0-9]{24})\b',
            'paypal_key': r'\b(access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32})\b',
            'braintree_key': r'\b(access_token\$sandbox\$[0-9a-z]{16}\$[0-9a-f]{32})\b',
            
            # Database - simplified to prevent ReDoS
            'connection_string': r'(mongodb|mysql|postgresql|sqlserver)://[^:\s]+:[^@\s]+@[^/\s]+(?::[0-9]+)?',
            'mongodb_uri': r'mongodb(?:\+srv)?://[^:\s]+:[^@\s]+@[^/\s]+',
            'mysql_conn': r'mysql://[^:\s]+:[^@\s]+@[^/\s]+',
            'postgres_conn': r'postgres(?:ql)?://[^:\s]+:[^@\s]+@[^/\s]+',
            
            # Social media - simplified patterns
            'twitter_key': r'(?i)(twitter_api_key|twitter_token)\s*[=:]\s*["\']?([a-zA-Z0-9]{35,50})["\']?',
            'facebook_key': r'(?i)(facebook_app_secret|facebook_token)\s*[=:]\s*["\']?([a-zA-Z0-9]{32,40})["\']?',
            'github_token': r'\b(gh[pousr]_[a-zA-Z0-9_]{36})\b',
            
            # Passwords - simplified
            'password': r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']{8,32})["\']',
            'passwd_assignment': r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']{8,32})["\']'
        }
        
        # Map of file extensions to language-specific comment patterns
        self.comment_patterns = {
            # Python
            '.py': [r'#.*?$', r'""".*?"""', r"'''.*?'''"],
            '.pyw': [r'#.*?$', r'""".*?"""', r"'''.*?'''"],
            '.pyx': [r'#.*?$', r'""".*?"""', r"'''.*?'''"],
            '.pyi': [r'#.*?$', r'""".*?"""', r"'''.*?'''"],
            
            # JavaScript/TypeScript
            '.js': [r'//.*?$', r'/\*.*?\*/', r'<!--.*?-->'],
            '.jsx': [r'//.*?$', r'/\*.*?\*/', r'<!--.*?-->'],
            '.mjs': [r'//.*?$', r'/\*.*?\*/'],
            '.ts': [r'//.*?$', r'/\*.*?\*/'],
            '.tsx': [r'//.*?$', r'/\*.*?\*/', r'<!--.*?-->'],
            
            # Java
            '.java': [r'//.*?$', r'/\*.*?\*/'],
            '.jsp': [r'//.*?$', r'/\*.*?\*/', r'<!--.*?-->', r'<%--.*?--%>'],
            '.jav': [r'//.*?$', r'/\*.*?\*/'],
            
            # PHP
            '.php': [r'//.*?$', r'/\*.*?\*/', r'#.*?$', r'<!--.*?-->'],
            '.phtml': [r'//.*?$', r'/\*.*?\*/', r'#.*?$', r'<!--.*?-->'],
            
            # Ruby
            '.rb': [r'#.*?$', r'=begin.*?=end'],
            '.rhtml': [r'#.*?$', r'<!--.*?-->'],
            '.erb': [r'#.*?$', r'<%#.*?%>', r'<!--.*?-->'],
            
            # C#
            '.cs': [r'//.*?$', r'/\*.*?\*/'],
            '.cshtml': [r'//.*?$', r'/\*.*?\*/', r'<!--.*?-->'],
            '.csx': [r'//.*?$', r'/\*.*?\*/'],
            
            # Go
            '.go': [r'//.*?$', r'/\*.*?\*/'],
            
            # Rust
            '.rs': [r'//.*?$', r'/\*.*?\*/'],
            
            # C/C++
            '.c': [r'//.*?$', r'/\*.*?\*/'],
            '.cpp': [r'//.*?$', r'/\*.*?\*/'],
            '.cc': [r'//.*?$', r'/\*.*?\*/'],
            '.h': [r'//.*?$', r'/\*.*?\*/'],
            '.hpp': [r'//.*?$', r'/\*.*?\*/'],
            
            # Kotlin
            '.kt': [r'//.*?$', r'/\*.*?\*/'],
            '.kts': [r'//.*?$', r'/\*.*?\*/'],
            
            # Swift
            '.swift': [r'//.*?$', r'/\*.*?\*/'],
            
            # Terraform
            '.tf': [r'#.*?$', r'/\*.*?\*/'],
            '.tfvars': [r'#.*?$', r'/\*.*?\*/'],
            
            # YAML
            '.yml': [r'#.*?$'],
            '.yaml': [r'#.*?$'],
            
            # HTML/CSS
            '.html': [r'<!--.*?-->'],
            '.htm': [r'<!--.*?-->'],
            '.xhtml': [r'<!--.*?-->'],
            '.css': [r'/\*.*?\*/'],
            '.scss': [r'/\*.*?\*/', r'//.*?$'],
            '.sass': [r'/\*.*?\*/', r'//.*?$'],
            
            # SQL
            '.sql': [r'--.*?$', r'/\*.*?\*/'],
            
            # Bash
            '.sh': [r'#.*?$'],
            '.bash': [r'#.*?$'],
            
            # PowerShell
            '.ps1': [r'#.*?$', r'<#.*?#>'],
            '.psm1': [r'#.*?$', r'<#.*?#>'],
            
            # Config files
            '.env': [r'#.*?$'],
            '.properties': [r'#.*?$'],
            '.conf': [r'#.*?$'],
            '.ini': [r';.*?$'],
            
            # Documentation
            '.md': [r'<!--.*?-->'],
            '.txt': []
        }
        
        # AI Act compliance patterns for EU AI Act 2025 enforcement
        self.ai_act_patterns = {
            'ai_frameworks': [
                r'import\s+(tensorflow|torch|pytorch|sklearn|keras|transformers|huggingface)',
                r'from\s+(tensorflow|torch|pytorch|sklearn|keras|transformers|huggingface)',
                r'import\s+.*\b(tf|torch|nn|model|neural|network)\b',
                r'(TensorFlow|PyTorch|Keras|Scikit-learn|HuggingFace|OpenAI|Anthropic)'
            ],
            'prohibited_ai_practices': [
                r'(subliminal|manipulative|deceptive).*\b(ai|algorithm|model)\b',
                r'(social.*scoring|citizen.*scoring|behavioral.*scoring)',
                r'(emotion.*recognition|emotional.*ai|affect.*recognition)',
                r'(biometric.*identification|facial.*recognition|voice.*print)',
                r'(predictive.*policing|crime.*prediction|risk.*assessment)',
                r'(dark.*pattern|manipulation|exploitation).*\b(ai|ml|algorithm)\b'
            ],
            'high_risk_ai_systems': [
                r'(medical|healthcare|diagnostic).*\b(ai|ml|model|algorithm)\b',
                r'(autonomous|self.*driving|driverless).*\b(vehicle|car|transport)\b',
                r'(recruitment|hiring|employment).*\b(ai|algorithm|scoring)\b',
                r'(education|grading|assessment).*\b(ai|algorithm|automated)\b',
                r'(credit.*scoring|loan.*approval|financial.*ai)',
                r'(border.*control|immigration|visa).*\b(ai|automated)\b',
                r'(legal|judicial|court).*\b(ai|algorithm|automated.*decision)\b'
            ],
            'ai_training_patterns': [
                r'(train|training|fit|compile).*\b(model|neural|network|ai)\b',
                r'(dataset|training.*data|model.*training)',
                r'(epochs|batch.*size|learning.*rate|optimizer)',
                r'(model\.fit|model\.train|train_step|training_loop)',
                r'(loss.*function|cost.*function|objective.*function)'
            ],
            'ai_model_files': [
                r'\.(h5|pkl|pickle|joblib|model|weights|checkpoint|pb|pth|pt|onnx|tflite)$',
                r'(model|weights|checkpoint).*\.(json|yaml|yml|config)$',
                r'(trained.*model|saved.*model|model.*export)'
            ],
            'ai_transparency_requirements': [
                r'(explainability|interpretability|transparency).*\b(ai|model)\b',
                r'(bias.*detection|fairness.*testing|algorithmic.*audit)',
                r'(model.*documentation|ai.*documentation|algorithm.*description)',
                r'(human.*oversight|human.*review|manual.*override)',
                r'(ai.*impact.*assessment|algorithmic.*impact.*assessment)'
            ]
        }
        
        # Code Fraud Detection Patterns - Plagiarism, License Violations, IP Theft
        self.code_fraud_patterns = {
            'license_violations': [
                r'\b(GPL|GNU|LGPL|AGPL|MIT|Apache|BSD|MPL|CC[-\s]BY|Creative\s+Commons)\b',
                r'\b(copyleft|copyright|©|all\s+rights\s+reserved|proprietary)\b',
                r'\b(license|licensing|licensed\s+under|distributed\s+under)\b',
                r'\b(open[-\s]?source|closed[-\s]?source|commercial\s+use)\b'
            ],
            'attribution_missing': [
                r'\b(based\s+on|derived\s+from|forked\s+from|adapted\s+from|copied\s+from)\b',
                r'\b(original\s+author|credit|attribution|acknowledgment)\b',
                r'\b(stackoverflow|github|gitlab|bitbucket|gist)\s*[:/]',
                r'\b(source|origin|reference):\s*http[s]?://'
            ],
            'code_duplication_indicators': [
                r'#\s*(TODO|FIXME|XXX|HACK):\s*(remove|replace|original|copied)',
                r'//\s*(TODO|FIXME|XXX|HACK):\s*(remove|replace|original|copied)',
                r'/\*\s*(TODO|FIXME|XXX|HACK):\s*(remove|replace|original|copied)',
                r'\b(duplicate|duplicated|copy[-\s]?paste|plagiari[sz])',
                r'\b(temporary|temp|placeholder)\s+(code|implementation|solution)'
            ],
            'stolen_code_markers': [
                r'\b(stolen|pirated|cracked|keygen|nulled|warez)\b',
                r'\b(decompiled|reverse[-\s]?engineer|disassembl)',
                r'\b(bypass|crack|patch)\s+(license|activation|drm|protection)',
                r'\b(serial|registration)\s*(key|code|number)\s*[:=]',
                r'\b(license\s*key|product\s*key|activation\s*code)\s*[:=]\s*["\'][^"\']{8,}'
            ],
            'obfuscation_indicators': [
                r'\b(obfuscate[dr]?|minified|packed|encrypted\s+code)\b',
                r'eval\s*\(\s*["\'][A-Za-z0-9+/=]{50,}',  # Base64 eval
                r'\\x[0-9a-fA-F]{2}\\x[0-9a-fA-F]{2}\\x[0-9a-fA-F]{2}',  # Hex encoded
                r'String\.fromCharCode\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+',  # JS char codes
                r'_0x[a-fA-F0-9]{4,}',  # Obfuscated variable names
                r'\\u[0-9a-fA-F]{4}\\u[0-9a-fA-F]{4}\\u[0-9a-fA-F]{4}'  # Unicode escape
            ],
            'ip_theft_indicators': [
                r'\b(trade[-\s]?secret|proprietary\s+algorithm|confidential\s+code)\b',
                r'\b(intellectual\s+property|IP\s+theft|code\s+theft)\b',
                r'\b(non[-\s]?disclosure|NDA|confidential)\b.*\b(code|algorithm|implementation)\b',
                r'\b(competitor|competing|rival)\s+(code|product|implementation)'
            ],
            'backdoor_indicators': [
                r'\b(backdoor|rootkit|trojan|malware|keylogger)\b',
                r'\b(remote\s+access|shell\s+access|command\s+injection)\b',
                r'socket\.connect\s*\([^)]*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # Hardcoded IPs
                r'\b(reverse\s+shell|bind\s+shell|netcat|nc\s+-[lpe])',
                r'subprocess\.call\s*\(\s*["\'].*\b(sh|bash|cmd|powershell)\b'
            ],
            'copyright_infringement': [
                r'©\s*\d{4}(?:\s*-\s*\d{4})?\s+[A-Z][a-zA-Z\s]+',  # Copyright notices
                r'\b(all\s+rights\s+reserved|unauthorized.*prohibited)\b',
                r'\bpatent(?:ed|s)?\s*(?:pending|#|no\.?|number)',
                r'\b(trademark|®|™)\b',
                r'\b(proprietary|confidential|internal\s+use\s+only)\b'
            ],
            'license_compatibility_issues': [
                r'\b(GPL|AGPL)\b.*\b(proprietary|commercial|closed[-\s]?source)\b',
                r'\b(MIT|BSD|Apache)\b.*\b(GPL[-\s]?3|AGPL)\b.*\b(incompatible|conflict)\b',
                r'\blicense\s+(?:conflict|incompatib|violation)',
                r'\b(dual[-\s]?licens|relicens|sublicens)\b'
            ],
            'code_origin_suspicious': [
                r'\b(dark[-\s]?web|underground|black[-\s]?market)\b',
                r'\b(leaked|dump|breach).*\b(code|source|repository)\b',
                r'\b(unlicensed|unauthorized|illegal)\s+(copy|use|distribution)',
                r'\b(anonymous|unknown)\s+(?:author|source|origin)'
            ],
            'ai_generated_code': [
                # Direct AI attribution markers
                r'\b(generated\s+by|created\s+by|written\s+by)\s+(chatgpt|gpt[-\s]?[34]|openai|claude|anthropic|copilot|gemini|bard|llama|mistral)\b',
                r'\b(ai[-\s]?generated|llm[-\s]?generated|machine[-\s]?generated)\s+(code|function|class|script)\b',
                r'#\s*(chatgpt|gpt|copilot|claude|gemini|ai[-\s]?generated)',
                r'//\s*(chatgpt|gpt|copilot|claude|gemini|ai[-\s]?generated)',
                r'/\*\s*(chatgpt|gpt|copilot|claude|gemini|ai[-\s]?generated)',
                # AI assistant acknowledgment patterns
                r'\b(github\s+copilot|copilot\s+suggestion|copilot[-\s]?generated)\b',
                r'\b(cursor\s+ai|tabnine|codeium|amazon\s+codewhisperer)\b',
                # Common AI-generated comment patterns
                r'#\s*This\s+(code|function|class|method)\s+(was\s+)?generated',
                r'//\s*This\s+(code|function|class|method)\s+(was\s+)?generated',
                r'#\s*Auto[-\s]?generated\s+(by|using|with)',
                r'//\s*Auto[-\s]?generated\s+(by|using|with)'
            ],
            'ai_code_style_indicators': [
                # Overly verbose/explanatory comments typical of AI
                r'#\s*This\s+function\s+(takes|accepts|receives)\s+\w+\s+as\s+(a\s+)?parameter\s+and\s+(returns|outputs)',
                r'//\s*This\s+function\s+(takes|accepts|receives)\s+\w+\s+as\s+(a\s+)?parameter\s+and\s+(returns|outputs)',
                r'#\s*The\s+following\s+(code|implementation|function)\s+(will|does|is\s+used\s+to)',
                r'//\s*The\s+following\s+(code|implementation|function)\s+(will|does|is\s+used\s+to)',
                # AI-typical variable naming patterns
                r'\b(result_value|return_value|output_result|input_data|data_input)\b',
                r'\b(is_valid_\w+|has_\w+_property|should_\w+_be)\b.*\b(is_valid_\w+|has_\w+_property|should_\w+_be)\b',
                # Excessive docstring patterns
                r'"""[\s\S]{200,}?Args:[\s\S]+?Returns:[\s\S]+?Raises:[\s\S]+?Example:[\s\S]+?"""',
                # AI-typical error handling patterns
                r'except\s+Exception\s+as\s+e:\s*\n\s*#\s*Handle\s+(the\s+)?exception',
                r'catch\s*\(\s*error\s*\)\s*\{\s*//\s*Handle\s+(the\s+)?error',
                # AI placeholder patterns
                r'#\s*TODO:\s*(Implement|Add|Complete)\s+(the\s+)?(logic|functionality|implementation)\s+(here|below)',
                r'//\s*TODO:\s*(Implement|Add|Complete)\s+(the\s+)?(logic|functionality|implementation)\s+(here|below)',
                r'pass\s*#\s*(Placeholder|TODO|Not\s+implemented)',
                # Repetitive structure patterns
                r'def\s+\w+\([^)]*\):\s*\n\s*"""[^"]+"""\s*\n\s*#\s*\w+',
                # AI-typical print/log statements
                r'print\s*\(\s*f?["\'](?:Starting|Processing|Completed|Finished|Error occurred)',
                r'console\.log\s*\(\s*["\'](?:Starting|Processing|Completed|Finished|Error occurred)'
            ],
            'ai_code_patterns_advanced': [
                # Uniform formatting typical of AI
                r'(?:def\s+\w+\([^)]*\):\s*\n\s*""".+?"""\s*\n){3,}',  # Multiple similar docstrings
                # AI-typical import organization
                r'^import\s+\w+\s*\n(?:import\s+\w+\s*\n){5,}',  # Many single imports
                # Standard AI boilerplate
                r'if\s+__name__\s*==\s*["\']__main__["\']\s*:\s*\n\s*#\s*(Run|Execute|Start)',
                # AI-generated test patterns
                r'def\s+test_\w+\([^)]*\):\s*\n\s*"""Test\s+(that|if|whether)',
                r'it\s*\(\s*["\']should\s+\w+',  # Jest/Mocha style
                # Excessive type hints (AI loves these)
                r'def\s+\w+\([^)]*:\s*\w+(?:\s*,\s*\w+\s*:\s*\w+){4,}[^)]*\)\s*->\s*\w+',
                # AI attribution in docstrings
                r'"""[\s\S]*?(generated|created|written)\s+by\s+(an?\s+)?(AI|LLM|language\s+model)[\s\S]*?"""',
                r"'''[\s\S]*?(generated|created|written)\s+by\s+(an?\s+)?(AI|LLM|language\s+model)[\s\S]*?'''",
                # Suspiciously perfect code comments ratio
                r'(?:#[^\n]+\n[^\n#]+\n){5,}',  # Alternating comments and code
                # AI hallucination patterns (common mistakes)
                r'import\s+(?:fake_module|nonexistent_lib|placeholder_package)\b',
                r'from\s+\w+\s+import\s+\w+\s*#\s*(?:May|Might)\s+not\s+exist'
            ]
        }
        
        # UAVG (Dutch GDPR implementation) specific compliance patterns
        self.uavg_patterns = {
            'bsn_numbers': [
                r'\b(BSN|Burgerservicenummer|sofi[-\s]?nummer)(?:[:\s-]+)?(\d{9})\b',
                r'\b(BSN|Burgerservicenummer|sofi[-\s]?nummer)(?:[:\s-]+)?(\d{3}[-\s]\d{3}[-\s]\d{3})\b',
                r'\b(\d{9})\b(?=.*(?:BSN|burger|citizen|persoon))'
            ],
            'dutch_medical_data': [
                r'\b(medisch(?:e)?|patiënt(?:en)?|diagnos(?:e|tisch)|behandeling|gezondheid(?:s)?)\b',
                r'\b(ziekenhuis|huisarts|specialist|UMC|zorg(?:verlener)?|apotheek)\b',
                r'\b(elektronisch\s+patiëntendossier|EPD|zorgverlening|medische\s+gegevens)\b',
                r'\b(DigiD|medicijnen|behandelplan|zorgverzekeraar)\b'
            ],
            'dutch_personal_identifiers': [
                r'\b(paspoort(?:nummer)?|rijbewijs(?:nummer)?|identiteitskaart)\b',
                r'\b(Nederlandse\s+nationaliteit|Nederlands\s+staatsburgerschap)\b',
                r'\b(GBA|BRP|basisregistratie\s+personen)\b',
                r'\b(postcode|huisnummer|adres(?:gegevens)?)\s*[:\s]*[0-9]{4}\s*[A-Z]{2}\b'
            ],
            'dutch_financial_identifiers': [
                r'\b(IBAN\s*[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}[A-Z0-9]{0,16})\b',
                r'\b(bank(?:rekening)?(?:nummer)?|rekeningnummer|BIC|SWIFT)\b',
                r'\b(belasting(?:nummer)?|BTW[-\s]?nummer|fiscaal\s+nummer)\b',
                r'\b(ABN\s+AMRO|ING\s+Bank|Rabobank|SNS\s+Bank)\b'
            ],
            'dutch_employment_data': [
                r'\b(werknemers(?:nummer)?|personeelsnummer|UWV|WW[-\s]?uitkering)\b',
                r'\b(CAO|arbeidscontract|salaris(?:administratie)?|loonstrook)\b',
                r'\b(ziekteverzuim|arbeidsongeschiktheid|pensioen(?:regeling)?)\b'
            ],
            'dutch_education_data': [
                r'\b(onderwijsnummer|studentnummer|leerlingnummer|diplomanummer)\b',
                r'\b(onderwijsinstelling|school(?:gegevens)?|studieresultaten)\b',
                r'\b(DUO|studiefinanciering|onderwijsloopbaan)\b'
            ],
            'dutch_minors_consent': [
                r'\b(leeftijd(?:s)?verificatie|leeftijd(?:s)?check|16\s*jaar)\b',
                r'\b(onder|jonger\s+dan)\s+(?:16|zestien)\s+jaar\b',
                r'\b(ouderlijke\s+toestemming|toestemming\s+van\s+ouders|minderjarig)\b',
                r'\b(wettelijke\s+vertegenwoordiger|voogd(?:ij)?)\b'
            ],
            'dutch_legal_basis': [
                r'\b(gerechtvaardigd\s+belang|toestemming|wettelijke\s+verplichting)\b',
                r'\b(vitaal\s+belang|openbaar\s+belang|uitvoering\s+overeenkomst)\b',
                r'\b(UAVG|Uitvoeringswet|AVG|gegevensbescherming)\b',
                r'\b(Autoriteit\s+Persoonsgegevens|AP|privacy(?:beleid)?)\b'
            ]
        }
        
        # Pre-compile regex patterns to improve performance and catch compilation errors early
        self.compiled_patterns = {}
        self.compiled_comment_patterns = {}
        self.compiled_ai_patterns = {}
        self._compile_patterns()
        
        # Regulatory frameworks mapped to article references
        self.regulatory_refs = {
            "GDPR (EU)": {
                "PII": "Art. 4(1)",
                "Sensitive Data": "Art. 9",
                "Data Processing": "Art. 6",
                "Children's Data": "Art. 8",
                "Data Subject Rights": "Art. 15-22",
                "Security": "Art. 32",
                "Consent": "Art. 7"
            },
            "UAVG (NL)": {
                "BSN": "Art. 46",
                "Criminal Data": "Art. 31-33",
                "Health Data": "Art. 30",
                "Data for Research": "Art. 43-47",
                "Special Categories": "Art. 22-30"
            },
            "BDSG (DE)": {
                "Employee Data": "§26",
                "Credit Scoring": "§31",
                "Video Surveillance": "§4",
                "Special Categories": "§22",
                "Automated Decisions": "§37"
            },
            "CNIL (FR)": {
                "Health Data": "Articles L1111-7 and L1111-8 of the Public Health Code",
                "Biometric Data": "Deliberation No. 2019-001",
                "Financial Data": "Deliberation No. 2018-303"
            },
            "DPA (UK)": {
                "PII": "Section 3",
                "Special Categories": "Section 10",
                "Criminal Data": "Section 11",
                "Automated Decisions": "Section 14"
            }
        }
        
        # Known providers patterns for API keys and secrets
        self.known_providers = {
            "AWS": [
                r'AKIA[0-9A-Z]{16}',
                r'aws_access_key_id',
                r'aws_secret_access_key'
            ],
            "Azure": [
                r'DefaultEndpointsProtocol=https',
                r'AccountKey=',
                r'StorageAccountKey=',
                r'azure_storage_key',
                r'azure_connection_string'
            ],
            "GCP": [
                r'AIza[0-9A-Za-z\-_]{35}',
                r'"type": "service_account"',
                r'GOOG[0-9A-Za-z\-_]{32}'
            ],
            "Stripe": [
                r'sk_live_[0-9a-zA-Z]{24}',
                r'pk_live_[0-9a-zA-Z]{24}',
                r'sk_test_[0-9a-zA-Z]{24}',
                r'pk_test_[0-9a-zA-Z]{24}'
            ],
            "GitHub": [
                r'gh[pousr]_[a-zA-Z0-9_]{36}',
                r'github_token',
                r'GITHUB_TOKEN'
            ],
            "Twilio": [
                r'SK[0-9a-fA-F]{32}',
                r'AC[a-zA-Z0-9]{32}',
                r'twilio_account_sid',
                r'twilio_auth_token'
            ],
            "SendGrid": [
                r'SG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43}',
                r'sendgrid_api_key'
            ],
            "MailChimp": [
                r'[0-9a-f]{32}-us[0-9]{1,2}',
                r'mailchimp_api_key'
            ],
            "Slack": [
                r'xox[baprs]-[0-9]{12}-[0-9]{12}-[0-9a-zA-Z]{24}',
                r'slack_token',
                r'slack_api_token'
            ],
            "NPM": [
                r'npm_[0-9a-zA-Z]{36}',
                r'NPM_TOKEN'
            ],
            "Heroku": [
                r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
                r'heroku_api_key'
            ],
            "Facebook": [
                r'EAACEdEose0cBA[0-9A-Za-z]+',
                r'[A-Za-z0-9]{30,}',
                r'facebook_client_secret'
            ]
        }
        
    def _compile_patterns(self):
        """
        Pre-compile all regex patterns to improve performance and catch compilation errors early.
        Raises PatternCompilationError if any pattern fails to compile.
        """
        # Compile secret detection patterns
        for name, pattern in self.secret_patterns.items():
            try:
                self.compiled_patterns[name] = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            except re.error as e:
                raise PatternCompilationError(f"Failed to compile pattern '{name}': {e}")
        
        # Compile comment patterns for each file extension
        for ext, patterns in self.comment_patterns.items():
            compiled_ext_patterns = []
            for pattern in patterns:
                try:
                    compiled_ext_patterns.append(re.compile(pattern, re.MULTILINE | re.DOTALL))
                except re.error as e:
                    logger.warning(f"Failed to compile comment pattern for {ext}: {e}")
            self.compiled_comment_patterns[ext] = compiled_ext_patterns
        
        # Compile AI Act patterns
        for category, patterns in self.ai_act_patterns.items():
            compiled_category_patterns = []
            for pattern in patterns:
                try:
                    compiled_category_patterns.append(re.compile(pattern, re.IGNORECASE | re.MULTILINE))
                except re.error as e:
                    logger.warning(f"Failed to compile AI Act pattern for {category}: {e}")
            self.compiled_ai_patterns[category] = compiled_category_patterns
        
        # Compile UAVG (Dutch GDPR) patterns
        self.compiled_uavg_patterns = {}
        for category, patterns in self.uavg_patterns.items():
            compiled_category_patterns = []
            for pattern in patterns:
                try:
                    compiled_category_patterns.append(re.compile(pattern, re.IGNORECASE | re.MULTILINE))
                except re.error as e:
                    logger.warning(f"Failed to compile UAVG pattern for {category}: {e}")
            self.compiled_uavg_patterns[category] = compiled_category_patterns
        
        # Compile Code Fraud Detection patterns
        self.compiled_code_fraud_patterns = {}
        for category, patterns in self.code_fraud_patterns.items():
            compiled_category_patterns = []
            for pattern in patterns:
                try:
                    compiled_category_patterns.append(re.compile(pattern, re.IGNORECASE | re.MULTILINE))
                except re.error as e:
                    logger.warning(f"Failed to compile code fraud pattern for {category}: {e}")
            self.compiled_code_fraud_patterns[category] = compiled_category_patterns
        
        logger.info(f"Successfully compiled {len(self.compiled_patterns)} secret patterns, {len(self.compiled_comment_patterns)} comment patterns, {len(self.compiled_ai_patterns)} AI Act patterns, {len(self.compiled_uavg_patterns)} UAVG patterns, and {len(self.compiled_code_fraud_patterns)} code fraud patterns")
        
    def set_progress_callback(self, callback_function: Optional[Callable[[int, int, str], None]]):
        """
        Set a callback function to report progress during long-running scans.
        
        Args:
            callback_function: Function that takes (current_progress, total_files, current_file_name)
        """
        self.progress_callback = callback_function
        
    def scan_directory(self, directory_path: str, progress_callback=None, 
                      ignore_patterns=None, max_file_size_mb=50, 
                      continue_from_checkpoint=False, 
                      smart_sampling=True, 
                      max_files_to_scan=1000) -> Dict[str, Any]:
        """
        Scan a directory of files with timeout protection, checkpoints and smart sampling.
        
        Args:
            directory_path: Path to the directory to scan
            progress_callback: Optional callback to report progress
            ignore_patterns: List of glob patterns to ignore
            max_file_size_mb: Max file size to scan in MB
            continue_from_checkpoint: Whether to continue from last checkpoint if available
            smart_sampling: Whether to use smart sampling for large repositories
            max_files_to_scan: Maximum number of files to scan in a large repository
            
        Returns:
            Dictionary containing scan results
        """
        if progress_callback:
            self.progress_callback = progress_callback
            
        # Setup for long-running scan
        self.start_time = datetime.now()
        self.is_running = True
        scan_id = hashlib.md5(f"{directory_path}:{self.start_time.isoformat()}".encode()).hexdigest()[:10]
        
        # Prepare checkpoint file path
        checkpoint_path = f"scan_checkpoint_{scan_id}.json"
        
        # Initialize or restore checkpoint data
        self._setup_checkpoint(continue_from_checkpoint, checkpoint_path, scan_id, directory_path)
        
        # Compile ignore patterns
        ignore_regexes = self._compile_ignore_patterns(ignore_patterns)
        
        # Discover and filter files
        all_files, total_file_count = self._discover_files(
            directory_path, ignore_regexes, max_file_size_mb
        )
        
        # Set up multiprocessing pool for parallel scanning - use more workers for performance
        num_workers = max(2, multiprocessing.cpu_count())  # Use all available CPUs for faster scanning
        
        # Use better batch size for faster scanning
        batch_size = 100  # Increased batch size for better performance
        
        # Apply smart sampling if needed
        filtered_files = self._apply_smart_sampling(
            all_files, smart_sampling, max_files_to_scan
        )
            
        # Total file stats for logging
        print(f"Total files found: {total_file_count}, files to scan: {len(filtered_files)}, files skipped: {self.scan_checkpoint_data['stats']['files_skipped']}")
        
        # Execute parallel scanning
        self._execute_parallel_scan(
            filtered_files, directory_path, checkpoint_path, num_workers, batch_size
        )
        
        # Mark scan as complete
        self.is_running = False
        
        # Create final result
        result = {
            'scan_id': scan_id,
            'scan_type': 'directory',
            'directory': directory_path,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.start_time).total_seconds(),
            'files_scanned': self.scan_checkpoint_data['stats']['files_scanned'],
            'files_skipped': self.scan_checkpoint_data['stats']['files_skipped'],
            'total_findings': self.scan_checkpoint_data['stats']['total_findings'],
            'findings': self.scan_checkpoint_data['findings'],
            'status': 'completed' if len(all_files) == len(self.scan_checkpoint_data['completed_files']) else 'partial',
            'completion_percentage': int(100 * len(self.scan_checkpoint_data['completed_files']) / max(1, len(all_files)))
        }
        
        # Clean up checkpoint file if scan completed successfully
        if result['status'] == 'completed' and os.path.exists(checkpoint_path):
            try:
                os.remove(checkpoint_path)
            except:
                pass
        
        # Integrate cost savings analysis
        try:
            from services.cost_savings_calculator import integrate_cost_savings_into_report
            result = integrate_cost_savings_into_report(result, 'code', self.region)
        except Exception as e:
            logger.warning(f"Cost savings integration failed: {e}")
        
        return result
    
    def _setup_checkpoint(self, continue_from_checkpoint: bool, checkpoint_path: str, 
                         scan_id: str, directory_path: str) -> None:
        """
        Setup or restore checkpoint data for resumable scans.
        
        Args:
            continue_from_checkpoint: Whether to continue from existing checkpoint
            checkpoint_path: Path to the checkpoint file
            scan_id: Unique scan identifier
            directory_path: Directory being scanned
        """
        if continue_from_checkpoint and os.path.exists(checkpoint_path):
            try:
                with open(checkpoint_path, 'r') as f:
                    self.scan_checkpoint_data = json.load(f)
                logger.info(f"Restored scan from checkpoint, {len(self.scan_checkpoint_data.get('completed_files', []))} files already processed")
            except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
                raise CheckpointError(f"Failed to load checkpoint: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error loading checkpoint: {e}")
                self._initialize_checkpoint_data(scan_id, directory_path)
        else:
            self._initialize_checkpoint_data(scan_id, directory_path)
    
    def _initialize_checkpoint_data(self, scan_id: str, directory_path: str) -> None:
        """Initialize fresh checkpoint data."""
        if self.start_time is None:
            raise InvalidConfigurationError("Start time must be set before initializing checkpoint data")
            
        self.scan_checkpoint_data = {
            'scan_id': scan_id,
            'start_time': self.start_time.isoformat(),
            'directory': directory_path,
            'completed_files': [],
            'findings': [],
            'stats': {'files_scanned': 0, 'files_skipped': 0, 'total_findings': 0}
        }
    
    def _compile_ignore_patterns(self, ignore_patterns: Optional[List[str]]) -> List[re.Pattern]:
        """
        Compile ignore patterns into regex objects.
        
        Args:
            ignore_patterns: List of glob patterns to ignore
            
        Returns:
            List of compiled regex patterns
        """
        ignore_regexes = []
        if ignore_patterns:
            for pattern in ignore_patterns:
                try:
                    # Convert glob pattern to regex - simplified to prevent ReDoS
                    regex_pattern = pattern.replace('.', '\\.').replace('*', '[^/]*').replace('?', '[^/]')
                    if '/' in pattern:
                        # Path pattern
                        ignore_regexes.append(re.compile(regex_pattern))
                    else:
                        # File pattern
                        ignore_regexes.append(re.compile(f".*{regex_pattern}$"))
                except re.error as e:
                    logger.warning(f"Invalid ignore pattern '{pattern}': {e}")
        return ignore_regexes
    
    def _discover_files(self, directory_path: str, ignore_regexes: List[re.Pattern], 
                       max_file_size_mb: int) -> Tuple[List[Tuple[str, bool]], int]:
        """
        Discover and filter files for scanning.
        
        Args:
            directory_path: Directory to scan
            ignore_regexes: Compiled ignore patterns
            max_file_size_mb: Maximum file size in MB
            
        Returns:
            Tuple of (filtered files with priority flags, total file count)
        """
        all_files = []
        total_file_count = 0
        
        # Skip certain file types and patterns that are unlikely to contain PII
        skip_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.ttf', '.eot', 
            '.mp3', '.mp4', '.avi', '.pdf', '.zip', '.tar', '.gz', '.lock', '.pyc', 
            '.mo', '.class', '.jar', '.bin', '.exe', '.dll', '.so', '.o'
        }
        skip_dirs = {
            'node_modules', 'vendor', 'dist', 'build', '.git', '.idea', '.vscode', 
            '__pycache__', 'venv', 'env', 'lib', 'bin', 'obj', 'assets', 'images', 
            'fonts', 'locales', 'i18n', 'docs'
        }
        
        # Priority extensions - scan these first and thoroughly
        priority_extensions = {
            '.py', '.js', '.ts', '.java', '.cs', '.php', '.rb', '.go', '.sql', 
            '.env', '.json', '.yaml', '.yml', '.xml', '.csv', '.md'
        }
        
        max_file_size_bytes = max_file_size_mb * 1024 * 1024
        
        for root, dirs, files in os.walk(directory_path):
            # Skip entire directories that match skip patterns
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                total_file_count += 1
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, directory_path)
                
                # Skip already processed files
                if rel_path in self.scan_checkpoint_data['completed_files']:
                    continue
                
                # Check extensions to skip
                _, ext = os.path.splitext(file.lower())
                if ext in skip_extensions:
                    self.scan_checkpoint_data['stats']['files_skipped'] += 1
                    continue
                
                # Check if should ignore
                if any(ignore_regex.match(rel_path) for ignore_regex in ignore_regexes):
                    self.scan_checkpoint_data['stats']['files_skipped'] += 1
                    continue
                
                # Check file size
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > max_file_size_bytes:
                        self.scan_checkpoint_data['stats']['files_skipped'] += 1
                        continue
                except (OSError, PermissionError):
                    # If we can't get file size, skip
                    self.scan_checkpoint_data['stats']['files_skipped'] += 1
                    continue
                
                # Add to scan list with priority flag
                is_priority = ext in priority_extensions
                all_files.append((file_path, is_priority))
        
        return all_files, total_file_count
    
    def _apply_smart_sampling(self, all_files: List[Tuple[str, bool]], 
                            smart_sampling: bool, max_files_to_scan: int) -> List[str]:
        """
        Apply smart sampling to reduce file count for large repositories.
        
        Args:
            all_files: List of (file_path, is_priority) tuples
            smart_sampling: Whether to use smart sampling
            max_files_to_scan: Maximum number of files to scan
            
        Returns:
            List of file paths to scan
        """
        if not smart_sampling or len(all_files) <= max_files_to_scan:
            return [f[0] for f in all_files]
        
        logger.info(f"Repository is very large ({len(all_files)} files). Using smart sampling to scan ~{max_files_to_scan} files.")
        
        # Sort files by priority flag (True/False)
        all_files.sort(key=lambda x: not x[1])  # Priority files first
        
        # Calculate how many files to keep from each priority group
        priority_files = [f for f in all_files if f[1]]
        non_priority_files = [f for f in all_files if not f[1]]
        
        # Always keep all priority files up to a reasonable limit
        priority_limit = min(len(priority_files), int(max_files_to_scan * 0.7))
        non_priority_limit = max_files_to_scan - priority_limit
        
        # Sample files intelligently
        sampled_files = []
        
        # Take all or sample priority files
        if len(priority_files) <= priority_limit:
            sampled_files.extend(priority_files)
        else:
            # Systematic sampling to get representative subset
            step = len(priority_files) / priority_limit
            indices = [int(i * step) for i in range(priority_limit)]
            sampled_files.extend([priority_files[i] for i in indices])
        
        # Sample non-priority files if needed
        if non_priority_limit > 0 and non_priority_files:
            step = len(non_priority_files) / non_priority_limit
            indices = [int(i * step) for i in range(non_priority_limit)]
            sampled_files.extend([non_priority_files[i] for i in indices])
        
        # Update skip count
        self.scan_checkpoint_data['stats']['files_skipped'] += len(all_files) - len(sampled_files)
        
        # Extract file paths
        filtered_files = [f[0] for f in sampled_files]
        logger.info(f"Smart sampling selected {len(filtered_files)} files out of {len(all_files)} total files.")
        
        return filtered_files
    
    def _execute_parallel_scan(self, filtered_files: List[str], directory_path: str, 
                             checkpoint_path: str, num_workers: int, batch_size: int) -> None:
        """
        Execute parallel scanning of files with checkpointing.
        
        Args:
            filtered_files: List of file paths to scan
            directory_path: Base directory path
            checkpoint_path: Path to save checkpoints
            num_workers: Number of worker processes
            batch_size: Batch size for processing
        """
        try:
            with multiprocessing.Pool(processes=num_workers) as pool:
                # Map function for scanning files in parallel
                scan_tasks = [(i, file_path) for i, file_path in enumerate(filtered_files)]
                
                # Process files in parallel batches
                for batch_start in range(0, len(filtered_files), batch_size):
                    # Check if timeout reached
                    if self.start_time is not None:
                        elapsed_time = (datetime.now() - self.start_time).total_seconds()
                        if elapsed_time >= self.max_timeout:
                            raise TimeoutError(f"Scan timeout reached after {elapsed_time:.1f} seconds")
                    
                    # Get current batch
                    batch_end = min(batch_start + batch_size, len(filtered_files))
                    current_batch = scan_tasks[batch_start:batch_end]
                    
                    # Submit work to process pool for parallel processing
                    batch_results = pool.map_async(
                        self._scan_file_wrapper, 
                        [(file_path, directory_path, self.progress_callback, i, len(filtered_files)) 
                         for i, file_path in current_batch]
                    )
                    
                    # Process results as they complete
                    for result in batch_results.get():
                        if result and 'file_path' in result:
                            # Mark as completed
                            rel_path = os.path.relpath(result['file_path'], directory_path)
                            self.scan_checkpoint_data['completed_files'].append(rel_path)
                            
                            # Update stats
                            self.scan_checkpoint_data['stats']['files_scanned'] += 1
                            if result.get('pii_count', 0) > 0:
                                self.scan_checkpoint_data['findings'].append(result)
                                self.scan_checkpoint_data['stats']['total_findings'] += result.get('pii_count', 0)
                    
                    # Save checkpoint after each batch
                    self._save_checkpoint_if_needed(checkpoint_path)
                    
        except (multiprocessing.ProcessError, OSError) as e:
            raise FileProcessingError(f"Parallel processing failed: {e}")
    
    def _save_checkpoint_if_needed(self, checkpoint_path: str) -> None:
        """
        Save checkpoint if the interval has passed.
        
        Args:
            checkpoint_path: Path to save the checkpoint
        """
        if self.start_time is not None and (datetime.now() - self.start_time).total_seconds() % self.checkpoint_interval < 1:
            try:
                with open(checkpoint_path, 'w') as f:
                    json.dump(self.scan_checkpoint_data, f, indent=2)
                logger.info(f"Saved checkpoint at {datetime.now().isoformat()}")
            except (OSError, PermissionError) as e:
                logger.warning(f"Failed to save checkpoint: {e}")
    
    def _scan_file_wrapper(self, args):
        """
        Wrapper function for parallel file scanning.
        
        Args:
            args: Tuple of (file_path, directory_path, progress_callback, index, total)
            
        Returns:
            Scan results for the file
        """
        file_path, directory_path, progress_callback, index, total = args
        
        # Report progress if callback exists
        if progress_callback:
            file_name = os.path.basename(file_path)
            progress_callback(index, total, file_name)
            
        try:
            # Scan the file with timeout protection
            return self._scan_file_with_timeout(file_path)
        except Exception as e:
            print(f"Error scanning {file_path}: {str(e)}")
            return None
    
    def _scan_file_with_timeout(self, file_path: str, timeout=30) -> Dict[str, Any]:
        """
        Scan a file with a timeout to prevent hanging.
        
        Args:
            file_path: Path to the file to scan
            timeout: Timeout in seconds (reduced from 60 to 30 for faster scans)
            
        Returns:
            Scan result dictionary
        """
        # Check elapsed time for overall scan timeout
        if self.start_time:
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
            if elapsed_time >= self.max_timeout:
                raise TimeoutError(f"Overall scan timeout reached after {elapsed_time:.1f} seconds")
        
        # Create a event for timeout notification
        event = threading.Event()
        result = {"status": "timeout", "file_name": os.path.basename(file_path), "file_path": file_path}
        
        def scan_target():
            nonlocal result
            # Log scan start
            logger.info(f'Code scanner processing file: {file_path}')

            try:
                result = self.scan_file(file_path)
            except Exception as e:
                result = {
                    "status": "error",
                    "error": str(e),
                    "file_name": os.path.basename(file_path)
                }
            finally:
                event.set()
        
        # Start scan in a separate thread
        scan_thread = threading.Thread(target=scan_target)
        scan_thread.daemon = True
        scan_thread.start()
        
        # Wait for scan to complete or timeout
        if not event.wait(timeout):
            # Timeout occurred
            return {
                "status": "timeout",
                "file_name": os.path.basename(file_path),
                "error": f"Scan timed out after {timeout} seconds"
            }
        
        return result
        
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a single file for PII and secrets using advanced detection techniques.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            Dictionary containing scan results with detailed metadata
        """
        if not os.path.isfile(file_path):
            return {
                'file_name': os.path.basename(file_path),
                'status': 'error',
                'error': 'File not found',
                'pii_found': []
            }
        
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.extensions:
            return {
                'file_name': os.path.basename(file_path),
                'status': 'skipped',
                'reason': f'File extension {ext} not in scan list',
                'pii_found': []
            }
        
        try:
            # Get file metadata including Git info if available
            file_metadata = self._get_file_metadata(file_path)
            
            # Check file size for streaming vs in-memory processing
            file_size = os.path.getsize(file_path)
            large_file_threshold = 10 * 1024 * 1024  # 10MB threshold
            
            if file_size > large_file_threshold:
                # Use streaming for large files to reduce memory usage
                return self._scan_large_file_streaming(file_path, file_metadata)
            else:
                # Use in-memory processing for smaller files (faster)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                return self._scan_file_content(file_path, content, file_metadata)
            
        except (OSError, PermissionError) as e:
            raise FileProcessingError(f"Cannot access file {file_path}: {e}")
        except UnicodeDecodeError as e:
            logger.warning(f"Unicode decode error in {file_path}: {e}")
            return {
                'file_name': os.path.basename(file_path),
                'status': 'skipped',
                'reason': 'Unicode decode error',
                'pii_found': []
            }
        except Exception as e:
            raise FileProcessingError(f"Error processing file {file_path}: {e}")
    
    def _scan_file_content(self, file_path: str, content: str, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan file content for PII and secrets (in-memory processing).
        
        Args:
            file_path: Path to the file
            content: File content to scan
            file_metadata: File metadata
            
        Returns:
            Scan results dictionary
        """
        _, ext = os.path.splitext(file_path)
        
        # First, extract code and comments separately
        code_content = content
        comments = []
        
        if not self.include_comments:
            # Remove comments from code if not including them
            if ext.lower() in self.compiled_comment_patterns:
                for compiled_pattern in self.compiled_comment_patterns[ext.lower()]:
                    # Extract comments before removing them
                    for match in compiled_pattern.finditer(code_content):
                        comments.append(match.group(0))
                    
                    # Remove comments from code content
                    code_content = compiled_pattern.sub('', code_content)
        
        # Find PII in code
        pii_in_code = self._scan_content(code_content, "code", file_path)
        
        # Find PII in comments if included
        pii_in_comments = []
        if self.include_comments and comments:
            comments_text = '\n'.join(comments)
            pii_in_comments = self._scan_content(comments_text, "comment", file_path)
        
        # Combine results
        all_pii = pii_in_code + pii_in_comments
        
        # Scan for secrets using compiled regex patterns
        for secret_type, compiled_pattern in self.compiled_patterns.items():
            for match in compiled_pattern.finditer(content):
                if len(match.groups()) >= 2:
                    # Variable name is in group 1, value in group 2
                    var_name = match.group(1)
                    value = match.group(2)
                    
                    # Find line number
                    line_no = content[:match.start()].count('\n') + 1
                    
                    # Identify provider if possible
                    provider = self._identify_provider(var_name, value)
                    
                    # Calculate entropy if enabled
                    entropy_score = None
                    if self.use_entropy:
                        entropy_score = self._calculate_entropy(value)
                        if len(value) < 8 or entropy_score < 3.5:  # Low entropy threshold
                            continue  # Skip if entropy is too low (likely not a secret)
                    
                    # Create secret finding
                    secret_finding = {
                        'type': f'Secret:{secret_type.replace("_", " ").title()}',
                        'value': f'{value[:3]}***{value[-3:]}' if len(value) > 6 else '***',
                        'location': f'Line {line_no}',
                        'risk_level': 'High',
                        'reason': f'Potential secret detected: {secret_type}',
                        'provider': provider,
                        'entropy': entropy_score
                    }
                    
                    if self.include_article_refs:
                        secret_finding['regulatory_refs'] = self._get_regulation_references(secret_type)
                    
                    all_pii.append(secret_finding)
        
        # Apply high entropy detection if enabled
        if self.use_entropy:
            entropy_findings = self._detect_high_entropy_strings(content, file_path)
            all_pii.extend(entropy_findings)
        
        # Create final result
        return self._create_scan_result(file_path, all_pii, file_metadata)
    
    def _scan_large_file_streaming(self, file_path: str, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan large files using streaming to reduce memory usage.
        
        Args:
            file_path: Path to the file
            file_metadata: File metadata
            
        Returns:
            Scan results dictionary
        """
        _, ext = os.path.splitext(file_path)
        all_pii = []
        chunk_size = 8192  # 8KB chunks
        line_number = 1
        buffer = ""
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # Add chunk to buffer
                    buffer += chunk
                    
                    # Process complete lines to avoid cutting PII patterns in half
                    lines = buffer.split('\n')
                    buffer = lines[-1]  # Keep incomplete line in buffer
                    
                    for line in lines[:-1]:
                        # Scan each line for PII
                        line_pii = self._scan_content(line, "code", file_path)
                        for pii in line_pii:
                            pii['location'] = f'Line {line_number} (code)'
                        all_pii.extend(line_pii)
                        
                        # Scan for secrets in the line
                        for secret_type, compiled_pattern in self.compiled_patterns.items():
                            for match in compiled_pattern.finditer(line):
                                if len(match.groups()) >= 2:
                                    var_name = match.group(1)
                                    value = match.group(2)
                                    provider = self._identify_provider(var_name, value)
                                    
                                    entropy_score = None
                                    if self.use_entropy:
                                        entropy_score = self._calculate_entropy(value)
                                    
                                    secret_finding = {
                                        'type': f'Secret:{secret_type.replace("_", " ").title()}',
                                        'value': f'{value[:3]}***{value[-3:]}' if len(value) > 6 else '***',
                                        'location': f'Line {line_number}',
                                        'risk_level': 'High',
                                        'reason': f'Potential secret detected: {secret_type}',
                                        'provider': provider,
                                        'entropy': entropy_score
                                    }
                                    
                                    if self.include_article_refs:
                                        secret_finding['regulatory_refs'] = self._get_regulation_references(secret_type)
                                    
                                    all_pii.append(secret_finding)
                        
                        line_number += 1
                
                # Process any remaining buffer content
                if buffer.strip():
                    line_pii = self._scan_content(buffer, "code", file_path)
                    for pii in line_pii:
                        pii['location'] = f'Line {line_number} (code)'
                    all_pii.extend(line_pii)
        
        except (OSError, PermissionError) as e:
            raise FileProcessingError(f"Cannot stream file {file_path}: {e}")
        
        # Apply high entropy detection if enabled
        if self.use_entropy:
            entropy_findings = self._detect_high_entropy_strings_streaming(file_path)
            all_pii.extend(entropy_findings)
        
        # Combine with file metadata
        return self._create_scan_result(file_path, all_pii, file_metadata, "streaming")
    
    def _detect_high_entropy_strings_streaming(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Detect high entropy strings in large files using streaming.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of high entropy findings
        """
        findings = []
        chunk_size = 8192
        line_number = 1
        buffer = ""
        
        # String patterns for detecting potential secrets
        string_patterns = [
            re.compile(r'"([^"\\]*(\\.[^"\\]*)*)"'),    # Double-quoted strings
            re.compile(r"'([^'\\]*(\\.[^'\\]*)*)'"),    # Single-quoted strings
            re.compile(r"`([^`\\]*(\\.[^`\\]*)*)`")     # Backtick strings
        ]
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    buffer += chunk
                    lines = buffer.split('\n')
                    buffer = lines[-1]
                    
                    for line in lines[:-1]:
                        for pattern in string_patterns:
                            for match in pattern.finditer(line):
                                string_value = match.group(1)
                                
                                # Only analyze strings that might be secrets
                                if len(string_value) >= 8 and re.search(r'[A-Za-z0-9]', string_value) and re.search(r'[^A-Za-z0-9]', string_value):
                                    entropy = self._calculate_entropy(string_value)
                                    
                                    if entropy > 4.0:
                                        findings.append({
                                            'type': 'High Entropy String',
                                            'value': f'{string_value[:3]}***{string_value[-3:]}',
                                            'location': f'Line {line_number}',
                                            'risk_level': 'Medium',
                                            'reason': f'String with high entropy (randomness) detected. Entropy: {entropy:.2f}',
                                            'entropy': f"{entropy:.2f}"
                                        })
                        line_number += 1
        
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot analyze entropy for {file_path}: {e}")
        
        return findings
    
    def _detect_code_fraud(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Detect code fraud indicators including plagiarism, license violations, IP theft.
        
        Args:
            content: File content to analyze
            file_path: Path to the file being analyzed
            
        Returns:
            List of code fraud findings
        """
        findings = []
        
        # Severity mapping for different fraud categories
        severity_map = {
            'stolen_code_markers': 'Critical',
            'backdoor_indicators': 'Critical',
            'ip_theft_indicators': 'Critical',
            'license_violations': 'High',
            'license_compatibility_issues': 'High',
            'code_origin_suspicious': 'High',
            'copyright_infringement': 'High',
            'ai_generated_code': 'High',
            'ai_code_patterns_advanced': 'Medium',
            'ai_code_style_indicators': 'Medium',
            'obfuscation_indicators': 'Medium',
            'attribution_missing': 'Medium',
            'code_duplication_indicators': 'Low'
        }
        
        # Compliance mapping
        compliance_refs = {
            'license_violations': 'EU Copyright Directive (2019/790) + NL Auteurswet',
            'stolen_code_markers': 'EU Copyright Directive + Criminal Code (Art. 310 NL)',
            'backdoor_indicators': 'NIS2 Directive Art. 21 + GDPR Art. 32',
            'ip_theft_indicators': 'Trade Secrets Directive (2016/943) + NL Trade Secrets Act',
            'copyright_infringement': 'EU Copyright Directive (2019/790) + NL Auteurswet',
            'obfuscation_indicators': 'EU AI Act Art. 52 (Transparency) + GDPR Art. 5',
            'attribution_missing': 'Open Source License Requirements + NL Auteurswet Art. 25',
            'code_duplication_indicators': 'Software Quality Standards + ISO/IEC 25010',
            'license_compatibility_issues': 'GPL/AGPL/Apache/MIT License Terms',
            'code_origin_suspicious': 'GDPR Art. 32 + NIS2 Directive Art. 21',
            'ai_generated_code': 'EU AI Act Art. 50 (Transparency) + Art. 52 (Disclosure)',
            'ai_code_style_indicators': 'EU AI Act Art. 50 + ISO/IEC 42001 AI Management',
            'ai_code_patterns_advanced': 'EU AI Act Art. 50 + NL AI Guidelines 2024'
        }
        
        for category, compiled_patterns in self.compiled_code_fraud_patterns.items():
            for pattern in compiled_patterns:
                for match in pattern.finditer(content):
                    matched_text = match.group(0)
                    start_pos = match.start()
                    
                    # Get line number
                    line_number = content[:start_pos].count('\n') + 1
                    
                    # Get context (surrounding lines)
                    lines = content.split('\n')
                    context_start = max(0, line_number - 2)
                    context_end = min(len(lines), line_number + 1)
                    context = '\n'.join(lines[context_start:context_end])
                    
                    finding = {
                        'type': f'Code Fraud: {category.replace("_", " ").title()}',
                        'category': 'Code Fraud Detection',
                        'value': matched_text[:100] + ('...' if len(matched_text) > 100 else ''),
                        'location': f'Line {line_number}',
                        'file_path': file_path,
                        'risk_level': severity_map.get(category, 'Medium'),
                        'severity': severity_map.get(category, 'Medium'),
                        'context': context[:300] if context else '',
                        'compliance_reference': compliance_refs.get(category, 'EU/NL IP & Copyright Law'),
                        'fraud_category': category,
                        'description': self._get_fraud_description(category, matched_text),
                        'remediation': self._get_fraud_remediation(category),
                        'netherlands_specific': True
                    }
                    
                    findings.append(finding)
        
        return findings
    
    def _get_fraud_description(self, category: str, matched_text: str) -> str:
        """Get description for code fraud finding."""
        descriptions = {
            'license_violations': f'License indicator detected: "{matched_text}". Verify compliance with license terms.',
            'attribution_missing': f'Attribution reference detected: "{matched_text}". Ensure proper credit is given.',
            'code_duplication_indicators': f'Code duplication marker found: "{matched_text}". Review for plagiarism.',
            'stolen_code_markers': f'Suspicious code marker detected: "{matched_text}". Investigate code origin immediately.',
            'obfuscation_indicators': f'Code obfuscation detected: "{matched_text}". May hide malicious or stolen code.',
            'ip_theft_indicators': f'IP theft indicator found: "{matched_text}". Verify code ownership and rights.',
            'backdoor_indicators': f'Potential backdoor/malware indicator: "{matched_text}". Security review required.',
            'copyright_infringement': f'Copyright indicator: "{matched_text}". Verify usage rights.',
            'license_compatibility_issues': f'License compatibility issue: "{matched_text}". Legal review recommended.',
            'code_origin_suspicious': f'Suspicious code origin: "{matched_text}". Verify legitimate source.',
            'ai_generated_code': f'AI-generated code indicator detected: "{matched_text}". Code may have been generated by ChatGPT, Copilot, Claude, or other AI systems. EU AI Act Art. 50 requires disclosure.',
            'ai_code_style_indicators': f'AI coding style pattern detected: "{matched_text}". This pattern is commonly produced by AI code generators. Review for accuracy and security.',
            'ai_code_patterns_advanced': f'Advanced AI code signature found: "{matched_text}". This code exhibits characteristics typical of LLM-generated code. Verify correctness and licensing.'
        }
        return descriptions.get(category, f'Code fraud indicator detected: {matched_text}')
    
    def _get_fraud_remediation(self, category: str) -> str:
        """Get remediation guidance for code fraud finding."""
        remediations = {
            'license_violations': 'Review and comply with all applicable license terms. Consult legal if uncertain.',
            'attribution_missing': 'Add proper attribution to original authors as required by license terms.',
            'code_duplication_indicators': 'Remove or properly attribute copied code. Implement original solution.',
            'stolen_code_markers': 'Remove suspicious code immediately. Conduct security and legal review.',
            'obfuscation_indicators': 'Deobfuscate and review code. Replace with transparent implementation.',
            'ip_theft_indicators': 'Verify code ownership. Remove any unauthorized proprietary code.',
            'backdoor_indicators': 'Remove potential backdoor code. Conduct full security audit.',
            'copyright_infringement': 'Obtain proper licenses or remove infringing code.',
            'license_compatibility_issues': 'Resolve license conflicts. Consider dual licensing or code replacement.',
            'code_origin_suspicious': 'Verify code source. Replace with code from trusted repositories.',
            'ai_generated_code': 'Per EU AI Act Art. 50: Disclose AI-generated code in documentation. Review for accuracy, security vulnerabilities, and hallucinated dependencies. Ensure proper testing coverage.',
            'ai_code_style_indicators': 'Review AI-generated code patterns for correctness. Test thoroughly for edge cases. Consider refactoring to improve maintainability and remove AI-typical verbosity.',
            'ai_code_patterns_advanced': 'Document AI assistance usage per EU AI Act. Verify all imports and dependencies exist. Review business logic for AI hallucinations. Conduct security audit for potential vulnerabilities.'
        }
        return remediations.get(category, 'Review code origin and ensure compliance with applicable laws.')
    
    def _create_scan_result(self, file_path: str, all_pii: List[Dict[str, Any]], 
                           file_metadata: Dict[str, Any], scan_method: str = "in-memory") -> Dict[str, Any]:
        """
        Create standardized scan result dictionary.
        
        Args:
            file_path: Path to the scanned file
            all_pii: List of PII findings
            file_metadata: File metadata
            scan_method: Method used for scanning (in-memory or streaming)
            
        Returns:
            Standardized scan result dictionary
        """
        # Add Netherlands-specific GDPR (UAVG) violations if available
        try:
            # Check both GDPR and Dutch UAVG compliance
            content_for_nl_check = '\n'.join([str(pii) for pii in all_pii])
            nl_violations = detect_nl_violations(content_for_nl_check)
            
            # Add UAVG-specific compliance information
            for violation in nl_violations:
                violation['compliance_frameworks'] = ['GDPR', 'UAVG']
                violation['netherlands_specific'] = True
                
            all_pii.extend(nl_violations)
            logger.info(f"Netherlands GDPR/UAVG compliance check completed: {len(nl_violations)} violations found")
        except Exception as e:
            logger.warning(f"Netherlands GDPR/UAVG violation detection failed: {e}")
        
        # Add code fraud detection
        try:
            # Read file content for fraud analysis
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read()
            except:
                file_content = ""
            
            if file_content:
                fraud_findings = self._detect_code_fraud(file_content, file_path)
                all_pii.extend(fraud_findings)
                if fraud_findings:
                    logger.info(f"Code fraud detection completed for {file_path}: {len(fraud_findings)} indicators found")
        except Exception as e:
            logger.warning(f"Code fraud detection failed for {file_path}: {e}")
        
        # Calculate risk metrics
        risk_counts = {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
        for finding in all_pii:
            risk_level = finding.get('risk_level', 'Medium')
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        return {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'scan_method': scan_method,
            'status': 'completed',
            'pii_found': all_pii,
            'pii_count': len(all_pii),
            'risk_summary': risk_counts,
            'file_size_bytes': file_metadata.get('size_bytes', 0),
            'scan_timestamp': datetime.now().isoformat(),
            'region': self.region,
            **file_metadata
        }
    
    def _get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed file metadata, including Git information if available.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file metadata
        """
        metadata = {
            'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
            'size_bytes': os.path.getsize(file_path),
            'extension': os.path.splitext(file_path)[1].lower()
        }
        
        # Get Git metadata if enabled and the file is in a Git repository
        if self.use_git_metadata:
            try:
                git_data = {}
                
                # Get the file's Git history
                result = subprocess.run(
                    ['git', 'log', '-n', '1', '--pretty=format:%H|%an|%ae|%ad|%s', '--', file_path],
                    capture_output=True, text=True, check=False
                )
                
                if result.returncode == 0 and result.stdout:
                    parts = result.stdout.split('|')
                    if len(parts) >= 5:
                        git_data['commit_hash'] = parts[0]
                        git_data['author_name'] = parts[1]
                        git_data['author_email'] = parts[2]
                        git_data['commit_date'] = parts[3]
                        git_data['commit_message'] = parts[4]
                
                # Get Git blame info
                result = subprocess.run(
                    ['git', 'blame', '--porcelain', file_path],
                    capture_output=True, text=True, check=False
                )
                
                if result.returncode == 0 and result.stdout:
                    # Parse blame output to get line-by-line author info
                    blame_data = {}
                    lines = result.stdout.split('\n')
                    current_commit = None
                    line_number = 0
                    
                    for line in lines:
                        if line.startswith('author '):
                            author = line[7:]
                            if current_commit and current_commit not in blame_data:
                                blame_data[current_commit] = {
                                    'author': author,
                                    'lines': [line_number]
                                }
                            elif current_commit:
                                blame_data[current_commit]['lines'].append(line_number)
                        elif line and not line.startswith('\t'):
                            parts = line.split(' ')
                            if len(parts) > 0:
                                current_commit = parts[0]
                                line_number = int(parts[2]) if len(parts) > 2 else 0
                    
                    # Add line count per author summary
                    authors = {}
                    for commit, data in blame_data.items():
                        author = data['author']
                        if author in authors:
                            authors[author] += len(data['lines'])
                        else:
                            authors[author] = len(data['lines'])
                    
                    git_data['blame_summary'] = {
                        'authors': authors,
                        'total_lines': sum(authors.values())
                    }
                
                metadata['git'] = git_data
            except Exception as e:
                # Git metadata collection failed, but we don't want to fail the whole scan
                metadata['git_error'] = str(e)
        
        return metadata
    
    def _calculate_entropy(self, string: str) -> float:
        """
        Calculate Shannon entropy of a string.
        Higher values indicate more randomness (higher likelihood of being a secret).
        
        Args:
            string: The string to calculate entropy for
            
        Returns:
            Entropy value (typically 3.5+ for secrets, 5+ for strong secrets)
        """
        if not string:
            return 0.0
        
        # Count character frequencies
        freq = {}
        for c in string:
            if c in freq:
                freq[c] += 1
            else:
                freq[c] = 1
        
        # Calculate entropy
        length = len(string)
        entropy = 0.0
        
        for count in freq.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _detect_high_entropy_strings(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Detect high entropy strings that might be secrets but weren't caught by regex patterns.
        
        Args:
            content: The file content
            file_path: Path to the file for reference
            
        Returns:
            List of findings with high entropy strings
        """
        findings = []
        
        # Look for string literals in the code
        # This is a simplified approach - each language has different string literal syntax
        string_patterns = [
            r'"([^"\\]*(\\.[^"\\]*)*)"',    # Double-quoted strings
            r"'([^'\\]*(\\.[^'\\]*)*)'",    # Single-quoted strings
            r"`([^`\\]*(\\.[^`\\]*)*)`"     # Backtick strings (JavaScript)
        ]
        
        for pattern in string_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                string_value = match.group(1)
                
                # Only analyze strings that might be secrets (8+ chars, alphanumeric+symbols)
                if len(string_value) >= 8 and re.search(r'[A-Za-z0-9]', string_value) and re.search(r'[^A-Za-z0-9]', string_value):
                    entropy = self._calculate_entropy(string_value)
                    
                    # High entropy threshold (adjust as needed)
                    if entropy > 4.0:
                        line_no = content[:match.start()].count('\n') + 1
                        entropy_formatted = str(round(entropy, 2))
                        
                        # Add to findings
                        findings.append({
                            'type': 'High Entropy String',
                            'value': f'{string_value[:3]}***{string_value[-3:]}',  # Mask the value
                            'location': f'Line {line_no}',
                            'risk_level': 'Medium',
                            'reason': f'String with high entropy (randomness) detected. Entropy: {entropy_formatted}',
                            'entropy': entropy_formatted
                        })
        
        return findings
    
    def _identify_provider(self, var_name: str, value: str) -> Optional[str]:
        """
        Identify the provider/service based on key patterns.
        
        Args:
            var_name: Variable name or key
            value: The secret value
            
        Returns:
            Provider name if identified, None otherwise
        """
        combined = f"{var_name} {value}".lower()
        
        for provider, patterns in self.known_providers.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return provider
        
        return None
    
    def _get_regulation_references(self, finding_type: str) -> Dict[str, str]:
        """
        Get relevant regulatory references for a finding type.
        
        Args:
            finding_type: The type of finding
            
        Returns:
            Dictionary mapping regulation names to article references
        """
        references = {}
        
        finding_type = finding_type.lower()
        
        # Map finding types to regulatory categories
        category_map = {
            'secret': 'Security',
            'api key': 'Security',
            'token': 'Security',
            'password': 'Security',
            'email': 'PII',
            'name': 'PII',
            'address': 'PII',
            'phone': 'PII',
            'ip': 'PII',
            'credit card': 'Financial Data',
            'bank': 'Financial Data',
            'passport': 'Special Categories',
            'medical': 'Health Data',
            'health': 'Health Data',
            'ethnic': 'Special Categories',
            'biometric': 'Special Categories'
        }
        
        # Determine which category this finding falls into
        matched_category = None
        for key, category in category_map.items():
            if key in finding_type:
                matched_category = category
                break
        
        if not matched_category:
            matched_category = 'PII'  # Default category
        
        # Add references from each regulatory framework
        for regulation, ref_map in self.regulatory_refs.items():
            for ref_category, article in ref_map.items():
                if matched_category in ref_category or ref_category in matched_category:
                    references[regulation] = article
                    break
            
            # Add general reference if no specific one was found
            if regulation not in references and 'PII' in ref_map:
                references[regulation] = ref_map['PII']
        
        return references
    
    def _scan_content(self, content: str, content_type: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Scan content (code or comments) for PII and security vulnerabilities.
        
        Args:
            content: The text content to scan
            content_type: Either "code" or "comment"
            file_path: Original file path for reference
            
        Returns:
            List of PII and vulnerability findings
        """
        pii_found = []
        
        # Split into lines for better location reporting
        lines = content.split('\n')
        
        # Define vulnerability patterns for specific repository types
        vulnerability_patterns = {
            # SQL Injection
            'sql_injection': [
                r'(?i).*execute\s*\(\s*[\'"](.*?(%s|%d|%[0-9]+d|{[^}]+}).*?)[\'"].*\)',
                r'(?i).*cursor\.execute\s*\(\s*[\'"](.*?(%s|%d|%[0-9]+d|{[^}]+}).*?)[\'"].*\)',
                r'(?i).*query\s*=\s*[\'"](.*?(%s|%d|%[0-9]+d|{[^}]+}).*?)[\'"].*',
                r'(?i).*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP).*\+',
                r'(?i).*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP).*\|\|',
                r'(?i).*raw_input\s*\(\s*.*\)',
                r'(?i).*\bexec\s*\(\s*.*\+\s*.*\)',
                r'(?i).*\bformat\s*\(\s*["\'](SELECT|INSERT|UPDATE|DELETE).*\)',
                r'(?i).*(request\.args|request\.params|request\.form|request\.values|request\.query|request\.body)\s*[\[\.].*\bexecute\b',
                r'(?i).*user.*input.*query',
                r'(?i).*string\s+concatenat.*\s+(query|sql)'
            ],
            
            # XSS
            'xss': [
                r'(?i).*innerHTML\s*=',
                r'(?i).*document\.write\s*\(',
                r'(?i).*eval\s*\(',
                r'(?i).*setTimeout\s*\(',
                r'(?i).*setInterval\s*\(',
                r'(?i).*new Function\s*\(',
                r'(?i).*(render|send|write|output).*\(\s*[^\)]*\$\{',
                r'(?i).*\$\.html\s*\(',
                r'(?i).*jinja2\.Template\s*\(.*request',
                r'(?i).*(response|res)\.write\s*\(.*request',
                r'(?i).*\.send\s*\(\s*.*\+.*\)',
                r'(?i).*\.html\s*\(\s*.*request.*\)'
            ],
            
            # CSRF
            'csrf': [
                r'(?i).*disable.*csrf.*',
                r'(?i).*csrf_exempt.*',
                r'(?i).*WTF_CSRF_ENABLED\s*=\s*False.*',
                r'(?i).*csrf_protect\s*=\s*False.*',
                r'(?i).*@csrf_exempt.*'
            ],
            
            # Insecure Authentication
            'insecure_auth': [
                r'(?i).*password(?!.*hash)(?!.*crypt)(?!.*salt).*',
                r'(?i).*md5\s*\(.*password.*\).*',
                r'(?i).*sha1\s*\(.*password.*\).*',
                r'(?i).*hardcoded.*password.*',
                r'(?i).*hardcoded.*credentials.*',
                r'(?i).*default.*password.*',
                r'(?i).*admin.*password\s*=\s*["\']+.*',
                r'(?i).*test.*password\s*=\s*["\']+.*'
            ],
            
            # Path Traversal
            'path_traversal': [
                r'(?i).*open\s*\(\s*.*\+.*\)',
                r'(?i).*os\.path\.join.*\(\s*.*request',
                r'(?i).*readfile.*\(\s*.*request',
                r'(?i).*\.\./',
                r'(?i).*\.\.\\',
                r'(?i).*file_get_contents\s*\(.*\$_.*\)',
                r'(?i).*include\s*\(.*\+.*\)'
            ],
            
            # Insecure Deserialization
            'insecure_deserialization': [
                r'(?i).*pickle\.loads.*\(',
                r'(?i).*yaml\.load.*\(',
                r'(?i).*marshal\.loads.*\(',
                r'(?i).*unserialize.*\('
            ]
        }
        
        # Additional patterns for Intentionally-Vulnerable-Python applications
        vuln_app_patterns = {
            'intentional_vuln': [
                r'(?i).*INTENTIONAL.*VULN.*',
                r'(?i).*DELIBERATELY.*VULN.*',
                r'(?i).*THIS.*IS.*VULNERABLE.*',
                r'(?i).*INSECURE.*CODE.*',
                r'(?i).*UNSAFE.*CODE.*',
                r'(?i).*EXAMPLE.*VULN.*',
                r'(?i).*SECURITY.*ISSUE.*',
                r'(?i).*password\s*=\s*["\'](admin|password|123456|root)["\']+',
                r'(?i).*username\s*=\s*["\'](admin|root|user|test)["\']+',
                r'(?i).*trust.*all.*certs.*',
                r'(?i).*disable.*security.*',
                r'(?i).*bypass.*security.*',
                r'(?i).*ignore.*warning.*'
            ]
        }
        
        # Add Intentionally-Vulnerable patterns to all categories
        for vuln_type in vulnerability_patterns:
            vulnerability_patterns[vuln_type].extend(vuln_app_patterns['intentional_vuln'])
        
        # First process each line for regular PII
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Use PII detection utility
            pii_items = identify_pii_in_text(line, self.region)
            
            for pii_item in pii_items:
                pii_type = pii_item['type']
                
                # Evaluate risk level
                risk_level = evaluate_risk_level(pii_type, self.region_rules)
                
                # Create finding entry
                finding = {
                    'type': pii_type,
                    'value': pii_item['value'],
                    'location': f'Line {line_num} ({content_type})',
                    'risk_level': risk_level,
                    'reason': self._get_reason(pii_type, risk_level)
                }
                
                pii_found.append(finding)
            
            # Check for UAVG (Dutch GDPR) specific patterns
            if self.region.lower() in ['netherlands', 'nederland', 'nl']:
                for category, compiled_patterns in self.compiled_uavg_patterns.items():
                    for pattern in compiled_patterns:
                        matches = pattern.finditer(line)
                        for match in matches:
                            # Determine UAVG-specific risk level
                            uavg_risk_level = self._get_uavg_risk_level(category, match.group())
                            
                            # Create UAVG finding
                            uavg_finding = {
                                'type': f'UAVG-{category.replace("_", " ").title()}',
                                'value': match.group()[:50] + '...' if len(match.group()) > 50 else match.group(),
                                'location': f'Line {line_num} ({content_type})',
                                'risk_level': uavg_risk_level,
                                'reason': self._get_uavg_reason(category),
                                'compliance_frameworks': ['GDPR', 'UAVG'],
                                'netherlands_specific': True,
                                'regulatory_reference': self._get_uavg_article_reference(category)
                            }
                            
                            pii_found.append(uavg_finding)
            
            # Check for vulnerability patterns in each line
            if content_type == "code":  # Only check code, not comments
                for vuln_type, patterns in vulnerability_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, line):
                            # Create vulnerability finding
                            finding = {
                                'type': f'Vulnerability:{vuln_type.replace("_", " ").title()}',
                                'value': line.strip(),
                                'location': f'Line {line_num} (code)',
                                'risk_level': 'High',
                                'reason': f'Potential security vulnerability: {vuln_type.replace("_", " ")}. This pattern is commonly found in intentionally vulnerable applications.'
                            }
                            pii_found.append(finding)
        
        # Also check multiline patterns (for complex vulnerabilities spanning multiple lines)
        if content_type == "code" and len(lines) > 1:
            # Multiline chunked analysis - check 5 lines at a time
            for i in range(0, len(lines), 5):
                chunk = "\n".join(lines[i:i+5])
                for vuln_type, patterns in vulnerability_patterns.items():
                    for pattern in patterns:
                        match = re.search(pattern, chunk, re.DOTALL)
                        if match:
                            # Create vulnerability finding for the chunk
                            finding = {
                                'type': f'Vulnerability:{vuln_type.replace("_", " ").title()}',
                                'value': match.group(0),
                                'location': f'Lines {i+1}-{min(i+5, len(lines))} (code)',
                                'risk_level': 'High',
                                'reason': f'Potential security vulnerability: {vuln_type.replace("_", " ")}. This pattern is commonly found in intentionally vulnerable applications.'
                            }
                            pii_found.append(finding)
        
        return pii_found
    
    def _get_reason(self, pii_type: str, risk_level: str) -> str:
        """
        Get a reason explanation for the PII finding.
        
        Args:
            pii_type: The type of PII found
            risk_level: The risk level (Low, Medium, High)
            
        Returns:
            A string explaining why this PII is a concern
        """
        reasons = {
            'BSN': 'Dutch citizen service number (BSN) is highly sensitive personal data under GDPR and UAVG',
            'Email': 'Email addresses are personal data under GDPR',
            'Phone': 'Phone numbers are personal data under GDPR',
            'Address': 'Physical addresses are personal data under GDPR',
            'Name': 'Personal names are personal data under GDPR',
            'Credit Card': 'Payment information is highly sensitive under GDPR',
            'IP Address': 'IP addresses are considered personal data under GDPR',
            'Date of Birth': 'Birth dates are personal data and can be used for identity theft',
            'Passport Number': 'Passport numbers are highly sensitive personal data under GDPR',
            'Medical Data': 'Medical data is special category data under GDPR Article 9',
            'Financial Data': 'Financial information is sensitive personal data under GDPR',
            'Username': 'Usernames may be personal data under GDPR',
            'Password': 'Password storage should follow strict security guidelines under GDPR',
        }
        
        # Default reason if specific one not found
        default_reason = f"{pii_type} is potentially personal data under GDPR"
        
        return reasons.get(pii_type, default_reason)
    
    def _get_uavg_risk_level(self, category: str, matched_text: str) -> str:
        """
        Determine UAVG-specific risk level for different categories.
        
        Args:
            category: UAVG pattern category
            matched_text: The matched text
            
        Returns:
            Risk level string
        """
        risk_levels = {
            'bsn_numbers': 'Critical',  # BSN is highly sensitive in Netherlands
            'dutch_medical_data': 'High',
            'dutch_personal_identifiers': 'High',
            'dutch_financial_identifiers': 'High',
            'dutch_employment_data': 'Medium',
            'dutch_education_data': 'Medium',
            'dutch_minors_consent': 'High',  # Important for UAVG compliance
            'dutch_legal_basis': 'Medium'
        }
        
        return risk_levels.get(category, 'Medium')
    
    def _get_uavg_reason(self, category: str) -> str:
        """
        Get UAVG-specific reason for the finding.
        
        Args:
            category: UAVG pattern category
            
        Returns:
            Explanation string
        """
        reasons = {
            'bsn_numbers': 'Dutch Burgerservicenummer (BSN) detected - requires special handling under UAVG Article 46',
            'dutch_medical_data': 'Medical data requires additional safeguards under UAVG Article 30',
            'dutch_personal_identifiers': 'Dutch personal identifiers require GDPR/UAVG compliance measures',
            'dutch_financial_identifiers': 'Financial identifiers require secure processing under GDPR/UAVG',
            'dutch_employment_data': 'Employment data processing must comply with Dutch labor law and UAVG',
            'dutch_education_data': 'Educational data requires special handling under Dutch privacy laws',
            'dutch_minors_consent': 'Parental consent required for users under 16 years under UAVG Article 5',
            'dutch_legal_basis': 'Legal basis references indicate data processing requiring GDPR/UAVG compliance'
        }
        
        return reasons.get(category, 'UAVG compliance required for Dutch personal data processing')
    
    def _get_uavg_article_reference(self, category: str) -> str:
        """
        Get specific UAVG article reference for the category.
        
        Args:
            category: UAVG pattern category
            
        Returns:
            Article reference string
        """
        article_refs = {
            'bsn_numbers': 'UAVG Article 46',
            'dutch_medical_data': 'UAVG Article 30',
            'dutch_personal_identifiers': 'GDPR Article 4(1) + UAVG',
            'dutch_financial_identifiers': 'GDPR Article 6 + UAVG',
            'dutch_employment_data': 'GDPR Article 6(1)(b) + UAVG',
            'dutch_education_data': 'GDPR Article 6 + UAVG Article 43-47',
            'dutch_minors_consent': 'UAVG Article 5 (GDPR Article 8)',
            'dutch_legal_basis': 'GDPR Articles 6-7 + UAVG'
        }
        
        return article_refs.get(category, 'GDPR + UAVG')
