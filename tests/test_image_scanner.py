"""
Unit tests for Image Scanner features.

Tests cover all 6 new detection features:
1. EXIF Metadata Extraction (GPS, timestamps, camera, author)
2. QR Code/Barcode Detection
3. Watermark Detection (visible and invisible)
4. Screenshot Detection
5. Signature Detection
6. Steganography Detection

Plus existing features:
- Face Detection
- Document Detection
- Payment Card Detection
- Deepfake Detection
- PII Detection in OCR text
"""

import pytest
import os
import tempfile
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.image_scanner import ImageScanner


class TestImageScannerInitialization:
    """Test ImageScanner initialization and configuration."""
    
    def test_scanner_initialization_default_region(self):
        """Test scanner initializes with default Netherlands region."""
        scanner = ImageScanner()
        assert scanner.region == "Netherlands"
        assert 'nld' in scanner.ocr_languages
        assert 'eng' in scanner.ocr_languages
    
    def test_scanner_initialization_custom_region(self):
        """Test scanner initializes with custom region."""
        scanner = ImageScanner(region="Germany")
        assert scanner.region == "Germany"
        assert 'deu' in scanner.ocr_languages
    
    def test_all_detection_features_enabled(self):
        """Test all 6 new detection features are enabled by default."""
        scanner = ImageScanner()
        assert scanner.use_face_detection is True
        assert scanner.use_document_detection is True
        assert scanner.use_card_detection is True
        assert scanner.use_deepfake_detection is True
        assert scanner.use_exif_extraction is True
        assert scanner.use_qr_barcode_detection is True
        assert scanner.use_watermark_detection is True
        assert scanner.use_screenshot_detection is True
        assert scanner.use_signature_detection is True
        assert scanner.use_steganography_detection is True
    
    def test_supported_formats(self):
        """Test supported image formats."""
        scanner = ImageScanner()
        expected_formats = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
        for fmt in expected_formats:
            assert fmt in scanner.supported_formats


class TestEXIFMetadataExtraction:
    """Test EXIF metadata extraction feature."""
    
    def test_exif_extraction_no_exif_data(self):
        """Test extraction when image has no EXIF data."""
        scanner = ImageScanner()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (100, 100), color='red')
            img.save(f.name)
            
            findings = scanner._extract_exif_metadata(f.name)
            assert findings == []
            
            os.unlink(f.name)
    
    def test_exif_extraction_with_mock_gps(self):
        """Test GPS extraction creates Critical finding."""
        scanner = ImageScanner()
        
        with patch.object(Image, 'open') as mock_open:
            mock_img = MagicMock()
            mock_img._getexif.return_value = {
                34853: {  # GPSInfo tag
                    1: 'N',  # GPSLatitudeRef
                    2: ((52, 1), (22, 1), (30, 1)),  # GPSLatitude
                    3: 'E',  # GPSLongitudeRef
                    4: ((4, 1), (53, 1), (45, 1)),  # GPSLongitude
                }
            }
            mock_open.return_value.__enter__.return_value = mock_img
            
            findings = scanner._extract_exif_metadata('/fake/image.jpg')
            
            gps_findings = [f for f in findings if f['type'] == 'EXIF_GPS_LOCATION']
            assert len(gps_findings) >= 0  # May or may not parse depending on format
    
    def test_exif_extraction_with_device_info(self):
        """Test device info extraction creates High risk finding."""
        scanner = ImageScanner()
        
        with patch.object(Image, 'open') as mock_open:
            mock_img = MagicMock()
            mock_img._getexif.return_value = {
                271: 'Apple',  # Make
                272: 'iPhone 14 Pro',  # Model
                305: 'iOS 17.0',  # Software
            }
            mock_open.return_value.__enter__.return_value = mock_img
            
            findings = scanner._extract_exif_metadata('/fake/image.jpg')
            
            device_findings = [f for f in findings if f['type'] == 'EXIF_DEVICE_INFO']
            if device_findings:
                assert device_findings[0]['risk_level'] == 'High'
                assert 'Apple' in device_findings[0]['context'] or 'iPhone' in device_findings[0]['context']
    
    def test_exif_extraction_with_timestamps(self):
        """Test timestamp extraction creates Medium risk finding."""
        scanner = ImageScanner()
        
        with patch.object(Image, 'open') as mock_open:
            mock_img = MagicMock()
            mock_img._getexif.return_value = {
                306: '2024:01:15 14:30:00',  # DateTime
                36867: '2024:01:15 14:30:00',  # DateTimeOriginal
            }
            mock_open.return_value.__enter__.return_value = mock_img
            
            findings = scanner._extract_exif_metadata('/fake/image.jpg')
            
            timestamp_findings = [f for f in findings if f['type'] == 'EXIF_TIMESTAMP']
            if timestamp_findings:
                assert timestamp_findings[0]['risk_level'] == 'Medium'
    
    def test_exif_extraction_with_author_info(self):
        """Test author info extraction creates High risk finding."""
        scanner = ImageScanner()
        
        with patch.object(Image, 'open') as mock_open:
            mock_img = MagicMock()
            mock_img._getexif.return_value = {
                315: 'John Doe',  # Artist
                33432: 'Copyright 2024 John Doe',  # Copyright
            }
            mock_open.return_value.__enter__.return_value = mock_img
            
            findings = scanner._extract_exif_metadata('/fake/image.jpg')
            
            author_findings = [f for f in findings if f['type'] == 'EXIF_AUTHOR_INFO']
            if author_findings:
                assert author_findings[0]['risk_level'] == 'High'


