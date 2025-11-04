"""
Legal content checker module
Summary: Scans campaign messages for prohibited words and legal violations
"""

import logging
import json
from pathlib import Path
from typing import List, Dict

from schemas.campaign import LegalCheckResult

logger = logging.getLogger(__name__)


class LegalChecker:
    """Checks campaign content for legal compliance"""

    def __init__(self, prohibited_words_path: Path = Path("data/prohibited_words.json")):
        """
        Initialize legal checker with prohibited words dictionary
        """
        self.prohibited_words = self._load_prohibited_words(prohibited_words_path)

    def _load_prohibited_words(self, path: Path) -> Dict:
        """
        Load prohibited words from JSON file
        Summary: Reads prohibited words configuration
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load prohibited words: {e}")
            return {}

    def check_content(self, message: str, translated_message: str) -> LegalCheckResult:
        """
        Check campaign message for legal violations
        Summary: Scans both original and translated messages for prohibited terms
        """
        try:
            all_violations = []
            highest_severity = "NONE"

            # Check both original and translated messages
            messages = [
                ("original", message),
                ("translated", translated_message)
            ]

            for msg_type, msg_text in messages:
                msg_lower = msg_text.lower()

                for category, config in self.prohibited_words.items():
                    severity = config.get("severity", "WARNING")
                    words = config.get("words", [])

                    for word in words:
                        if word.lower() in msg_lower:
                            violation = f"[{severity}] {category}: '{word}' in {msg_type} message"
                            all_violations.append(violation)
                            logger.warning(violation)

                            # Update highest severity
                            if severity == "ERROR":
                                highest_severity = "ERROR"
                            elif severity == "WARNING" and highest_severity == "NONE":
                                highest_severity = "WARNING"

            # Determine if content should be blocked
            blocked = highest_severity == "ERROR"

            if all_violations:
                details = f"Found {len(all_violations)} legal issue(s)"
            else:
                details = "No legal issues detected"

            result = LegalCheckResult(
                prohibited_words_found=[v for v in all_violations],
                severity=highest_severity,
                blocked=blocked,
                details=details
            )

            if blocked:
                logger.error(f"[FAIL] Legal check BLOCKED: {details}")
            elif all_violations:
                logger.warning(f"[WARN] Legal warnings: {len(all_violations)} issue(s)")

            return result

        except Exception as e:
            logger.error(f"Legal check error: {e}")
            return LegalCheckResult(
                prohibited_words_found=[],
                severity="NONE",
                blocked=False,
                details=f"Legal check failed: {str(e)}"
            )

    def add_custom_prohibited_word(
        self,
        category: str,
        word: str,
        severity: str = "WARNING"
    ):
        """
        Add custom prohibited word at runtime
        Summary: Allows dynamic addition of prohibited terms
        """
        if category not in self.prohibited_words:
            self.prohibited_words[category] = {
                "severity": severity,
                "words": []
            }

        if word not in self.prohibited_words[category]["words"]:
            self.prohibited_words[category]["words"].append(word)
