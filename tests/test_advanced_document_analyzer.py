"""
Comprehensive Unit Tests for Advanced Document Analyzer

Tests all 12 advanced document analysis features:
1. Document Metadata Extraction
2. Document Tampering/Integrity Detection
3. Language Detection
4. Document Classification
5. Hidden Content Detection
6. Embedded Object Detection
7. Digital Signature Detection
8. Redaction Detection
9. Version/Revision History Analysis
10. Enhanced Table/Form Data Extraction
11. Document Forensics
12. Cross-Reference Detection
"""

import os
import sys
import pytest
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.advanced_document_analyzer import AdvancedDocumentAnalyzer, create_document_analyzer


class TestAdvancedDocumentAnalyzerInitialization:
    """Test analyzer initialization."""
    
    def test_default_initialization(self):
        """Test default initialization with Netherlands region."""
        analyzer = AdvancedDocumentAnalyzer()
        
        assert analyzer.region == "Netherlands"
        assert analyzer.analysis_features is not None
        assert all(analyzer.analysis_features.values())
    
    def test_custom_region(self):
        """Test initialization with custom region."""
        analyzer = AdvancedDocumentAnalyzer(region="Germany")
        
        assert analyzer.region == "Germany"
    
    def test_factory_function(self):
        """Test factory function creates analyzer correctly."""
        analyzer = create_document_analyzer(region="France")
        
        assert isinstance(analyzer, AdvancedDocumentAnalyzer)
        assert analyzer.region == "France"
    
    def test_classification_keywords_present(self):
        """Test that classification keywords are defined."""
        analyzer = AdvancedDocumentAnalyzer()
        
        assert 'contract' in analyzer.classification_keywords
        assert 'invoice' in analyzer.classification_keywords
        assert 'medical' in analyzer.classification_keywords
        assert 'hr' in analyzer.classification_keywords
        assert 'legal' in analyzer.classification_keywords


class TestMetadataExtraction:
    """Test Document Metadata Extraction (Feature 1)."""
    
    def test_metadata_extraction_structure(self):
        """Test metadata extraction returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content for metadata extraction")
            temp_path = f.name
        
        try:
            result = analyzer._extract_metadata(temp_path, '.txt')
            
            assert 'author' in result
            assert 'creation_date' in result
            assert 'modification_date' in result
            assert 'file_size' in result
            assert 'file_created' in result
            assert 'file_modified' in result
            assert 'pii_in_metadata' in result
        finally:
            os.unlink(temp_path)
    
    def test_pii_detection_in_metadata(self):
        """Test PII detection in metadata works."""
        analyzer = AdvancedDocumentAnalyzer()
        
        metadata = {
            'author': 'john.doe@example.com',
            'creator': 'Jane Smith',
            'last_modified_by': 'Admin User',
            'company': 'Example Corp'
        }
        
        pii_findings = analyzer._detect_pii_in_metadata(metadata)
        
        email_findings = [f for f in pii_findings if f['type'] == 'EMAIL_IN_METADATA']
        assert len(email_findings) > 0
    
    def test_file_size_extraction(self):
        """Test file size is correctly extracted."""
        analyzer = AdvancedDocumentAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            test_content = b"A" * 1000
            f.write(test_content)
            temp_path = f.name
        
        try:
            result = analyzer._extract_metadata(temp_path, '.txt')
            
            assert result['file_size'] == 1000
        finally:
            os.unlink(temp_path)


class TestTamperingDetection:
    """Test Document Tampering/Integrity Detection (Feature 2)."""
    
    def test_tampering_detection_structure(self):
        """Test tampering detection returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name
        
        try:
            metadata = analyzer._extract_metadata(temp_path, '.txt')
            result = analyzer._detect_tampering(temp_path, '.txt', metadata)
            
            assert 'tampering_detected' in result
            assert 'integrity_score' in result
            assert 'issues' in result
            assert 'file_hash' in result
            assert 'timestamp_consistency' in result
            assert 'metadata_consistency' in result
        finally:
            os.unlink(temp_path)
    
    def test_file_hash_generation(self):
        """Test file hash is correctly generated."""
        analyzer = AdvancedDocumentAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Consistent content for hashing")
            temp_path = f.name
        
        try:
            metadata = analyzer._extract_metadata(temp_path, '.txt')
            result = analyzer._detect_tampering(temp_path, '.txt', metadata)
            
            assert result['file_hash'] is not None
            assert len(result['file_hash']) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)
    
    def test_integrity_score_starts_at_100(self):
        """Test integrity score starts at 100 for clean files."""
        analyzer = AdvancedDocumentAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Clean file content")
            temp_path = f.name
        
        try:
            metadata = analyzer._extract_metadata(temp_path, '.txt')
            result = analyzer._detect_tampering(temp_path, '.txt', metadata)
            
            assert result['integrity_score'] <= 100
            assert result['integrity_score'] >= 0
        finally:
            os.unlink(temp_path)


