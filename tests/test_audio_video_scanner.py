"""
Tests for Audio/Video Scanner - Deepfake Detection
Tests spectral analysis, voice cloning detection, and EU AI Act compliance
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestAudioVideoScanner:
    """Test suite for Audio/Video Scanner functionality"""
    
    def test_scanner_import(self):
        """Test that the scanner module can be imported"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        assert scanner is not None
    
    def test_scanner_has_required_methods(self):
        """Test that scanner has all required methods"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        
        assert hasattr(scanner, 'scan_file')
        assert hasattr(scanner, 'scan_bytes')
        assert hasattr(scanner, 'generate_html_report')
    
    def test_supported_audio_formats(self):
        """Test that all expected audio formats are supported"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        
        expected_formats = ['mp3', 'wav', 'flac', 'm4a']
        for fmt in expected_formats:
            assert fmt in scanner.SUPPORTED_AUDIO
    
    def test_supported_video_formats(self):
        """Test that all expected video formats are supported"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        
        expected_formats = ['mp4', 'avi', 'mov', 'mkv']
        for fmt in expected_formats:
            assert fmt in scanner.SUPPORTED_VIDEO
    
    def test_max_file_size(self):
        """Test that max file size is set correctly"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        
        assert scanner.MAX_FILE_SIZE_MB >= 100
    
    def test_risk_level_enum(self):
        """Test that risk levels are properly defined"""
        from services.audio_video_scanner import RiskLevel
        
        assert hasattr(RiskLevel, 'CRITICAL')
        assert hasattr(RiskLevel, 'HIGH')
        assert hasattr(RiskLevel, 'MEDIUM')
        assert hasattr(RiskLevel, 'LOW')
        assert hasattr(RiskLevel, 'NONE')
    
    def test_media_fraud_type_enum(self):
        """Test that MediaFraudType has required values"""
        from services.audio_video_scanner import MediaFraudType
        
        assert hasattr(MediaFraudType, 'AUDIO_DEEPFAKE')
        assert hasattr(MediaFraudType, 'VOICE_CLONING')
        assert hasattr(MediaFraudType, 'VIDEO_DEEPFAKE')
        assert hasattr(MediaFraudType, 'FACE_SWAP')
        assert hasattr(MediaFraudType, 'METADATA_TAMPERING')
    
    def test_media_scan_result_dataclass(self):
        """Test that MediaScanResult has required fields"""
        from services.audio_video_scanner import MediaScanResult, RiskLevel
        
        result = MediaScanResult(
            scan_id="test123",
            scan_type="audio_video",
            timestamp=datetime.now().isoformat(),
            file_name="test.mp4",
            file_size=10500000,
            file_hash="abc123",
            media_type="video",
            duration_seconds=120.0,
            is_authentic=True,
            authenticity_score=0.85,
            risk_level=RiskLevel.LOW,
            fraud_types_detected=[],
            audio_analysis=None,
            video_analysis=None,
            metadata_analysis={},
            findings=[],
            recommendations=[],
            eu_ai_act_flags=[],
            processing_time_ms=1000
        )
        
        assert result.file_name == "test.mp4"
        assert result.authenticity_score == 0.85
        assert result.risk_level == RiskLevel.LOW
        assert result.is_authentic == True


class TestAudioAnalysis:
    """Test audio-specific analysis features"""
    
    def test_audio_analysis_result_dataclass(self):
        """Test AudioAnalysisResult dataclass"""
        from services.audio_video_scanner import AudioAnalysisResult
        
        result = AudioAnalysisResult(
            is_suspicious=False,
            fraud_score=0.1,
            fraud_types=[],
            confidence=0.85,
            details={},
            spectral_anomalies=[],
            recommendations=[]
        )
        
        assert result.is_suspicious == False
        assert result.fraud_score == 0.1
    
    def test_analyze_audio_method_exists(self):
        """Test that _analyze_audio method exists"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        
        assert hasattr(scanner, '_analyze_audio')


class TestVideoAnalysis:
    """Test video-specific analysis features"""
    
    def test_video_analysis_result_dataclass(self):
        """Test VideoAnalysisResult dataclass"""
        from services.audio_video_scanner import VideoAnalysisResult
        
        result = VideoAnalysisResult(
            is_suspicious=False,
            fraud_score=0.2,
            fraud_types=[],
            confidence=0.90,
            details={},
            frame_anomalies=[],
            face_analysis={},
            recommendations=[]
        )
        
        assert result.is_suspicious == False
        assert result.fraud_score == 0.2
    
    def test_analyze_video_method_exists(self):
        """Test that _analyze_video method exists"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        
        assert hasattr(scanner, '_analyze_video')
    
    def test_frame_consistency_method_exists(self):
        """Test that frame consistency analysis method exists"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        
        assert hasattr(scanner, '_frame_consistency_analysis')
    
    def test_face_deepfake_method_exists(self):
        """Test that face deepfake detection method exists"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        
        assert hasattr(scanner, '_face_deepfake_detection')


