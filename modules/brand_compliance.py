"""
Brand compliance checker module
Summary: Validates campaign assets for logo presence and brand color usage
"""

import logging
from pathlib import Path
from typing import List
import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from schemas.campaign import Brand, ComplianceResult

logger = logging.getLogger(__name__)


class BrandComplianceChecker:
    """Checks campaign assets for brand compliance"""

    def __init__(self):
        """
        Initialize compliance checker
        """
        self.logo_match_threshold = 0.7
        self.color_presence_threshold = 0.001  # 0.1% of pixels

    def check_compliance(
        self,
        campaign_asset_path: Path,
        brand: Brand
    ) -> ComplianceResult:
        """
        Perform comprehensive brand compliance check
        Summary: Checks logo presence and brand color usage in campaign asset
        """
        violations = []

        try:
            # Check logo presence
            logo_detected, logo_confidence = self._detect_logo(
                campaign_asset_path,
                Path(brand.logo_path)
            )

            if not logo_detected:
                violations.append(f"Logo not detected (confidence: {logo_confidence:.2f})")

            # Check brand colors
            primary_present, primary_pct = self._check_color_presence(
                campaign_asset_path,
                brand.primary_color
            )

            secondary_present, secondary_pct = self._check_color_presence(
                campaign_asset_path,
                brand.secondary_color
            )

            if not primary_present:
                violations.append(
                    f"Primary color {brand.primary_color} not present "
                    f"({primary_pct*100:.1f}% < {self.color_presence_threshold*100}%)"
                )

            if not secondary_present:
                violations.append(
                    f"Secondary color {brand.secondary_color} not present "
                    f"({secondary_pct*100:.1f}% < {self.color_presence_threshold*100}%)"
                )

            passed = len(violations) == 0

            result = ComplianceResult(
                logo_detected=logo_detected,
                logo_confidence=logo_confidence,
                primary_color_present=primary_present,
                primary_color_percentage=primary_pct,
                secondary_color_present=secondary_present,
                secondary_color_percentage=secondary_pct,
                passed=passed,
                violations=violations
            )

            return result

        except Exception as e:
            logger.error(f"Compliance check error: {e}")
            return ComplianceResult(
                logo_detected=False,
                logo_confidence=0.0,
                primary_color_present=False,
                primary_color_percentage=0.0,
                secondary_color_present=False,
                secondary_color_percentage=0.0,
                passed=False,
                violations=[f"Compliance check failed: {str(e)}"]
            )

    def _detect_logo(
        self,
        campaign_asset_path: Path,
        logo_path: Path
    ) -> tuple[bool, float]:
        """
        Detect logo in campaign asset using template matching
        Summary: Uses OpenCV template matching to find logo
        """
        try:
            # Load images
            campaign_img = cv2.imread(str(campaign_asset_path))
            logo_img = cv2.imread(str(logo_path))

            if campaign_img is None or logo_img is None:
                logger.error("Failed to load images for logo detection")
                return False, 0.0

            # Convert to grayscale
            campaign_gray = cv2.cvtColor(campaign_img, cv2.COLOR_BGR2GRAY)
            logo_gray = cv2.cvtColor(logo_img, cv2.COLOR_BGR2GRAY)

            # Template matching
            result = cv2.matchTemplate(campaign_gray, logo_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            confidence = float(max_val)
            detected = confidence >= self.logo_match_threshold
            return detected, confidence

        except Exception as e:
            logger.error(f"Logo detection error: {e}")
            return False, 0.0

    def _check_color_presence(
        self,
        image_path: Path,
        hex_color: str
    ) -> tuple[bool, float]:
        """
        Check if brand color is present in image (checks shades before/after target color)
        """
        try:
            # Load image
            img = Image.open(image_path)
            img_array = np.array(img.convert('RGB'))
            pixels = img_array.reshape(-1, 3)

            # Convert hex to RGB
            target_rgb = self._hex_to_rgb(hex_color)

            # Generate color range: lighter and darker shades
            # Check 5 shades before (darker) and 5 after (lighter)
            shade_range = 5
            shade_step = 15  # RGB value step for each shade

            total_matching = 0

            for i in range(-shade_range, shade_range + 1):
                # Create shade variant
                shade_rgb = np.clip(target_rgb + (i * shade_step), 0, 255).astype(int)

                # Calculate color similarity for all pixels
                distances = np.sqrt(np.sum((pixels - shade_rgb) ** 2, axis=1))

                # Tolerance for matching (allow slight variations)
                color_tolerance = 40
                matching_pixels = np.sum(distances <= color_tolerance)
                total_matching += matching_pixels

            # Remove duplicates (same pixel counted multiple times)
            # Use a more lenient approach - just sum all matches
            total_pixels = len(pixels)

            # Calculate percentage (capped at 100%)
            percentage = min(total_matching / total_pixels, 1.0)
            present = percentage >= self.color_presence_threshold
            return present, percentage

        except Exception as e:
            logger.error(f"Color presence check error: {e}")
            return False, 0.0

    def _hex_to_rgb(self, hex_color: str) -> np.ndarray:
        """
        Convert hex color to RGB array
        Summary: Converts #RRGGBB to numpy array [R, G, B]
        """
        hex_color = hex_color.lstrip('#')
        return np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)])