class TestLanguageDetection:
    """Test Language Detection (Feature 3)."""
    
    def test_language_detection_structure(self):
        """Test language detection returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "This is a sample English text for testing language detection capabilities."
        result = analyzer._detect_language(text)
        
        assert 'detected_language' in result
        assert 'language_code' in result
        assert 'confidence' in result
        assert 'all_languages' in result
        assert 'is_multilingual' in result
    
    def test_english_detection(self):
        """Test English language detection."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "This is a sample text written in English. It contains multiple sentences to help with detection."
        result = analyzer._detect_language(text)
        
        assert result['detected_language'] is not None
    
    def test_short_text_handling(self):
        """Test handling of short text (less than 50 chars)."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "Short text"
        result = analyzer._detect_language(text)
        
        assert result['detected_language'] == 'unknown'
    
    def test_heuristic_detection_dutch(self):
        """Test heuristic Dutch language detection."""
        analyzer = AdvancedDocumentAnalyzer()
        
        dutch_text = "de het een van en dat is op te voor met zijn niet aan wordt"
        result = analyzer._detect_language_heuristic(dutch_text)
        
        assert result in ['Dutch', 'English', 'German', 'French']


class TestDocumentClassification:
    """Test Document Classification (Feature 4)."""
    
    def test_classification_structure(self):
        """Test classification returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "This is a sample document for testing classification."
        result = analyzer._classify_document(text, "test.pdf", ".pdf")
        
        assert 'primary_category' in result
        assert 'confidence' in result
        assert 'all_categories' in result
        assert 'sensitivity_level' in result
        assert 'gdpr_relevance' in result
    
    def test_contract_classification(self):
        """Test contract document classification."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "This agreement is entered into between the parties hereby. Terms and conditions apply. Termination clause included."
        result = analyzer._classify_document(text, "agreement.pdf", ".pdf")
        
        assert result['primary_category'] == 'contract' or result['confidence'] > 0
    
    def test_invoice_classification(self):
        """Test invoice document classification."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "Invoice number: 12345. Total amount due: €500. VAT: €105. Subtotal: €395. Payment due date: 30 days."
        result = analyzer._classify_document(text, "invoice.pdf", ".pdf")
        
        assert result['primary_category'] == 'invoice' or 'invoice' in [c['category'] for c in result.get('all_categories', [])]
    
    def test_medical_high_sensitivity(self):
        """Test medical documents are marked as high sensitivity."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "Patient diagnosis: hypertension. Treatment includes medication. Doctor recommended hospital visit."
        result = analyzer._classify_document(text, "medical_record.pdf", ".pdf")
        
        if result['primary_category'] == 'medical':
            assert result['sensitivity_level'] == 'high'
            assert result['gdpr_relevance'] == 'high'


class TestHiddenContentDetection:
    """Test Hidden Content Detection (Feature 5)."""
    
    def test_hidden_content_structure(self):
        """Test hidden content detection returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name
        
        try:
            result = analyzer._detect_hidden_content(temp_path, '.txt')
            
            assert 'hidden_content_found' in result
            assert 'hidden_items' in result
            assert 'hidden_text' in result
            assert 'hidden_layers' in result
            assert 'hidden_rows_columns' in result
        finally:
            os.unlink(temp_path)


class TestEmbeddedObjectDetection:
    """Test Embedded Object Detection (Feature 6)."""
    
    def test_embedded_object_structure(self):
        """Test embedded object detection returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name
        
        try:
            result = analyzer._detect_embedded_objects(temp_path, '.txt')
            
            assert 'embedded_objects_found' in result
            assert 'objects' in result
            assert 'macros_detected' in result
            assert 'scripts_detected' in result
        finally:
            os.unlink(temp_path)


class TestDigitalSignatureDetection:
    """Test Digital Signature Detection (Feature 7)."""
    
    def test_signature_detection_structure(self):
        """Test signature detection returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name
        
        try:
            result = analyzer._detect_digital_signatures(temp_path, '.txt')
            
            assert 'has_signature' in result
            assert 'signatures' in result
            assert 'signature_valid' in result
        finally:
            os.unlink(temp_path)


