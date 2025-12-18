"""
MADERA MCP - Gemini Agent
Uses Google Gemini for training analysis
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import json
import google.generativeai as genai
from PIL import Image

from madera.config import settings
from madera.core.vision import convert_pdf_to_images

logger = logging.getLogger(__name__)


class GeminiAgent:
    """Gemini-powered training agent"""

    def __init__(self):
        """Initialize Gemini agent"""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")

        genai.configure(api_key=settings.GEMINI_API_KEY)

        # Use Gemini 2.0 Flash Thinking for training (fast + reasoning)
        self.model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-1219")

        logger.info("Gemini agent initialized")

    async def analyze_logos(
        self,
        pdf_path: Path,
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze PDF for logo detection

        Args:
            pdf_path: Path to PDF
            document_type: Optional document type hint

        Returns:
            Analysis results with detected logos and zones
        """
        # Convert PDF to images
        images = convert_pdf_to_images(pdf_path, dpi=200)

        # Prepare prompt
        prompt = self._get_logo_detection_prompt(document_type)

        # Analyze first page (logos usually on page 1)
        image = images[0] if images else None

        if not image:
            return {"logos_detected": [], "error": "No pages in PDF"}

        try:
            # Call Gemini with image
            response = await self._call_gemini(prompt, image)

            # Parse response
            result = self._parse_logo_response(response)

            return result

        except Exception as e:
            logger.error(f"Gemini logo analysis failed: {e}")
            return {"logos_detected": [], "error": str(e)}

    async def analyze_zones(
        self,
        pdf_path: Path,
        field_type: str
    ) -> Dict[str, Any]:
        """
        Analyze PDF for zone extraction

        Args:
            pdf_path: Path to PDF
            field_type: Field type to extract

        Returns:
            Analysis results with detected zones
        """
        # Convert PDF to images
        images = convert_pdf_to_images(pdf_path, dpi=200)

        prompt = self._get_zone_extraction_prompt(field_type)

        image = images[0] if images else None

        if not image:
            return {"zones_detected": [], "error": "No pages in PDF"}

        try:
            response = await self._call_gemini(prompt, image)
            result = self._parse_zone_response(response)

            return result

        except Exception as e:
            logger.error(f"Gemini zone analysis failed: {e}")
            return {"zones_detected": [], "error": str(e)}

    async def validate_template(
        self,
        pdf_path: Path,
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate template against PDF

        Args:
            pdf_path: Path to PDF
            template: Template to validate

        Returns:
            Validation results
        """
        images = convert_pdf_to_images(pdf_path, dpi=200)

        prompt = self._get_validation_prompt(template)

        image = images[0] if images else None

        if not image:
            return {"valid": False, "error": "No pages in PDF"}

        try:
            response = await self._call_gemini(prompt, image)
            result = self._parse_validation_response(response)

            return result

        except Exception as e:
            logger.error(f"Gemini validation failed: {e}")
            return {"valid": False, "error": str(e)}

    async def _call_gemini(self, prompt: str, image: Image.Image) -> str:
        """
        Call Gemini API with prompt and image

        Args:
            prompt: Text prompt
            image: PIL Image

        Returns:
            Model response text
        """
        # Gemini expects images in specific format
        response = self.model.generate_content(
            [prompt, image],
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,  # Low temperature for consistency
                response_mime_type="application/json",  # Request JSON response
            )
        )

        return response.text

    def _get_logo_detection_prompt(self, document_type: Optional[str] = None) -> str:
        """Generate prompt for logo detection"""
        base_prompt = """
Analyze this document image and detect logos/branding elements.

For each logo detected, provide:
1. logo_name: Name of the organization (e.g., "SAAQ", "TD Canada Trust", "Revenu Québec")
2. document_type: Type of document (e.g., "permis_conduire", "releve_bancaire", "avis_cotisation")
3. confidence: Confidence score 0.0-1.0
4. zone: Bounding box coordinates {x, y, width, height} in pixels from top-left

Return ONLY valid JSON in this format:
{
  "logos_detected": [
    {
      "logo_name": "SAAQ",
      "document_type": "permis_conduire",
      "confidence": 0.94,
      "zone": {"x": 50, "y": 30, "width": 200, "height": 80}
    }
  ],
  "suggestions": ["suggestion1", "suggestion2"]
}
"""

        if document_type:
            base_prompt += f"\n\nExpected document type: {document_type}"

        return base_prompt

    def _get_zone_extraction_prompt(self, field_type: str) -> str:
        """Generate prompt for zone extraction"""
        return f"""
Analyze this document and locate the zone for: {field_type}

Provide the bounding box coordinates for where this field is located.

Return ONLY valid JSON in this format:
{{
  "zones_detected": [
    {{
      "field_type": "{field_type}",
      "zone": {{"x": 100, "y": 200, "width": 300, "height": 40}},
      "confidence": 0.88
    }}
  ],
  "suggestions": []
}}
"""

    def _get_validation_prompt(self, template: Dict[str, Any]) -> str:
        """Generate prompt for template validation"""
        return f"""
Validate if this document matches the provided template.

Template: {json.dumps(template, indent=2)}

Check if:
1. The logo is in the expected zone
2. The document type matches
3. The template coordinates are accurate

Return ONLY valid JSON in this format:
{{
  "valid": true,
  "confidence": 0.92,
  "issues": [],
  "suggestions": ["suggestion1"]
}}
"""

    def _parse_logo_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response for logo detection"""
        try:
            # Gemini should return JSON directly
            result = json.loads(response)

            # Validate structure
            if "logos_detected" not in result:
                result["logos_detected"] = []

            if "suggestions" not in result:
                result["suggestions"] = []

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.debug(f"Response: {response}")
            return {
                "logos_detected": [],
                "suggestions": [],
                "error": "Failed to parse response"
            }

    def _parse_zone_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response for zone extraction"""
        try:
            result = json.loads(response)

            if "zones_detected" not in result:
                result["zones_detected"] = []

            if "suggestions" not in result:
                result["suggestions"] = []

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return {
                "zones_detected": [],
                "suggestions": [],
                "error": "Failed to parse response"
            }

    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response for validation"""
        try:
            result = json.loads(response)

            # Ensure required fields
            if "valid" not in result:
                result["valid"] = False

            if "confidence" not in result:
                result["confidence"] = 0.0

            if "issues" not in result:
                result["issues"] = []

            if "suggestions" not in result:
                result["suggestions"] = []

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return {
                "valid": False,
                "confidence": 0.0,
                "issues": ["Failed to parse validation"],
                "suggestions": []
            }
