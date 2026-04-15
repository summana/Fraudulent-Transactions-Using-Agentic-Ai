
import argparse
import json
import logging
import subprocess
import sys
from collections import Counter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run_cli():
    """Run fraud analysis in CLI mode and print results."""
    from agent import load_transactions, load_rules, analyze_batch

    logger.info("Loading rules...")
    rules = load_rules()
    logger.info("Loaded %d rules.", len(rules))

    logger.info("Loading transactions...")
    transactions = load_transactions()
    logger.info("Loaded %d transactions.", len(transactions))

    logger.info("Analyzing transactions...")
    results = analyze_batch(transactions, rules)

    for result in results:
        print(json.dumps(result, indent=2, default=str))
        print("-" * 60)

    # Summary
    classifications = Counter(r.get("classification", "unknown") for r in results)
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total transactions analyzed: {len(results)}")
    for classification, count in classifications.most_common():
        print(f"  {classification}: {count}")
    print("=" * 60)

    logger.info("CLI analysis complete.")


def run_ui():
    """Launch the Streamlit UI."""
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/app.py"])
    except FileNotFoundError:
        print(
            "Error: Could not launch Streamlit. "
            "Please install it with: pip install streamlit"
        )
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="AI Fraud Detection Agent")
    parser.add_argument(
        "--mode",
        choices=["cli", "ui"],
        default="ui",
        help="Run mode: 'cli' for console analysis, 'ui' for Streamlit dashboard (default: ui)",
    )
    args = parser.parse_args()

    if args.mode == "cli":
        run_cli()
    else:
        run_ui()


if __name__ == "__main__":
    main()
