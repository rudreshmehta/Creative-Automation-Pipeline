import logging
import json
import sys
import time
from pathlib import Path
from typing import List

from pydantic import ValidationError

from config import settings
from schemas.campaign import CampaignBrief, CampaignOutput
from modules.vertex_ai_service import VertexAIService
from modules.asset_manager import AssetManager
from modules.campaign_composer import CampaignComposer
from modules.brand_compliance import BrandComplianceChecker
from modules.legal_checker import LegalChecker
from modules.reporter import Reporter
from modules.dropbox_uploader import DropboxUploader


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('creative_automation.log')
    ]
)

# Disable verbose HTTP logging from Google SDK and Dropbox
logging.getLogger('google.auth').setLevel(logging.WARNING)
logging.getLogger('google.api_core').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('google.genai').setLevel(logging.WARNING)
logging.getLogger('google.api_core.bidi').setLevel(logging.WARNING)
logging.getLogger('google_auth_httplib2').setLevel(logging.WARNING)
logging.getLogger('dropbox').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class CreativeAutomationPipeline:
    def __init__(self):
        self.vertex_ai_service = VertexAIService()
        self.asset_manager = AssetManager(self.vertex_ai_service)
        self.campaign_composer = CampaignComposer(self.vertex_ai_service)
        self.compliance_checker = BrandComplianceChecker()
        self.legal_checker = LegalChecker()
        self.reporter = Reporter()
        self.dropbox_uploader = DropboxUploader()

    def run(self, campaign_brief_path: Path) -> bool:
        start_time = time.time()
        errors = []
        all_outputs: List[CampaignOutput] = []

        try:
            campaign_brief = self._load_campaign_brief(campaign_brief_path)
            logger.info(f"Campaign: {campaign_brief.campaign_id} | Products: {len(campaign_brief.products)} | Region: {campaign_brief.region}")

            legal_result = self.legal_checker.check_content(
                campaign_brief.campaign_message,
                campaign_brief.campaign_message
            )

            if legal_result.blocked:
                error_msg = f"Campaign blocked: {legal_result.details}"
                logger.error(error_msg)
                errors.append(error_msg)
                return False

            translated_message = self.vertex_ai_service.translate_message(
                message=campaign_brief.campaign_message,
                region=campaign_brief.region,
                target_audience=campaign_brief.target_audience
            )

            translated_legal_result = self.legal_checker.check_content(
                campaign_brief.campaign_message,
                translated_message
            )

            for product in campaign_brief.products:
                logger.info(f"Processing: {product.name}")

                try:
                    # Get or generate product asset
                    product_asset_path, asset_generated = self.asset_manager.get_or_create_asset(
                        product=product,
                        brand_theme=campaign_brief.brand.theme
                    )

                    if not product_asset_path:
                        error_msg = f"Failed to obtain asset for {product.name}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue

                    # Compose campaigns for all aspect ratios
                    campaign_outputs = self.campaign_composer.compose_campaigns(
                        campaign_id=campaign_brief.campaign_id,
                        product=product,
                        product_asset_path=product_asset_path,
                        brand=campaign_brief.brand,
                        original_message=campaign_brief.campaign_message,
                        translated_message=translated_message,
                        language=self._get_language_from_region(campaign_brief.region),
                        asset_was_generated=asset_generated
                    )

                    # Perform compliance and legal checks on generated campaigns
                    for campaign_output in campaign_outputs:
                        # Brand compliance check
                        compliance_result = self.compliance_checker.check_compliance(
                            campaign_asset_path=Path(campaign_output.output_path),
                            brand=campaign_brief.brand
                        )

                        campaign_output.compliance_passed = compliance_result.passed
                        campaign_output.legal_flags = translated_legal_result.prohibited_words_found

                        if not compliance_result.passed:
                            logger.warning(
                                f"COMPLIANCE FAILED | Product: {campaign_output.product_name} | "
                                f"Aspect: {campaign_output.aspect_ratio} | "
                                f"Violations: {', '.join(compliance_result.violations)}"
                            )

                    all_outputs.extend(campaign_outputs)

                    # Upload to Dropbox if enabled
                    if settings.dropbox_upload_enabled:
                        asset_paths = [Path(output.output_path) for output in campaign_outputs]
                        if product_asset_path.exists():
                            asset_paths.insert(0, product_asset_path)

                        self.dropbox_uploader.upload_campaign_assets(
                            campaign_id=campaign_brief.campaign_id,
                            product_name=product.name,
                            asset_paths=asset_paths
                        )

                except Exception as e:
                    error_msg = f"Error processing product {product.name}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
                    continue

            total_time = time.time() - start_time
            report_path = self.reporter.generate_report(
                campaign_id=campaign_brief.campaign_id,
                outputs=all_outputs,
                total_time=total_time,
                errors=errors
            )

            # Upload report to Dropbox if enabled
            if settings.dropbox_upload_enabled:
                self.dropbox_uploader.upload_report(
                    campaign_id=campaign_brief.campaign_id,
                    report_path=report_path
                )

            logger.info(f"Completed in {total_time:.2f}s | Assets: {len(all_outputs)} | Report: {report_path}")
            return len(errors) == 0

        except ValidationError as e:
            logger.error(f"Campaign brief validation failed: {e}")
            return False

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            return False

    def _load_campaign_brief(self, path: Path) -> CampaignBrief:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            campaign_brief = CampaignBrief(**data)
            return campaign_brief

        except FileNotFoundError:
            logger.error(f"Campaign brief file not found: {path}")
            raise

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in campaign brief: {e}")
            raise

        except ValidationError as e:
            logger.error(f"Campaign brief validation failed:\n{e}")
            raise

    def _get_language_from_region(self, region: str) -> str:
        language_map = {
            "quebec": "French",
            "france": "French",
            "mexico": "Spanish",
            "spain": "Spanish",
            "india": "Hindi",
            "japan": "Japanese",
            "china": "Chinese",
            "germany": "German",
            "brazil": "Portuguese"
        }

        return language_map.get(region.lower(), "English")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <campaign_brief.json>")
        print("Example: python main.py data/campaign_brief.json")
        sys.exit(1)

    campaign_brief_path = Path(sys.argv[1])

    if not campaign_brief_path.exists():
        logger.error(f"Campaign brief file not found: {campaign_brief_path}")
        sys.exit(1)

    pipeline = CreativeAutomationPipeline()
    success = pipeline.run(campaign_brief_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
