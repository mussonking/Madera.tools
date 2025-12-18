"""
MADERA MCP - assess_image_quality
HINTS Tool - Assesses image quality to determine if preprocessing is needed

Execution time: ~100ms per page
Technique: DPI detection + blur detection + brightness/contrast analysis + skew detection
"""
from typing import Dict, Any, List, Tuple
from madera.mcp.tools.base import BaseTool, ToolResult
from madera.core.vision import convert_pdf_to_images
from PIL import Image
import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)


class QualityAssessor(BaseTool):
    """Assesses image quality for document processing"""

    # Quality thresholds
    MIN_DPI = 150
    GOOD_DPI = 300
    MIN_SHARPNESS = 100  # Laplacian variance threshold
    MIN_BRIGHTNESS = 50
    MAX_BRIGHTNESS = 200
    MAX_SKEW_ANGLE = 3.0  # degrees

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _detect_dpi(self, image: Image.Image) -> int:
        """
        Detect image DPI

        Returns:
            DPI value
        """
        # Try to get DPI from image info
        if hasattr(image, 'info') and 'dpi' in image.info:
            dpi_x, dpi_y = image.info['dpi']
            return int((dpi_x + dpi_y) / 2)

        # Estimate DPI based on size (assuming 8.5x11 inch page)
        width, height = image.size

        # If portrait orientation
        if height > width:
            estimated_dpi = int(height / 11)
        else:
            estimated_dpi = int(width / 11)

        return estimated_dpi

    def _detect_blur(self, image: Image.Image) -> Tuple[float, str]:
        """
        Detect image blur using Laplacian variance

        Returns:
            (blur_score, quality_level)
        """
        img_array = np.array(image)

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Calculate Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        # Determine quality level
        if variance > 500:
            quality_level = "excellent"
        elif variance > 200:
            quality_level = "good"
        elif variance > 100:
            quality_level = "acceptable"
        elif variance > 50:
            quality_level = "poor"
        else:
            quality_level = "very_poor"

        return variance, quality_level

    def _analyze_brightness_contrast(self, image: Image.Image) -> Dict[str, Any]:
        """
        Analyze brightness and contrast

        Returns:
            {
                "mean_brightness": float,
                "std_brightness": float,
                "contrast": float,
                "quality_level": str
            }
        """
        img_array = np.array(image)

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Calculate brightness (mean)
        mean_brightness = np.mean(gray)

        # Calculate contrast (std dev)
        std_brightness = np.std(gray)

        # Determine quality
        issues = []

        if mean_brightness < self.MIN_BRIGHTNESS:
            issues.append("too_dark")
        elif mean_brightness > self.MAX_BRIGHTNESS:
            issues.append("too_bright")

        if std_brightness < 30:
            issues.append("low_contrast")

        if not issues:
            quality_level = "good"
        elif len(issues) == 1:
            quality_level = "acceptable"
        else:
            quality_level = "poor"

        return {
            "mean_brightness": float(mean_brightness),
            "std_brightness": float(std_brightness),
            "contrast": float(std_brightness),
            "quality_level": quality_level,
            "issues": issues
        }

    def _detect_skew(self, image: Image.Image) -> Tuple[float, bool]:
        """
        Detect page skew angle

        Returns:
            (angle_degrees, needs_correction)
        """
        img_array = np.array(image)

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Hough line detection
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is None or len(lines) == 0:
            return 0.0, False

        # Calculate average angle
        angles = []

        for line in lines[:50]:  # Check first 50 lines
            rho, theta = line[0]

            # Convert to degrees
            angle = (theta * 180 / np.pi) - 90

            # Normalize to -45 to 45 range
            if angle < -45:
                angle += 90
            elif angle > 45:
                angle -= 90

            angles.append(angle)

        if not angles:
            return 0.0, False

        # Use median to be robust against outliers
        median_angle = float(np.median(angles))

        needs_correction = abs(median_angle) > self.MAX_SKEW_ANGLE

        return median_angle, needs_correction

    def _calculate_overall_quality_score(
        self,
        dpi: int,
        blur_score: float,
        brightness_analysis: Dict[str, Any],
        skew_angle: float
    ) -> Tuple[float, str, List[str]]:
        """
        Calculate overall quality score and recommendations

        Returns:
            (quality_score, quality_level, recommendations)
        """
        score = 100.0
        recommendations = []

        # DPI penalty
        if dpi < self.MIN_DPI:
            penalty = (self.MIN_DPI - dpi) / self.MIN_DPI * 40
            score -= penalty
            recommendations.append(f"increase_dpi_from_{dpi}_to_{self.MIN_DPI}")
        elif dpi < self.GOOD_DPI:
            penalty = (self.GOOD_DPI - dpi) / self.GOOD_DPI * 10
            score -= penalty

        # Blur penalty
        if blur_score < self.MIN_SHARPNESS:
            penalty = (self.MIN_SHARPNESS - blur_score) / self.MIN_SHARPNESS * 30
            score -= penalty
            recommendations.append("image_too_blurry")

        # Brightness/contrast penalty
        for issue in brightness_analysis["issues"]:
            score -= 15
            recommendations.append(issue)

        # Skew penalty
        if abs(skew_angle) > self.MAX_SKEW_ANGLE:
            penalty = min(abs(skew_angle) * 5, 20)
            score -= penalty
            recommendations.append(f"deskew_{abs(skew_angle):.1f}_degrees")

        # Clamp score
        score = max(0, min(100, score))

        # Determine quality level
        if score >= 85:
            quality_level = "excellent"
        elif score >= 70:
            quality_level = "good"
        elif score >= 50:
            quality_level = "acceptable"
        elif score >= 30:
            quality_level = "poor"
        else:
            quality_level = "very_poor"

        return score, quality_level, recommendations

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Assess image quality in a PDF

        Args:
            presigned_url: MinIO presigned URL for PDF

        Returns:
            ToolResult with hints: {
                "pages": {
                    1: {
                        "dpi": 300,
                        "blur_score": 450,
                        "brightness": 128,
                        "contrast": 65,
                        "skew_angle": 1.2,
                        "quality_score": 92,
                        "quality_level": "excellent",
                        "needs_preprocessing": false
                    }
                },
                "overall_quality": "good",
                "needs_preprocessing": false,
                "recommendations": []
            }
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Convert to images
        images = convert_pdf_to_images(local_pdf, dpi=150)  # Lower DPI for analysis
        total_pages = len(images)

        logger.info(f"Analyzing {total_pages} pages for quality assessment")

        # Analyze each page
        pages_analysis = {}
        all_recommendations = set()

        for page_num, image in enumerate(images, start=1):
            # Detect DPI
            dpi = self._detect_dpi(image)

            # Detect blur
            blur_score, blur_level = self._detect_blur(image)

            # Analyze brightness/contrast
            brightness_analysis = self._analyze_brightness_contrast(image)

            # Detect skew
            skew_angle, needs_deskew = self._detect_skew(image)

            # Calculate overall quality
            quality_score, quality_level, recommendations = self._calculate_overall_quality_score(
                dpi, blur_score, brightness_analysis, skew_angle
            )

            all_recommendations.update(recommendations)

            pages_analysis[page_num] = {
                "dpi": dpi,
                "blur_score": round(blur_score, 2),
                "blur_level": blur_level,
                "brightness": round(brightness_analysis["mean_brightness"], 2),
                "contrast": round(brightness_analysis["contrast"], 2),
                "skew_angle": round(skew_angle, 2),
                "quality_score": round(quality_score, 2),
                "quality_level": quality_level,
                "needs_preprocessing": len(recommendations) > 0,
                "recommendations": recommendations
            }

            logger.info(
                f"Page {page_num}: Quality {quality_level} "
                f"(score: {quality_score:.0f}, DPI: {dpi}, "
                f"blur: {blur_score:.0f}, skew: {skew_angle:.1f}°)"
            )

        # Calculate overall statistics
        avg_quality_score = sum(p["quality_score"] for p in pages_analysis.values()) / total_pages

        if avg_quality_score >= 85:
            overall_quality = "excellent"
        elif avg_quality_score >= 70:
            overall_quality = "good"
        elif avg_quality_score >= 50:
            overall_quality = "acceptable"
        else:
            overall_quality = "poor"

        needs_preprocessing = any(p["needs_preprocessing"] for p in pages_analysis.values())

        # Create hints message
        if needs_preprocessing:
            hints_message = f"Overall quality: {overall_quality}. Preprocessing recommended: " + \
                           ", ".join(all_recommendations)
        else:
            hints_message = f"Overall quality: {overall_quality}. No preprocessing needed."

        # Calculate overall confidence
        overall_confidence = 0.90  # High confidence in quality metrics

        logger.info(
            f"Quality assessment complete: {overall_quality} "
            f"(avg score: {avg_quality_score:.0f}). "
            f"Preprocessing needed: {needs_preprocessing}"
        )

        return ToolResult(
            success=True,
            data={
                "pages": pages_analysis,
                "overall_quality": overall_quality,
                "average_quality_score": round(avg_quality_score, 2),
                "needs_preprocessing": needs_preprocessing,
                "recommendations": sorted(list(all_recommendations)),
                "total_pages": total_pages
            },
            hints={
                "overall_quality": overall_quality,
                "needs_preprocessing": needs_preprocessing,
                "recommendations": sorted(list(all_recommendations)),
                "message": hints_message
            },
            confidence=overall_confidence
        )