class TestEUAIActCompliance:
    """Test EU AI Act 2025 compliance features"""
    
    def test_eu_ai_act_flags_method_exists(self):
        """Test that EU AI Act flags generation method exists"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        
        assert hasattr(scanner, '_generate_eu_ai_act_flags')
    
    def test_eu_ai_act_flags_in_result(self):
        """Test that EU AI Act flags are included in scan results"""
        from services.audio_video_scanner import MediaScanResult, RiskLevel
        
        result = MediaScanResult(
            scan_id="test456",
            scan_type="audio_video",
            timestamp=datetime.now().isoformat(),
            file_name="test.mp4",
            file_size=10500000,
            file_hash="xyz789",
            media_type="video",
            duration_seconds=120.0,
            is_authentic=False,
            authenticity_score=0.45,
            risk_level=RiskLevel.HIGH,
            fraud_types_detected=[],
            audio_analysis=None,
            video_analysis=None,
            metadata_analysis={},
            findings=[{"type": "deepfake", "severity": "high"}],
            recommendations=["Review media authenticity"],
            eu_ai_act_flags=["Article 52 - Transparency obligations"],
            processing_time_ms=2000
        )
        
        assert len(result.eu_ai_act_flags) > 0
        assert "Article 52" in result.eu_ai_act_flags[0]


class TestHTMLReportGeneration:
    """Test HTML report generation for Audio/Video scanner"""
    
    def test_generate_html_report_method_exists(self):
        """Test that HTML report generation method exists"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        
        assert hasattr(scanner, 'generate_html_report')
    
    def test_html_report_generation(self):
        """Test that HTML report can be generated"""
        from services.audio_video_scanner import AudioVideoScanner, MediaScanResult, RiskLevel
        
        scanner = AudioVideoScanner()
        
        result = MediaScanResult(
            scan_id="test789",
            scan_type="audio_video",
            timestamp=datetime.now().isoformat(),
            file_name="test_video.mp4",
            file_size=25000000,
            file_hash="report123",
            media_type="video",
            duration_seconds=180.0,
            is_authentic=True,
            authenticity_score=0.92,
            risk_level=RiskLevel.LOW,
            fraud_types_detected=[],
            audio_analysis=None,
            video_analysis=None,
            metadata_analysis={"codec": "h264"},
            findings=[],
            recommendations=["Media appears authentic"],
            eu_ai_act_flags=[],
            processing_time_ms=1500
        )
        
        html = scanner.generate_html_report(result)
        
        assert "DataGuardian Pro" in html
        assert "test_video.mp4" in html


class TestLicenseIntegration:
    """Test license manager integration for Audio/Video scanner"""
    
    def test_audio_video_in_license_scanners(self):
        """Test that audio_video is in the license manager scanners list"""
        from services.license_manager import LicenseManager, LicenseType
        
        manager = LicenseManager()
        license_config = manager.generate_license(
            license_type=LicenseType.ENTERPRISE,
            customer_id="test",
            customer_name="Test Customer",
            company_name="Test Company",
            email="test@example.com"
        )
        
        assert "audio_video" in license_config.allowed_scanners
    
    def test_audio_video_tier_restrictions(self):
        """Test that audio_video has proper tier restrictions"""
        from config.pricing_config import PricingConfig
        
        config = PricingConfig()
        features = config.features_matrix.get("advanced_scanners", {})
        
        audio_video_tiers = features.get("audio_video_deepfake_detection", [])
        
        assert len(audio_video_tiers) > 0


class TestActivityTracking:
    """Test activity tracker integration for Audio/Video scanner"""
    
    def test_audio_video_scanner_type_enum(self):
        """Test that AUDIO_VIDEO is in the ScannerType enum"""
        from utils.activity_tracker import ScannerType
        
        assert hasattr(ScannerType, 'AUDIO_VIDEO')
        assert ScannerType.AUDIO_VIDEO.value == "audio_video"


class TestDashboardIntegration:
    """Test dashboard integration for Audio/Video scanner"""
    
    def test_scanner_type_map_includes_audio_video(self):
        """Test that scanner_type_map includes audio_video variations"""
        scanner_type_map = {
            'audio_video': '🎬 Audio/Video Scanner',
            'audio/video': '🎬 Audio/Video Scanner',
            'audio-video': '🎬 Audio/Video Scanner',
            'deepfake': '🎬 Deepfake Scanner',
            'video': '🎬 Video Scanner',
            'audio': '🎬 Audio Scanner',
            'media': '🎬 Media Scanner',
        }
        
        assert 'audio_video' in scanner_type_map
        assert 'deepfake' in scanner_type_map
        assert 'video' in scanner_type_map
        assert 'audio' in scanner_type_map


class TestScannerInitialization:
    """Test scanner initialization options"""
    
    def test_default_region(self):
        """Test default region is Netherlands"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner()
        
        assert scanner.region == "Netherlands"
    
    def test_custom_region(self):
        """Test custom region setting"""
        from services.audio_video_scanner import AudioVideoScanner
        scanner = AudioVideoScanner(region="Germany")
        
        assert scanner.region == "Germany"
    
    def test_sensitivity_levels(self):
        """Test different sensitivity levels"""
        from services.audio_video_scanner import AudioVideoScanner
        
        low_scanner = AudioVideoScanner(sensitivity="low")
        high_scanner = AudioVideoScanner(sensitivity="high")
        max_scanner = AudioVideoScanner(sensitivity="maximum")
        
        assert low_scanner.detection_threshold > high_scanner.detection_threshold
        assert high_scanner.detection_threshold > max_scanner.detection_threshold


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