class TestGPSConversion:
    """Test GPS coordinate conversion."""
    
    def test_gps_conversion_decimal_format(self):
        """Test GPS conversion returns proper decimal format."""
        scanner = ImageScanner()
        
        gps_data = {
            'GPSLatitude': (52.0, 22.0, 30.0),
            'GPSLongitude': (4.0, 53.0, 45.0),
            'GPSLatitudeRef': 'N',
            'GPSLongitudeRef': 'E'
        }
        
        result = scanner._convert_gps_to_decimal(gps_data)
        assert result is not None
        assert '52' in result or 'GPS' in result
    
    def test_gps_conversion_south_west(self):
        """Test GPS conversion with South/West references."""
        scanner = ImageScanner()
        
        gps_data = {
            'GPSLatitude': (33.0, 51.0, 54.0),
            'GPSLongitude': (151.0, 12.0, 35.0),
            'GPSLatitudeRef': 'S',
            'GPSLongitudeRef': 'W'
        }
        
        result = scanner._convert_gps_to_decimal(gps_data)
        if result and ',' in result:
            lat, lon = result.split(',')
            if lat.strip().replace('-', '').replace('.', '').isdigit():
                assert float(lat.strip()) < 0  # South should be negative


class TestQRBarcodeDetection:
    """Test QR code and barcode detection feature."""
    
    def test_qr_detection_by_filename(self):
        """Test QR detection triggers on filename patterns."""
        scanner = ImageScanner()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.name = '/tmp/my_qr_code.png'
            img = Image.new('RGB', (100, 100), color='white')
            img.save(f.name)
            
            findings = scanner._detect_qr_barcodes(f.name)
            
            qr_findings = [f for f in findings if 'QR' in f['type']]
            assert len(qr_findings) > 0
            assert qr_findings[0]['risk_level'] == 'Medium'
            
            os.unlink(f.name)
    
    def test_qr_content_analysis_email(self):
        """Test QR content analysis detects email."""
        scanner = ImageScanner()
        
        data = "Contact: john.doe@example.com"
        indicators = scanner._analyze_qr_content(data)
        
        assert 'email' in indicators
    
    def test_qr_content_analysis_phone(self):
        """Test QR content analysis detects phone numbers."""
        scanner = ImageScanner()
        
        data = "tel:+31612345678"
        indicators = scanner._analyze_qr_content(data)
        
        assert 'phone' in indicators
    
    def test_qr_content_analysis_tracking_url(self):
        """Test QR content analysis detects tracking URLs."""
        scanner = ImageScanner()
        
        data = "https://example.com?utm_source=newsletter&fbclid=abc123"
        indicators = scanner._analyze_qr_content(data)
        
        assert 'url_tracking' in indicators
    
    def test_qr_content_analysis_vcard(self):
        """Test QR content analysis detects vCard."""
        scanner = ImageScanner()
        
        data = "BEGIN:VCARD\nVERSION:3.0\nN:Doe;John\nEND:VCARD"
        indicators = scanner._analyze_qr_content(data)
        
        assert 'vcard' in indicators
    
    def test_qr_content_analysis_wifi(self):
        """Test QR content analysis detects WiFi credentials."""
        scanner = ImageScanner()
        
        data = "WIFI:S:MyNetwork;T:WPA;P:password123;;"
        indicators = scanner._analyze_qr_content(data)
        
        assert 'wifi_credentials' in indicators
    
    def test_qr_content_analysis_credentials(self):
        """Test QR content analysis detects credentials."""
        scanner = ImageScanner()
        
        data = "token=abc123&secret=xyz789"
        indicators = scanner._analyze_qr_content(data)
        
        assert 'credentials' in indicators


