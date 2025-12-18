"""
MADERA MCP - detect_id_card_sides
HINTS Tool - Detects ID card recto/verso in images

Execution time: ~50ms per image
Technique: Aspect ratio + corner detection + visual patterns
"""
from typing import Dict, Any, List, Tuple
from madera.mcp.tools.base import BaseTool, ToolResult
from madera.core.vision import convert_pdf_to_images
from PIL import Image
import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)


class IDCardDetector(BaseTool):
    """Detects ID card sides (recto/verso) without AI"""

    # Standard ID card aspect ratios
    CARD_ASPECT_RATIOS = {
        'credit_card': 1.586,  # 85.60 × 53.98 mm (ISO/IEC 7810)
        'driving_license_qc': 1.58,  # Quebec driving license
        'health_card_qc': 1.56,  # Quebec health card
    }

    ASPECT_RATIO_TOLERANCE = 0.15

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _calculate_aspect_ratio(self, image: Image.Image) -> float:
        """Calculate image aspect ratio"""
        width, height = image.size
        return width / height

    def _detect_rounded_corners(self, image: Image.Image) -> Tuple[bool, float]:
        """
        Detect if image has rounded corners (common for ID cards)

        Returns:
            (has_rounded_corners, confidence)
        """
        # Convert to numpy array
        img_array = np.array(image)

        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Get image dimensions
        h, w = gray.shape

        # Check corners (10% of width/height)
        corner_size = int(min(w, h) * 0.1)

        corners = [
            gray[0:corner_size, 0:corner_size],  # Top-left
            gray[0:corner_size, -corner_size:],  # Top-right
            gray[-corner_size:, 0:corner_size],  # Bottom-left
            gray[-corner_size:, -corner_size:],  # Bottom-right
        ]

        # Count corners with significant edge curvature
        rounded_count = 0
        for corner in corners:
            # Apply Canny edge detection
            edges = cv2.Canny(corner, 50, 150)

            # If less than 30% of corner pixels are edges, likely rounded
            edge_percentage = np.sum(edges > 0) / edges.size
            if edge_percentage < 0.3:
                rounded_count += 1

        has_rounded = rounded_count >= 3  # At least 3 corners rounded
        confidence = rounded_count / 4.0

        return has_rounded, confidence

    def _detect_barcode(self, image: Image.Image) -> Tuple[bool, float]:
        """
        Detect barcode presence (common on Quebec driving license verso)

        Returns:
            (has_barcode, confidence)
        """
        img_array = np.array(image)

        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        h, w = gray.shape

        # Focus on bottom third (where barcodes usually are)
        bottom_third = gray[int(h * 0.66):, :]

        # Look for horizontal line patterns (characteristic of barcodes)
        # Apply horizontal sobel filter
        sobel_x = cv2.Sobel(bottom_third, cv2.CV_64F, 1, 0, ksize=3)
        sobel_x = np.abs(sobel_x)

        # Threshold and count strong horizontal edges
        threshold = np.mean(sobel_x) + np.std(sobel_x)
        strong_edges = sobel_x > threshold

        # Barcode should have consistent vertical lines
        vertical_edge_counts = np.sum(strong_edges, axis=0)

        # Check for periodicity (barcode pattern)
        if len(vertical_edge_counts) > 10:
            # Simple periodicity check
            high_edge_columns = np.sum(vertical_edge_counts > (h * 0.1))
            has_barcode = high_edge_columns > (w * 0.2)
            confidence = min(high_edge_columns / (w * 0.3), 1.0)
        else:
            has_barcode = False
            confidence = 0.0

        return has_barcode, confidence

    def _detect_magnetic_stripe(self, image: Image.Image) -> Tuple[bool, float]:
        """
        Detect magnetic stripe (dark horizontal band)

        Returns:
            (has_stripe, confidence)
        """
        img_array = np.array(image)

        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        h, w = gray.shape

        # Scan for dark horizontal bands
        row_means = np.mean(gray, axis=1)

        # Find consecutive dark rows (magnetic stripe)
        dark_threshold = np.mean(row_means) - np.std(row_means)
        dark_rows = row_means < dark_threshold

        # Find longest consecutive sequence
        max_consecutive = 0
        current_consecutive = 0

        for is_dark in dark_rows:
            if is_dark:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        # Magnetic stripe is typically 5-10% of card height
        expected_stripe_height = h * 0.075
        has_stripe = max_consecutive > (expected_stripe_height * 0.5)

        if has_stripe:
            confidence = min(max_consecutive / expected_stripe_height, 1.0)
        else:
            confidence = 0.0

        return has_stripe, confidence

    def _detect_hologram_area(self, image: Image.Image) -> Tuple[bool, float]:
        """
        Detect hologram/security feature area (shiny, reflective regions)

        Returns:
            (has_hologram, confidence)
        """
        img_array = np.array(image)

        if len(img_array.shape) == 3:
            # Holograms often have high variance in color channels
            std_per_channel = np.std(img_array, axis=(0, 1))
            mean_std = np.mean(std_per_channel)

            # Also check for high local variance (shiny areas)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
            mean_std = np.std(gray)

        # Calculate local standard deviation using sliding window
        h, w = gray.shape
        kernel_size = int(min(h, w) * 0.1)

        if kernel_size < 3:
            return False, 0.0

        # Use cv2 blur and variance to detect high-variance regions
        blur = cv2.GaussianBlur(gray, (kernel_size | 1, kernel_size | 1), 0)
        variance = cv2.absdiff(gray, blur)

        # High variance regions indicate potential hologram
        high_variance_threshold = np.mean(variance) + np.std(variance)
        high_variance_pixels = np.sum(variance > high_variance_threshold)
        high_variance_percentage = high_variance_pixels / (h * w)

        # Holograms typically cover 10-30% of card area
        has_hologram = 0.05 < high_variance_percentage < 0.35
        confidence = min(high_variance_percentage / 0.2, 1.0)

        return has_hologram, confidence

    def _classify_card_side(self, image: Image.Image) -> Dict[str, Any]:
        """
        Classify if image is ID card and which side (recto/verso)

        Returns:
            {
                "is_id_card": bool,
                "side": "recto" | "verso" | "unknown",
                "card_type": str,
                "confidence": float,
                "features": dict
            }
        """
        # Check aspect ratio
        aspect_ratio = self._calculate_aspect_ratio(image)

        is_card_ratio = False
        for card_type, expected_ratio in self.CARD_ASPECT_RATIOS.items():
            if abs(aspect_ratio - expected_ratio) / expected_ratio < self.ASPECT_RATIO_TOLERANCE:
                is_card_ratio = True
                detected_card_type = card_type
                break
        else:
            detected_card_type = "unknown"

        if not is_card_ratio:
            return {
                "is_id_card": False,
                "side": "unknown",
                "card_type": "not_a_card",
                "confidence": 0.1,
                "features": {"aspect_ratio": aspect_ratio}
            }

        # Detect features
        has_rounded, rounded_conf = self._detect_rounded_corners(image)
        has_barcode, barcode_conf = self._detect_barcode(image)
        has_stripe, stripe_conf = self._detect_magnetic_stripe(image)
        has_hologram, hologram_conf = self._detect_hologram_area(image)

        features = {
            "aspect_ratio": aspect_ratio,
            "rounded_corners": has_rounded,
            "barcode": has_barcode,
            "magnetic_stripe": has_stripe,
            "hologram": has_hologram,
        }

        # Determine side based on features
        recto_score = 0.0
        verso_score = 0.0

        # Recto typically has hologram/security features
        if has_hologram:
            recto_score += hologram_conf * 0.6

        # Verso typically has barcode or magnetic stripe
        if has_barcode:
            verso_score += barcode_conf * 0.7
        if has_stripe:
            verso_score += stripe_conf * 0.5

        # Both should have rounded corners
        base_score = rounded_conf * 0.3

        recto_score += base_score
        verso_score += base_score

        # Determine side
        if max(recto_score, verso_score) < 0.3:
            side = "unknown"
            confidence = 0.3
        elif recto_score > verso_score:
            side = "recto"
            confidence = min(recto_score, 0.95)
        else:
            side = "verso"
            confidence = min(verso_score, 0.95)

        return {
            "is_id_card": True,
            "side": side,
            "card_type": detected_card_type,
            "confidence": confidence,
            "features": features
        }

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Detect ID card sides in a PDF

        Args:
            presigned_url: MinIO presigned URL for PDF

        Returns:
            ToolResult with hints: {
                "id_cards": [
                    {"page": 1, "side": "recto", "card_type": "driving_license_qc", "confidence": 0.92},
                    {"page": 2, "side": "verso", "card_type": "driving_license_qc", "confidence": 0.88}
                ],
                "groupings": [[1, 2]],  # Suggested page groupings
                "total_pages": 2
            }
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Convert to images
        images = convert_pdf_to_images(local_pdf, dpi=200)  # Higher DPI for card details
        total_pages = len(images)

        logger.info(f"Analyzing {total_pages} pages for ID card detection")

        # Detect ID cards
        id_cards = []

        for page_num, image in enumerate(images, start=1):
            result = self._classify_card_side(image)

            if result["is_id_card"]:
                id_cards.append({
                    "page": page_num,
                    "side": result["side"],
                    "card_type": result["card_type"],
                    "confidence": round(result["confidence"], 2),
                    "features": result["features"]
                })
                logger.info(
                    f"Page {page_num}: ID card detected - "
                    f"{result['side']} ({result['card_type']}) "
                    f"confidence: {result['confidence']:.2f}"
                )

        # Group consecutive recto/verso pairs
        groupings = []
        i = 0
        while i < len(id_cards):
            card = id_cards[i]

            # Check if next card is the opposite side
            if i + 1 < len(id_cards):
                next_card = id_cards[i + 1]

                if (card["side"] == "recto" and next_card["side"] == "verso") or \
                   (card["side"] == "verso" and next_card["side"] == "recto"):
                    groupings.append([card["page"], next_card["page"]])
                    i += 2
                    continue

            # Single card without pair
            groupings.append([card["page"]])
            i += 1

        # Calculate overall confidence
        if id_cards:
            overall_confidence = sum(c["confidence"] for c in id_cards) / len(id_cards)
        else:
            overall_confidence = 0.9  # High confidence that there are NO ID cards

        # Create hints message
        if id_cards:
            hints_message = f"ID cards detected: {', '.join([f'page {c['page']} ({c['side']})' for c in id_cards])}"
            if groupings:
                hints_message += f". Suggested groupings: {groupings}"
        else:
            hints_message = "No ID cards detected"

        logger.info(
            f"Detected {len(id_cards)} ID card pages out of {total_pages} "
            f"(confidence: {overall_confidence:.2f})"
        )

        return ToolResult(
            success=True,
            data={
                "id_cards": id_cards,
                "groupings": groupings,
                "total_pages": total_pages
            },
            hints={
                "id_cards": id_cards,
                "groupings": groupings,
                "message": hints_message
            },
            confidence=overall_confidence
        )


