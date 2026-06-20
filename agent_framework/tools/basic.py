"""
Basic Utility Tools
---
General-purpose tools: calculator, web search, environment control.
Available to the Executor Agent regardless of the application domain.
"""

import random
from datetime import datetime


def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Supports +, -, *, /, **, () and basic math functions."""
    safe_builtins = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sum": sum, "pow": pow,
    }
    try:
        result = eval(expression, {"__builtins__": safe_builtins}, {})
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Calculation error: {e}"


def web_search(query: str, num_results: int = 3) -> str:
    """Search the web for information. Returns top results with title and URL."""
    mock_results = [
        {
            "title": f"Latest research on {query} – Medical Journal",
            "snippet": f"Recent studies show promising results in {query} treatment for elderly patients...",
            "url": f"https://medical-journal.example.com/{query.replace(' ', '-')}",
        },
        {
            "title": f"{query} guidelines for senior care – WHO",
            "snippet": f"World Health Organization guidelines on {query} management in geriatric care settings...",
            "url": f"https://who.int/guidelines/{query.replace(' ', '-')}",
        },
        {
            "title": f"FAQ: {query} in elderly patients – HealthLine",
            "snippet": f"Common questions about {query} answered by board-certified geriatricians...",
            "url": f"https://healthline.example.com/{query.replace(' ', '-')}",
        },
    ]
    results = mock_results[:num_results]
    lines = [f"Web search results for '{query}':"]
    for i, r in enumerate(results, 1):
        lines.append(f"\n  {i}. {r['title']}\n     {r['snippet']}\n     {r['url']}")
    return "\n".join(lines)


def control_environment(device: str, action: str, value: str = "") -> str:
    """Control smart home environment devices. device: 'light', 'thermostat', 'curtain', 'door_lock'. action: 'on'/'off'/'set'."""
    valid_devices = ["light", "thermostat", "curtain", "door_lock"]
    if device not in valid_devices:
        return f"Error: Unknown device '{device}'. Available: {', '.join(valid_devices)}"

    return (
        f"Environment control executed:\n"
        f"  Device: {device}\n"
        f"  Action: {action}" + (f"\n  Value: {value}" if value else "") +
        f"\n  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"  Status: Success"
    )