# Register tool with MCP server
def register(mcp_server):
    """Register assess_image_quality tool"""
    assessor = QualityAssessor()

    @mcp_server.tool()
    async def assess_image_quality(presigned_url: str) -> Dict[str, Any]:
        """
        Assesses image quality to determine if preprocessing is needed.

        This tool analyzes DPI, sharpness (blur detection), brightness/contrast,
        and page skew to determine if images are suitable for AI analysis or if
        preprocessing (enhancement, deskewing) is recommended.

        Helps AI make better decisions about document processing strategy.

        Args:
            presigned_url: MinIO presigned URL for the PDF to analyze

        Returns:
            {
                "success": true,
                "data": {
                    "pages": {
                        1: {
                            "dpi": 300,
                            "blur_score": 450,
                            "blur_level": "excellent",
                            "brightness": 128,
                            "contrast": 65,
                            "skew_angle": 1.2,
                            "quality_score": 92,
                            "quality_level": "excellent",
                            "needs_preprocessing": false,
                            "recommendations": []
                        }
                    },
                    "overall_quality": "good",
                    "average_quality_score": 87,
                    "needs_preprocessing": false,
                    "recommendations": [],
                    "total_pages": 3
                },
                "hints": {
                    "overall_quality": "good",
                    "needs_preprocessing": false,
                    "recommendations": [],
                    "message": "Overall quality: good. No preprocessing needed."
                },
                "confidence": 0.90,
                "execution_time_ms": 98
            }

        Quality metrics:
            - DPI: Resolution (min 150, good 300+)
            - Blur score: Laplacian variance (min 100, good 500+)
            - Brightness: Mean pixel value (50-200 range)
            - Contrast: Standard deviation (higher is better)
            - Skew: Page rotation angle (max 3° acceptable)

        Recommendations:
            - increase_dpi: Rescan at higher resolution
            - image_too_blurry: Rescan or enhance
            - too_dark/too_bright: Adjust scanning settings
            - low_contrast: Enhance image
            - deskew_X_degrees: Rotate page

        Example usage:
            result = await assess_image_quality("https://minio/file.pdf?presigned=...")
            if result["hints"]["needs_preprocessing"]:
                recommendations = result["hints"]["recommendations"]
                prompt += f"Warning: Image quality issues detected: {recommendations}"
        """
        result = await assessor.execute(presigned_url=presigned_url)
        return result.model_dump()
