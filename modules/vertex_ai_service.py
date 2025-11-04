import logging
import time
import base64
from pathlib import Path
from typing import Dict
from io import BytesIO

from google import genai
from google.genai import types
from PIL import Image

from config import settings
from modules.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class VertexAIService:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=settings.gcp_project_id,
            location=settings.gcp_location
        )
        self.prompt_loader = PromptLoader()
        self._request_count = 0
        self._last_request_time = time.time()

    def _rate_limit(self):
        current_time = time.time()
        elapsed = current_time - self._last_request_time

        if self._request_count >= settings.imagen_rpm_limit:
            if elapsed < 60:
                sleep_time = 60 - elapsed
                logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = time.time()
            else:
                self._request_count = 0
                self._last_request_time = current_time

        self._request_count += 1

    def generate_product_asset(
        self,
        product_name: str,
        product_description: str,
        brand_theme: str,
        output_path: Path
    ) -> bool:
        try:
            self._rate_limit()

            prompt = self.prompt_loader.format(
                "product_image_generation",
                product_name=product_name,
                product_description=product_description,
                brand_theme=brand_theme
            )

            response = self.client.models.generate_images(
                model=settings.imagen_model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",
                    safety_filter_level="block_medium_and_above",
                    person_generation="allow_adult"
                )
            )

            if response.generated_images:
                image_base64 = response.generated_images[0].image.image_bytes
                image_bytes = base64.b64decode(image_base64)
                with open(str(output_path), 'wb') as f:
                    f.write(image_bytes)
                return True

            return False

        except Exception as e:
            logger.error(f"Error generating product asset: {e}")
            return False

    def translate_message(
        self,
        message: str,
        region: str,
        target_audience: str
    ) -> str:
        try:
            self._rate_limit()

            language_map = {
                "quebec": "French (Canadian)",
                "france": "French",
                "mexico": "Spanish (Mexican)",
                "spain": "Spanish",
                "india": "Hindi",
                "japan": "Japanese",
                "china": "Chinese (Simplified)",
                "germany": "German",
                "brazil": "Portuguese (Brazilian)"
            }

            target_language = language_map.get(region.lower(), "English")

            if target_language == "English":
                return message

            prompt = self.prompt_loader.format(
                "message_translation",
                target_language=target_language,
                region=region,
                target_audience=target_audience,
                message=message
            )

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=settings.gemini_text_model,
                        contents=prompt
                    )
                    return response.text.strip()
                except Exception as retry_error:
                    if "429" in str(retry_error) and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 10
                        time.sleep(wait_time)
                    else:
                        raise retry_error

        except Exception as e:
            logger.error(f"Translation error: {e}")
            return message

    def compose_campaign_asset(
        self,
        product_asset_path: Path,
        brand_logo_path: Path,
        original_message: str,
        translated_message: str,
        brand_colors: Dict[str, str],
        brand_font: str,
        brand_domain: str,
        aspect_ratio: str,
        output_path: Path,
        product_description: str = ""
    ) -> bool:
        try:
            self._rate_limit()

            prompt = self.prompt_loader.format(
                "campaign_composition",
                dimensions=aspect_ratio,
                original_message=original_message,
                translated_message=translated_message,
                brand_font=brand_font,
                primary_color=brand_colors['primary'],
                secondary_color=brand_colors['secondary'],
                brand_domain=brand_domain,
                product_description=product_description
            )

            product_image = Image.open(product_asset_path)

            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[product_image, prompt],
                config=types.GenerateContentConfig(
                    response_modalities=[types.Modality.IMAGE],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio)
                )
            )

            # Check if response was blocked or empty
            if not response.candidates:
                logger.error(f"Gemini 2.5 Flash Image returned no candidates - Content may be blocked by safety filters")
                logger.error(f"Prompt safety: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}")
                return False

            if not response.candidates[0].content.parts:
                logger.error(f"Gemini 2.5 Flash Image returned empty response - No image generated")
                logger.error(f"Finish reason: {response.candidates[0].finish_reason if hasattr(response.candidates[0], 'finish_reason') else 'N/A'}")
                return False

            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    edited = Image.open(BytesIO(base64.b64decode(part.inline_data.data)))
                    temp_path = output_path.parent / f"temp_{output_path.name}"
                    edited.save(str(temp_path))
                    self._add_logo_overlay(temp_path, brand_logo_path, output_path)
                    temp_path.unlink()
                    return True

            logger.error(f"Gemini 2.5 Flash Image response contained no inline_data")
            return False

        except Exception as e:
            logger.error(f"Error composing campaign asset: {e}")
            return False

    def _add_logo_overlay(self, campaign_image_path: Path, logo_path: Path, output_path: Path):
        try:
            campaign = Image.open(campaign_image_path).convert('RGBA')
            width, height = campaign.size
            logo = Image.open(logo_path).convert('RGBA')

            logo_max_width = int(width * 0.1)
            logo_ratio = logo_max_width / logo.width
            logo_height = int(logo.height * logo_ratio)
            logo = logo.resize((logo_max_width, logo_height), Image.Resampling.LANCZOS)

            padding = 20
            logo_position = (width - logo_max_width - padding, padding)

            logo_layer = Image.new('RGBA', campaign.size, (0, 0, 0, 0))
            logo_layer.paste(logo, logo_position, logo)

            final = Image.alpha_composite(campaign, logo_layer)

            if output_path.suffix.lower() in ['.jpg', '.jpeg']:
                final = final.convert('RGB')

            final.save(str(output_path))

        except Exception as e:
            logger.error(f"Error adding logo overlay: {e}")
            Image.open(campaign_image_path).save(str(output_path))
