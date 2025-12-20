"""
Advanced Image Fraud Detection Module
Enterprise-grade fake/manipulated image detection using computer vision techniques.

Features:
- Error Level Analysis (ELA) for detecting edited regions
- Statistical anomaly detection for AI-generated images
- Noise pattern analysis for deepfake detection
- Metadata forensics for authenticity verification
- Face consistency analysis
- Copy-move forgery detection

No external API dependencies - runs fully locally for GDPR compliance.
"""

import logging
import os
import io
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageChops, ImageEnhance, ImageFilter
    from PIL.ExifTags import TAGS, GPSTAGS
    CV_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenCV/PIL not available: {e}")
    CV_AVAILABLE = False


class FraudType(Enum):
    """Types of image fraud that can be detected."""
    DEEPFAKE = "deepfake"
    AI_GENERATED = "ai_generated"
    PHOTOSHOP_EDIT = "photoshop_edit"
    COPY_MOVE_FORGERY = "copy_move_forgery"
    SPLICING = "splicing"
    METADATA_TAMPERING = "metadata_tampering"
    FACE_SWAP = "face_swap"
    DOCUMENT_FORGERY = "document_forgery"


@dataclass
class FraudDetectionResult:
    """Result of fraud detection analysis."""
    is_suspicious: bool
    fraud_score: float  # 0.0 to 1.0
    fraud_types: List[FraudType]
    confidence: float
    details: Dict[str, Any]
    recommendations: List[str]
    eu_ai_act_flags: List[str]


