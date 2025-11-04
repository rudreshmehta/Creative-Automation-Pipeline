"""
Reporting module for campaign execution results
Summary: Generates execution logs and summary reports in JSON format
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from config import settings
from schemas.campaign import CampaignOutput

logger = logging.getLogger(__name__)


class Reporter:
    """Generates execution reports and logs"""

    def __init__(self):
        """
        Initialize reporter
        """
        self.reports_dir = settings.reports_dir
        self.reports_dir.mkdir(exist_ok=True)

    def generate_report(
        self,
        campaign_id: str,
        outputs: List[CampaignOutput],
        total_time: float,
        errors: List[str] = None
    ) -> Path:
        """
        Generate comprehensive campaign execution report
        Summary: Creates JSON report with execution statistics and results
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"campaign_{campaign_id}_{timestamp}.json"
            report_path = self.reports_dir / report_filename

            # Calculate statistics
            total_campaigns = len(outputs)
            assets_generated = sum(1 for o in outputs if o.asset_generated)
            assets_reused = total_campaigns - assets_generated
            compliance_passed = sum(1 for o in outputs if o.compliance_passed)
            compliance_failed = total_campaigns - compliance_passed
            total_legal_flags = sum(len(o.legal_flags) for o in outputs)

            # Group by product
            products = {}
            for output in outputs:
                if output.product_name not in products:
                    products[output.product_name] = []
                products[output.product_name].append({
                    "aspect_ratio": output.aspect_ratio,
                    "output_path": output.output_path,
                    "language": output.language,
                    "translated_message": output.translated_message,
                    "compliance_passed": output.compliance_passed,
                    "legal_flags": output.legal_flags,
                    "generation_time_seconds": output.generation_time_seconds
                })

            # Build report
            report = {
                "campaign_id": campaign_id,
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_campaigns_generated": total_campaigns,
                    "total_products": len(products),
                    "aspect_ratios": ["1:1", "9:16", "16:9"],
                    "assets_generated": assets_generated,
                    "assets_reused": assets_reused,
                    "compliance_passed": compliance_passed,
                    "compliance_failed": compliance_failed,
                    "total_legal_flags": total_legal_flags,
                    "total_execution_time_seconds": total_time,
                    "average_time_per_campaign": total_time / total_campaigns if total_campaigns > 0 else 0
                },
                "products": products,
                "errors": errors or []
            }

            # Write report to file
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            self._print_summary(report)

            return report_path

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise

    def _print_summary(self, report: Dict[str, Any]):
        """
        Print report summary to console
        Summary: Displays human-readable summary of execution results
        """
        summary = report["summary"]

        print("\n" + "="*60)
        print(f"CAMPAIGN EXECUTION REPORT: {report['campaign_id']}")
        print("="*60)
        print(f"Campaigns Generated:    {summary['total_campaigns_generated']}")
        print(f"Products:               {summary['total_products']}")
        print(f"Assets Generated:       {summary['assets_generated']}")
        print(f"Assets Reused:          {summary['assets_reused']}")
        print(f"Compliance Passed:      {summary['compliance_passed']}")
        print(f"Compliance Failed:      {summary['compliance_failed']}")
        print(f"Legal Flags:            {summary['total_legal_flags']}")
        print(f"Total Time:             {summary['total_execution_time_seconds']:.2f}s")
        print(f"Avg Time/Campaign:      {summary['average_time_per_campaign']:.2f}s")
        print("="*60)

        if report["errors"]:
            print(f"\n[WARN] ERRORS ({len(report['errors'])}):")
            for error in report["errors"]:
                print(f"  - {error}")

        campaign_id = report["campaign_id"]
        print(f"\nFull report: {self.reports_dir / f'campaign_{campaign_id}_*.json'}")
        print()

    def log_error(self, error_message: str):
        """
        Log error to file and logger
        Summary: Records errors for reporting
        """
        logger.error(error_message)
