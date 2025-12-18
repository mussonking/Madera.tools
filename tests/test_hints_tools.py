"""
MADERA MCP - HINTS Tools Tests
Comprehensive test suite for all 7 HINTS tools
"""
import pytest
import asyncio
from pathlib import Path
from PIL import Image
from madera.mcp.tools.hints.blank_page_detector import BlankPageDetector
from madera.mcp.tools.hints.id_card_detector import IDCardDetector
from madera.mcp.tools.hints.cra_doc_detector import CRADocumentDetector
from madera.mcp.tools.hints.tax_form_detector import TaxFormDetector
from madera.mcp.tools.hints.document_splitter import DocumentSplitter
from madera.mcp.tools.hints.fiscal_year_detector import FiscalYearDetector
from madera.mcp.tools.hints.quality_assessor import QualityAssessor


# ========================================
# TEST BLANK PAGE DETECTOR
# ========================================

@pytest.mark.asyncio
class TestBlankPageDetector:
    """Test suite for detect_blank_pages"""

    async def test_detect_no_blank_pages(self, sample_pdf_3_pages):
        """Test PDF with no blank pages"""
        detector = BlankPageDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_3_pages}")

        assert result.success is True
        assert result.data["blank_pages"] == []
        assert result.data["total_pages"] == 3
        assert result.confidence > 0.9

    async def test_detect_blank_page(self, sample_pdf_with_blank):
        """Test PDF with one blank page"""
        detector = BlankPageDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_with_blank}")

        assert result.success is True
        assert 2 in result.data["blank_pages"]  # Page 2 is blank
        assert result.data["total_pages"] == 3
        assert result.hints["message"] contains "Skip"

    async def test_execution_time(self, sample_pdf_3_pages):
        """Test execution time is within limits"""
        detector = BlankPageDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_3_pages}")

        # Should be ~50ms per page = ~150ms total
        assert result.execution_time_ms < 500  # Allow some overhead


# ========================================
# TEST ID CARD DETECTOR
# ========================================

@pytest.mark.asyncio
class TestIDCardDetector:
    """Test suite for detect_id_card_sides"""

    async def test_detect_id_cards(self, sample_pdf_id_cards):
        """Test detection of ID card recto/verso"""
        detector = IDCardDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_id_cards}")

        assert result.success is True
        assert len(result.data["id_cards"]) == 2
        assert result.data["id_cards"][0]["side"] == "recto"
        assert result.data["id_cards"][1]["side"] == "verso"
        assert result.data["groupings"] == [[1, 2]]

    async def test_no_id_cards(self, sample_pdf_3_pages):
        """Test PDF with no ID cards"""
        detector = IDCardDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_3_pages}")

        assert result.success is True
        assert len(result.data["id_cards"]) == 0

    async def test_aspect_ratio_detection(self, create_id_card_image):
        """Test aspect ratio detection"""
        detector = IDCardDetector()

        # Create card with correct aspect ratio
        card = create_id_card_image('recto')
        aspect = detector._calculate_aspect_ratio(card)

        # Should be ~1.58 (credit card ratio)
        assert 1.5 < aspect < 1.7


# ========================================
# TEST CRA DOCUMENT DETECTOR
# ========================================

@pytest.mark.asyncio
class TestCRADocumentDetector:
    """Test suite for identify_cra_document_type"""

    async def test_detect_notice_of_assessment(self, create_cra_document_image, create_test_pdf, temp_dir):
        """Test detection of Notice of Assessment"""
        noa_image = create_cra_document_image('notice_of_assessment', 2024)
        pdf_path = temp_dir / "noa.pdf"
        create_test_pdf([noa_image], pdf_path)

        detector = CRADocumentDetector()
        result = await detector.execute(presigned_url=f"file://{pdf_path}")

        assert result.success is True
        assert len(result.data["documents"]) == 1
        assert result.data["documents"][0]["type"] == "notice_of_assessment"
        assert result.data["documents"][0]["issuer"] == "cra"

    async def test_no_cra_documents(self, sample_pdf_3_pages):
        """Test PDF with no CRA documents"""
        detector = CRADocumentDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_3_pages}")

        assert result.success is True
        assert len(result.data["documents"]) == 0


# ========================================
# TEST TAX FORM DETECTOR
# ========================================