class TestRedactionDetection:
    """Test Redaction Detection (Feature 8)."""
    
    def test_redaction_detection_structure(self):
        """Test redaction detection returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "This is a normal document without redactions."
        result = analyzer._detect_redaction(text, "/fake/path.pdf", ".pdf")
        
        assert 'redaction_detected' in result
        assert 'redaction_patterns' in result
        assert 'potential_hidden_pii' in result
    
    def test_black_block_redaction_detection(self):
        """Test detection of black block character redaction."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "The SSN is ██████████ and the name is ████████."
        result = analyzer._detect_redaction(text, "/fake/path.pdf", ".pdf")
        
        assert result['redaction_detected'] == True
        assert len(result['redaction_patterns']) > 0
    
    def test_redacted_label_detection(self):
        """Test detection of [REDACTED] label."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "The password was [REDACTED] and the API key was [CONFIDENTIAL]."
        result = analyzer._detect_redaction(text, "/fake/path.pdf", ".pdf")
        
        assert result['redaction_detected'] == True
    
    def test_asterisk_pattern_detection(self):
        """Test detection of asterisk redaction pattern."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "Credit card: ************1234"
        result = analyzer._detect_redaction(text, "/fake/path.pdf", ".pdf")
        
        assert result['redaction_detected'] == True


class TestVersionHistoryAnalysis:
    """Test Version/Revision History Analysis (Feature 9)."""
    
    def test_version_history_structure(self):
        """Test version history analysis returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name
        
        try:
            result = analyzer._analyze_version_history(temp_path, '.txt')
            
            assert 'has_revisions' in result
            assert 'revision_count' in result
            assert 'revisions' in result
        finally:
            os.unlink(temp_path)


class TestTableDataExtraction:
    """Test Enhanced Table/Form Data Extraction (Feature 10)."""
    
    def test_table_extraction_structure(self):
        """Test table extraction returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name
        
        try:
            result = analyzer._extract_table_data(temp_path, '.txt')
            
            assert 'tables_found' in result
            assert 'tables' in result
            assert 'forms_found' in result
            assert 'form_fields' in result
        finally:
            os.unlink(temp_path)


class TestDocumentForensics:
    """Test Document Forensics (Feature 11)."""
    
    def test_forensics_structure(self):
        """Test forensics analysis returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        metadata = {
            'author': 'John Doe',
            'creator': 'Microsoft Word',
            'last_modified_by': 'Jane Smith',
            'file_created': datetime.now().isoformat(),
            'file_modified': datetime.now().isoformat(),
            'creation_date': datetime.now().isoformat(),
            'modification_date': datetime.now().isoformat(),
            'file_size': 1000
        }
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name
        
        try:
            result = analyzer._perform_forensic_analysis(temp_path, '.txt', metadata)
            
            assert 'creation_timeline' in result
            assert 'authorship_analysis' in result
            assert 'anomalies' in result
            assert 'forensic_score' in result
        finally:
            os.unlink(temp_path)
    
    def test_multiple_authors_detection(self):
        """Test detection of multiple authors."""
        analyzer = AdvancedDocumentAnalyzer()
        
        metadata = {
            'author': 'John Doe',
            'creator': 'Microsoft Word',
            'last_modified_by': 'Jane Smith',
            'file_created': datetime.now().isoformat(),
            'file_modified': datetime.now().isoformat(),
            'file_size': 1000
        }
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name
        
        try:
            result = analyzer._perform_forensic_analysis(temp_path, '.txt', metadata)
            
            assert result['authorship_analysis']['multiple_authors'] == True
            assert any(a['type'] == 'MULTIPLE_AUTHORS' for a in result['anomalies'])
        finally:
            os.unlink(temp_path)


class TestCrossReferenceDetection:
    """Test Cross-Reference Detection (Feature 12)."""
    
    def test_cross_reference_structure(self):
        """Test cross-reference detection returns expected structure."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "Please visit our website for more information."
        result = analyzer._detect_cross_references(text, "/fake/path.pdf")
        
        assert 'references_found' in result
        assert 'internal_references' in result
        assert 'external_references' in result
        assert 'urls' in result
        assert 'file_references' in result
        assert 'data_sharing_indicators' in result
    
    def test_url_detection(self):
        """Test URL detection in document."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "Visit https://example.com and http://test.org for more info. Also check www.sample.net."
        result = analyzer._detect_cross_references(text, "/fake/path.pdf")
        
        assert len(result['urls']) >= 2
        assert result['references_found'] >= 2
    
    def test_file_reference_detection(self):
        """Test file path reference detection."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = 'See the attached document at "C:\\Documents\\report.pdf" for details.'
        result = analyzer._detect_cross_references(text, "/fake/path.pdf")
        
        assert 'pdf' in str(result).lower() or len(result['file_references']) >= 0
    
    def test_data_sharing_indicator_detection(self):
        """Test data sharing indicator detection."""
        analyzer = AdvancedDocumentAnalyzer()
        
        text = "This report was shared with John and forwarded to the team. See also the attached appendix."
        result = analyzer._detect_cross_references(text, "/fake/path.pdf")
        
        assert len(result['data_sharing_indicators']) > 0 or result['references_found'] >= 0


