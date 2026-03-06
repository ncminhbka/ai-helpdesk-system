"""
Utility functions and helpers.
"""
from datetime import datetime, timezone
from typing import Optional
import json


def parse_datetime(dt_string: str) -> Optional[datetime]:
    """Parse datetime string to datetime object, supports multiple formats."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
    ]

    for fmt in formats:
        try:
            # Parse as naive datetime then assume UTC timezone
            naive_dt = datetime.strptime(dt_string, fmt)
            return naive_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def safe_json_loads(json_str: str, default: dict = None) -> dict:
    """Safely parse JSON string."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default or {}


def safe_json_dumps(data: dict) -> str:
    """Safely dump dict to JSON string."""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return "{}"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def get_vietnam_time() -> str:
    """Get current time in Vietnam timezone (UTC+7), formatted for agent prompts."""
    from datetime import timezone, timedelta
    vn_tz = timezone(timedelta(hours=7))
    now = datetime.now(vn_tz)
    return now.strftime("%Y-%m-%d %H:%M:%S (UTC+7, Vietnam)")

