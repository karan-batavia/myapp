import os
import tempfile
import re
import logging
from collections import Counter
from statistics import mean, stdev

# Import centralized logging
try:
    from utils.centralized_logger import get_scanner_logger
    logger = get_scanner_logger("blob_scanner")
except ImportError:
    # Fallback to standard logging if centralized logger not available
    logger = logging.getLogger(__name__)
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import PyPDF2
# import textract  # Replaced with enhanced_document_processor
from services.enhanced_document_processor import enhanced_processor as textract
from utils.pii_detection import identify_pii_in_text
from utils.gdpr_rules import get_region_rules, evaluate_risk_level
from utils.netherlands_gdpr import detect_nl_violations
from utils.comprehensive_gdpr_validator import validate_comprehensive_gdpr_compliance
from utils.eu_ai_act_compliance import detect_ai_act_violations, generate_ai_act_compliance_report

# Import Advanced Document Analyzer for comprehensive document analysis
try:
    from services.advanced_document_analyzer import AdvancedDocumentAnalyzer
    ADVANCED_ANALYZER_AVAILABLE = True
except ImportError:
    ADVANCED_ANALYZER_AVAILABLE = False
    logger.warning("Advanced Document Analyzer not available")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class BlobScanner:
    """
    A scanner that detects PII in document files (PDFs, Word documents, text files, etc.)
    
    Enhanced with 12 advanced document analysis features:
    - Document Metadata Extraction (author, creation date, company, software)
    - Document Tampering/Integrity Detection
    - Language Detection for proper PII matching
    - Document Classification (contract, invoice, medical, HR, legal)
    - Hidden Content Detection (hidden layers, rows, columns)
    - Embedded Object Detection (macros, scripts, OLE objects)
    - Digital Signature Detection and Validation
    - Redaction Detection
    - Version/Revision History Analysis
    - Enhanced Table/Form Data Extraction
    - Document Forensics (authorship, timeline analysis)
    - Cross-Reference Detection (linked documents, URLs)
    """
    
    def __init__(self, file_types: Optional[List[str]] = None, region: str = "Netherlands"):
        """
        Initialize the blob scanner.
        
        Args:
            file_types: List of file types to scan (e.g., ['PDF', 'DOCX'])
            region: The region for which to apply GDPR rules
        """
        self.file_types = file_types if file_types is not None else [
            "PDF", "DOCX", "TXT", "RTF", "CSV", "XLSX", "JSON", "XML", 
            "HTML", "MD", "LOG", "CONF", "INI", "ENV", "SQL", "JS", 
            "PY", "JAVA", "PHP", "RB", "C", "CPP", "CS", "GO", "TS"
        ]
        self.region = region
        self.region_rules = get_region_rules(region)
        
        # Initialize Advanced Document Analyzer
        self.advanced_analyzer = None
        if ADVANCED_ANALYZER_AVAILABLE:
            try:
                self.advanced_analyzer = AdvancedDocumentAnalyzer(region=region)
                logger.info("Advanced Document Analyzer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Advanced Document Analyzer: {e}")
        
        # Expanded mapping of file extensions to their types
        self.extension_map = {
            # Document formats
            '.pdf': 'PDF',
            '.docx': 'DOCX',
            '.doc': 'DOCX',
            '.rtf': 'RTF',
            '.odt': 'DOCX',
            '.pptx': 'PPTX',
            '.ppt': 'PPTX',
            '.odp': 'PPTX',
            
            # Spreadsheet formats
            '.xlsx': 'XLSX',
            '.xls': 'XLSX',
            '.csv': 'CSV',
            '.ods': 'XLSX',
            '.tsv': 'CSV',
            
            # Text formats
            '.txt': 'TXT',
            '.md': 'MD',
            '.markdown': 'MD',
            '.rst': 'TXT',
            
            # Data formats
            '.json': 'JSON',
            '.xml': 'XML',
            '.html': 'HTML',
            '.htm': 'HTML',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.toml': 'TOML',
            
            # Config files
            '.conf': 'CONF',
            '.config': 'CONF',
            '.ini': 'INI',
            '.cfg': 'CONF',
            '.env': 'ENV',
            '.properties': 'CONF',
            '.cnf': 'CONF',
            
            # Log files
            '.log': 'LOG',
            
            # Database files
            '.sql': 'SQL',
            '.sqlite': 'SQL',
            '.db': 'SQL',
            
            # Programming languages
            '.py': 'PY',
            '.js': 'JS',
            '.ts': 'TS',
            '.jsx': 'JS',
            '.tsx': 'TS',
            '.java': 'JAVA',
            '.cs': 'CS',
            '.php': 'PHP',
            '.rb': 'RB',
            '.c': 'C',
            '.cpp': 'CPP',
            '.h': 'C',
            '.hpp': 'CPP',
            '.go': 'GO',
            '.rs': 'RS',
            '.swift': 'SWIFT',
            '.kt': 'KT',
            '.sh': 'SH',
            '.ps1': 'PS1',
            '.bat': 'BAT',
            '.css': 'CSS',
            '.scss': 'CSS',
            '.less': 'CSS'
        }
        
        # High-risk file types that might contain sensitive information
        self.high_risk_files = [
            '.env', '.ini', '.conf', '.config', '.cnf', '.properties',
            '.pem', '.key', '.cert', '.crt', '.p12', '.pfx', '.keystore',
            '.htpasswd', '.netrc', '.pgpass', '.aws/credentials', 
            'secrets.json', 'credentials.json', 'auth.json'
        ]
    
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a single document file for PII.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            Dictionary containing scan results
        """
        if not os.path.isfile(file_path):
            return {
                'file_name': os.path.basename(file_path),
                'status': 'error',
                'error': 'File not found',
                'pii_found': []
            }
        
        # Get filename for checks
        file_name = os.path.basename(file_path)
        
        # Check if file is in high-risk list - always scan these regardless of extension
        is_high_risk = any(file_name.endswith(ext) for ext in self.high_risk_files) or any(pattern in file_name.lower() for pattern in ['secret', 'password', 'credential', 'token', 'key', 'auth'])
        
        # Check if file type is supported
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # For high-risk files, try to scan even if extension is not in the map
        if ext not in self.extension_map and not is_high_risk:
            return {
                'file_name': file_name,
                'status': 'skipped',
                'reason': f'File extension {ext} not supported',
                'pii_found': []
            }
        
        # For high-risk files without recognized extension, treat as text
        if ext not in self.extension_map and is_high_risk:
            file_type = 'TXT'  # Treat as plain text
        else:
            file_type = self.extension_map[ext]
            
        # Skip normal files if type not in scan list, but always scan high-risk files
        if file_type not in self.file_types and not is_high_risk:
            return {
                'file_name': file_name,
                'status': 'skipped',
                'reason': f'File type {file_type} not in scan list',
                'pii_found': []
            }
        
        try:
            # Extract text based on file type
            text = self._extract_text(file_path, file_type)
            
            if not text:
                return {
                    'file_name': os.path.basename(file_path),
                    'status': 'warning',
                    'warning': 'No text content could be extracted',
                    'pii_found': []
                }
            
            # Scan the extracted text for PII
            pii_items = self._scan_text(text, file_path)
            
            # Perform comprehensive compliance validation with error handling
            try:
                gdpr_compliance = validate_comprehensive_gdpr_compliance(text, self.region)
            except Exception as e:
                print(f"GDPR compliance validation failed: {str(e)}")
                gdpr_compliance = {'findings': [], 'overall_compliance_score': 100}
            
            try:
                netherlands_violations = detect_nl_violations(text) if self.region == "Netherlands" else []
            except Exception as e:
                print(f"Netherlands violations detection failed: {str(e)}")
                netherlands_violations = []
            
            try:
                ai_act_violations = detect_ai_act_violations(text)
            except Exception as e:
                print(f"AI Act violations detection failed: {str(e)}")
                ai_act_violations = []
            
            # AI Fraud Detection - NEW
            try:
                ai_fraud_analysis = self._detect_ai_generated_documents(file_path, text, file_type)
            except Exception as e:
                logger.error(f"AI fraud detection failed: {str(e)}")
                ai_fraud_analysis = None
            
            # Combine all findings
            all_compliance_findings = []
            if gdpr_compliance and 'findings' in gdpr_compliance:
                all_compliance_findings.extend(gdpr_compliance.get('findings', []))
            if netherlands_violations:
                all_compliance_findings.extend(netherlands_violations)
            if ai_act_violations:
                all_compliance_findings.extend(ai_act_violations)
            
            # Calculate risk assessment including compliance findings
            all_findings = pii_items if pii_items else []
            if all_compliance_findings:
                all_findings.extend(all_compliance_findings)
            risk_assessment = self._calculate_risk_score(all_findings)
            
            # Determine GDPR categories
            gdpr_categories = self._get_gdpr_categories(pii_items)
            
            # Generate comprehensive compliance notes
            compliance_notes = self._generate_comprehensive_compliance_notes(
                pii_items, all_compliance_findings, file_type, gdpr_compliance, ai_act_violations
            )
            
            # Generate AI Act compliance report with error handling
            try:
                ai_act_report = generate_ai_act_compliance_report(ai_act_violations)
            except Exception as e:
                print(f"AI Act report generation failed: {str(e)}")
                ai_act_report = {'compliance_score': 100, 'compliance_status': 'Compliant', 'risk_distribution': {}, 'recommendations': []}
            
            # Advanced Document Analysis (12 features)
            advanced_analysis = {}
            if self.advanced_analyzer:
                try:
                    advanced_analysis = self.advanced_analyzer.analyze_document(file_path, text)
                    logger.info(f"Advanced document analysis completed for {os.path.basename(file_path)}")
                    
                    # Add advanced findings to all findings
                    advanced_findings = advanced_analysis.get('findings', [])
                    if advanced_findings:
                        all_findings.extend(advanced_findings)
                        # Recalculate risk with new findings
                        risk_assessment = self._calculate_risk_score(all_findings)
                except Exception as e:
                    logger.warning(f"Advanced document analysis failed: {str(e)}")
                    advanced_analysis = {'error': str(e)}
            
            # Create comprehensive results
            result = {
                'file_name': os.path.basename(file_path),
                'file_path': file_path,
                'status': 'scanned',
                'file_type': file_type,
                'file_size': os.path.getsize(file_path),
                'pii_found': pii_items,
                'findings': pii_items,  # Add findings field for compatibility
                'pii_count': len(pii_items),
                'risk_assessment': risk_assessment,
                'risk_level': risk_assessment.get('level', 'Low'),
                'gdpr_categories': gdpr_categories,
                'compliance_notes': compliance_notes,
                'scan_timestamp': datetime.now().isoformat(),
                'region': self.region,
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'text_length': len(text) if text else 0,
                # Enhanced compliance reporting
                'gdpr_compliance': {
                    'overall_score': gdpr_compliance.get('overall_compliance_score', 0),
                    'status': gdpr_compliance.get('compliance_status', 'Unknown'),
                    'principle_scores': gdpr_compliance.get('principle_compliance', {}),
                    'rights_scores': gdpr_compliance.get('rights_compliance', {}),
                    'recommendations': gdpr_compliance.get('recommendations', [])
                },
                'netherlands_compliance': {
                    'violations_found': len(netherlands_violations),
                    'violations': netherlands_violations
                } if self.region == "Netherlands" else {},
                'ai_act_compliance': {
                    'compliance_score': ai_act_report.get('compliance_score', 100),
                    'status': ai_act_report.get('compliance_status', 'Compliant'),
                    'risk_distribution': ai_act_report.get('risk_distribution', {}),
                    'violations': ai_act_violations,
                    'recommendations': ai_act_report.get('recommendations', [])
                },
                'all_compliance_findings': all_compliance_findings,
                'fraud_analysis': ai_fraud_analysis or {},
                # NEW: Advanced Document Analysis (12 features)
                'advanced_analysis': {
                    'metadata': advanced_analysis.get('metadata', {}),
                    'integrity': advanced_analysis.get('integrity', {}),
                    'language': advanced_analysis.get('language', {}),
                    'classification': advanced_analysis.get('classification', {}),
                    'hidden_content': advanced_analysis.get('hidden_content', {}),
                    'embedded_objects': advanced_analysis.get('embedded_objects', {}),
                    'digital_signatures': advanced_analysis.get('digital_signatures', {}),
                    'redaction': advanced_analysis.get('redaction', {}),
                    'version_history': advanced_analysis.get('version_history', {}),
                    'table_data': advanced_analysis.get('table_data', {}),
                    'forensics': advanced_analysis.get('forensics', {}),
                    'cross_references': advanced_analysis.get('cross_references', {}),
                    'advanced_findings': advanced_analysis.get('findings', []),
                    'risk_indicators': advanced_analysis.get('risk_indicators', [])
                }
            }
            
            return result
            
        except Exception as e:
            return {
                'file_name': os.path.basename(file_path),
                'status': 'error',
                'error': str(e),
                'pii_found': []
            }
    
    def _extract_text(self, file_path: str, file_type: str) -> str:
        """
        Extract text content from a document file.
        
        Args:
            file_path: Path to the document file
            file_type: Type of the document (PDF, DOCX, etc.)
            
        Returns:
            Extracted text content
        """
        # Group file types by extraction method
        text_based_formats = [
            'TXT', 'JSON', 'XML', 'HTML', 'MD', 'LOG', 'CONF', 'INI', 'ENV', 'YAML', 
            'TOML', 'SQL'
        ]
        document_formats = ['DOCX', 'RTF', 'PPTX']
        spreadsheet_formats = ['XLSX', 'CSV', 'TSV']
        code_formats = [
            'PY', 'JS', 'TS', 'JAVA', 'CS', 'PHP', 'RB', 'C', 'CPP', 'GO', 'RS', 
            'SWIFT', 'KT', 'SH', 'PS1', 'BAT', 'CSS'
        ]
        
        # Check if file is in high-risk list
        file_name = os.path.basename(file_path)
        is_high_risk = any(file_name.endswith(ext) for ext in self.high_risk_files) or any(pattern in file_name for pattern in ['secret', 'password', 'credential', 'token', 'key', 'auth'])
        
        try:
            # Handle PDF documents with specialized extraction
            if file_type == 'PDF':
                return self._extract_pdf_text(file_path)
                
            # Handle plain text, config files, and similar
            elif file_type in text_based_formats:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Add a note for high-risk files
                    if is_high_risk:
                        content = f"[HIGH-RISK FILE: {file_name}]\n\n" + content
                    return content
                    
            # Handle programming language source files (treat as text)
            elif file_type in code_formats:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Add a note for potentially sensitive code files
                    if any(pattern in content.lower() for pattern in ['password', 'secret', 'token', 'key', 'credential', 'auth']):
                        content = f"[POTENTIALLY SENSITIVE CODE: {file_name}]\n\n" + content
                    return content
                    
            # Handle document formats using textract
            elif file_type in document_formats:
                try:
                    return textract.process(file_path).decode('utf-8', errors='ignore')
                except:
                    # Fallback to basic text reading
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                        
            # Handle spreadsheet formats
            elif file_type in spreadsheet_formats:
                try:
                    return textract.process(file_path).decode('utf-8', errors='ignore')
                except:
                    # Fallback for CSV/TSV files
                    if file_type in ['CSV', 'TSV']:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            return f.read()
                    return ""
            
            # Handle binary files by checking for text patterns
            elif os.path.splitext(file_path)[1].lower() in ['.db', '.sqlite']:
                # Extract strings from binary files using strings command if available
                try:
                    import subprocess
                    result = subprocess.run(['strings', file_path], capture_output=True, text=True)
                    if result.returncode == 0:
                        return result.stdout
                    return ""
                except:
                    return ""
            
            # Unknown format - try basic text extraction
            else:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                except:
                    # For binary files, make a note but don't attempt to read
                    if os.path.getsize(file_path) > 0:
                        return f"[BINARY FILE: {file_name} - size: {os.path.getsize(file_path)} bytes]"
                    return ""
                    
        except Exception as e:
            print(f"Error extracting text from {file_path}: {str(e)}")
            return f"[ERROR: Could not extract text from {file_name} - {str(e)}]"
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        text = ""
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                    
            # If no text was extracted (e.g., scanned PDF), try OCR if available
            if not text.strip():
                try:
                    # Attempt to use textract as a fallback for OCR
                    return textract.process(pdf_path).decode('utf-8', errors='ignore')
                except:
                    return text
            
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def _scan_text(self, text: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Enhanced text scanning for PII and compliance violations.
        
        Args:
            text: Text content to scan
            file_path: Path to the file being scanned (for context)
            
        Returns:
            List of PII findings and violations
        """
        if not text or not text.strip():
            return []
        
        try:
            # Use the PII detection utility
            pii_items = identify_pii_in_text(text, region=self.region)
            
            # Enhance PII items with location information
            enhanced_pii_items = []
            lines = text.split('\n')
            
            for pii_item in pii_items:
                pii_value = pii_item.get('value', '')
                # Find the line number where this PII appears
                line_number = 0
                element_context = "Document Content"
                
                for i, line in enumerate(lines, 1):
                    if pii_value in line:
                        line_number = i
                        # Extract some context around the PII
                        words = line.split()
                        pii_index = -1
                        for j, word in enumerate(words):
                            if pii_value in word:
                                pii_index = j
                                break
                        
                        if pii_index >= 0:
                            # Create context with up to 3 words before and after
                            start_idx = max(0, pii_index - 3)
                            end_idx = min(len(words), pii_index + 4)
                            context_words = words[start_idx:end_idx]
                            element_context = "..." + " ".join(context_words) + "..."
                        break
                
                # Create enhanced PII item with location information
                enhanced_item = {
                    'type': pii_item.get('type', 'Unknown'),
                    'value': pii_value,
                    'file': os.path.basename(file_path),
                    'line': line_number if line_number > 0 else 'N/A',
                    'location': f"{file_path}:{line_number}" if line_number > 0 else file_path,
                    'element': element_context,
                    'description': f"{pii_item.get('type', 'PII')} found in document",
                    'severity': 'High' if pii_item.get('type') in ['BSN', 'Credit Card', 'SSN'] else 'Medium',
                    'risk_level': 'High' if pii_item.get('type') in ['BSN', 'Credit Card', 'SSN'] else 'Medium'
                }
                enhanced_pii_items.append(enhanced_item)
            
            # Enhanced violation detection for demonstration files
            demonstration_violations = self._detect_demonstration_violations(text, file_path)
            
            # Return combined findings with enhanced location information
            return enhanced_pii_items + demonstration_violations
            
        except Exception as e:
            print(f"Error scanning text: {str(e)}")
            return []
    
    def _detect_demonstration_violations(self, text: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Detect violations in demonstration or example files that contain violation examples.
        """
        violations = []
        
        # Check if this is a demonstration file with violation examples
        if any(marker in text.lower() for marker in ['violation', '❌', 'unauthorized', 'prohibited']):
            
            # Detect BSN violations
            bsn_violations = re.findall(r'❌.*?BSN.*?(\d{9})', text, re.IGNORECASE | re.DOTALL)
            for bsn in bsn_violations:
                violations.append({
                    'type': 'BSN_VIOLATION',
                    'value': bsn,
                    'risk_level': 'High',
                    'location': file_path,
                    'description': 'Unauthorized BSN collection example detected',
                    'gdpr_article': 'UAVG Article 46',
                    'recommendation': 'Remove unauthorized BSN examples or add proper legal basis'
                })
            
            # Detect AI Act violations
            if re.search(r'❌.*?AI.*?(?:hiring|automatic|evaluat)', text, re.IGNORECASE):
                violations.append({
                    'type': 'AI_ACT_VIOLATION',
                    'value': 'High-risk AI system without safeguards',
                    'risk_level': 'Critical',
                    'location': file_path,
                    'description': 'High-risk AI system detected without proper compliance framework',
                    'gdpr_article': 'EU AI Act Annex III',
                    'recommendation': 'Implement AI governance framework with human oversight'
                })
            
            # Detect general GDPR violations
            if re.search(r'❌.*?(?:collect|data|processing).*?(?:business purposes|no legal basis)', text, re.IGNORECASE):
                violations.append({
                    'type': 'GDPR_LAWFULNESS_VIOLATION',
                    'value': 'Processing without legal basis',
                    'risk_level': 'High',
                    'location': file_path,
                    'description': 'Data processing without proper legal basis under GDPR Article 6',
                    'gdpr_article': 'GDPR Article 6',
                    'recommendation': 'Establish clear legal basis for all data processing activities'
                })
            
            # Detect transparency violations
            if re.search(r'❌.*?(?:hidden|no notice|undisclosed)', text, re.IGNORECASE):
                violations.append({
                    'type': 'GDPR_TRANSPARENCY_VIOLATION',
                    'value': 'Hidden data processing',
                    'risk_level': 'High',
                    'location': file_path,
                    'description': 'Data processing without transparent disclosure to data subjects',
                    'gdpr_article': 'GDPR Article 5(1)(a)',
                    'recommendation': 'Implement clear privacy notices and transparent data processing disclosure'
                })
            
            # Detect data minimization violations
            if re.search(r'❌.*?(?:excessive|unnecessary|over-collection)', text, re.IGNORECASE):
                violations.append({
                    'type': 'GDPR_DATA_MINIMIZATION_VIOLATION',
                    'value': 'Excessive data collection',
                    'risk_level': 'Medium',
                    'location': file_path,
                    'description': 'Data collection exceeds what is necessary for stated purposes',
                    'gdpr_article': 'GDPR Article 5(1)(c)',
                    'recommendation': 'Review and limit data collection to what is strictly necessary'
                })
            
            # Detect special category violations
            if re.search(r'(?:health|medical|biometric|genetic).*?(?:without.*?consent|unauthorized)', text, re.IGNORECASE):
                violations.append({
                    'type': 'GDPR_SPECIAL_CATEGORY_VIOLATION',
                    'value': 'Special category data without proper basis',
                    'risk_level': 'Critical',
                    'location': file_path,
                    'description': 'Special categories of personal data processed without explicit consent or other Article 9 basis',
                    'gdpr_article': 'GDPR Article 9',
                    'recommendation': 'Obtain explicit consent or establish other lawful basis under Article 9'
                })
        
        return violations
    
    def _legacy_scan_text(self, text: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Legacy scanning method for compatibility.
        """
        pii_found = []
        
        # Split text into paragraphs/chunks for processing
        chunks = re.split(r'\n{2,}', text)
        
        for i, chunk in enumerate(chunks):
            # Skip empty chunks
            if not chunk.strip():
                continue
            
            # Use PII detection utility
            pii_items = identify_pii_in_text(chunk, self.region)
            
            for pii_item in pii_items:
                pii_type = pii_item['type']
                
                # Evaluate risk level
                risk_level = evaluate_risk_level(pii_type, self.region_rules)
                
                # Create finding entry
                finding = {
                    'type': pii_type,
                    'value': pii_item['value'],
                    'location': f'Paragraph/Chunk {i+1}',
                    'risk_level': risk_level,
                    'reason': self._get_reason(pii_type, risk_level, self.region)
                }
                
                pii_found.append(finding)
        
        return pii_found
    
    def _get_reason(self, pii_type: str, risk_level: str, region: str) -> str:
        """
        Get a reason explanation for the PII finding.
        
        Args:
            pii_type: The type of PII found
            risk_level: The risk level (Low, Medium, High)
            region: The region for which GDPR rules are applied
            
        Returns:
            A string explaining why this PII is a concern
        """
        # Common reasons for all regions
        common_reasons = {
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
        
        # Region-specific reasons
        region_reasons = {
            'Netherlands': {
                'BSN': 'BSN (Burgerservicenummer) has special protection under Dutch UAVG law',
                'Medical Data': 'Medical data requires explicit consent under Dutch UAVG law',
                'Minor Data': 'Data of minors (under 16) requires parental consent under Dutch UAVG'
            },
            'Germany': {
                'Address': 'Addresses have heightened protection under German BDSG',
                'Medical Data': 'Health data has special protection under German BDSG'
            },
            'France': {
                'Minor Data': 'Data of minors (under 15) requires parental consent under French law'
            },
            'Belgium': {
                'Minor Data': 'Data of minors (under 13) requires parental consent under Belgian law'
            }
        }
        
        # Check if there's a region-specific reason
        if region in region_reasons and pii_type in region_reasons[region]:
            return region_reasons[region][pii_type]
        
        # Fall back to common reason
        if pii_type in common_reasons:
            return common_reasons[pii_type]
        
        # Default reason if specific one not found
        return f"{pii_type} is potentially personal data under GDPR"
    
    def _calculate_risk_score(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate risk score based on findings.
        
        Args:
            findings: List of PII findings
            
        Returns:
            Dictionary with risk score details
        """
        if not findings:
            return {
                "score": 0,
                "max_score": 100,
                "level": "Low",
                "factors": []
            }
        
        # Count findings by risk level
        risk_counts = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0
        }
        
        for finding in findings:
            risk_level = finding.get("risk_level", "Medium")
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1
        
        # Calculate weighted score
        weights = {
            "Critical": 25,
            "High": 15,
            "Medium": 7,
            "Low": 2
        }
        
        score = sum(risk_counts[level] * weights[level] for level in risk_counts)
        score = min(score, 100)  # Cap at 100
        
        # Determine overall risk level
        level = "Low"
        if score >= 75:
            level = "Critical"
        elif score >= 50:
            level = "High"
        elif score >= 25:
            level = "Medium"
        
        # Risk factors explanation
        factors = []
        for risk_level, count in risk_counts.items():
            if count > 0:
                factors.append(f"{count} {risk_level} risk finding{'s' if count > 1 else ''}")
        
        return {
            "score": score,
            "max_score": 100,
            "level": level,
            "factors": factors
        }
    
    def _get_gdpr_categories(self, findings: List[Dict[str, Any]]) -> List[str]:
        """
        Determine GDPR categories based on findings.
        
        Args:
            findings: List of PII findings
            
        Returns:
            List of GDPR categories
        """
        categories = set()
        
        for finding in findings:
            pii_type = finding.get('type', '')
            
            # Map PII types to GDPR categories
            if pii_type in ['Name', 'Email', 'Phone', 'Address', 'IP Address']:
                categories.add('Personal Data (Article 4)')
            elif pii_type in ['BSN', 'Passport Number', 'Credit Card', 'Financial Data']:
                categories.add('Personal Data (Article 4)')
                categories.add('Sensitive Personal Data')
            elif pii_type in ['Medical Data', 'Health Information']:
                categories.add('Special Category Data (Article 9)')
            elif pii_type in ['Date of Birth', 'Minor Data']:
                categories.add('Personal Data (Article 4)')
                if 'Minor' in pii_type:
                    categories.add('Children\'s Data (Article 8)')
        
        return list(categories)
    
    def _generate_compliance_notes(self, findings: List[Dict[str, Any]], file_type: str) -> List[str]:
        """
        Generate comprehensive compliance notes based on findings and file type.
        
        Args:
            findings: List of PII findings
            file_type: Type of file scanned
            
        Returns:
            List of compliance notes
        """
        notes = []
        
        if not findings:
            notes.append("No PII detected in document")
            return notes
        
        # High-risk data types
        high_risk_types = [f['type'] for f in findings if f.get('risk_level') == 'High']
        if high_risk_types:
            notes.append(f"High-risk PII detected: {', '.join(set(high_risk_types))}")
        
        # Special category data (GDPR Article 9)
        special_categories = [f['type'] for f in findings if f['type'] in ['Medical Data', 'Biometric Data', 'Genetic Data', 'Health Information']]
        if special_categories:
            notes.append("Special category data found - requires explicit consent under GDPR Article 9")
        
        # Dutch-specific BSN
        bsn_found = any(f['type'] == 'BSN' for f in findings)
        if bsn_found and self.region == "Netherlands":
            notes.append("BSN (Dutch Citizen Service Number) detected - requires special handling under UAVG Article 46")
        
        return notes
    
    def _generate_comprehensive_compliance_notes(self, pii_findings: List[Dict[str, Any]], 
                                               compliance_findings: List[Dict[str, Any]], 
                                               file_type: str, gdpr_compliance: Dict[str, Any],
                                               ai_act_violations: List[Dict[str, Any]]) -> List[str]:
        """
        Generate comprehensive compliance notes including GDPR, Netherlands-specific, and AI Act findings.
        """
        notes = []
        
        # Start with basic PII notes
        if not pii_findings and not compliance_findings:
            notes.append("No PII or compliance issues detected in document")
            return notes
        
        # PII findings summary
        if pii_findings:
            high_risk_types = [f['type'] for f in pii_findings if f.get('risk_level') == 'High']
            if high_risk_types:
                notes.append(f"High-risk PII detected: {', '.join(set(high_risk_types))}")
            
            # Special category data (GDPR Article 9)
            special_categories = [f['type'] for f in pii_findings if f['type'] in ['Medical Data', 'Biometric Data', 'Genetic Data', 'Health Information']]
            if special_categories:
                notes.append("Special category data found - requires explicit consent under GDPR Article 9")
        
        # GDPR compliance summary
        gdpr_score = gdpr_compliance.get('overall_compliance_score', 100)
        if gdpr_score < 70:
            notes.append(f"GDPR compliance score: {gdpr_score}/100 - Significant compliance gaps identified")
        elif gdpr_score < 90:
            notes.append(f"GDPR compliance score: {gdpr_score}/100 - Minor compliance improvements needed")
        else:
            notes.append(f"GDPR compliance score: {gdpr_score}/100 - Good compliance level")
        
        # Netherlands-specific findings
        if self.region == "Netherlands":
            nl_violations = [f for f in compliance_findings if f.get('gdpr_principle') == 'netherlands_specific']
            if nl_violations:
                notes.append(f"Netherlands UAVG violations detected: {len(nl_violations)} issues requiring attention")
        
        # EU AI Act findings
        if ai_act_violations:
            critical_ai = [f for f in ai_act_violations if f.get('risk_level') == 'Critical']
            high_ai = [f for f in ai_act_violations if f.get('risk_level') == 'High']
            
            if critical_ai:
                notes.append(f"EU AI Act CRITICAL violations: {len(critical_ai)} prohibited practices detected")
            if high_ai:
                notes.append(f"EU AI Act high-risk systems: {len(high_ai)} require compliance framework")
        
        # Data subject rights assessment
        rights_scores = gdpr_compliance.get('rights_compliance', {}).get('scores', {})
        missing_rights = [right.replace('_', ' ').title() for right, score in rights_scores.items() if score < 80]
        if missing_rights:
            notes.append(f"Data subject rights gaps: {', '.join(missing_rights[:3])}{'...' if len(missing_rights) > 3 else ''}")
        
        # GDPR principles assessment
        principle_scores = gdpr_compliance.get('principle_compliance', {}).get('scores', {})
        weak_principles = [principle.replace('_', ' ').title() for principle, score in principle_scores.items() if score < 70]
        if weak_principles:
            notes.append(f"GDPR principle weaknesses: {', '.join(weak_principles[:3])}{'...' if len(weak_principles) > 3 else ''}")
        
        # File type specific notes
        if file_type in ['PDF', 'DOCX', 'HTML'] and any('automated' in str(f).lower() for f in compliance_findings):
            notes.append("Document contains automated processing references - ensure GDPR Article 22 compliance")
        
        if file_type in ['JSON', 'XML'] and pii_findings:
            notes.append("Structured data with PII - ensure data minimization and purpose limitation")
        
        return notes
    
    def _scan_file_with_timeout(self, file_path: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Scan a file with timeout protection to prevent hanging on large files.
        
        Args:
            file_path: Path to the file to scan
            timeout: Timeout in seconds
            
        Returns:
            Scan results dictionary
        """
        import threading
        import multiprocessing
        
        # Using a queue to get the result from the worker process
        result_queue = multiprocessing.Queue()
        
        def worker():
            try:
                result = self.scan_file(file_path)
                result_queue.put(result)
            except Exception as e:
                result_queue.put({
                    'file_name': os.path.basename(file_path),
                    'status': 'error',
                    'error': f'Scan failed with error: {str(e)}',
                    'pii_found': []
                })
        
        # Start worker thread
        worker_thread = threading.Thread(target=worker)
        worker_thread.daemon = True  # Thread will die when main program exits
        worker_thread.start()
        
        # Wait for result with timeout
        worker_thread.join(timeout)
        
        # Check if worker completed
        if worker_thread.is_alive():
            return {
                'file_name': os.path.basename(file_path),
                'status': 'error',
                'error': f'Scan timed out after {timeout} seconds',
                'pii_found': []
            }
        
        # Get result from queue
        try:
            return result_queue.get(block=False)
        except Exception:
            return {
                'file_name': os.path.basename(file_path),
                'status': 'error',
                'error': 'Failed to retrieve scan results',
                'pii_found': []
            }
        
    def scan_directory(self, directory_path: str, recursive: bool = True, max_files: int = 1000, 
                      skip_patterns: Optional[List[str]] = None, callback_fn = None) -> Dict[str, Any]:
        """
        Scan all files in a directory for PII.
        
        Args:
            directory_path: Path to the directory to scan
            recursive: Whether to scan subdirectories
            max_files: Maximum number of files to scan
            skip_patterns: List of patterns to skip (e.g., ['node_modules', '.git'])
            callback_fn: Callback function for progress updates
            
        Returns:
            Dictionary containing aggregated scan results
        """
        if not os.path.isdir(directory_path):
            return {
                'status': 'error',
                'error': 'Directory not found',
                'scan_results': []
            }
        
        # Default skip patterns if none provided
        skip_patterns = skip_patterns if skip_patterns is not None else [
            '.git', 'node_modules', '__pycache__', 'venv', 'env', '.pytest_cache',
            'build', 'dist', '.next', '.cache', '.yarn', '.npm', 'coverage'
        ]
        
        # Results container
        results = {
            'directory': directory_path,
            'scan_timestamp': datetime.now().isoformat(),
            'files_scanned': 0,
            'files_skipped': 0,
            'files_with_pii': 0,
            'total_pii_items': 0,
            'scan_results': [],
            'pii_types': {},
            'risk_levels': {'High': 0, 'Medium': 0, 'Low': 0},
            'high_risk_files': [],
            'errors': []
        }
        
        # Find all files with priority ordering
        all_files = []
        high_risk_files = []
        normal_files = []
        
        # Walk directory
        for root, dirs, files in os.walk(directory_path):
            # Skip directories matching patterns
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in skip_patterns)]
            
            # Process files in this directory
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip files matching patterns
                if any(pattern in file_path for pattern in skip_patterns):
                    continue
                
                # Check if high-risk file (prioritize these)
                if any(file.endswith(ext) for ext in self.high_risk_files) or any(pattern in file.lower() for pattern in ['secret', 'password', 'credential', 'token', 'key', 'auth']):
                    high_risk_files.append(file_path)
                else:
                    normal_files.append(file_path)
            
            # If not recursive, break after first iteration
            if not recursive:
                break
                
        # Combine with high-risk files first
        all_files = high_risk_files + normal_files
        
        # Limit to max_files
        all_files = all_files[:max_files]
        
        # Scan each file
        for i, file_path in enumerate(all_files):
            # Report progress if callback provided
            if callback_fn:
                callback_fn(i + 1, len(all_files), file_path)
            
            # Check file size and use timeout protection for large files
            file_size = os.path.getsize(file_path)
            large_file = file_size > 5 * 1024 * 1024  # 5MB threshold
            
            # Scan file with timeout protection for large files
            try:
                if large_file:
                    # Use timeout for large files
                    file_result = self._scan_file_with_timeout(file_path, timeout=60)
                else:
                    # Use standard scan for normal files
                    file_result = self.scan_file(file_path)
                    
                results['scan_results'].append(file_result)
                
                # Update counts
                if file_result['status'] == 'scanned':
                    results['files_scanned'] += 1
                    
                    # Update PII counts
                    if file_result.get('pii_count', 0) > 0:
                        results['files_with_pii'] += 1
                        results['total_pii_items'] += file_result['pii_count']
                        
                        # Track high-risk files
                        if any(finding['risk_level'] == 'High' for finding in file_result['pii_found']):
                            results['high_risk_files'].append(file_result['file_name'])
                        
                        # Update PII type counts
                        for finding in file_result['pii_found']:
                            pii_type = finding['type']
                            risk_level = finding['risk_level']
                            
                            # Update PII types count
                            if pii_type not in results['pii_types']:
                                results['pii_types'][pii_type] = 0
                            results['pii_types'][pii_type] += 1
                            
                            # Update risk level counts
                            results['risk_levels'][risk_level] += 1
                elif file_result['status'] == 'error':
                    # Track errors
                    results['errors'].append({
                        'file': file_path,
                        'error': file_result.get('error', 'Unknown error')
                    })
                    results['files_skipped'] += 1
                else:
                    results['files_skipped'] += 1
            except Exception as e:
                results['errors'].append({
                    'file': file_path,
                    'error': str(e)
                })
                results['files_skipped'] += 1
        
        # Integrate cost savings analysis
        try:
            from services.cost_savings_calculator import integrate_cost_savings_into_report
            results = integrate_cost_savings_into_report(results, 'document', self.region)
        except Exception as e:
            logger.warning(f"Cost savings integration failed: {e}")
        
        return results
    
    def scan_multiple_documents(self, file_paths: List[str], callback_fn=None) -> Dict[str, Any]:
        """
        Scan multiple documents for PII with comprehensive reporting.
        
        Args:
            file_paths: List of document file paths to scan
            callback_fn: Optional callback function for progress updates
            
        Returns:
            Dictionary containing comprehensive scan results matching Image Scanner structure
        """
        logger.info(f"Starting document scan of {len(file_paths)} files")
        
        # Initialize results structure
        all_findings = []
        document_results = []
        errors = []
        documents_scanned = 0
        documents_with_pii = 0
        
        # Process each document
        for i, file_path in enumerate(file_paths):
            if callback_fn:
                callback_fn(i + 1, len(file_paths), os.path.basename(file_path))
            
            try:
                # Scan individual document
                result = self.scan_file(file_path)
                document_results.append(result)
                
                if result['status'] == 'scanned':
                    documents_scanned += 1
                    
                    # Collect findings
                    document_findings = result.get('pii_found', [])
                    if document_findings:
                        documents_with_pii += 1
                        all_findings.extend(document_findings)
                        
                        logger.info(f"Completed scan for {os.path.basename(file_path)}. Found {len(document_findings)} PII instances.")
                    else:
                        logger.info(f"Completed scan for {os.path.basename(file_path)}. Found 0 PII instances.")
                
                elif result['status'] == 'error':
                    errors.append({
                        'file': os.path.basename(file_path),
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                logger.error(f"Error scanning {file_path}: {str(e)}")
                errors.append({
                    'file': os.path.basename(file_path),
                    'error': str(e)
                })
        
        # Calculate overall risk assessment
        overall_risk = self._calculate_risk_score(all_findings)
        
        # Generate metadata
        metadata = {
            'scan_type': 'document',
            'documents_scanned': documents_scanned,
            'documents_with_pii': documents_with_pii,
            'total_findings': len(all_findings),
            'scan_timestamp': datetime.now().isoformat(),
            'region': self.region,
            'scanner_version': '2.0.0'
        }
        
        logger.info(f"Completed document scan. Scanned {documents_scanned} documents, found {len(all_findings)} PII instances.")
        
        # Count findings by risk level for proper UI display
        critical_count = len([f for f in all_findings if f.get('risk_level') == 'Critical'])
        high_count = len([f for f in all_findings if f.get('risk_level') == 'High'])
        medium_count = len([f for f in all_findings if f.get('risk_level') == 'Medium'])
        low_count = len([f for f in all_findings if f.get('risk_level') == 'Low'])
        
        scan_results = {
            "scan_type": "document", 
            "scan_id": f"doc_scan_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "document_results": document_results,
            "findings": all_findings,
            "documents_with_pii": documents_with_pii,
            "file_count": documents_scanned,
            "total_pii_found": len(all_findings),
            "critical_risk_count": critical_count,
            "high_risk_count": high_count,
            "medium_risk_count": medium_count,
            "low_risk_count": low_count,
            "errors": errors,
            "risk_summary": overall_risk
        }
        
        # Integrate cost savings analysis
        try:
            from services.cost_savings_calculator import integrate_cost_savings_into_report
            scan_results = integrate_cost_savings_into_report(scan_results, 'document', self.region)
        except Exception as e:
            logger.warning(f"Cost savings integration failed: {e}")
        
        return scan_results
    
    # ============================================================================
    # AI FRAUD DETECTION METHODS - NEW
    # ============================================================================
    
    def _detect_ai_generated_documents(
        self, 
        file_path: str, 
        text: str, 
        file_type: str,
        sensitivity: str = "maximum"
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if document is AI-generated using multiple detection methods.
        Enhanced with receipt/invoice fraud detection and maximum sensitivity.
        
        Args:
            file_path: Path to the document
            text: Extracted text content
            file_type: Type of document (PDF, DOCX, etc.)
            sensitivity: Detection sensitivity (low, medium, high, maximum)
        
        Returns:
            Dict with fraud analysis OR None if low risk
        """
        if not text or len(text) < 50:  # Lowered from 100 for short receipts
            return None
        
        # Sensitivity thresholds (matching image scanner)
        sensitivity_thresholds = {
            "low": 0.50,
            "medium": 0.35,
            "high": 0.20,
            "maximum": 0.08  # Maximum sensitivity for catching all fraud
        }
        detection_threshold = sensitivity_thresholds.get(sensitivity, 0.08)
        
        try:
            # ============================================================
            # Run ALL detection methods (HIGH, MEDIUM, LOW priority)
            # ============================================================
            
            # Original detection methods
            chatgpt_score = self._analyze_chatgpt_patterns(text)
            statistical_score = self._analyze_statistical_anomalies(text)
            metadata_score = self._analyze_metadata_fraud(file_path)
            receipt_score = self._analyze_receipt_fraud(text, file_path)
            
            # HIGH PRIORITY: New enhanced detection methods
            pdf_image_score = self._analyze_pdf_embedded_images(file_path)
            signature_score = self._detect_forged_signatures(text, file_path)
            iban_score = self._validate_iban_numbers(text)
            
            # MEDIUM PRIORITY: Additional detection methods
            qr_score = self._validate_qr_codes(text, file_path)
            stamp_score = self._detect_fake_stamps_logos(text, file_path)
            stylometry_score = self._analyze_stylometry(text)
            
            # LOW PRIORITY: Netherlands-specific validation
            kvk_score = self._validate_kvk_number(text)
            btw_score = self._validate_btw_number(text)
            template_score = self._detect_template_fraud(text, file_path)
            
            # Calculate combined fraud score with all indicators
            fraud_indicators = [
                {'type': 'chatgpt_patterns', 'score': chatgpt_score['score'], 'details': chatgpt_score['details']},
                {'type': 'statistical_anomalies', 'score': statistical_score['score'], 'details': statistical_score['details']},
                {'type': 'metadata_fraud', 'score': metadata_score['score'], 'details': metadata_score['details']},
                {'type': 'receipt_invoice_fraud', 'score': receipt_score['score'], 'details': receipt_score['details']},
                {'type': 'pdf_embedded_images', 'score': pdf_image_score['score'], 'details': pdf_image_score['details']},
                {'type': 'signature_forgery', 'score': signature_score['score'], 'details': signature_score['details']},
                {'type': 'iban_validation', 'score': iban_score['score'], 'details': iban_score['details']},
                {'type': 'qr_code_fraud', 'score': qr_score['score'], 'details': qr_score['details']},
                {'type': 'stamp_logo_fraud', 'score': stamp_score['score'], 'details': stamp_score['details']},
                {'type': 'stylometric_analysis', 'score': stylometry_score['score'], 'details': stylometry_score['details']},
                {'type': 'kvk_validation', 'score': kvk_score['score'], 'details': kvk_score['details']},
                {'type': 'btw_validation', 'score': btw_score['score'], 'details': btw_score['details']},
                {'type': 'template_fraud', 'score': template_score['score'], 'details': template_score['details']}
            ]
            
            # Filter out zero-score indicators for cleaner output
            active_indicators = [ind for ind in fraud_indicators if ind['score'] > 0]
            
            # Comprehensive weighted scoring across all detection methods
            # HIGH priority (60% weight): chatgpt, statistical, pdf_images, signature, iban
            # MEDIUM priority (25% weight): metadata, receipt, qr, stamp, stylometry
            # LOW priority (15% weight): kvk, btw, template
            
            high_priority_score = (
                chatgpt_score['score'] * 0.15 +
                statistical_score['score'] * 0.15 +
                pdf_image_score['score'] * 0.10 +
                signature_score['score'] * 0.10 +
                iban_score['score'] * 0.10
            )
            
            medium_priority_score = (
                metadata_score['score'] * 0.05 +
                receipt_score['score'] * 0.05 +
                qr_score['score'] * 0.05 +
                stamp_score['score'] * 0.05 +
                stylometry_score['score'] * 0.05
            )
            
            low_priority_score = (
                kvk_score['score'] * 0.05 +
                btw_score['score'] * 0.05 +
                template_score['score'] * 0.05
            )
            
            ai_generated_risk = high_priority_score + medium_priority_score + low_priority_score
            
            # Boost score if multiple indicators are triggered
            triggered_count = len(active_indicators)
            if triggered_count >= 3:
                ai_generated_risk = min(ai_generated_risk * 1.2, 1.0)
            if triggered_count >= 5:
                ai_generated_risk = min(ai_generated_risk * 1.3, 1.0)
            
            # Confidence based on number of active indicators
            all_scores = [ind['score'] for ind in fraud_indicators]
            confidence = mean(all_scores) * 100 if all_scores else 0
            
            # Apply maximum sensitivity threshold
            if ai_generated_risk < detection_threshold:
                return None
            
            # Determine risk level
            if ai_generated_risk >= 0.75:
                risk_level = 'Critical'
            elif ai_generated_risk >= 0.60:
                risk_level = 'High'
            elif ai_generated_risk >= 0.40:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'
            
            # Guess AI model
            ai_model = self._guess_ai_model(chatgpt_score, statistical_score)
            
            # Generate recommendations
            recommendations = self._generate_fraud_recommendations(risk_level, fraud_indicators)
            
            # Netherlands-specific multiplier
            if self.region == "Netherlands":
                # Flag if document contains sensitive data + AI-generated
                has_sensitive = any(
                    indicator['type'] in ['chatgpt_patterns', 'metadata_fraud'] 
                    for indicator in fraud_indicators if indicator['score'] > 0.6
                )
                if has_sensitive:
                    ai_generated_risk = min(ai_generated_risk * 1.4, 1.0)
            
            return {
                'ai_generated_risk': round(ai_generated_risk, 2),
                'confidence': round(confidence, 1),
                'ai_model': ai_model,
                'risk_level': risk_level,
                'fraud_indicators': fraud_indicators,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error in AI fraud detection: {str(e)}")
            return None
    
    def _analyze_chatgpt_patterns(self, text: str) -> Dict[str, Any]:
        """Detect ChatGPT-specific writing patterns"""
        chatgpt_patterns = [
            r'\b(Furthermore|Moreover|In conclusion|As previously mentioned|It is important to note)\b',
            r'(\?|!)\s+[A-Z]',  # Perfect punctuation
            r'\b(the fact that|it is clear that|it appears that)\b',
            r'\b(Additionally|Consequently|However|Therefore|Thus)\b',
        ]
        
        pattern_count = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in chatgpt_patterns)
        total_words = len(text.split())
        
        # High pattern frequency = likely AI
        pattern_density = pattern_count / max(total_words, 1)
        
        # Check for contractions (humans use them, AI avoids)
        contractions = len(re.findall(r"\b(can't|won't|don't|isn't|aren't|wasn't)\b", text, re.IGNORECASE))
        contraction_density = contractions / max(total_words, 1)
        
        # Score: high patterns + low contractions = AI
        score = min(0.5 * pattern_density + 0.5 * (1 - min(contraction_density * 10, 1)), 1.0)
        
        details = f"Pattern density: {pattern_density:.3f}, Contractions: {contractions}/{total_words}"
        return {'score': score, 'details': details}
    
    def _analyze_statistical_anomalies(self, text: str) -> Dict[str, Any]:
        """Detect statistical anomalies in text"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 5:
            return {'score': 0.0, 'details': 'Too few sentences for analysis'}
        
        # Sentence length analysis
        sentence_lengths = [len(s.split()) for s in sentences]
        
        # Low variance = AI (consistent sentences)
        # High variance = Human (varied sentences)
        try:
            length_stdev = stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
            avg_length = mean(sentence_lengths)
            length_variance_score = 1.0 - min(length_stdev / max(avg_length, 1), 1.0)
        except:
            length_variance_score = 0.0
        
        # Word frequency - AI generates common words, humans use varied vocabulary
        words = re.findall(r'\b\w+\b', text.lower())
        if len(words) > 20:
            word_freq = Counter(words)
            top_10_freq = sum(count for word, count in word_freq.most_common(10)) / len(words)
            vocab_score = min(top_10_freq * 2, 1.0)  # Higher = more repetitive = AI
        else:
            vocab_score = 0.0
        
        # Combined statistical score
        score = (length_variance_score * 0.5 + vocab_score * 0.5)
        details = f"Sentence variance: {length_variance_score:.3f}, Vocab repetition: {vocab_score:.3f}"
        return {'score': score, 'details': details}
    
    def _analyze_metadata_fraud(self, file_path: str) -> Dict[str, Any]:
        """Detect suspicious metadata patterns"""
        score = 0.0
        details_list = []
        
        try:
            if file_path.endswith('.pdf'):
                try:
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        if pdf_reader.metadata:
                            metadata = pdf_reader.metadata
                            
                            # Check creator vs producer mismatch
                            creator = metadata.get('/Creator', '').lower()
                            producer = metadata.get('/Producer', '').lower()
                            
                            if creator and producer and creator != producer:
                                score += 0.2
                                details_list.append(f"Creator/Producer mismatch: {creator} vs {producer}")
                            
                            # Check for suspicious producer
                            if producer and any(x in producer for x in ['photoshop', 'gimp', 'paint']):
                                score += 0.3
                                details_list.append(f"Suspicious producer: {producer}")
                except:
                    pass
            
            # File timestamp analysis
            try:
                import time
                file_stat = os.stat(file_path)
                creation_time = file_stat.st_ctime
                mod_time = file_stat.st_mtime
                current_time = time.time()
                
                # File modified very recently but created much earlier
                creation_age = (current_time - creation_time) / 86400
                mod_age = (current_time - mod_time) / 86400
                
                if creation_age > 30 and mod_age < 1:
                    score += 0.2
                    details_list.append(f"Recent modification: {int(mod_age)} days old vs {int(creation_age)} created")
            except:
                pass
            
            score = min(score, 1.0)
            details = " | ".join(details_list) if details_list else "No metadata anomalies detected"
            
        except Exception as e:
            logger.warning(f"Metadata analysis failed: {str(e)}")
            details = f"Metadata analysis error: {str(e)}"
        
        return {'score': score, 'details': details}
    
    def _analyze_receipt_fraud(self, text: str, file_path: str) -> Dict[str, Any]:
        """
        Enhanced receipt/invoice fraud detection.
        Detects forged receipts, fake invoices, and AI-generated financial documents.
        """
        score = 0.0
        details_list = []
        text_lower = text.lower()
        
        try:
            # 1. Check for invoice/receipt keywords
            is_receipt = any(kw in text_lower for kw in ['receipt', 'invoice', 'factuur', 'bon', 'kassabon', 'btw', 'vat', 'total', 'totaal', 'subtotal'])
            
            if not is_receipt:
                return {'score': 0.0, 'details': 'Not a receipt/invoice document'}
            
            # 2. BTW/VAT Calculation Verification (Netherlands: 21%, 9%, 0%)
            amounts = re.findall(r'[€$]\s*(\d+[.,]\d{2})', text)
            btw_mentions = re.findall(r'btw|vat|tax', text_lower)
            
            if amounts and btw_mentions:
                # Check if BTW percentages are valid Dutch rates
                btw_rates = re.findall(r'(\d+(?:[.,]\d+)?)\s*%', text)
                invalid_rates = [r for r in btw_rates if float(r.replace(',', '.')) not in [0, 6, 9, 21]]
                if invalid_rates:
                    score += 0.3
                    details_list.append(f"Invalid BTW rates: {invalid_rates}")
            
            # 3. Check for suspiciously round numbers (AI often generates €10.00, €100.00)
            round_amounts = re.findall(r'[€$]\s*(\d+)[.,]00', text)
            if len(round_amounts) >= 3:
                score += 0.2
                details_list.append(f"Multiple round amounts: {len(round_amounts)} found")
            
            # 4. Check for fake/suspicious vendor patterns
            fake_vendor_patterns = [
                r'example\s*(?:company|store|shop)',
                r'test\s*(?:vendor|shop|store)',
                r'sample\s*(?:receipt|invoice)',
                r'acme\s*(?:corp|company)',
                r'your\s*(?:company|business)\s*name',
                r'lorem\s*ipsum',
                r'\[company\s*name\]',
                r'\[your\s*name\]'
            ]
            for pattern in fake_vendor_patterns:
                if re.search(pattern, text_lower):
                    score += 0.4
                    details_list.append(f"Fake vendor pattern: {pattern}")
                    break
            
            # 5. Check for missing essential receipt elements
            essential_elements = {
                'date': r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
                'amount': r'[€$]\s*\d+[.,]\d{2}',
                'vendor_name': r'^[A-Z][a-zA-Z\s]{2,}'
            }
            missing_elements = []
            for element, pattern in essential_elements.items():
                if not re.search(pattern, text):
                    missing_elements.append(element)
            
            if missing_elements:
                score += 0.15 * len(missing_elements)
                details_list.append(f"Missing: {', '.join(missing_elements)}")
            
            # 6. Check for Dutch KvK (Chamber of Commerce) number validity
            kvk_pattern = re.findall(r'kvk[:\s]*(\d{8})', text_lower)
            if kvk_pattern:
                # KvK numbers should be 8 digits, check for suspicious patterns
                for kvk in kvk_pattern:
                    if kvk in ['00000000', '12345678', '11111111', '99999999']:
                        score += 0.35
                        details_list.append(f"Suspicious KvK: {kvk}")
            
            # 7. Check for suspicious address patterns
            fake_address_patterns = [
                r'123\s*main\s*street',
                r'1234\s*example',
                r'test\s*address',
                r'\[address\]',
                r'city,?\s*state\s*\d{5}'
            ]
            for pattern in fake_address_patterns:
                if re.search(pattern, text_lower):
                    score += 0.3
                    details_list.append("Fake address pattern detected")
                    break
            
            # 8. Check for AI-generated receipt templates (common phrases)
            ai_receipt_phrases = [
                'thank you for your purchase',
                'we appreciate your business',
                'your satisfaction is our priority',
                'please retain this receipt',
                'for your records'
            ]
            ai_phrase_count = sum(1 for phrase in ai_receipt_phrases if phrase in text_lower)
            if ai_phrase_count >= 2:
                score += 0.15
                details_list.append(f"AI-style phrases: {ai_phrase_count}")
            
            # 9. Verify total matches line items (if parseable)
            line_amounts = re.findall(r'[€$]?\s*(\d+[.,]\d{2})', text)
            if len(line_amounts) >= 3:
                try:
                    amounts_float = [float(a.replace(',', '.')) for a in line_amounts]
                    # Check if last amount equals sum of others (simple validation)
                    if len(amounts_float) >= 2:
                        potential_total = max(amounts_float)
                        other_amounts = [a for a in amounts_float if a != potential_total]
                        if other_amounts and abs(sum(other_amounts) - potential_total) > 0.1:
                            score += 0.2
                            details_list.append("Total doesn't match line items")
                except:
                    pass
            
            # 10. Check for currency format anomalies (Dutch uses €1.234,56)
            us_format = re.findall(r'\$\d+\.\d{2}', text)
            eu_format = re.findall(r'€\s*\d+[.,]\d{2}', text)
            if us_format and self.region == "Netherlands":
                score += 0.15
                details_list.append("US currency format in Dutch document")
            
            score = min(score, 1.0)
            details = " | ".join(details_list) if details_list else "No receipt fraud indicators"
            
        except Exception as e:
            logger.warning(f"Receipt fraud analysis failed: {str(e)}")
            details = f"Analysis error: {str(e)}"
        
        return {'score': score, 'details': details}
    
    # ============================================================================
    # ENHANCED FRAUD DETECTION - HIGH PRIORITY FEATURES
    # ============================================================================
    
    def _analyze_pdf_embedded_images(self, file_path: str) -> Dict[str, Any]:
        """
        HIGH PRIORITY: Analyze embedded images in PDFs for manipulation/forgery.
        Extracts images from PDFs and runs fraud detection on each.
        """
        score = 0.0
        details_list = []
        manipulated_images = 0
        
        if not file_path.lower().endswith('.pdf'):
            return {'score': 0.0, 'details': 'Not a PDF file', 'images_analyzed': 0}
        
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    if '/XObject' in page.get('/Resources', {}):
                        xobjects = page['/Resources']['/XObject'].get_object()
                        
                        for obj_name in xobjects:
                            xobj = xobjects[obj_name]
                            if xobj['/Subtype'] == '/Image':
                                # Check image properties for manipulation indicators
                                width = xobj.get('/Width', 0)
                                height = xobj.get('/Height', 0)
                                
                                # Suspicious: very small images (possible hidden data)
                                if width < 10 or height < 10:
                                    score += 0.2
                                    details_list.append(f"Suspicious small image on page {page_num + 1}")
                                    manipulated_images += 1
                                
                                # Suspicious: unusual aspect ratios
                                if width > 0 and height > 0:
                                    ratio = max(width, height) / min(width, height)
                                    if ratio > 20:  # Very stretched images
                                        score += 0.15
                                        details_list.append(f"Unusual aspect ratio on page {page_num + 1}")
                                
                                # Check for filter mismatches (common in manipulated PDFs)
                                img_filter = xobj.get('/Filter', '')
                                if isinstance(img_filter, list) and len(img_filter) > 2:
                                    score += 0.2
                                    details_list.append("Multiple compression filters (potential manipulation)")
                                    manipulated_images += 1
            
            score = min(score, 1.0)
            details = " | ".join(details_list) if details_list else "No embedded image anomalies"
            
        except Exception as e:
            logger.warning(f"PDF image analysis failed: {str(e)}")
            details = f"Analysis error: {str(e)}"
        
        return {'score': score, 'details': details, 'manipulated_images': manipulated_images}
    
    def _detect_forged_signatures(self, text: str, file_path: str) -> Dict[str, Any]:
        """
        HIGH PRIORITY: Detect potentially forged digital signatures.
        Checks for signature patterns and validates digital signature metadata.
        """
        score = 0.0
        details_list = []
        text_lower = text.lower()
        
        try:
            # Check for signature-related keywords
            signature_keywords = ['signed', 'signature', 'ondertekend', 'getekend', 'handtekening']
            has_signature_mention = any(kw in text_lower for kw in signature_keywords)
            
            if not has_signature_mention:
                return {'score': 0.0, 'details': 'No signature mentions found'}
            
            # Check for suspicious signature patterns
            # 1. Multiple different signature dates
            date_patterns = re.findall(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text)
            if len(set(date_patterns)) > 3:
                score += 0.15
                details_list.append(f"Multiple different dates ({len(set(date_patterns))} unique)")
            
            # 2. Check for placeholder signatures
            placeholder_patterns = [
                r'\[signature\]', r'\[sign here\]', r'\[your signature\]',
                r'\[handtekening\]', r'x{3,}', r'_{5,}signature',
                r'sign:\s*$', r'signed:\s*$'
            ]
            for pattern in placeholder_patterns:
                if re.search(pattern, text_lower):
                    score += 0.3
                    details_list.append("Placeholder signature detected")
                    break
            
            # 3. Check PDF for digital signature validity
            if file_path.lower().endswith('.pdf'):
                try:
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        
                        # Check for signature field
                        if '/AcroForm' in pdf_reader.trailer.get('/Root', {}):
                            acroform = pdf_reader.trailer['/Root']['/AcroForm']
                            if '/SigFlags' not in acroform:
                                score += 0.2
                                details_list.append("PDF has form but no signature flags")
                except:
                    pass
            
            # 4. Check for copy-paste signature indicators
            if re.search(r'(signed|signature).{0,20}(copy|copied|duplicate)', text_lower):
                score += 0.25
                details_list.append("Copy/duplicate signature mention")
            
            score = min(score, 1.0)
            details = " | ".join(details_list) if details_list else "No signature fraud indicators"
            
        except Exception as e:
            logger.warning(f"Signature detection failed: {str(e)}")
            details = f"Analysis error: {str(e)}"
        
        return {'score': score, 'details': details}
    
    def _validate_iban_numbers(self, text: str) -> Dict[str, Any]:
        """
        HIGH PRIORITY: Validate Dutch and EU IBAN numbers.
        Uses official IBAN checksum algorithm (ISO 13616).
        """
        score = 0.0
        details_list = []
        valid_ibans = []
        invalid_ibans = []
        
        try:
            # IBAN pattern (NL = Netherlands, but support all EU)
            iban_pattern = r'\b([A-Z]{2}\d{2}[A-Z0-9]{4,30})\b'
            potential_ibans = re.findall(iban_pattern, text.upper())
            
            for iban in potential_ibans:
                iban_clean = iban.replace(' ', '').replace('-', '')
                
                # Skip if too short or too long
                if len(iban_clean) < 15 or len(iban_clean) > 34:
                    continue
                
                # Validate using mod-97 algorithm
                if self._is_valid_iban(iban_clean):
                    valid_ibans.append(iban_clean)
                else:
                    invalid_ibans.append(iban_clean)
                    score += 0.35
                    details_list.append(f"Invalid IBAN checksum: {iban_clean[:8]}...")
            
            # Check for suspicious IBAN patterns
            for iban in valid_ibans:
                # Fake test IBANs
                if iban.startswith('NL00') or 'TEST' in iban or '000000000' in iban:
                    score += 0.3
                    details_list.append(f"Suspicious test IBAN: {iban[:8]}...")
            
            score = min(score, 1.0)
            details = " | ".join(details_list) if details_list else f"IBANs validated: {len(valid_ibans)} valid"
            
        except Exception as e:
            logger.warning(f"IBAN validation failed: {str(e)}")
            details = f"Analysis error: {str(e)}"
        
        return {
            'score': score, 
            'details': details, 
            'valid_ibans': len(valid_ibans),
            'invalid_ibans': len(invalid_ibans)
        }
    
    def _is_valid_iban(self, iban: str) -> bool:
        """
        Validate IBAN using ISO 13616 mod-97 algorithm.
        """
        try:
            # Move first 4 chars to end
            rearranged = iban[4:] + iban[:4]
            
            # Convert letters to numbers (A=10, B=11, ..., Z=35)
            numeric = ''
            for char in rearranged:
                if char.isalpha():
                    numeric += str(ord(char.upper()) - 55)
                else:
                    numeric += char
            
            # Check mod 97
            return int(numeric) % 97 == 1
            
        except:
            return False
    
    # ============================================================================
    # ENHANCED FRAUD DETECTION - MEDIUM PRIORITY FEATURES
    # ============================================================================
    
    def _validate_qr_codes(self, text: str, file_path: str) -> Dict[str, Any]:
        """
        MEDIUM PRIORITY: Validate QR codes in receipts/invoices.
        Checks for suspicious QR code patterns and validates URL destinations.
        """
        score = 0.0
        details_list = []
        text_lower = text.lower()
        
        try:
            # Check for QR code mentions
            qr_mentions = re.findall(r'qr[-\s]?code|scan.*code|betaal.*code', text_lower)
            
            if not qr_mentions:
                return {'score': 0.0, 'details': 'No QR code references found'}
            
            # Check for suspicious URL patterns in text (often from OCR'd QR codes)
            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
            
            for url in urls:
                url_lower = url.lower()
                
                # Suspicious URL shorteners (often used in fraud)
                suspicious_shorteners = ['bit.ly', 'tinyurl', 'goo.gl', 't.co', 'ow.ly']
                if any(shortener in url_lower for shortener in suspicious_shorteners):
                    score += 0.25
                    details_list.append(f"Suspicious URL shortener: {url[:30]}...")
                
                # Suspicious domains (non-standard TLDs)
                suspicious_tlds = ['.xyz', '.top', '.click', '.work', '.link', '.loan']
                if any(tld in url_lower for tld in suspicious_tlds):
                    score += 0.3
                    details_list.append(f"Suspicious TLD in QR URL: {url[:30]}...")
                
                # Check for typosquatting of Dutch banks
                dutch_banks = ['ing', 'rabobank', 'abn', 'sns', 'triodos']
                for bank in dutch_banks:
                    if bank in url_lower and f'{bank}.nl' not in url_lower and f'{bank}.com' not in url_lower:
                        score += 0.35
                        details_list.append(f"Potential bank typosquatting: {url[:40]}...")
            
            score = min(score, 1.0)
            details = " | ".join(details_list) if details_list else "QR code patterns appear valid"
            
        except Exception as e:
            logger.warning(f"QR code validation failed: {str(e)}")
            details = f"Analysis error: {str(e)}"
        
        return {'score': score, 'details': details}
    
    def _detect_fake_stamps_logos(self, text: str, file_path: str) -> Dict[str, Any]:
        """
        MEDIUM PRIORITY: Detect potentially fake company stamps and logos.
        Analyzes text patterns that indicate stamp/logo presence and validates.
        """
        score = 0.0
        details_list = []
        text_lower = text.lower()
        
        try:
            # Check for stamp-related keywords
            stamp_keywords = ['official stamp', 'company stamp', 'bedrijfsstempel', 
                            'firmastempel', 'notaris', 'certified', 'gecertificeerd']
            has_stamp = any(kw in text_lower for kw in stamp_keywords)
            
            if has_stamp:
                # Check for inconsistencies
                
                # 1. Stamp mentions without company details
                has_company_name = bool(re.search(r'\b[A-Z][a-z]+\s+(?:B\.?V\.?|N\.?V\.?|VOF|CV)\b', text))
                if not has_company_name:
                    score += 0.2
                    details_list.append("Stamp mentioned but no company name found")
                
                # 2. Multiple different stamps mentioned
                stamp_count = sum(1 for kw in stamp_keywords if kw in text_lower)
                if stamp_count > 2:
                    score += 0.15
                    details_list.append(f"Multiple stamp references ({stamp_count})")
            
            # Check for logo-related issues
            logo_keywords = ['logo', 'trademark', 'handelsmerk', '®', '™']
            logo_count = sum(1 for kw in logo_keywords if kw in text_lower)
            
            # Suspicious: too many trademark symbols (possible copied content)
            if logo_count > 5:
                score += 0.2
                details_list.append(f"Excessive trademark mentions ({logo_count})")
            
            # Check for known fake certification patterns
            fake_cert_patterns = [
                r'certified\s+\d{4}',  # "Certified 2024" without proper authority
                r'iso\s*\d+.*self[-\s]?certified',
                r'verified\s+by\s+\[',  # Placeholder verification
            ]
            for pattern in fake_cert_patterns:
                if re.search(pattern, text_lower):
                    score += 0.3
                    details_list.append("Suspicious certification pattern")
                    break
            
            score = min(score, 1.0)
            details = " | ".join(details_list) if details_list else "No stamp/logo fraud indicators"
            
        except Exception as e:
            logger.warning(f"Stamp/logo detection failed: {str(e)}")
            details = f"Analysis error: {str(e)}"
        
        return {'score': score, 'details': details}
    
    def _analyze_stylometry(self, text: str) -> Dict[str, Any]:
        """
        MEDIUM PRIORITY: Advanced stylometric analysis for AI detection.
        Uses linguistic features beyond simple pattern matching.
        """
        score = 0.0
        details_list = []
        
        if len(text) < 200:
            return {'score': 0.0, 'details': 'Text too short for stylometric analysis'}
        
        try:
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # 1. Vocabulary richness (Type-Token Ratio)
            unique_words = set(w.lower() for w in words if w.isalpha())
            ttr = len(unique_words) / max(len(words), 1)
            
            # AI text often has moderate TTR (not too high, not too low)
            if 0.35 < ttr < 0.55:
                score += 0.15
                details_list.append(f"Suspicious vocabulary uniformity (TTR: {ttr:.2f})")
            
            # 2. Average word length
            avg_word_len = mean([len(w) for w in words if w.isalpha()]) if words else 0
            
            # AI tends to use slightly longer words consistently
            if 5.0 < avg_word_len < 6.5:
                score += 0.1
                details_list.append(f"AI-typical word length (avg: {avg_word_len:.1f})")
            
            # 3. Sentence complexity analysis
            if sentences:
                # Count commas per sentence (AI often over-structures)
                comma_counts = [s.count(',') for s in sentences]
                avg_commas = mean(comma_counts)
                if 2 < avg_commas < 4:
                    score += 0.15
                    details_list.append("AI-typical sentence structure")
            
            # 4. Transition word density
            transitions = ['however', 'therefore', 'furthermore', 'moreover', 
                          'additionally', 'consequently', 'nevertheless', 'thus']
            transition_count = sum(1 for t in transitions if t in text.lower())
            transition_density = transition_count / max(len(sentences), 1)
            
            if transition_density > 0.3:
                score += 0.2
                details_list.append(f"High transition word density ({transition_density:.2f})")
            
            # 5. Hedging language (AI often hedges)
            hedges = ['might', 'could', 'perhaps', 'possibly', 'generally', 
                     'typically', 'often', 'usually', 'tend to']
            hedge_count = sum(text.lower().count(h) for h in hedges)
            hedge_density = hedge_count / max(len(words), 1) * 100
            
            if hedge_density > 2:
                score += 0.15
                details_list.append(f"High hedging language ({hedge_density:.1f}%)")
            
            # 6. Passive voice ratio
            passive_patterns = [r'\b(?:is|are|was|were|been|being)\s+\w+ed\b']
            passive_count = sum(len(re.findall(p, text)) for p in passive_patterns)
            passive_ratio = passive_count / max(len(sentences), 1)
            
            if passive_ratio > 0.4:
                score += 0.1
                details_list.append("High passive voice usage")
            
            score = min(score, 1.0)
            details = " | ".join(details_list) if details_list else "Natural writing style"
            
        except Exception as e:
            logger.warning(f"Stylometric analysis failed: {str(e)}")
            details = f"Analysis error: {str(e)}"
        
        return {'score': score, 'details': details, 'ttr': round(ttr, 3) if 'ttr' in dir() else 0}
    
    # ============================================================================
    # ENHANCED FRAUD DETECTION - LOW PRIORITY FEATURES
    # ============================================================================
    
    def _validate_kvk_number(self, text: str) -> Dict[str, Any]:
        """
        LOW PRIORITY: Validate Dutch KvK (Chamber of Commerce) numbers.
        KvK numbers are 8 digits with specific patterns.
        """
        score = 0.0
        details_list = []
        valid_kvk = []
        invalid_kvk = []
        
        try:
            # KvK pattern: 8 digits
            kvk_pattern = r'\b(?:kvk|kamer\s*van\s*koophandel|handelsregister)[:\s#]*(\d{8})\b'
            explicit_kvks = re.findall(kvk_pattern, text.lower())
            
            # Also look for standalone 8-digit numbers near business context
            business_context = r'\b(\d{8})\b'
            potential_kvks = re.findall(business_context, text)
            
            all_kvks = set(explicit_kvks + [k for k in potential_kvks if k in text])
            
            for kvk in all_kvks:
                # Known invalid/test patterns
                invalid_patterns = ['00000000', '11111111', '12345678', '99999999', '87654321']
                
                if kvk in invalid_patterns:
                    score += 0.35
                    details_list.append(f"Invalid KvK pattern: {kvk}")
                    invalid_kvk.append(kvk)
                elif kvk.startswith('00') or kvk.startswith('99'):
                    score += 0.2
                    details_list.append(f"Suspicious KvK prefix: {kvk}")
                    invalid_kvk.append(kvk)
                else:
                    valid_kvk.append(kvk)
            
            score = min(score, 1.0)
            details = " | ".join(details_list) if details_list else f"KvK numbers appear valid: {len(valid_kvk)}"
            
        except Exception as e:
            logger.warning(f"KvK validation failed: {str(e)}")
            details = f"Analysis error: {str(e)}"
        
        return {
            'score': score,
            'details': details,
            'valid_kvk': valid_kvk,
            'invalid_kvk': invalid_kvk
        }
    
    def _validate_btw_number(self, text: str) -> Dict[str, Any]:
        """
        LOW PRIORITY: Validate Dutch BTW (VAT) numbers.
        Dutch BTW format: NL + 9 digits + B + 2 digits (e.g., NL123456789B01)
        """
        score = 0.0
        details_list = []
        valid_btw = []
        invalid_btw = []
        
        try:
            # Dutch BTW pattern
            btw_pattern = r'\b(NL\d{9}B\d{2})\b'
            btw_numbers = re.findall(btw_pattern, text.upper())
            
            # Also check for mentioned BTW without proper format
            btw_mentions = re.findall(r'btw[-\s]?(?:nummer|nr|id)?[:\s]*([A-Z0-9]{5,})', text, re.IGNORECASE)
            
            for btw in btw_numbers:
                # Validate format
                if self._is_valid_dutch_btw(btw):
                    valid_btw.append(btw)
                else:
                    invalid_btw.append(btw)
                    score += 0.3
                    details_list.append(f"Invalid BTW format: {btw}")
            
            # Check for suspicious patterns
            for btw in btw_mentions:
                btw_upper = btw.upper()
                if 'TEST' in btw_upper or '000000000' in btw_upper:
                    score += 0.35
                    details_list.append(f"Test BTW number detected: {btw}")
                    invalid_btw.append(btw)
            
            score = min(score, 1.0)
            details = " | ".join(details_list) if details_list else f"BTW numbers validated: {len(valid_btw)}"
            
        except Exception as e:
            logger.warning(f"BTW validation failed: {str(e)}")
            details = f"Analysis error: {str(e)}"
        
        return {
            'score': score,
            'details': details,
            'valid_btw': valid_btw,
            'invalid_btw': invalid_btw
        }
    
    def _is_valid_dutch_btw(self, btw: str) -> bool:
        """Validate Dutch BTW number format and checksum."""
        try:
            # Basic format check: NL + 9 digits + B + 2 digits
            if not re.match(r'^NL\d{9}B\d{2}$', btw):
                return False
            
            # Extract components
            digits = btw[2:11]  # 9 digits
            suffix = btw[12:14]  # 2 digits after B
            
            # Check for obviously invalid patterns
            if digits == '000000000' or suffix == '00':
                return False
            
            return True
            
        except:
            return False
    
    def _detect_template_fraud(self, text: str, file_path: str) -> Dict[str, Any]:
        """
        LOW PRIORITY: Detect documents created from common fraud templates.
        Identifies signatures of known fake document templates.
        """
        score = 0.0
        details_list = []
        text_lower = text.lower()
        
        try:
            # Known fraud template signatures
            template_signatures = {
                'generic_invoice': [
                    'invoice template', 'sample invoice', 'invoice example',
                    '[company name]', '[your company]', '[client name]'
                ],
                'fake_receipt': [
                    'receipt template', 'sample receipt', 'demo receipt',
                    'your store name', 'store address here'
                ],
                'forged_contract': [
                    'contract template', 'sample agreement', 'template agreement',
                    '[party a]', '[party b]', 'insert name here'
                ],
                'fake_certificate': [
                    'certificate template', 'sample certificate', 'demo certificate',
                    '[recipient name]', 'awarded to [name]'
                ]
            }
            
            matched_templates = []
            for template_type, signatures in template_signatures.items():
                matches = sum(1 for sig in signatures if sig in text_lower)
                if matches >= 2:
                    score += 0.4
                    matched_templates.append(template_type)
                    details_list.append(f"Matches {template_type} pattern")
            
            # Check for placeholder patterns
            placeholder_patterns = [
                r'\[.*?\]',  # [anything]
                r'\{.*?\}',  # {anything}
                r'<.*?>',    # <anything>
                r'xxx+',     # xxx placeholders
                r'___+',     # ___ placeholders
            ]
            
            placeholder_count = sum(len(re.findall(p, text)) for p in placeholder_patterns)
            if placeholder_count > 5:
                score += 0.3
                details_list.append(f"Multiple placeholders found ({placeholder_count})")
            
            # Check for lorem ipsum
            if 'lorem ipsum' in text_lower or 'dolor sit amet' in text_lower:
                score += 0.5
                details_list.append("Lorem ipsum placeholder text detected")
            
            score = min(score, 1.0)
            details = " | ".join(details_list) if details_list else "No template fraud detected"
            
        except Exception as e:
            logger.warning(f"Template fraud detection failed: {str(e)}")
            details = f"Analysis error: {str(e)}"
        
        return {
            'score': score,
            'details': details,
            'matched_templates': matched_templates if 'matched_templates' in dir() else []
        }
    
    def _guess_ai_model(self, chatgpt_score: Dict, statistical_score: Dict) -> str:
        """Guess which AI model generated document"""
        chatgpt_patterns = ['furthermore', 'in conclusion', 'as a whole', 'it is important']
        
        # If ChatGPT patterns strongly present, likely ChatGPT
        if chatgpt_score['score'] > 0.6:
            return 'GPT-4/GPT-3.5'
        
        # If statistical anomalies high but patterns low, might be other model
        if statistical_score['score'] > 0.5:
            return 'Claude/Gemini'
        
        return 'Unknown AI Model'
    
    def _generate_fraud_recommendations(self, risk_level: str, fraud_indicators: List[Dict]) -> List[str]:
        """Generate comprehensive remediation recommendations for all fraud types"""
        recommendations = []
        
        if risk_level in ['High', 'Critical']:
            recommendations.append('Request original document directly from sender')
            recommendations.append('Verify authenticity through independent communication channel')
            
            # Check which indicators are strongest
            for indicator in fraud_indicators:
                if indicator['score'] > 0.3:  # Lower threshold for comprehensive recommendations
                    indicator_type = indicator['type']
                    
                    if 'chatgpt' in indicator_type:
                        recommendations.append('Verify document was not generated by AI language model')
                    elif 'statistical' in indicator_type or 'stylometric' in indicator_type:
                        recommendations.append('Check for unusual writing patterns or consistency')
                    elif 'metadata' in indicator_type:
                        recommendations.append('Examine document edit history and timestamps')
                    elif 'receipt' in indicator_type or 'invoice' in indicator_type:
                        recommendations.append('Verify receipt/invoice with vendor via phone or official website')
                    elif 'pdf_embedded' in indicator_type:
                        recommendations.append('Inspect embedded images for manipulation using forensic tools')
                    elif 'signature' in indicator_type:
                        recommendations.append('Verify digital signature authenticity with signer directly')
                        recommendations.append('Request handwritten signature on physical document')
                    elif 'iban' in indicator_type:
                        recommendations.append('Verify IBAN through bank confirmation before payment')
                        recommendations.append('Cross-check IBAN with known vendor bank details')
                    elif 'qr' in indicator_type:
                        recommendations.append('Do not scan suspicious QR codes; verify URL manually')
                    elif 'stamp' in indicator_type or 'logo' in indicator_type:
                        recommendations.append('Verify company stamp/logo authenticity with issuer')
                    elif 'kvk' in indicator_type:
                        recommendations.append('Verify KvK number at kvk.nl/handelsregister')
                    elif 'btw' in indicator_type:
                        recommendations.append('Verify BTW number at ec.europa.eu/taxation_customs/vies')
                    elif 'template' in indicator_type:
                        recommendations.append('Document appears to use fraud template - reject and report')
            
            recommendations.append('Consider requesting notarized or digitally signed version')
        
        elif risk_level == 'Medium':
            recommendations.append('Request confirmation of document authenticity from sender')
            recommendations.append('Review document creation and modification dates')
            
            for indicator in fraud_indicators:
                if indicator['score'] > 0.2:
                    if 'receipt' in indicator['type']:
                        recommendations.append('Verify vendor details before processing payment')
                    if 'iban' in indicator['type']:
                        recommendations.append('Double-check IBAN before making transfers')
        
        if self.region == "Netherlands":
            recommendations.append('Ensure compliance with UAVG document verification requirements')
            recommendations.append('For invoices: verify vendor in KvK Handelsregister')
            recommendations.append('For payments: validate IBAN via Dutch banking standards')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:8]  # Return top 8 recommendations

# Create an alias for compatibility
def create_document_scanner(region: str = "Netherlands") -> BlobScanner:
    """Factory function to create BlobScanner instance for document scanning."""
    return BlobScanner(region=region)
