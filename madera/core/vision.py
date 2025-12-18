"""
MADERA MCP - Vision Utilities
PDF to image conversion and basic image analysis
"""
from pdf2image import convert_from_path
from PIL import Image
import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)


def convert_pdf_to_images(pdf_path: str, dpi: int = 200) -> List[Image.Image]:
    """
    Convert PDF to list of PIL images

    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for conversion (default 200 for speed)

    Returns:
        List of PIL Image objects (one per page)
    """
    logger.debug(f"Converting PDF to images: {pdf_path} at {dpi} DPI")

    images = convert_from_path(pdf_path, dpi=dpi)

    logger.info(f"Converted PDF to {len(images)} images")
    return images


def calculate_pixel_variance(image: Image.Image) -> float:
    """
    Calculate pixel variance for blank page detection

    Low variance = likely blank page

    Args:
        image: PIL Image

    Returns:
        Variance value (0-100+)
    """
    # Convert to grayscale numpy array
    grayscale = image.convert('L')
    pixels = np.array(grayscale)

    # Calculate variance
    variance = np.var(pixels)

    return float(variance)


def estimate_text_density(image: Image.Image, sample_regions: int = 9) -> float:
    """
    Estimate text density by sampling image regions

    Args:
        image: PIL Image
        sample_regions: Number of regions to sample (3x3 grid)

    Returns:
        Density score 0.0-1.0 (higher = more content)
    """
    grayscale = image.convert('L')
    width, height = grayscale.size

    # Sample 3x3 grid
    grid_size = int(np.sqrt(sample_regions))
    cell_width = width // grid_size
    cell_height = height // grid_size

    non_white_scores = []

    for row in range(grid_size):
        for col in range(grid_size):
            # Extract cell
            left = col * cell_width
            top = row * cell_height
            right = left + cell_width
            bottom = top + cell_height

            cell = grayscale.crop((left, top, right, bottom))
            pixels = np.array(cell)

            # Calculate % of non-white pixels (< 240)
            non_white = np.sum(pixels < 240) / pixels.size
            non_white_scores.append(non_white)

    # Average density
    density = np.mean(non_white_scores)

    return float(density)


def is_image_blank(
    image: Image.Image,
    variance_threshold: float = 100.0,
    density_threshold: float = 0.02
) -> tuple[bool, float]:
    """
    Determine if image is blank using combined heuristics

    Args:
        image: PIL Image
        variance_threshold: Max variance for blank (lower = more blank)
        density_threshold: Max text density for blank

    Returns:
        (is_blank: bool, confidence: float)
    """
    variance = calculate_pixel_variance(image)
    density = estimate_text_density(image)

    # Decision logic
    is_blank = variance < variance_threshold and density < density_threshold

    # Calculate confidence based on how far from thresholds
    if is_blank:
        # Confidence increases as variance/density decrease
        variance_conf = 1.0 - (variance / variance_threshold)
        density_conf = 1.0 - (density / density_threshold)
        confidence = (variance_conf + density_conf) / 2
    else:
        # Confidence increases as variance/density increase
        variance_conf = min(1.0, (variance - variance_threshold) / variance_threshold)
        density_conf = min(1.0, (density - density_threshold) / density_threshold)
        confidence = (variance_conf + density_conf) / 2

    # Clamp confidence to 0.5-1.0 range
    confidence = max(0.5, min(1.0, confidence))

    logger.debug(
        f"Blank detection: variance={variance:.1f}, density={density:.3f}, "
        f"blank={is_blank}, confidence={confidence:.2f}"
    )

    return is_blank, confidence
