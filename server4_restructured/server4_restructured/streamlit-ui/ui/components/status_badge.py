def status_badge(status: str | None) -> str:
    """Return an HTML badge for a service/incident status."""
    if not status:
        return "<span style='padding:2px 8px;border-radius:999px;background:#444;color:#fff;font-size:11px;'>—</span>"
    s = status.upper()
    color_map = {
        "HEALTHY":    "#1f8b4c",
        "PASSED":     "#1f8b4c",
        "RUNNING":    "#b54708",
        "UNHEALTHY":  "#b42318",
        "FAILED":     "#b42318",
        "PENDING":    "#444",
        "APPROVED":   "#1f8b4c",
        "REJECTED":   "#b42318",
    }
    bg = color_map.get(s, "#444")
    return (f"<span style='padding:2px 8px;border-radius:999px;"
            f"background:{bg};color:#fff;font-size:11px;font-weight:600;'>{s}</span>")
