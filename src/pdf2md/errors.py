"""Error handling classes and exit code mapping for pdf2md.

This module defines the error taxonomy and exit code mapping according to PRD Section 15.
All fatal errors should inherit from the appropriate base exception to ensure proper
exit code handling in the CLI.
"""

from __future__ import annotations

import sys
from typing import Any


class Pdf2MdError(Exception):
    """Base exception for all pdf2md errors."""

    category: str = "GENERAL"
    exit_code: int = 1
    error_code: str = "unhandled_exception"

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize error with message and optional context.

        Args:
            message: Human-readable error message
            context: Optional dictionary of context data (must be JSON-serializable)
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}


class ConfigError(Pdf2MdError):
    """CONFIG category errors (exit code 2)."""

    category: str = "CONFIG"
    exit_code: int = 2


class ConfigParseError(ConfigError):
    """YAML/JSON config file load failure."""

    error_code: str = "config_parse_error"


class ConfigInvalidValueError(ConfigError):
    """Value outside allowed domain."""

    error_code: str = "config_invalid_value"


class ConfigWeightSumInvalidError(ConfigError):
    """Figure caption weights sum ≠ 1 ±1e-6."""

    error_code: str = "config_weight_sum_invalid"


class ConfigRegexInvalidError(ConfigError):
    """Supplied regex fails to compile."""

    error_code: str = "config_regex_invalid"


class ConfigConflictError(ConfigError):
    """Mutually exclusive options."""

    error_code: str = "config_conflict"


class ConfigUnknownKeyError(ConfigError):
    """Extraneous key in strict mode."""

    error_code: str = "config_unknown_key"


class IOError(Pdf2MdError):
    """IO category errors (exit code 3)."""

    category: str = "IO"
    exit_code: int = 3


class PdfUnreadableError(IOError):
    """PDF file cannot be read."""

    error_code: str = "pdf_unreadable"


class OutputPathUnwritableError(IOError):
    """Output path is not writable."""

    error_code: str = "output_path_unwritable"


class ImageWriteFailedError(IOError):
    """Image write failed (fatal only if all figures fail)."""

    error_code: str = "image_write_failed"


class ParseError(Pdf2MdError):
    """PARSE category errors (exit code 4)."""

    category: str = "PARSE"
    exit_code: int = 4


class UnresolvableSlugCollisionError(ParseError):
    """Cannot resolve slug collision."""

    error_code: str = "unresolvable_slug_collision"


class DuplicateSlugDetectedError(ParseError):
    """Duplicate slug detected."""

    error_code: str = "duplicate_slug_detected"


class StructuralHashFailureError(ParseError):
    """Structural hash computation failed."""

    error_code: str = "structural_hash_failure"


class OverRemovalAbortError(ParseError):
    """Over-removal of content detected, aborting."""

    error_code: str = "over_removal_abort"


class NumberingStrictViolationError(ParseError):
    """Duplicate chapter/appendix when strict mode enabled."""

    error_code: str = "numbering_strict_violation"


def handle_fatal_error(error: Pdf2MdError, *, debug_json_errors: bool = False) -> None:
    """Handle fatal error with proper exit code and optional JSON output.

    Args:
        error: The fatal error to handle
        debug_json_errors: Whether to output structured JSON error format
    """
    if debug_json_errors:
        import json

        error_data = {
            "category": error.category,
            "code": error.error_code,
            "message": error.message,
            "context": error.context,
        }
        print(json.dumps(error_data), file=sys.stderr)
    else:
        print(f"Error: {error.message}", file=sys.stderr)

    sys.exit(error.exit_code)
