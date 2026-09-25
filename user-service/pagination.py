"""
pagination.py — Generic pagination helper for list endpoints.

No Flask imports — kept standalone so it can be unit-tested independently.

REQ-USR-B03: paginated responses include items, page, page_size, total.
"""
from __future__ import annotations

from typing import Any, Dict, List


def paginate(items: List[Any], page: int, page_size: int) -> Dict[str, Any]:
    """Slice a list and return a Page dict.

    Args:
        items:     The full (already-filtered) list of items.
        page:      1-based page number.
        page_size: Number of items per page.

    Returns:
        {
            "items":     items[start:end],
            "page":      page,
            "page_size": page_size,
            "total":     len(items),
        }

    Notes:
        - Caller is responsible for validating that page >= 1 and
          1 <= page_size <= 100 before calling this function.
        - If the requested page is beyond the last page, ``items`` will be
          an empty list and ``total`` will still reflect the full count.
    """
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": len(items),
    }
