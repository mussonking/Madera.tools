"""
MADERA Training Bot
AI-powered document analysis using Gemini Pro
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import google.generativeai as genai
from pdf2image import convert_from_path
import os

logger = logging.getLogger(__name__)

class TrainingBot:
    """AI Training Bot using configurable AI models"""

    def __init__(self, provider: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize Training Bot with specified or default AI model

        Args:
            provider: AI provider ("gemini", "claude", "openai") - reads from settings if not specified
            model_name: Exact model name - reads from settings if not specified
        """
        # Import settings here to avoid circular import
        try:
            from madera.web.routes.settings import current_settings
            self.provider = provider or current_settings.get("ai_provider", "gemini")
            self.model_name = model_name or current_settings.get("model_name", "gemini-2.5-pro")
        except ImportError:
            # Fallback if settings not available
            self.provider = provider or os.getenv("TRAINING_AI_PROVIDER", "gemini")
            self.model_name = model_name or "gemini-2.5-pro"

        # Configure based on provider
        if self.provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"TrainingBot initialized with Gemini: {self.model_name}")

        elif self.provider == "claude":
            # TODO: Implement Claude support
            raise NotImplementedError("Claude provider not yet implemented")

        elif self.provider == "openai":
            # TODO: Implement OpenAI support
            raise NotImplementedError("OpenAI provider not yet implemented")

        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")

    async def analyze_for_logo_detection(
        self,
        pdf_path: Path,
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze PDF for logo detection training

        Args:
            pdf_path: Path to PDF file
            document_type: Optional document type hint

        Returns:
            {
                "logos_detected": [
                    {
                        "name": "TD_CANADA_TRUST",
                        "confidence": 0.95,
                        "bounding_box": {"x": 50, "y": 30, "width": 200, "height": 80}
                    }
                ],
                "document_type": "bank_statement",
                "confidence": 0.92
            }
        """
        try:
            # Convert first page to image
            images = convert_from_path(str(pdf_path), first_page=1, last_page=1, dpi=200)

            if not images:
                return {"error": "Could not convert PDF to image"}

            image = images[0]

            # Prepare prompt
            prompt = f"""Analyze this document image and identify any logos, especially from Canadian institutions.

Focus on:
- Bank logos (TD, RBC, Scotiabank, BMO, CIBC, National Bank, Desjardins)
- Government logos (Canada Revenue Agency, Revenu Québec)
- Insurance logos
- Financial institution logos

For each logo found, provide:
1. Name of the institution
2. Confidence score (0-1)
3. Approximate bounding box coordinates (x, y, width, height) as percentage of image

Also identify the document type (bank_statement, tax_form, insurance_doc, etc.)

Return ONLY valid JSON format:
{{
    "logos_detected": [
        {{
            "name": "TD_CANADA_TRUST",
            "confidence": 0.95,
            "bounding_box": {{"x": 10, "y": 5, "width": 30, "height": 15}}
        }}
    ],
    "document_type": "bank_statement",
    "confidence": 0.92
}}
"""

            # Analyze with Gemini
            response = await self._analyze_with_gemini(image, prompt)

            return response

        except Exception as e:
            logger.error(f"Logo detection analysis failed: {e}")
            return {"error": str(e)}

    async def analyze_for_zone_extraction(
        self,
        pdf_path: Path,
        zone_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Analyze PDF for zone extraction training

        Args:
            pdf_path: Path to PDF file
            zone_type: Type of zones to extract (auto, dates, amounts, names)

        Returns:
            {
                "zones": [
                    {
                        "type": "date",
                        "label": "statement_date",
                        "value": "2024-12-16",
                        "bounding_box": {"x": 70, "y": 10, "width": 20, "height": 5}
                    }
                ],
                "confidence": 0.88
            }
        """
        try:
            # Convert first page to image
            images = convert_from_path(str(pdf_path), first_page=1, last_page=1, dpi=200)

            if not images:
                return {"error": "Could not convert PDF to image"}

            image = images[0]

            # Prepare prompt
            prompt = """Analyze this document and identify key data zones:

Extract zones for:
- Dates (statement date, due date, period dates)
- Amounts (totals, balances, payments)
- Names (account holder, business name)
- Addresses
- Account numbers
- Reference numbers

For each zone, provide:
1. Type (date, amount, name, address, account_number, reference)
2. Label (descriptive name like "statement_date", "total_balance")
3. Extracted value
4. Bounding box coordinates (x, y, width, height) as percentage of image

Return ONLY valid JSON:
{
    "zones": [
        {
            "type": "date",
            "label": "statement_date",
            "value": "2024-12-16",
            "bounding_box": {"x": 70, "y": 10, "width": 20, "height": 5}
        }
    ],
    "confidence": 0.88
}
"""

            # Analyze with Gemini
            response = await self._analyze_with_gemini(image, prompt)

            return response

        except Exception as e:
            logger.error(f"Zone extraction analysis failed: {e}")
            return {"error": str(e)}

    async def _analyze_with_gemini(self, image, prompt: str) -> Dict[str, Any]:
        """
        Call Gemini API with image and prompt

        Args:
            image: PIL Image object
            prompt: Analysis prompt

        Returns:
            Parsed JSON response
        """
        import json

        try:
            # Generate response
            response = self.model.generate_content([prompt, image])

            # Parse JSON from response
            text = response.text.strip()

            # Extract JSON if wrapped in code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            result = json.loads(text)

            logger.info(f"Gemini analysis successful - confidence: {result.get('confidence', 0)}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Raw response: {text}")
            return {"error": "Invalid JSON response from AI"}

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return {"error": str(e)}
