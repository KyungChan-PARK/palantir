def generate_plotly_html(result: dict) -> str:
    if result.get("type") == "table":
        return "<div>table</div>"
    return "<pre>" + str(result.get("data", "")) + "</pre>"
