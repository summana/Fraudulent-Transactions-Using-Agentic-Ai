"""Rule engine for fraud detection.

Loads fraud detection rules from JSON, applies them against normalized
transactions, and classifies risk levels.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

RULES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "rules", "fraud_rules.json"
)

ALLOWED_ACTIONS = [
    "Monitor",
    "Request Customer Verification",
    "Escalate to Senior Analyst",
    "Flag for Compliance Review",
]


def load_rules(path: str | None = None) -> list[dict]:
    """Load fraud detection rules from a JSON file.

    Args:
        path: Optional path to the rules JSON. Defaults to rules/fraud_rules.json.

    Returns:
        A list of rule dicts.
    """
    if path is None:
        path = RULES_PATH
    logger.info("Loading rules from %s", path)
    with open(path, "r", encoding="utf-8") as f:
        rules = json.load(f)
    logger.info("Loaded %d rules", len(rules))
    return rules


def apply_rules(normalized: dict, rules: list) -> tuple[list, int]:
    """Evaluate all rules against a normalized transaction.

    Returns:
        A tuple of (triggered_rules_list, total_risk_score).
    """
    triggered_rules = []
    score = 0

    amount = normalized["amount"]
    hour = normalized["hour"]
    transactions_last_10min = normalized["transactions_last_10min"]
    transaction_country = normalized["transaction_country"]
    account_home_country = normalized["account_home_country"]
    is_new_device = normalized["is_new_device"]
    merchant_category = normalized["merchant_category"]
    prior_flagged_amounts = normalized["prior_flagged_amounts"]
    account_age_days = normalized["account_age_days"]

    for rule in rules:
        trigger = False
        r_id = rule["rule_id"]

        if r_id == "R001" and amount > 100000:
            trigger = True
        elif r_id == "R002" and 0 <= hour <= 4:
            trigger = True
        elif r_id == "R003" and transactions_last_10min > 5:
            trigger = True
        elif r_id == "R004" and transaction_country != account_home_country:
            trigger = True
        elif r_id == "R005" and is_new_device:
            trigger = True
        elif r_id == "R006" and merchant_category in ["Gambling", "Crypto Exchange"]:
            trigger = True
        elif r_id == "R007" and prior_flagged_amounts:
            if any(
                abs(amount - flagged_amount) < 1e-9
                for flagged_amount in prior_flagged_amounts
            ):
                trigger = True
        elif r_id == "R008" and account_age_days < 30 and amount > 50000:
            trigger = True

        if trigger:
            triggered_rules.append(rule)
            score += rule["risk_weight"]

    logger.debug(
        "Applied %d rules: %d triggered, score=%d",
        len(rules),
        len(triggered_rules),
        score,
    )
    return triggered_rules, score


def classify(score: int) -> str:
    """Classify risk level based on the total risk score.

    Returns:
        'Legitimate', 'Suspicious', or 'Likely Fraud'.
    """
    if score <= 3:
        return "Legitimate"
    elif score <= 6:
        return "Suspicious"
    else:
        return "Likely Fraud"


def choose_next_action(classification: str) -> str:
    """Map a risk classification to a default recommended action."""
    if classification == "Likely Fraud":
        return "Flag for Compliance Review"
    if classification == "Suspicious":
        return "Request Customer Verification"
    return "Monitor"


def normalize_action(action_text: str, classification: str) -> str:
    """Normalize an LLM-suggested action to one of the allowed actions.

    Falls back to the default action for the given classification if
    the action text cannot be matched.
    """
    if not action_text:
        return choose_next_action(classification)

    canonical = {value.lower(): value for value in ALLOWED_ACTIONS}
    normalized = action_text.strip().lower()
    if normalized in canonical:
        return canonical[normalized]

    for allowed in ALLOWED_ACTIONS:
        if allowed.lower() in normalized:
            return allowed

    return choose_next_action(classification)