# Register tool with MCP server
def register(mcp_server):
    """Register detect_id_card_sides tool"""
    detector = IDCardDetector()

    @mcp_server.tool()
    async def detect_id_card_sides(presigned_url: str) -> Dict[str, Any]:
        """
        Detects ID card recto/verso sides in a PDF using computer vision.

        This tool uses aspect ratio analysis, corner detection, barcode detection,
        magnetic stripe detection, and hologram area detection to identify ID cards
        and determine which side (recto/verso) each page represents.

        Helps AI understand document structure by grouping recto/verso pairs.

        Args:
            presigned_url: MinIO presigned URL for the PDF to analyze

        Returns:
            {
                "success": true,
                "data": {
                    "id_cards": [
                        {"page": 1, "side": "recto", "card_type": "driving_license_qc", "confidence": 0.92},
                        {"page": 2, "side": "verso", "card_type": "driving_license_qc", "confidence": 0.88}
                    ],
                    "groupings": [[1, 2]],
                    "total_pages": 2
                },
                "hints": {
                    "id_cards": [...],
                    "groupings": [[1, 2]],
                    "message": "ID cards detected: page 1 (recto), page 2 (verso). Suggested groupings: [[1, 2]]"
                },
                "confidence": 0.90,
                "execution_time_ms": 52
            }

        Example usage:
            result = await detect_id_card_sides("https://minio/file.pdf?presigned=...")
            if result["hints"]["groupings"]:
                # Tell Gemini Flash to group these pages
                prompt += f"Pages {result['hints']['groupings']} are recto/verso pairs"
        """
        result = await detector.execute(presigned_url=presigned_url)
        return result.model_dump()