class AdvancedFraudDetector:
    """
    Enterprise-grade image fraud detection using computer vision.
    
    Detection Methods:
    1. ELA (Error Level Analysis) - Detects JPEG compression inconsistencies
    2. Statistical Analysis - Detects AI-generated image patterns
    3. Noise Analysis - Detects deepfake artifacts
    4. Metadata Forensics - Detects tampering in EXIF data
    5. Face Consistency - Detects face swap/manipulation
    6. Copy-Move Detection - Detects cloned regions
    """
    
    def __init__(self, region: str = "Netherlands"):
        self.region = region
        self.ela_quality = 90  # JPEG quality for ELA
        self.detection_threshold = 0.35  # Overall fraud threshold
        
        logger.info(f"AdvancedFraudDetector initialized for region: {region}")
    
    def analyze_image(self, image_path: str) -> FraudDetectionResult:
        """
        Perform comprehensive fraud analysis on an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            FraudDetectionResult with detailed analysis
        """
        if not CV_AVAILABLE:
            return FraudDetectionResult(
                is_suspicious=False,
                fraud_score=0.0,
                fraud_types=[],
                confidence=0.0,
                details={"error": "OpenCV/PIL not available"},
                recommendations=["Install OpenCV and PIL for fraud detection"],
                eu_ai_act_flags=[]
            )
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return self._create_error_result("Could not load image")
            
            pil_image = Image.open(image_path)
            
            # Run all detection methods
            ela_result = self._error_level_analysis(image_path, pil_image)
            noise_result = self._noise_pattern_analysis(image)
            stat_result = self._statistical_analysis(image)
            face_result = self._face_consistency_analysis(image)
            meta_result = self._metadata_forensics(pil_image)
            copymove_result = self._copy_move_detection(image)
            ai_gen_result = self._ai_generation_detection(image)
            
            # Combine results
            all_scores = [
                ela_result["score"] * 0.20,       # 20% weight
                noise_result["score"] * 0.15,      # 15% weight
                stat_result["score"] * 0.15,       # 15% weight
                face_result["score"] * 0.15,       # 15% weight
                meta_result["score"] * 0.10,       # 10% weight
                copymove_result["score"] * 0.10,   # 10% weight
                ai_gen_result["score"] * 0.15      # 15% weight
            ]
            
            total_score = sum(all_scores)
            
            # Determine fraud types
            fraud_types = []
            if ela_result["score"] > 0.4:
                fraud_types.append(FraudType.PHOTOSHOP_EDIT)
            if noise_result["score"] > 0.4 or ai_gen_result["score"] > 0.4:
                fraud_types.append(FraudType.DEEPFAKE)
            if ai_gen_result["score"] > 0.5:
                fraud_types.append(FraudType.AI_GENERATED)
            if face_result["score"] > 0.4:
                fraud_types.append(FraudType.FACE_SWAP)
            if meta_result["score"] > 0.5:
                fraud_types.append(FraudType.METADATA_TAMPERING)
            if copymove_result["score"] > 0.4:
                fraud_types.append(FraudType.COPY_MOVE_FORGERY)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(total_score, fraud_types)
            
            # EU AI Act Article 50 flags
            eu_ai_act_flags = self._check_eu_ai_act_compliance(total_score, fraud_types)
            
            return FraudDetectionResult(
                is_suspicious=total_score >= self.detection_threshold,
                fraud_score=round(total_score, 3),
                fraud_types=fraud_types,
                confidence=round(min(total_score * 1.2, 0.98), 2),
                details={
                    "ela_analysis": ela_result,
                    "noise_analysis": noise_result,
                    "statistical_analysis": stat_result,
                    "face_analysis": face_result,
                    "metadata_analysis": meta_result,
                    "copymove_analysis": copymove_result,
                    "ai_generation_analysis": ai_gen_result,
                    "image_path": image_path,
                    "analysis_timestamp": datetime.now().isoformat()
                },
                recommendations=recommendations,
                eu_ai_act_flags=eu_ai_act_flags
            )
            
        except Exception as e:
            logger.error(f"Fraud detection failed: {e}")
            return self._create_error_result(str(e))
    
    def _error_level_analysis(self, image_path: str, pil_image: Image.Image) -> Dict[str, Any]:
        """
        Error Level Analysis (ELA) - Detects JPEG compression inconsistencies.
        Edited regions have different compression levels than original content.
        """
        try:
            # Save image at known quality
            temp_path = "/tmp/ela_temp.jpg"
            pil_image.save(temp_path, "JPEG", quality=self.ela_quality)
            
            # Reload and compare
            resaved = Image.open(temp_path)
            ela = ImageChops.difference(pil_image.convert("RGB"), resaved.convert("RGB"))
            
            # Enhance difference for analysis
            extrema = ela.getextrema()
            max_diff = max([ex[1] for ex in extrema])
            
            if max_diff == 0:
                scale = 1
            else:
                scale = 255.0 / max_diff
            
            ela = ImageEnhance.Brightness(ela).enhance(scale)
            
            # Analyze ELA image for anomalies
            ela_array = np.array(ela)
            
            # Calculate statistics
            mean_ela = np.mean(ela_array)
            std_ela = np.std(ela_array)
            max_ela = np.max(ela_array)
            
            # High variation suggests manipulation
            ela_score = 0.0
            if std_ela > 30:
                ela_score += 0.3
            if std_ela > 50:
                ela_score += 0.3
            if max_ela > 200:
                ela_score += 0.2
            if mean_ela > 50:
                ela_score += 0.2
            
            # Clean up
            try:
                os.remove(temp_path)
            except:
                pass
            
            return {
                "score": min(ela_score, 1.0),
                "mean_ela": round(mean_ela, 2),
                "std_ela": round(std_ela, 2),
                "max_ela": int(max_ela),
                "interpretation": self._interpret_ela_score(ela_score)
            }
            
        except Exception as e:
            logger.warning(f"ELA analysis failed: {e}")
            return {"score": 0.0, "error": str(e)}
    
    def _noise_pattern_analysis(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze noise patterns to detect deepfakes and AI-generated content.
        Real images have consistent noise; manipulated images have anomalies.
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Extract high-frequency noise using Laplacian
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            laplacian_var = laplacian.var()
            
            # Analyze noise distribution
            noise = gray.astype(float) - cv2.GaussianBlur(gray, (5, 5), 0).astype(float)
            noise_std = np.std(noise)
            noise_mean = np.mean(np.abs(noise))
            
            # Check for unnatural noise patterns
            # AI-generated images often have too smooth or too uniform noise
            score = 0.0
            
            # Very low noise variance (too smooth - AI generated)
            if laplacian_var < 100:
                score += 0.4
            
            # Very uniform noise (unnatural)
            if noise_std < 5:
                score += 0.3
            
            # Check for periodic patterns in noise (GAN artifacts)
            fft = np.fft.fft2(noise)
            fft_shift = np.fft.fftshift(fft)
            magnitude = np.abs(fft_shift)
            
            # Periodic artifacts show as peaks in FFT
            peak_ratio = np.max(magnitude) / (np.mean(magnitude) + 1e-10)
            if peak_ratio > 1000:
                score += 0.3
            
            return {
                "score": min(score, 1.0),
                "laplacian_variance": round(laplacian_var, 2),
                "noise_std": round(noise_std, 2),
                "noise_mean": round(noise_mean, 2),
                "fft_peak_ratio": round(peak_ratio, 2),
                "interpretation": "Smooth/uniform" if score > 0.4 else "Natural noise pattern"
            }
            
        except Exception as e:
            logger.warning(f"Noise analysis failed: {e}")
            return {"score": 0.0, "error": str(e)}
    
    def _statistical_analysis(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Statistical analysis to detect anomalies in color distribution and gradients.
        """
        try:
            # Convert to different color spaces
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # Analyze color channel statistics
            b, g, r = cv2.split(image)
            h, s, v = cv2.split(hsv)
            
            # Calculate statistics
            stats = {
                "r_mean": np.mean(r), "r_std": np.std(r),
                "g_mean": np.mean(g), "g_std": np.std(g),
                "b_mean": np.mean(b), "b_std": np.std(b),
                "saturation_mean": np.mean(s),
                "saturation_std": np.std(s)
            }
            
            score = 0.0
            
            # Check for unnatural color distributions
            # AI images often have unusual saturation patterns
            if stats["saturation_std"] < 20:
                score += 0.2  # Too uniform saturation
            
            # Check for channel correlation anomalies
            rg_corr = np.corrcoef(r.flatten(), g.flatten())[0, 1]
            rb_corr = np.corrcoef(r.flatten(), b.flatten())[0, 1]
            
            # Natural images have moderate channel correlation
            if abs(rg_corr) > 0.95 or abs(rb_corr) > 0.95:
                score += 0.2  # Unnaturally high correlation
            
            # Check gradient consistency
            grad_x = cv2.Sobel(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.CV_64F, 1, 0)
            grad_y = cv2.Sobel(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.CV_64F, 0, 1)
            grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            grad_std = np.std(grad_magnitude)
            if grad_std < 10:
                score += 0.2  # Too smooth gradients (AI generated)
            
            return {
                "score": min(score, 1.0),
                "channel_correlation_rg": round(rg_corr, 3),
                "channel_correlation_rb": round(rb_corr, 3),
                "gradient_std": round(grad_std, 2),
                "saturation_std": round(stats["saturation_std"], 2)
            }
            
        except Exception as e:
            logger.warning(f"Statistical analysis failed: {e}")
            return {"score": 0.0, "error": str(e)}
    
    def _face_consistency_analysis(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze facial features for consistency (detects face swaps/deepfakes).
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Load face detector
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            
            if len(faces) == 0:
                return {"score": 0.0, "faces_detected": 0, "note": "No faces detected"}
            
            score = 0.0
            face_details = []
            
            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                
                # Analyze face region for artifacts
                laplacian_var = cv2.Laplacian(face_roi, cv2.CV_64F).var()
                
                # Check for blur inconsistencies (deepfake artifact)
                face_blur = cv2.Laplacian(face_roi, cv2.CV_64F).var()
                bg_region = gray[max(0, y-20):y, x:x+w] if y > 20 else gray[y+h:y+h+20, x:x+w]
                if bg_region.size > 0:
                    bg_blur = cv2.Laplacian(bg_region, cv2.CV_64F).var()
                    blur_ratio = face_blur / (bg_blur + 1e-10)
                    
                    # Face significantly different blur than background
                    if blur_ratio < 0.3 or blur_ratio > 3.0:
                        score += 0.3
                
                # Check for edge artifacts around face boundary
                edges = cv2.Canny(face_roi, 100, 200)
                edge_density = np.sum(edges > 0) / edges.size
                
                # Unusual edge patterns
                if edge_density < 0.02 or edge_density > 0.3:
                    score += 0.2
                
                face_details.append({
                    "position": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                    "sharpness": round(laplacian_var, 2),
                    "edge_density": round(edge_density, 4)
                })
            
            return {
                "score": min(score, 1.0),
                "faces_detected": len(faces),
                "face_details": face_details,
                "interpretation": "Potential manipulation" if score > 0.3 else "Faces appear consistent"
            }
            
        except Exception as e:
            logger.warning(f"Face analysis failed: {e}")
            return {"score": 0.0, "error": str(e)}
    
    def _metadata_forensics(self, pil_image: Image.Image) -> Dict[str, Any]:
        """
        Analyze image metadata for tampering indicators.
        """
        try:
            exif_data = {}
            suspicious_indicators = []
            score = 0.0
            
            if hasattr(pil_image, '_getexif') and pil_image._getexif():
                exif = pil_image._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = str(value)[:100]  # Truncate long values
                
                # Check for software editing indicators
                software = exif_data.get('Software', '').lower()
                editing_software = ['photoshop', 'gimp', 'lightroom', 'affinity', 'paint']
                if any(sw in software for sw in editing_software):
                    score += 0.4
                    suspicious_indicators.append(f"Editing software detected: {software}")
                
                # Check for missing expected fields
                expected_fields = ['Make', 'Model', 'DateTime']
                missing = [f for f in expected_fields if f not in exif_data]
                if len(missing) >= 2:
                    score += 0.2
                    suspicious_indicators.append(f"Missing expected metadata: {missing}")
                
                # Check for date inconsistencies
                if 'DateTime' in exif_data and 'DateTimeOriginal' in exif_data:
                    if exif_data['DateTime'] != exif_data['DateTimeOriginal']:
                        score += 0.3
                        suspicious_indicators.append("Date modified after original capture")
            else:
                # No EXIF at all can be suspicious for camera photos
                score += 0.1
                suspicious_indicators.append("No EXIF metadata found")
            
            return {
                "score": min(score, 1.0),
                "exif_fields_found": len(exif_data),
                "suspicious_indicators": suspicious_indicators,
                "has_gps": 'GPSInfo' in exif_data
            }
            
        except Exception as e:
            logger.warning(f"Metadata analysis failed: {e}")
            return {"score": 0.0, "error": str(e)}
    
    def _copy_move_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect copy-move forgery (cloned regions within image).
        Uses block matching to find duplicated regions.
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Downsample for efficiency
            scale = 0.5
            small = cv2.resize(gray, None, fx=scale, fy=scale)
            
            # Use ORB for feature detection
            orb = cv2.ORB_create(nfeatures=500)
            keypoints, descriptors = orb.detectAndCompute(small, None)
            
            if descriptors is None or len(keypoints) < 10:
                return {"score": 0.0, "note": "Insufficient features for analysis"}
            
            # Match features to find duplicates
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            matches = bf.knnMatch(descriptors, descriptors, k=2)
            
            # Find suspicious matches (similar regions in different locations)
            suspicious_matches = 0
            for m, n in matches:
                if m.distance < 0.6 * n.distance:
                    # Check if match is not to itself
                    pt1 = keypoints[m.queryIdx].pt
                    pt2 = keypoints[m.trainIdx].pt
                    distance = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                    
                    # Significant spatial distance = potential clone
                    if distance > 50:
                        suspicious_matches += 1
            
            # Calculate score based on suspicious matches
            match_ratio = suspicious_matches / (len(keypoints) + 1)
            score = min(match_ratio * 5, 1.0)  # Scale appropriately
            
            return {
                "score": score,
                "features_detected": len(keypoints),
                "suspicious_matches": suspicious_matches,
                "interpretation": "Potential cloning detected" if score > 0.3 else "No obvious cloning"
            }
            
        except Exception as e:
            logger.warning(f"Copy-move detection failed: {e}")
            return {"score": 0.0, "error": str(e)}
    
    def _ai_generation_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect AI-generated images using multiple heuristics.
        Looks for common artifacts in GAN/diffusion model outputs.
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            
            score = 0.0
            indicators = []
            
            # Check for unusual aspect ratios (AI often uses standard sizes)
            common_ai_sizes = [(512, 512), (768, 768), (1024, 1024), (512, 768), (768, 512)]
            if (w, h) in common_ai_sizes or (h, w) in common_ai_sizes:
                score += 0.15
                indicators.append("Common AI generation size detected")
            
            # Check for symmetric patterns (common in AI)
            left_half = gray[:, :w//2]
            right_half = cv2.flip(gray[:, w//2:], 1)
            if left_half.shape == right_half.shape:
                symmetry = np.corrcoef(left_half.flatten(), right_half.flatten())[0, 1]
                if symmetry > 0.8:
                    score += 0.2
                    indicators.append(f"High symmetry detected: {symmetry:.2f}")
            
            # Check for texture consistency (AI images often too consistent)
            texture_blocks = []
            block_size = 64
            for i in range(0, h - block_size, block_size):
                for j in range(0, w - block_size, block_size):
                    block = gray[i:i+block_size, j:j+block_size]
                    texture_blocks.append(np.std(block))
            
            if texture_blocks:
                texture_variance = np.var(texture_blocks)
                if texture_variance < 50:
                    score += 0.2
                    indicators.append("Unnaturally consistent texture")
            
            # Check color histogram for unnatural distributions
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            h_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
            h_hist = h_hist.flatten() / h_hist.sum()
            
            # AI images often have unusual hue distributions
            h_entropy = -np.sum(h_hist * np.log2(h_hist + 1e-10))
            if h_entropy < 4.0:  # Low entropy = limited color palette
                score += 0.15
                indicators.append(f"Limited color diversity (entropy: {h_entropy:.2f})")
            
            # Check for high-frequency artifacts (GAN fingerprints)
            fft = np.fft.fft2(gray)
            fft_shift = np.fft.fftshift(fft)
            magnitude = np.log(np.abs(fft_shift) + 1)
            
            # GAN images often have periodic patterns in FFT
            center_region = magnitude[h//2-10:h//2+10, w//2-10:w//2+10]
            outer_region = np.concatenate([
                magnitude[:20, :].flatten(),
                magnitude[-20:, :].flatten()
            ])
            
            if np.mean(outer_region) / (np.mean(center_region) + 1e-10) > 0.5:
                score += 0.15
                indicators.append("Unusual frequency distribution")
            
            return {
                "score": min(score, 1.0),
                "indicators": indicators,
                "texture_variance": round(texture_variance if texture_blocks else 0, 2),
                "color_entropy": round(h_entropy, 2),
                "interpretation": "Likely AI-generated" if score > 0.4 else "Appears natural"
            }
            
        except Exception as e:
            logger.warning(f"AI generation detection failed: {e}")
            return {"score": 0.0, "error": str(e)}
    
    def _interpret_ela_score(self, score: float) -> str:
        """Interpret ELA score."""
        if score >= 0.7:
            return "Strong indicators of image manipulation"
        elif score >= 0.4:
            return "Moderate manipulation indicators"
        elif score >= 0.2:
            return "Minor anomalies detected"
        else:
            return "No significant manipulation detected"
    
    def _generate_recommendations(self, score: float, fraud_types: List[FraudType]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        if score >= 0.7:
            recommendations.append("CRITICAL: High likelihood of image manipulation. Verify authenticity before use.")
            recommendations.append("Request original unedited version if possible.")
            recommendations.append("Document this finding for compliance records.")
        elif score >= 0.4:
            recommendations.append("MODERATE RISK: Manual review recommended before accepting image.")
            recommendations.append("Request additional verification of image source.")
        elif score >= 0.2:
            recommendations.append("LOW RISK: Minor anomalies detected. Consider additional checks for sensitive use cases.")
        else:
            recommendations.append("No significant fraud indicators detected.")
        
        if FraudType.DEEPFAKE in fraud_types or FraudType.AI_GENERATED in fraud_types:
            recommendations.append("EU AI Act Article 50: Synthetic content must be clearly labeled if used publicly.")
        
        if FraudType.DOCUMENT_FORGERY in fraud_types:
            recommendations.append("ALERT: Potential document forgery. Do not accept for legal or financial purposes.")
        
        return recommendations
    
    def _check_eu_ai_act_compliance(self, score: float, fraud_types: List[FraudType]) -> List[str]:
        """Check EU AI Act compliance requirements."""
        flags = []
        
        if FraudType.DEEPFAKE in fraud_types or FraudType.AI_GENERATED in fraud_types:
            flags.append("Article 50(2): Synthetic content labeling required")
            flags.append("Article 50(4): AI-generated content transparency obligation")
        
        if score >= 0.5:
            flags.append("Article 52: Transparency requirements may apply")
        
        if self.region == "Netherlands":
            flags.append("Dutch AI Act Implementation: AP enforcement applies")
        
        return flags
    
    def _create_error_result(self, error: str) -> FraudDetectionResult:
        """Create an error result."""
        return FraudDetectionResult(
            is_suspicious=False,
            fraud_score=0.0,
            fraud_types=[],
            confidence=0.0,
            details={"error": error},
            recommendations=["Analysis failed - manual review required"],
            eu_ai_act_flags=[]
        )


# Singleton instance
_fraud_detector_instance = None

def get_fraud_detector(region: str = "Netherlands") -> AdvancedFraudDetector:
    """Get singleton fraud detector instance."""
    global _fraud_detector_instance
    if _fraud_detector_instance is None:
        _fraud_detector_instance = AdvancedFraudDetector(region)
    return _fraud_detector_instance