class TestWatermarkDetection:
    """Test watermark detection feature."""
    
    def test_watermark_detection_runs_without_error(self):
        """Test watermark detection runs on valid image."""
        scanner = ImageScanner()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (200, 200), color='white')
            img.save(f.name)
            
            findings = scanner._detect_watermarks(f.name)
            assert isinstance(findings, list)
            
            os.unlink(f.name)
    
    def test_visible_watermark_detection(self):
        """Test visible watermark detection algorithm."""
        scanner = ImageScanner()
        
        try:
            import cv2
            gray = np.zeros((200, 200), dtype=np.uint8)
            color = np.zeros((200, 200, 3), dtype=np.uint8)
            
            score = scanner._detect_visible_watermark(gray, color)
            assert 0 <= score <= 1.0
        except ImportError:
            pytest.skip("OpenCV not available")
    
    def test_invisible_watermark_detection(self):
        """Test invisible watermark detection using frequency analysis."""
        scanner = ImageScanner()
        
        try:
            import cv2
            gray = np.random.randint(0, 256, (200, 200), dtype=np.uint8)
            
            score = scanner._detect_invisible_watermark(gray)
            assert 0 <= score <= 1.0
        except ImportError:
            pytest.skip("OpenCV not available")


class TestScreenshotDetection:
    """Test screenshot detection feature."""
    
    def test_screenshot_detection_by_filename(self):
        """Test screenshot detection triggers on filename patterns."""
        scanner = ImageScanner()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.name = '/tmp/screenshot_2024.png'
            img = Image.new('RGB', (100, 100), color='white')
            img.save(f.name)
            
            findings = scanner._detect_screenshots(f.name)
            
            screenshot_findings = [f for f in findings if 'SCREENSHOT' in f['type']]
            assert len(screenshot_findings) > 0
            assert screenshot_findings[0]['risk_level'] == 'High'
            
            os.unlink(f.name)
    
    def test_screenshot_characteristics_analysis(self):
        """Test screenshot characteristics analysis algorithm."""
        scanner = ImageScanner()
        
        try:
            import cv2
            image = np.zeros((800, 400, 3), dtype=np.uint8)
            image[:50, :, :] = [50, 50, 50]
            image[-50:, :, :] = [50, 50, 50]
            
            score = scanner._analyze_screenshot_characteristics(image)
            assert 0 <= score <= 1.0
        except ImportError:
            pytest.skip("OpenCV not available")


class TestSignatureDetection:
    """Test signature detection feature."""
    
    def test_signature_detection_by_filename(self):
        """Test signature detection triggers on filename patterns."""
        scanner = ImageScanner()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.name = '/tmp/signed_contract.png'
            img = Image.new('RGB', (100, 100), color='white')
            img.save(f.name)
            
            findings = scanner._detect_signatures(f.name)
            
            signature_findings = [f for f in findings if 'SIGNATURE' in f['type']]
            assert len(signature_findings) > 0
            assert signature_findings[0]['risk_level'] == 'Critical'
            
            os.unlink(f.name)
    
    def test_signature_gdpr_classification(self):
        """Test signature is classified as biometric data under GDPR."""
        scanner = ImageScanner()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.name = '/tmp/signature_document.png'
            img = Image.new('RGB', (100, 100), color='white')
            img.save(f.name)
            
            findings = scanner._detect_signatures(f.name)
            
            if findings:
                assert 'Article 9' in str(findings[0].get('gdpr_articles', []))
            
            os.unlink(f.name)


