"""
MADERA MCP - detect_document_boundaries
HINTS Tool - Detects where to split a multi-document PDF

Execution time: ~150ms total
Technique: Blank page detection + layout changes + page numbering patterns
"""
from typing import Dict, Any, List, Tuple, Optional
from madera.mcp.tools.base import BaseTool, ToolResult
from madera.core.vision import convert_pdf_to_images, is_image_blank
from PIL import Image
import numpy as np
import cv2
import pytesseract
import re
import logging

logger = logging.getLogger(__name__)


class DocumentSplitter(BaseTool):
    """Detects document boundaries in multi-document PDFs"""

    def __init__(self):
        super().__init__()
        self.tool_class = "all_around"

    def _calculate_layout_hash(self, image: Image.Image) -> str:
        """
        Calculate a simple layout signature for comparison

        Returns:
            Hash string representing layout structure
        """
        # Convert to grayscale
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Resize to small size for faster comparison
        small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)

        # Edge detection
        edges = cv2.Canny(small, 50, 150)

        # Create simple hash from edge patterns
        # Divide into quadrants and count edges
        h, w = edges.shape
        quadrants = [
            edges[0:h//2, 0:w//2],           # Top-left
            edges[0:h//2, w//2:],             # Top-right
            edges[h//2:, 0:w//2],             # Bottom-left
            edges[h//2:, w//2:],              # Bottom-right
        ]

        edge_counts = [np.sum(q > 0) for q in quadrants]

        # Create simple hash
        layout_hash = "-".join([str(int(c / 10)) for c in edge_counts])

        return layout_hash

    def _detect_page_number(self, image: Image.Image) -> Tuple[Optional[int], Optional[int]]:
        """
        Detect "Page X of Y" pattern

        Returns:
            (current_page, total_pages) or (None, None)
        """
        width, height = image.size

        # Check bottom 10% of page (common location for page numbers)
        footer_zone = (0, int(height * 0.90), width, int(height * 0.1))

        x, y, w, h = footer_zone
        cropped = image.crop((x, y, x + w, y + h))

        try:
            text = pytesseract.image_to_string(cropped, config='--psm 6').lower()

            # Look for "page X of Y" patterns
            patterns = [
                r'page\s+(\d+)\s+of\s+(\d+)',
                r'page\s+(\d+)\s*/\s*(\d+)',
                r'(\d+)\s+of\s+(\d+)',
                r'(\d+)\s*/\s*(\d+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    return current, total

            return None, None

        except Exception as e:
            logger.warning(f"Page number detection failed: {e}")
            return None, None

    def _detect_header_footer_change(self, image1: Image.Image, image2: Image.Image) -> Tuple[bool, float]:
        """
        Detect if header/footer changed significantly between pages

        Returns:
            (changed, similarity)
        """
        width1, height1 = image1.size
        width2, height2 = image2.size

        # Check header (top 10%)
        header1 = image1.crop((0, 0, width1, int(height1 * 0.1)))
        header2 = image2.crop((0, 0, width2, int(height2 * 0.1)))

        # Check footer (bottom 10%)
        footer1 = image1.crop((0, int(height1 * 0.9), width1, int(height1 * 0.1)))
        footer2 = image2.crop((0, int(height2 * 0.9), width2, int(height2 * 0.1)))

        # Convert to numpy arrays and resize to same size
        def image_similarity(img1, img2):
            arr1 = np.array(img1.resize((100, 100)))
            arr2 = np.array(img2.resize((100, 100)))

            if len(arr1.shape) == 3:
                arr1 = cv2.cvtColor(arr1, cv2.COLOR_RGB2GRAY)
            if len(arr2.shape) == 3:
                arr2 = cv2.cvtColor(arr2, cv2.COLOR_RGB2GRAY)

            # Calculate MSE
            mse = np.mean((arr1.astype(float) - arr2.astype(float)) ** 2)

            # Convert to similarity score (0-1)
            similarity = 1.0 / (1.0 + mse / 1000.0)

            return similarity

        header_similarity = image_similarity(header1, header2)
        footer_similarity = image_similarity(footer1, footer2)

        avg_similarity = (header_similarity + footer_similarity) / 2.0

        # Changed if similarity is low
        changed = avg_similarity < 0.6

        return changed, avg_similarity

    def _analyze_document_boundaries(self, images: List[Image.Image]) -> List[Dict[str, Any]]:
        """
        Analyze all pages and detect document boundaries

        Returns:
            List of boundary indicators with confidence scores
        """
        boundaries = []

        for i in range(len(images)):
            page_num = i + 1
            image = images[i]

            # Check if blank page (strong boundary indicator)
            is_blank, blank_confidence = is_image_blank(image)

            # Calculate layout hash
            layout_hash = self._calculate_layout_hash(image)

            # Detect page numbering
            current_page, total_pages = self._detect_page_number(image)

            # Check for header/footer changes (if not first page)
            if i > 0:
                header_changed, header_similarity = self._detect_header_footer_change(
                    images[i - 1], image
                )
            else:
                header_changed = False
                header_similarity = 1.0

            # Detect "Page 1 of X" pattern (indicates start of new document)
            is_page_one = current_page == 1 if current_page else False

            boundaries.append({
                "page": page_num,
                "is_blank": is_blank,
                "blank_confidence": blank_confidence,
                "layout_hash": layout_hash,
                "page_numbering": (current_page, total_pages),
                "is_page_one": is_page_one,
                "header_changed": header_changed,
                "header_similarity": header_similarity,
            })

        return boundaries

    def _identify_split_points(self, boundaries: List[Dict[str, Any]]) -> List[Tuple[int, float, str]]:
        """
        Identify likely split points between documents

        Returns:
            List of (page_num, confidence, reason)
        """
        split_points = []

        for i, boundary in enumerate(boundaries):
            page_num = boundary["page"]
            reasons = []
            confidence_factors = []

            # Reason 1: Blank page (previous page is end, next page is start)
            if boundary["is_blank"]:
                if i + 1 < len(boundaries):  # Next page exists
                    split_points.append((
                        page_num + 1,  # Split AFTER blank page
                        0.85,
                        f"blank_page_{page_num}"
                    ))
                    continue  # Don't check other reasons for blank pages

            # Reason 2: "Page 1 of X" detected
            if boundary["is_page_one"]:
                reasons.append("page_one_detected")
                confidence_factors.append(0.80)

            # Reason 3: Header/footer changed significantly
            if boundary["header_changed"]:
                reasons.append("header_change")
                confidence_factors.append(0.70)

            # Reason 4: Layout changed significantly
            if i > 0:
                prev_hash = boundaries[i - 1]["layout_hash"]
                curr_hash = boundary["layout_hash"]

                if prev_hash != curr_hash:
                    # Calculate similarity
                    prev_parts = [int(x) for x in prev_hash.split("-")]
                    curr_parts = [int(x) for x in curr_hash.split("-")]

                    differences = sum(abs(a - b) for a, b in zip(prev_parts, curr_parts))

                    if differences > 10:  # Significant layout change
                        reasons.append("layout_change")
                        confidence_factors.append(0.60)

            # If we have multiple indicators, this is a strong split point
            if confidence_factors:
                combined_confidence = min(sum(confidence_factors) / len(confidence_factors), 0.95)
                combined_reasons = ",".join(reasons)

                split_points.append((page_num, combined_confidence, combined_reasons))

        return split_points

    async def _execute(self, presigned_url: str) -> ToolResult:
        """
        Detect document boundaries in a PDF

        Args:
            presigned_url: MinIO presigned URL for PDF

        Returns:
            ToolResult with hints: {
                "split_points": [1, 5, 9],  # Pages where new documents start
                "document_ranges": [[1, 4], [5, 8], [9, 12]],
                "confidences": {1: 0.95, 5: 0.88, 9: 0.90},
                "total_pages": 12
            }
        """
        # Download PDF
        local_pdf = await self.fetch_file(presigned_url)

        # Convert to images
        images = convert_pdf_to_images(local_pdf, dpi=150)
        total_pages = len(images)

        logger.info(f"Analyzing {total_pages} pages for document boundaries")

        # Analyze boundaries
        boundaries = self._analyze_document_boundaries(images)

        # Identify split points
        raw_split_points = self._identify_split_points(boundaries)

        # Format results
        split_points = [1]  # First page always starts a document
        confidences = {1: 1.0}
        reasons = {1: "first_page"}

        for page_num, confidence, reason in raw_split_points:
            if page_num not in split_points:
                split_points.append(page_num)
                confidences[page_num] = confidence
                reasons[page_num] = reason

        split_points.sort()

        # Create document ranges
        document_ranges = []
        for i in range(len(split_points)):
            start = split_points[i]
            end = split_points[i + 1] - 1 if i + 1 < len(split_points) else total_pages
            document_ranges.append([start, end])

        # Calculate overall confidence
        if len(split_points) > 1:
            overall_confidence = sum(confidences.values()) / len(confidences)
        else:
            overall_confidence = 0.90  # Single document, high confidence

        # Create hints message
        if len(document_ranges) > 1:
            hints_message = f"Multiple documents detected: {len(document_ranges)} documents. " + \
                           f"Split at pages: {split_points[1:]}"
        else:
            hints_message = "Single document (no splits needed)"

        logger.info(
            f"Detected {len(document_ranges)} documents in {total_pages} pages "
            f"(confidence: {overall_confidence:.2f})"
        )

        return ToolResult(
            success=True,
            data={
                "split_points": split_points,
                "document_ranges": document_ranges,
                "confidences": confidences,
                "reasons": reasons,
                "total_pages": total_pages
            },
            hints={
                "split_points": split_points,
                "document_ranges": document_ranges,
                "message": hints_message
            },
            confidence=overall_confidence
        )


# Register tool with MCP server
def register(mcp_server):
    """Register detect_document_boundaries tool"""
    splitter = DocumentSplitter()

    @mcp_server.tool()
    async def detect_document_boundaries(presigned_url: str) -> Dict[str, Any]:
        """
        Detects document boundaries in multi-document PDFs.

        This tool analyzes page patterns to identify where one document ends
        and another begins. Uses blank page detection, layout change analysis,
        header/footer comparison, and page numbering patterns.

        Helps AI understand document structure by grouping related pages.

        Args:
            presigned_url: MinIO presigned URL for the PDF to analyze

        Returns:
            {
                "success": true,
                "data": {
                    "split_points": [1, 5, 9],
                    "document_ranges": [[1, 4], [5, 8], [9, 12]],
                    "confidences": {1: 1.0, 5: 0.88, 9: 0.90},
                    "reasons": {1: "first_page", 5: "blank_page_4,page_one_detected", 9: "header_change"},
                    "total_pages": 12
                },
                "hints": {
                    "split_points": [1, 5, 9],
                    "document_ranges": [[1, 4], [5, 8], [9, 12]],
                    "message": "Multiple documents detected: 3 documents. Split at pages: [5, 9]"
                },
                "confidence": 0.93,
                "execution_time_ms": 147
            }

        Detection methods:
            - Blank pages: Strong indicator of document separation
            - "Page 1 of X": Indicates start of new document
            - Header/footer changes: Different headers suggest different documents
            - Layout changes: Significant layout shifts suggest new document

        Example usage:
            result = await detect_document_boundaries("https://minio/file.pdf?presigned=...")
            if len(result["hints"]["document_ranges"]) > 1:
                for i, range in enumerate(result["hints"]["document_ranges"], 1):
                    prompt += f"Document {i}: pages {range[0]}-{range[1]}"
        """
        result = await splitter.execute(presigned_url=presigned_url)
        return result.model_dump()
