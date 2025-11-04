import logging
from pathlib import Path
from typing import Optional

from config import settings
from schemas.campaign import Product
from modules.vertex_ai_service import VertexAIService as GeminiService

logger = logging.getLogger(__name__)


class AssetManager:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
        self.products_dir = settings.assets_dir / "products"
        self.products_dir.mkdir(exist_ok=True)

    def get_or_create_asset(
        self,
        product: Product,
        brand_theme: str
    ) -> tuple[Optional[Path], bool]:
        try:
            if product.asset_path:
                asset_path = settings.assets_dir / product.asset_path
                if asset_path.exists():
                    return asset_path, False

            safe_name = "".join(c if c.isalnum() or c in "_ " else "_" for c in product.name)
            safe_name = safe_name.replace(" ", "_").lower()
            output_path = self.products_dir / f"{safe_name}.png"

            if output_path.exists():
                return output_path, False

            success = self.gemini_service.generate_product_asset(
                product_name=product.name,
                product_description=product.description,
                brand_theme=brand_theme,
                output_path=output_path
            )

            if success:
                return output_path, True

            logger.error(f"Failed to generate asset: {product.name}")
            return None, False

        except Exception as e:
            logger.error(f"Asset error: {e}")
            return None, False