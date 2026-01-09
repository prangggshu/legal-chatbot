def detect_risk(clause_text: str):
    if not clause_text:
        return {
            "risk_level": "Unknown",
            "risk_reason": "No clause available for risk analysis"
        }

    text = clause_text.lower()

    if "without notice" in text or "terminate" in text:
        return {
            "risk_level": "High",
            "risk_reason": "Employer can terminate without prior notice"
        }

    if "penalty" in text or "liquidated damages" in text:
        return {
            "risk_level": "Medium",
            "risk_reason": "Financial penalty imposed"
        }

    if "jurisdiction" in text or "governing law" in text:
        return {
            "risk_level": "Low",
            "risk_reason": "Standard legal clause"
        }

    return {
        "risk_level": "Low",
        "risk_reason": "No significant legal risk detected"
    }
