
import logging
from typing import Any

from agent.data_loader import normalize_transaction
from agent.rule_engine import apply_rules, classify, choose_next_action

logger = logging.getLogger(__name__)


def analyze_transaction(transaction: dict, rules: list) -> dict[str, Any]:
    normalized, data_issues = normalize_transaction(transaction)
    triggered_rules, score = apply_rules(normalized, rules)
    classification = classify(score)
    
    # Generate reasoning without LLM
    reasoning = generate_reasoning(transaction, triggered_rules, score, classification, data_issues)
    recommended_action = choose_next_action(classification)
    disclaimer = "This is an AI-assisted analysis for decision support only. Final action must be reviewed and approved by an authorized human analyst."

    transaction_id = transaction.get("transaction_id", "unknown")
    logger.info(
        "Analyzed %s: classification=%s, score=%d",
        transaction_id,
        classification,
        score,
    )

    return {
        "transaction_id": transaction_id,
        "classification": classification,
        "risk_score": score,
        "triggered_rules": [
            {
                "rule_id": r["rule_id"],
                "description": r["description"],
                "risk_weight": r["risk_weight"],
            }
            for r in triggered_rules
        ],
        "reasoning": reasoning,
        "recommended_action": recommended_action,
        "disclaimer": disclaimer,
        "transaction_details": dict(transaction),
        "data_quality_notes": list(data_issues),
    }


def generate_reasoning(transaction: dict, triggered_rules: list, score: int, classification: str, data_issues: list) -> str:
    """Generate a reasoning summary without using LLM."""
    if not triggered_rules:
        return f"Transaction analyzed with risk score {score}. No fraud rules were triggered. Transaction appears {classification.lower()}."
    
    rule_descriptions = [r["description"] for r in triggered_rules]
    rules_text = ", ".join(rule_descriptions)
    
    reasoning = f"Transaction flagged with risk score {score} ({classification}). "
    reasoning += f"Triggered rules: {rules_text}. "
    
    if data_issues:
        reasoning += f"Data quality notes: {'; '.join(data_issues)}. "
    
    reasoning += f"Based on the rule-based analysis, this transaction is classified as {classification}."
    return reasoning


def analyze_batch(
    transactions: list[dict], rules: list
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    total = len(transactions)
    for i, txn in enumerate(transactions, start=1):
        txn_id = txn.get("transaction_id", "unknown")
        logger.info("Processing transaction %d/%d: %s", i, total, txn_id)
        result = analyze_transaction(txn, rules)
        results.append(result)
    logger.info("Batch analysis complete: %d transactions processed", total)
    return results
