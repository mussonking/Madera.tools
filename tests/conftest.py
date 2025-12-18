"""
MADERA MCP - Pytest Configuration & Fixtures
Shared fixtures for all test modules
"""
import pytest
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from io import BytesIO
import pypdf


# Set event loop policy for async tests
@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests"""
    return asyncio.get_event_loop_policy()


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for test files"""
    return tmp_path


@pytest.fixture
def create_test_pdf():
    """Factory fixture to create test PDFs"""
    def _create_pdf(pages: list, output_path: Path) -> Path:
        """
        Create a test PDF with specified pages

        Args:
            pages: List of PIL Images or "blank" for blank pages
            output_path: Where to save PDF

        Returns:
            Path to created PDF
        """
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import tempfile

        # Create temporary image files
        temp_images = []

        for i, page in enumerate(pages):
            if page == "blank":
                # Create blank page
                img = Image.new('RGB', (850, 1100), color='white')
            elif isinstance(page, str):
                # Create page with text
                img = Image.new('RGB', (850, 1100), color='white')
                draw = ImageDraw.Draw(img)
                try:
                    # Try to use a font
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
                except:
                    font = ImageFont.load_default()
                draw.text((50, 50), page, fill='black', font=font)
            else:
                # Use provided PIL Image
                img = page

            # Save to temp
            temp_file = Path(tempfile.gettempdir()) / f"test_page_{i}.png"
            img.save(temp_file)
            temp_images.append(temp_file)

        # Convert images to PDF using img2pdf
        import img2pdf

        with open(output_path, "wb") as f:
            f.write(img2pdf.convert([str(p) for p in temp_images]))

        # Cleanup temp images
        for temp_file in temp_images:
            temp_file.unlink()

        return output_path

    return _create_pdf


@pytest.fixture
def create_blank_image():
    """Create a blank white image"""
    def _create(width=850, height=1100, color='white'):
        return Image.new('RGB', (width, height), color=color)
    return _create


@pytest.fixture
def create_text_image():
    """Create an image with text"""
    def _create(text: str, width=850, height=1100):
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            font = ImageFont.load_default()
        draw.text((50, 50), text, fill='black', font=font)
        return img
    return _create


@pytest.fixture
def create_id_card_image():
    """Create a fake ID card image"""
    def _create(side='recto', width=856, height=540):  # Credit card aspect ratio
        img = Image.new('RGB', (width, height), color='lightblue')
        draw = ImageDraw.Draw(img)

        # Draw rounded corners (approximate)
        # Top-left corner
        draw.ellipse([0, 0, 40, 40], fill='white')
        # Top-right corner
        draw.ellipse([width-40, 0, width, 40], fill='white')
        # Bottom-left corner
        draw.ellipse([0, height-40, 40, height], fill='white')
        # Bottom-right corner
        draw.ellipse([width-40, height-40, width, height], fill='white')

        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()

        if side == 'recto':
            draw.text((50, 50), "DRIVER'S LICENSE", fill='black', font=font)
            draw.text((50, 100), "Quebec - SAAQ", fill='black', font=font)
            # Simulate hologram area (high variance)
            hologram_area = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            hologram_img = Image.fromarray(hologram_area)
            img.paste(hologram_img, (600, 50))
        else:  # verso
            draw.text((50, 50), "Restrictions: None", fill='black', font=font)
            # Simulate barcode
            for i in range(0, width, 4):
                if i % 8 == 0:
                    draw.rectangle([i, height-80, i+2, height-20], fill='black')
            # Simulate magnetic stripe
            draw.rectangle([0, height-100, width, height-90], fill='black')

        return img

    return _create


@pytest.fixture
def create_tax_form_image():
    """Create a fake tax form image"""
    def _create(form_type='T4', year=2024, width=850, height=1100):
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)

        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Form code in top-right
        draw.text((width - 150, 30), form_type, fill='black', font=font_large)

        # Year
        draw.text((width - 200, 120), str(year), fill='black', font=font_small)

        # Form title
        if form_type == 'T4':
            draw.text((50, 30), "Statement of Remuneration Paid", fill='black', font=font_small)
        elif form_type == 'T5':
            draw.text((50, 30), "Statement of Investment Income", fill='black', font=font_small)
        elif form_type == 'T1':
            draw.text((50, 30), "Income Tax and Benefit Return", fill='black', font=font_small)

        # Fake form boxes
        for i in range(5):
            y = 200 + i * 100
            draw.rectangle([50, y, width-50, y+80], outline='black', width=2)

        return img

    return _create


@pytest.fixture
def create_cra_document_image():
    """Create a fake CRA document image"""
    def _create(doc_type='notice_of_assessment', year=2024, width=850, height=1100):
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)

        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # CRA header
        draw.text((50, 20), "Canada Revenue Agency", fill='black', font=font_large)
        draw.text((50, 80), "Agence du revenu du Canada", fill='grey', font=font_small)

        # Document title
        if doc_type == 'notice_of_assessment':
            draw.text((50, 200), "NOTICE OF ASSESSMENT", fill='black', font=font_large)
            draw.text((50, 260), f"Tax Year {year}", fill='black', font=font_small)
        elif doc_type == 'family_allowance':
            draw.text((50, 200), "Canada Child Benefit", fill='black', font=font_large)
            draw.text((50, 260), "RC151", fill='black', font=font_small)

        return img

    return _create


@pytest.fixture
def mock_minio_url(create_test_pdf, temp_dir):
    """Create a test PDF and return a mock presigned URL"""
    async def _create(pages):
        pdf_path = temp_dir / "test.pdf"
        create_test_pdf(pages, pdf_path)
        # Return file:// URL for local testing
        return f"file://{pdf_path}"

    return _create


@pytest.fixture
def sample_pdf_3_pages(create_test_pdf, create_text_image, temp_dir):
    """Create a sample 3-page PDF"""
    pages = [
        create_text_image("Page 1 Content"),
        create_text_image("Page 2 Content"),
        create_text_image("Page 3 Content"),
    ]
    pdf_path = temp_dir / "sample_3_pages.pdf"
    return create_test_pdf(pages, pdf_path)


@pytest.fixture
def sample_pdf_with_blank(create_test_pdf, create_text_image, temp_dir):
    """Create a PDF with a blank page"""
    pages = [
        create_text_image("Page 1"),
        "blank",
        create_text_image("Page 3"),
    ]
    pdf_path = temp_dir / "sample_with_blank.pdf"
    return create_test_pdf(pages, pdf_path)


@pytest.fixture
def sample_pdf_id_cards(create_test_pdf, create_id_card_image, temp_dir):
    """Create a PDF with ID card images"""
    pages = [
        create_id_card_image('recto'),
        create_id_card_image('verso'),
    ]
    pdf_path = temp_dir / "sample_id_cards.pdf"
    return create_test_pdf(pages, pdf_path)


@pytest.fixture
def sample_pdf_tax_forms(create_test_pdf, create_tax_form_image, temp_dir):
    """Create a PDF with tax forms"""
    pages = [
        create_tax_form_image('T4', 2024),
        create_tax_form_image('T5', 2023),
    ]
    pdf_path = temp_dir / "sample_tax_forms.pdf"
    return create_test_pdf(pages, pdf_path)


# Async test support
@pytest.fixture
def anyio_backend():
    """Use asyncio as the async backend"""
    return 'asyncio'
