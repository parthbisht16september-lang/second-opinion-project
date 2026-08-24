def format_suggestion(raw_issue, style):
    if style == "bare":
        return f"Issue: {raw_issue}"
    elif style == "confidence":
        return f"Issue: {raw_issue} (Confidence: 78%)"
    elif style == "socratic":
        return f"Have you considered: {raw_issue}?"
    return raw_issue