@pytest.mark.asyncio
class TestTaxFormDetector:
    """Test suite for detect_tax_form_type"""

    async def test_detect_t4_form(self, sample_pdf_tax_forms):
        """Test detection of T4 form"""
        detector = TaxFormDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_tax_forms}")

        assert result.success is True
        assert len(result.data["tax_forms"]) >= 1

        # Find T4
        t4_forms = [f for f in result.data["tax_forms"] if f["form_type"] == "T4"]
        assert len(t4_forms) == 1
        assert t4_forms[0]["year"] == 2024

    async def test_detect_multiple_form_types(self, sample_pdf_tax_forms):
        """Test detection of multiple form types"""
        detector = TaxFormDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_tax_forms}")

        assert result.success is True
        # Should detect both T4 and T5
        form_types = [f["form_type"] for f in result.data["tax_forms"]]
        assert "T4" in form_types
        assert "T5" in form_types


# ========================================
# TEST DOCUMENT SPLITTER
# ========================================

@pytest.mark.asyncio
class TestDocumentSplitter:
    """Test suite for detect_document_boundaries"""

    async def test_single_document(self, sample_pdf_3_pages):
        """Test PDF with single document"""
        splitter = DocumentSplitter()
        result = await splitter.execute(presigned_url=f"file://{sample_pdf_3_pages}")

        assert result.success is True
        assert result.data["split_points"] == [1]
        assert result.data["document_ranges"] == [[1, 3]]

    async def test_blank_page_boundary(self, sample_pdf_with_blank):
        """Test blank page as document boundary"""
        splitter = DocumentSplitter()
        result = await splitter.execute(presigned_url=f"file://{sample_pdf_with_blank}")

        assert result.success is True
        # Should detect split after blank page (page 2)
        assert 3 in result.data["split_points"]


# ========================================
# TEST FISCAL YEAR DETECTOR
# ========================================

@pytest.mark.asyncio
class TestFiscalYearDetector:
    """Test suite for detect_fiscal_year"""

    async def test_detect_year_in_tax_form(self, sample_pdf_tax_forms):
        """Test year detection in tax forms"""
        detector = FiscalYearDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_tax_forms}")

        assert result.success is True
        assert result.data["most_common_year"] in [2023, 2024]
        assert len(result.data["fiscal_years"]) >= 1

    async def test_year_validation(self):
        """Test year validation logic"""
        detector = FiscalYearDetector()

        # Valid years
        assert detector._validate_year(2024) is True
        assert detector._validate_year(2020) is True
        assert detector._validate_year(2025) is True

        # Invalid years
        assert detector._validate_year(2010) is False  # Too old
        assert detector._validate_year(2030) is False  # Too far future
        assert detector._validate_year(1999) is False


# ========================================
# TEST QUALITY ASSESSOR
# ========================================

@pytest.mark.asyncio
class TestQualityAssessor:
    """Test suite for assess_image_quality"""

    async def test_assess_good_quality(self, sample_pdf_3_pages):
        """Test assessment of good quality PDF"""
        assessor = QualityAssessor()
        result = await assessor.execute(presigned_url=f"file://{sample_pdf_3_pages}")

        assert result.success is True
        assert result.data["overall_quality"] in ["excellent", "good", "acceptable"]
        assert "pages" in result.data
        assert len(result.data["pages"]) == 3

    async def test_dpi_detection(self, create_text_image):
        """Test DPI detection"""
        assessor = QualityAssessor()

        # Create image with known DPI
        img = create_text_image("Test")
        img.info['dpi'] = (300, 300)

        dpi = assessor._detect_dpi(img)
        assert dpi == 300

    async def test_blur_detection(self, create_blank_image):
        """Test blur detection"""
        assessor = QualityAssessor()

        # Sharp image should have high variance
        sharp_img = create_blank_image()
        blur_score, quality = assessor._detect_blur(sharp_img)

        assert blur_score >= 0
        assert quality in ["excellent", "good", "acceptable", "poor", "very_poor"]


# ========================================
# INTEGRATION TESTS
# ========================================

