"""
Campaign composition module
Summary: Orchestrates campaign asset generation across multiple aspect ratios
"""

import logging
from pathlib import Path
from typing import List, Dict
import time

from config import settings
from schemas.campaign import Product, Brand, CampaignOutput
from modules.vertex_ai_service import VertexAIService as GeminiService

logger = logging.getLogger(__name__)


class CampaignComposer:
    """Composes campaign assets in multiple aspect ratios"""

    ASPECT_RATIOS = ["1:1", "9:16", "16:9"]

    def __init__(self, gemini_service: GeminiService):
        """
        Initialize campaign composer
        """
        self.gemini_service = gemini_service

    def compose_campaigns(
        self,
        campaign_id: str,
        product: Product,
        product_asset_path: Path,
        brand: Brand,
        original_message: str,
        translated_message: str,
        language: str,
        asset_was_generated: bool
    ) -> List[CampaignOutput]:
        """
        Generate campaign assets for all aspect ratios
        Summary: Creates 3 campaign variations (1:1, 9:16, 16:9) for single product
        """
        results = []

        # Create output directory for this product
        safe_product_name = "".join(c if c.isalnum() or c in "_ " else "_" for c in product.name)
        safe_product_name = safe_product_name.replace(" ", "_")

        output_dir = settings.output_dir / campaign_id / safe_product_name
        output_dir.mkdir(parents=True, exist_ok=True)

        brand_colors = {
            "primary": brand.primary_color,
            "secondary": brand.secondary_color
        }

        brand_logo_path = Path(brand.logo_path)

        for aspect_ratio in self.ASPECT_RATIOS:
            try:
                start_time = time.time()
                ratio_filename = aspect_ratio.replace(":", "x") + ".png"
                output_path = output_dir / ratio_filename

                logger.info(f"Generating: {product.name} | Aspect: {aspect_ratio} | Output: {ratio_filename}")

                success = self.gemini_service.compose_campaign_asset(
                    product_asset_path=product_asset_path,
                    brand_logo_path=brand_logo_path,
                    original_message=original_message,
                    translated_message=translated_message,
                    brand_colors=brand_colors,
                    brand_font=brand.font_name,
                    brand_domain=brand.domain,
                    aspect_ratio=aspect_ratio,
                    output_path=output_path,
                    product_description=product.description
                )

                generation_time = time.time() - start_time

                if success:
                    campaign_output = CampaignOutput(
                        campaign_id=campaign_id,
                        product_name=product.name,
                        aspect_ratio=aspect_ratio,
                        output_path=str(output_path),
                        language=language,
                        translated_message=translated_message,
                        asset_generated=asset_was_generated,
                        compliance_passed=False,
                        legal_flags=[],
                        generation_time_seconds=generation_time
                    )
                    results.append(campaign_output)
                else:
                    logger.error(f"Failed: {product.name} | Aspect: {aspect_ratio}")

            except Exception as e:
                logger.error(f"Composition error ({aspect_ratio}): {e}")
                continue

        return results