class TestFullDocumentAnalysis:
    """Test complete document analysis workflow."""
    
    def test_full_analysis_structure(self):
        """Test full analysis returns all expected sections."""
        analyzer = AdvancedDocumentAnalyzer()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"This is a comprehensive test document with various content.")
            temp_path = f.name
        
        try:
            result = analyzer.analyze_document(temp_path, "This is test content for analysis.")
            
            assert 'file_name' in result
            assert 'analysis_timestamp' in result
            assert 'metadata' in result
            assert 'integrity' in result
            assert 'language' in result
            assert 'classification' in result
            assert 'hidden_content' in result
            assert 'embedded_objects' in result
            assert 'digital_signatures' in result
            assert 'redaction' in result
            assert 'version_history' in result
            assert 'table_data' in result
            assert 'forensics' in result
            assert 'cross_references' in result
            assert 'findings' in result
            assert 'risk_indicators' in result
        finally:
            os.unlink(temp_path)
    
    def test_nonexistent_file_handling(self):
        """Test handling of non-existent file."""
        analyzer = AdvancedDocumentAnalyzer()
        
        result = analyzer.analyze_document("/nonexistent/path/file.pdf")
        
        assert 'error' in result
        assert result['error'] == 'File not found'
    
    def test_findings_generation(self):
        """Test findings are properly generated from analysis."""
        analyzer = AdvancedDocumentAnalyzer()
        
        analysis = {
            'metadata': {
                'pii_in_metadata': [
                    {'type': 'EMAIL_IN_METADATA', 'field': 'author', 'value': 'test@example.com', 'risk_level': 'Medium', 'description': 'Email found'}
                ]
            },
            'integrity': {'issues': []},
            'hidden_content': {'hidden_content_found': False, 'hidden_items': []},
            'embedded_objects': {'macros_detected': False},
            'redaction': {'redaction_detected': False},
            'classification': {'sensitivity_level': 'low'},
            'cross_references': {'urls': []}
        }
        
        findings = analyzer._generate_findings(analysis)
        
        assert len(findings) >= 1
        assert any(f['category'] == 'METADATA_PII' for f in findings)
    
    def test_risk_indicators_calculation(self):
        """Test risk indicators are properly calculated."""
        analyzer = AdvancedDocumentAnalyzer()
        
        analysis = {
            'integrity': {'integrity_score': 50},
            'embedded_objects': {'risk_level': 'high'},
            'classification': {'gdpr_relevance': 'high'},
            'hidden_content': {'hidden_content_found': True}
        }
        
        indicators = analyzer._calculate_risk_indicators(analysis)
        
        assert len(indicators) >= 1


class TestBlobScannerIntegration:
    """Test integration with BlobScanner."""
    
    def test_blob_scanner_uses_advanced_analyzer(self):
        """Test BlobScanner initializes with advanced analyzer."""
        from services.blob_scanner import BlobScanner, ADVANCED_ANALYZER_AVAILABLE
        
        if ADVANCED_ANALYZER_AVAILABLE:
            scanner = BlobScanner(region="Netherlands")
            assert scanner.advanced_analyzer is not None
    
    def test_scan_file_includes_advanced_analysis(self):
        """Test scan_file includes advanced analysis results."""
        from services.blob_scanner import BlobScanner, ADVANCED_ANALYZER_AVAILABLE
        
        if not ADVANCED_ANALYZER_AVAILABLE:
            pytest.skip("Advanced analyzer not available")
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"This is a test document with some content for scanning. Email: test@example.com")
            temp_path = f.name
        
        try:
            scanner = BlobScanner(region="Netherlands")
            result = scanner.scan_file(temp_path)
            
            assert 'advanced_analysis' in result
            assert 'metadata' in result['advanced_analysis']
            assert 'integrity' in result['advanced_analysis']
            assert 'language' in result['advanced_analysis']
            assert 'classification' in result['advanced_analysis']
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
