"""Data loading and transaction normalization utilities.

Handles CSV parsing, field validation, and transaction normalization
for the fraud detection pipeline.
"""

import os
import csv
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "mock_transactions.csv"
)


def parse_float_field(
    transaction: dict, field: str, default: float, data_issues: list[str]
) -> float:
    """Parse a float field from a transaction dict, tracking data issues."""
    raw = transaction.get(field)
    if raw is None or str(raw).strip() == "":
        data_issues.append(f"{field} missing; defaulted to {default}")
        return default
    try:
        return float(str(raw).strip())
    except ValueError:
        data_issues.append(f"{field} invalid ({raw}); defaulted to {default}")
        return default


def parse_int_field(
    transaction: dict, field: str, default: int, data_issues: list[str]
) -> int:
    """Parse an integer field from a transaction dict, tracking data issues."""
    raw = transaction.get(field)
    if raw is None or str(raw).strip() == "":
        data_issues.append(f"{field} missing; defaulted to {default}")
        return default
    try:
        return int(str(raw).strip())
    except ValueError:
        data_issues.append(f"{field} invalid ({raw}); defaulted to {default}")
        return default


def parse_bool_field(
    transaction: dict, field: str, default: bool, data_issues: list[str]
) -> bool:
    """Parse a boolean field from a transaction dict, tracking data issues."""
    raw = transaction.get(field)
    if raw is None or str(raw).strip() == "":
        data_issues.append(f"{field} missing; defaulted to {default}")
        return default

    parsed = str(raw).strip().lower()
    if parsed in ["true", "1", "yes", "y"]:
        return True
    if parsed in ["false", "0", "no", "n"]:
        return False

    data_issues.append(f"{field} invalid ({raw}); defaulted to {default}")
    return default


def parse_prior_flagged_amounts(
    raw_value: str, data_issues: list[str]
) -> list[float]:
    """Parse comma-separated prior flagged amounts into a list of floats."""
    if raw_value is None or str(raw_value).strip() == "":
        return []

    values = []
    for chunk in str(raw_value).split(","):
        token = chunk.strip()
        if not token:
            continue
        try:
            values.append(float(token))
        except ValueError:
            data_issues.append(
                f"prior_flagged_amounts contains invalid value ({token}); ignored"
            )
    return values


def normalize_transaction(transaction: dict) -> tuple[dict, list[str]]:
    """Normalize raw transaction data into a consistent dict for rule evaluation.

    Returns:
        A tuple of (normalized_dict, data_issues_list).
    """
    data_issues: list[str] = []

    amount = parse_float_field(transaction, "amount", 0.0, data_issues)
    timestamp_raw = transaction.get("timestamp")
    if timestamp_raw is None or str(timestamp_raw).strip() == "":
        data_issues.append("timestamp missing; defaulted to hour=12")
        hour = 12
    else:
        try:
            dt = datetime.strptime(str(timestamp_raw).strip(), "%Y-%m-%d %H:%M:%S")
            hour = dt.hour
        except ValueError:
            data_issues.append(
                f"timestamp invalid ({timestamp_raw}); defaulted to hour=12"
            )
            hour = 12

    normalized = {
        "amount": amount,
        "hour": hour,
        "transactions_last_10min": parse_int_field(
            transaction, "transactions_last_10min", 0, data_issues
        ),
        "transaction_country": str(
            transaction.get("transaction_country", "") or ""
        ).strip(),
        "account_home_country": str(
            transaction.get("account_home_country", "") or ""
        ).strip(),
        "is_new_device": parse_bool_field(
            transaction, "is_new_device", False, data_issues
        ),
        "merchant_category": str(
            transaction.get("merchant_category", "") or ""
        ).strip(),
        "prior_flagged_amounts": parse_prior_flagged_amounts(
            transaction.get("prior_flagged_amounts", ""), data_issues
        ),
        "account_age_days": parse_int_field(
            transaction, "account_age_days", 100, data_issues
        ),
    }
    return normalized, data_issues


def load_transactions(path: str | None = None) -> list[dict]:
    """Load transactions from a CSV file.

    Args:
        path: Optional path to the CSV file. Defaults to data/mock_transactions.csv.

    Returns:
        A list of transaction dicts.
    """
    if path is None:
        path = DATA_PATH
    logger.info("Loading transactions from %s", path)
    transactions: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(row)
    logger.info("Loaded %d transactions", len(transactions))
    return transactions