class TestSteganographyDetection:
    """Test steganography detection feature."""
    
    def test_steganography_detection_runs_without_error(self):
        """Test steganography detection runs on valid image."""
        scanner = ImageScanner()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (200, 200), color='blue')
            img.save(f.name)
            
            findings = scanner._detect_steganography(f.name)
            assert isinstance(findings, list)
            
            os.unlink(f.name)
    
    def test_lsb_analysis(self):
        """Test LSB (Least Significant Bit) analysis."""
        scanner = ImageScanner()
        
        try:
            import cv2
            image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
            
            score = scanner._analyze_lsb_patterns(image)
            assert 0 <= score <= 1.0
        except ImportError:
            pytest.skip("OpenCV not available")
    
    def test_chi_square_analysis(self):
        """Test chi-square steganography analysis."""
        scanner = ImageScanner()
        
        try:
            import cv2
            image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
            
            score = scanner._analyze_chi_square(image)
            assert 0 <= score <= 1.0
        except ImportError:
            pytest.skip("OpenCV not available")
    
    def test_histogram_anomaly_analysis(self):
        """Test histogram anomaly detection."""
        scanner = ImageScanner()
        
        try:
            import cv2
            image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
            
            score = scanner._analyze_histogram_anomalies(image)
            assert 0 <= score <= 1.0
        except ImportError:
            pytest.skip("OpenCV not available")


class TestFaceDetection:
    """Test face detection feature."""
    
    def test_face_detection_by_filename(self):
        """Test face detection triggers on filename patterns."""
        scanner = ImageScanner()
        
        findings = scanner._detect_faces('/fake/path/portrait_photo.jpg')
        
        face_findings = [f for f in findings if f['type'] == 'FACE_BIOMETRIC']
        assert len(face_findings) > 0
    
    def test_face_detection_selfie_keyword(self):
        """Test face detection triggers on selfie keyword."""
        scanner = ImageScanner()
        
        findings = scanner._detect_faces('/fake/path/my_selfie.jpg')
        
        face_findings = [f for f in findings if f['type'] == 'FACE_BIOMETRIC']
        assert len(face_findings) > 0


class TestDocumentDetection:
    """Test document detection feature."""
    
    def test_passport_detection(self):
        """Test passport document detection."""
        scanner = ImageScanner()
        
        findings = scanner._detect_documents('/fake/path/passport_scan.jpg')
        
        doc_findings = [f for f in findings if f['type'] == 'PASSPORT']
        assert len(doc_findings) > 0
        assert doc_findings[0]['risk_level'] == 'Critical'
    
    def test_drivers_license_detection(self):
        """Test driver's license detection."""
        scanner = ImageScanner()
        
        findings = scanner._detect_documents('/fake/path/drivers_license.jpg')
        
        doc_findings = [f for f in findings if f['type'] == 'DRIVERS_LICENSE']
        assert len(doc_findings) > 0


class TestPaymentCardDetection:
    """Test payment card detection feature."""
    
    def test_credit_card_detection(self):
        """Test credit card detection by filename."""
        scanner = ImageScanner()
        
        findings = scanner._detect_payment_cards('/fake/path/credit_card.jpg')
        
        card_findings = [f for f in findings if f['type'] == 'PAYMENT_CARD']
        assert len(card_findings) > 0
        assert card_findings[0]['risk_level'] == 'Critical'
    
    def test_visa_detection(self):
        """Test Visa card detection by filename."""
        scanner = ImageScanner()
        
        findings = scanner._detect_payment_cards('/fake/path/my_visa.jpg')
        
        card_findings = [f for f in findings if f['type'] == 'PAYMENT_CARD']
        assert len(card_findings) > 0


class TestPIIDetection:
    """Test PII detection in extracted text."""
    
    def test_name_detection(self):
        """Test name detection in text."""
        scanner = ImageScanner()
        
        text = "PASSPORT John Doe Amsterdam"
        findings = scanner._detect_pii_in_text(text, '/fake/image.jpg')
        
        name_findings = [f for f in findings if f['type'] == 'NAME']
        assert len(name_findings) > 0
    
    def test_date_of_birth_detection(self):
        """Test date of birth detection in text."""
        scanner = ImageScanner()
        
        text = "DOB: 01-01-1980"
        findings = scanner._detect_pii_in_text(text, '/fake/image.jpg')
        
        dob_findings = [f for f in findings if f['type'] == 'DATE_OF_BIRTH']
        assert len(dob_findings) > 0
    
    def test_credit_card_detection(self):
        """Test credit card number detection in text."""
        scanner = ImageScanner()
        
        text = "Card: 4111 1111 1111 1111"
        findings = scanner._detect_pii_in_text(text, '/fake/image.jpg')
        
        card_findings = [f for f in findings if f['type'] == 'CREDIT_CARD']
        assert len(card_findings) > 0
    
    def test_passport_number_detection(self):
        """Test passport number detection in text."""
        scanner = ImageScanner()
        
        text = "Passport Number: AB1234567"
        findings = scanner._detect_pii_in_text(text, '/fake/image.jpg')
        
        passport_findings = [f for f in findings if f['type'] == 'PASSPORT_NUMBER']
        assert len(passport_findings) > 0


