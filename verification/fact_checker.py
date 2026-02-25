import re


def extract_numbers(text: str) -> list[str]:
    """Find all numeric values (with optional $ and %) in a text string."""
    return re.findall(r"\$?[\d,]+\.?\d*%?", text)


def verify_claims(tool_results: list[dict]) -> dict:
    """
    Cross-reference tool results to detect failed tools and calculate
    confidence score. Each failed tool reduces confidence by 0.15.

    Returns a verification summary dict.
    """
    failed_tools = [
        r.get("tool_name", "unknown")
        for r in tool_results
        if not r.get("success", False)
    ]

    tool_count = len(tool_results)
    confidence_adjustment = -0.15 * len(failed_tools)

    if len(failed_tools) == 0:
        base_confidence = 0.9
        outcome = "pass"
    elif len(failed_tools) < tool_count:
        base_confidence = max(0.4, 0.9 + confidence_adjustment)
        outcome = "flag"
    else:
        base_confidence = 0.1
        outcome = "escalate"

    tool_data_str = str(tool_results).lower()
    all_numbers = extract_numbers(tool_data_str)

    return {
        "verified": len(failed_tools) == 0,
        "tool_count": tool_count,
        "failed_tools": failed_tools,
        "successful_tools": [
            r.get("tool_name", "unknown")
            for r in tool_results
            if r.get("success", False)
        ],
        "confidence_adjustment": confidence_adjustment,
        "base_confidence": base_confidence,
        "outcome": outcome,
        "numeric_data_points": len(all_numbers),
    }
