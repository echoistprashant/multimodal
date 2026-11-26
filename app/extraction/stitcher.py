"""Multi-Page Line Item Stitcher and Payload Aggregator.

Consolidates per-page extracted field dictionaries into a unified document representation,
stitching continuous line items, resolving running headers, and merging financial totals.
"""

from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel

from app.core.logging import get_logger
from app.schemas.validation_rules import sanitize_extraction_payload

logger = get_logger("app.extraction.stitcher")


class MultiPageItemStitcher:
    """Stitches multi-page extraction fragments into a single unified document payload."""

    def stitch_pages(
        self,
        page_payloads: List[Dict[str, Any]],
        target_schema_cls: Optional[Type[BaseModel]] = None,
    ) -> Dict[str, Any]:
        """Merge per-page extracted payloads into a consolidated document object."""
        if not page_payloads:
            return {}

        if len(page_payloads) == 1:
            sanitized = sanitize_extraction_payload(page_payloads[0])
            if target_schema_cls:
                return target_schema_cls.model_validate(sanitized).model_dump(mode="json")
            return sanitized

        consolidated: Dict[str, Any] = {}
        all_line_items: List[Dict[str, Any]] = []

        # 1. Merge top-level metadata from earliest non-empty page
        for p in page_payloads:
            for key, val in p.items():
                if key in ["line_items", "items"]:
                    continue
                # Overwrite if consolidated doesn't have it or current page has non-null value
                if val is not None and (key not in consolidated or consolidated[key] is None):
                    consolidated[key] = val

        # 2. Accumulate line items across pages
        for p in page_payloads:
            items = p.get("line_items") or p.get("items") or []
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and item.get("description"):
                        all_line_items.append(item)

        # 3. Deduplicate exact duplicate items across page boundaries
        deduped_items: List[Dict[str, Any]] = []
        seen_keys = set()
        for item in all_line_items:
            key = (str(item.get("description")).strip().lower(), item.get("amount"))
            if key not in seen_keys:
                seen_keys.add(key)
                deduped_items.append(item)

        if "items" in consolidated or any("items" in p for p in page_payloads):
            consolidated["items"] = deduped_items
        else:
            consolidated["line_items"] = deduped_items

        # 4. Resolve financial totals from the last page containing totals
        for p in reversed(page_payloads):
            for total_key in ["total_amount", "total_billed_amount", "subtotal", "tax_amount"]:
                if p.get(total_key) is not None:
                    consolidated[total_key] = p[total_key]

        sanitized_final = sanitize_extraction_payload(consolidated)

        # 5. Validate with Pydantic target schema if provided
        if target_schema_cls:
            try:
                validated = target_schema_cls.model_validate(sanitized_final)
                return validated.model_dump(mode="json")
            except Exception as err:
                logger.warning(f"Consolidated payload validation warning: {err}")

        return sanitized_final