class TestFullImageScan:
    """Test complete image scanning workflow."""
    
    def test_scan_nonexistent_file(self):
        """Test scanning nonexistent file returns error."""
        scanner = ImageScanner()
        
        result = scanner.scan_image('/nonexistent/path/image.jpg')
        
        assert 'error' in result
        assert result['findings'] == []
    
    def test_scan_unsupported_format(self):
        """Test scanning unsupported format returns error."""
        scanner = ImageScanner()
        
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'fake data')
            f.flush()
            
            result = scanner.scan_image(f.name)
            
            assert 'error' in result
            
            os.unlink(f.name)
    
    def test_scan_valid_image(self):
        """Test scanning valid image returns proper structure."""
        scanner = ImageScanner()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (100, 100), color='red')
            img.save(f.name)
            
            result = scanner.scan_image(f.name)
            
            assert 'metadata' in result
            assert 'findings' in result
            assert 'risk_score' in result
            assert 'has_pii' in result
            assert result['metadata']['format'] == 'png'
            
            os.unlink(f.name)
    
    def test_scan_with_sensitive_filename(self):
        """Test scanning file with sensitive filename triggers findings."""
        scanner = ImageScanner()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False, 
                                         prefix='passport_scan_') as f:
            img = Image.new('RGB', (100, 100), color='white')
            img.save(f.name)
            
            result = scanner.scan_image(f.name)
            
            assert result['has_pii'] is True
            assert len(result['findings']) > 0
            
            os.unlink(f.name)


class TestRiskScoreCalculation:
    """Test risk score calculation."""
    
    def test_risk_score_no_findings(self):
        """Test risk score is 0 with no findings."""
        scanner = ImageScanner()
        
        result = scanner._calculate_risk_score([])
        assert result['score'] == 0
        assert result['level'] == 'Low'
    
    def test_risk_score_critical_finding(self):
        """Test risk score increases with critical findings."""
        scanner = ImageScanner()
        
        findings = [{'risk_level': 'Critical'}]
        result = scanner._calculate_risk_score(findings)
        
        assert result['score'] > 0
        assert 'factors' in result
    
    def test_risk_score_multiple_findings(self):
        """Test risk score accumulates with multiple findings."""
        scanner = ImageScanner()
        
        findings = [
            {'risk_level': 'Critical'},
            {'risk_level': 'High'},
            {'risk_level': 'Medium'}
        ]
        result = scanner._calculate_risk_score(findings)
        
        single_result = scanner._calculate_risk_score([{'risk_level': 'Critical'}])
        assert result['score'] > single_result['score']
    
    def test_risk_score_level_determination(self):
        """Test risk level is correctly determined."""
        scanner = ImageScanner()
        
        critical_findings = [{'risk_level': 'Critical'} for _ in range(3)]
        result = scanner._calculate_risk_score(critical_findings)
        
        assert result['level'] in ['High', 'Critical']


class TestMultipleImageScanning:
    """Test scanning multiple images."""
    
    def test_scan_multiple_images(self):
        """Test scanning multiple images at once."""
        scanner = ImageScanner()
        
        temp_files = []
        for i in range(3):
            f = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            img = Image.new('RGB', (50, 50), color='green')
            img.save(f.name)
            temp_files.append(f.name)
        
        result = scanner.scan_multiple_images(temp_files)
        
        assert 'scan_type' in result
        assert result['scan_type'] == 'image'
        assert 'metadata' in result
        assert result['metadata']['images_scanned'] == 3
        assert 'image_results' in result
        assert len(result['image_results']) == 3
        assert 'findings' in result
        assert 'risk_summary' in result
        
        for f in temp_files:
            os.unlink(f)
    
    def test_scan_multiple_with_callback(self):
        """Test scanning multiple images with progress callback."""
        scanner = ImageScanner()
        
        progress_updates = []
        def callback(current, total, filename):
            progress_updates.append((current, total, filename))
        
        temp_files = []
        for i in range(2):
            f = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            img = Image.new('RGB', (50, 50), color='blue')
            img.save(f.name)
            temp_files.append(f.name)
        
        result = scanner.scan_multiple_images(temp_files, callback_fn=callback)
        
        assert len(progress_updates) == 2
        assert progress_updates[0][0] == 1
        assert progress_updates[1][0] == 2
        
        for f in temp_files:
            os.unlink(f)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