@pytest.mark.asyncio
class TestToolIntegration:
    """Integration tests for tools working together"""

    async def test_all_tools_on_same_pdf(self, sample_pdf_tax_forms):
        """Test all tools can process the same PDF"""
        pdf_url = f"file://{sample_pdf_tax_forms}"

        # Run all tools
        blank_detector = BlankPageDetector()
        id_detector = IDCardDetector()
        cra_detector = CRADocumentDetector()
        tax_detector = TaxFormDetector()
        splitter = DocumentSplitter()
        year_detector = FiscalYearDetector()
        assessor = QualityAssessor()

        results = await asyncio.gather(
            blank_detector.execute(presigned_url=pdf_url),
            id_detector.execute(presigned_url=pdf_url),
            cra_detector.execute(presigned_url=pdf_url),
            tax_detector.execute(presigned_url=pdf_url),
            splitter.execute(presigned_url=pdf_url),
            year_detector.execute(presigned_url=pdf_url),
            assessor.execute(presigned_url=pdf_url),
        )

        # All should succeed
        for result in results:
            assert result.success is True

    async def test_parallel_execution_time(self, sample_pdf_3_pages):
        """Test that parallel execution is faster than sequential"""
        import time

        pdf_url = f"file://{sample_pdf_3_pages}"

        # Create all detectors
        detectors = [
            BlankPageDetector(),
            IDCardDetector(),
            QualityAssessor(),
        ]

        # Parallel execution
        start = time.time()
        await asyncio.gather(*[d.execute(presigned_url=pdf_url) for d in detectors])
        parallel_time = time.time() - start

        # Sequential execution
        start = time.time()
        for d in detectors:
            await d.execute(presigned_url=pdf_url)
        sequential_time = time.time() - start

        # Parallel should be significantly faster (at least 30% faster)
        assert parallel_time < sequential_time * 0.7


# ========================================
# ERROR HANDLING TESTS
# ========================================

@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and edge cases"""

    async def test_invalid_pdf_url(self):
        """Test handling of invalid PDF URL"""
        detector = BlankPageDetector()
        result = await detector.execute(presigned_url="file:///nonexistent.pdf")

        # Should gracefully fail
        assert result.success is False
        assert result.error is not None

    async def test_corrupted_pdf(self, temp_dir):
        """Test handling of corrupted PDF"""
        # Create corrupted PDF
        corrupted_path = temp_dir / "corrupted.pdf"
        with open(corrupted_path, 'wb') as f:
            f.write(b"This is not a valid PDF")

        detector = BlankPageDetector()
        result = await detector.execute(presigned_url=f"file://{corrupted_path}")

        # Should gracefully fail
        assert result.success is False

    async def test_empty_pdf(self, create_test_pdf, temp_dir):
        """Test handling of empty PDF"""
        # Create empty PDF (0 pages)
        empty_path = temp_dir / "empty.pdf"
        # Note: Some tools might not support 0-page PDFs
        # This tests graceful handling

        detector = BlankPageDetector()
        # Depending on implementation, this might succeed with 0 pages
        # or fail gracefully
        result = await detector.execute(presigned_url=f"file://{empty_path}")

        # Should either succeed with 0 pages or fail gracefully
        if result.success:
            assert result.data.get("total_pages", 0) == 0
        else:
            assert result.error is not None


# ========================================
# PERFORMANCE TESTS
# ========================================

@pytest.mark.asyncio
class TestPerformance:
    """Performance benchmark tests"""

    async def test_blank_detector_speed(self, sample_pdf_3_pages):
        """Test blank detector meets speed requirements (~50ms per page)"""
        detector = BlankPageDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_3_pages}")

        # 3 pages @ 50ms = 150ms, allow 2x overhead
        assert result.execution_time_ms < 300

    async def test_id_detector_speed(self, sample_pdf_id_cards):
        """Test ID detector meets speed requirements (~50ms per page)"""
        detector = IDCardDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_id_cards}")

        # 2 pages @ 50ms = 100ms, allow 2x overhead
        assert result.execution_time_ms < 200

    async def test_quality_assessor_speed(self, sample_pdf_3_pages):
        """Test quality assessor meets speed requirements (~100ms per page)"""
        assessor = QualityAssessor()
        result = await assessor.execute(presigned_url=f"file://{sample_pdf_3_pages}")

        # 3 pages @ 100ms = 300ms, allow 2x overhead
        assert result.execution_time_ms < 600


# ========================================
# CONFIDENCE SCORING TESTS
# ========================================

@pytest.mark.asyncio
class TestConfidenceScoring:
    """Test confidence scoring accuracy"""

    async def test_high_confidence_on_clear_result(self, sample_pdf_with_blank):
        """Test high confidence when result is clear"""
        detector = BlankPageDetector()
        result = await detector.execute(presigned_url=f"file://{sample_pdf_with_blank}")

        # Should have high confidence for blank page detection
        assert result.confidence > 0.7

    async def test_confidence_in_hints(self, sample_pdf_tax_forms):
        """Test all tools return confidence scores"""
        detectors = [
            BlankPageDetector(),
            IDCardDetector(),
            TaxFormDetector(),
        ]

        pdf_url = f"file://{sample_pdf_tax_forms}"

        for detector in detectors:
            result = await detector.execute(presigned_url=pdf_url)
            assert result.confidence is not None
            assert 0.0 <= result.confidence <= 1.0
